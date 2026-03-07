-- Migration 011: Magic system elements and supernatural elements
CREATE TABLE IF NOT EXISTS magic_system_elements (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    name                TEXT    NOT NULL,
    element_type        TEXT    NOT NULL DEFAULT 'ability',
    rules               TEXT,
    limitations         TEXT,
    costs               TEXT,
    exceptions          TEXT,
    introduced_chapter_id INTEGER REFERENCES chapters(id),
    notes               TEXT,
    canon_status        TEXT    NOT NULL DEFAULT 'draft',
    created_at          TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at          TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS supernatural_elements (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    name                TEXT    NOT NULL,
    element_type        TEXT    NOT NULL DEFAULT 'creature',
    description         TEXT,
    rules               TEXT,
    voice_guidelines    TEXT,
    introduced_chapter_id INTEGER REFERENCES chapters(id),
    notes               TEXT,
    canon_status        TEXT    NOT NULL DEFAULT 'draft',
    created_at          TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at          TEXT    NOT NULL DEFAULT (datetime('now'))
);
