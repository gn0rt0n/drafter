"""Relationship domain Pydantic models — CharacterRelationship, RelationshipChangeEvent, PerceptionProfile."""

from pydantic import BaseModel


class CharacterRelationship(BaseModel):
    """Represents a row in the character_relationships table (migration 012)."""
    id: int | None = None
    character_a_id: int
    character_b_id: int
    relationship_type: str = "acquaintance"
    bond_strength: int = 0
    trust_level: int = 0
    current_status: str = "neutral"
    history_summary: str | None = None
    first_meeting_chapter_id: int | None = None
    notes: str | None = None
    canon_status: str = "draft"
    created_at: str | None = None
    updated_at: str | None = None


class RelationshipChangeEvent(BaseModel):
    """Represents a row in the relationship_change_events table (migration 012)."""
    id: int | None = None
    relationship_id: int
    chapter_id: int | None = None
    event_id: int | None = None
    change_type: str = "shift"
    description: str
    bond_delta: int = 0
    trust_delta: int = 0
    created_at: str | None = None


class PerceptionProfile(BaseModel):
    """Represents a row in the perception_profiles table (migration 012)."""
    id: int | None = None
    observer_id: int
    subject_id: int
    chapter_id: int | None = None
    perceived_traits: str | None = None
    trust_level: int = 0
    emotional_valence: str = "neutral"
    misperceptions: str | None = None
    notes: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
