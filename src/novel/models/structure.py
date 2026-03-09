"""Structure domain Pydantic models — story-level 7-point beats and per-arc beats.

Migration 022: story_structure and arc_seven_point_beats tables.
Field names match SQL column names exactly (migration SQL is ground truth).
No to_db_dict() — neither model has JSON TEXT columns.
"""

from pydantic import BaseModel


class StoryStructure(BaseModel):
    """Represents a row in the story_structure table (migration 022)."""
    id: int | None = None
    book_id: int
    hook_chapter_id: int | None = None
    plot_turn_1_chapter_id: int | None = None
    pinch_1_chapter_id: int | None = None
    midpoint_chapter_id: int | None = None
    pinch_2_chapter_id: int | None = None
    plot_turn_2_chapter_id: int | None = None
    resolution_chapter_id: int | None = None
    act_1_inciting_incident_chapter_id: int | None = None
    act_2_midpoint_chapter_id: int | None = None
    act_3_climax_chapter_id: int | None = None
    notes: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class ArcSevenPointBeat(BaseModel):
    """Represents a row in the arc_seven_point_beats table (migration 022)."""
    id: int | None = None
    arc_id: int
    beat_type: str
    chapter_id: int | None = None
    notes: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
