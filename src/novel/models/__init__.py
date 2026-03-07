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
from novel.models.chapters import Chapter, ChapterStructuralObligation
from novel.models.scenes import Scene, SceneCharacterGoal
from novel.models.plot import ChapterCharacterArc, ChapterPlotThread, PlotThread
from novel.models.arcs import CharacterArc, ArcHealthLog, ChekhovGun, SubplotTouchpoint
from novel.models.voice import SupernaturalVoiceGuideline, VoiceDriftLog, VoiceProfile
from novel.models.sessions import (
    AgentRunLog,
    DecisionsLogEntry,
    OpenQuestion,
    ProjectMetricsSnapshot,
    PovBalanceSnapshot,
    SessionLog,
)
from novel.models.timeline import (
    Event,
    EventArtifact,
    EventParticipant,
    PovChronologicalPosition,
    TravelSegment,
)
from novel.models.canon import (
    CanonFact,
    ContinuityIssue,
    DramaticIronyEntry,
    ForeshadowingEntry,
    MotifEntry,
    MotifOccurrence,
    OppositionPair,
    ProphecyEntry,
    ReaderExperienceNote,
    ReaderInformationState,
    ReaderReveal,
    ThematicMirror,
)
from novel.models.gate import ArchitectureGate, GateChecklistItem
from novel.models.publishing import (
    DocumentationTask,
    PublishingAsset,
    ResearchNote,
    SubmissionEntry,
)
from novel.models.magic import (
    MagicSystemElement,
    MagicUseLog,
    NameRegistryEntry,
    PractitionerAbility,
    SupernaturalElement,
)
from novel.models.pacing import PacingBeat, TensionMeasurement

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
    # chapters domain
    "Chapter",
    "ChapterStructuralObligation",
    # scenes domain
    "Scene",
    "SceneCharacterGoal",
    # plot domain
    "PlotThread",
    "ChapterPlotThread",
    "ChapterCharacterArc",
    # arcs domain
    "CharacterArc",
    "ArcHealthLog",
    "ChekhovGun",
    "SubplotTouchpoint",
    # voice domain
    "VoiceProfile",
    "VoiceDriftLog",
    "SupernaturalVoiceGuideline",
    # sessions domain
    "SessionLog",
    "AgentRunLog",
    "ProjectMetricsSnapshot",
    "PovBalanceSnapshot",
    "OpenQuestion",
    "DecisionsLogEntry",
    # timeline domain
    "Event",
    "EventParticipant",
    "EventArtifact",
    "TravelSegment",
    "PovChronologicalPosition",
    # canon domain
    "CanonFact",
    "ContinuityIssue",
    "ForeshadowingEntry",
    "ProphecyEntry",
    "MotifEntry",
    "MotifOccurrence",
    "ThematicMirror",
    "OppositionPair",
    "ReaderInformationState",
    "ReaderReveal",
    "DramaticIronyEntry",
    "ReaderExperienceNote",
    # gate domain
    "ArchitectureGate",
    "GateChecklistItem",
    # publishing domain
    "PublishingAsset",
    "SubmissionEntry",
    "ResearchNote",
    "DocumentationTask",
    # magic domain
    "MagicSystemElement",
    "SupernaturalElement",
    "MagicUseLog",
    "PractitionerAbility",
    "NameRegistryEntry",
    # pacing domain
    "PacingBeat",
    "TensionMeasurement",
]
