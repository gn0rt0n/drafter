---
phase: 04-chapters-scenes-world
plan: 03
subsystem: api
tags: [mcp, fastmcp, sqlite, aiosqlite, pydantic, world, locations, factions, cultures]

# Dependency graph
requires:
  - phase: 04-chapters-scenes-world-01
    provides: chapters tool module pattern (register(mcp), NotFoundResponse, ValidationFailure)
  - phase: 02-pydantic-models-seed-data
    provides: Location, Faction, FactionPoliticalState, Culture models with to_db_dict()
provides:
  - World domain MCP tools: get_location, get_faction, get_faction_political_state, get_culture, upsert_location, upsert_faction
  - sensory_profile JSON round-trip via Location.to_db_dict() and field_validator auto-parse
  - political state retrieval with most-recent or chapter-specific lookup
  - faction upsert using UNIQUE(name) conflict target (no id required)
affects: [05-plot-arcs, 06-gate-system, 09-names-voice-publishing]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "World tool module follows register(mcp) pattern established in Phase 03"
    - "JSON TEXT columns: to_db_dict() for writes, field_validator for reads (Location.sensory_profile)"
    - "Two-branch upsert: None id → INSERT + lastrowid; provided id → ON CONFLICT(id) DO UPDATE"
    - "Name-conflict upsert for Faction: ON CONFLICT(name) DO UPDATE; always re-query by name after write"
    - "Political state log table: read-only in world module; upsert_faction never touches faction_political_states"

key-files:
  created:
    - src/novel/tools/world.py
  modified: []

key-decisions:
  - "upsert_location uses two-branch pattern (None id → INSERT, provided id → ON CONFLICT(id) DO UPDATE) — locations table has no UNIQUE other than PK"
  - "upsert_faction uses ON CONFLICT(name) for None-id branch; always SELECT back by name (lastrowid is 0 on conflict)"
  - "get_faction_political_state accepts optional chapter_id: None returns most recent (ORDER BY chapter_id DESC LIMIT 1), provided value returns exact row"
  - "upsert_faction explicitly does NOT write to faction_political_states — separate time-stamped log table"

patterns-established:
  - "JSON column round-trip: Location model handles sensory_profile via to_db_dict() on write, field_validator on read"
  - "Name-keyed faction upsert: ON CONFLICT(name) works without knowing the PK; SELECT by name ensures correct row return"

requirements-completed: [WRLD-01, WRLD-02, WRLD-03, WRLD-04, WRLD-09, WRLD-10]

# Metrics
duration: 3min
completed: 2026-03-07
---

# Phase 04 Plan 03: World Tool Module Summary

**6 world domain MCP tools covering location, faction, political state, and culture — with JSON sensory_profile round-trip and name-keyed faction upsert**

## Performance

- **Duration:** ~3 min
- **Started:** 2026-03-07T21:41:54Z
- **Completed:** 2026-03-07T21:44:45Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments
- Implemented `src/novel/tools/world.py` with `register(mcp)` exposing 6 world domain tools
- `get_location` returns Location with sensory_profile auto-parsed from JSON string to dict via field_validator
- `get_faction_political_state` handles optional chapter_id — None returns most recent, provided value returns exact match
- `upsert_location` uses Location.to_db_dict() for sensory_profile serialisation on the INSERT branch
- `upsert_faction` uses UNIQUE(name) conflict target for the None-id branch; always re-queries by name to handle lastrowid=0 on conflict
- All 6 tools implement the error contract: NotFoundResponse for missing records, ValidationFailure for DB errors

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement world tool module (6 tools)** - `0356c20` (feat)

**Plan metadata:** (docs commit below)

## Files Created/Modified
- `src/novel/tools/world.py` - World domain MCP tools: get_location, get_faction, get_faction_political_state, get_culture, upsert_location, upsert_faction

## Decisions Made
- upsert_location uses two-branch pattern: None id → INSERT letting AUTOINCREMENT fire, provided id → ON CONFLICT(id) DO UPDATE (locations has no UNIQUE besides PK)
- upsert_faction with None id uses ON CONFLICT(name) conflict target; always SELECT back by name since lastrowid is 0 when the conflict path fires
- get_faction_political_state optional chapter_id: None → most recent row (ORDER BY chapter_id DESC LIMIT 1), provided → exact WHERE faction_id=? AND chapter_id=?
- faction_political_states is a read-only log table in this module; upsert_faction deliberately does not write to it

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- World domain tools ready for integration in Phase 04 server wiring
- All 6 world tools (WRLD-01/02/03/04/09/10) complete
- Pattern consistent with characters.py, relationships.py, chapters.py, scenes.py tool modules

## Self-Check: PASSED

- FOUND: `src/novel/tools/world.py`
- FOUND: `.planning/phases/04-chapters-scenes-world/04-03-SUMMARY.md`
- FOUND: commit `0356c20`

---
*Phase: 04-chapters-scenes-world*
*Completed: 2026-03-07*
