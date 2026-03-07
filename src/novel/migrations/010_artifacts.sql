-- Migration 010: Artifacts (FK to characters, locations, eras — all nullable)
CREATE TABLE IF NOT EXISTS artifacts (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    name                TEXT    NOT NULL,
    artifact_type       TEXT,
    current_owner_id    INTEGER REFERENCES characters(id),
    current_location_id INTEGER REFERENCES locations(id),
    origin_era_id       INTEGER REFERENCES eras(id),
    description         TEXT,
    significance        TEXT,
    magical_properties  TEXT,
    history             TEXT,
    notes               TEXT,
    canon_status        TEXT    NOT NULL DEFAULT 'draft',
    source_file         TEXT,
    created_at          TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at          TEXT    NOT NULL DEFAULT (datetime('now'))
);
