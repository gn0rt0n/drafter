---
phase: 14-mcp-api-completeness
plan: "18"
subsystem: api
tags: [mcp, sqlite, junction-tables, plot-threads, character-arcs, tdd]

# Dependency graph
requires:
  - phase: 14-mcp-api-completeness
    plan: "03"
    provides: "delete_plot_thread added to plot.py"
  - phase: 14-mcp-api-completeness
    plan: "08"
    provides: "upsert_arc and log_subplot_touchpoint added to arcs.py"
provides:
  - link_chapter_to_plot_thread, unlink_chapter_from_plot_thread, get_plot_threads_for_chapter (plot.py)
  - link_chapter_to_arc, unlink_chapter_from_arc, get_arcs_for_chapter (arcs.py)
  - Full M:N junction coverage for chapter_plot_threads and chapter_character_arcs tables
affects: [phase-15-docs, any plan querying chapter narrative coverage]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Junction tool pattern: FK checks on both sides before INSERT ON CONFLICT DO UPDATE
    - Unlink idempotent pattern: SELECT existence check before DELETE, NotFoundResponse if absent
    - GET junction list pattern: SELECT * WHERE chapter_id=? ORDER BY FK_id

key-files:
  created: []
  modified:
    - src/novel/tools/plot.py
    - src/novel/tools/arcs.py
    - tests/test_plot.py
    - tests/test_arcs.py

key-decisions:
  - "arc_progression is the real schema column in chapter_character_arcs (not arc_role as in plan interface) — confirmed from migration 017"
  - "ChapterCharacterArc model is in novel.models.plot (not novel.models.arcs) — imported cross-module"
  - "chapter_plot_threads and chapter_character_arcs both have surrogate id columns (AUTOINCREMENT PK) with UNIQUE(chapter_id, FK_id) — ON CONFLICT targets composite unique, not PK"

patterns-established:
  - "Junction link tool: verify chapter FK, verify entity FK, INSERT ON CONFLICT(chapter_id, entity_id) DO UPDATE, SELECT back by composite key"
  - "Junction unlink tool: SELECT id WHERE composite key, NotFoundResponse if missing, DELETE, return unlinked dict"
  - "Junction query tool: SELECT * WHERE chapter_id=? ORDER BY entity_id, return list[Model]"

requirements-completed: [MCP-01, MCP-02]

# Metrics
duration: 3min
completed: 2026-03-09
---

# Phase 14 Plan 18: Chapter Junction Tools for Plot Threads and Arcs Summary

**Six M:N junction tools linking chapters to plot threads (plot.py) and character arcs (arcs.py) with FK validation, idempotent upsert, and idempotent delete**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-09T20:32:44Z
- **Completed:** 2026-03-09T20:35:44Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Added 3 junction tools to plot.py: link_chapter_to_plot_thread (FK checks + ON CONFLICT upsert), unlink_chapter_from_plot_thread (idempotent DELETE), get_plot_threads_for_chapter (list query)
- Added 3 junction tools to arcs.py: link_chapter_to_arc (FK checks + ON CONFLICT upsert), unlink_chapter_from_arc (idempotent DELETE), get_arcs_for_chapter (list query)
- Full TDD coverage: 7 tests per module (14 total), all passing — RED commits precede GREEN commits for each task
- Both modules import cleanly, no gate checks, no print()

## Task Commits

Each task was committed atomically:

1. **Task 1 (TDD RED): Failing tests for plot.py junction tools** - `de17e72` (test)
2. **Task 1 (TDD GREEN): chapter_plot_threads junction tools to plot.py** - `e7e5b9d` (feat)
3. **Task 2 (TDD RED): Failing tests for arcs.py junction tools** - `61da197` (test)
4. **Task 2 (TDD GREEN): chapter_character_arcs junction tools to arcs.py** - `a62ebf0` (feat)

_Note: TDD tasks have multiple commits (test RED → feat GREEN)_

## Files Created/Modified
- `src/novel/tools/plot.py` - Added ChapterPlotThread import + 3 junction tools (link, unlink, get); docstring updated to 7 tools
- `src/novel/tools/arcs.py` - Added ChapterCharacterArc import from novel.models.plot + 3 junction tools (link, unlink, get); docstring updated to 15 tools
- `tests/test_plot.py` - 7 new tests for chapter_plot_threads junction tools
- `tests/test_arcs.py` - 7 new tests for chapter_character_arcs junction tools

## Decisions Made
- **arc_progression not arc_role**: The plan interface specified `arc_role` as the parameter name, but the real schema column in chapter_character_arcs (migration 017) is `arc_progression`. Used the real column name to match the schema and `ChapterCharacterArc` model.
- **Cross-module import**: `ChapterCharacterArc` is defined in `novel.models.plot` (not `novel.models.arcs`), so arcs.py imports it cross-module. This is correct — the model file groups plot/chapter-arc junction models together.
- **Surrogate PK confirmed**: Both junction tables have AUTOINCREMENT `id` columns with UNIQUE(chapter_id, FK_id). ON CONFLICT targets the composite unique constraint, not the PK.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Used arc_progression instead of arc_role for chapter_character_arcs**
- **Found during:** Task 2 (schema inspection before implementation)
- **Issue:** Plan interface specified `arc_role` parameter, but real schema uses `arc_progression` (confirmed from migration 017 and ChapterCharacterArc model)
- **Fix:** Used `arc_progression` as both parameter name and SQL column name throughout; tests use `arc_progression` consistently
- **Files modified:** src/novel/tools/arcs.py, tests/test_arcs.py
- **Verification:** Import OK, all 7 arcs junction tests pass
- **Committed in:** a62ebf0 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 schema mismatch corrected)
**Impact on plan:** Required for correctness — using wrong column name would cause INSERT failures. No scope creep.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Self-Check: PASSED

All created/modified files exist on disk. All 4 task commits confirmed in git log.

## Next Phase Readiness
- All 6 junction tools operational: Claude Code can now associate chapters with plot threads and character arcs
- chapter_plot_threads and chapter_character_arcs tables fully covered
- Ready for Phase 15 (documentation)

---
*Phase: 14-mcp-api-completeness*
*Completed: 2026-03-09*
