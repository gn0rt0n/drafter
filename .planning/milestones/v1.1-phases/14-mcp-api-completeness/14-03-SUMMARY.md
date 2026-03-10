---
phase: 14-mcp-api-completeness
plan: "03"
subsystem: api
tags: [mcp, sqlite, fk-safe-delete, plot, timeline]

# Dependency graph
requires:
  - phase: 14-mcp-api-completeness
    provides: FK-safe delete pattern established in plan 01 (characters) and plan 02 (chapters/scenes)
provides:
  - delete_plot_thread tool in src/novel/tools/plot.py
  - delete_event tool in src/novel/tools/timeline.py
  - delete_pov_position tool in src/novel/tools/timeline.py
  - delete_travel_segment tool in src/novel/tools/timeline.py
affects: [phase 15, integration testing]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "FK-safe delete: pre-existence check (NotFoundResponse) then try/except DELETE (ValidationFailure)"
    - "Log-delete: pre-existence check only for leaf tables with no FK children"
    - "Delete tools do not call check_gate regardless of module's other tool patterns"

key-files:
  created: []
  modified:
    - src/novel/tools/plot.py
    - src/novel/tools/timeline.py

key-decisions:
  - "delete tools in timeline.py do not call check_gate even though read/write tools in the same module do — matches phase 14 no-gate pattern for deletes"
  - "ValidationFailure added to timeline.py shared import (was missing) to support delete_event and delete_pov_position"
  - "delete_travel_segment uses simpler log-delete (no try/except) since travel_segments has no FK children"
  - "delete_pov_position accepts integer primary key (id), not the (character_id, chapter_id) composite, matching delete-by-id convention"

patterns-established:
  - "FK-safe delete: SELECT id first → NotFoundResponse if missing; try DELETE/commit → except Exception → ValidationFailure(errors=[str(exc)])"
  - "Log-delete (leaf table): SELECT id first → NotFoundResponse if missing; DELETE/commit → return dict (no try/except needed)"

requirements-completed:
  - MCP-01
  - MCP-02

# Metrics
duration: 8min
completed: 2026-03-09
---

# Phase 14 Plan 03: Plot and Timeline Delete Tools Summary

**4 FK-safe delete tools added to plot.py and timeline.py: delete_plot_thread, delete_event, delete_pov_position, delete_travel_segment**

## Performance

- **Duration:** 8 min
- **Started:** 2026-03-09T19:20:00Z
- **Completed:** 2026-03-09T19:28:00Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Added delete_plot_thread to plot.py with FK-safe pattern (chapter_plot_threads and subplot_touchpoint_log reference plot_threads)
- Added delete_event to timeline.py with FK-safe pattern (event_participants and event_artifacts reference events)
- Added delete_pov_position to timeline.py with FK-safe pattern for pov_chronological_position rows
- Added delete_travel_segment to timeline.py with simpler log-delete (travel_segments is a leaf table)
- Added ValidationFailure to timeline.py shared imports (was missing; required by delete_event and delete_pov_position)

## Task Commits

Each task was committed atomically:

1. **Task 1: Add delete_plot_thread to plot.py** - `826b13b` (feat)
2. **Task 2: Add delete tools to timeline.py** - `1e4e1dc` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified
- `src/novel/tools/plot.py` - Added delete_plot_thread (FK-safe), updated docstrings (3 tools -> 4 tools)
- `src/novel/tools/timeline.py` - Added ValidationFailure import + delete_event, delete_pov_position, delete_travel_segment; updated docstrings (8 tools -> 11 tools)

## Decisions Made
- Delete tools do not call check_gate even in timeline.py (which uses check_gate for reads and writes) — consistent with phase 14 no-gate pattern for all delete tools
- ValidationFailure was missing from timeline.py imports; added to shared import line to enable FK-safe deletes
- delete_travel_segment uses the simpler log-delete pattern (no try/except) since travel_segments has no FK children
- delete_pov_position uses integer primary key (id column) rather than composite key (character_id, chapter_id) to match the delete-by-id convention used across all other delete tools

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Plot and timeline delete tools complete; 4 new delete tools bring phase 14 total to 12 (3 in plan 01, 5 in plan 02, 4 in plan 03)
- Remaining phase 14 plans can continue adding delete tools to other domain modules

---
*Phase: 14-mcp-api-completeness*
*Completed: 2026-03-09*

## Self-Check: PASSED

- FOUND: src/novel/tools/plot.py
- FOUND: src/novel/tools/timeline.py
- FOUND: 14-03-SUMMARY.md
- FOUND: commit 826b13b (Task 1)
- FOUND: commit 1e4e1dc (Task 2)
