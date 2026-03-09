---
phase: 05-plot-arcs
plan: 03
subsystem: testing
tags: [mcp, fastmcp, pytest, pytest-asyncio, sqlite, plot, arcs]

# Dependency graph
requires:
  - phase: 05-01
    provides: plot.py tool module (3 tools: get_plot_thread, list_plot_threads, upsert_plot_thread)
  - phase: 05-02
    provides: arcs.py tool module (6 tools: get_chekovs_guns, get_arc, get_arc_health, get_subplot_touchpoint_gaps, upsert_chekov, log_arc_health)
provides:
  - server.py wired with all 8 tool domains (characters, relationships, chapters, scenes, world, magic, plot, arcs)
  - tests/test_plot.py — 6 in-memory MCP client tests for all 3 plot tools
  - tests/test_arcs.py — 12 in-memory MCP client tests for all 6 arc tools
affects: [06-gate-system, 10-cli-integration-testing]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Session-scoped tmp_path_factory fixture with unique mktemp dir names (plot_db, arcs_db) to prevent cross-file fixture collisions"
    - "_call_tool helper opens+closes MCP session per test coroutine — anyio cancel scope must not span fixture lifecycle"
    - "FastMCP list[T] response serialized as N TextContent blocks — multi-item: [json.loads(c.text) for c in result.content]"
    - "get_arc dual-mode: single ContentBlock for arc_id path, multiple ContentBlocks for character_id path"
    - "Raw sqlite3 insert inside test body for test_get_subplot_touchpoint_gaps — seeds data not in minimal profile"

key-files:
  created:
    - tests/test_plot.py
    - tests/test_arcs.py
  modified:
    - src/novel/mcp/server.py

key-decisions:
  - "test_get_subplot_touchpoint_gaps inserts subplot thread via raw sqlite3 inside test body — minimal seed has only main threads, gap query filters to subplot type"
  - "test_upsert_chekov_update uses chekov_id=1 (The Scratch Marks from seed) — confirms ON CONFLICT(id) DO UPDATE path"
  - "test_log_arc_health uses arc_id=1, chapter_id=2 (not chapter_id=1 which already has a log in seed) — confirms append-only behavior"

patterns-established:
  - "All plot/arc test files follow canonical Phase 3-4 test pattern: session-scoped DB fixture, _call_tool helper, per-test MCP session entry"

requirements-completed: [PLOT-01, PLOT-02, PLOT-03, PLOT-04, PLOT-05, PLOT-06, PLOT-07, PLOT-08, PLOT-09]

# Metrics
duration: 5min
completed: 2026-03-07
---

# Phase 5 Plan 03: Wire Server and Plot/Arc MCP Tests Summary

**Full MCP protocol path verified for 9 new plot/arc tools — server.py wired with 8 domains, 18 in-memory client tests all passing**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-07T22:17:00Z
- **Completed:** 2026-03-07T22:18:16Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- server.py extended to import and register plot and arcs tool modules — all 8 domains now wired
- tests/test_plot.py: 6 tests covering get_plot_thread (found/not-found), list_plot_threads (unfiltered, filtered by type+status), upsert_plot_thread (create, update)
- tests/test_arcs.py: 12 tests covering get_chekovs_guns (all, status filter, unresolved_only), get_arc (by arc_id, by character_id, not-found, neither=validation failure), get_arc_health, get_subplot_touchpoint_gaps (with inserted subplot), upsert_chekov (create, update), log_arc_health
- All 18 tests pass; no print() in tool modules confirmed

## Task Commits

Each task was committed atomically:

1. **Task 1: Wire server.py with plot and arcs register() calls** - `c5776c1` (feat)
2. **Task 2: Write MCP in-memory tests for plot and arc tools** - `d1f1a60` (feat)

**Plan metadata:** (pending)

## Files Created/Modified
- `src/novel/mcp/server.py` - Extended import + 2 register() calls for plot/arcs; docstring updated to Phase 5
- `tests/test_plot.py` - 6 in-memory MCP client tests for 3 plot tools
- `tests/test_arcs.py` - 12 in-memory MCP client tests for 6 arc tools

## Decisions Made
- test_get_subplot_touchpoint_gaps inserts a subplot thread via raw sqlite3 inside the test body because the minimal seed only contains thread_type="main" threads; the gap query filters to thread_type="subplot" — no seed change required
- log_arc_health test uses chapter_id=2 (seed has chapter_id=1 already) to confirm append-only INSERT behavior without unique-constraint conflicts

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered
- None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 5 (Plot & Arcs) is complete: 9 tools implemented and fully tested via in-memory MCP client tests
- Phase 6 (Gate System) can begin: all core tool modules exist (characters, relationships, chapters, scenes, world, magic, plot, arcs) for the check_gate() helper to gate-block
- No blockers

## Self-Check: PASSED

- FOUND: tests/test_plot.py
- FOUND: tests/test_arcs.py
- FOUND: src/novel/mcp/server.py
- FOUND: .planning/phases/05-plot-arcs/05-03-SUMMARY.md
- FOUND: commit c5776c1 (wire server.py)
- FOUND: commit d1f1a60 (write MCP tests)

---
*Phase: 05-plot-arcs*
*Completed: 2026-03-07*
