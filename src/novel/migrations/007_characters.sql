-- Migration 007: Characters
-- FK to factions, cultures, eras are all nullable (tables exist but data populated later).
CREATE TABLE IF NOT EXISTS characters (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    name                TEXT    NOT NULL,
    role                TEXT    NOT NULL DEFAULT 'supporting',
    faction_id          INTEGER REFERENCES factions(id),
    culture_id          INTEGER REFERENCES cultures(id),
    home_era_id         INTEGER REFERENCES eras(id),
    age                 INTEGER,
    physical_description TEXT,
    personality_core    TEXT,
    backstory_summary   TEXT,
    secret              TEXT,
    motivation          TEXT,
    fear                TEXT,
    flaw                TEXT,
    strength            TEXT,
    arc_summary         TEXT,
    voice_signature     TEXT,
    notes               TEXT,
    canon_status        TEXT    NOT NULL DEFAULT 'draft',
    source_file         TEXT,
    created_at          TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at          TEXT    NOT NULL DEFAULT (datetime('now')),
    reviewed_at         TEXT
);

CREATE INDEX IF NOT EXISTS idx_characters_faction ON characters(faction_id);
CREATE INDEX IF NOT EXISTS idx_characters_culture ON characters(culture_id);
