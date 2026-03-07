"""Magic domain Pydantic models — Magic system elements, supernatural elements, use log, practitioners, name registry."""

from pydantic import BaseModel


class MagicSystemElement(BaseModel):
    """Represents a row in the magic_system_elements table (migration 011)."""

    id: int | None = None
    name: str
    element_type: str = "ability"
    rules: str | None = None
    limitations: str | None = None
    costs: str | None = None
    exceptions: str | None = None
    introduced_chapter_id: int | None = None
    notes: str | None = None
    canon_status: str = "draft"
    created_at: str | None = None
    updated_at: str | None = None


class SupernaturalElement(BaseModel):
    """Represents a row in the supernatural_elements table (migration 011)."""

    id: int | None = None
    name: str
    element_type: str = "creature"
    description: str | None = None
    rules: str | None = None
    voice_guidelines: str | None = None
    introduced_chapter_id: int | None = None
    notes: str | None = None
    canon_status: str = "draft"
    created_at: str | None = None
    updated_at: str | None = None


class MagicUseLog(BaseModel):
    """Represents a row in the magic_use_log table (migration 021)."""

    id: int | None = None
    chapter_id: int
    scene_id: int | None = None
    character_id: int
    magic_element_id: int | None = None
    action_description: str
    cost_paid: str | None = None
    compliance_status: str = "compliant"
    notes: str | None = None
    created_at: str | None = None


class PractitionerAbility(BaseModel):
    """Represents a row in the practitioner_abilities table (migration 021)."""

    id: int | None = None
    character_id: int
    magic_element_id: int
    proficiency_level: int = 1
    acquired_chapter_id: int | None = None
    notes: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class NameRegistryEntry(BaseModel):
    """Represents a row in the name_registry table (migration 021)."""

    id: int | None = None
    name: str
    entity_type: str = "character"
    culture_id: int | None = None
    linguistic_notes: str | None = None
    introduced_chapter_id: int | None = None
    notes: str | None = None
    created_at: str | None = None
