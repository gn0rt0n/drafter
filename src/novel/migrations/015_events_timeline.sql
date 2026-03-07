-- Migration 015: Timeline events, participants, travel segments, POV positions
CREATE TABLE IF NOT EXISTS events (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT    NOT NULL,
    event_type      TEXT    NOT NULL DEFAULT 'plot',
    chapter_id      INTEGER REFERENCES chapters(id),
    location_id     INTEGER REFERENCES locations(id),
    in_story_date   TEXT,
    duration        TEXT,
    summary         TEXT,
    significance    TEXT,
    notes           TEXT,
    canon_status    TEXT    NOT NULL DEFAULT 'draft',
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS event_participants (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id        INTEGER NOT NULL REFERENCES events(id),
    character_id    INTEGER NOT NULL REFERENCES characters(id),
    role            TEXT    NOT NULL DEFAULT 'participant',
    notes           TEXT,
    UNIQUE(event_id, character_id)
);

CREATE TABLE IF NOT EXISTS event_artifacts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id        INTEGER NOT NULL REFERENCES events(id),
    artifact_id     INTEGER NOT NULL REFERENCES artifacts(id),
    involvement     TEXT,
    UNIQUE(event_id, artifact_id)
);

CREATE TABLE IF NOT EXISTS travel_segments (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    character_id        INTEGER NOT NULL REFERENCES characters(id),
    from_location_id    INTEGER REFERENCES locations(id),
    to_location_id      INTEGER REFERENCES locations(id),
    start_chapter_id    INTEGER REFERENCES chapters(id),
    end_chapter_id      INTEGER REFERENCES chapters(id),
    start_event_id      INTEGER REFERENCES events(id),
    elapsed_days        INTEGER,
    travel_method       TEXT,
    notes               TEXT,
    created_at          TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS pov_chronological_position (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    character_id    INTEGER NOT NULL REFERENCES characters(id),
    chapter_id      INTEGER NOT NULL REFERENCES chapters(id),
    in_story_date   TEXT,
    day_number      INTEGER,
    location_id     INTEGER REFERENCES locations(id),
    notes           TEXT,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE(character_id, chapter_id)
);

CREATE INDEX IF NOT EXISTS idx_events_chapter ON events(chapter_id);
CREATE INDEX IF NOT EXISTS idx_travel_character ON travel_segments(character_id);
