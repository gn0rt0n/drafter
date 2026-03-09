---
phase: 14-mcp-api-completeness
plan: "09"
subsystem: api
tags: [mcp, world, cultures, faction_political_states, upsert, sqlite]

# Dependency graph
requires:
  - phase: 14-04
    provides: delete_location and delete_faction added to world.py — sequential to avoid file conflicts
provides:
  - upsert_culture tool (two-branch ON CONFLICT(name)/ON CONFLICT(id) upsert)
  - list_cultures tool (SELECT all ORDER BY name)
  - delete_culture tool (FK-safe delete with try/except)
  - log_faction_political_state tool (log_* pattern with faction FK pre-check)
  - get_current_faction_political_state tool (SELECT ORDER BY id DESC LIMIT 1)
  - delete_faction_political_state tool (log-style delete, no FK children)
affects: [phase-15-docs, world-domain-coverage]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "ON CONFLICT(name) DO UPDATE upsert for tables with UNIQUE(name) — cultures mirrors factions pattern"
    - "log_* pattern: faction FK pre-check, INSERT, lastrowid select-back, return model"
    - "get_current_* pattern: SELECT ORDER BY id DESC LIMIT 1 for most recent log entry"
    - "Log-style delete (no try/except) for append-only log tables without FK children"
    - "FK-safe delete (try/except ValidationFailure) for parent tables referenced by other tables"

key-files:
  created: []
  modified:
    - src/novel/tools/world.py
    - tests/test_world.py

key-decisions:
  - "cultures UNIQUE(name) constraint confirmed in migration 004 — ON CONFLICT(name) upsert pattern used like upsert_faction"
  - "faction_political_states chapter_id is NOT NULL (required) — log_faction_political_state makes chapter_id a required parameter"
  - "delete_faction_political_state uses log-style delete (no try/except) since faction_political_states has no FK children"
  - "delete_culture uses FK-safe try/except since locations and name_registry reference cultures via culture_id"

patterns-established:
  - "upsert_culture: ON CONFLICT(name) when no id, ON CONFLICT(id) when id provided — matches upsert_faction exactly"
  - "get_current_faction_political_state: ORDER BY id DESC LIMIT 1 (by insert order, not chapter_id)"

requirements-completed:
  - MCP-01
  - MCP-02

# Metrics
duration: 3min
completed: 2026-03-09
---

# Phase 14 Plan 09: Cultures and Faction Political States Write Tools Summary

**6 new write tools in world.py: upsert_culture, list_cultures, delete_culture, log_faction_political_state, get_current_faction_political_state, delete_faction_political_state — completing write coverage for two previously read-only world tables**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-09T19:47:42Z
- **Completed:** 2026-03-09T19:50:46Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Added upsert_culture using two-branch ON CONFLICT(name)/ON CONFLICT(id) pattern matching upsert_faction exactly
- Added list_cultures returning all cultures ordered by name
- Added delete_culture with FK-safe try/except (cultures referenced by locations and name_registry)
- Added log_faction_political_state with faction FK pre-check; chapter_id required per NOT NULL schema constraint
- Added get_current_faction_political_state returning most recent entry by ORDER BY id DESC LIMIT 1
- Added delete_faction_political_state as log-style delete (no FK children on this table)
- 20 tests pass including 12 new tests for the 6 new tools

## Task Commits

Each task was committed atomically:

1. **TDD RED: Failing tests for all 6 tools** - `257ae68` (test)
2. **Task 1: Add cultures write tools** - `9a2db7e` (feat)
3. **Task 2: Add faction_political_states write tools** - `48e7f26` (feat)

_Note: TDD tasks have multiple commits (test RED → feat GREEN)_

## Files Created/Modified
- `src/novel/tools/world.py` - Added upsert_culture, list_cultures, delete_culture, log_faction_political_state, get_current_faction_political_state, delete_faction_political_state; updated docstring to "14 world domain tools"
- `tests/test_world.py` - Added 12 new tests covering all 6 new tools

## Decisions Made
- cultures has `UNIQUE(name)` constraint in migration 004 — confirmed before implementing, used ON CONFLICT(name) pattern like upsert_faction
- faction_political_states.chapter_id is `NOT NULL` in schema — made it a required parameter in log_faction_political_state (plan spec showed it as optional but schema enforces it)
- delete_culture uses FK-safe try/except: locations.culture_id and name_registry.culture_id reference cultures
- delete_faction_political_state uses simpler log-style delete: no FK children on faction_political_states

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed test using non-existent chapter_id=4**
- **Found during:** Task 2 (test_delete_faction_political_state_success)
- **Issue:** Test used chapter_id=4 for log_faction_political_state but seed only has 3 chapters — caused FK constraint failure
- **Fix:** Changed test to use chapter_id=2 (seed has chapter_ids 1, 2, 3; faction_id=1 uses chapter_id=1 in seed, chapter_id=3 in prior test)
- **Files modified:** tests/test_world.py
- **Verification:** All 20 tests pass
- **Committed in:** 48e7f26 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 — bug in test)
**Impact on plan:** Minimal — test data fix only, implementation unchanged. No scope creep.

## Issues Encountered
- faction_political_states.chapter_id has NOT NULL constraint (schema requires it), while plan spec suggested it as optional. Made it a required parameter rather than optional since the DB will reject NULLs anyway.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- world.py now has full write coverage for all world tables: locations, factions, cultures, and faction_political_states
- Ready for Phase 15 documentation work
- No blockers

## Self-Check: PASSED
- src/novel/tools/world.py: FOUND
- tests/test_world.py: FOUND
- 14-09-SUMMARY.md: FOUND
- Commit 257ae68: FOUND
- Commit 9a2db7e: FOUND
- Commit 48e7f26: FOUND

---
*Phase: 14-mcp-api-completeness*
*Completed: 2026-03-09*
