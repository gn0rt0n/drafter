"""Structure domain MCP tools — story-level 7-point beats and per-arc beats.

All 6 structure tools are registered via the register(mcp) function pattern.
This module is standalone — it does not modify server.py; wiring happens in
the server module.

IMPORTANT: Never use the print function in this module. All logging goes to
stderr via the logging module — using print corrupts the stdio protocol.
"""

import logging

from mcp.server.fastmcp import FastMCP

from novel.mcp.db import get_connection
from novel.models.shared import NotFoundResponse, ValidationFailure
from novel.models.structure import ArcSevenPointBeat, StoryStructure

logger = logging.getLogger(__name__)

VALID_BEAT_TYPES = frozenset({
    "hook", "plot_turn_1", "pinch_1", "midpoint",
    "pinch_2", "plot_turn_2", "resolution",
})


def register(mcp: FastMCP) -> None:
    """Register all 6 structure domain tools with the given FastMCP instance.

    Tools are defined as local async functions and decorated with @mcp.tool().
    The FastMCP instance is always the one passed in — never imported globally.

    Args:
        mcp: The FastMCP server instance to register tools against.
    """

    # ------------------------------------------------------------------
    # get_story_structure (STRUCT-05)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def get_story_structure(book_id: int) -> StoryStructure | NotFoundResponse:
        """Retrieve the story structure row for a book.

        Returns the single story_structure record for the given book_id, or
        NotFoundResponse if no structure has been defined yet.

        Gate-free: structure tools populate data that gate checks — they must
        work without requiring prior certification.

        Args:
            book_id: Primary key of the book whose structure to retrieve.

        Returns:
            StoryStructure record, or NotFoundResponse if not found.
        """
        async with get_connection() as conn:
            rows = await conn.execute_fetchall(
                "SELECT * FROM story_structure WHERE book_id = ?",
                (book_id,),
            )
            if not rows:
                return NotFoundResponse(
                    not_found_message=f"No story structure found for book {book_id}."
                )
            return StoryStructure(**dict(rows[0]))

    # ------------------------------------------------------------------
    # upsert_story_structure (STRUCT-06)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def upsert_story_structure(
        book_id: int,
        hook_chapter_id: int | None = None,
        plot_turn_1_chapter_id: int | None = None,
        pinch_1_chapter_id: int | None = None,
        midpoint_chapter_id: int | None = None,
        pinch_2_chapter_id: int | None = None,
        plot_turn_2_chapter_id: int | None = None,
        resolution_chapter_id: int | None = None,
        act_1_inciting_incident_chapter_id: int | None = None,
        act_2_midpoint_chapter_id: int | None = None,
        act_3_climax_chapter_id: int | None = None,
        notes: str | None = None,
    ) -> StoryStructure | ValidationFailure:
        """Create or update the story structure for a book.

        Single-branch upsert on book_id (UNIQUE constraint). Creates a new row
        if none exists for the book; updates the existing row otherwise.

        Args:
            book_id: Primary key of the book to create/update structure for.
            hook_chapter_id: Chapter containing the story hook (optional).
            plot_turn_1_chapter_id: Chapter of first plot turn (optional).
            pinch_1_chapter_id: Chapter of first pinch point (optional).
            midpoint_chapter_id: Chapter of the midpoint (optional).
            pinch_2_chapter_id: Chapter of second pinch point (optional).
            plot_turn_2_chapter_id: Chapter of second plot turn (optional).
            resolution_chapter_id: Chapter of the resolution (optional).
            act_1_inciting_incident_chapter_id: 3-act inciting incident chapter (optional).
            act_2_midpoint_chapter_id: 3-act Act 2 midpoint chapter (optional).
            act_3_climax_chapter_id: 3-act climax chapter (optional).
            notes: Free-form notes (optional).

        Returns:
            The created or updated StoryStructure record, or ValidationFailure
            on database error.
        """
        async with get_connection() as conn:
            try:
                await conn.execute(
                    """INSERT INTO story_structure (
                           book_id,
                           hook_chapter_id,
                           plot_turn_1_chapter_id,
                           pinch_1_chapter_id,
                           midpoint_chapter_id,
                           pinch_2_chapter_id,
                           plot_turn_2_chapter_id,
                           resolution_chapter_id,
                           act_1_inciting_incident_chapter_id,
                           act_2_midpoint_chapter_id,
                           act_3_climax_chapter_id,
                           notes,
                           updated_at
                       ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                       ON CONFLICT(book_id) DO UPDATE SET
                           hook_chapter_id = excluded.hook_chapter_id,
                           plot_turn_1_chapter_id = excluded.plot_turn_1_chapter_id,
                           pinch_1_chapter_id = excluded.pinch_1_chapter_id,
                           midpoint_chapter_id = excluded.midpoint_chapter_id,
                           pinch_2_chapter_id = excluded.pinch_2_chapter_id,
                           plot_turn_2_chapter_id = excluded.plot_turn_2_chapter_id,
                           resolution_chapter_id = excluded.resolution_chapter_id,
                           act_1_inciting_incident_chapter_id = excluded.act_1_inciting_incident_chapter_id,
                           act_2_midpoint_chapter_id = excluded.act_2_midpoint_chapter_id,
                           act_3_climax_chapter_id = excluded.act_3_climax_chapter_id,
                           notes = excluded.notes,
                           updated_at = datetime('now')""",
                    (
                        book_id,
                        hook_chapter_id,
                        plot_turn_1_chapter_id,
                        pinch_1_chapter_id,
                        midpoint_chapter_id,
                        pinch_2_chapter_id,
                        plot_turn_2_chapter_id,
                        resolution_chapter_id,
                        act_1_inciting_incident_chapter_id,
                        act_2_midpoint_chapter_id,
                        act_3_climax_chapter_id,
                        notes,
                    ),
                )
                await conn.commit()
                rows = await conn.execute_fetchall(
                    "SELECT * FROM story_structure WHERE book_id = ?",
                    (book_id,),
                )
                return StoryStructure(**dict(rows[0]))
            except Exception as exc:
                logger.error("upsert_story_structure failed: %s", exc)
                return ValidationFailure(is_valid=False, errors=[str(exc)])

    # ------------------------------------------------------------------
    # get_arc_beats (STRUCT-07)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def get_arc_beats(arc_id: int) -> list[ArcSevenPointBeat]:
        """Retrieve all 7-point beat records for a character arc.

        Returns the arc_seven_point_beats rows for the given arc, ordered by
        beat_type. Returns an empty list when no beats have been defined yet —
        this is a valid state (arcs are populated progressively).

        Gate-free: structure tools must work without requiring prior
        certification.

        Args:
            arc_id: Primary key of the arc whose beats to retrieve.

        Returns:
            List of ArcSevenPointBeat records ordered by beat_type (may be
            empty).
        """
        async with get_connection() as conn:
            rows = await conn.execute_fetchall(
                "SELECT * FROM arc_seven_point_beats WHERE arc_id = ? ORDER BY beat_type",
                (arc_id,),
            )
            return [ArcSevenPointBeat(**dict(r)) for r in rows]

    # ------------------------------------------------------------------
    # upsert_arc_beat (STRUCT-07)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def upsert_arc_beat(
        arc_id: int,
        beat_type: str,
        chapter_id: int | None = None,
        notes: str | None = None,
    ) -> ArcSevenPointBeat | ValidationFailure:
        """Create or update a single 7-point beat for a character arc.

        Python-side validation of beat_type (no CHECK constraint in SQL).
        Single-branch upsert on (arc_id, beat_type) UNIQUE constraint.

        Args:
            arc_id: FK to character_arcs — the arc this beat belongs to.
            beat_type: One of 'hook', 'plot_turn_1', 'pinch_1', 'midpoint',
                       'pinch_2', 'plot_turn_2', 'resolution'.
            chapter_id: Chapter where this beat occurs (optional — may be
                        recorded before chapter is locked).
            notes: Free-form notes (optional).

        Returns:
            The created or updated ArcSevenPointBeat record, or
            ValidationFailure on invalid beat_type or database error.
        """
        if beat_type not in VALID_BEAT_TYPES:
            return ValidationFailure(
                is_valid=False,
                errors=[
                    f"Invalid beat_type '{beat_type}'. Must be one of: "
                    f"{sorted(VALID_BEAT_TYPES)}"
                ],
            )
        async with get_connection() as conn:
            try:
                await conn.execute(
                    """INSERT INTO arc_seven_point_beats
                           (arc_id, beat_type, chapter_id, notes, updated_at)
                       VALUES (?, ?, ?, ?, datetime('now'))
                       ON CONFLICT(arc_id, beat_type) DO UPDATE SET
                           chapter_id = excluded.chapter_id,
                           notes = excluded.notes,
                           updated_at = datetime('now')""",
                    (arc_id, beat_type, chapter_id, notes),
                )
                await conn.commit()
                rows = await conn.execute_fetchall(
                    "SELECT * FROM arc_seven_point_beats WHERE arc_id = ? AND beat_type = ?",
                    (arc_id, beat_type),
                )
                return ArcSevenPointBeat(**dict(rows[0]))
            except Exception as exc:
                logger.error("upsert_arc_beat failed: %s", exc)
                return ValidationFailure(is_valid=False, errors=[str(exc)])

    # ------------------------------------------------------------------
    # delete_story_structure
    # ------------------------------------------------------------------

    @mcp.tool()
    async def delete_story_structure(
        story_structure_id: int,
    ) -> NotFoundResponse | ValidationFailure | dict:
        """Delete a story structure row by ID.

        story_structure may be referenced by other tables (FK-safe delete).
        Idempotent (returns NotFoundResponse if absent).

        Args:
            story_structure_id: Primary key of the story_structure row to delete.

        Returns:
            {"deleted": True, "id": story_structure_id} on success.
            NotFoundResponse if not found.
            ValidationFailure if FK constraint blocks deletion.
        """
        async with get_connection() as conn:
            row = await conn.execute_fetchall(
                "SELECT id FROM story_structure WHERE id = ?", (story_structure_id,)
            )
            if not row:
                return NotFoundResponse(
                    not_found_message=f"Story structure {story_structure_id} not found"
                )
            try:
                await conn.execute(
                    "DELETE FROM story_structure WHERE id = ?", (story_structure_id,)
                )
                await conn.commit()
                return {"deleted": True, "id": story_structure_id}
            except Exception as exc:
                logger.error("delete_story_structure failed: %s", exc)
                return ValidationFailure(is_valid=False, errors=[str(exc)])

    # ------------------------------------------------------------------
    # delete_arc_beat
    # ------------------------------------------------------------------

    @mcp.tool()
    async def delete_arc_beat(arc_beat_id: int) -> NotFoundResponse | dict:
        """Delete an arc seven-point beat row by ID.

        arc_seven_point_beats is a leaf table with no FK children — uses the
        simpler log-delete pattern. Idempotent (returns NotFoundResponse if
        absent).

        Args:
            arc_beat_id: Primary key of the arc_seven_point_beats row to delete.

        Returns:
            {"deleted": True, "id": arc_beat_id} on success.
            NotFoundResponse if not found.
        """
        async with get_connection() as conn:
            row = await conn.execute_fetchall(
                "SELECT id FROM arc_seven_point_beats WHERE id = ?", (arc_beat_id,)
            )
            if not row:
                return NotFoundResponse(
                    not_found_message=f"Arc beat {arc_beat_id} not found"
                )
            await conn.execute(
                "DELETE FROM arc_seven_point_beats WHERE id = ?", (arc_beat_id,)
            )
            await conn.commit()
            return {"deleted": True, "id": arc_beat_id}
