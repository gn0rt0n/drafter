-- Migration 006: Locations (FK to cultures, factions; self-referential parent_location_id)
CREATE TABLE IF NOT EXISTS locations (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    name                TEXT    NOT NULL,
    location_type       TEXT,
    parent_location_id  INTEGER REFERENCES locations(id),   -- nullable self-ref
    culture_id          INTEGER REFERENCES cultures(id),
    controlling_faction_id INTEGER REFERENCES factions(id),
    description         TEXT,
    sensory_profile     TEXT,   -- JSON: {sight, sound, smell, touch, taste}
    strategic_value     TEXT,
    accessibility       TEXT,
    notable_features    TEXT,
    notes               TEXT,
    canon_status        TEXT    NOT NULL DEFAULT 'draft',
    source_file         TEXT,
    created_at          TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at          TEXT    NOT NULL DEFAULT (datetime('now'))
);
