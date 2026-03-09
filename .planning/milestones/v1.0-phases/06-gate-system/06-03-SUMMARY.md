---
phase: 06-gate-system
plan: "03"
subsystem: cli
tags: [gate, cli, typer, mcp, sqlite, pytest, seed]

# Dependency graph
requires:
  - phase: 06-gate-system/06-01
    provides: GATE_QUERIES dict (34 SQL queries), GATE_ITEM_META dict, gate MCP tools register()
  - phase: 06-gate-system/06-02
    provides: gate_ready seed profile, check_gate() helper, gate tools wired into MCP server
  - phase: 01-project-foundation-database
    provides: novel.db.connection.get_connection() sync context manager
provides:
  - novel gate CLI subcommand group (check, status, certify) in novel.gate.cli
  - tests/test_gate.py with 8 MCP in-memory tests using gate_ready seed
  - gate_ready seed corrected to satisfy all 34 GATE_QUERIES SQL checks
affects:
  - 10-cli-completion-integration-testing

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Gate CLI uses sync sqlite3 via novel.db.connection.get_connection() — same pattern as db CLI, never novel.mcp.db"
    - "novel gate check iterates GATE_QUERIES and upserts into gate_checklist_items using ON CONFLICT(gate_id, item_key) DO UPDATE"
    - "test_gate.py follows established per-test MCP session pattern from test_plot.py"

key-files:
  created:
    - src/novel/gate/__init__.py
    - src/novel/gate/cli.py
    - tests/test_gate.py
  modified:
    - src/novel/cli.py
    - src/novel/db/seed.py

key-decisions:
  - "gate_ready seed had 3 missing data items that were auto-fixed: chapter 2 pacing_beats, Ithrel Cass character_arc, chapter 3 plot_thread coverage"
  - "test_get_gate_checklist_returns_items asserts len==35 (34 GATE_ITEM_META + 1 min_characters from minimal seed) not 33 as plan prose stated"
  - "test_run_gate_audit_returns_expected_items asserts total_items==35 (all gate_checklist_items rows) not 34 as plan prose stated"
  - "certify test must explicitly set min_characters to passing (not part of GATE_QUERIES, audit does not reset it) before certify call"

patterns-established:
  - "novel gate CLI pattern: sync sqlite3 via get_connection(), share SQL from GATE_QUERIES/GATE_ITEM_META in novel.tools.gate"
  - "gate_ready seed must satisfy ALL 34 GATE_QUERIES SQL checks — verified by test_run_gate_audit_gate_ready_all_pass"

requirements-completed:
  - CLSG-03
  - CLSG-04
  - CLSG-05
  - GATE-01
  - GATE-02
  - GATE-03
  - GATE-04
  - GATE-05
  - GATE-06

# Metrics
duration: 12min
completed: 2026-03-07
---

# Phase 06 Plan 03: Gate CLI and MCP Tests Summary

**novel gate CLI (check/status/certify) using sync sqlite3, 8 MCP in-memory tests confirming full audit-certify workflow on gate_ready seed**

## Performance

- **Duration:** ~12 min
- **Started:** 2026-03-07T22:57:08Z
- **Completed:** 2026-03-07T23:09:00Z
- **Tasks:** 2
- **Files modified:** 5 (3 created, 2 modified)

## Accomplishments

- Created `src/novel/gate/` CLI package with `check`, `status`, and `certify` subcommands — `novel gate check` runs all 34 gate SQL queries, upserts results, and displays formatted gap report
- Wired `gate_cli.app` into `src/novel/cli.py` root as `novel gate` subcommand group
- Created `tests/test_gate.py` with 8 MCP in-memory tests covering all 5 gate tools using `gate_ready` seed — all pass including `test_certify_gate_passes_after_full_audit`
- Auto-fixed 3 missing data items in the gate_ready seed that were causing gate SQL queries to fail (see Deviations)

## Task Commits

1. **Task 1: Create novel/gate/ CLI package with check, status, certify commands** - `36c7921` (feat)
2. **Task 2: Write MCP in-memory tests for all 5 gate tools** - `54bbe57` (feat)

**Plan metadata:** (final docs commit follows)

## Files Created/Modified

- `src/novel/gate/__init__.py` — Package marker for novel.gate module
- `src/novel/gate/cli.py` — Typer app with check/status/certify commands using sync sqlite3 via get_connection(); imports GATE_QUERIES and GATE_ITEM_META from novel.tools.gate to share SQL logic with MCP layer
- `src/novel/cli.py` — Added `from novel.gate import cli as gate_cli` import and `app.add_typer(gate_cli.app, name="gate")` registration
- `tests/test_gate.py` — 8 async MCP tests: get_gate_status (1), get_gate_checklist (1), run_gate_audit (2), update_checklist_item (2), certify_gate (2); session-scoped DB fixture with gate_ready seed
- `src/novel/db/seed.py` — Fixed _load_gate_ready: added chapter 2 pacing_beats, Ithrel Cass character_arc, chapter 3 chapter_plot_threads (auto-fix Rule 1)

## Decisions Made

