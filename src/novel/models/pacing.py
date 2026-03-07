"""Pacing domain Pydantic models — Pacing beats and tension measurements."""

from pydantic import BaseModel


class PacingBeat(BaseModel):
    """Represents a row in the pacing_beats table (migration 018)."""

    id: int | None = None
    chapter_id: int
    scene_id: int | None = None
    beat_type: str = "action"
    description: str
    sequence_order: int = 0
    notes: str | None = None
    created_at: str | None = None


class TensionMeasurement(BaseModel):
    """Represents a row in the tension_measurements table (migration 018)."""

    id: int | None = None
    chapter_id: int
    tension_level: int = 5
    measurement_type: str = "overall"
    notes: str | None = None
    measured_at: str | None = None
