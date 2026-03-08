"""Timeline domain Pydantic models — Events, participants, artifacts, travel, POV positions."""

from pydantic import BaseModel


class Event(BaseModel):
    """Represents a row in the events table (migration 015)."""

    id: int | None = None
    name: str
    event_type: str = "plot"
    chapter_id: int | None = None
    location_id: int | None = None
    in_story_date: str | None = None
    duration: str | None = None
    summary: str | None = None
    significance: str | None = None
    notes: str | None = None
    canon_status: str = "draft"
    created_at: str | None = None
    updated_at: str | None = None


class EventParticipant(BaseModel):
    """Represents a row in the event_participants table (migration 015)."""

    id: int | None = None
    event_id: int
    character_id: int
    role: str = "participant"
    notes: str | None = None


class EventArtifact(BaseModel):
    """Represents a row in the event_artifacts table (migration 015)."""

    id: int | None = None
    event_id: int
    artifact_id: int
    involvement: str | None = None


class TravelSegment(BaseModel):
    """Represents a row in the travel_segments table (migration 015)."""

    id: int | None = None
    character_id: int
    from_location_id: int | None = None
    to_location_id: int | None = None
    start_chapter_id: int | None = None
    end_chapter_id: int | None = None
    start_event_id: int | None = None
    elapsed_days: int | None = None
    travel_method: str | None = None
    notes: str | None = None
    created_at: str | None = None


class PovChronologicalPosition(BaseModel):
    """Represents a row in the pov_chronological_position table (migration 015)."""

    id: int | None = None
    character_id: int
    chapter_id: int
    in_story_date: str | None = None
    day_number: int | None = None
    location_id: int | None = None
    notes: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class TravelValidationResult(BaseModel):
    """Result of travel realism validation for a travel segment or character."""

    is_realistic: bool
    issues: list[str]
    segment: TravelSegment | None = None
