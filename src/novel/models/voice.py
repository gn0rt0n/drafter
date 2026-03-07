"""Voice domain Pydantic models — Voice profiles and drift log."""

from pydantic import BaseModel


class VoiceProfile(BaseModel):
    """Represents a row in the voice_profiles table (migration 014)."""
    id: int | None = None
    character_id: int
    sentence_length: str | None = None
    vocabulary_level: str | None = None
    speech_patterns: str | None = None
    verbal_tics: str | None = None
    avoids: str | None = None
    internal_voice_notes: str | None = None
    dialogue_sample: str | None = None
    notes: str | None = None
    canon_status: str = "draft"
    created_at: str | None = None
    updated_at: str | None = None


class VoiceDriftLog(BaseModel):
    """Represents a row in the voice_drift_log table (migration 014)."""
    id: int | None = None
    character_id: int
    chapter_id: int | None = None
    scene_id: int | None = None
    drift_type: str = "vocabulary"
    description: str
    severity: str = "minor"
    is_resolved: bool = False
    created_at: str | None = None


class SupernaturalVoiceGuideline(BaseModel):
    """Represents a row in the supernatural_voice_guidelines table (migration 021)."""
    id: int | None = None
    element_name: str
    element_type: str = "creature"
    writing_rules: str
    avoid: str | None = None
    example_phrases: str | None = None
    notes: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
