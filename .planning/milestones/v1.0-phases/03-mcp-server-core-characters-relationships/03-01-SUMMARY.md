---
phase: 03-mcp-server-core-characters-relationships
plan: "01"
subsystem: api
tags: [mcp, fastmcp, aiosqlite, pydantic, characters, sqlite]

# Dependency graph
requires:
  - phase: 02-pydantic-models-seed-data
    provides: Character, CharacterKnowledge, CharacterBelief, CharacterLocation, InjuryState Pydantic models; minimal seed with 5 characters and 3 chapters
  - phase: 01-project-foundation-database
    provides: get_connection() async context manager; migrations; NotFoundResponse, ValidationFailure shared models
provides:
  - src/novel/tools/characters.py with register(mcp: FastMCP) -> None
  - 8 character domain MCP tools: get_character, list_characters, upsert_character, get_character_injuries, get_character_beliefs, get_character_knowledge, log_character_knowledge, get_character_location
  - test suite (17 tests) covering all character tools via FastMCP.call_tool()
affects: [03-02-relationships, 03-03-server-wiring, 04-chapters-scenes-world, all-domain-tool-phases]

# Tech tracking
tech-stack:
  added: [pytest-asyncio>=1.3.0]
  patterns:
    - register(mcp: FastMCP) -> None domain tool registration pattern
    - async with get_connection() as conn for every tool
    - NotFoundResponse returned (not raised) for missing records
    - ValidationFailure returned (not raised) for DB errors
    - cursor.lastrowid (not conn.lastrowid) for aiosqlite INSERT row ID
    - Chapter-scoped state queries use WHERE chapter_id <= ? ORDER BY chapter_id DESC

key-files:
  created:
    - src/novel/tools/characters.py
    - tests/test_characters.py
  modified:
    - pyproject.toml

key-decisions:
  - "cursor.lastrowid used for aiosqlite INSERT row ID — aiosqlite Connection does not expose lastrowid, only the cursor from execute() does"
  - "Test FK safety: test fixtures that insert into character_knowledge, character_locations, injury_states must use chapter IDs that exist in the seeded DB (1, 2, 3 from minimal seed)"
  - "Docstring text must not contain literal print( — rewrote docstring to avoid false positives in the no-print test"
  - "pytest-asyncio added as dev dependency and asyncio_mode=auto set in pyproject.toml — strict mode requires explicit decorator on every test"

patterns-established:
  - "Domain tool module pattern: all tools defined as local async functions inside register(mcp) and decorated with @mcp.tool()"
  - "State query pattern: verify character exists first, then query state table with optional chapter_id <= N scoping"
  - "Upsert pattern: character_id=None omits id column so AUTOINCREMENT fires; non-None uses ON CONFLICT(id) DO UPDATE SET"
  - "FastMCP test pattern: call_tool() returns (content_blocks, structured_dict); structured_dict['result'] contains the serialized return value"

requirements-completed: [ERRC-01, ERRC-02, ERRC-04, CHAR-01, CHAR-02, CHAR-03, CHAR-04, CHAR-05, CHAR-06, CHAR-07]

# Metrics
duration: 5min
completed: 2026-03-07
---

# Phase 03 Plan 01: Character Domain MCP Tools Summary

**8 async character tools in tools/characters.py registered via register(mcp: FastMCP) with error contract (NotFoundResponse/ValidationFailure), chapter-scoped state queries, and 17 FastMCP.call_tool() tests**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-07T20:51:53Z
- **Completed:** 2026-03-07T20:57:03Z
- **Tasks:** 1 (TDD: test commit + impl commit)
- **Files modified:** 3

## Accomplishments