- **Test item counts use actual values**: The plan prose said 33 checklist items but GATE_ITEM_META has 34, and minimal seed adds 1 more (`min_characters`) for a total of 35 rows in gate_checklist_items. Tests assert the correct value (35) not plan's stated value.
- **certify test handles min_characters separately**: The `min_characters` row is not a GATE_QUERIES item so run_gate_audit does not update it. The certify test explicitly sets it to `is_passing=True` before calling certify to ensure all 35 rows pass.
- **gate check uses total from len(GATE_QUERIES)**: The CLI `check` command reports totals based on `len(GATE_QUERIES)` (34) rather than the hardcoded 33 in the plan, staying consistent with the actual implementation.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed gate_ready seed: chapter 2 missing pacing_beats**
- **Found during:** Task 2 (running tests — test_run_gate_audit_gate_ready_all_pass failed)
- **Issue:** `_load_gate_ready()` comment said "ch1+ch2 already in minimal" but minimal only inserted pacing_beats for chapter 1, not chapter 2. The `pacing_beats` gate SQL query was returning missing_count=1.
- **Fix:** Added `INSERT OR IGNORE INTO pacing_beats (chapter_id, beat_type, description) VALUES (2, 'rising-action', '...')` to `_load_gate_ready()`
- **Files modified:** `src/novel/db/seed.py`
- **Verification:** `pacing_beats` gate query returns 0 after fix; 147 total tests pass
- **Committed in:** `54bbe57` (Task 2 commit)

**2. [Rule 1 - Bug] Fixed gate_ready seed: Ithrel Cass (char_id=3) missing character_arc**
- **Found during:** Task 2 (running tests — test_run_gate_audit_gate_ready_all_pass failed)
- **Issue:** Chapter 3 has pov_character_id=3 (Ithrel Cass/mentor) but `_load_gate_ready()` only added a character_arc for char_id=1 (Aeryn/protagonist). The `arcs_pov` gate SQL query was returning missing_count=1.
- **Fix:** Added `INSERT OR IGNORE INTO character_arcs (character_id=3, ...)` with full arc data for Ithrel Cass
- **Files modified:** `src/novel/db/seed.py`
- **Verification:** `arcs_pov` gate query returns 0 after fix
- **Committed in:** `54bbe57` (Task 2 commit)

**3. [Rule 1 - Bug] Fixed gate_ready seed: chapter 3 missing chapter_plot_threads entry**
- **Found during:** Task 2 (running tests — test_run_gate_audit_gate_ready_all_pass failed)
- **Issue:** `_load_minimal()` only links chapters 1 and 2 to plot thread 1. Chapter 3 had no chapter_plot_threads entry, causing `plot_chapter_coverage` gate SQL to return missing_count=1.
- **Fix:** Added `INSERT OR IGNORE INTO chapter_plot_threads (chapter_id=3, plot_thread_id=1, thread_role='converge')` to `_load_gate_ready()`
- **Files modified:** `src/novel/db/seed.py`
- **Verification:** `plot_chapter_coverage` gate query returns 0 after fix
- **Committed in:** `54bbe57` (Task 2 commit)

**4. [Rule 1 - Bug] Adjusted test assertions for correct item counts (35 not 33)**
- **Found during:** Task 2 (writing tests — plan prose said 33 items but implementation has 35)
- **Issue:** Plan's test code asserted `len(items) == 33` and `total_items == 33` but actual gate_checklist_items has 35 rows (34 GATE_ITEM_META + 1 min_characters from minimal seed)
- **Fix:** Tests written with correct counts (35); test for run_gate_audit also allows for min_characters handling
- **Files modified:** `tests/test_gate.py`
- **Verification:** All 8 tests pass
- **Committed in:** `54bbe57` (Task 2 commit)

---

**Total deviations:** 4 auto-fixed (all Rule 1 — seed data gaps and incorrect plan item counts)
**Impact on plan:** All auto-fixes necessary for correctness. The gate_ready seed must actually satisfy all 34 gate SQL queries for the test assertions to be meaningful. The count corrections maintain test integrity.

## Issues Encountered

None beyond the seed data gaps documented above.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 6 (Gate System) is fully complete: 34 SQL queries (06-01) + check_gate() helper + gate_ready seed (06-02) + gate CLI + MCP tests (06-03)
- `novel gate check` / `novel gate status` / `novel gate certify` are ready for user use
- gate_ready seed now correctly satisfies all 34 gate SQL checks — ready for Phase 7 integration tests
- All 147 tests passing (no regressions in characters, relationships, chapters, scenes, world, magic, plot, arcs domains)

## Self-Check: PASSED

All created files exist and all task commits verified:
- `src/novel/gate/__init__.py` — FOUND
- `src/novel/gate/cli.py` — FOUND
- `tests/test_gate.py` — FOUND
- `.planning/phases/06-gate-system/06-03-SUMMARY.md` — FOUND
- Commit `36c7921` (Task 1) — FOUND
- Commit `54bbe57` (Task 2) — FOUND

---
*Phase: 06-gate-system*
*Completed: 2026-03-07*
