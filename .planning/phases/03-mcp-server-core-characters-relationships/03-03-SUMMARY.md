---
phase: 03-mcp-server-core-characters-relationships
plan: "03"
subsystem: testing
tags: [mcp, fastmcp, pytest-asyncio, anyio, sqlite, in-memory-transport]

# Dependency graph
requires:
  - phase: 03-01
    provides: FastMCP server scaffold and character tools module
  - phase: 03-02
    provides: Relationship tools module with register(mcp) pattern

provides:
  - FastMCP server with all 14 tools registered (8 character + 6 relationship)
  - In-memory MCP client test suite verifying full protocol path
  - tests/conftest.py with session-scoped DB fixture and mcp_session pattern
  - 21 passing tests covering all 14 tools end-to-end through MCP protocol

affects:
  - Phase 4 (chapters/scenes/world tools) — same register(mcp) pattern
  - Phase 10 (integration testing) — test infrastructure pattern established

# Tech tracking
tech-stack:
  added: [pytest-asyncio>=1.3.0, mcp.shared.memory.create_connected_server_and_client_session]
  patterns:
    - in-memory MCP transport for tool tests (no subprocess, no stdio)
    - Per-test MCP session entry to avoid anyio cancel scope teardown issues
    - Session-scoped SQLite DB fixture with migrations + minimal seed
    - FastMCP list returns as multiple content blocks (one per item)

key-files:
  created:
    - tests/conftest.py
    - tests/test_characters.py
    - tests/test_relationships.py
  modified:
    - src/novel/mcp/server.py

key-decisions:
  - "MCP session entered per-test (not per-fixture) to avoid anyio cancel scope teardown error with pytest-asyncio"
  - "FastMCP returns list[T] as N separate content blocks, not a JSON array in content[0] — tests iterate result.content"
  - "Seed relationship data uses (1,3) mentor pair, not (1,2) as plan context stated — plan corrected to actual seed"

patterns-established:
  - "in-memory MCP transport: create_connected_server_and_client_session(mcp) entered within each test coroutine"
  - "List tool tests: [json.loads(c.text) for c in result.content] collects all content blocks"
  - "Not-found tests: assert not result.isError and 'not_found_message' in json.loads(result.content[0].text)"

requirements-completed:
  - ERRC-01
  - ERRC-02
  - ERRC-03
  - ERRC-04
  - CHAR-01
  - CHAR-02
  - CHAR-03
  - CHAR-04
  - CHAR-05
  - CHAR-06
  - CHAR-07
  - REL-01
  - REL-02
  - REL-03
  - REL-04
  - REL-05
  - REL-06

# Metrics
duration: 15min
completed: 2026-03-07
---

# Phase 03 Plan 03: Wire Server and MCP In-Memory Tests Summary

**FastMCP server wired with 14 tools and verified end-to-end via in-memory MCP client tests — 21 tests, 0 failures, using create_connected_server_and_client_session**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-03-07T21:04:30Z
- **Completed:** 2026-03-07T21:20:00Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Added `characters.register(mcp)` and `relationships.register(mcp)` to server.py — 14 tools now callable via MCP protocol
- Created `tests/conftest.py` with session-scoped temp DB (migrations + minimal seed) and `mcp_session` fixture pattern
- Wrote 13 character tool tests and 8 relationship tool tests using `create_connected_server_and_client_session` — all 21 pass
- Verified error contract: not-found responses have `not_found_message` key and `result.isError = False`

## Task Commits

Each task was committed atomically:

1. **Task 1: Wire server + install pytest-asyncio + build conftest** - `eb393bc` (feat)
2. **Task 2: Write MCP tool tests for characters and relationships** - `7950903` (feat)

**Plan metadata:** (docs commit — see below)

## Files Created/Modified

- `src/novel/mcp/server.py` - Added characters/relationships imports and register() calls; 14 tools now wired
- `tests/conftest.py` - Session-scoped DB fixture + mcp_session async fixture using in-memory MCP transport
- `tests/test_characters.py` - 13 in-memory MCP tests for all 8 character tools (226 lines)
- `tests/test_relationships.py` - 8 in-memory MCP tests for all 6 relationship tools (188 lines)

