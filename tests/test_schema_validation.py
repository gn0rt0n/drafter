"""TEST-01: Schema validation — Pydantic model fields vs PRAGMA table_info."""
import sqlite3
import pytest
from novel.db.migrations import apply_migrations
from novel.models import (
    Book, Era, Act, Culture, Faction, Location, Artifact, ObjectState, FactionPoliticalState,
    Character, CharacterKnowledge, CharacterBelief, CharacterLocation, InjuryState, TitleState,
    CharacterRelationship, RelationshipChangeEvent, PerceptionProfile,
    Chapter, ChapterStructuralObligation,
    Scene, SceneCharacterGoal,
    PlotThread, ChapterPlotThread, ChapterCharacterArc,
    CharacterArc, ArcHealthLog, ChekhovGun, SubplotTouchpoint,
    VoiceProfile, VoiceDriftLog, SupernaturalVoiceGuideline,
    SessionLog, AgentRunLog, ProjectMetricsSnapshot, PovBalanceSnapshot, OpenQuestion, DecisionsLogEntry,
    Event, EventParticipant, EventArtifact, TravelSegment, PovChronologicalPosition,
    CanonFact, ContinuityIssue, ForeshadowingEntry, ProphecyEntry, MotifEntry,
    MotifOccurrence, ThematicMirror, OppositionPair, ReaderInformationState, ReaderReveal,
    DramaticIronyEntry, ReaderExperienceNote,
    ArchitectureGate, GateChecklistItem,
    PublishingAsset, SubmissionEntry, ResearchNote, DocumentationTask,
    MagicSystemElement, SupernaturalElement, MagicUseLog, PractitionerAbility, NameRegistryEntry,
    PacingBeat, TensionMeasurement,
)


TABLE_MODEL_MAP = {
    # world
    "books": Book,
    "eras": Era,
    "acts": Act,
    "cultures": Culture,
    "factions": Faction,
    "locations": Location,
    "artifacts": Artifact,
    "object_states": ObjectState,
    "faction_political_states": FactionPoliticalState,
    # characters
    "characters": Character,
    "character_knowledge": CharacterKnowledge,
    "character_beliefs": CharacterBelief,
    "character_locations": CharacterLocation,
    "injury_states": InjuryState,
    "title_states": TitleState,
    # relationships
    "character_relationships": CharacterRelationship,
    "relationship_change_events": RelationshipChangeEvent,
    "perception_profiles": PerceptionProfile,
    # chapters/scenes
    "chapters": Chapter,
    "chapter_structural_obligations": ChapterStructuralObligation,
    "scenes": Scene,
    "scene_character_goals": SceneCharacterGoal,
    # plot/arcs
    "plot_threads": PlotThread,
    "chapter_plot_threads": ChapterPlotThread,
    "chapter_character_arcs": ChapterCharacterArc,
    "character_arcs": CharacterArc,
    "arc_health_log": ArcHealthLog,
    "chekovs_gun_registry": ChekhovGun,
    "subplot_touchpoint_log": SubplotTouchpoint,
    # voice
    "voice_profiles": VoiceProfile,
    "voice_drift_log": VoiceDriftLog,
    "supernatural_voice_guidelines": SupernaturalVoiceGuideline,
    # sessions
    "session_logs": SessionLog,
    "agent_run_log": AgentRunLog,
    "project_metrics_snapshots": ProjectMetricsSnapshot,
    "pov_balance_snapshots": PovBalanceSnapshot,
    "open_questions": OpenQuestion,
    "decisions_log": DecisionsLogEntry,
    # timeline
    "events": Event,
    "event_participants": EventParticipant,
    "event_artifacts": EventArtifact,
    "travel_segments": TravelSegment,
    "pov_chronological_position": PovChronologicalPosition,
    # canon
    "canon_facts": CanonFact,
    "continuity_issues": ContinuityIssue,
    "foreshadowing_registry": ForeshadowingEntry,
    "prophecy_registry": ProphecyEntry,
    "motif_registry": MotifEntry,
    "motif_occurrences": MotifOccurrence,
    "thematic_mirrors": ThematicMirror,
    "opposition_pairs": OppositionPair,
    "reader_information_states": ReaderInformationState,
    "reader_reveals": ReaderReveal,
    "dramatic_irony_inventory": DramaticIronyEntry,
    "reader_experience_notes": ReaderExperienceNote,
    # gate
    "architecture_gate": ArchitectureGate,
    "gate_checklist_items": GateChecklistItem,
    # publishing
    "publishing_assets": PublishingAsset,
    "submission_tracker": SubmissionEntry,
    "research_notes": ResearchNote,
    "documentation_tasks": DocumentationTask,
    # magic
    "magic_system_elements": MagicSystemElement,
    "supernatural_elements": SupernaturalElement,
    "magic_use_log": MagicUseLog,
    "practitioner_abilities": PractitionerAbility,
    "name_registry": NameRegistryEntry,
    # pacing
    "pacing_beats": PacingBeat,
    "tension_measurements": TensionMeasurement,
}


@pytest.fixture(scope="session")
def db_conn():
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys=ON")
    apply_migrations(conn)
    yield conn
    conn.close()


def _get_table_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return {row[1] for row in rows}


@pytest.mark.parametrize("table,model_class", list(TABLE_MODEL_MAP.items()))
def test_model_matches_schema(table, model_class, db_conn):
    db_cols = _get_table_columns(db_conn, table)
    model_fields = set(model_class.model_fields.keys())
    missing_from_model = db_cols - model_fields
    extra_in_model = model_fields - db_cols
    assert not missing_from_model, (
        f"{model_class.__name__} is missing fields for SQL columns: {missing_from_model}"
    )
    assert not extra_in_model, (
        f"{model_class.__name__} has extra fields not in SQL schema: {extra_in_model}"
    )
