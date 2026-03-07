"""World domain Pydantic models — Books, Eras, Acts, Cultures, Factions, Locations, Artifacts."""

import json

from pydantic import BaseModel, field_validator


class Book(BaseModel):
    """Represents a row in the books table (migration 002)."""
    id: int | None = None
    title: str
    series_order: int | None = None
    word_count_target: int | None = None
    actual_word_count: int = 0
    status: str = "planning"
    notes: str | None = None
    canon_status: str = "draft"
    created_at: str | None = None
    updated_at: str | None = None


class Era(BaseModel):
    """Represents a row in the eras table (migration 002)."""
    id: int | None = None
    name: str
    sequence_order: int | None = None
    date_start: str | None = None
    date_end: str | None = None
    summary: str | None = None
    certainty_level: str = "established"
    notes: str | None = None
    canon_status: str = "draft"
    created_at: str | None = None
    updated_at: str | None = None


class Act(BaseModel):
    """Represents a row in the acts table (migration 003)."""
    id: int | None = None
    book_id: int
    act_number: int
    name: str | None = None
    purpose: str | None = None
    word_count_target: int | None = None
    start_chapter_id: int | None = None
    end_chapter_id: int | None = None
    structural_notes: str | None = None
    canon_status: str = "draft"
    created_at: str | None = None
    updated_at: str | None = None


class Culture(BaseModel):
    """Represents a row in the cultures table (migration 004)."""
    id: int | None = None
    name: str
    region: str | None = None
    language_family: str | None = None
    naming_conventions: str | None = None
    social_structure: str | None = None
    values_beliefs: str | None = None
    taboos: str | None = None
    aesthetic_style: str | None = None
    notes: str | None = None
    canon_status: str = "draft"
    source_file: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class Faction(BaseModel):
    """Represents a row in the factions table (migration 005)."""
    id: int | None = None
    name: str
    faction_type: str | None = None
    leader_character_id: int | None = None
    headquarters: str | None = None
    size_estimate: str | None = None
    goals: str | None = None
    resources: str | None = None
    weaknesses: str | None = None
    alliances: str | None = None
    conflicts: str | None = None
    notes: str | None = None
    canon_status: str = "draft"
    source_file: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class Location(BaseModel):
    """Represents a row in the locations table (migration 006).

    sensory_profile is stored as JSON TEXT in SQLite.
    The field_validator coerces an incoming JSON string to dict automatically.
    Use to_db_dict() when writing back to SQLite.
    """
    id: int | None = None
    name: str
    location_type: str | None = None
    parent_location_id: int | None = None
    culture_id: int | None = None
    controlling_faction_id: int | None = None
    description: str | None = None
    sensory_profile: dict | None = None
    strategic_value: str | None = None
    accessibility: str | None = None
    notable_features: str | None = None
    notes: str | None = None
    canon_status: str = "draft"
    source_file: str | None = None
    created_at: str | None = None
    updated_at: str | None = None

    @field_validator("sensory_profile", mode="before")
    @classmethod
    def _parse_sensory_profile(cls, v: object) -> dict | None:
        if isinstance(v, str):
            return json.loads(v)
        return v

    def to_db_dict(self) -> dict:
        """Return a dict ready for SQLite insertion, serialising sensory_profile to JSON."""
        data = self.model_dump()
        if data["sensory_profile"] is not None:
            data["sensory_profile"] = json.dumps(data["sensory_profile"])
        return data


class Artifact(BaseModel):
    """Represents a row in the artifacts table (migration 010)."""
    id: int | None = None
    name: str
    artifact_type: str | None = None
    current_owner_id: int | None = None
    current_location_id: int | None = None
    origin_era_id: int | None = None
    description: str | None = None
    significance: str | None = None
    magical_properties: str | None = None
    history: str | None = None
    notes: str | None = None
    canon_status: str = "draft"
    source_file: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class ObjectState(BaseModel):
    """Represents a row in the object_states table (migration 021)."""
    id: int | None = None
    artifact_id: int
    chapter_id: int
    owner_id: int | None = None
    location_id: int | None = None
    condition: str = "intact"
    notes: str | None = None
    created_at: str | None = None


class FactionPoliticalState(BaseModel):
    """Represents a row in the faction_political_states table (migration 021)."""
    id: int | None = None
    faction_id: int
    chapter_id: int
    power_level: int = 5
    alliances: str | None = None
    conflicts: str | None = None
    internal_state: str | None = None
    noted_by_character_id: int | None = None
    notes: str | None = None
    created_at: str | None = None
