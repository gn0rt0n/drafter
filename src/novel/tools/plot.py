"""Plot domain MCP tools.

All 4 plot thread tools are registered via the register(mcp) function pattern.
This module is standalone — it does not modify server.py; wiring happens in
the server module.

IMPORTANT: Never use the print function in this module. All logging goes to
stderr via the logging module — using print corrupts the stdio protocol.
"""

import logging

from mcp.server.fastmcp import FastMCP

from novel.mcp.db import get_connection
from novel.models.plot import PlotThread
from novel.models.shared import NotFoundResponse, ValidationFailure

logger = logging.getLogger(__name__)


def register(mcp: FastMCP) -> None:
    """Register all 4 plot thread tools with the given FastMCP instance.

    Tools are defined as local async functions and decorated with @mcp.tool().
    The FastMCP instance is always the one passed in — never imported globally.

    Args:
        mcp: The FastMCP server instance to register tools against.
    """

    # ------------------------------------------------------------------
    # get_plot_thread
    # ------------------------------------------------------------------

    @mcp.tool()
    async def get_plot_thread(plot_thread_id: int) -> PlotThread | NotFoundResponse:
        """Look up a single plot thread by ID, returning all fields.

        Args:
            plot_thread_id: Primary key of the plot thread to retrieve.

        Returns:
            PlotThread with all fields populated, or NotFoundResponse if the
            plot thread does not exist.
        """
        async with get_connection() as conn:
            rows = await conn.execute_fetchall(
                "SELECT * FROM plot_threads WHERE id = ?", (plot_thread_id,)
            )
            if not rows:
                logger.debug("Plot thread %d not found", plot_thread_id)
                return NotFoundResponse(
                    not_found_message=f"Plot thread {plot_thread_id} not found"
                )
            return PlotThread(**dict(rows[0]))

    # ------------------------------------------------------------------
    # list_plot_threads
    # ------------------------------------------------------------------

    @mcp.tool()
    async def list_plot_threads(
        thread_type: str | None = None,
        status: str | None = None,
    ) -> list[PlotThread]:
        """List all plot threads, optionally filtered by thread_type and/or status.

        Args:
            thread_type: If provided, filter to only threads with this type
                         (e.g. "main", "subplot", "backstory").
            status: If provided, filter to only threads with this status
                    (e.g. "active", "resolved", "dormant").

        Returns:
            List of PlotThread records ordered by id, filtered as requested.
            Returns an empty list if no threads match.
        """
        async with get_connection() as conn:
            clauses, params = [], []
            if thread_type is not None:
                clauses.append("thread_type = ?")
                params.append(thread_type)
            if status is not None:
                clauses.append("status = ?")
                params.append(status)
            where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
            rows = await conn.execute_fetchall(
                f"SELECT * FROM plot_threads {where} ORDER BY id", params
            )
            return [PlotThread(**dict(r)) for r in rows]

    # ------------------------------------------------------------------
    # upsert_plot_thread
    # ------------------------------------------------------------------

    @mcp.tool()
    async def upsert_plot_thread(
        plot_thread_id: int | None,
        name: str,
        thread_type: str | None = None,
        status: str | None = None,
        opened_chapter_id: int | None = None,
        closed_chapter_id: int | None = None,
        parent_thread_id: int | None = None,
        summary: str | None = None,
        resolution: str | None = None,
        stakes: str | None = None,
        notes: str | None = None,
        canon_status: str | None = None,
    ) -> PlotThread | ValidationFailure:
        """Create or update a plot thread.

        When plot_thread_id is None, a new plot thread is inserted and the
        AUTOINCREMENT primary key is assigned. When plot_thread_id is provided,
        the existing row is updated via ON CONFLICT(id) DO UPDATE.

        Does NOT touch the chapter_plot_threads junction table — junction
        management is handled via chapter tools.

        Args:
            plot_thread_id: Existing plot thread ID to update, or None to create.
            name: Plot thread name (required).
            thread_type: Category of thread — e.g. "main", "subplot", "backstory".
                         Defaults to "main" when None.
            status: Thread status — e.g. "active", "resolved", "dormant".
                    Defaults to "active" when None.
            opened_chapter_id: FK to chapters table where this thread opens (optional).
            closed_chapter_id: FK to chapters table where this thread closes (optional).
            parent_thread_id: FK to plot_threads for nesting subplots (optional).
            summary: Narrative summary of the plot thread (optional).
            resolution: How the thread resolves (optional).
            stakes: Stakes involved in this thread (optional).
            notes: Free-form notes (optional).
            canon_status: Canon status — e.g. "draft", "canon", "cut".
                          Defaults to "draft" when None.

        Returns:
            The created or updated PlotThread, or ValidationFailure on DB error.
        """
        async with get_connection() as conn:
            try:
                if plot_thread_id is None:
                    cursor = await conn.execute(
                        """INSERT INTO plot_threads
                               (name, thread_type, status, opened_chapter_id, closed_chapter_id,
                                parent_thread_id, summary, resolution, stakes, notes, canon_status,
                                updated_at)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))""",
                        (
                            name,
                            thread_type or "main",
                            status or "active",
                            opened_chapter_id,
                            closed_chapter_id,
                            parent_thread_id,
                            summary,
                            resolution,
                            stakes,
                            notes,
                            canon_status or "draft",
                        ),
                    )
                    new_id = cursor.lastrowid
                    await conn.commit()
                    row = await conn.execute_fetchall(
                        "SELECT * FROM plot_threads WHERE id = ?", (new_id,)
                    )
                else:
                    await conn.execute(
                        """INSERT INTO plot_threads
                               (id, name, thread_type, status, opened_chapter_id, closed_chapter_id,
                                parent_thread_id, summary, resolution, stakes, notes, canon_status,
                                updated_at)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                           ON CONFLICT(id) DO UPDATE SET
                               name=excluded.name,
                               thread_type=excluded.thread_type,
                               status=excluded.status,
                               opened_chapter_id=excluded.opened_chapter_id,
                               closed_chapter_id=excluded.closed_chapter_id,
                               parent_thread_id=excluded.parent_thread_id,
                               summary=excluded.summary,
                               resolution=excluded.resolution,
                               stakes=excluded.stakes,
                               notes=excluded.notes,
                               canon_status=excluded.canon_status,
                               updated_at=datetime('now')""",
                        (
                            plot_thread_id,
                            name,
                            thread_type or "main",
                            status or "active",
                            opened_chapter_id,
                            closed_chapter_id,
                            parent_thread_id,
                            summary,
                            resolution,
                            stakes,
                            notes,
                            canon_status or "draft",
                        ),
                    )
                    await conn.commit()
                    row = await conn.execute_fetchall(
                        "SELECT * FROM plot_threads WHERE id = ?", (plot_thread_id,)
                    )
            except Exception as exc:
                logger.error("upsert_plot_thread failed: %s", exc)
                return ValidationFailure(is_valid=False, errors=[str(exc)])

            return PlotThread(**dict(row[0]))

    # ------------------------------------------------------------------
    # delete_plot_thread
    # ------------------------------------------------------------------

    @mcp.tool()
    async def delete_plot_thread(
        plot_thread_id: int,
    ) -> NotFoundResponse | ValidationFailure | dict:
        """Delete a plot thread by ID if it is not referenced by any FK children.

        plot_threads is referenced by chapter_plot_threads (plot_thread_id FK)
        and subplot_touchpoint_log (plot_thread_id FK). If either table holds a
        row referencing this plot thread, the DELETE will be blocked by the
        FOREIGN KEY constraint and a ValidationFailure is returned instead.

        Args:
            plot_thread_id: Primary key of the plot thread to delete.

        Returns:
            {"deleted": True, "id": plot_thread_id} on success,
            NotFoundResponse if the plot thread does not exist,
            ValidationFailure if a FK constraint prevents deletion.
        """
        async with get_connection() as conn:
            rows = await conn.execute_fetchall(
                "SELECT id FROM plot_threads WHERE id = ?", (plot_thread_id,)
            )
            if not rows:
                logger.debug("delete_plot_thread: %d not found", plot_thread_id)
                return NotFoundResponse(
                    not_found_message=f"Plot thread {plot_thread_id} not found"
                )
            try:
                await conn.execute(
                    "DELETE FROM plot_threads WHERE id = ?", (plot_thread_id,)
                )
                await conn.commit()
                return {"deleted": True, "id": plot_thread_id}
            except Exception as exc:
                logger.error("delete_plot_thread failed: %s", exc)
                return ValidationFailure(is_valid=False, errors=[str(exc)])
