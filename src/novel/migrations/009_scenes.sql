-- Migration 009: Scenes (FK to chapters, locations)
CREATE TABLE IF NOT EXISTS scenes (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    chapter_id          INTEGER NOT NULL REFERENCES chapters(id),
    scene_number        INTEGER NOT NULL,
    location_id         INTEGER REFERENCES locations(id),
    time_marker         TEXT,
    summary             TEXT,
    scene_type          TEXT    NOT NULL DEFAULT 'action',
    dramatic_question   TEXT,
    scene_goal          TEXT,
    obstacle            TEXT,
    turn                TEXT,
    consequence         TEXT,
    emotional_function  TEXT,
    narrative_functions TEXT,   -- JSON array
    word_count_target   INTEGER,
    status              TEXT    NOT NULL DEFAULT 'planned',
    notes               TEXT,
    canon_status        TEXT    NOT NULL DEFAULT 'draft',
    created_at          TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at          TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE(chapter_id, scene_number)
);

CREATE INDEX IF NOT EXISTS idx_scenes_chapter ON scenes(chapter_id);
