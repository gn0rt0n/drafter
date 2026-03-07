-- Migration 014: Voice profiles and drift log
CREATE TABLE IF NOT EXISTS voice_profiles (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    character_id          INTEGER NOT NULL UNIQUE REFERENCES characters(id),
    sentence_length       TEXT,
    vocabulary_level      TEXT,
    speech_patterns       TEXT,
    verbal_tics           TEXT,
    avoids                TEXT,
    internal_voice_notes  TEXT,
    dialogue_sample       TEXT,
    notes                 TEXT,
    canon_status          TEXT    NOT NULL DEFAULT 'draft',
    created_at            TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at            TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS voice_drift_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    character_id    INTEGER NOT NULL REFERENCES characters(id),
    chapter_id      INTEGER REFERENCES chapters(id),
    scene_id        INTEGER REFERENCES scenes(id),
    drift_type      TEXT    NOT NULL DEFAULT 'vocabulary',
    description     TEXT    NOT NULL,
    severity        TEXT    NOT NULL DEFAULT 'minor',
    is_resolved     INTEGER NOT NULL DEFAULT 0,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);
