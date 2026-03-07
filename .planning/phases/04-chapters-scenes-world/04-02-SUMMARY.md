---
phase: 04-chapters-scenes-world
plan: "02"
subsystem: api
tags: [mcp, fastmcp, sqlite, aiosqlite, pydantic, scenes, scene-goals]

# Dependency graph
requires:
  - phase: 04-chapters-scenes-world-01
    provides: chapters tool module; scenes Pydantic models (Scene, SceneCharacterGoal with to_db_dict)
  - phase: 03-mcp-server-core-characters-relationships
    provides: register(mcp) pattern, get_connection, error contract (NotFoundResponse, ValidationFailure)
provides:
  - src/novel/tools/scenes.py with register() — 4 tools: get_scene, get_scene_character_goals, upsert_scene, upsert_scene_goal
affects:
  - 04-chapters-scenes-world-03 (world tools, server wiring)
  - 03-03-style tests for scenes domain

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "to_db_dict() called before write to serialise JSON TEXT columns (narrative_functions)"
    - "ON CONFLICT(scene_id, character_id) DO UPDATE for junction tables with FK children"
    - "ON CONFLICT(id) DO UPDATE for upsert-by-primary-key pattern"
    - "Scene field_validator auto-parses JSON string to list[str] on read"

key-files:
  created:
    - src/novel/tools/scenes.py
  modified: []

key-decisions:
  - "upsert_scene uses Scene.to_db_dict() to serialise narrative_functions before passing to SQLite — ensures JSON encoding is always correct regardless of caller input"
  - "upsert_scene_goal uses ON CONFLICT(scene_id, character_id) DO UPDATE — consistent with Phase 03 decision to avoid INSERT OR REPLACE on tables with FK children"

patterns-established:
  - "JSON TEXT field pattern: build model object → call to_db_dict() → extract serialised value → use in SQL"

requirements-completed: [CHAP-04, CHAP-05, CHAP-08, CHAP-09]

# Metrics
duration: 2min
completed: 2026-03-07
---

# Phase 04 Plan 02: Scenes Tool Module Summary

**scenes.py register() with 4 typed MCP tools covering scene retrieval, character goal retrieval, and upsert operations for both scenes and scene-character goals**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-03-07T21:38:46Z
- **Completed:** 2026-03-07T21:40:09Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments
- Implemented `get_scene` — retrieves Scene by id with automatic JSON parsing of narrative_functions via field_validator
- Implemented `get_scene_character_goals` — verifies scene existence first, returns ordered list of SceneCharacterGoal records
- Implemented `upsert_scene` — two-branch CREATE/UPDATE using `Scene.to_db_dict()` for correct JSON serialisation of narrative_functions; ON CONFLICT(id) DO UPDATE for updates
- Implemented `upsert_scene_goal` — ON CONFLICT(scene_id, character_id) DO UPDATE ensuring no duplicate dyad rows on FK child table

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement scenes tool module (4 tools)** - `5149ced` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified
- `src/novel/tools/scenes.py` — 4 MCP tools registered via register(mcp); no print() calls; uses logging to stderr

## Decisions Made
- Used `Scene.to_db_dict()` to extract the JSON-serialised `narrative_functions` value before the INSERT — this mirrors the established Phase 02 decision that only models with JSON TEXT columns get `to_db_dict()`, and ensures the serialisation is always correct regardless of caller input shape.
- Used `ON CONFLICT(scene_id, character_id) DO UPDATE` for `upsert_scene_goal` consistent with Phase 03 decision against `INSERT OR REPLACE` on tables with FK children.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Scenes tool module complete; ready for world tools (04-03) and server wiring
- All 4 tools follow the established register(mcp) pattern — wiring in server.py requires only `from novel.tools import scenes` and `scenes.register(mcp)`

---
*Phase: 04-chapters-scenes-world*
*Completed: 2026-03-07*
