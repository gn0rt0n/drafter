"""Scene domain Pydantic models — Scenes and per-scene character goals."""

import json

from pydantic import BaseModel, field_validator


class Scene(BaseModel):
    """Represents a row in the scenes table (migration 009).

    narrative_functions is stored as JSON TEXT in SQLite.
    The field_validator coerces an incoming JSON string to list[str] automatically.
    Use to_db_dict() when writing back to SQLite.
    """
    id: int | None = None
    chapter_id: int
    scene_number: int
    location_id: int | None = None
    time_marker: str | None = None
    summary: str | None = None
    scene_type: str = "action"
    dramatic_question: str | None = None
    scene_goal: str | None = None
    obstacle: str | None = None
    turn: str | None = None
    consequence: str | None = None
    emotional_function: str | None = None
    narrative_functions: list[str] | None = None
    word_count_target: int | None = None
    status: str = "planned"
    notes: str | None = None
    canon_status: str = "draft"
    created_at: str | None = None
    updated_at: str | None = None

    @field_validator("narrative_functions", mode="before")
    @classmethod
    def _parse_narrative_functions(cls, v: object) -> list[str] | None:
        if isinstance(v, str):
            return json.loads(v)
        return v

    def to_db_dict(self) -> dict:
        """Return a dict ready for SQLite insertion, serialising narrative_functions to JSON."""
        data = self.model_dump()
        if data["narrative_functions"] is not None:
            data["narrative_functions"] = json.dumps(data["narrative_functions"])
        return data


class SceneCharacterGoal(BaseModel):
    """Represents a row in the scene_character_goals table (migration 018)."""
    id: int | None = None
    scene_id: int
    character_id: int
    goal: str
    obstacle: str | None = None
    outcome: str | None = None
    notes: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
