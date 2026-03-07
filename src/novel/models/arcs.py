"""Arc domain Pydantic models — Character arcs, health log, Chekhov's guns, subplot touchpoints."""

from pydantic import BaseModel


class CharacterArc(BaseModel):
    """Represents a row in the character_arcs table (migration 017)."""
    id: int | None = None
    character_id: int
    arc_type: str = "growth"
    starting_state: str | None = None
    desired_state: str | None = None
    wound: str | None = None
    lie_believed: str | None = None
    truth_to_learn: str | None = None
    opened_chapter_id: int | None = None
    closed_chapter_id: int | None = None
    notes: str | None = None
    canon_status: str = "draft"
    created_at: str | None = None
    updated_at: str | None = None


class ArcHealthLog(BaseModel):
    """Represents a row in the arc_health_log table (migration 017)."""
    id: int | None = None
    arc_id: int
    chapter_id: int
    health_status: str = "on-track"
    notes: str | None = None
    created_at: str | None = None


class ChekhovGun(BaseModel):
    """Represents a row in the chekovs_gun_registry table (migration 017)."""
    id: int | None = None
    name: str
    description: str
    planted_chapter_id: int | None = None
    planted_scene_id: int | None = None
    payoff_chapter_id: int | None = None
    payoff_scene_id: int | None = None
    status: str = "planted"
    notes: str | None = None
    canon_status: str = "draft"
    created_at: str | None = None
    updated_at: str | None = None


class SubplotTouchpoint(BaseModel):
    """Represents a row in the subplot_touchpoint_log table (migration 017)."""
    id: int | None = None
    plot_thread_id: int
    chapter_id: int
    touchpoint_type: str = "advance"
    notes: str | None = None
    created_at: str | None = None
