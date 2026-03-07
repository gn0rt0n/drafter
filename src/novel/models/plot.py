"""Plot domain Pydantic models — Plot threads, chapter-plot mapping, chapter-arc mapping."""

from pydantic import BaseModel


class PlotThread(BaseModel):
    """Represents a row in the plot_threads table (migration 016)."""
    id: int | None = None
    name: str
    thread_type: str = "main"
    status: str = "active"
    opened_chapter_id: int | None = None
    closed_chapter_id: int | None = None
    parent_thread_id: int | None = None
    summary: str | None = None
    resolution: str | None = None
    stakes: str | None = None
    notes: str | None = None
    canon_status: str = "draft"
    created_at: str | None = None
    updated_at: str | None = None


class ChapterPlotThread(BaseModel):
    """Represents a row in the chapter_plot_threads table (migration 016)."""
    id: int | None = None
    chapter_id: int
    plot_thread_id: int
    thread_role: str = "advance"
    notes: str | None = None
    created_at: str | None = None


class ChapterCharacterArc(BaseModel):
    """Represents a row in the chapter_character_arcs table (migration 017)."""
    id: int | None = None
    chapter_id: int
    arc_id: int
    arc_progression: str = "stasis"
    notes: str | None = None
    created_at: str | None = None
