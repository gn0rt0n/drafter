"""Arc domain MCP tools.

All 12 arc tools are registered via the register(mcp) function pattern.
This module is standalone — it does not modify server.py; wiring happens in
the server module.

IMPORTANT: Never use the print function in this module. All logging goes to
stderr via the logging module — using print corrupts the stdio protocol.
"""

import logging

from mcp.server.fastmcp import FastMCP

from novel.mcp.db import get_connection
from novel.models.arcs import ArcHealthLog, CharacterArc, ChekhovGun, SubplotTouchpoint
from novel.models.shared import NotFoundResponse, ValidationFailure

logger = logging.getLogger(__name__)


def register(mcp: FastMCP) -> None:
    """Register all 12 arc domain tools with the given FastMCP instance.

    Tools are defined as local async functions and decorated with @mcp.tool().
    The FastMCP instance is always the one passed in — never imported globally.

    Args:
        mcp: The FastMCP server instance to register tools against.
    """

    # ------------------------------------------------------------------
    # get_chekovs_guns (PLOT-03)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def get_chekovs_guns(
        status: str | None = None,
        unresolved_only: bool = False,
    ) -> list[ChekhovGun]:
        """Retrieve Chekhov's gun entries from the registry.

        When unresolved_only is True, returns only planted guns that have no
        payoff chapter assigned yet. This takes precedence over the status
        filter.

        Args:
            status: Optional status filter (e.g. "planted", "fired"). Ignored
                    when unresolved_only is True.
            unresolved_only: When True, return only guns with status="planted"
                             AND payoff_chapter_id IS NULL. Takes precedence
                             over the status parameter.

        Returns:
            List of ChekhovGun records ordered by id (may be empty).
        """
        async with get_connection() as conn:
            if unresolved_only:
                rows = await conn.execute_fetchall(
                    "SELECT * FROM chekovs_gun_registry "
                    "WHERE status = 'planted' AND payoff_chapter_id IS NULL ORDER BY id",
                    [],
                )
            elif status is not None:
                rows = await conn.execute_fetchall(
                    "SELECT * FROM chekovs_gun_registry WHERE status = ? ORDER BY id",
                    (status,),
                )
            else:
                rows = await conn.execute_fetchall(
                    "SELECT * FROM chekovs_gun_registry ORDER BY id",
                    [],
                )
            return [ChekhovGun(**dict(r)) for r in rows]

    # ------------------------------------------------------------------
    # get_arc (PLOT-04)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def get_arc(
        arc_id: int | None = None,
        character_id: int | None = None,
    ) -> CharacterArc | list[CharacterArc] | NotFoundResponse | ValidationFailure:
        """Retrieve character arc(s) by arc_id or character_id.

        Dual-mode lookup:
        - If arc_id is provided, returns a single CharacterArc (arc_id takes
          precedence even if character_id is also given).
        - If only character_id is provided, returns all arcs for that character
          as a list (may be empty).
        - If neither is provided, returns ValidationFailure.

        Args:
            arc_id: Primary key of a specific arc to retrieve (takes precedence).
            character_id: Character whose arcs to retrieve (used when arc_id
                          is not provided).

        Returns:
            Single CharacterArc (arc_id path), list[CharacterArc] (character_id
            path), NotFoundResponse if the arc_id is not found, or
            ValidationFailure if neither parameter is provided.
        """
        if arc_id is None and character_id is None:
            return ValidationFailure(
                is_valid=False,
                errors=["At least one of arc_id or character_id must be provided"],
            )
        async with get_connection() as conn:
            if arc_id is not None:
                # arc_id takes precedence even if character_id also provided
                rows = await conn.execute_fetchall(
                    "SELECT * FROM character_arcs WHERE id = ?",
                    (arc_id,),
                )
                if not rows:
                    return NotFoundResponse(not_found_message=f"Arc {arc_id} not found")
                return CharacterArc(**dict(rows[0]))
            else:
                rows = await conn.execute_fetchall(
                    "SELECT * FROM character_arcs WHERE character_id = ? ORDER BY id",
                    (character_id,),
                )
                return [CharacterArc(**dict(r)) for r in rows]

    # ------------------------------------------------------------------
    # get_arc_health (PLOT-05)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def get_arc_health(
        character_id: int,
        arc_id: int | None = None,
    ) -> list[ArcHealthLog]:
        """Retrieve arc health log entries for a character, optionally filtered to one arc.

        JOINs arc_health_log to character_arcs to filter by character_id, since
        arc_health_log has no direct character_id column. Returns an empty list
        when no health log entries exist — this is a valid state (health logging
        is optional).

        Args:
            character_id: Primary key of the character whose arc health to retrieve.
            arc_id: Optional arc filter — when provided, only returns entries for
                    that specific arc belonging to the character.

        Returns:
            List of ArcHealthLog records ordered by chapter_id ascending (may
            be empty).
        """
        async with get_connection() as conn:
            if arc_id is not None:
                rows = await conn.execute_fetchall(
                    """SELECT ahl.*
                       FROM arc_health_log ahl
                       JOIN character_arcs ca ON ca.id = ahl.arc_id
                       WHERE ca.character_id = ? AND ahl.arc_id = ?
                       ORDER BY ahl.chapter_id ASC""",
                    (character_id, arc_id),
                )
            else:
                rows = await conn.execute_fetchall(
                    """SELECT ahl.*
                       FROM arc_health_log ahl
                       JOIN character_arcs ca ON ca.id = ahl.arc_id
                       WHERE ca.character_id = ?
                       ORDER BY ahl.chapter_id ASC""",
                    (character_id,),
                )
            return [ArcHealthLog(**dict(r)) for r in rows]

    # ------------------------------------------------------------------
    # get_subplot_touchpoint_gaps (PLOT-06)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def get_subplot_touchpoint_gaps(
        threshold_chapters: int = 5,
    ) -> list[dict]:
        """Return active subplots that are overdue for a touchpoint.

        A subplot is overdue when either:
        - It has never appeared in subplot_touchpoint_log (NULL last touchpoint), or
        - The current max chapter_id minus the last touchpoint chapter_id exceeds
          threshold_chapters.

        Only applies to plot_threads with thread_type='subplot' and status='active'.

        Args:
            threshold_chapters: Number of chapters without a touchpoint before a
                                subplot is considered overdue (default: 5).

        Returns:
            List of dicts with keys: plot_thread_id, name,
            last_touchpoint_chapter_id, chapters_since_touchpoint. Ordered by
            chapters_since_touchpoint DESC (NULLs last). Empty list when no
            active subplots exist or none exceed the threshold.
        """
        async with get_connection() as conn:
            max_row = await conn.execute_fetchall(
                "SELECT MAX(id) AS max_id FROM chapters",
                [],
            )
            max_chapter_id = max_row[0]["max_id"] or 0

            rows = await conn.execute_fetchall(
                """SELECT
                       pt.id AS plot_thread_id,
                       pt.name,
                       MAX(stl.chapter_id) AS last_touchpoint_chapter_id,
                       CASE
                           WHEN MAX(stl.chapter_id) IS NULL THEN NULL
                           ELSE (? - MAX(stl.chapter_id))
                       END AS chapters_since_touchpoint
                   FROM plot_threads pt
                   LEFT JOIN subplot_touchpoint_log stl ON stl.plot_thread_id = pt.id
                   WHERE pt.thread_type = 'subplot'
                     AND pt.status = 'active'
                   GROUP BY pt.id, pt.name
                   HAVING MAX(stl.chapter_id) IS NULL
                       OR (? - MAX(stl.chapter_id)) > ?
                   ORDER BY chapters_since_touchpoint DESC NULLS LAST""",
                (max_chapter_id, max_chapter_id, threshold_chapters),
            )
            return [dict(r) for r in rows]

    # ------------------------------------------------------------------
    # upsert_chekov (PLOT-08)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def upsert_chekov(
        chekov_id: int | None,
        name: str,
        description: str,
        planted_chapter_id: int | None = None,
        planted_scene_id: int | None = None,
        payoff_chapter_id: int | None = None,
        payoff_scene_id: int | None = None,
        status: str | None = None,
        notes: str | None = None,
        canon_status: str | None = None,
    ) -> ChekhovGun | ValidationFailure:
        """Create or update a Chekhov's gun entry in the registry.

        Two-branch upsert because chekovs_gun_registry has no UNIQUE constraint
        beyond the primary key (no ON CONFLICT(name) possible):
        - chekov_id=None: plain INSERT, returns new row by lastrowid.
        - chekov_id provided: ON CONFLICT(id) DO UPDATE, returns updated row.

        Args:
            chekov_id: Existing gun id to update, or None to create a new entry.
            name: Name/label for the Chekhov's gun element (required).
            description: Description of the planted element (required).
            planted_chapter_id: Chapter where the element was planted (optional).
            planted_scene_id: Scene where the element was planted (optional).
            payoff_chapter_id: Chapter where the element pays off (optional).
            payoff_scene_id: Scene where the element pays off (optional).
            status: Status of the element — e.g. "planted", "fired" (default:
                    "planted").
            notes: Free-form notes (optional).
            canon_status: Canon status — e.g. "draft", "canon" (default: "draft").

        Returns:
            The created or updated ChekhovGun record, or ValidationFailure on
            database error.
        """
        async with get_connection() as conn:
            try:
                if chekov_id is None:
                    cursor = await conn.execute(
                        """INSERT INTO chekovs_gun_registry
                               (name, description, planted_chapter_id, planted_scene_id,
                                payoff_chapter_id, payoff_scene_id, status, notes, canon_status,
                                updated_at)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))""",
                        (
                            name,
                            description,
                            planted_chapter_id,
                            planted_scene_id,
                            payoff_chapter_id,
                            payoff_scene_id,
                            status or "planted",
                            notes,
                            canon_status or "draft",
                        ),
                    )
                    new_id = cursor.lastrowid
                    await conn.commit()
                    row = await conn.execute_fetchall(
                        "SELECT * FROM chekovs_gun_registry WHERE id = ?",
                        (new_id,),
                    )
                else:
                    await conn.execute(
                        """INSERT INTO chekovs_gun_registry
                               (id, name, description, planted_chapter_id, planted_scene_id,
                                payoff_chapter_id, payoff_scene_id, status, notes, canon_status,
                                updated_at)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                           ON CONFLICT(id) DO UPDATE SET
                               name=excluded.name,
                               description=excluded.description,
                               planted_chapter_id=excluded.planted_chapter_id,
                               planted_scene_id=excluded.planted_scene_id,
                               payoff_chapter_id=excluded.payoff_chapter_id,
                               payoff_scene_id=excluded.payoff_scene_id,
                               status=excluded.status,
                               notes=excluded.notes,
                               canon_status=excluded.canon_status,
                               updated_at=datetime('now')""",
                        (
                            chekov_id,
                            name,
                            description,
                            planted_chapter_id,
                            planted_scene_id,
                            payoff_chapter_id,
                            payoff_scene_id,
                            status or "planted",
                            notes,
                            canon_status or "draft",
                        ),
                    )
                    await conn.commit()
                    row = await conn.execute_fetchall(
                        "SELECT * FROM chekovs_gun_registry WHERE id = ?",
                        (chekov_id,),
                    )
                return ChekhovGun(**dict(row[0]))
            except Exception as exc:
                logger.error("upsert_chekov failed: %s", exc)
                return ValidationFailure(is_valid=False, errors=[str(exc)])

    # ------------------------------------------------------------------
    # log_arc_health (PLOT-09)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def log_arc_health(
        arc_id: int,
        chapter_id: int,
        health_status: str = "on-track",
        notes: str | None = None,
    ) -> ArcHealthLog | ValidationFailure:
        """Append an arc health log entry for a character arc at a chapter.

        Append-only INSERT — arc_health_log has no UNIQUE constraint, so each
        call always inserts a new row (same pattern as magic_use_log). Multiple
        health snapshots per arc/chapter are valid.

        Args:
            arc_id: FK to character_arcs — the arc being assessed (required).
            chapter_id: FK to chapters — the chapter at which the assessment is
                        recorded (required).
            health_status: Health status of the arc — e.g. "on-track",
                           "at-risk", "derailed" (default: "on-track").
            notes: Free-form notes about the arc's health at this chapter
                   (optional).

        Returns:
            The newly created ArcHealthLog row, or ValidationFailure on
            database error.
        """
        async with get_connection() as conn:
            try:
                cursor = await conn.execute(
                    "INSERT INTO arc_health_log (arc_id, chapter_id, health_status, notes) "
                    "VALUES (?, ?, ?, ?)",
                    (arc_id, chapter_id, health_status, notes),
                )
                new_id = cursor.lastrowid
                await conn.commit()
                row = await conn.execute_fetchall(
                    "SELECT * FROM arc_health_log WHERE id = ?",
                    (new_id,),
                )
                return ArcHealthLog(**dict(row[0]))
            except Exception as exc:
                logger.error("log_arc_health failed: %s", exc)
                return ValidationFailure(is_valid=False, errors=[str(exc)])

    # ------------------------------------------------------------------
    # delete_arc
    # ------------------------------------------------------------------

    @mcp.tool()
    async def delete_arc(arc_id: int) -> NotFoundResponse | ValidationFailure | dict:
        """Delete a character arc by ID.

        Idempotent: returns NotFoundResponse if the arc does not exist.
        Refuses with ValidationFailure if dependent records reference this arc
        (chapter_character_arcs, arc_health_log, or arc_seven_point_beats all
        have FK into character_arcs).

        Args:
            arc_id: Primary key of the character_arcs row.

        Returns:
            {"deleted": True, "id": arc_id} on success.
            NotFoundResponse if not found.
            ValidationFailure if FK constraint blocks deletion.
        """
        async with get_connection() as conn:
            row = await conn.execute_fetchall(
                "SELECT id FROM character_arcs WHERE id = ?", (arc_id,)
            )
            if not row:
                return NotFoundResponse(not_found_message=f"Arc {arc_id} not found")
            try:
                await conn.execute("DELETE FROM character_arcs WHERE id = ?", (arc_id,))
                await conn.commit()
                return {"deleted": True, "id": arc_id}
            except Exception as exc:
                logger.error("delete_arc failed: %s", exc)
                return ValidationFailure(is_valid=False, errors=[str(exc)])

    # ------------------------------------------------------------------
    # delete_arc_health_log
    # ------------------------------------------------------------------

    @mcp.tool()
    async def delete_arc_health_log(
        arc_health_log_id: int,
    ) -> NotFoundResponse | dict:
        """Delete an arc health log entry by ID.

        Idempotent: returns NotFoundResponse if the record does not exist.
        arc_health_log is a log table with no FK children, so no FK constraint
        check is needed.

        Args:
            arc_health_log_id: Primary key of the arc_health_log row.

        Returns:
            {"deleted": True, "id": arc_health_log_id} on success.
            NotFoundResponse if not found.
        """
        async with get_connection() as conn:
            row = await conn.execute_fetchall(
                "SELECT id FROM arc_health_log WHERE id = ?", (arc_health_log_id,)
            )
            if not row:
                return NotFoundResponse(
                    not_found_message=f"Arc health log {arc_health_log_id} not found"
                )
            await conn.execute(
                "DELETE FROM arc_health_log WHERE id = ?", (arc_health_log_id,)
            )
            await conn.commit()
            return {"deleted": True, "id": arc_health_log_id}

    # ------------------------------------------------------------------
    # delete_chekov
    # ------------------------------------------------------------------

    @mcp.tool()
    async def delete_chekov(chekov_id: int) -> NotFoundResponse | ValidationFailure | dict:
        """Delete a Chekhov's gun registry entry by ID.

        Idempotent: returns NotFoundResponse if the record does not exist.
        Uses FK-safe pattern (ValidationFailure on exception) for consistency
        with the safety-first delete approach.

        Args:
            chekov_id: Primary key of the chekovs_gun_registry row.

        Returns:
            {"deleted": True, "id": chekov_id} on success.
            NotFoundResponse if not found.
            ValidationFailure if FK constraint blocks deletion.
        """
        async with get_connection() as conn:
            row = await conn.execute_fetchall(
                "SELECT id FROM chekovs_gun_registry WHERE id = ?", (chekov_id,)
            )
            if not row:
                return NotFoundResponse(
                    not_found_message=f"Chekhov's gun {chekov_id} not found"
                )
            try:
                await conn.execute(
                    "DELETE FROM chekovs_gun_registry WHERE id = ?", (chekov_id,)
                )
                await conn.commit()
                return {"deleted": True, "id": chekov_id}
            except Exception as exc:
                logger.error("delete_chekov failed: %s", exc)
                return ValidationFailure(is_valid=False, errors=[str(exc)])

    # ------------------------------------------------------------------
    # upsert_arc
    # ------------------------------------------------------------------

    @mcp.tool()
    async def upsert_arc(
        character_id: int,
        arc_type: str = "growth",
        arc_id: int | None = None,
        starting_state: str | None = None,
        desired_state: str | None = None,
        wound: str | None = None,
        lie_believed: str | None = None,
        truth_to_learn: str | None = None,
        opened_chapter_id: int | None = None,
        closed_chapter_id: int | None = None,
        notes: str | None = None,
        canon_status: str = "draft",
    ) -> CharacterArc | NotFoundResponse | ValidationFailure:
        """Create or update a character arc.

        Two-branch upsert:
        - arc_id=None: INSERT a new row; character_id existence is verified
          first.
        - arc_id provided: INSERT ... ON CONFLICT(id) DO UPDATE; character_id
          existence is verified first.

        Always selects back and returns the created or updated CharacterArc row.
        No gate check — arc tools are not gated.

        Args:
            character_id: FK to characters table (required).
            arc_type: Type of arc — e.g. "growth", "fall", "flat" (default:
                      "growth").
            arc_id: Existing arc ID to update, or None to create a new arc.
            starting_state: Narrative state the character starts in (optional).
            desired_state: Narrative state the character is striving toward
                           (optional).
            wound: Core wound driving the character's flaw (optional).
            lie_believed: Lie the character believes about themselves or the
                          world (optional).
            truth_to_learn: Truth the character must learn to complete the arc
                            (optional).
            opened_chapter_id: Chapter where this arc begins (optional).
            closed_chapter_id: Chapter where this arc concludes (optional).
            notes: Free-form notes (optional).
            canon_status: Canon status — e.g. "draft", "canon" (default:
                          "draft").

        Returns:
            The created or updated CharacterArc record.
            NotFoundResponse if the character_id does not exist.
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
            try:
                if arc_id is None:
                    cursor = await conn.execute(
                        """INSERT INTO character_arcs
                               (character_id, arc_type, starting_state, desired_state,
                                wound, lie_believed, truth_to_learn,
                                opened_chapter_id, closed_chapter_id,
                                notes, canon_status, updated_at)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))""",
                        (
                            character_id,
                            arc_type,
                            starting_state,
                            desired_state,
                            wound,
                            lie_believed,
                            truth_to_learn,
                            opened_chapter_id,
                            closed_chapter_id,
                            notes,
                            canon_status,
                        ),
                    )
                    new_id = cursor.lastrowid
                    await conn.commit()
                    row = await conn.execute_fetchall(
                        "SELECT * FROM character_arcs WHERE id = ?", (new_id,)
                    )
                else:
                    await conn.execute(
                        """INSERT INTO character_arcs
                               (id, character_id, arc_type, starting_state, desired_state,
                                wound, lie_believed, truth_to_learn,
                                opened_chapter_id, closed_chapter_id,
                                notes, canon_status, updated_at)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                           ON CONFLICT(id) DO UPDATE SET
                               character_id=excluded.character_id,
                               arc_type=excluded.arc_type,
                               starting_state=excluded.starting_state,
                               desired_state=excluded.desired_state,
                               wound=excluded.wound,
                               lie_believed=excluded.lie_believed,
                               truth_to_learn=excluded.truth_to_learn,
                               opened_chapter_id=excluded.opened_chapter_id,
                               closed_chapter_id=excluded.closed_chapter_id,
                               notes=excluded.notes,
                               canon_status=excluded.canon_status,
                               updated_at=datetime('now')""",
                        (
                            arc_id,
                            character_id,
                            arc_type,
                            starting_state,
                            desired_state,
                            wound,
                            lie_believed,
                            truth_to_learn,
                            opened_chapter_id,
                            closed_chapter_id,
                            notes,
                            canon_status,
                        ),
                    )
                    await conn.commit()
                    row = await conn.execute_fetchall(
                        "SELECT * FROM character_arcs WHERE id = ?", (arc_id,)
                    )
                return CharacterArc(**dict(row[0]))
            except Exception as exc:
                logger.error("upsert_arc failed: %s", exc)
                return ValidationFailure(is_valid=False, errors=[str(exc)])

    # ------------------------------------------------------------------
    # log_subplot_touchpoint
    # ------------------------------------------------------------------

    @mcp.tool()
    async def log_subplot_touchpoint(
        plot_thread_id: int,
        chapter_id: int,
        touchpoint_type: str = "advance",
        notes: str | None = None,
    ) -> SubplotTouchpoint | NotFoundResponse | ValidationFailure:
        """Append a subplot touchpoint entry to the log.

        Append-only INSERT — subplot_touchpoint_log has no UNIQUE constraint
        beyond the primary key, so each call always inserts a new row. Multiple
        touchpoints per plot thread and chapter are valid.

        Pre-checks that both plot_thread_id exists in plot_threads and
        chapter_id exists in chapters.

        Args:
            plot_thread_id: FK to plot_threads — the subplot receiving this
                            touchpoint (required).
            chapter_id: FK to chapters — the chapter where the touchpoint
                        occurs (required).
            touchpoint_type: Type of touchpoint — e.g. "advance", "callback",
                             "resolve" (default: "advance").
            notes: Free-form notes about this touchpoint (optional).

        Returns:
            The newly created SubplotTouchpoint row.
            NotFoundResponse if plot_thread_id or chapter_id does not exist.
            ValidationFailure on database error.
        """
        async with get_connection() as conn:
            thread = await conn.execute_fetchall(
                "SELECT id FROM plot_threads WHERE id = ?", (plot_thread_id,)
            )
            if not thread:
                return NotFoundResponse(
                    not_found_message=f"Plot thread {plot_thread_id} not found"
                )
            chapter = await conn.execute_fetchall(
                "SELECT id FROM chapters WHERE id = ?", (chapter_id,)
            )
            if not chapter:
                return NotFoundResponse(
                    not_found_message=f"Chapter {chapter_id} not found"
                )
            try:
                cursor = await conn.execute(
                    "INSERT INTO subplot_touchpoint_log "
                    "(plot_thread_id, chapter_id, touchpoint_type, notes) "
                    "VALUES (?, ?, ?, ?)",
                    (plot_thread_id, chapter_id, touchpoint_type, notes),
                )
                new_id = cursor.lastrowid
                await conn.commit()
                row = await conn.execute_fetchall(
                    "SELECT * FROM subplot_touchpoint_log WHERE id = ?", (new_id,)
                )
                return SubplotTouchpoint(**dict(row[0]))
            except Exception as exc:
                logger.error("log_subplot_touchpoint failed: %s", exc)
                return ValidationFailure(is_valid=False, errors=[str(exc)])

    # ------------------------------------------------------------------
    # delete_subplot_touchpoint
    # ------------------------------------------------------------------

    @mcp.tool()
    async def delete_subplot_touchpoint(
        touchpoint_id: int,
    ) -> NotFoundResponse | dict:
        """Delete a subplot touchpoint log entry by ID.

        Idempotent: returns NotFoundResponse if the record does not exist.
        subplot_touchpoint_log is an append-only log with no FK children —
        deletion uses the log-style pattern (no try/except needed).

        Args:
            touchpoint_id: Primary key of the subplot_touchpoint_log row to
                           delete.

        Returns:
            {"deleted": True, "id": touchpoint_id} on success.
            NotFoundResponse if not found.
        """
        async with get_connection() as conn:
            row = await conn.execute_fetchall(
                "SELECT id FROM subplot_touchpoint_log WHERE id = ?", (touchpoint_id,)
            )
            if not row:
                return NotFoundResponse(
                    not_found_message=f"Subplot touchpoint {touchpoint_id} not found"
                )
            await conn.execute(
                "DELETE FROM subplot_touchpoint_log WHERE id = ?", (touchpoint_id,)
            )
            await conn.commit()
            return {"deleted": True, "id": touchpoint_id}
