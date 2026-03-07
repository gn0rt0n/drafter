-- Migration 001: Schema migrations tracking table
-- Must run first — used by the migration runner to track applied versions.
CREATE TABLE IF NOT EXISTS schema_migrations (
    version    INTEGER PRIMARY KEY,
    name       TEXT    NOT NULL,
    applied_at TEXT    NOT NULL
);
