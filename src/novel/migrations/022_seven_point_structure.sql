-- Migration 022: Story structure (7-point beats at story level and per-arc)
CREATE TABLE IF NOT EXISTS story_structure (
    id                                  INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id                             INTEGER NOT NULL REFERENCES books(id),
    hook_chapter_id                     INTEGER REFERENCES chapters(id),
    plot_turn_1_chapter_id              INTEGER REFERENCES chapters(id),
    pinch_1_chapter_id                  INTEGER REFERENCES chapters(id),
    midpoint_chapter_id                 INTEGER REFERENCES chapters(id),
    pinch_2_chapter_id                  INTEGER REFERENCES chapters(id),
    plot_turn_2_chapter_id              INTEGER REFERENCES chapters(id),
    resolution_chapter_id               INTEGER REFERENCES chapters(id),
    act_1_inciting_incident_chapter_id  INTEGER REFERENCES chapters(id),
    act_2_midpoint_chapter_id           INTEGER REFERENCES chapters(id),
    act_3_climax_chapter_id             INTEGER REFERENCES chapters(id),
    notes                               TEXT,
    created_at                          TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at                          TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(book_id)
);

CREATE TABLE IF NOT EXISTS arc_seven_point_beats (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    arc_id      INTEGER NOT NULL REFERENCES character_arcs(id),
    beat_type   TEXT    NOT NULL,
    chapter_id  INTEGER REFERENCES chapters(id),
    notes       TEXT,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE(arc_id, beat_type)
);
