"""Chapter domain MCP tools.

All 8 chapter tools are registered via the register(mcp) function pattern.
This module is standalone — it does not modify server.py; wiring happens in
the server module.

IMPORTANT: Never use the print function in this module. All logging goes to
stderr via the logging module — using print corrupts the stdio protocol.
"""

import logging

from mcp.server.fastmcp import FastMCP

from novel.mcp.db import get_connection
from novel.models.chapters import Chapter, ChapterPlan, ChapterStructuralObligation
from novel.models.shared import NotFoundResponse, ValidationFailure

logger = logging.getLogger(__name__)


def register(mcp: FastMCP) -> None:
    """Register all 8 chapter domain tools with the given FastMCP instance.

    Tools are defined as local async functions and decorated with @mcp.tool().
    The FastMCP instance is always the one passed in — never imported globally.

    Args:
        mcp: The FastMCP server instance to register tools against.
    """

    # ------------------------------------------------------------------
    # get_chapter
    # ------------------------------------------------------------------

    @mcp.tool()
    async def get_chapter(chapter_id: int) -> Chapter | NotFoundResponse:
        """Look up a single chapter by ID, returning all fields.

        Args:
            chapter_id: Primary key of the chapter to retrieve.

        Returns:
            Chapter with all fields populated, or NotFoundResponse if the
            chapter does not exist.
        """
        async with get_connection() as conn:
            row = await conn.execute_fetchall(
                "SELECT * FROM chapters WHERE id = ?", (chapter_id,)
            )
            if not row:
                logger.debug("Chapter %d not found", chapter_id)
                return NotFoundResponse(not_found_message=f"Chapter {chapter_id} not found")
            return Chapter(**dict(row[0]))

    # ------------------------------------------------------------------
    # get_chapter_plan
    # ------------------------------------------------------------------

    @mcp.tool()
    async def get_chapter_plan(chapter_id: int) -> ChapterPlan | NotFoundResponse:
        """Return the focused writing-guidance subset of a chapter.

        Returns the 8 writing-relevant fields from the chapter row — useful
        for understanding structure and hooks without the full metadata set.

        Args:
            chapter_id: Primary key of the chapter to retrieve.

        Returns:
            ChapterPlan with writing-guidance fields, or NotFoundResponse if
            the chapter does not exist.
        """
        async with get_connection() as conn:
            row = await conn.execute_fetchall(
                "SELECT * FROM chapters WHERE id = ?", (chapter_id,)
            )
            if not row:
                logger.debug("Chapter %d not found for plan", chapter_id)
                return NotFoundResponse(not_found_message=f"Chapter {chapter_id} not found")
            r = row[0]
            return ChapterPlan(
                chapter_id=r["id"],
                summary=r["summary"],
                opening_state=r["opening_state"],
                closing_state=r["closing_state"],
                opening_hook_note=r["opening_hook_note"],
                closing_hook_note=r["closing_hook_note"],
                structural_function=r["structural_function"],
                hook_strength_rating=r["hook_strength_rating"],
            )

    # ------------------------------------------------------------------
    # get_chapter_obligations
    # ------------------------------------------------------------------

    @mcp.tool()
    async def get_chapter_obligations(
        chapter_id: int,
    ) -> list[ChapterStructuralObligation] | NotFoundResponse:
        """Return all structural obligations for a chapter.

        Args:
            chapter_id: Primary key of the chapter to query.

        Returns:
            List of ChapterStructuralObligation records ordered by id, or
            NotFoundResponse if the chapter does not exist.
        """
        async with get_connection() as conn:
            exists = await conn.execute_fetchall(
                "SELECT id FROM chapters WHERE id = ?", (chapter_id,)
            )
            if not exists:
                logger.debug("Chapter %d not found for obligations", chapter_id)
                return NotFoundResponse(not_found_message=f"Chapter {chapter_id} not found")

            rows = await conn.execute_fetchall(
                "SELECT * FROM chapter_structural_obligations "
                "WHERE chapter_id = ? ORDER BY id",
                (chapter_id,),
            )
            return [ChapterStructuralObligation(**dict(row)) for row in rows]

    # ------------------------------------------------------------------
    # list_chapters
    # ------------------------------------------------------------------

    @mcp.tool()
    async def list_chapters(book_id: int) -> list[Chapter]:
        """Return all chapters in a book ordered by chapter number.

        Args:
            book_id: ID of the book whose chapters to list.

        Returns:
            List of Chapter objects ordered by chapter_number (may be empty
            if the book has no chapters).
        """
        async with get_connection() as conn:
            rows = await conn.execute_fetchall(
                "SELECT * FROM chapters WHERE book_id = ? ORDER BY chapter_number",
                (book_id,),
            )
            return [Chapter(**dict(row)) for row in rows]

    # ------------------------------------------------------------------
    # upsert_chapter
    # ------------------------------------------------------------------

    @mcp.tool()
    async def upsert_chapter(
        chapter_id: int | None,
        book_id: int,
        chapter_number: int,
        act_id: int | None = None,
        title: str | None = None,
        pov_character_id: int | None = None,
        word_count_target: int | None = None,
        summary: str | None = None,
        opening_state: str | None = None,
        closing_state: str | None = None,
        opening_hook_note: str | None = None,
        closing_hook_note: str | None = None,
        hook_strength_rating: int | None = None,
        structural_function: str | None = None,
        status: str = "planned",
        notes: str | None = None,
    ) -> Chapter | ValidationFailure:
        """Create or update a chapter.

        When chapter_id is None, a new chapter is inserted and the
        AUTOINCREMENT primary key is assigned. When chapter_id is provided,
        the existing row is updated via ON CONFLICT(id) DO UPDATE.

        Args:
            chapter_id: Existing chapter ID to update, or None to create.
            book_id: FK to books table (required).
            chapter_number: Position in the book (required).
            act_id: FK to acts table (optional).
            title: Chapter title (optional).
            pov_character_id: FK to characters table for POV (optional).
            word_count_target: Target word count for this chapter (optional).
            summary: Brief summary of chapter events (optional).
            opening_state: Story state at chapter open (optional).
            closing_state: Story state at chapter close (optional).
            opening_hook_note: Notes on the opening hook (optional).
            closing_hook_note: Notes on the closing hook (optional).
            hook_strength_rating: Rating 1-10 for hook effectiveness (optional).
            structural_function: Narrative role of this chapter (optional).
            status: Chapter status — "planned", "drafted", "revised", etc.
            notes: Free-form notes (optional).

        Returns:
            The created or updated Chapter, or ValidationFailure on DB error.
        """
        async with get_connection() as conn:
            try:
                if chapter_id is None:
                    # INSERT without id — let AUTOINCREMENT fire
                    cursor = await conn.execute(
                        """INSERT INTO chapters (
                            book_id, act_id, chapter_number, title,
                            pov_character_id, word_count_target,
                            summary, opening_state, closing_state,
                            opening_hook_note, closing_hook_note,
                            hook_strength_rating, structural_function,
                            status, notes, updated_at
                        ) VALUES (
                            ?, ?, ?, ?,
                            ?, ?,
                            ?, ?, ?,
                            ?, ?,
                            ?, ?,
                            ?, ?, datetime('now')
                        )""",
                        (
                            book_id, act_id, chapter_number, title,
                            pov_character_id, word_count_target,
                            summary, opening_state, closing_state,
                            opening_hook_note, closing_hook_note,
                            hook_strength_rating, structural_function,
                            status, notes,
                        ),
                    )
                    new_id = cursor.lastrowid
                    await conn.commit()
                    row = await conn.execute_fetchall(
                        "SELECT * FROM chapters WHERE id = ?", (new_id,)
                    )
                else:
                    # UPSERT — update existing row
                    await conn.execute(
                        """INSERT INTO chapters (
                            id, book_id, act_id, chapter_number, title,
                            pov_character_id, word_count_target,
                            summary, opening_state, closing_state,
                            opening_hook_note, closing_hook_note,
                            hook_strength_rating, structural_function,
                            status, notes, updated_at
                        ) VALUES (
                            ?, ?, ?, ?, ?,
                            ?, ?,
                            ?, ?, ?,
                            ?, ?,
                            ?, ?,
                            ?, ?, datetime('now')
                        )
                        ON CONFLICT(id) DO UPDATE SET
                            book_id=excluded.book_id,
                            act_id=excluded.act_id,
                            chapter_number=excluded.chapter_number,
                            title=excluded.title,
                            pov_character_id=excluded.pov_character_id,
                            word_count_target=excluded.word_count_target,
                            summary=excluded.summary,
                            opening_state=excluded.opening_state,
                            closing_state=excluded.closing_state,
                            opening_hook_note=excluded.opening_hook_note,
                            closing_hook_note=excluded.closing_hook_note,
                            hook_strength_rating=excluded.hook_strength_rating,
                            structural_function=excluded.structural_function,
                            status=excluded.status,
                            notes=excluded.notes,
                            updated_at=datetime('now')
                        """,
                        (
                            chapter_id,
                            book_id, act_id, chapter_number, title,
                            pov_character_id, word_count_target,
                            summary, opening_state, closing_state,
                            opening_hook_note, closing_hook_note,
                            hook_strength_rating, structural_function,
                            status, notes,
                        ),
                    )
                    await conn.commit()
                    row = await conn.execute_fetchall(
                        "SELECT * FROM chapters WHERE id = ?", (chapter_id,)
                    )
            except Exception as exc:
                logger.error("upsert_chapter failed: %s", exc)
                return ValidationFailure(is_valid=False, errors=[str(exc)])

            return Chapter(**dict(row[0]))

    # ------------------------------------------------------------------
    # delete_chapter
    # ------------------------------------------------------------------

    @mcp.tool()
    async def delete_chapter(chapter_id: int) -> NotFoundResponse | ValidationFailure | dict:
        """Delete a chapter by ID.

        Refuses if scenes, acts, character state tables, pacing_beats, junction
        tables, or other records reference this chapter. Idempotent (returns
        NotFoundResponse if absent).

        Args:
            chapter_id: Primary key of the chapter to delete.

        Returns:
            {"deleted": True, "id": chapter_id} on success.
            NotFoundResponse if not found.
            ValidationFailure if FK constraint blocks deletion.
        """
        async with get_connection() as conn:
            row = await conn.execute_fetchall(
                "SELECT id FROM chapters WHERE id = ?", (chapter_id,)
            )
            if not row:
                return NotFoundResponse(
                    not_found_message=f"Chapter {chapter_id} not found"
                )
            try:
                await conn.execute("DELETE FROM chapters WHERE id = ?", (chapter_id,))
                await conn.commit()
                return {"deleted": True, "id": chapter_id}
            except Exception as exc:
                logger.error("delete_chapter failed: %s", exc)
                return ValidationFailure(is_valid=False, errors=[str(exc)])

    # ------------------------------------------------------------------
    # upsert_chapter_obligation
    # ------------------------------------------------------------------

    @mcp.tool()
    async def upsert_chapter_obligation(
        chapter_id: int,
        obligation_type: str,
        description: str,
        obligation_id: int | None = None,
        is_met: bool = False,
        notes: str | None = None,
    ) -> ChapterStructuralObligation | NotFoundResponse | ValidationFailure:
        """Create or update a structural obligation for a chapter.

        Two-branch upsert:
        - obligation_id=None: INSERT a new row; chapter_id existence is
          verified first.
        - obligation_id provided: INSERT ... ON CONFLICT(id) DO UPDATE;
          chapter_id existence is verified first.

        Not gate-gated — chapter structural work does not require prose-phase
        certification.

        Args:
            chapter_id: FK to chapters table (required).
            obligation_type: Type of obligation — e.g. "setup", "payoff",
                             "foreshadow" (required).
            description: Description of what must happen in this chapter
                         (required).
            obligation_id: Existing obligation ID to update, or None to
                           create a new record.
            is_met: Whether the obligation has been fulfilled (default:
                    False).
            notes: Free-form notes (optional).

        Returns:
            The created or updated ChapterStructuralObligation record.
            NotFoundResponse if chapter_id does not exist.
            ValidationFailure on database error.
        """
        async with get_connection() as conn:
            chapter = await conn.execute_fetchall(
                "SELECT id FROM chapters WHERE id = ?", (chapter_id,)
            )
            if not chapter:
                return NotFoundResponse(
                    not_found_message=f"Chapter {chapter_id} not found"
                )
            try:
                if obligation_id is None:
                    cursor = await conn.execute(
                        """INSERT INTO chapter_structural_obligations
                               (chapter_id, obligation_type, description,
                                is_met, notes, updated_at)
                           VALUES (?, ?, ?, ?, ?, datetime('now'))""",
                        (chapter_id, obligation_type, description, is_met, notes),
                    )
                    new_id = cursor.lastrowid
                    await conn.commit()
                    row = await conn.execute_fetchall(
                        "SELECT * FROM chapter_structural_obligations WHERE id = ?",
                        (new_id,),
                    )
                else:
                    await conn.execute(
                        """INSERT INTO chapter_structural_obligations
                               (id, chapter_id, obligation_type, description,
                                is_met, notes, updated_at)
                           VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
                           ON CONFLICT(id) DO UPDATE SET
                               chapter_id=excluded.chapter_id,
                               obligation_type=excluded.obligation_type,
                               description=excluded.description,
                               is_met=excluded.is_met,
                               notes=excluded.notes,
                               updated_at=datetime('now')""",
                        (
                            obligation_id,
                            chapter_id,
                            obligation_type,
                            description,
                            is_met,
                            notes,
                        ),
                    )
                    await conn.commit()
                    row = await conn.execute_fetchall(
                        "SELECT * FROM chapter_structural_obligations WHERE id = ?",
                        (obligation_id,),
                    )
                return ChapterStructuralObligation(**dict(row[0]))
            except Exception as exc:
                logger.error("upsert_chapter_obligation failed: %s", exc)
                return ValidationFailure(is_valid=False, errors=[str(exc)])

    # ------------------------------------------------------------------
    # delete_chapter_obligation
    # ------------------------------------------------------------------

    @mcp.tool()
    async def delete_chapter_obligation(
        obligation_id: int,
    ) -> NotFoundResponse | dict:
        """Delete a chapter structural obligation by ID.

        Idempotent: returns NotFoundResponse if the record does not exist.
        chapter_structural_obligations is a log-style table with no FK
        children — deletion uses the log-style pattern (no try/except needed).

        Args:
            obligation_id: Primary key of the chapter_structural_obligations
                           row to delete.

        Returns:
            {"deleted": True, "id": obligation_id} on success.
            NotFoundResponse if not found.
        """
        async with get_connection() as conn:
            row = await conn.execute_fetchall(
                "SELECT id FROM chapter_structural_obligations WHERE id = ?",
                (obligation_id,),
            )
            if not row:
                return NotFoundResponse(
                    not_found_message=f"Chapter obligation {obligation_id} not found"
                )
            await conn.execute(
                "DELETE FROM chapter_structural_obligations WHERE id = ?",
                (obligation_id,),
            )
            await conn.commit()
            return {"deleted": True, "id": obligation_id}
