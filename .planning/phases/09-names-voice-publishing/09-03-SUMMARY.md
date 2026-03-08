---
phase: 09-names-voice-publishing
plan: "03"
subsystem: mcp-tools
tags: [python, fastmcp, sqlite, aiosqlite, publishing, voice, names, mcp-tools, gate-system, pytest]

# Dependency graph
requires:
  - phase: 09-01
    provides: names.py with 4 gate-free MCP tools
  - phase: 09-02
    provides: voice.py with 5 gated MCP tools
  - phase: 06-gate-system
    provides: check_gate() helper, architecture_gate table, gate_ready seed
  - phase: 08-canon-knowledge-foreshadowing
    provides: server.py with Phases 3-8 wired, test patterns (test_foreshadowing.py template)
provides:
  - publishing.py with 5 gated MCP tools (get_publishing_assets, upsert_publishing_asset, get_submissions, log_submission, update_submission)
  - server.py wired for all 14 Phase 9 tools (names + voice + publishing)
  - tests/test_names.py covering all 4 name tools (10 tests, gate-free)
  - tests/test_voice.py covering all 5 voice tools (8 tests, certified_gate fixture)
  - tests/test_publishing.py covering all 5 publishing tools (9 tests, certified_gate fixture)
affects: [phase-10-cli, integration-testing]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Two-branch upsert on PK: None-id INSERT+lastrowid, provided-id ON CONFLICT(id) DO UPDATE"
    - "SELECT-back after UPDATE to detect missing rows (update_submission)"
    - "Append-only INSERT for log_submission — no ON CONFLICT"
    - "Gate check pattern: gate = await check_gate(conn); if gate is not None: return gate"
    - "Session-scoped sqlite3 seed fixtures for domain data not in gate_ready seed"
    - "INSERT OR IGNORE for gate_ready data already present (voice_profiles)"

key-files:
  created:
    - src/novel/tools/publishing.py
    - tests/test_voice.py
    - tests/test_publishing.py
  modified:
    - src/novel/mcp/server.py

key-decisions:
  - "upsert_publishing_asset ON CONFLICT targets id (PK) not a named UNIQUE — publishing_assets has no UNIQUE beyond PK"
  - "update_submission SELECT-back after UPDATE required — SQLite does not error on UPDATE of missing row"
  - "log_submission is append-only with no ON CONFLICT — each submission event is a discrete record"
  - "gate_ready seed already has voice_profiles for all 5 characters (1-5) — _insert_voice_seed inserts a 6th character (Tessan Vel) to test the CREATE branch of upsert_voice_profile"
  - "INSERT OR IGNORE used in test_voice.py voice_profiles seed to handle gate_ready seed already populating character_id=1"

patterns-established:
  - "Publishing tools follow same gate-check-first pattern as voice/canon/foreshadowing tools"
  - "Test seed fixtures check gate_ready coverage before inserting duplicate data"

requirements-completed: [PUBL-01, PUBL-02, PUBL-03, PUBL-04, PUBL-05]

# Metrics
duration: 6min
completed: 2026-03-08
---

# Phase 9 Plan 03: Publishing Tools, Server Wiring, and Phase 9 Tests Summary

**5 gated publishing MCP tools (publishing_assets + submission_tracker), full Phase 9 server wiring, and 27 in-memory FastMCP tests across all 14 Phase 9 tools**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-08T02:44:59Z
- **Completed:** 2026-03-08T02:50:22Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Implemented `publishing.py` with 5 gated tools: get_publishing_assets (asset_type filter), upsert_publishing_asset (two-branch PK upsert), get_submissions (status filter), log_submission (append-only), update_submission (dynamic SET + SELECT-back for NotFoundResponse)
- Wired `server.py` to register all 14 Phase 9 tools (names + voice + publishing) completing Phase 9 server integration
- 27 in-memory FastMCP tests across all 14 Phase 9 tools: 10 name tests, 8 voice tests, 9 publishing tests — all 219 total suite tests passing

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement publishing.py with 5 gated tools** - `653b16e` (feat)
2. **Task 2: Wire server.py and write MCP tests for all 14 Phase 9 tools** - `6deb1ea` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified

- `src/novel/tools/publishing.py` - 5 gated publishing MCP tools registered via register(mcp)
- `src/novel/mcp/server.py` - Added voice.register(mcp) and publishing.register(mcp); updated docstring to Phase 9 complete
- `tests/test_voice.py` - 8 tests covering all 5 voice tools with certified_gate and seed fixtures
- `tests/test_publishing.py` - 9 tests covering all 5 publishing tools with certified_gate and seed fixtures
- `tests/test_names.py` - Pre-existing 10 tests confirmed passing (already written in 09-01)

## Decisions Made

- `upsert_publishing_asset` uses `ON CONFLICT(id)` (PK target) not a named UNIQUE — publishing_assets has no UNIQUE columns beyond PK, consistent with Phase 05 upsert_chekov pattern
- `update_submission` must SELECT-back after UPDATE — SQLite does not raise on UPDATE of non-existent row; consistent with Phase 08-01 resolve_continuity_issue pattern
- `log_submission` is append-only (no ON CONFLICT) — submission events are discrete audit records, consistent with log_ naming convention across the codebase
- gate_ready seed already inserts voice_profiles for all 5 characters (1-5); `_insert_voice_seed` inserts a 6th character "Tessan Vel" to enable testing the None-id CREATE branch of upsert_voice_profile

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] gate_ready seed already has voice_profiles for all 5 characters**
- **Found during:** Task 2 (writing test_voice.py)
- **Issue:** Plan said gate_ready seed does NOT populate voice_profiles, but seed actually inserts profiles for character_ids 1-5. INSERT INTO voice_profiles for character_id=1 failed with UNIQUE constraint error.
- **Fix:** Changed seed fixture to INSERT a new character (Tessan Vel, id=6) for the CREATE branch test; used INSERT OR IGNORE for the existing character_id=1 seed line; updated test_upsert_voice_profile_create to dynamically fetch the new character's id.
- **Files modified:** tests/test_voice.py
- **Verification:** All 8 voice tests pass
- **Committed in:** 6deb1ea (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - incorrect plan assumption about seed data)
**Impact on plan:** Required a small test fixture adjustment. No scope creep. All must_haves met.

## Issues Encountered

- `characters` table has no `status` column (plan context was wrong) — auto-fixed by using correct columns `(name, role)` for the INSERT.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 9 fully complete: all 14 Phase 9 tools implemented and tested
- server.py now registers 80+ tools across all 14 domains
- Phase 10 (CLI completion and integration testing) can proceed immediately

## Self-Check: PASSED

- FOUND: src/novel/tools/publishing.py
- FOUND: src/novel/mcp/server.py (with names.register, voice.register, publishing.register)
- FOUND: tests/test_voice.py
- FOUND: tests/test_publishing.py
- FOUND: commit 653b16e (publishing.py implementation)
- FOUND: commit 6deb1ea (server wiring + tests)

---
*Phase: 09-names-voice-publishing*
*Completed: 2026-03-08*