- Delivered all 8 character domain tools: get_character, list_characters, upsert_character, get_character_injuries, get_character_beliefs, get_character_knowledge, log_character_knowledge, get_character_location
- Established the `register(mcp: FastMCP) -> None` domain module pattern used by all subsequent phases (relationships, chapters, world, plot, etc.)
- Complete test coverage with 17 tests using FastMCP.call_tool() interface, verifying real SQL against real schema with seeded data
- Error contract enforced: NotFoundResponse for missing records, ValidationFailure for DB errors, zero print() calls

## Task Commits

Each task was committed atomically:

1. **TDD RED - Test file:** `8c3954b` (test: add failing tests for character domain tools)
2. **TDD GREEN - Implementation:** `43b3c80` (feat: implement character domain MCP tools module)

## Files Created/Modified

- `src/novel/tools/characters.py` — 8 character tools via register(mcp: FastMCP) pattern; 350 lines
- `tests/test_characters.py` — 17 async tests via FastMCP.call_tool() covering all tools and edge cases
- `pyproject.toml` — Added pytest-asyncio dev dependency; set asyncio_mode=auto

## Decisions Made

- Used `cursor.lastrowid` (not `conn.lastrowid`) for aiosqlite INSERT — Connection object doesn't expose lastrowid, only the cursor from `await conn.execute()` does
- Test fixtures using chapter-FK tables (character_knowledge, character_locations, injury_states) must use only chapter IDs that exist in the minimal seed (1, 2, 3) — FK enforcement is active in test DB
- Rewrote module docstring to avoid literal `print(` text that would trigger the no-print test as a false positive
- pytest-asyncio set to `auto` mode so async test functions are detected without per-test `@pytest.mark.asyncio` decorator

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Installed missing pytest-asyncio dependency**
- **Found during:** Task 1 (TDD RED phase — running tests)
- **Issue:** `pytest-asyncio` not installed; async tests couldn't run
- **Fix:** `uv add --dev pytest-asyncio`; set `asyncio_mode = "auto"` in pyproject.toml
- **Files modified:** pyproject.toml
- **Verification:** 17 async tests collected and executed
- **Committed in:** 8c3954b (test commit)

**2. [Rule 1 - Bug] Fixed aiosqlite lastrowid access**
- **Found during:** Task 1 (TDD GREEN phase — upsert_character test failing)
- **Issue:** `conn.lastrowid` raises AttributeError — `aiosqlite.Connection` doesn't expose lastrowid; only the cursor from `await conn.execute()` does
- **Fix:** Changed `await conn.execute(INSERT...)` to `cursor = await conn.execute(INSERT...)` and used `cursor.lastrowid`
- **Files modified:** src/novel/tools/characters.py
- **Verification:** upsert_character create/update tests both pass
- **Committed in:** 43b3c80 (feat commit)

**3. [Rule 1 - Bug] Fixed test FK constraint violations**
- **Found during:** Task 1 (TDD GREEN phase — chapter scoping tests failing)
- **Issue:** Test fixtures inserted into character_knowledge/character_locations using chapter_id=5 and chapter_id=10, which don't exist in the minimal seed (only chapters 1, 2, 3 seeded); FK enforcement was active causing IntegrityError
- **Fix:** Updated test fixtures to use chapter IDs 1 and 3 (both seeded); adjusted scoping queries accordingly
- **Files modified:** tests/test_characters.py
- **Verification:** All 17 tests pass; all 88 project tests pass
- **Committed in:** 43b3c80 (feat commit)

---

**Total deviations:** 3 auto-fixed (1 blocking dependency, 2 bugs)
**Impact on plan:** All auto-fixes were necessary for correct operation. No scope creep.

## Issues Encountered

None beyond the auto-fixed deviations above.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- Character tools complete; Plan 02 (relationships tools) and Plan 03 (server wiring) can proceed
- `register(mcp)` pattern established — all future domain tool phases follow identical structure
- Test infrastructure established: pytest-asyncio, FastMCP.call_tool() pattern, seeded DB fixture
- All 88 project tests passing

---
*Phase: 03-mcp-server-core-characters-relationships*
*Completed: 2026-03-07*
