"""Timeline domain MCP tools.

All 12 timeline tools are registered via the register(mcp) function
pattern.  This module is standalone — it does not modify server.py; wiring
happens in the server module.

Tools: 5 reads (get_pov_positions, get_pov_position, get_event, list_events,
get_travel_segments) + 4 write/validation tools (validate_travel_realism,
upsert_event, upsert_pov_position, log_travel_segment) + 3 delete tools
(delete_event, delete_pov_position, delete_travel_segment).

IMPORTANT: Never use the print function in this module. All logging goes to
stderr via the logging module — using print corrupts the stdio protocol.
"""

import logging

from mcp.server.fastmcp import FastMCP

from novel.mcp.db import get_connection
from novel.mcp.gate import check_gate
from novel.models.shared import GateViolation, NotFoundResponse, ValidationFailure
from novel.models.timeline import Event, PovChronologicalPosition, TravelSegment, TravelValidationResult

logger = logging.getLogger(__name__)


def register(mcp: FastMCP) -> None:
    """Register all 12 timeline tools with the given FastMCP instance.

    Tools are defined as local async functions and decorated with @mcp.tool().
    The FastMCP instance is always the one passed in — never imported globally.

    Most read and write/validation tools call check_gate(conn) and return
    GateViolation if the gate is not certified. Delete tools and
    log_travel_segment do not call check_gate.

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

    # ------------------------------------------------------------------
    # validate_travel_realism (TIME-06)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def validate_travel_realism(
        travel_segment_id: int | None = None,
        character_id: int | None = None,
    ) -> TravelValidationResult | GateViolation:
        """Validate whether travel between locations is realistic given elapsed in-story time.

        Checks one or more travel segments for logical consistency:
        - elapsed_days must be non-null and greater than 0
        - travel_method must be non-null
        - Advisory: walking travel with less than 1 day elapsed is suspicious
        - Advisory: missing from/to location endpoints

        Args:
            travel_segment_id: Validate a single travel segment by its primary key.
            character_id: Validate all travel segments for a character.
              At least one of travel_segment_id or character_id must be provided.

        Returns:
            TravelValidationResult with is_realistic=True/False, list of issues,
            and the segment (if single segment validated), or GateViolation if
            gate is not certified.
        """
        async with get_connection() as conn:
            violation = await check_gate(conn)
            if violation:
                return violation

            if travel_segment_id is None and character_id is None:
                return TravelValidationResult(
                    is_realistic=False,
                    issues=["Must provide travel_segment_id or character_id"],
                    segment=None,
                )

            if travel_segment_id is not None:
                rows = await conn.execute_fetchall(
                    "SELECT * FROM travel_segments WHERE id = ?",
                    (travel_segment_id,),
                )
                if not rows:
                    return TravelValidationResult(
                        is_realistic=False,
                        issues=["Travel segment not found"],
                        segment=None,
                    )
            else:
                rows = await conn.execute_fetchall(
                    "SELECT * FROM travel_segments WHERE character_id = ? ORDER BY id",
                    (character_id,),
                )
                if not rows:
                    return TravelValidationResult(is_realistic=True, issues=[], segment=None)

            def _validate_segment(seg) -> list[str]:
                issues: list[str] = []
                if seg["elapsed_days"] is None or seg["elapsed_days"] <= 0:
                    issues.append("elapsed_days must be non-null and greater than 0")
                if seg["travel_method"] is None:
                    issues.append("travel_method must be non-null")
                if (
                    seg["travel_method"] == "walking"
                    and seg["elapsed_days"] is not None
                    and seg["elapsed_days"] < 1
                ):
                    issues.append("Suspicious: walking travel with less than 1 day elapsed")
                if seg["from_location_id"] is None or seg["to_location_id"] is None:
                    issues.append("Incomplete: missing location endpoint")
                return issues

            if travel_segment_id is not None:
                # Single segment — return with segment attached
                seg_issues = _validate_segment(rows[0])
                return TravelValidationResult(
                    is_realistic=len(seg_issues) == 0,
                    issues=seg_issues,
                    segment=TravelSegment(**dict(rows[0])),
                )
            else:
                # Multiple segments — aggregate issues, no segment attached
                all_issues: list[str] = []
                for row in rows:
                    all_issues.extend(_validate_segment(row))
                return TravelValidationResult(
                    is_realistic=len(all_issues) == 0,
                    issues=all_issues,
                    segment=None,
                )

    # ------------------------------------------------------------------
    # upsert_event (TIME-07)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def upsert_event(
        name: str,
        event_type: str | None = None,
        chapter_id: int | None = None,
        location_id: int | None = None,
        in_story_date: str | None = None,
        duration: str | None = None,
        summary: str | None = None,
        significance: str | None = None,
        notes: str | None = None,
        canon_status: str | None = None,
        event_id: int | None = None,
    ) -> Event | GateViolation:
        """Create or update a timeline event.

        Two-branch upsert pattern:
        - If event_id is None: INSERT and return the new row.
        - If event_id is provided: INSERT ... ON CONFLICT(id) DO UPDATE,
          then SELECT back the updated row.

        Args:
            name: Event name (required).
            event_type: Type of event (e.g. 'conflict', 'revelation', 'travel').
            chapter_id: Chapter in which the event occurs.
            location_id: Location where the event occurs.
            in_story_date: In-story date string for the event.
            duration: Duration description (e.g. '3 days').
            summary: Brief summary of the event.
            significance: Narrative significance notes.
            notes: Freeform notes.
            canon_status: Canon status (e.g. 'draft', 'confirmed').
            event_id: If provided, update the existing event with this ID.

        Returns:
            The created or updated Event row, or GateViolation if gate is
            not certified.
        """
        # Apply SQL DEFAULT values for NOT NULL columns when caller passes None
        effective_event_type = event_type if event_type is not None else "plot"
        effective_canon_status = canon_status if canon_status is not None else "draft"

        async with get_connection() as conn:
            violation = await check_gate(conn)
            if violation:
                return violation

            if event_id is None:
                cursor = await conn.execute(
                    "INSERT INTO events "
                    "(name, event_type, chapter_id, location_id, in_story_date, "
                    "duration, summary, significance, notes, canon_status) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        name,
                        effective_event_type,
                        chapter_id,
                        location_id,
                        in_story_date,
                        duration,
                        summary,
                        significance,
                        notes,
                        effective_canon_status,
                    ),
                )
                new_id = cursor.lastrowid
                await conn.commit()
            else:
                await conn.execute(
                    "INSERT INTO events "
                    "(id, name, event_type, chapter_id, location_id, in_story_date, "
                    "duration, summary, significance, notes, canon_status) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
                    "ON CONFLICT(id) DO UPDATE SET "
                    "name=excluded.name, event_type=excluded.event_type, "
                    "chapter_id=excluded.chapter_id, location_id=excluded.location_id, "
                    "in_story_date=excluded.in_story_date, duration=excluded.duration, "
                    "summary=excluded.summary, significance=excluded.significance, "
                    "notes=excluded.notes, canon_status=excluded.canon_status",
                    (
                        event_id,
                        name,
                        effective_event_type,
                        chapter_id,
                        location_id,
                        in_story_date,
                        duration,
                        summary,
                        significance,
                        notes,
                        effective_canon_status,
                    ),
                )
                new_id = event_id
                await conn.commit()

            rows = await conn.execute_fetchall(
                "SELECT * FROM events WHERE id = ?",
                (new_id,),
            )
            return Event(**dict(rows[0]))

    # ------------------------------------------------------------------
    # upsert_pov_position (TIME-08)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def upsert_pov_position(
        character_id: int,
        chapter_id: int,
        in_story_date: str | None = None,
        day_number: int | None = None,
        location_id: int | None = None,
        notes: str | None = None,
    ) -> PovChronologicalPosition | GateViolation:
        """Create or update a POV character chronological position at a chapter.

        Uses ON CONFLICT(character_id, chapter_id) DO UPDATE — the pair is the
        natural unique key for this table.

        Args:
            character_id: The POV character (required).
            chapter_id: The chapter at which to record the position (required).
            in_story_date: In-story date string at this position.
            day_number: Story day number at this position.
            location_id: Location the character is at in this chapter.
            notes: Freeform notes.

        Returns:
            The created or updated PovChronologicalPosition row, or GateViolation
            if gate is not certified.
        """
        async with get_connection() as conn:
            violation = await check_gate(conn)
            if violation:
                return violation

            await conn.execute(
                "INSERT INTO pov_chronological_position "
                "(character_id, chapter_id, in_story_date, day_number, location_id, notes) "
                "VALUES (?, ?, ?, ?, ?, ?) "
                "ON CONFLICT(character_id, chapter_id) DO UPDATE SET "
                "in_story_date=excluded.in_story_date, day_number=excluded.day_number, "
                "location_id=excluded.location_id, notes=excluded.notes",
                (character_id, chapter_id, in_story_date, day_number, location_id, notes),
            )
            await conn.commit()

            rows = await conn.execute_fetchall(
                "SELECT * FROM pov_chronological_position "
                "WHERE character_id = ? AND chapter_id = ?",
                (character_id, chapter_id),
            )
            return PovChronologicalPosition(**dict(rows[0]))

    # ------------------------------------------------------------------
    # log_travel_segment (TIME-09)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def log_travel_segment(
        character_id: int,
        from_location_id: int | None = None,
        to_location_id: int | None = None,
        start_chapter_id: int | None = None,
        end_chapter_id: int | None = None,
        start_event_id: int | None = None,
        elapsed_days: int | None = None,
        travel_method: str | None = None,
        notes: str | None = None,
    ) -> TravelSegment | NotFoundResponse | ValidationFailure:
        """Append a travel segment record for a character.

        Append-only INSERT — travel_segments has no UNIQUE constraint beyond
        the primary key, so each call always inserts a new row. Multiple travel
        segments per character are expected and valid.

        Pre-checks that character_id exists in characters. If start_chapter_id
        is provided, also verifies it exists in chapters.

        Not gate-gated — travel segment logging does not require prose-phase
        certification.

        Args:
            character_id: FK to characters — the travelling character (required).
            from_location_id: FK to locations — starting location (optional).
            to_location_id: FK to locations — destination location (optional).
            start_chapter_id: FK to chapters — chapter where travel begins
                              (optional).
            end_chapter_id: FK to chapters — chapter where travel ends
                            (optional).
            start_event_id: FK to events — event that triggers this travel
                            (optional).
            elapsed_days: Number of in-story days the journey takes (optional).
            travel_method: Mode of travel — e.g. "walking", "horse", "ship"
                           (optional).
            notes: Free-form notes about the journey (optional).

        Returns:
            The newly created TravelSegment row.
            NotFoundResponse if character_id or start_chapter_id does not exist.
            ValidationFailure on database error.
        """
        async with get_connection() as conn:
            char = await conn.execute_fetchall(
                "SELECT id FROM characters WHERE id = ?", (character_id,)
            )
            if not char:
                return NotFoundResponse(
                    not_found_message=f"Character {character_id} not found"
                )

            if start_chapter_id is not None:
                chapter = await conn.execute_fetchall(
                    "SELECT id FROM chapters WHERE id = ?", (start_chapter_id,)
                )
                if not chapter:
                    return NotFoundResponse(
                        not_found_message=f"Chapter {start_chapter_id} not found"
                    )

            try:
                cursor = await conn.execute(
                    "INSERT INTO travel_segments "
                    "(character_id, from_location_id, to_location_id, "
                    "start_chapter_id, end_chapter_id, start_event_id, "
                    "elapsed_days, travel_method, notes) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        character_id,
                        from_location_id,
                        to_location_id,
                        start_chapter_id,
                        end_chapter_id,
                        start_event_id,
                        elapsed_days,
                        travel_method,
                        notes,
                    ),
                )
                new_id = cursor.lastrowid
                await conn.commit()
                row = await conn.execute_fetchall(
                    "SELECT * FROM travel_segments WHERE id = ?", (new_id,)
                )
                return TravelSegment(**dict(row[0]))
            except Exception as exc:
                logger.error("log_travel_segment failed: %s", exc)
                return ValidationFailure(is_valid=False, errors=[str(exc)])

    # ------------------------------------------------------------------
    # delete_event
    # ------------------------------------------------------------------

    @mcp.tool()
    async def delete_event(
        event_id: int,
    ) -> NotFoundResponse | ValidationFailure | dict:
        """Delete a timeline event by ID if it is not referenced by any FK children.

        events is referenced by event_participants and event_artifacts. If either
        table holds a row referencing this event, the DELETE will be blocked by
        the FOREIGN KEY constraint and a ValidationFailure is returned instead.

        Does not call check_gate — delete tools follow no-gate pattern.

        Args:
            event_id: Primary key of the event to delete.

        Returns:
            {"deleted": True, "id": event_id} on success,
            NotFoundResponse if the event does not exist,
            ValidationFailure if a FK constraint prevents deletion.
        """
        async with get_connection() as conn:
            rows = await conn.execute_fetchall(
                "SELECT id FROM events WHERE id = ?", (event_id,)
            )
            if not rows:
                logger.debug("delete_event: %d not found", event_id)
                return NotFoundResponse(
                    not_found_message=f"Event {event_id} not found"
                )
            try:
                await conn.execute(
                    "DELETE FROM events WHERE id = ?", (event_id,)
                )
                await conn.commit()
                return {"deleted": True, "id": event_id}
            except Exception as exc:
                logger.error("delete_event failed: %s", exc)
                return ValidationFailure(is_valid=False, errors=[str(exc)])

    # ------------------------------------------------------------------
    # delete_pov_position
    # ------------------------------------------------------------------

    @mcp.tool()
    async def delete_pov_position(
        pov_position_id: int,
    ) -> NotFoundResponse | ValidationFailure | dict:
        """Delete a POV chronological position row by its primary key.

        Uses FK-safe try/except pattern for safety. Looks up the row by the
        integer primary key (id column) of the pov_chronological_position table.

        Does not call check_gate — delete tools follow no-gate pattern.

        Args:
            pov_position_id: Primary key (id) of the pov_chronological_position
                row to delete.

        Returns:
            {"deleted": True, "id": pov_position_id} on success,
            NotFoundResponse if the row does not exist,
            ValidationFailure if a FK constraint prevents deletion.
        """
        async with get_connection() as conn:
            rows = await conn.execute_fetchall(
                "SELECT id FROM pov_chronological_position WHERE id = ?",
                (pov_position_id,),
            )
            if not rows:
                logger.debug("delete_pov_position: %d not found", pov_position_id)
                return NotFoundResponse(
                    not_found_message=f"POV position {pov_position_id} not found"
                )
            try:
                await conn.execute(
                    "DELETE FROM pov_chronological_position WHERE id = ?",
                    (pov_position_id,),
                )
                await conn.commit()
                return {"deleted": True, "id": pov_position_id}
            except Exception as exc:
                logger.error("delete_pov_position failed: %s", exc)
                return ValidationFailure(is_valid=False, errors=[str(exc)])

    # ------------------------------------------------------------------
    # delete_travel_segment
    # ------------------------------------------------------------------

    @mcp.tool()
    async def delete_travel_segment(
        travel_segment_id: int,
    ) -> NotFoundResponse | dict:
        """Delete a travel segment by ID.

        travel_segments is a log-style table with no FK children. Uses the
        simpler pre-existence check only (no try/except needed).

        Does not call check_gate — delete tools follow no-gate pattern.

        Args:
            travel_segment_id: Primary key of the travel segment to delete.

        Returns:
            {"deleted": True, "id": travel_segment_id} on success,
            NotFoundResponse if the travel segment does not exist.
        """
        async with get_connection() as conn:
            rows = await conn.execute_fetchall(
                "SELECT id FROM travel_segments WHERE id = ?",
                (travel_segment_id,),
            )
            if not rows:
                logger.debug(
                    "delete_travel_segment: %d not found", travel_segment_id
                )
                return NotFoundResponse(
                    not_found_message=f"Travel segment {travel_segment_id} not found"
                )
            await conn.execute(
                "DELETE FROM travel_segments WHERE id = ?", (travel_segment_id,)
            )
            await conn.commit()
            return {"deleted": True, "id": travel_segment_id}
