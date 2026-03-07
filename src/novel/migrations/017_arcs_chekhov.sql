-- Migration 017: Character arcs, arc health log, Chekhov's guns, subplot touchpoints
CREATE TABLE IF NOT EXISTS character_arcs (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    character_id        INTEGER NOT NULL REFERENCES characters(id),
    arc_type            TEXT    NOT NULL DEFAULT 'growth',
    starting_state      TEXT,
    desired_state       TEXT,
    wound               TEXT,
    lie_believed        TEXT,
    truth_to_learn      TEXT,
    opened_chapter_id   INTEGER REFERENCES chapters(id),
    closed_chapter_id   INTEGER REFERENCES chapters(id),
    notes               TEXT,
    canon_status        TEXT    NOT NULL DEFAULT 'draft',
    created_at          TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at          TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS chapter_character_arcs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    chapter_id      INTEGER NOT NULL REFERENCES chapters(id),
    arc_id          INTEGER NOT NULL REFERENCES character_arcs(id),
    arc_progression TEXT    NOT NULL DEFAULT 'stasis',
    notes           TEXT,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE(chapter_id, arc_id)
);

CREATE TABLE IF NOT EXISTS arc_health_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    arc_id          INTEGER NOT NULL REFERENCES character_arcs(id),
    chapter_id      INTEGER NOT NULL REFERENCES chapters(id),
    health_status   TEXT    NOT NULL DEFAULT 'on-track',
    notes           TEXT,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS chekovs_gun_registry (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    name                TEXT    NOT NULL,
    description         TEXT    NOT NULL,
    planted_chapter_id  INTEGER REFERENCES chapters(id),
    planted_scene_id    INTEGER REFERENCES scenes(id),
    payoff_chapter_id   INTEGER REFERENCES chapters(id),
    payoff_scene_id     INTEGER REFERENCES scenes(id),
    status              TEXT    NOT NULL DEFAULT 'planted',
    notes               TEXT,
    canon_status        TEXT    NOT NULL DEFAULT 'draft',
    created_at          TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at          TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS subplot_touchpoint_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    plot_thread_id  INTEGER NOT NULL REFERENCES plot_threads(id),
    chapter_id      INTEGER NOT NULL REFERENCES chapters(id),
    touchpoint_type TEXT    NOT NULL DEFAULT 'advance',
    notes           TEXT,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);
