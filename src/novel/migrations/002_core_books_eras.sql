-- Migration 002: Eras and books (no cross-table FK dependencies)
CREATE TABLE IF NOT EXISTS eras (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT    NOT NULL,
    sequence_order  INTEGER,
    date_start      TEXT,
    date_end        TEXT,
    summary         TEXT,
    certainty_level TEXT    NOT NULL DEFAULT 'established',
    notes           TEXT,
    canon_status    TEXT    NOT NULL DEFAULT 'draft',
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS books (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    title             TEXT    NOT NULL,
    series_order      INTEGER,
    word_count_target INTEGER,
    actual_word_count INTEGER NOT NULL DEFAULT 0,
    status            TEXT    NOT NULL DEFAULT 'planning',
    notes             TEXT,
    canon_status      TEXT    NOT NULL DEFAULT 'draft',
    created_at        TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at        TEXT    NOT NULL DEFAULT (datetime('now'))
);
