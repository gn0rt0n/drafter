-- Migration 004: Cultures (no FK dependencies on other user tables)
CREATE TABLE IF NOT EXISTS cultures (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    name                 TEXT    NOT NULL UNIQUE,
    region               TEXT,
    language_family      TEXT,
    naming_conventions   TEXT,
    social_structure     TEXT,
    values_beliefs       TEXT,
    taboos               TEXT,
    aesthetic_style      TEXT,
    notes                TEXT,
    canon_status         TEXT    NOT NULL DEFAULT 'draft',
    source_file          TEXT,
    created_at           TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at           TEXT    NOT NULL DEFAULT (datetime('now'))
);
