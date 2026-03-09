"""Knowledge domain MCP tools.

All 5 knowledge tools are registered via the register(mcp) function pattern.
This module is standalone — it does not modify server.py; wiring happens in
the server module.

IMPORTANT: Never use the print function in this module. All logging goes to
stderr via the logging module — using print corrupts the stdio protocol.
"""

import logging

from mcp.server.fastmcp import FastMCP

from novel.mcp.db import get_connection
from novel.mcp.gate import check_gate
from novel.models.canon import DramaticIronyEntry, ReaderInformationState, ReaderReveal
from novel.models.shared import GateViolation, NotFoundResponse, ValidationFailure

logger = logging.getLogger(__name__)


def register(mcp: FastMCP) -> None:
    """Register all 7 knowledge domain tools with the given FastMCP instance.

    Tools are defined as local async functions and decorated with @mcp.tool().
    The FastMCP instance is always the one passed in — never imported globally.

    All tools are prose-phase tools — each calls check_gate(conn) at the top
    before any DB logic and returns GateViolation if the gate is not certified.

    Args:
        mcp: The FastMCP server instance to register tools against.
    """

    # ------------------------------------------------------------------
    # get_reader_state (KNOW-01)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def get_reader_state(
        chapter_id: int,
    ) -> list[ReaderInformationState] | GateViolation:
        """Retrieve cumulative reader information state up to a given chapter.

        Uses cumulative semantics: returns all reader_information_states rows
        where chapter_id <= the requested chapter_id. This gives Claude a
        complete snapshot of what readers know at any story point in a single
        call — not just what was revealed at that exact chapter.

        Results are ordered by chapter_id ASC so earlier reveals appear first.

        Args:
            chapter_id: The chapter boundary (inclusive). All reader state
                        entries from chapter 1 through this chapter are
                        returned.

        Returns:
            List of ReaderInformationState records (may be empty if no reader
            state exists up to this chapter), or GateViolation if gate is not
            certified.
        """
        async with get_connection() as conn:
            violation = await check_gate(conn)
            if violation:
                return violation

            rows = await conn.execute_fetchall(
                "SELECT * FROM reader_information_states "
                "WHERE chapter_id <= ? "
                "ORDER BY chapter_id ASC",
                (chapter_id,),
            )
            return [ReaderInformationState(**dict(r)) for r in rows]

    # ------------------------------------------------------------------
    # get_dramatic_irony_inventory (KNOW-02)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def get_dramatic_irony_inventory(
        include_resolved: bool = False,
        chapter_id: int | None = None,
    ) -> list[DramaticIronyEntry] | GateViolation:
        """Retrieve the dramatic irony inventory, unresolved by default.

        Returns dramatic irony entries filtered by resolution status and
        optionally scoped to a specific chapter.

        Args:
            include_resolved: If False (default), only unresolved entries are
                              returned. If True, all entries are returned.
            chapter_id: Optional chapter filter. If provided, only entries
                        created at that specific chapter are returned.

        Returns:
            List of DramaticIronyEntry records ordered by created_at ASC
            (may be empty), or GateViolation if gate is not certified.
        """
        async with get_connection() as conn:
            violation = await check_gate(conn)
            if violation:
                return violation

            conditions: list[str] = []
            params: list = []

            if not include_resolved:
                conditions.append("resolved = FALSE")
            if chapter_id is not None:
                conditions.append("chapter_id = ?")
                params.append(chapter_id)

            sql = "SELECT * FROM dramatic_irony_inventory"
            if conditions:
                sql += " WHERE " + " AND ".join(conditions)
            sql += " ORDER BY created_at ASC"

            rows = await conn.execute_fetchall(sql, params)
            return [DramaticIronyEntry(**dict(r)) for r in rows]

    # ------------------------------------------------------------------
    # get_reader_reveals (KNOW-03)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def get_reader_reveals(
        chapter_id: int | None = None,
    ) -> list[ReaderReveal] | GateViolation:
        """Retrieve planned and actual reader reveals.

        Returns reader reveal entries, optionally filtered to a specific
        chapter. Both planned_reveal and actual_reveal may be null for
        entries that have been planned but not yet written.

        Args:
            chapter_id: Optional chapter filter. If provided, only reveals
                        associated with that chapter are returned.

        Returns:
            List of ReaderReveal records ordered by created_at ASC (may be
            empty), or GateViolation if gate is not certified.
        """
        async with get_connection() as conn:
            violation = await check_gate(conn)
            if violation:
                return violation

            sql = "SELECT * FROM reader_reveals"
            params: list = []
            if chapter_id is not None:
                sql += " WHERE chapter_id = ?"
                params.append(chapter_id)
            sql += " ORDER BY created_at ASC"

            rows = await conn.execute_fetchall(sql, params)
            return [ReaderReveal(**dict(r)) for r in rows]

    # ------------------------------------------------------------------
    # upsert_reader_state (KNOW-04)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def upsert_reader_state(
        chapter_id: int,
        domain: str,
        information: str,
        reader_state_id: int | None = None,
        revealed_how: str | None = None,
        notes: str | None = None,
    ) -> ReaderInformationState | GateViolation:
        """Create or update a reader information state entry.

        reader_information_states has a UNIQUE(chapter_id, domain) constraint.
        Two branches are used:

        - None reader_state_id: INSERT with ON CONFLICT(chapter_id, domain)
          DO UPDATE — creates or updates by (chapter_id, domain) key.
          cursor.lastrowid returns the existing row id on conflict (correct
          SQLite behavior).
        - Provided reader_state_id: INSERT with ON CONFLICT(id) DO UPDATE —
          updates the specific row by primary key.

        After either branch, the row is SELECT-ed back by id and returned.

        Args:
            chapter_id: The chapter this reader state entry is associated with.
            domain: The knowledge domain (e.g. 'magic', 'character', 'plot').
            information: The information state description.
            reader_state_id: If provided, upsert by primary key; otherwise
                             upsert by (chapter_id, domain) unique key.
            revealed_how: Optional description of how this was revealed to
                          the reader.
            notes: Optional freeform notes.

        Returns:
            The created or updated ReaderInformationState row, or GateViolation
            if gate is not certified.
        """
        async with get_connection() as conn:
            violation = await check_gate(conn)
            if violation:
                return violation

            if reader_state_id is None:
                # None-id branch: upsert by (chapter_id, domain) unique key
                cursor = await conn.execute(
                    "INSERT INTO reader_information_states "
                    "(chapter_id, domain, information, revealed_how, notes) "
                    "VALUES (?, ?, ?, ?, ?) "
                    "ON CONFLICT(chapter_id, domain) DO UPDATE SET "
                    "information = excluded.information, "
                    "revealed_how = excluded.revealed_how, "
                    "notes = excluded.notes",
                    (chapter_id, domain, information, revealed_how, notes),
                )
                row_id = cursor.lastrowid
            else:
                # Provided-id branch: upsert by primary key
                cursor = await conn.execute(
                    "INSERT INTO reader_information_states "
                    "(id, chapter_id, domain, information, revealed_how, notes) "
                    "VALUES (?, ?, ?, ?, ?, ?) "
                    "ON CONFLICT(id) DO UPDATE SET "
                    "information = excluded.information, "
                    "revealed_how = excluded.revealed_how, "
                    "notes = excluded.notes",
                    (reader_state_id, chapter_id, domain, information, revealed_how, notes),
                )
                row_id = reader_state_id

            await conn.commit()

            rows = await conn.execute_fetchall(
                "SELECT * FROM reader_information_states WHERE id = ?",
                (row_id,),
            )
            return ReaderInformationState(**dict(rows[0]))

    # ------------------------------------------------------------------
    # log_dramatic_irony (KNOW-05)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def log_dramatic_irony(
        chapter_id: int,
        reader_knows: str,
        character_doesnt_know: str,
        character_id: int | None = None,
        irony_type: str = "situational",
        tension_level: int = 5,
        resolved_chapter_id: int | None = None,
        notes: str | None = None,
    ) -> DramaticIronyEntry | GateViolation:
        """Log a new dramatic irony entry (append-only).

        Appends a new entry to the dramatic_irony_inventory. This is
        append-only — no ON CONFLICT clause. Each call creates a distinct
        dramatic irony record. The resolved field defaults to FALSE via the
        DB schema default.

        Args:
            chapter_id: The chapter where this dramatic irony begins.
            reader_knows: Description of what the reader knows.
            character_doesnt_know: Description of what the character does
                                   not know (creating the irony).
            character_id: Optional FK to the character who doesn't know.
            irony_type: Type of dramatic irony (default: 'situational').
                        Other values: 'tragic', 'comic'.
            tension_level: Tension intensity 1–10 (default: 5).
            resolved_chapter_id: Optional chapter where the irony is
                                 resolved (if already known at creation).
            notes: Optional freeform notes.

        Returns:
            The newly created DramaticIronyEntry row, or GateViolation if
            gate is not certified.
        """
        async with get_connection() as conn:
            violation = await check_gate(conn)
            if violation:
                return violation

            cursor = await conn.execute(
                "INSERT INTO dramatic_irony_inventory "
                "(chapter_id, reader_knows, character_id, character_doesnt_know, "
                "irony_type, tension_level, resolved_chapter_id, notes) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    chapter_id,
                    reader_knows,
                    character_id,
                    character_doesnt_know,
                    irony_type,
                    tension_level,
                    resolved_chapter_id,
                    notes,
                ),
            )
            new_id = cursor.lastrowid
            await conn.commit()

            rows = await conn.execute_fetchall(
                "SELECT * FROM dramatic_irony_inventory WHERE id = ?",
                (new_id,),
            )
            return DramaticIronyEntry(**dict(rows[0]))

    # ------------------------------------------------------------------
    # delete_reader_state (KNOW-06)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def delete_reader_state(
        reader_state_id: int,
    ) -> GateViolation | NotFoundResponse | ValidationFailure | dict:
        """Delete a reader information state entry by ID.

        Requires gate certification. Idempotent: returns NotFoundResponse if
        absent. reader_information_states may have FK children (reader_reveals
        references reader_information_state_id) — FK-safe try/except pattern
        used to handle IntegrityError if children exist.

        Args:
            reader_state_id: Primary key of the reader state entry to delete.

        Returns:
            {"deleted": True, "id": N} on success.
            GateViolation if the gate is not certified.
            NotFoundResponse if the reader state does not exist.
            ValidationFailure if the delete violates a FK constraint.
        """
        async with get_connection() as conn:
            gate = await check_gate(conn)
            if gate is not None:
                return gate

            rows = await conn.execute_fetchall(
                "SELECT id FROM reader_information_states WHERE id = ?",
                (reader_state_id,),
            )
            if not rows:
                return NotFoundResponse(
                    not_found_message=f"Reader state {reader_state_id} not found"
                )

            try:
                await conn.execute(
                    "DELETE FROM reader_information_states WHERE id = ?",
                    (reader_state_id,),
                )
                await conn.commit()
                return {"deleted": True, "id": reader_state_id}
            except Exception as exc:
                logger.error("delete_reader_state failed: %s", exc)
                return ValidationFailure(is_valid=False, errors=[str(exc)])

    # ------------------------------------------------------------------
    # delete_dramatic_irony (KNOW-07)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def delete_dramatic_irony(
        dramatic_irony_id: int,
    ) -> GateViolation | NotFoundResponse | dict:
        """Delete a dramatic irony entry by ID.

        Requires gate certification. Idempotent: returns NotFoundResponse if
        absent. dramatic_irony_inventory is a log table with no FK children —
        no IntegrityError expected.

        Args:
            dramatic_irony_id: Primary key of the dramatic irony entry to delete.

        Returns:
            {"deleted": True, "id": N} on success.
            GateViolation if the gate is not certified.
            NotFoundResponse if the dramatic irony entry does not exist.
        """
        async with get_connection() as conn:
            gate = await check_gate(conn)
            if gate is not None:
                return gate

            rows = await conn.execute_fetchall(
                "SELECT id FROM dramatic_irony_inventory WHERE id = ?",
                (dramatic_irony_id,),
            )
            if not rows:
                return NotFoundResponse(
                    not_found_message=f"Dramatic irony entry {dramatic_irony_id} not found"
                )

            await conn.execute(
                "DELETE FROM dramatic_irony_inventory WHERE id = ?",
                (dramatic_irony_id,),
            )
            await conn.commit()
            return {"deleted": True, "id": dramatic_irony_id}
