-- Migration 018: Scene character goals, pacing beats, tension measurements
CREATE TABLE IF NOT EXISTS scene_character_goals (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    scene_id        INTEGER NOT NULL REFERENCES scenes(id),
    character_id    INTEGER NOT NULL REFERENCES characters(id),
    goal            TEXT    NOT NULL,
    obstacle        TEXT,
    outcome         TEXT,
    notes           TEXT,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE(scene_id, character_id)
);

CREATE TABLE IF NOT EXISTS pacing_beats (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    chapter_id      INTEGER NOT NULL REFERENCES chapters(id),
    scene_id        INTEGER REFERENCES scenes(id),
    beat_type       TEXT    NOT NULL DEFAULT 'action',
    description     TEXT    NOT NULL,
    sequence_order  INTEGER NOT NULL DEFAULT 0,
    notes           TEXT,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS tension_measurements (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    chapter_id      INTEGER NOT NULL REFERENCES chapters(id),
    tension_level   INTEGER NOT NULL DEFAULT 5,
    measurement_type TEXT   NOT NULL DEFAULT 'overall',
    notes           TEXT,
    measured_at     TEXT    NOT NULL DEFAULT (datetime('now'))
);
