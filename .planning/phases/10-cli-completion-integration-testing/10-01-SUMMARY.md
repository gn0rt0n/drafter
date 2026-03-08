---
phase: 10-cli-completion-integration-testing
plan: "01"
subsystem: cli
tags: [typer, sqlite3, session, query, pov-balance, arc-health, thread-gaps]

# Dependency graph
requires:
  - phase: 07-session-timeline
    provides: session_logs, open_questions tables and session SQL patterns
  - phase: 05-plot-arcs
    provides: character_arcs, arc_health_log, subplot_touchpoint_log tables
  - phase: 04-chapters-scenes-world
    provides: chapters, characters tables for pov_character_id JOINs
  - phase: 06-gate-system
    provides: gate/cli.py as canonical CLI module pattern
provides:
  - novel session start — display briefing from last session log
  - novel session close — prompt for summary and close open session with carried_forward
  - novel query pov-balance — POV balance table by character (chapter count + word count)
  - novel query arc-health — arc progression with latest health per character arc
  - novel query thread-gaps — subplots overdue for touchpoint via HAVING clause SQL
affects:
  - phase 10 integration testing (uses these CLI commands for smoke tests)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "CLI module pattern from gate/cli.py: app = typer.Typer(), try/except typer.Exit pattern"
    - "Read-only sync sqlite3 queries in CLI — never async novel.mcp.db"
    - "Tabular output with fixed-width f-string columns via typer.echo()"
    - "Mirror MCP SQL in CLI without reusing MCP imports — SQL duplication intentional"

key-files:
  created:
    - src/novel/session/__init__.py
    - src/novel/session/cli.py
    - src/novel/query/__init__.py
    - src/novel/query/cli.py
  modified:
    - src/novel/cli.py

key-decisions:
  - "open_questions uses column 'question' not 'question_text' — migration 021 is ground truth"
  - "arc_health table name is arc_health_log not arc_health_logs — confirmed from migration 017"
  - "thread-gaps SQL duplicates MCP tool logic using sync sqlite3 — intentional isolation between CLI and MCP layers"
  - "close command finds open session by SELECT not by session_id argument — mirrors CLSG-02 spec"

patterns-established:
  - "CLI subcommand packages follow src/novel/{domain}/__init__.py + cli.py structure"
  - "No cross-layer imports: CLI uses novel.db.connection.get_connection(), never novel.mcp.db"

requirements-completed: [CLSG-01, CLSG-02, CLSG-06, CLSG-07, CLSG-08]

# Metrics
duration: 3min
completed: 2026-03-08
---

# Phase 10 Plan 01: CLI Session and Query Commands Summary

**Five human-facing CLI commands across two new subcommand groups: `novel session start/close` and `novel query pov-balance/arc-health/thread-gaps`, using sync sqlite3 against the narrative database.**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-08T22:56:24Z
- **Completed:** 2026-03-08T22:58:40Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- Created `novel session` group with `start` (briefing display) and `close` (prompted summary write) commands
- Created `novel query` group with `pov-balance`, `arc-health`, and `thread-gaps` read-only commands
- Registered both new subcommand groups in the root `novel` CLI
- All five commands exit 0 on success, print errors to stderr with exit 1 on failure
- End-to-end smoke test passed: all commands work against minimal seed database

## Task Commits

Each task was committed atomically:

1. **Task 1: Create session CLI module (novel session start / close)** - `4afc190` (feat)
2. **Task 2: Create query CLI module and register in root CLI** - `ebc9c5e` (feat)

**Plan metadata:** (docs commit below)

## Files Created/Modified
- `src/novel/session/__init__.py` - Package marker for session CLI
- `src/novel/session/cli.py` - Typer app with start and close commands using sync sqlite3
- `src/novel/query/__init__.py` - Package marker for query CLI
- `src/novel/query/cli.py` - Typer app with pov-balance, arc-health, thread-gaps commands
- `src/novel/cli.py` - Root CLI updated to register session and query subcommand groups

## Decisions Made
- `open_questions` column is `question` (not `question_text` as plan prose stated) — migration 021 is ground truth, corrected automatically
- `arc_health_log` (not `arc_health_logs`) confirmed from migration 017
- CLI layers SQL is intentionally duplicated from MCP tools — isolation between sync CLI and async MCP layers is by design
- `novel session close` finds the open session by querying DB (not by user-supplied ID) — simpler UX, matches CLSG-02 spec

## Deviations from Plan

**1. [Rule 2 - Missing Critical] Plan spec said `question_text` but actual column is `question`**
- **Found during:** Task 1 (session CLI implementation)
- **Issue:** Plan context block said `SELECT question_text FROM open_questions` but migration 021 defines column as `question`
- **Fix:** Used `question` throughout (session/cli.py and query context noted for future)
- **Files modified:** src/novel/session/cli.py
- **Verification:** `novel session start` displays open questions correctly against seeded DB
- **Committed in:** 4afc190 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (Rule 2 - schema column name correction)
**Impact on plan:** Necessary for correctness — wrong column name would cause runtime error. No scope creep.

## Issues Encountered
- Discovered pre-existing `novel` CLI already had `export` and `name` imports from prior Phase 9 execution — not a conflict, both modules were already complete. Task 2 simply added session and query on top.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All five CLI commands implemented and verified
- `novel session close` tested with `--summary` flag (non-interactive) and prompt path (interactive)
- Ready for Phase 10 integration testing plans

## Self-Check: PASSED
- src/novel/session/__init__.py: FOUND
- src/novel/session/cli.py: FOUND
- src/novel/query/__init__.py: FOUND
- src/novel/query/cli.py: FOUND
- 10-01-SUMMARY.md: FOUND
- Commit 4afc190: FOUND
- Commit ebc9c5e: FOUND
