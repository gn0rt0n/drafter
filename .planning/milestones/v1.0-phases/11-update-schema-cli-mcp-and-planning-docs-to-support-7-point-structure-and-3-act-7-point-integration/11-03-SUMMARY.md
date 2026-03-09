---
phase: 11-update-schema-cli-mcp-and-planning-docs-to-support-7-point-structure-and-3-act-7-point-integration
plan: "03"
subsystem: mcp
tags: [fastmcp, sqlite, structure, 7-point, pydantic, testing]

# Dependency graph
requires:
  - phase: 11-01
    provides: migration 022 (story_structure + arc_seven_point_beats tables) and Pydantic models
  - phase: 11-02
    provides: gate.py with 36 GATE_ITEM_META entries including struct_story_beats and arcs_seven_point_beats
provides:
  - 4 MCP structure tools via tools/structure.py (get_story_structure, upsert_story_structure, get_arc_beats, upsert_arc_beat)
  - structure domain wired into MCP server
  - test_structure.py with 7 in-memory FastMCP client tests
  - TABLE_MODEL_MAP coverage for story_structure and arc_seven_point_beats
  - database-schema.md Section 3 updated with both new table definitions
affects:
  - future phases consuming structure data via MCP

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "VALID_BEAT_TYPES frozenset for Python-side enum validation (no SQL CHECK constraint)"
    - "Single-branch ON CONFLICT upsert for UNIQUE(book_id) and UNIQUE(arc_id, beat_type)"
    - "gate-free tools: structure tools populate data that gate checks, so no check_gate() calls"

key-files:
  created:
    - src/novel/tools/structure.py
    - tests/test_structure.py
  modified:
    - src/novel/mcp/server.py
    - tests/test_schema_validation.py
    - tests/test_gate.py
    - project-research/database-schema.md
    - src/novel/db/seed.py

key-decisions:
  - "test_structure.py uses create_connected_server_and_client_session(mcp) not mcp._mcp_server — matches test_arcs.py pattern"
  - "gate_ready seed inserts story_structure rows for both books (book_id=1 and 2) — minimal seed has 2 books, gate query checks ALL books"
  - "structure tools are gate-free — they populate data that gate checks, requiring no prior certification"

patterns-established:
  - "Structure test pattern: session-scoped DB + _call_tool with create_connected_server_and_client_session(mcp)"

requirements-completed: [STRUCT-05, STRUCT-06, STRUCT-07]

# Metrics
duration: 5min
completed: 2026-03-09
---

# Phase 11 Plan 03: Structure MCP Tools Summary

**4 gate-free MCP structure tools (get/upsert story_structure, get/upsert arc_seven_point_beats) wired into FastMCP server, with 7 passing in-memory client tests and 36+1 gate count assertions updated**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-09T14:44:00Z
- **Completed:** 2026-03-09T14:46:24Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments
- Created `tools/structure.py` with 4 MCP tools using `register(mcp)` pattern: `get_story_structure`, `upsert_story_structure` (single-branch ON CONFLICT(book_id)), `get_arc_beats` (empty list valid), `upsert_arc_beat` (Python-side VALID_BEAT_TYPES validation)
- Wired structure domain into `server.py` — import extended and `structure.register(mcp)` added in Phase 11 block
- Created `test_structure.py` with 7 asyncio tests covering all 4 tools including invalid beat_type validation
- Updated `test_gate.py` count assertions from 35 to 37 (36 GATE_ITEM_META + 1 min_characters)
- Updated `test_schema_validation.py` TABLE_MODEL_MAP with `story_structure` and `arc_seven_point_beats`
- Updated `database-schema.md` Section 3 with both new table definitions

## Task Commits

Each task was committed atomically:

1. **Task 1: Create tools/structure.py and wire into server.py** - `1f7cc24` (feat)
2. **Task 2: Update tests and docs** - `9b4ee95` (feat)

## Files Created/Modified
- `src/novel/tools/structure.py` - 4 MCP structure tools via register(mcp) pattern
- `src/novel/mcp/server.py` - structure added to tools import and register call in Phase 11 block
- `tests/test_structure.py` - 7 in-memory FastMCP client tests for all 4 structure tools
- `tests/test_schema_validation.py` - StoryStructure and ArcSevenPointBeat added to TABLE_MODEL_MAP
- `tests/test_gate.py` - count assertions updated 35→37 throughout
- `project-research/database-schema.md` - story_structure and arc_seven_point_beats table definitions added to Section 3
- `src/novel/db/seed.py` - gate_ready seed now inserts story_structure for both books (book_id=1 and 2)

## Decisions Made
- `test_structure.py` uses `create_connected_server_and_client_session(mcp)` (not `mcp._mcp_server`) — the plan template had the wrong form; correct form matches `test_arcs.py` pattern established in Phase 03-03
- `gate_ready` seed required story_structure rows for both books (book_id=1 and 2) — `_load_minimal()` inserts 2 books but the plan only seeded 1 story_structure row; the gate query `struct_story_beats` checks ALL books so missing_count was 1 instead of 0

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed test_structure.py _call_tool helper using wrong MCP session form**
- **Found during:** Task 2 (Create test_structure.py)
- **Issue:** Plan template used `create_connected_server_and_client_session(mcp._mcp_server) as (_, client)` which raised `TypeError: cannot unpack non-iterable ClientSession object`
- **Fix:** Changed to `create_connected_server_and_client_session(mcp) as session` matching `test_arcs.py` pattern
- **Files modified:** tests/test_structure.py
- **Verification:** All 7 test_structure.py tests pass
- **Committed in:** 9b4ee95 (Task 2 commit)

**2. [Rule 1 - Bug] Fixed gate_ready seed to insert story_structure for both books**
- **Found during:** Task 2 verification (test_gate.py::test_run_gate_audit_gate_ready_all_pass)
- **Issue:** Plan only seeded story_structure for book_id=1 but minimal seed has 2 books; `struct_story_beats` gate query checks ALL books so missing_count=1, causing test failure
- **Fix:** Changed seed to iterate over (1, 2) and insert a story_structure row for each book
- **Files modified:** src/novel/db/seed.py
- **Verification:** test_run_gate_audit_gate_ready_all_pass passes; full suite 273/273
- **Committed in:** 9b4ee95 (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (2 Rule 1 bugs)
**Impact on plan:** Both auto-fixes necessary for test correctness. No scope creep.

## Issues Encountered
- gate_ready seed missing story_structure for book_id=2 — resolved by iterating both book IDs in the seed INSERT loop

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 11 complete — all 3 plans executed
- 4 structure MCP tools callable by Claude via in-memory FastMCP client
- Full test suite (273 tests) passes with no regressions
- Gate check count updated to 37 (36 SQL checks + 1 min_characters manual item)

---
*Phase: 11-update-schema-cli-mcp-and-planning-docs-to-support-7-point-structure-and-3-act-7-point-integration*
*Completed: 2026-03-09*
