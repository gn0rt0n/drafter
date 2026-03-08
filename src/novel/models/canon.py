"""Canon domain Pydantic models — Canon facts, continuity, foreshadowing, prophecy, motifs, mirrors, opposition, reader experience."""

from pydantic import BaseModel


class CanonFact(BaseModel):
    """Represents a row in the canon_facts table (migration 021)."""

    id: int | None = None
    domain: str = "general"
    fact: str
    source_chapter_id: int | None = None
    source_event_id: int | None = None
    parent_fact_id: int | None = None
    certainty_level: str = "established"
    canon_status: str = "approved"
    notes: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class ContinuityIssue(BaseModel):
    """Represents a row in the continuity_issues table (migration 021)."""

    id: int | None = None
    severity: str = "minor"
    description: str
    chapter_id: int | None = None
    scene_id: int | None = None
    canon_fact_id: int | None = None
    is_resolved: bool = False
    resolution_note: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class ForeshadowingEntry(BaseModel):
    """Represents a row in the foreshadowing_registry table (migration 021)."""

    id: int | None = None
    description: str
    plant_chapter_id: int
    plant_scene_id: int | None = None
    payoff_chapter_id: int | None = None
    payoff_scene_id: int | None = None
    foreshadowing_type: str = "direct"
    status: str = "planted"
    notes: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class ProphecyEntry(BaseModel):
    """Represents a row in the prophecy_registry table (migration 021)."""

    id: int | None = None
    name: str
    text: str
    subject_character_id: int | None = None
    source_character_id: int | None = None
    uttered_chapter_id: int | None = None
    fulfilled_chapter_id: int | None = None
    status: str = "active"
    interpretation: str | None = None
    notes: str | None = None
    canon_status: str = "draft"
    created_at: str | None = None
    updated_at: str | None = None


class MotifEntry(BaseModel):
    """Represents a row in the motif_registry table (migration 021)."""

    id: int | None = None
    name: str
    motif_type: str = "symbol"
    description: str
    thematic_role: str | None = None
    first_appearance_chapter_id: int | None = None
    notes: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class MotifOccurrence(BaseModel):
    """Represents a row in the motif_occurrences table (migration 021)."""

    id: int | None = None
    motif_id: int
    chapter_id: int
    scene_id: int | None = None
    description: str | None = None
    occurrence_type: str = "direct"
    notes: str | None = None
    created_at: str | None = None


class ThematicMirror(BaseModel):
    """Represents a row in the thematic_mirrors table (migration 021).

    element_a_id and element_b_id are plain ints (no FK constraint — polymorphic
    references that may point to characters, locations, or other entities).
    """

    id: int | None = None
    name: str
    mirror_type: str = "character"
    element_a_id: int
    element_a_type: str = "character"
    element_b_id: int
    element_b_type: str = "character"
    mirror_description: str | None = None
    thematic_purpose: str | None = None
    notes: str | None = None
    created_at: str | None = None


class OppositionPair(BaseModel):
    """Represents a row in the opposition_pairs table (migration 021)."""

    id: int | None = None
    name: str
    concept_a: str
    concept_b: str
    manifested_in: str | None = None
    resolved_chapter_id: int | None = None
    notes: str | None = None
    created_at: str | None = None


class ReaderInformationState(BaseModel):
    """Represents a row in the reader_information_states table (migration 021)."""

    id: int | None = None
    chapter_id: int
    domain: str = "general"
    information: str
    revealed_how: str | None = None
    notes: str | None = None
    created_at: str | None = None


class ReaderReveal(BaseModel):
    """Represents a row in the reader_reveals table (migration 021)."""

    id: int | None = None
    chapter_id: int | None = None
    scene_id: int | None = None
    character_id: int | None = None
    reveal_type: str = "exposition"
    planned_reveal: str | None = None
    actual_reveal: str | None = None
    reader_impact: str | None = None
    notes: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class DramaticIronyEntry(BaseModel):
    """Represents a row in the dramatic_irony_inventory table (migration 021)."""

    id: int | None = None
    chapter_id: int
    reader_knows: str
    character_id: int | None = None
    character_doesnt_know: str
    irony_type: str = "situational"
    tension_level: int = 5
    resolved: bool = False
    resolved_chapter_id: int | None = None
    notes: str | None = None
    created_at: str | None = None


class ReaderExperienceNote(BaseModel):
    """Represents a row in the reader_experience_notes table (migration 021)."""

    id: int | None = None
    chapter_id: int | None = None
    scene_id: int | None = None
    note_type: str = "pacing"
    content: str
    created_at: str | None = None


class StoryDecision(BaseModel):
    """Represents a row in the decisions_log table (migration 021)."""

    id: int | None = None
    decision_type: str = "plot"
    description: str
    rationale: str | None = None
    alternatives: str | None = None
    session_id: int | None = None
    chapter_id: int | None = None
    created_at: str | None = None
