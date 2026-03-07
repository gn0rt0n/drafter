-- Migration 003: Acts (FK to books; start/end chapter FKs are nullable to avoid
-- the circular dependency with chapters — acts created before chapters exist)
CREATE TABLE IF NOT EXISTS acts (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id            INTEGER NOT NULL REFERENCES books(id),
    act_number         INTEGER NOT NULL,
    name               TEXT,
    purpose            TEXT,
    word_count_target  INTEGER,
    start_chapter_id   INTEGER REFERENCES chapters(id),  -- nullable: populated after chapters
    end_chapter_id     INTEGER REFERENCES chapters(id),  -- nullable: populated after chapters
    structural_notes   TEXT,
    canon_status       TEXT    NOT NULL DEFAULT 'draft',
    created_at         TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at         TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE(book_id, act_number)
);
