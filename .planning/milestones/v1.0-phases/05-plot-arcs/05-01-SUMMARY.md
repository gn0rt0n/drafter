---
phase: 05-plot-arcs
plan: "01"
subsystem: api
tags: [mcp, fastmcp, sqlite, aiosqlite, plot-threads]

# Dependency graph
requires:
  - phase: 04-chapters-scenes-world
    provides: register(mcp) tool module pattern, get_connection async context manager
  - phase: 02-pydantic-models-seed-data
    provides: PlotThread model in novel.models.plot
provides:
  - novel.tools.plot with register(mcp) containing 3 plot thread tools
  - get_plot_thread: retrieve plot thread by ID
  - list_plot_threads: list all threads with optional thread_type and status filters
  - upsert_plot_thread: two-branch create/update (INSERT or ON CONFLICT(id) DO UPDATE)
affects: [05-02-arcs, 05-03-tests, 06-gate-system]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Two-branch upsert: None id uses INSERT + cursor.lastrowid; provided id uses ON CONFLICT(id) DO UPDATE
    - Dynamic WHERE clause construction with clauses/params list pattern for optional filters
    - No conn.commit() in read-only tools (get_*, list_*)
    - try/except in upsert tools returning ValidationFailure on DB error

key-files:
  created:
    - src/novel/tools/plot.py
  modified: []

key-decisions:
  - "upsert_plot_thread uses ON CONFLICT(id) DO UPDATE (not INSERT OR REPLACE) for provided-id branch — plot_threads has FK children in chapter_plot_threads and subplot_touchpoint_log"
  - "upsert_plot_thread does NOT touch chapter_plot_threads junction table — junction management is via chapter tools"
  - "list_plot_threads uses dynamic WHERE clause via clauses/params lists — same pattern as established in world tools"

patterns-established:
  - "list_plot_threads dynamic WHERE: build clauses[] and params[] lists, join with AND, prefix WHERE only if non-empty"

requirements-completed: [PLOT-01, PLOT-02, PLOT-07]

# Metrics
duration: 2min
completed: 2026-03-07
---

# Phase 5 Plan 01: Plot Thread Tools Summary

**Plot thread MCP tool module with get/list/upsert tools using dynamic WHERE filtering and FK-safe ON CONFLICT(id) DO UPDATE upsert pattern**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-07T22:12:30Z
- **Completed:** 2026-03-07T22:13:48Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments

- Created `src/novel/tools/plot.py` with `register(mcp)` containing 3 tools
- `get_plot_thread`: returns PlotThread on hit, NotFoundResponse on miss
- `list_plot_threads`: dynamic WHERE clause for optional thread_type and/or status filters, returns list[PlotThread]
- `upsert_plot_thread`: two-branch — None id uses INSERT + cursor.lastrowid, provided id uses ON CONFLICT(id) DO UPDATE; defaults thread_type/"main", status/"active", canon_status/"draft" when None

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement plot thread tool module (3 tools)** - `2378b07` (feat)

**Plan metadata:** (docs commit — see final_commit below)

## Files Created/Modified

- `src/novel/tools/plot.py` - Plot domain MCP tools: register(mcp), get_plot_thread, list_plot_threads, upsert_plot_thread

## Decisions Made

- Used ON CONFLICT(id) DO UPDATE (not INSERT OR REPLACE) for the provided-id branch — plot_threads has FK children in chapter_plot_threads and subplot_touchpoint_log; replacing the row would cascade-delete child rows.
- upsert_plot_thread does NOT write to chapter_plot_threads — junction management is via chapter tools.
- Dynamic WHERE clause uses clauses/params list pattern (same as established in world.py) — avoids string interpolation of user input.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - straightforward implementation following established world.py pattern.

## Next Phase Readiness

- Plot thread tools complete and importable at `novel.tools.plot`
- Ready for Plan 05-02 (character arc tools) and Plan 05-03 (wire server + tests)
- No blockers

---
*Phase: 05-plot-arcs*
*Completed: 2026-03-07*
