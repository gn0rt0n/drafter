"""Scene domain MCP tools.

All 6 scene tools are registered via the register(mcp) function pattern.
This module is standalone — it does not modify server.py; wiring happens in
the server module.

IMPORTANT: Never use the print function in this module. All logging goes to
stderr via the logging module — using print corrupts the stdio protocol.
"""

import json
import logging

from mcp.server.fastmcp import FastMCP

from novel.mcp.db import get_connection
from novel.models.scenes import Scene, SceneCharacterGoal
from novel.models.shared import NotFoundResponse, ValidationFailure

logger = logging.getLogger(__name__)


def register(mcp: FastMCP) -> None:
    """Register all 6 scene domain tools with the given FastMCP instance.

    Tools are defined as local async functions and decorated with @mcp.tool().
    The FastMCP instance is always the one passed in — never imported globally.

    Args:
        mcp: The FastMCP server instance to register tools against.
    """

    # ------------------------------------------------------------------
    # get_scene
    # ------------------------------------------------------------------

    @mcp.tool()
    async def get_scene(scene_id: int) -> Scene | NotFoundResponse:
        """Look up a single scene by ID, returning all fields.

        narrative_functions is automatically parsed from JSON TEXT to list[str]
        by the Scene model's field_validator.

        Args:
            scene_id: Primary key of the scene to retrieve.

        Returns:
            Scene with all fields populated (narrative_functions as list), or
            NotFoundResponse if the scene does not exist.
        """
        async with get_connection() as conn:
            row = await conn.execute_fetchall(
                "SELECT * FROM scenes WHERE id = ?", (scene_id,)
            )
            if not row:
                logger.debug("Scene %d not found", scene_id)
                return NotFoundResponse(not_found_message=f"Scene {scene_id} not found")
            return Scene(**dict(row[0]))

    # ------------------------------------------------------------------
    # get_scene_character_goals
    # ------------------------------------------------------------------

    @mcp.tool()
    async def get_scene_character_goals(
        scene_id: int,
    ) -> list[SceneCharacterGoal] | NotFoundResponse:
        """Return all per-character goals for a scene.

        First verifies the scene exists, then returns all associated goal records.
        An empty list is valid when a scene exists but no goals have been recorded.

        Args:
            scene_id: Primary key of the scene whose character goals to retrieve.

        Returns:
            List of SceneCharacterGoal records ordered by id, or
            NotFoundResponse if the scene does not exist.
        """
        async with get_connection() as conn:
            exists = await conn.execute_fetchall(
                "SELECT id FROM scenes WHERE id = ?", (scene_id,)
            )
            if not exists:
                logger.debug("Scene %d not found for character goals", scene_id)
                return NotFoundResponse(not_found_message=f"Scene {scene_id} not found")

            rows = await conn.execute_fetchall(
                "SELECT * FROM scene_character_goals WHERE scene_id = ? ORDER BY id",
                (scene_id,),
            )
            return [SceneCharacterGoal(**dict(row)) for row in rows]

    # ------------------------------------------------------------------
    # upsert_scene
    # ------------------------------------------------------------------

    @mcp.tool()
    async def upsert_scene(
        scene_id: int | None,
        chapter_id: int,
        scene_number: int,
        location_id: int | None = None,
        time_marker: str | None = None,
        summary: str | None = None,
        scene_type: str = "action",
        dramatic_question: str | None = None,
        scene_goal: str | None = None,
        obstacle: str | None = None,
        turn: str | None = None,
        consequence: str | None = None,
        emotional_function: str | None = None,
        narrative_functions: list[str] | None = None,
        word_count_target: int | None = None,
        status: str = "planned",
        notes: str | None = None,
    ) -> Scene | ValidationFailure:
        """Create or update a scene.

        When scene_id is None, a new scene is inserted and the AUTOINCREMENT
        primary key is assigned. When scene_id is provided, the existing row is
        updated via ON CONFLICT(id) DO UPDATE.

        narrative_functions is serialised to JSON TEXT before writing to SQLite
        via Scene.to_db_dict(). The returned Scene automatically parses it back
        to list[str] via the field_validator.

        Args:
            scene_id: Existing scene ID to update, or None to create.
            chapter_id: FK to chapters table (required).
            scene_number: Position within the chapter (required).
            location_id: FK to locations table (optional).
            time_marker: Narrative time label for this scene (optional).
            summary: Brief description of scene events (optional).
            scene_type: Type such as "action", "dialogue", "transition" (default "action").
            dramatic_question: Central tension this scene answers (optional).
            scene_goal: What the POV character wants in this scene (optional).
            obstacle: What stands in the way of the scene goal (optional).
            turn: How the scene pivots or resolves (optional).
            consequence: Aftermath or consequence of the scene turn (optional).
            emotional_function: Emotional beat this scene serves (optional).
            narrative_functions: List of narrative roles, e.g. ["setup", "payoff"] (optional).
            word_count_target: Target word count for this scene (optional).
            status: Scene status — "planned", "drafted", "revised", etc.
            notes: Free-form notes (optional).

        Returns:
            The created or updated Scene (with narrative_functions as list), or
            ValidationFailure on DB error.
        """
        async with get_connection() as conn:
            try:
                # Build a Scene object so to_db_dict() handles JSON serialisation
                scene = Scene(
                    id=scene_id,
                    chapter_id=chapter_id,
                    scene_number=scene_number,
                    location_id=location_id,
                    time_marker=time_marker,
                    summary=summary,
                    scene_type=scene_type,
                    dramatic_question=dramatic_question,
                    scene_goal=scene_goal,
                    obstacle=obstacle,
                    turn=turn,
                    consequence=consequence,
                    emotional_function=emotional_function,
                    narrative_functions=narrative_functions,
                    word_count_target=word_count_target,
                    status=status,
                    notes=notes,
                )
                db_dict = scene.to_db_dict()
                nf_json = db_dict["narrative_functions"]  # JSON string or None

                if scene_id is None:
                    # INSERT without id — let AUTOINCREMENT fire
                    cursor = await conn.execute(
                        """INSERT INTO scenes (
                            chapter_id, scene_number, location_id, time_marker,
                            summary, scene_type, dramatic_question, scene_goal,
                            obstacle, turn, consequence, emotional_function,
                            narrative_functions, word_count_target, status, notes,
                            updated_at
                        ) VALUES (
                            ?, ?, ?, ?,
                            ?, ?, ?, ?,
                            ?, ?, ?, ?,
                            ?, ?, ?, ?,
                            datetime('now')
                        )""",
                        (
                            chapter_id, scene_number, location_id, time_marker,
                            summary, scene_type, dramatic_question, scene_goal,
                            obstacle, turn, consequence, emotional_function,
                            nf_json, word_count_target, status, notes,
                        ),
                    )
                    new_id = cursor.lastrowid
                    await conn.commit()
                    row = await conn.execute_fetchall(
                        "SELECT * FROM scenes WHERE id = ?", (new_id,)
                    )
                else:
                    # UPSERT — update existing row by id
                    await conn.execute(
                        """INSERT INTO scenes (
                            id, chapter_id, scene_number, location_id, time_marker,
                            summary, scene_type, dramatic_question, scene_goal,
                            obstacle, turn, consequence, emotional_function,
                            narrative_functions, word_count_target, status, notes,
                            updated_at
                        ) VALUES (
                            ?, ?, ?, ?, ?,
                            ?, ?, ?, ?,
                            ?, ?, ?, ?,
                            ?, ?, ?, ?,
                            datetime('now')
                        )
                        ON CONFLICT(id) DO UPDATE SET
                            chapter_id=excluded.chapter_id,
                            scene_number=excluded.scene_number,
                            location_id=excluded.location_id,
                            time_marker=excluded.time_marker,
                            summary=excluded.summary,
                            scene_type=excluded.scene_type,
                            dramatic_question=excluded.dramatic_question,
                            scene_goal=excluded.scene_goal,
                            obstacle=excluded.obstacle,
                            turn=excluded.turn,
                            consequence=excluded.consequence,
                            emotional_function=excluded.emotional_function,
                            narrative_functions=excluded.narrative_functions,
                            word_count_target=excluded.word_count_target,
                            status=excluded.status,
                            notes=excluded.notes,
                            updated_at=datetime('now')
                        """,
                        (
                            scene_id,
                            chapter_id, scene_number, location_id, time_marker,
                            summary, scene_type, dramatic_question, scene_goal,
                            obstacle, turn, consequence, emotional_function,
                            nf_json, word_count_target, status, notes,
                        ),
                    )
                    await conn.commit()
                    row = await conn.execute_fetchall(
                        "SELECT * FROM scenes WHERE id = ?", (scene_id,)
                    )
            except Exception as exc:
                logger.error("upsert_scene failed: %s", exc)
                return ValidationFailure(is_valid=False, errors=[str(exc)])

            return Scene(**dict(row[0]))

    # ------------------------------------------------------------------
    # upsert_scene_goal
    # ------------------------------------------------------------------

    @mcp.tool()
    async def upsert_scene_goal(
        scene_id: int,
        character_id: int,
        goal: str,
        obstacle: str | None = None,
        outcome: str | None = None,
        notes: str | None = None,
    ) -> SceneCharacterGoal | ValidationFailure:
        """Create or update a per-character goal for a scene.

        Uses ON CONFLICT(scene_id, character_id) DO UPDATE so that repeated
        calls with the same pair always overwrite rather than creating duplicates.

        Args:
            scene_id: FK to scenes table (required).
            character_id: FK to characters table (required).
            goal: What this character wants during the scene (required).
            obstacle: What prevents the character from achieving the goal (optional).
            outcome: How the goal attempt resolved (optional).
            notes: Free-form notes (optional).

        Returns:
            The created or updated SceneCharacterGoal, or ValidationFailure on DB error.
        """
        async with get_connection() as conn:
            try:
                await conn.execute(
                    """INSERT INTO scene_character_goals (
                        scene_id, character_id, goal, obstacle, outcome, notes,
                        updated_at
                    ) VALUES (
                        ?, ?, ?, ?, ?, ?,
                        datetime('now')
                    )
                    ON CONFLICT(scene_id, character_id) DO UPDATE SET
                        goal=excluded.goal,
                        obstacle=excluded.obstacle,
                        outcome=excluded.outcome,
                        notes=excluded.notes,
                        updated_at=datetime('now')
                    """,
                    (scene_id, character_id, goal, obstacle, outcome, notes),
                )
                await conn.commit()
                row = await conn.execute_fetchall(
                    "SELECT * FROM scene_character_goals "
                    "WHERE scene_id = ? AND character_id = ?",
                    (scene_id, character_id),
                )
                return SceneCharacterGoal(**dict(row[0]))
            except Exception as exc:
                logger.error("upsert_scene_goal failed: %s", exc)
                return ValidationFailure(is_valid=False, errors=[str(exc)])

    # ------------------------------------------------------------------
    # delete_scene
    # ------------------------------------------------------------------

    @mcp.tool()
    async def delete_scene(scene_id: int) -> NotFoundResponse | ValidationFailure | dict:
        """Delete a scene by ID.

        Refuses if scene_character_goals or other records reference this scene
        (FK-safe). Idempotent (returns NotFoundResponse if absent).

        Args:
            scene_id: Primary key of the scene to delete.

        Returns:
            {"deleted": True, "id": scene_id} on success.
            NotFoundResponse if not found.
            ValidationFailure if FK constraint blocks deletion.
        """
        async with get_connection() as conn:
            row = await conn.execute_fetchall(
                "SELECT id FROM scenes WHERE id = ?", (scene_id,)
            )
            if not row:
                return NotFoundResponse(
                    not_found_message=f"Scene {scene_id} not found"
                )
            try:
                await conn.execute("DELETE FROM scenes WHERE id = ?", (scene_id,))
                await conn.commit()
                return {"deleted": True, "id": scene_id}
            except Exception as exc:
                logger.error("delete_scene failed: %s", exc)
                return ValidationFailure(is_valid=False, errors=[str(exc)])

    # ------------------------------------------------------------------
    # delete_scene_goal
    # ------------------------------------------------------------------

    @mcp.tool()
    async def delete_scene_goal(scene_goal_id: int) -> NotFoundResponse | dict:
        """Delete a scene character goal by ID.

        scene_character_goals is a leaf table with no FK children — uses the
        simpler log-delete pattern (no ValidationFailure return needed).
        Idempotent (returns NotFoundResponse if absent).

        Args:
            scene_goal_id: Primary key of the scene_character_goals row to delete.

        Returns:
            {"deleted": True, "id": scene_goal_id} on success.
            NotFoundResponse if not found.
        """
        async with get_connection() as conn:
            row = await conn.execute_fetchall(
                "SELECT id FROM scene_character_goals WHERE id = ?", (scene_goal_id,)
            )
            if not row:
                return NotFoundResponse(
                    not_found_message=f"Scene goal {scene_goal_id} not found"
                )
            await conn.execute(
                "DELETE FROM scene_character_goals WHERE id = ?", (scene_goal_id,)
            )
            await conn.commit()
            return {"deleted": True, "id": scene_goal_id}
