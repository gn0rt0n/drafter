---
phase: 05-plot-arcs
plan: 02
subsystem: api
tags: [mcp, fastmcp, sqlite, aiosqlite, pydantic, character-arcs, chekovs-gun, subplot-touchpoints]

# Dependency graph
requires:
  - phase: 05-plot-arcs-01
    provides: plot_threads and plot_thread_events tools; plot models already exist from Phase 2
  - phase: 04-chapters-scenes-world
    provides: get_connection pattern, FastMCP register() pattern, chapters/scenes tables
  - phase: 02-pydantic-models-seed-data
    provides: CharacterArc, ArcHealthLog, ChekhovGun models in novel.models.arcs
provides:
  - novel.tools.arcs.register(mcp) with 6 tools covering arc health monitoring and Chekhov's gun registry
  - get_chekovs_guns: retrieve Chekhov's gun entries with status/unresolved_only filters
  - get_arc: dual-mode arc lookup by arc_id (single) or character_id (list) with ValidationFailure guard
  - get_arc_health: JOIN-based health log retrieval ordered by chapter_id
  - get_subplot_touchpoint_gaps: LEFT JOIN query detecting overdue subplot touchpoints
  - upsert_chekov: two-branch upsert for chekovs_gun_registry (no UNIQUE name constraint)
  - log_arc_health: append-only INSERT to arc_health_log
affects: [05-plot-arcs-03, 06-gate-system, 07-session-timeline, 10-cli-integration-testing]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Two-branch upsert: None-id INSERT+lastrowid vs provided-id ON CONFLICT(id) DO UPDATE (same as upsert_location)"
    - "Append-only INSERT with no ON CONFLICT clause (same as log_magic_use)"
    - "JOIN from log table to parent table to filter by grandparent FK (arc_health_log JOIN character_arcs WHERE character_id)"
    - "Two-step max-chapter query for gap detection: MAX(id) then LEFT JOIN aggregate"
    - "unresolved_only flag takes precedence over status parameter (explicit priority ordering)"

key-files:
  created:
    - src/novel/tools/arcs.py
  modified: []

key-decisions:
  - "upsert_chekov uses two-branch (None-id INSERT+lastrowid, provided-id ON CONFLICT(id)) because chekovs_gun_registry has no UNIQUE constraint beyond PK — no ON CONFLICT(name) possible"
  - "get_arc returns ValidationFailure (not NotFoundResponse) when neither arc_id nor character_id provided — this is a caller error, not a missing resource"
  - "get_arc_health returns empty list (not NotFoundResponse) when no health logs exist — health logging is optional for any arc"
  - "get_subplot_touchpoint_gaps returns list[dict] not list[Pydantic] — structured enough for Claude to act on, no dedicated model needed"

patterns-established:
  - "Validation guard before connection context: check required params, return ValidationFailure early before async with get_connection()"
  - "arc_id precedence in dual-mode tools: arc_id overrides character_id when both provided"

requirements-completed: [PLOT-03, PLOT-04, PLOT-05, PLOT-06, PLOT-08, PLOT-09]

# Metrics
duration: 2min
completed: 2026-03-07
---

# Phase 5 Plan 02: Arcs Tools Summary

**Six narrative health monitoring tools covering Chekhov's gun registry, character arc lookup, arc health logging, and subplot touchpoint gap detection using JOIN-based queries and two-branch upsert patterns.**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-07T22:12:33Z
- **Completed:** 2026-03-07T22:14:20Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments

- Implemented `src/novel/tools/arcs.py` with `register(mcp)` containing all 6 arc domain tools
- get_chekovs_guns supports unresolved_only precedence over status filter, returns list[ChekhovGun]
- get_arc is dual-mode: ValidationFailure when neither param given, single CharacterArc on arc_id path, list on character_id path
- get_arc_health JOINs arc_health_log to character_arcs to resolve character_id (no direct FK in log table)
- get_subplot_touchpoint_gaps uses two-step max-chapter + LEFT JOIN aggregate to detect never-touched and overdue subplots
- upsert_chekov two-branch handles the missing UNIQUE name constraint correctly
- log_arc_health is append-only with no ON CONFLICT clause — arc_health_log is a pure audit trail

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement arcs tool module (6 tools)** - `3aed50c` (feat)

**Plan metadata:** _(docs commit follows)_

## Files Created/Modified

- `src/novel/tools/arcs.py` - Arc domain MCP tools module with register(mcp) containing 6 tools: get_chekovs_guns, get_arc, get_arc_health, get_subplot_touchpoint_gaps, upsert_chekov, log_arc_health

## Decisions Made

- upsert_chekov uses two-branch rather than ON CONFLICT(name) because chekovs_gun_registry has no UNIQUE name constraint — only ON CONFLICT(id) is valid for update path
- get_arc returns ValidationFailure (not NotFoundResponse) for missing params — consistent with character tools validation pattern
- get_arc_health returns empty list for no logs — health logging is optional, empty is valid state
- get_subplot_touchpoint_gaps returns list[dict] — no Pydantic model needed for this projection query

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- All 6 arc tools are registered and importable
- Ready to wire into server.py (Phase 5 Plan 03 or equivalent wiring step)
- gate system (Phase 6) can reference arc health and Chekhov's gun status for check_gate() implementation
- Integration tests (Phase 10) can use seed data: arc id=1 (character_id=1), arc_health_log id=1, chekov id=1

---
*Phase: 05-plot-arcs*
*Completed: 2026-03-07*
