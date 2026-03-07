---
phase: 01-project-foundation-database
plan: "03"
subsystem: database
tags: [sqlite, typer, cli, migrations, database-lifecycle]

# Dependency graph
requires:
  - phase: 01-01
    provides: get_connection context manager, pyproject entry points, db/cli.py stub
  - phase: 01-02
    provides: 21 SQL migration files, apply_migrations/drop_all_tables functions, seed stub

provides:
  - Full implementation of `novel db migrate` command (CLDB-01)
  - Full implementation of `novel db seed` command (CLDB-02)
  - Full implementation of `novel db reset` command (CLDB-03)
  - Full implementation of `novel db status` command (CLDB-04)
  - Phase 1 end-to-end database lifecycle complete

affects: [phase-02-models-seed, phase-03-mcp-characters, all-phases]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "time.monotonic() for CLI duration reporting"
    - "typer.confirm() for destructive operation confirmation"
    - "Helper functions prefixed with _ for private SQL query logic"
    - "sqlite3.OperationalError caught locally when table may not exist yet"

key-files:
  created: []
  modified:
    - src/novel/db/cli.py

key-decisions:
  - "seed raises Exit(code=0) on Phase 1 ValueError — not an error, expected stub behavior"
  - "status helper functions (_get_migration_version etc) are module-private with _ prefix"
  - "reset uses a single get_connection() context covering both drop_all_tables and apply_migrations"

patterns-established:
  - "DB CLI commands: wrap in try/except, print to stderr on error, exit code 1 on failure"
  - "Confirmation pattern: --yes/-y flag skips typer.confirm() for scripted/automated use"
  - "Status display: fixed-width label padding for aligned terminal output"

requirements-completed: [SETUP-03, CLDB-01, CLDB-02, CLDB-03, CLDB-04]

# Metrics
duration: 4min
completed: 2026-03-07
---

# Phase 1 Plan 03: DB CLI Commands Summary

**Four-command `novel db` CLI (migrate/seed/reset/status) wiring 21 SQL migrations into a fully managed SQLite lifecycle with sub-100ms fresh-database creation**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-07T19:35:14Z
- **Completed:** 2026-03-07T19:39:00Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments

- `novel db migrate` applies all 21 migrations, reports each file name and elapsed time, completes in ~20ms on fresh database
- `novel db migrate` is idempotent — second run prints "Database is already up to date."
- `novel db status` displays migration version 21, 69 tables, and zero row counts for books/chapters/characters/scenes
- `novel db reset --yes` drops all tables then re-applies all 21 migrations cleanly in a single connection
- `novel db seed minimal` prints the Phase 1 stub message ("No seed profiles defined yet") and exits 0
- All four Phase 1 success criteria verified: entry points, migrate speed, reset+status, FK enforcement

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement novel db CLI commands (migrate, seed, reset, status)** - `a0f9e69` (feat)

**Plan metadata:** (docs commit to follow)

## Files Created/Modified

- `src/novel/db/cli.py` - Full implementation of migrate, seed, reset, status replacing stubs

## Decisions Made

- `seed` command catches `ValueError` from the Phase 1 stub and exits with code 0 — it is an expected, non-error condition until Phase 2
- `reset` reuses a single `get_connection()` context for both `drop_all_tables` and `apply_migrations` to keep the reset atomic
- Private helper functions `_get_migration_version`, `_get_table_count`, `_get_key_row_counts` keep the `status` command readable

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 1 is fully complete: all 21 migrations, all CLI commands, FK enforcement, WAL mode
- Phase 2 (Pydantic Models and Seed Data) can proceed: database schema is stable and CLI-managed
- `novel db seed minimal` and `novel db seed gate-ready` will be implemented in Phase 2

---
*Phase: 01-project-foundation-database*
*Completed: 2026-03-07*
