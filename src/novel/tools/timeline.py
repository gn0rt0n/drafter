"""Timeline domain MCP tools.

All 5 timeline read tools are registered via the register(mcp) function
pattern.  This module is standalone — it does not modify server.py; wiring
happens in the server module.

IMPORTANT: Never use the print function in this module. All logging goes to
stderr via the logging module — using print corrupts the stdio protocol.
"""

import logging

from mcp.server.fastmcp import FastMCP

from novel.mcp.db import get_connection
from novel.mcp.gate import check_gate
from novel.models.shared import GateViolation, NotFoundResponse
from novel.models.timeline import Event, PovChronologicalPosition, TravelSegment

logger = logging.getLogger(__name__)


def register(mcp: FastMCP) -> None:
    """Register all 5 timeline read tools with the given FastMCP instance.

    Tools are defined as local async functions and decorated with @mcp.tool().
    The FastMCP instance is always the one passed in — never imported globally.

    All tools are prose-phase tools — each calls check_gate(conn) at the top
    before any DB logic and returns GateViolation if the gate is not certified.

    Args:
        mcp: The FastMCP server instance to register tools against.
    """

    # ------------------------------------------------------------------
    # get_pov_positions (TIME-01)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def get_pov_positions(
        chapter_id: int,
    ) -> list[PovChronologicalPosition] | GateViolation:
        """Retrieve all POV character chronological positions at a given chapter.

        Returns all rows in pov_chronological_position where chapter_id
        matches, ordered by character_id ASC. Returns an empty list if no
        POV positions have been recorded for the chapter.

        Args:
            chapter_id: The chapter to look up positions for.

        Returns:
            List of PovChronologicalPosition records (may be empty), or
            GateViolation if gate is not certified.
        """
        async with get_connection() as conn:
            violation = await check_gate(conn)
            if violation:
                return violation

            rows = await conn.execute_fetchall(
                "SELECT * FROM pov_chronological_position "
                "WHERE chapter_id = ? ORDER BY character_id",
                (chapter_id,),
            )
            return [PovChronologicalPosition(**dict(r)) for r in rows]

    # ------------------------------------------------------------------
    # get_pov_position (TIME-02)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def get_pov_position(
        character_id: int,
        chapter_id: int,
    ) -> PovChronologicalPosition | NotFoundResponse | GateViolation:
        """Retrieve a specific POV character's chronological position at a chapter.

        Looks up the unique row for (character_id, chapter_id) in
        pov_chronological_position — the table has a UNIQUE constraint on
        this pair.

        Args:
            character_id: The character whose position to retrieve.
            chapter_id: The chapter at which to retrieve the position.

        Returns:
            PovChronologicalPosition if the record exists, NotFoundResponse
            if not found, or GateViolation if gate is not certified.
        """
        async with get_connection() as conn:
            violation = await check_gate(conn)
            if violation:
                return violation

            rows = await conn.execute_fetchall(
                "SELECT * FROM pov_chronological_position "
                "WHERE character_id = ? AND chapter_id = ?",
                (character_id, chapter_id),
            )
            if not rows:
                return NotFoundResponse(
                    not_found_message=(
                        f"POV position for character {character_id} "
                        f"at chapter {chapter_id} not found"
                    )
                )
            return PovChronologicalPosition(**dict(rows[0]))

    # ------------------------------------------------------------------
    # get_event (TIME-03)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def get_event(
        event_id: int,
    ) -> Event | NotFoundResponse | GateViolation:
        """Retrieve a single timeline event by its primary key.

        Args:
            event_id: Primary key of the events row to retrieve.

        Returns:
            Event if found, NotFoundResponse if the event_id does not exist,
            or GateViolation if gate is not certified.
        """
        async with get_connection() as conn:
            violation = await check_gate(conn)
            if violation:
                return violation

            rows = await conn.execute_fetchall(
                "SELECT * FROM events WHERE id = ?",
                (event_id,),
            )
            if not rows:
                return NotFoundResponse(
                    not_found_message=f"Event {event_id} not found"
                )
            return Event(**dict(rows[0]))

    # ------------------------------------------------------------------
    # list_events (TIME-04)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def list_events(
        chapter_id: int | None = None,
        start_chapter: int | None = None,
        end_chapter: int | None = None,
    ) -> list[Event] | GateViolation:
        """List timeline events, optionally filtered by chapter or chapter range.

        Filtering rules (in priority order):
        - If chapter_id is provided: returns events for that exact chapter only.
        - Else if start_chapter or end_chapter provided: returns events in the
          chapter range (both bounds inclusive, either bound may be omitted).
        - If no filters provided: returns all events.

        Results are always ordered by chapter_id ASC, id ASC.

        Args:
            chapter_id: Exact chapter to filter by (takes priority over range).
            start_chapter: Lower bound of chapter range (inclusive).
            end_chapter: Upper bound of chapter range (inclusive).

        Returns:
            List of Event records (may be empty), or GateViolation if gate
            is not certified.
        """
        async with get_connection() as conn:
            violation = await check_gate(conn)
            if violation:
                return violation

            conditions: list[str] = []
            params: list = []

            if chapter_id is not None:
                conditions.append("chapter_id = ?")
                params.append(chapter_id)
            else:
                if start_chapter is not None:
                    conditions.append("chapter_id >= ?")
                    params.append(start_chapter)
                if end_chapter is not None:
                    conditions.append("chapter_id <= ?")
                    params.append(end_chapter)

            sql = "SELECT * FROM events"
            if conditions:
                sql += " WHERE " + " AND ".join(conditions)
            sql += " ORDER BY chapter_id ASC, id ASC"

            rows = await conn.execute_fetchall(sql, params)
            return [Event(**dict(r)) for r in rows]

    # ------------------------------------------------------------------
    # get_travel_segments (TIME-05)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def get_travel_segments(
        character_id: int,
    ) -> list[TravelSegment] | GateViolation:
        """Retrieve all travel segments for a character, ordered chronologically.

        Returns an empty list (not NotFoundResponse) when no travel segments
        exist for the character — this is a valid state for non-travelling
        characters.

        Args:
            character_id: The character whose travel segments to retrieve.

        Returns:
            List of TravelSegment records ordered by start_chapter_id ASC,
            id ASC (may be empty), or GateViolation if gate is not certified.
        """
        async with get_connection() as conn:
            violation = await check_gate(conn)
            if violation:
                return violation

            rows = await conn.execute_fetchall(
                "SELECT * FROM travel_segments "
                "WHERE character_id = ? ORDER BY start_chapter_id ASC, id ASC",
                (character_id,),
            )
            return [TravelSegment(**dict(r)) for r in rows]
