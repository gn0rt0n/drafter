-- Migration 016: Plot threads, chapter-plot mapping, structural obligations
CREATE TABLE IF NOT EXISTS plot_threads (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    name                TEXT    NOT NULL,
    thread_type         TEXT    NOT NULL DEFAULT 'main',
    status              TEXT    NOT NULL DEFAULT 'active',
    opened_chapter_id   INTEGER REFERENCES chapters(id),
    closed_chapter_id   INTEGER REFERENCES chapters(id),
    parent_thread_id    INTEGER REFERENCES plot_threads(id),  -- subplot self-ref
    summary             TEXT,
    resolution          TEXT,
    stakes              TEXT,
    notes               TEXT,
    canon_status        TEXT    NOT NULL DEFAULT 'draft',
    created_at          TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at          TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS chapter_plot_threads (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    chapter_id      INTEGER NOT NULL REFERENCES chapters(id),
    plot_thread_id  INTEGER NOT NULL REFERENCES plot_threads(id),
    thread_role     TEXT    NOT NULL DEFAULT 'advance',
    notes           TEXT,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE(chapter_id, plot_thread_id)
);

CREATE TABLE IF NOT EXISTS chapter_structural_obligations (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    chapter_id      INTEGER NOT NULL REFERENCES chapters(id),
    obligation_type TEXT    NOT NULL DEFAULT 'setup',
    description     TEXT    NOT NULL,
    is_met          INTEGER NOT NULL DEFAULT 0,
    notes           TEXT,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);
