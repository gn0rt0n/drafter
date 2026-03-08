---
phase: 09-names-voice-publishing
plan: "01"
subsystem: database
tags: [sqlite, aiosqlite, mcp, fastmcp, name-registry, pydantic]

# Dependency graph
requires:
  - phase: 08-canon-knowledge-foreshadowing
    provides: established register(mcp) pattern, get_connection() async context manager
  - phase: 02-pydantic-models-seed-data
    provides: NameRegistryEntry model in models/magic.py, NotFoundResponse, ValidationFailure in models/shared.py
  - phase: 01-project-foundation-database
    provides: migration 021 with name_registry table (name UNIQUE constraint)
provides:
  - 4 gate-free name domain MCP tools: check_name, register_name, get_name_registry, generate_name_suggestions
  - NameSuggestionsResult inline Pydantic model in names.py
  - names.register(mcp) wired into server.py
affects: [09-02-voice, 09-03-publishing, 10-cli-integration-testing]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Gate-free tool module: name tools declared without check_gate() — locked domain exception"
    - "aiosqlite.IntegrityError catch for UNIQUE violations instead of pre-flight SELECT"
    - "Two-pass SELECTs (no JOIN) for generate_name_suggestions: name_registry then cultures"
    - "Inline result model (NameSuggestionsResult) in tools module when result type is domain-local"

key-files:
  created:
    - src/novel/tools/names.py
    - tests/test_names.py
  modified:
    - src/novel/mcp/server.py

key-decisions:
  - "NameSuggestionsResult defined inline in names.py (not in models/) — result type is tool-local, no cross-domain use"
  - "register_name wraps INSERT in try/except aiosqlite.IntegrityError — avoids race-condition window of pre-flight SELECT"
  - "generate_name_suggestions uses two separate SELECTs not a JOIN — cultures row absence must yield None not 0-row mismatch"
  - "No check_gate() in names.py — gate-free by locked design decision from 09-CONTEXT.md"
  - "Test seed uses minimal profile (not gate_ready) — name tools are gate-free so gate certification not required"

patterns-established:
  - "Gate-free domain: when a tool domain must work pre-gate (worldbuilding), omit check_gate() entirely"

requirements-completed: [NAME-01, NAME-02, NAME-03, NAME-04]

# Metrics
duration: 3min
completed: 2026-03-08
---

# Phase 9 Plan 01: Names Domain Summary

**4 gate-free MCP name tools via aiosqlite with case-insensitive UNIQUE-guarded name_registry operations**

## Performance

- **Duration:** ~3 min
- **Started:** 2026-03-08T02:39:58Z
- **Completed:** 2026-03-08T02:43:02Z
- **Tasks:** 1 (TDD: test commit + impl commit)
- **Files modified:** 3

## Accomplishments
- `check_name` performs case-insensitive exact match via `LOWER(name) = LOWER(?)` and returns `NotFoundResponse` with "safe to use" wording when absent
- `register_name` uses try/except aiosqlite.IntegrityError for UNIQUE violation detection; returns `ValidationFailure` on duplicate, `NameRegistryEntry` (with lastrowid SELECT-back) on success
- `get_name_registry` builds conditional WHERE clause for optional `entity_type` and `culture_id` filters, ordered by name ASC
- `generate_name_suggestions` issues two independent SELECTs (name_registry + cultures.naming_conventions) and returns `NameSuggestionsResult` inline model
- All 4 tools explicitly gate-free (no `check_gate()` import or call) — worldbuilding operations available pre-certification
- 10 tests passing; no regressions in full 202-test suite

## Task Commits

Each task was committed atomically:

1. **TDD RED: Failing tests for 4 name tools** - `2a65f23` (test)
2. **TDD GREEN: names.py implementation + server.py wiring** - `d4e5080` (feat)

**Plan metadata:** (docs commit below)

_Note: TDD tasks have two commits (test RED → feat GREEN)_

## Files Created/Modified
- `src/novel/tools/names.py` - 4 gate-free name domain MCP tools + NameSuggestionsResult model
- `src/novel/mcp/server.py` - Added `names` import and `names.register(mcp)` for Phase 9
- `tests/test_names.py` - 10 in-memory MCP protocol tests (minimal seed, no gate certification)

## Decisions Made
- `NameSuggestionsResult` is defined inline in `names.py` rather than in `models/` — this result type is specific to the generate_name_suggestions tool and has no cross-domain consumers
- `register_name` catches `aiosqlite.IntegrityError` rather than pre-flight SELECT-checking for existence — avoids TOCTOU race condition window; matches intent of the plan spec
- `generate_name_suggestions` uses two separate SELECTs (not a JOIN) — the plan spec required this pattern so absent culture rows yield `None` linguistic context rather than a missing-row JOIN mismatch
- Test seed profile is `minimal` (not `gate_ready`) — name tools are gate-free, so gate certification state is irrelevant to their operation

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None — no external service configuration required.

## Next Phase Readiness
- Names domain complete and wired into server.py
- Ready for 09-02: Voice domain (`src/novel/tools/voice.py`, 5 gated tools)
- names.register(mcp) already in server.py; voice.register(mcp) and publishing.register(mcp) to be added in 09-03

---
*Phase: 09-names-voice-publishing*
*Completed: 2026-03-08*
