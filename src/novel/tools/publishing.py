"""Publishing domain MCP tools.

All 7 publishing tools are registered via the register(mcp) function pattern.
Read/write tools call check_gate(conn) before any database logic. Delete tools
do NOT require gate certification — publishing module deletes are administrative
operations not gated by the architecture gate.

IMPORTANT: Never use the print function in this module. All logging goes to
stderr via the logging module — using print corrupts the stdio protocol.
"""
import logging

from mcp.server.fastmcp import FastMCP

from novel.mcp.db import get_connection
from novel.mcp.gate import check_gate
from novel.models.publishing import PublishingAsset, SubmissionEntry
from novel.models.shared import GateViolation, NotFoundResponse, ValidationFailure

logger = logging.getLogger(__name__)


def register(mcp: FastMCP) -> None:
    """Register all 7 publishing domain tools with the given FastMCP instance.

    Tools are defined as local async functions and decorated with @mcp.tool().
    The FastMCP instance is always the one passed in — never imported globally.

    Read/write tools call check_gate(conn) at the top before any DB logic and
    return GateViolation if the gate is not certified. Delete tools do NOT use
    check_gate — publishing deletes are administrative operations.

    Args:
        mcp: The FastMCP server instance to register tools against.
    """

    # ------------------------------------------------------------------
    # get_publishing_assets (PUBL-01)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def get_publishing_assets(
        asset_type: str | None = None,
    ) -> list[PublishingAsset] | GateViolation:
        """Retrieve all publishing assets, with optional asset_type filter.

        Returns a list of PublishingAsset records ordered by created_at DESC
        (most recently created first). The asset_type filter is optional.

        Args:
            asset_type: Filter by asset category (e.g. 'query_letter', 'synopsis').

        Returns:
            List of PublishingAsset records ordered by created_at DESC
            (may be empty). GateViolation if the gate is not certified.
        """
        async with get_connection() as conn:
            gate = await check_gate(conn)
            if gate is not None:
                return gate

            if asset_type is not None:
                sql = "SELECT * FROM publishing_assets WHERE asset_type = ? ORDER BY created_at DESC"
                params: list[object] = [asset_type]
            else:
                sql = "SELECT * FROM publishing_assets ORDER BY created_at DESC"
                params = []

            async with conn.execute(sql, params) as cursor:
                rows = await cursor.fetchall()

            return [PublishingAsset(**dict(row)) for row in rows]

    # ------------------------------------------------------------------
    # upsert_publishing_asset (PUBL-02)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def upsert_publishing_asset(
        title: str,
        content: str,
        asset_id: int | None = None,
        asset_type: str = "query_letter",
        version: int = 1,
        status: str = "draft",
        notes: str | None = None,
    ) -> PublishingAsset | GateViolation:
        """Create or update a publishing asset.

        Two-branch upsert on id (PK — no named UNIQUE beyond PK):
        - None asset_id: plain INSERT creates a new asset row.
        - Provided asset_id: INSERT ... ON CONFLICT(id) DO UPDATE updates the
          existing asset (id is the PK conflict target).

        After either branch, the row is SELECT-ed back by id and returned.

        Args:
            title: Title of the publishing asset.
            content: Full text content of the asset.
            asset_id: Existing asset ID for update branch (optional).
            asset_type: Category of asset (default 'query_letter').
            version: Version number of this asset (default 1).
            status: Publication status of the asset (default 'draft').
            notes: Additional notes (optional).

        Returns:
            The created or updated PublishingAsset record.
            GateViolation if the gate is not certified.
        """
        async with get_connection() as conn:
            gate = await check_gate(conn)
            if gate is not None:
                return gate

            if asset_id is None:
                # None-id branch: plain INSERT
                cursor = await conn.execute(
                    """
                    INSERT INTO publishing_assets
                        (asset_type, title, content, version, status, notes)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (asset_type, title, content, version, status, notes),
                )
                new_id = cursor.lastrowid
            else:
                # Provided-id branch: INSERT ... ON CONFLICT(id) DO UPDATE
                await conn.execute(
                    """
                    INSERT INTO publishing_assets
                        (id, asset_type, title, content, version, status, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        asset_type=excluded.asset_type,
                        title=excluded.title,
                        content=excluded.content,
                        version=excluded.version,
                        status=excluded.status,
                        notes=excluded.notes,
                        updated_at=datetime('now')
                    """,
                    (asset_id, asset_type, title, content, version, status, notes),
                )
                new_id = asset_id

            await conn.commit()

            async with conn.execute(
                "SELECT * FROM publishing_assets WHERE id = ?", (new_id,)
            ) as cur:
                row = await cur.fetchone()

            return PublishingAsset(**dict(row))

    # ------------------------------------------------------------------
    # get_submissions (PUBL-03)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def get_submissions(
        status: str | None = None,
    ) -> list[SubmissionEntry] | GateViolation:
        """Retrieve all submission tracker entries, with optional status filter.

        Returns a list of SubmissionEntry records ordered by submitted_at DESC
        (most recently submitted first). The status filter is optional.

        Args:
            status: Filter by submission status (e.g. 'pending', 'accepted', 'rejected').

        Returns:
            List of SubmissionEntry records ordered by submitted_at DESC
            (may be empty). GateViolation if the gate is not certified.
        """
        async with get_connection() as conn:
            gate = await check_gate(conn)
            if gate is not None:
                return gate

            if status is not None:
                sql = "SELECT * FROM submission_tracker WHERE status = ? ORDER BY submitted_at DESC"
                params: list[object] = [status]
            else:
                sql = "SELECT * FROM submission_tracker ORDER BY submitted_at DESC"
                params = []

            async with conn.execute(sql, params) as cursor:
                rows = await cursor.fetchall()

            return [SubmissionEntry(**dict(row)) for row in rows]

    # ------------------------------------------------------------------
    # log_submission (PUBL-04)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def log_submission(
        agency_or_publisher: str,
        submitted_at: str,
        asset_id: int | None = None,
        status: str = "pending",
        notes: str | None = None,
    ) -> SubmissionEntry | GateViolation:
        """Log a new submission to an agency or publisher (append-only).

        Append-only INSERT — each call creates a distinct submission log entry.
        Submissions are discrete historical events; they are not upserted.
        Use update_submission to record responses or status changes.

        Args:
            agency_or_publisher: Name of the agency or publisher submitted to.
            submitted_at: ISO date/datetime of submission (e.g. '2024-01-15').
            asset_id: FK to publishing_assets table (optional).
            status: Initial submission status (default 'pending').
            notes: Additional notes (optional).

        Returns:
            The newly created SubmissionEntry record with id set.
            GateViolation if the gate is not certified.
        """
        async with get_connection() as conn:
            gate = await check_gate(conn)
            if gate is not None:
                return gate

            cursor = await conn.execute(
                """
                INSERT INTO submission_tracker
                    (asset_id, agency_or_publisher, submitted_at, status, notes)
                VALUES (?, ?, ?, ?, ?)
                """,
                (asset_id, agency_or_publisher, submitted_at, status, notes),
            )
            new_id = cursor.lastrowid
            await conn.commit()

            async with conn.execute(
                "SELECT * FROM submission_tracker WHERE id = ?", (new_id,)
            ) as cur:
                row = await cur.fetchone()

            return SubmissionEntry(**dict(row))

    # ------------------------------------------------------------------
    # update_submission (PUBL-05)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def update_submission(
        submission_id: int,
        status: str,
        response_at: str | None = None,
        response_notes: str | None = None,
        follow_up_due: str | None = None,
    ) -> SubmissionEntry | NotFoundResponse | GateViolation:
        """Partially update a submission tracker entry.

        Updates status and optional response fields on an existing submission.
        Uses a dynamic SET clause — only fields provided are updated.
        After UPDATE, SELECT-back is required to detect missing rows (SQLite
        does not error when UPDATE matches no rows).

        Args:
            submission_id: ID of the submission to update.
            status: New submission status (required).
            response_at: Date/datetime when a response was received (optional).
            response_notes: Notes on the response received (optional).
            follow_up_due: Date/datetime for next follow-up action (optional).

        Returns:
            The updated SubmissionEntry record.
            NotFoundResponse if the submission_id does not exist.
            GateViolation if the gate is not certified.
        """
        async with get_connection() as conn:
            gate = await check_gate(conn)
            if gate is not None:
                return gate

            set_parts = ["status=?", "updated_at=datetime('now')"]
            params: list[object] = [status]

            if response_at is not None:
                set_parts.append("response_at=?")
                params.append(response_at)
            if response_notes is not None:
                set_parts.append("response_notes=?")
                params.append(response_notes)
            if follow_up_due is not None:
                set_parts.append("follow_up_due=?")
                params.append(follow_up_due)

            params.append(submission_id)
            await conn.execute(
                f"UPDATE submission_tracker SET {', '.join(set_parts)} WHERE id = ?",
                params,
            )
            await conn.commit()

            # SELECT-back: SQLite does not error on UPDATE of missing row
            async with conn.execute(
                "SELECT * FROM submission_tracker WHERE id = ?",
                (submission_id,),
            ) as cur:
                row = await cur.fetchone()

            if row is None:
                return NotFoundResponse(
                    not_found_message=f"Submission {submission_id} not found"
                )

            return SubmissionEntry(**dict(row))

    # ------------------------------------------------------------------
    # delete_publishing_asset (PUBL-06)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def delete_publishing_asset(
        asset_id: int,
    ) -> NotFoundResponse | ValidationFailure | dict:
        """Delete a publishing asset by ID.

        NOT gate-gated: publishing asset deletions are administrative operations
        that do not require architecture gate certification. publishing_assets may
        be referenced by submission_tracker (via asset_id FK); FK violations are
        caught and returned as ValidationFailure.

        Args:
            asset_id: Primary key of the publishing_assets row to delete.

        Returns:
            Dict with deleted=True and id on success. NotFoundResponse if the
            asset does not exist. ValidationFailure if a FK constraint prevents
            deletion (e.g. linked submission_tracker entries exist).
        """
        async with get_connection() as conn:
            async with conn.execute(
                "SELECT id FROM publishing_assets WHERE id = ?", (asset_id,)
            ) as cursor:
                row = await cursor.fetchone()

            if row is None:
                return NotFoundResponse(
                    not_found_message=f"Publishing asset {asset_id} not found"
                )

            try:
                await conn.execute(
                    "DELETE FROM publishing_assets WHERE id = ?", (asset_id,)
                )
                await conn.commit()
                return {"deleted": True, "id": asset_id}
            except Exception as exc:
                logger.error("delete_publishing_asset failed: %s", exc)
                return ValidationFailure(is_valid=False, errors=[str(exc)])

    # ------------------------------------------------------------------
    # delete_submission (PUBL-07)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def delete_submission(
        submission_id: int,
    ) -> NotFoundResponse | dict:
        """Delete a submission tracker entry by ID.

        NOT gate-gated: submission deletions are administrative operations
        that do not require architecture gate certification. submission_tracker
        is an append-only log with no FK children — deletion uses the log-style
        pattern (no try/except needed for FK safety).

        Args:
            submission_id: Primary key of the submission_tracker row to delete.

        Returns:
            Dict with deleted=True and id on success. NotFoundResponse if the
            submission does not exist.
        """
        async with get_connection() as conn:
            async with conn.execute(
                "SELECT id FROM submission_tracker WHERE id = ?", (submission_id,)
            ) as cursor:
                row = await cursor.fetchone()

            if row is None:
                return NotFoundResponse(
                    not_found_message=f"Submission {submission_id} not found"
                )

            await conn.execute(
                "DELETE FROM submission_tracker WHERE id = ?", (submission_id,)
            )
            await conn.commit()
            return {"deleted": True, "id": submission_id}
