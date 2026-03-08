---
phase: 08-canon-knowledge-foreshadowing
plan: "01"
subsystem: database
tags: [mcp, fastmcp, aiosqlite, pydantic, canon, continuity, decisions]

# Dependency graph
requires:
  - phase: 06-gate-system
    provides: check_gate() helper called first in every tool
  - phase: 02-pydantic-models-seed-data
    provides: CanonFact and ContinuityIssue models in models/canon.py
provides:
  - StoryDecision Pydantic model in models/canon.py
  - 7 canon domain MCP tools registered via register(mcp) in tools/canon.py
  - get_canon_facts, log_canon_fact, log_decision, get_decisions, log_continuity_issue, get_continuity_issues, resolve_continuity_issue
affects:
  - 08-02 knowledge plan (same file structure pattern)
  - 08-03 foreshadowing plan (same file structure pattern)
  - server.py wiring (tools/canon.py needs to be registered)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Append-only INSERT for canon_facts, decisions_log, continuity_issues — no ON CONFLICT clauses"
    - "Dynamic WHERE clause construction via conditions list + params list"
    - "check_gate(conn) called first in every tool before any DB access"

key-files:
  created:
    - src/novel/tools/canon.py
  modified:
    - src/novel/models/canon.py

key-decisions:
  - "resolve_continuity_issue returns NotFoundResponse when row is missing after UPDATE — UPDATE does not error on missing id so SELECT-after is required"
  - "get_continuity_issues uses is_resolved = FALSE (SQL) not Python bool — matches SQLite storage of 0/1"
  - "get_decisions and get_continuity_issues use dynamic WHERE construction to handle all optional filter combinations"

patterns-established:
  - "Canon tools: append-only INSERT for all log/fact tables — no upsert semantics"
  - "Resolve pattern: UPDATE then SELECT back, return NotFoundResponse if row missing"

requirements-completed:
  - CANO-01
  - CANO-02
  - CANO-03
  - CANO-04
  - CANO-05
  - CANO-06
  - CANO-07

# Metrics
duration: 4min
completed: 2026-03-08
---

# Phase 8 Plan 01: Canon Domain Tools Summary

**StoryDecision model added to canon.py and 7 canon MCP tools implemented covering fact retrieval, decision logging, and continuity issue management with gate enforcement**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-08T02:08:36Z
- **Completed:** 2026-03-08T02:10:00Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Added `StoryDecision` Pydantic model to `src/novel/models/canon.py` mapping to `decisions_log` table
- Implemented all 7 canon domain MCP tools in `src/novel/tools/canon.py` via `register(mcp)` pattern
- Every tool calls `check_gate(conn)` first — no print() anywhere — 7/7 confirmed

## Task Commits

Each task was committed atomically:

1. **Task 1: Add StoryDecision model to src/novel/models/canon.py** - `562d8da` (feat)
2. **Task 2: Implement canon domain tools in src/novel/tools/canon.py** - `5c51f87` (feat)

## Files Created/Modified
- `src/novel/models/canon.py` - StoryDecision class appended after ReaderExperienceNote
- `src/novel/tools/canon.py` - Created with 7 tools: get_canon_facts, log_canon_fact, log_decision, get_decisions, log_continuity_issue, get_continuity_issues, resolve_continuity_issue

## Decisions Made
- `resolve_continuity_issue` does UPDATE then SELECT-back to detect missing IDs — SQLite UPDATE does not raise on missing row so the SELECT is required to return NotFoundResponse
- Dynamic WHERE clause built with conditions/params lists for `get_decisions` and `get_continuity_issues` — handles all optional filter combinations cleanly
- `get_continuity_issues` uses SQL `is_resolved = FALSE` (not Python bool) — consistent with SQLite 0/1 storage

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Canon tools (CANO-01 through CANO-07) complete and verified importable
- Ready for Phase 08-02: Knowledge domain tools
- tools/canon.py must be wired into server.py in a future integration plan

## Self-Check: PASSED

- FOUND: src/novel/models/canon.py
- FOUND: src/novel/tools/canon.py
- FOUND: 08-01-SUMMARY.md
- FOUND: commit 562d8da (Task 1: StoryDecision model)
- FOUND: commit 5c51f87 (Task 2: canon tools)

---
*Phase: 08-canon-knowledge-foreshadowing*
*Completed: 2026-03-08*
