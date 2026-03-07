-- Migration 021: Remaining literary, continuity, canon, publishing, and utility tables.
-- This is the largest migration — 24 tables grouped by domain.

-- Reader knowledge state
CREATE TABLE IF NOT EXISTS reader_information_states (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    chapter_id      INTEGER NOT NULL REFERENCES chapters(id),
    domain          TEXT    NOT NULL DEFAULT 'general',
    information     TEXT    NOT NULL,
    revealed_how    TEXT,
    notes           TEXT,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE(chapter_id, domain)
);

CREATE TABLE IF NOT EXISTS reader_reveals (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    chapter_id      INTEGER REFERENCES chapters(id),
    scene_id        INTEGER REFERENCES scenes(id),
    character_id    INTEGER REFERENCES characters(id),
    reveal_type     TEXT    NOT NULL DEFAULT 'exposition',
    planned_reveal  TEXT,
    actual_reveal   TEXT,
    reader_impact   TEXT,
    notes           TEXT,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS dramatic_irony_inventory (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    chapter_id      INTEGER NOT NULL REFERENCES chapters(id),
    reader_knows    TEXT    NOT NULL,
    character_id    INTEGER REFERENCES characters(id),
    character_doesnt_know TEXT NOT NULL,
    irony_type      TEXT    NOT NULL DEFAULT 'situational',
    tension_level   INTEGER NOT NULL DEFAULT 5,
    resolved        INTEGER NOT NULL DEFAULT 0,
    resolved_chapter_id INTEGER REFERENCES chapters(id),
    notes           TEXT,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS reader_experience_notes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    chapter_id      INTEGER REFERENCES chapters(id),
    scene_id        INTEGER REFERENCES scenes(id),
    note_type       TEXT    NOT NULL DEFAULT 'pacing',
    content         TEXT    NOT NULL,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- Canon and continuity
CREATE TABLE IF NOT EXISTS canon_facts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    domain          TEXT    NOT NULL DEFAULT 'general',
    fact            TEXT    NOT NULL,
    source_chapter_id INTEGER REFERENCES chapters(id),
    source_event_id INTEGER REFERENCES events(id),
    parent_fact_id  INTEGER REFERENCES canon_facts(id),  -- self-ref for derived facts
    certainty_level TEXT    NOT NULL DEFAULT 'established',
    canon_status    TEXT    NOT NULL DEFAULT 'approved',
    notes           TEXT,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS continuity_issues (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    severity        TEXT    NOT NULL DEFAULT 'minor',
    description     TEXT    NOT NULL,
    chapter_id      INTEGER REFERENCES chapters(id),
    scene_id        INTEGER REFERENCES scenes(id),
    canon_fact_id   INTEGER REFERENCES canon_facts(id),
    is_resolved     INTEGER NOT NULL DEFAULT 0,
    resolution_note TEXT,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS decisions_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    decision_type   TEXT    NOT NULL DEFAULT 'plot',
    description     TEXT    NOT NULL,
    rationale       TEXT,
    alternatives    TEXT,
    session_id      INTEGER REFERENCES session_logs(id),
    chapter_id      INTEGER REFERENCES chapters(id),
    created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- Foreshadowing and literary devices
CREATE TABLE IF NOT EXISTS foreshadowing_registry (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    description         TEXT    NOT NULL,
    plant_chapter_id    INTEGER NOT NULL REFERENCES chapters(id),
    plant_scene_id      INTEGER REFERENCES scenes(id),
    payoff_chapter_id   INTEGER REFERENCES chapters(id),
    payoff_scene_id     INTEGER REFERENCES scenes(id),
    foreshadowing_type  TEXT    NOT NULL DEFAULT 'direct',
    status              TEXT    NOT NULL DEFAULT 'planted',
    notes               TEXT,
    created_at          TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at          TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS prophecy_registry (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    name                TEXT    NOT NULL,
    text                TEXT    NOT NULL,
    subject_character_id INTEGER REFERENCES characters(id),
    source_character_id INTEGER REFERENCES characters(id),
    uttered_chapter_id  INTEGER REFERENCES chapters(id),
    fulfilled_chapter_id INTEGER REFERENCES chapters(id),
    status              TEXT    NOT NULL DEFAULT 'active',
    interpretation      TEXT,
    notes               TEXT,
    canon_status        TEXT    NOT NULL DEFAULT 'draft',
    created_at          TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at          TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS motif_registry (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT    NOT NULL UNIQUE,
    motif_type      TEXT    NOT NULL DEFAULT 'symbol',
    description     TEXT    NOT NULL,
    thematic_role   TEXT,
    first_appearance_chapter_id INTEGER REFERENCES chapters(id),
    notes           TEXT,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS motif_occurrences (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    motif_id        INTEGER NOT NULL REFERENCES motif_registry(id),
    chapter_id      INTEGER NOT NULL REFERENCES chapters(id),
    scene_id        INTEGER REFERENCES scenes(id),
    description     TEXT,
    occurrence_type TEXT    NOT NULL DEFAULT 'direct',
    notes           TEXT,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS thematic_mirrors (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    name                TEXT    NOT NULL,
    mirror_type         TEXT    NOT NULL DEFAULT 'character',
    element_a_id        INTEGER NOT NULL,
    element_a_type      TEXT    NOT NULL DEFAULT 'character',
    element_b_id        INTEGER NOT NULL,
    element_b_type      TEXT    NOT NULL DEFAULT 'character',
    mirror_description  TEXT,
    thematic_purpose    TEXT,
    notes               TEXT,
    created_at          TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS opposition_pairs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT    NOT NULL,
    concept_a       TEXT    NOT NULL,
    concept_b       TEXT    NOT NULL,
    manifested_in   TEXT,
    resolved_chapter_id INTEGER REFERENCES chapters(id),
    notes           TEXT,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- World state tracking
CREATE TABLE IF NOT EXISTS faction_political_states (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    faction_id      INTEGER NOT NULL REFERENCES factions(id),
    chapter_id      INTEGER NOT NULL REFERENCES chapters(id),
    power_level     INTEGER NOT NULL DEFAULT 5,
    alliances       TEXT,
    conflicts       TEXT,
    internal_state  TEXT,
    noted_by_character_id INTEGER REFERENCES characters(id),
    notes           TEXT,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE(faction_id, chapter_id)
);

CREATE TABLE IF NOT EXISTS object_states (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    artifact_id     INTEGER NOT NULL REFERENCES artifacts(id),
    chapter_id      INTEGER NOT NULL REFERENCES chapters(id),
    owner_id        INTEGER REFERENCES characters(id),
    location_id     INTEGER REFERENCES locations(id),
    condition       TEXT    NOT NULL DEFAULT 'intact',
    notes           TEXT,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE(artifact_id, chapter_id)
);

-- Voice and writing guidelines
CREATE TABLE IF NOT EXISTS supernatural_voice_guidelines (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    element_name    TEXT    NOT NULL UNIQUE,
    element_type    TEXT    NOT NULL DEFAULT 'creature',
    writing_rules   TEXT    NOT NULL,
    avoid           TEXT,
    example_phrases TEXT,
    notes           TEXT,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- Magic use log and practitioner abilities
CREATE TABLE IF NOT EXISTS magic_use_log (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    chapter_id          INTEGER NOT NULL REFERENCES chapters(id),
    scene_id            INTEGER REFERENCES scenes(id),
    character_id        INTEGER NOT NULL REFERENCES characters(id),
    magic_element_id    INTEGER REFERENCES magic_system_elements(id),
    action_description  TEXT    NOT NULL,
    cost_paid           TEXT,
    compliance_status   TEXT    NOT NULL DEFAULT 'compliant',
    notes               TEXT,
    created_at          TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS practitioner_abilities (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    character_id        INTEGER NOT NULL REFERENCES characters(id),
    magic_element_id    INTEGER NOT NULL REFERENCES magic_system_elements(id),
    proficiency_level   INTEGER NOT NULL DEFAULT 1,
    acquired_chapter_id INTEGER REFERENCES chapters(id),
    notes               TEXT,
    created_at          TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at          TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE(character_id, magic_element_id)
);

-- Names registry
CREATE TABLE IF NOT EXISTS name_registry (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT    NOT NULL UNIQUE,
    entity_type     TEXT    NOT NULL DEFAULT 'character',
    culture_id      INTEGER REFERENCES cultures(id),
    linguistic_notes TEXT,
    introduced_chapter_id INTEGER REFERENCES chapters(id),
    notes           TEXT,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- Research and utility tables
CREATE TABLE IF NOT EXISTS research_notes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    topic           TEXT    NOT NULL,
    content         TEXT    NOT NULL,
    source          TEXT,
    relevance       TEXT,
    notes           TEXT,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS open_questions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    question        TEXT    NOT NULL,
    domain          TEXT    NOT NULL DEFAULT 'general',
    session_id      INTEGER REFERENCES session_logs(id),
    answer          TEXT,
    answered_at     TEXT,
    priority        TEXT    NOT NULL DEFAULT 'normal',
    notes           TEXT,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS documentation_tasks (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    title           TEXT    NOT NULL,
    description     TEXT,
    status          TEXT    NOT NULL DEFAULT 'pending',
    priority        TEXT    NOT NULL DEFAULT 'normal',
    due_chapter_id  INTEGER REFERENCES chapters(id),
    completed_at    TEXT,
    notes           TEXT,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- Publishing
CREATE TABLE IF NOT EXISTS publishing_assets (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_type      TEXT    NOT NULL DEFAULT 'query_letter',
    title           TEXT    NOT NULL,
    content         TEXT    NOT NULL,
    version         INTEGER NOT NULL DEFAULT 1,
    status          TEXT    NOT NULL DEFAULT 'draft',
    notes           TEXT,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS submission_tracker (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id        INTEGER REFERENCES publishing_assets(id),
    agency_or_publisher TEXT NOT NULL,
    submitted_at    TEXT    NOT NULL,
    status          TEXT    NOT NULL DEFAULT 'pending',
    response_at     TEXT,
    response_notes  TEXT,
    follow_up_due   TEXT,
    notes           TEXT,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- Indexes for commonly queried FKs in migration 021
CREATE INDEX IF NOT EXISTS idx_canon_facts_domain ON canon_facts(domain);
CREATE INDEX IF NOT EXISTS idx_continuity_issues_severity ON continuity_issues(severity, is_resolved);
CREATE INDEX IF NOT EXISTS idx_foreshadowing_status ON foreshadowing_registry(status);
CREATE INDEX IF NOT EXISTS idx_magic_use_chapter ON magic_use_log(chapter_id);
CREATE INDEX IF NOT EXISTS idx_open_questions_domain ON open_questions(domain, answered_at);
