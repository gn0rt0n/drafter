"""Canon domain MCP tools.

All 7 canon tools are registered via the register(mcp) function pattern.
This module is standalone — it does not modify server.py; wiring happens in
the server module.

IMPORTANT: Never use the print function in this module. All logging goes to
stderr via the logging module — using print corrupts the stdio protocol.
"""

import logging

from mcp.server.fastmcp import FastMCP

from novel.mcp.db import get_connection
from novel.mcp.gate import check_gate
from novel.models.canon import CanonFact, ContinuityIssue, StoryDecision
from novel.models.shared import GateViolation, NotFoundResponse

logger = logging.getLogger(__name__)


def register(mcp: FastMCP) -> None:
    """Register all 7 canon domain tools with the given FastMCP instance.

    Tools are defined as local async functions and decorated with @mcp.tool().
    The FastMCP instance is always the one passed in — never imported globally.

    All tools call check_gate(conn) at the top before any DB logic and return
    GateViolation if the gate is not certified.

    Args:
        mcp: The FastMCP server instance to register tools against.
    """

    # ------------------------------------------------------------------
    # get_canon_facts (CANO-01)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def get_canon_facts(domain: str) -> list[CanonFact] | GateViolation:
        """Retrieve all canon facts for a given domain.

        Args:
            domain: The domain to filter by (e.g. "magic", "geography", "general").

        Returns:
            List of CanonFact records for the domain (may be empty).
            GateViolation if the gate is not certified.
        """
        async with get_connection() as conn:
            gate = await check_gate(conn)
            if gate is not None:
                return gate

            async with conn.execute(
                "SELECT * FROM canon_facts WHERE domain = ? ORDER BY created_at",
                (domain,),
            ) as cursor:
                rows = await cursor.fetchall()

            return [CanonFact(**dict(row)) for row in rows]

    # ------------------------------------------------------------------
    # log_canon_fact (CANO-02)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def log_canon_fact(
        fact: str,
        domain: str = "general",
        source_chapter_id: int | None = None,
        source_event_id: int | None = None,
        parent_fact_id: int | None = None,
        certainty_level: str = "established",
        canon_status: str = "approved",
        notes: str | None = None,
    ) -> CanonFact | GateViolation:
        """Log a new canon fact to the database.

        Append-only insert — no conflict resolution. Each call creates a new row.

        Args:
            fact: The canon fact text.
            domain: Domain the fact belongs to (default "general").
            source_chapter_id: Chapter where this fact was established (optional).
            source_event_id: Event that established this fact (optional).
            parent_fact_id: Parent fact this derives from (optional).
            certainty_level: Certainty level (default "established").
            canon_status: Canon status (default "approved").
            notes: Additional notes (optional).

        Returns:
            The newly created CanonFact record.
            GateViolation if the gate is not certified.
        """
        async with get_connection() as conn:
            gate = await check_gate(conn)
            if gate is not None:
                return gate

            cursor = await conn.execute(
                """
                INSERT INTO canon_facts
                    (domain, fact, source_chapter_id, source_event_id,
                     parent_fact_id, certainty_level, canon_status, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    domain,
                    fact,
                    source_chapter_id,
                    source_event_id,
                    parent_fact_id,
                    certainty_level,
                    canon_status,
                    notes,
                ),
            )
            new_id = cursor.lastrowid
            await conn.commit()

            async with conn.execute(
                "SELECT * FROM canon_facts WHERE id = ?", (new_id,)
            ) as cur:
                row = await cur.fetchone()

            return CanonFact(**dict(row))

    # ------------------------------------------------------------------
    # log_decision (CANO-03)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def log_decision(
        description: str,
        decision_type: str = "plot",
        rationale: str | None = None,
        alternatives: str | None = None,
        session_id: int | None = None,
        chapter_id: int | None = None,
    ) -> StoryDecision | GateViolation:
        """Log a story decision with rationale to the decisions_log.

        Append-only insert — each call creates a new row.

        Args:
            description: Description of the decision made.
            decision_type: Type of decision (default "plot").
            rationale: Why this decision was made (optional).
            alternatives: Alternatives that were considered (optional).
            session_id: Writing session this decision was made in (optional).
            chapter_id: Chapter this decision applies to (optional).

        Returns:
            The newly created StoryDecision record.
            GateViolation if the gate is not certified.
        """
        async with get_connection() as conn:
            gate = await check_gate(conn)
            if gate is not None:
                return gate

            cursor = await conn.execute(
                """
                INSERT INTO decisions_log
                    (decision_type, description, rationale, alternatives,
                     session_id, chapter_id)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    decision_type,
                    description,
                    rationale,
                    alternatives,
                    session_id,
                    chapter_id,
                ),
            )
            new_id = cursor.lastrowid
            await conn.commit()

            async with conn.execute(
                "SELECT * FROM decisions_log WHERE id = ?", (new_id,)
            ) as cur:
                row = await cur.fetchone()

            return StoryDecision(**dict(row))

    # ------------------------------------------------------------------
    # get_decisions (CANO-04)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def get_decisions(
        decision_type: str | None = None,
        chapter_id: int | None = None,
    ) -> list[StoryDecision] | GateViolation:
        """Retrieve the decisions log with optional filters.

        Args:
            decision_type: Filter by decision type (optional).
            chapter_id: Filter by chapter (optional).

        Returns:
            List of StoryDecision records (may be empty).
            GateViolation if the gate is not certified.
        """
        async with get_connection() as conn:
            gate = await check_gate(conn)
            if gate is not None:
                return gate

            conditions: list[str] = []
            params: list[object] = []

            if decision_type is not None:
                conditions.append("decision_type = ?")
                params.append(decision_type)
            if chapter_id is not None:
                conditions.append("chapter_id = ?")
                params.append(chapter_id)

            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
            sql = f"SELECT * FROM decisions_log {where_clause} ORDER BY created_at DESC"

            async with conn.execute(sql, params) as cursor:
                rows = await cursor.fetchall()

            return [StoryDecision(**dict(row)) for row in rows]

    # ------------------------------------------------------------------
    # log_continuity_issue (CANO-05)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def log_continuity_issue(
        description: str,
        severity: str = "minor",
        chapter_id: int | None = None,
        scene_id: int | None = None,
        canon_fact_id: int | None = None,
    ) -> ContinuityIssue | GateViolation:
        """Log a new continuity issue with severity triage.

        Append-only insert — each call creates a new row.

        Args:
            description: Description of the continuity issue.
            severity: Severity level (default "minor").
            chapter_id: Chapter where the issue occurs (optional).
            scene_id: Scene where the issue occurs (optional).
            canon_fact_id: Canon fact this issue relates to (optional).

        Returns:
            The newly created ContinuityIssue record.
            GateViolation if the gate is not certified.
        """
        async with get_connection() as conn:
            gate = await check_gate(conn)
            if gate is not None:
                return gate

            cursor = await conn.execute(
                """
                INSERT INTO continuity_issues
                    (severity, description, chapter_id, scene_id, canon_fact_id)
                VALUES (?, ?, ?, ?, ?)
                """,
                (severity, description, chapter_id, scene_id, canon_fact_id),
            )
            new_id = cursor.lastrowid
            await conn.commit()

            async with conn.execute(
                "SELECT * FROM continuity_issues WHERE id = ?", (new_id,)
            ) as cur:
                row = await cur.fetchone()

            return ContinuityIssue(**dict(row))

    # ------------------------------------------------------------------
    # get_continuity_issues (CANO-06)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def get_continuity_issues(
        severity: str | None = None,
        include_resolved: bool = False,
    ) -> list[ContinuityIssue] | GateViolation:
        """Retrieve open continuity issues with optional severity filter.

        Args:
            severity: Filter by severity (optional).
            include_resolved: Include resolved issues (default False).

        Returns:
            List of ContinuityIssue records (may be empty).
            GateViolation if the gate is not certified.
        """
        async with get_connection() as conn:
            gate = await check_gate(conn)
            if gate is not None:
                return gate

            conditions: list[str] = []
            params: list[object] = []

            if not include_resolved:
                conditions.append("is_resolved = FALSE")
            if severity is not None:
                conditions.append("severity = ?")
                params.append(severity)

            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
            sql = f"SELECT * FROM continuity_issues {where_clause} ORDER BY created_at ASC"

            async with conn.execute(sql, params) as cursor:
                rows = await cursor.fetchall()

            return [ContinuityIssue(**dict(row)) for row in rows]

    # ------------------------------------------------------------------
    # resolve_continuity_issue (CANO-07)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def resolve_continuity_issue(
        issue_id: int,
        resolution_note: str,
    ) -> ContinuityIssue | NotFoundResponse | GateViolation:
        """Resolve a continuity issue by ID.

        Args:
            issue_id: ID of the continuity issue to resolve.
            resolution_note: Description of how the issue was resolved.

        Returns:
            The updated ContinuityIssue record.
            NotFoundResponse if issue_id does not exist.
            GateViolation if the gate is not certified.
        """
        async with get_connection() as conn:
            gate = await check_gate(conn)
            if gate is not None:
                return gate

            await conn.execute(
                """
                UPDATE continuity_issues
                SET is_resolved = 1,
                    resolution_note = ?,
                    updated_at = datetime('now')
                WHERE id = ?
                """,
                (resolution_note, issue_id),
            )
            await conn.commit()

            async with conn.execute(
                "SELECT * FROM continuity_issues WHERE id = ?", (issue_id,)
            ) as cursor:
                row = await cursor.fetchone()

            if row is None:
                return NotFoundResponse(
                    not_found_message=f"Continuity issue {issue_id} not found"
                )

            return ContinuityIssue(**dict(row))
