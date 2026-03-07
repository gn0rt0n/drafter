"""Pydantic domain models — populated in Phase 2.

Re-exports all model classes so downstream code can use:
    from novel.models import Character, Location, NotFoundResponse
"""

from novel.models.shared import GateViolation, NotFoundResponse, ValidationFailure
from novel.models.world import (
    Act,
    Artifact,
    Book,
    Culture,
    Era,
    Faction,
    FactionPoliticalState,
    Location,
    ObjectState,
)
from novel.models.characters import (
    Character,
    CharacterBelief,
    CharacterKnowledge,
    CharacterLocation,
    InjuryState,
    TitleState,
)
from novel.models.relationships import (
    CharacterRelationship,
    PerceptionProfile,
    RelationshipChangeEvent,
)

__all__ = [
    # shared error contract
    "NotFoundResponse",
    "ValidationFailure",
    "GateViolation",
    # world domain
    "Book",
    "Era",
    "Act",
    "Culture",
    "Faction",
    "Location",
    "Artifact",
    "ObjectState",
    "FactionPoliticalState",
    # character domain
    "Character",
    "CharacterKnowledge",
    "CharacterBelief",
    "CharacterLocation",
    "InjuryState",
    "TitleState",
    # relationship domain
    "CharacterRelationship",
    "RelationshipChangeEvent",
    "PerceptionProfile",
]
