---
phase: 14-mcp-api-completeness
plan: "14"
subsystem: api
tags: [mcp, sqlite, artifacts, object_states, world, upsert, fk-safe]

# Dependency graph
requires:
  - phase: 14-13
    provides: books, acts, eras CRUD tools added to world.py in same file

provides:
  - get_artifact, list_artifacts, upsert_artifact (two-branch), delete_artifact (FK-safe)
  - get_object_states, log_object_state, delete_object_state tools in world.py

affects: [world-domain, artifact-tracking, object-state-log]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - two-branch upsert (artifact_id None=INSERT, int=ON CONFLICT(id))
    - FK-safe delete with try/except ValidationFailure for tables with FK children
    - log_* pattern with dual FK pre-checks (artifact_id + chapter_id)
    - log-style delete (no try/except) for leaf tables

key-files:
  created: []
  modified:
    - src/novel/tools/world.py

key-decisions:
  - "Artifact model uses current_owner_id/current_location_id/significance/magical_properties/history fields — real schema from migration 010, not simplified plan interface"
  - "ObjectState model uses owner_id/location_id/condition fields — real schema from migration 021"
  - "delete_artifact FK-safe (object_states artifact_id NOT NULL + event_artifacts junction table both reference artifacts)"
  - "delete_object_state log-style (leaf table with no FK children) — no try/except needed"
  - "log_object_state pre-checks both artifact_id and chapter_id FKs before INSERT"
  - "object_states has UNIQUE(artifact_id, chapter_id) — only one state per artifact per chapter"

patterns-established:
  - "log_* tools with two FK pre-checks: confirm parent + secondary FK before INSERT"

requirements-completed: [MCP-01, MCP-02]

# Metrics
duration: 2min
completed: 2026-03-09
---

# Phase 14 Plan 14: Artifacts and Object States CRUD Summary

**7 new MCP tools for artifacts (magic items/relics) and object_states (item state log) — full CRUD coverage for both previously-uncovered world tables**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-09T20:28:31Z
- **Completed:** 2026-03-09T20:30:08Z
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments
- Added Artifact and ObjectState to world.py imports from novel.models.world
- Implemented get_artifact, list_artifacts, upsert_artifact (two-branch), delete_artifact (FK-safe vs object_states + event_artifacts)
- Implemented get_object_states, log_object_state (dual FK pre-checks), delete_object_state (log-style)
- Updated module and register() docstring from 26 to 33 tools

## Task Commits

Each task was committed atomically:

1. **Task 1 + Task 2: artifacts and object_states full CRUD** - `396beb5` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified
- `src/novel/tools/world.py` - Added Artifact/ObjectState imports + 7 new tool functions (301 lines inserted)

## Decisions Made
- Artifact model uses real schema columns from migration 010: current_owner_id, current_location_id, significance, magical_properties, history, canon_status, source_file (not the simplified plan interface which had different field names)
- ObjectState model uses real schema columns from migration 021: owner_id, location_id, condition (not state_description as in plan interface)
- delete_artifact is FK-safe because object_states.artifact_id is NOT NULL FK and event_artifacts.artifact_id also references it
- delete_object_state uses log-style delete (no try/except) since object_states is a leaf table with no FK children
- log_object_state pre-checks both artifact_id (in artifacts) and chapter_id (in chapters) before inserting

## Deviations from Plan

None - plan executed exactly as written, adjusted for real schema columns per standard practice established in prior plans.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All 7 artifact/object_state tools complete and importable
- world.py now has 33 tools covering books, eras, acts, locations, factions, cultures, artifacts, object_states, faction_political_states
- Ready for any remaining phase 14 plans

## Self-Check: PASSED
- src/novel/tools/world.py: FOUND
- 14-14-SUMMARY.md: FOUND
- commit 396beb5: FOUND

---
*Phase: 14-mcp-api-completeness*
*Completed: 2026-03-09*