## Decisions Made

- **Per-test MCP session entry:** `create_connected_server_and_client_session` is entered within each test coroutine rather than as a fixture. pytest-asyncio runs fixture teardown in a separate asyncio Runner, which breaks anyio cancel scopes. Entering the context manager inline avoids the "Attempted to exit cancel scope in a different task" RuntimeError.
- **List content iteration:** FastMCP serializes `list[Model]` returns as N separate TextContent blocks, one per item. Tests use `[json.loads(c.text) for c in result.content]` — not `json.loads(result.content[0].text)` which the plan's template incorrectly assumed.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed MCP session fixture teardown incompatibility with anyio**
- **Found during:** Task 2 (writing MCP tool tests)
- **Issue:** `@pytest_asyncio.fixture async def mcp_session` using `create_connected_server_and_client_session` raised `RuntimeError: Attempted to exit cancel scope in a different task than it was entered in` on every test teardown. The MCP's anyio TaskGroup cancel scope is entered in the fixture, but pytest-asyncio runs teardown in a new asyncio Runner (different task context), violating anyio's task invariant.
- **Fix:** Removed the `mcp_session` fixture and instead enter `create_connected_server_and_client_session` within each test function via a `_call_tool()` helper. Each test owns the full context manager lifecycle.
- **Files modified:** tests/test_characters.py, tests/test_relationships.py
- **Verification:** All 21 tests pass with 0 teardown errors
- **Committed in:** 7950903 (Task 2 commit)

**2. [Rule 1 - Bug] Fixed incorrect assumption about list content format**
- **Found during:** Task 2 (test_list_characters failing)
- **Issue:** Plan's test template used `json.loads(result.content[0].text)` expecting the entire list as JSON in the first content block. FastMCP actually returns each list item as a separate TextContent block.
- **Fix:** Changed all list-returning tool tests to use `[json.loads(c.text) for c in result.content]`
- **Files modified:** tests/test_characters.py, tests/test_relationships.py
- **Verification:** list_characters, list_relationships, and all `*_returns_list` tests pass
- **Committed in:** 7950903 (Task 2 commit)

**3. [Rule 1 - Bug] Fixed incorrect seed relationship pair in plan context**
- **Found during:** Task 2 (test_get_relationship_found failing)
- **Issue:** Plan's `<context>` section stated "(character_a_id=1, character_b_id=2): rivals relationship" but the actual seed has (1,3) mentor-student, (1,4) friendship, (1,5) rivalry — no (1,2) relationship exists.
- **Fix:** Updated `test_get_relationship_found` and `test_get_relationship_reversed_order` to use character pair (1,3).
- **Files modified:** tests/test_relationships.py
- **Verification:** Both relationship lookup tests pass
- **Committed in:** 7950903 (Task 2 commit)

---

**Total deviations:** 3 auto-fixed (3 Rule 1 bugs — incorrect assumptions in plan's test template)
**Impact on plan:** All auto-fixes necessary for tests to pass. No scope creep. Test coverage and error contract requirements fully met.

## Issues Encountered

- pytest-asyncio `asyncio_mode = "auto"` was already set in pyproject.toml from a previous run, so Step 2 of Task 1 was a no-op (verified and skipped).
- `pytest-asyncio` was already installed at version 1.3.0; no additional install needed.

## Next Phase Readiness

- Phase 3 complete: 14 MCP tools wired and tested end-to-end through the MCP protocol
- Phase 4 (Chapters, Scenes & World tools) can use the same `register(mcp)` pattern
- Test infrastructure pattern established: session-scoped DB + per-test MCP session

---
*Phase: 03-mcp-server-core-characters-relationships*
*Completed: 2026-03-07*

## Self-Check: PASSED

- tests/conftest.py: FOUND
- tests/test_characters.py: FOUND
- tests/test_relationships.py: FOUND
- 03-03-SUMMARY.md: FOUND
- Commit eb393bc (Task 1): FOUND
- Commit 7950903 (Task 2): FOUND
