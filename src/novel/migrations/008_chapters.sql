-- Migration 008: Chapters (FK to books, acts, characters; pov_character_id nullable)
CREATE TABLE IF NOT EXISTS chapters (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id               INTEGER NOT NULL REFERENCES books(id),
    act_id                INTEGER REFERENCES acts(id),
    chapter_number        INTEGER NOT NULL,
    title                 TEXT,
    pov_character_id      INTEGER REFERENCES characters(id),
    word_count_target     INTEGER,
    actual_word_count     INTEGER NOT NULL DEFAULT 0,
    status                TEXT    NOT NULL DEFAULT 'planned',
    summary               TEXT,
    opening_state         TEXT,
    closing_state         TEXT,
    opening_hook_note     TEXT,
    closing_hook_note     TEXT,
    hook_strength_rating  INTEGER,
    time_marker           TEXT,
    elapsed_days_from_start INTEGER,
    structural_function   TEXT,
    notes                 TEXT,
    canon_status          TEXT    NOT NULL DEFAULT 'draft',
    source_file           TEXT,
    created_at            TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at            TEXT    NOT NULL DEFAULT (datetime('now')),
    reviewed_at           TEXT,
    UNIQUE(book_id, chapter_number)
);

CREATE INDEX IF NOT EXISTS idx_chapters_book ON chapters(book_id);
CREATE INDEX IF NOT EXISTS idx_chapters_pov ON chapters(pov_character_id);
