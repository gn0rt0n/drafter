-- Migration 019: Session logs and agent run log
CREATE TABLE IF NOT EXISTS session_logs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    closed_at       TEXT,
    summary         TEXT,
    carried_forward TEXT,   -- JSON array of carried-forward items
    word_count_delta INTEGER NOT NULL DEFAULT 0,
    chapters_touched TEXT,  -- JSON array of chapter IDs
    notes           TEXT
);

CREATE TABLE IF NOT EXISTS agent_run_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id      INTEGER REFERENCES session_logs(id),
    agent_name      TEXT    NOT NULL,
    tool_name       TEXT,
    input_summary   TEXT,
    output_summary  TEXT,
    duration_ms     INTEGER,
    success         INTEGER NOT NULL DEFAULT 1,
    error_message   TEXT,
    ran_at          TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_agent_run_session ON agent_run_log(session_id);
