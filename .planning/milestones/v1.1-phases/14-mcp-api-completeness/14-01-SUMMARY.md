---
phase: 14-mcp-api-completeness
plan: "01"
subsystem: api
tags: [mcp, fastmcp, delete-tools, fk-safe, sqlite, aiosqlite]

# Dependency graph
requires:
  - phase: 03-mcp-server-characters-relationships
    provides: characters.py, relationships.py with existing get/list/upsert tools
  - phase: 05-plot-arcs
    provides: arcs.py with existing get_arc, get_chekovs_guns, upsert_chekov tools
provides:
  - delete_character (FK-safe, NotFoundResponse | ValidationFailure | dict)
  - delete_character_knowledge (log-table, NotFoundResponse | dict)
  - delete_relationship (FK-safe, NotFoundResponse | ValidationFailure | dict)
  - delete_relationship_change (log-table, NotFoundResponse | dict)
  - delete_perception_profile (FK-safe pattern, NotFoundResponse | ValidationFailure | dict)
  - delete_arc (FK-safe, NotFoundResponse | ValidationFailure | dict)
  - delete_arc_health_log (log-table, NotFoundResponse | dict)
  - delete_chekov (FK-safe pattern, NotFoundResponse | ValidationFailure | dict)
affects: [14-mcp-api-completeness, 15-docs-and-polish]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "FK-safe delete: pre-existence check returns NotFoundResponse, try/except DELETE returns ValidationFailure on constraint failure, success dict on pass"
    - "Log-table delete: pre-existence check returns NotFoundResponse, DELETE without try/except (no FK children), success dict on pass"

key-files:
  created: []
  modified:
    - src/novel/tools/characters.py
    - src/novel/tools/relationships.py
    - src/novel/tools/arcs.py

key-decisions:
  - "FK-safe pattern used for delete_relationship and delete_perception_profile even where no known FK children exist — safety-first consistency"
  - "Log-table pattern (no try/except) used for delete_character_knowledge, delete_relationship_change, delete_arc_health_log — these are append-only log tables with no FK children"
  - "No gate checks added to any delete tools — characters, relationships, arcs modules are not gate-gated"

patterns-established:
  - "FK-safe delete: pre-existence SELECT then try/except DELETE — pattern for all heavily-referenced tables"
  - "Log-table delete: pre-existence SELECT then direct DELETE — pattern for append-only log tables with no FK children"

requirements-completed: [MCP-01, MCP-02]

# Metrics
duration: 2min
completed: 2026-03-09
---

# Phase 14 Plan 01: Character Domain Delete Tools Summary

**8 FK-safe delete tools added across characters.py, relationships.py, and arcs.py using two-tier pattern (FK-safe try/except vs log-table direct delete)**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-09T19:07:27Z
- **Completed:** 2026-03-09T19:09:23Z
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments

- Added delete_character and delete_character_knowledge to characters.py (10 total tools, was 8)
- Added delete_relationship, delete_relationship_change, delete_perception_profile to relationships.py (9 total tools, was 6)
- Added delete_arc, delete_arc_health_log, delete_chekov to arcs.py (9 total tools, was 6)
- Established two-tier delete pattern: FK-safe (try/except ValidationFailure) for parent tables, log-table (direct delete) for leaf tables
- All modules import cleanly via `uv run python -c "from novel.tools.* import register"`

## Task Commits

Each task was committed atomically:

1. **Task 1: Add delete tools to characters.py** - `602bd86` (feat)
2. **Task 2: Add delete tools to relationships.py** - `86b9e39` (feat)
3. **Task 3: Add delete tools to arcs.py** - `49a484e` (feat)

**Plan metadata:** _(docs commit follows)_

## Files Created/Modified

- `src/novel/tools/characters.py` - Added delete_character (FK-safe) and delete_character_knowledge (log-table); docstring updated to 10 tools
- `src/novel/tools/relationships.py` - Added delete_relationship (FK-safe), delete_relationship_change (log-table), delete_perception_profile (FK-safe); docstring updated to 9 tools
- `src/novel/tools/arcs.py` - Added delete_arc (FK-safe), delete_arc_health_log (log-table), delete_chekov (FK-safe); docstring updated to 9 tools

## Decisions Made

- **FK-safe vs log-table pattern assignment:** characters, character_arcs, character_relationships, perception_profiles, chekovs_gun_registry all get FK-safe pattern. character_knowledge, relationship_change_events, arc_health_log get log-table (simpler) pattern — these are explicitly append-only log tables.
- **delete_perception_profile uses FK-safe pattern** despite no confirmed FK children — safety-first consistency with the rest of the approach.
- **No gate checks:** arcs, characters, and relationships modules have no check_gate() calls on any existing tools; new delete tools follow the same pattern (no gates).

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Character domain delete tools complete for Phase 14
- Remaining Phase 14 plans will add delete tools to the other 15 tool modules (chapters, scenes, world, plot, sessions, timeline, canon, knowledge, foreshadowing, names, voice, publishing)
- Pattern established in this plan should be applied consistently to all remaining delete tools

---
*Phase: 14-mcp-api-completeness*
*Completed: 2026-03-09*
