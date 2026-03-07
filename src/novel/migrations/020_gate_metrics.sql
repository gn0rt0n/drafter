-- Migration 020: Architecture gate, gate checklist, project metrics, POV balance snapshots
CREATE TABLE IF NOT EXISTS architecture_gate (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    is_certified    INTEGER NOT NULL DEFAULT 0,
    certified_at    TEXT,
    certified_by    TEXT,
    checklist_version INTEGER NOT NULL DEFAULT 1,
    notes           TEXT,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS gate_checklist_items (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    gate_id         INTEGER NOT NULL REFERENCES architecture_gate(id),
    item_key        TEXT    NOT NULL,
    category        TEXT    NOT NULL DEFAULT 'general',
    description     TEXT    NOT NULL,
    is_passing      INTEGER NOT NULL DEFAULT 0,
    missing_count   INTEGER NOT NULL DEFAULT 0,
    last_checked_at TEXT,
    notes           TEXT,
    UNIQUE(gate_id, item_key)
);

CREATE TABLE IF NOT EXISTS project_metrics_snapshots (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_at         TEXT    NOT NULL DEFAULT (datetime('now')),
    word_count          INTEGER NOT NULL DEFAULT 0,
    chapter_count       INTEGER NOT NULL DEFAULT 0,
    scene_count         INTEGER NOT NULL DEFAULT 0,
    character_count     INTEGER NOT NULL DEFAULT 0,
    session_count       INTEGER NOT NULL DEFAULT 0,
    notes               TEXT
);

CREATE TABLE IF NOT EXISTS pov_balance_snapshots (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_at     TEXT    NOT NULL DEFAULT (datetime('now')),
    chapter_id      INTEGER REFERENCES chapters(id),
    character_id    INTEGER REFERENCES characters(id),
    chapter_count   INTEGER NOT NULL DEFAULT 0,
    word_count      INTEGER NOT NULL DEFAULT 0
);
