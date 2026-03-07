---
phase: 03-mcp-server-core-characters-relationships
plan: "02"
subsystem: api
tags: [mcp, fastmcp, sqlite, aiosqlite, pydantic, relationships, tdd]

# Dependency graph
requires:
  - phase: 03-mcp-server-core-characters-relationships
    provides: register(mcp) pattern from Plan 01 (characters), FastMCP instance, get_connection() async context manager
  - phase: 02-pydantic-models-seed-data
    provides: CharacterRelationship, RelationshipChangeEvent, PerceptionProfile models, minimal seed data
  - phase: 01-project-foundation-database
    provides: migrations (character_relationships, relationship_change_events, perception_profiles tables), DB connection layer
provides:
  - src/novel/tools/relationships.py with register(mcp) exposing 6 relationship domain tools
  - REL-01 get_relationship (bi-directional symmetry query)
  - REL-02 list_relationships (OR query on both FK columns)
  - REL-03 upsert_relationship (canonical min/max ordering enforced)
  - REL-04 get_perception_profile
  - REL-05 upsert_perception_profile
  - REL-06 log_relationship_change (relationship existence verified before insert)
affects:
  - 03-mcp-server-core-characters-relationships (Plan 03 wires register calls into server.py)
  - future phases using relationship queries

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "register(mcp: FastMCP) -> None domain tool module pattern (consistent with Plan 01)"
    - "Relationship symmetry: get queries both (a,b) and (b,a); upsert canonicalizes via min/max"
    - "ON CONFLICT DO UPDATE for upsert tools — never INSERT OR REPLACE (avoids FK cascade failures)"
    - "TDD test helpers must use ON CONFLICT DO UPDATE not INSERT OR REPLACE when FKs could cascade"

key-files:
  created:
    - src/novel/tools/relationships.py
    - tests/test_relationships.py
  modified: []

key-decisions:
  - "get_relationship queries both orderings via OR clause — caller never needs to know canonical storage order"
  - "upsert_relationship canonicalizes (min, max) before INSERT to prevent duplicate dyad rows"
  - "log_relationship_change verifies relationship_id exists before inserting the event row"
  - "Test helper insert_relationship uses ON CONFLICT DO UPDATE (not INSERT OR REPLACE) to avoid FK cascade failures when seed rows have change-event children"

patterns-established:
  - "Relationship symmetry pattern: query both orderings for get; canonicalize for upsert"
  - "TDD test helpers: prefer ON CONFLICT DO UPDATE over INSERT OR REPLACE when target table has FK children"

requirements-completed: [REL-01, REL-02, REL-03, REL-04, REL-05, REL-06]

# Metrics
duration: 4min
completed: 2026-03-07
---

# Phase 03 Plan 02: Relationship Domain Tools Summary

**6 FastMCP relationship tools delivering A-B symmetry queries, canonical min/max ordering, and directional perception profiles via register(mcp) pattern**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-07T20:59:00Z
- **Completed:** 2026-03-07T21:03:00Z
- **Tasks:** 1 (TDD: RED + GREEN phases)
- **Files modified:** 2

## Accomplishments
- Implemented all 6 REL-domain tools in `src/novel/tools/relationships.py` with zero print() calls
- Enforced relationship symmetry: `get_relationship` queries both orderings; `upsert_relationship` canonicalizes with `min/max` before INSERT
- All 15 tests pass (103 total in test suite — no regressions)

## Task Commits

Each task was committed atomically:

1. **Task 1 RED: Failing tests for relationship tools** - `996b810` (test)
2. **Task 1 GREEN: Implement relationships.py + fix test helpers** - `fe2e91c` (feat)

**Plan metadata:** (docs commit follows)

_Note: TDD task produced two commits (test RED → feat GREEN)_

## Files Created/Modified
- `src/novel/tools/relationships.py` — 6 relationship domain tools via register(mcp) pattern
- `tests/test_relationships.py` — 15 tests covering all 6 tools + error contract

## Decisions Made
- `get_relationship` uses `OR` clause to query both `(a,b)` and `(b,a)` orderings — caller doesn't need to know canonical storage order
- `upsert_relationship` applies `a, b = min(character_a_id, character_b_id), max(...)` canonicalization before INSERT to prevent duplicate dyad rows
- `log_relationship_change` first verifies `relationship_id` exists in `character_relationships`, returning `NotFoundResponse` if not — prevents orphaned change events
- Test helper `insert_relationship` changed from `INSERT OR REPLACE` to `ON CONFLICT DO UPDATE` — `INSERT OR REPLACE` deletes the old row first, which triggers FK cascade failure when the seed row has `relationship_change_events` children

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed test helper UNIQUE constraint failures**
- **Found during:** Task 1 GREEN (test run)
- **Issue:** `insert_relationship()` used bare `INSERT INTO` which failed UNIQUE constraint when seed data already contained (1,3) and (1,2) perception rows
- **Fix 1:** Changed to `ON CONFLICT DO UPDATE` to handle seed-preexisting rows without deleting them
- **Fix 2:** Changed perception profile setup in `test_get_perception_profile_found` to `INSERT OR REPLACE` (safe since perception_profiles has no FK children)
- **Fix 3:** Changed `INSERT OR REPLACE` back to `ON CONFLICT DO UPDATE` on the relationship helper after discovering FK cascade failure
- **Files modified:** tests/test_relationships.py
- **Verification:** All 15 tests pass
- **Committed in:** fe2e91c (Task 1 feat commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - test infrastructure bug)
**Impact on plan:** Fix necessary for test correctness against seeded DB. No scope creep. Implementation module unchanged.

## Issues Encountered
- Seed data pre-populates `character_relationships` rows for (protagonist=1, mentor=3), (protagonist=1, ally=4), (protagonist=1, rival=5) and one `perception_profiles` row for (protagonist=1, antagonist=2) — test helpers must account for pre-existing rows in the shared module-scope fixture DB.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Both `tools/characters.py` and `tools/relationships.py` are complete with all tools registered via `register(mcp)`
- Plan 03 (server wiring) can now call `characters.register(mcp)` and `relationships.register(mcp)` in `server.py`
- No blockers or concerns

---
*Phase: 03-mcp-server-core-characters-relationships*
*Completed: 2026-03-07*
