"""TEST-02: Clean-rebuild test — migrate, FK check, seed, FK check, coverage."""
import sqlite3
from novel.db.migrations import apply_migrations
from novel.db.seed import load_seed_profile


def test_migrate_and_fk_check():
    """All 21 migrations apply cleanly with zero FK violations."""
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys=ON")
    apply_migrations(conn)
    violations = conn.execute("PRAGMA foreign_key_check").fetchall()
    assert violations == [], f"FK violations after migrate: {violations}"
    conn.close()


def test_seed_minimal_fk_check():
    """Minimal seed inserts cleanly with FK enforcement enabled."""
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys=ON")
    apply_migrations(conn)
    load_seed_profile(conn, "minimal")
    violations = conn.execute("PRAGMA foreign_key_check").fetchall()
    assert violations == [], f"FK violations after seed: {violations}"
    conn.close()


def test_seed_minimal_coverage():
    """Every required domain table has at least 1 row after minimal seed."""
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys=ON")
    apply_migrations(conn)
    load_seed_profile(conn, "minimal")

    required_tables = [
        "books", "eras", "cultures", "factions", "characters",
        "acts", "locations", "chapters", "scenes",
        "artifacts", "magic_system_elements", "supernatural_elements",
        "character_relationships", "perception_profiles", "voice_profiles",
        "events", "pov_chronological_position", "travel_segments",
        "plot_threads", "character_arcs", "chapter_plot_threads",
        "chapter_structural_obligations", "chekovs_gun_registry",
        "arc_health_log", "scene_character_goals",
        "pacing_beats", "tension_measurements",
        "session_logs", "architecture_gate", "gate_checklist_items",
        "open_questions", "decisions_log", "canon_facts",
        "foreshadowing_registry", "prophecy_registry",
        "motif_registry", "motif_occurrences",
        "reader_information_states", "faction_political_states",
        "practitioner_abilities", "name_registry",
        "publishing_assets",
        "character_knowledge", "character_beliefs", "character_locations",
        "injury_states", "voice_drift_log",
        "continuity_issues", "thematic_mirrors",
        "research_notes",
    ]
    for table in required_tables:
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        assert count >= 1, f"Table '{table}' has 0 rows after minimal seed"
    conn.close()
