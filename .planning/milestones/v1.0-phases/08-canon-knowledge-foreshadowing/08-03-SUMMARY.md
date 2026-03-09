---
phase: 08-canon-knowledge-foreshadowing
plan: "03"
subsystem: mcp-tools
tags: [fastmcp, sqlite, aiosqlite, foreshadowing, motifs, prophecy, thematic-mirrors, opposition-pairs, pytest, anyio]

requires:
  - phase: 08-01
    provides: "canon tools (7) in src/novel/tools/canon.py"
  - phase: 08-02
    provides: "knowledge tools (5) in src/novel/tools/knowledge.py"

provides:
  - "8 foreshadowing domain MCP tools in src/novel/tools/foreshadowing.py"
  - "All 20 Phase 8 tools wired into server.py (canon + knowledge + foreshadowing)"
  - "In-memory FastMCP tests for all 20 Phase 8 tools (21 test functions)"
affects:
  - phase-09-names-voice-publishing
  - phase-10-cli-completion-integration

tech-stack:
  added: []
  patterns:
    - "Foreshadowing two-branch upsert: None-id INSERT, provided-id INSERT ON CONFLICT(id) DO UPDATE"
    - "Motif occurrences append-only INSERT — historical events are immutable audit trail"
    - "Test FK compliance: use seed chapter IDs (1-3) not arbitrary chapter numbers"

key-files:
  created:
    - src/novel/tools/foreshadowing.py
    - tests/test_canon.py
    - tests/test_knowledge.py
    - tests/test_foreshadowing.py
  modified:
    - src/novel/mcp/server.py

key-decisions:
  - "log_foreshadowing is upsert (two-branch): allows payoff to be filled in later without creating a duplicate plant entry"
  - "log_motif_occurrence is append-only: each motif appearance is a discrete historical event"
  - "Test chapter IDs must match seed chapters (1-3 in gate_ready) — FK constraints enforced in test DB"

patterns-established:
  - "Phase 8 register() pattern: all three modules (canon, knowledge, foreshadowing) use register(mcp: FastMCP) -> None with local @mcp.tool() functions"
  - "Phase 8 test pattern: separate session-scoped DB fixture per test file with distinct mktemp names (canon_db, knowledge_db, foreshadowing_db)"

requirements-completed:
  - FORE-01
  - FORE-02
  - FORE-03
  - FORE-04
  - FORE-05
  - FORE-06
  - FORE-07
  - FORE-08

duration: 5min
completed: 2026-03-08
---

# Phase 8 Plan 03: Foreshadowing Tools, Server Wiring, and Phase 8 Tests Summary

**8 foreshadowing literary device tracking tools (prophecy, motifs, mirrors, opposition pairs) + all 20 Phase 8 tools wired into the MCP server + 21 in-memory FastMCP tests proving correctness**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-03-08T02:12:20Z
- **Completed:** 2026-03-08T02:16:58Z
- **Tasks:** 2
- **Files modified:** 5 (1 created tool, 3 new test files, 1 updated server)

## Accomplishments

- Created `src/novel/tools/foreshadowing.py` with 8 tools: `get_foreshadowing`, `get_prophecies`, `get_motifs`, `get_motif_occurrences`, `get_thematic_mirrors`, `get_opposition_pairs`, `log_foreshadowing` (upsert), `log_motif_occurrence` (append-only)
- Updated `src/novel/mcp/server.py` to import and register canon, knowledge, and foreshadowing modules — total MCP tool count: 85
- Wrote 21 in-memory FastMCP tests across 3 files covering all 20 Phase 8 tools; all pass

## Task Commits

1. **Task 1: Implement foreshadowing tools + wire server.py** - `b83f543` (feat)
2. **Task 2: Write in-memory FastMCP tests for all 20 Phase 8 tools** - `2855a25` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified

- `src/novel/tools/foreshadowing.py` — 8 foreshadowing domain tools (get/log for foreshadowing, prophecy, motifs, mirrors, opposition pairs)
- `src/novel/mcp/server.py` — Added Phase 8 import line and `canon.register(mcp)`, `knowledge.register(mcp)`, `foreshadowing.register(mcp)` block
- `tests/test_canon.py` — 7 tests for all canon tools using session-scoped gate_ready DB + certified_gate fixture
- `tests/test_knowledge.py` — 5 tests for all knowledge tools using session-scoped gate_ready DB + certified_gate fixture
- `tests/test_foreshadowing.py` — 9 tests for all 8 foreshadowing tools using session-scoped gate_ready DB + certified_gate fixture

## Decisions Made

- `log_foreshadowing` uses two-branch upsert (None-id INSERT; provided-id ON CONFLICT(id) DO UPDATE) — allows filling in payoff_chapter_id when the plant pays off without creating a duplicate row
- `log_motif_occurrence` is append-only INSERT — motif appearances are historical events, not updatable records
- FK-aware test values: tests use `chapter_id=3` (exists in gate_ready seed) not `chapter_id=5` (non-existent) — enforced by SQLite FK constraints in test DB

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Test chapter IDs corrected to match existing seed chapters**
- **Found during:** Task 2 (test execution)
- **Issue:** Plan spec used `chapter_id=5` and `payoff_chapter_id=5` but gate_ready seed only has chapters 1-3; SQLite FK constraint failed with "FOREIGN KEY constraint failed"
- **Fix:** Changed `chapter_id=5` to `chapter_id=3` in `test_upsert_reader_state_insert` (test_knowledge.py) and `payoff_chapter_id=5` to `payoff_chapter_id=3` in `test_log_foreshadowing_update` (test_foreshadowing.py)
- **Files modified:** tests/test_knowledge.py, tests/test_foreshadowing.py
- **Verification:** All 21 tests pass after correction
- **Committed in:** 2855a25 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - bug: plan spec referenced non-existent chapter IDs)
**Impact on plan:** Necessary correctness fix — tests verify the same behaviors as specified; only the FK-safe chapter ID changed.

## Issues Encountered

None beyond the auto-fixed FK constraint issue documented above.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- Phase 8 complete: all 20 tools (7 canon + 5 knowledge + 8 foreshadowing) implemented, wired, and tested
- 85 total MCP tools registered and verified in server
- Phase 9 (Names, Voice, Publishing — 14 tools) can proceed immediately
- No blockers

## Self-Check: PASSED

- src/novel/tools/foreshadowing.py: FOUND
- tests/test_canon.py: FOUND
- tests/test_knowledge.py: FOUND
- tests/test_foreshadowing.py: FOUND
- .planning/phases/08-canon-knowledge-foreshadowing/08-03-SUMMARY.md: FOUND
- Commit b83f543: FOUND
- Commit 2855a25: FOUND

---
*Phase: 08-canon-knowledge-foreshadowing*
*Completed: 2026-03-08*
