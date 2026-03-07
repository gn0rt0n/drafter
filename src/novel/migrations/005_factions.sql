-- Migration 005: Factions
-- leader_character_id is nullable because characters are defined in migration 007.
-- Resolved: populate leader_character_id after characters are created.
CREATE TABLE IF NOT EXISTS factions (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    name               TEXT    NOT NULL UNIQUE,
    faction_type       TEXT,
    leader_character_id INTEGER REFERENCES characters(id),  -- nullable: characters defined later
    headquarters       TEXT,
    size_estimate      TEXT,
    goals              TEXT,
    resources          TEXT,
    weaknesses         TEXT,
    alliances          TEXT,
    conflicts          TEXT,
    notes              TEXT,
    canon_status       TEXT    NOT NULL DEFAULT 'draft',
    source_file        TEXT,
    created_at         TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at         TEXT    NOT NULL DEFAULT (datetime('now'))
);
