-- Migration 013: Character state-over-time tables
CREATE TABLE IF NOT EXISTS character_knowledge (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    character_id    INTEGER NOT NULL REFERENCES characters(id),
    chapter_id      INTEGER NOT NULL REFERENCES chapters(id),
    knowledge_type  TEXT    NOT NULL DEFAULT 'fact',
    content         TEXT    NOT NULL,
    source          TEXT,
    is_secret       INTEGER NOT NULL DEFAULT 0,
    notes           TEXT,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS character_beliefs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    character_id    INTEGER NOT NULL REFERENCES characters(id),
    belief_type     TEXT    NOT NULL DEFAULT 'worldview',
    content         TEXT    NOT NULL,
    strength        INTEGER NOT NULL DEFAULT 5,
    formed_chapter_id INTEGER REFERENCES chapters(id),
    challenged_chapter_id INTEGER REFERENCES chapters(id),
    notes           TEXT,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS character_locations (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    character_id    INTEGER NOT NULL REFERENCES characters(id),
    chapter_id      INTEGER NOT NULL REFERENCES chapters(id),
    location_id     INTEGER REFERENCES locations(id),
    location_note   TEXT,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS injury_states (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    character_id    INTEGER NOT NULL REFERENCES characters(id),
    chapter_id      INTEGER NOT NULL REFERENCES chapters(id),
    injury_type     TEXT    NOT NULL DEFAULT 'wound',
    description     TEXT    NOT NULL,
    severity        TEXT    NOT NULL DEFAULT 'minor',
    is_resolved     INTEGER NOT NULL DEFAULT 0,
    resolved_chapter_id INTEGER REFERENCES chapters(id),
    notes           TEXT,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS title_states (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    character_id    INTEGER NOT NULL REFERENCES characters(id),
    chapter_id      INTEGER NOT NULL REFERENCES chapters(id),
    title           TEXT    NOT NULL,
    granted_by      TEXT,
    notes           TEXT,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_char_knowledge_char ON character_knowledge(character_id);
CREATE INDEX IF NOT EXISTS idx_char_beliefs_char ON character_beliefs(character_id);
CREATE INDEX IF NOT EXISTS idx_injury_states_char ON injury_states(character_id);
