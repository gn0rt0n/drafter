"""Character domain Pydantic models — Characters and character state-over-time tables."""

from pydantic import BaseModel


class Character(BaseModel):
    """Represents a row in the characters table (migration 007)."""
    id: int | None = None
    name: str
    role: str = "supporting"
    faction_id: int | None = None
    culture_id: int | None = None
    home_era_id: int | None = None
    age: int | None = None
    physical_description: str | None = None
    personality_core: str | None = None
    backstory_summary: str | None = None
    secret: str | None = None
    motivation: str | None = None
    fear: str | None = None
    flaw: str | None = None
    strength: str | None = None
    arc_summary: str | None = None
    voice_signature: str | None = None
    notes: str | None = None
    canon_status: str = "draft"
    source_file: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    reviewed_at: str | None = None


class CharacterKnowledge(BaseModel):
    """Represents a row in the character_knowledge table (migration 013)."""
    id: int | None = None
    character_id: int
    chapter_id: int
    knowledge_type: str = "fact"
    content: str
    source: str | None = None
    is_secret: bool = False
    notes: str | None = None
    created_at: str | None = None


class CharacterBelief(BaseModel):
    """Represents a row in the character_beliefs table (migration 013)."""
    id: int | None = None
    character_id: int
    belief_type: str = "worldview"
    content: str
    strength: int = 5
    formed_chapter_id: int | None = None
    challenged_chapter_id: int | None = None
    notes: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class CharacterLocation(BaseModel):
    """Represents a row in the character_locations table (migration 013)."""
    id: int | None = None
    character_id: int
    chapter_id: int
    location_id: int | None = None
    location_note: str | None = None
    created_at: str | None = None


class InjuryState(BaseModel):
    """Represents a row in the injury_states table (migration 013)."""
    id: int | None = None
    character_id: int
    chapter_id: int
    injury_type: str = "wound"
    description: str
    severity: str = "minor"
    is_resolved: bool = False
    resolved_chapter_id: int | None = None
    notes: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class TitleState(BaseModel):
    """Represents a row in the title_states table (migration 013)."""
    id: int | None = None
    character_id: int
    chapter_id: int
    title: str
    granted_by: str | None = None
    notes: str | None = None
    created_at: str | None = None
