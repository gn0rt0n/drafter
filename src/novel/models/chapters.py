"""Chapter domain Pydantic models — Chapters and structural obligations."""

from pydantic import BaseModel


class Chapter(BaseModel):
    """Represents a row in the chapters table (migration 008)."""
    id: int | None = None
    book_id: int
    act_id: int | None = None
    chapter_number: int
    title: str | None = None
    pov_character_id: int | None = None
    word_count_target: int | None = None
    actual_word_count: int = 0
    status: str = "planned"
    summary: str | None = None
    opening_state: str | None = None
    closing_state: str | None = None
    opening_hook_note: str | None = None
    closing_hook_note: str | None = None
    hook_strength_rating: int | None = None
    time_marker: str | None = None
    elapsed_days_from_start: int | None = None
    structural_function: str | None = None
    notes: str | None = None
    canon_status: str = "draft"
    source_file: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    reviewed_at: str | None = None


class ChapterStructuralObligation(BaseModel):
    """Represents a row in the chapter_structural_obligations table (migration 016)."""
    id: int | None = None
    chapter_id: int
    obligation_type: str = "setup"
    description: str
    is_met: bool = False
    notes: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
