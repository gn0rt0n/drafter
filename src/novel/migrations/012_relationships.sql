-- Migration 012: Character relationships, change events, perception profiles
-- Note: event_id FK references events (defined in 015). Nullable FK defined here
-- before events table exists — SQLite does not check FK target at DDL time, only at DML time.
CREATE TABLE IF NOT EXISTS character_relationships (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    character_a_id      INTEGER NOT NULL REFERENCES characters(id),
    character_b_id      INTEGER NOT NULL REFERENCES characters(id),
    relationship_type   TEXT    NOT NULL DEFAULT 'acquaintance',
    bond_strength       INTEGER NOT NULL DEFAULT 0,
    trust_level         INTEGER NOT NULL DEFAULT 0,
    current_status      TEXT    NOT NULL DEFAULT 'neutral',
    history_summary     TEXT,
    first_meeting_chapter_id INTEGER REFERENCES chapters(id),
    notes               TEXT,
    canon_status        TEXT    NOT NULL DEFAULT 'draft',
    created_at          TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at          TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE(character_a_id, character_b_id)
);

CREATE TABLE IF NOT EXISTS relationship_change_events (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    relationship_id     INTEGER NOT NULL REFERENCES character_relationships(id),
    chapter_id          INTEGER REFERENCES chapters(id),
    event_id            INTEGER REFERENCES events(id),   -- nullable; events defined in 015
    change_type         TEXT    NOT NULL DEFAULT 'shift',
    description         TEXT    NOT NULL,
    bond_delta          INTEGER NOT NULL DEFAULT 0,
    trust_delta         INTEGER NOT NULL DEFAULT 0,
    created_at          TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS perception_profiles (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    observer_id         INTEGER NOT NULL REFERENCES characters(id),
    subject_id          INTEGER NOT NULL REFERENCES characters(id),
    chapter_id          INTEGER REFERENCES chapters(id),
    perceived_traits    TEXT,
    trust_level         INTEGER NOT NULL DEFAULT 0,
    emotional_valence   TEXT    NOT NULL DEFAULT 'neutral',
    misperceptions      TEXT,
    notes               TEXT,
    created_at          TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at          TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE(observer_id, subject_id)
);

CREATE INDEX IF NOT EXISTS idx_relationships_char_a ON character_relationships(character_a_id);
CREATE INDEX IF NOT EXISTS idx_relationships_char_b ON character_relationships(character_b_id);
