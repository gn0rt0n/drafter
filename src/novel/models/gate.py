"""Gate domain Pydantic models — Architecture gate and checklist items."""

from pydantic import BaseModel, field_validator


class ArchitectureGate(BaseModel):
    """Represents a row in the architecture_gate table (migration 020)."""

    id: int | None = None
    is_certified: bool = False
    certified_at: str | None = None
    certified_by: str | None = None
    checklist_version: int = 1
    notes: str | None = None
    created_at: str | None = None
    updated_at: str | None = None

    @field_validator("is_certified", mode="before")
    @classmethod
    def coerce_bool(cls, v: object) -> bool:
        """Coerce SQLite INTEGER 0/1 to bool."""
        if isinstance(v, int):
            return bool(v)
        return v  # type: ignore[return-value]


class GateChecklistItem(BaseModel):
    """Represents a row in the gate_checklist_items table (migration 020)."""

    id: int | None = None
    gate_id: int
    item_key: str
    category: str = "general"
    description: str
    is_passing: bool = False
    missing_count: int = 0
    last_checked_at: str | None = None
    notes: str | None = None

    @field_validator("is_passing", mode="before")
    @classmethod
    def coerce_bool(cls, v: object) -> bool:
        """Coerce SQLite INTEGER 0/1 to bool."""
        if isinstance(v, int):
            return bool(v)
        return v  # type: ignore[return-value]
