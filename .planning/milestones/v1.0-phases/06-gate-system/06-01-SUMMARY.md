---
phase: 06-gate-system
plan: "01"
subsystem: gate
tags: [mcp, fastmcp, sqlite, gate, aiosqlite, pydantic]

# Dependency graph
requires:
  - phase: 02-pydantic-models-seed-data
    provides: ArchitectureGate and GateChecklistItem Pydantic models (gate.py), GateViolation in shared.py
  - phase: 03-mcp-server-core-characters-relationships
    provides: register(mcp) pattern, get_connection() async context manager, NotFoundResponse/ValidationFailure error contract
  - phase: 05-plot-arcs
    provides: All 5 domain areas (characters, chapters, scenes, world, plot, arcs) whose tables are queried by the 34 gate SQL checks

provides:
  - "src/novel/tools/gate.py with GateAuditReport model, GATE_QUERIES dict (34 SQL evidence queries), GATE_ITEM_META dict, and 5 MCP gate tools"
  - "get_gate_status: returns is_certified flag and blocking_item_count"
  - "get_gate_checklist: returns per-item pass/fail list from gate_checklist_items"
  - "run_gate_audit: executes all 34 SQL queries, upserts results into gate_checklist_items, returns GateAuditReport"
  - "update_checklist_item: full manual override of is_passing, missing_count, and notes"
  - "certify_gate: writes is_certified=1 when all items pass; returns ValidationFailure with error count otherwise"

affects:
  - 06-02-check-gate-helper-seed-wiring
  - 06-03-gate-cli-and-mcp-tests

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Gate tools follow established register(mcp: FastMCP) -> None pattern with local async functions"
    - "ON CONFLICT(gate_id, item_key) DO UPDATE for gate_checklist_items upsert in run_gate_audit"
    - "GATE_QUERIES dict: all 34 SQL queries return missing_count column (0=passing, positive=failing)"
    - "run_gate_audit and certify_gate are independent operations — audit does not certify, certify does not re-audit"
    - "Module-level assert ensures GATE_QUERIES and GATE_ITEM_META have identical key sets at import time"

key-files:
  created:
    - src/novel/tools/gate.py
  modified: []

key-decisions:
  - "Implemented 34 gate checklist items, not 33 — the plan's GATE_QUERIES dict and GATE_ITEM_META listing both contain 34 entries; the '33' mentioned in plan prose and assertions was a documentation error (fixed assertion to 34)"
  - "run_gate_audit stores max(missing, 0) in DB — errored queries (-1) are stored as 0 with is_passing=0 to avoid DB constraint issues"
  - "certify_gate uses 'system' as default certified_by when None provided"
  - "Module-level assert on GATE_QUERIES/GATE_ITEM_META key parity enforces consistency at import time — no silent key drift possible"

patterns-established:
  - "Gate SQL: all 34 queries return a single row with missing_count column; zero = passing"
  - "Gate SQL: relational checks ('all existing X must have Y'), not hard-coded counts"
  - "run_gate_audit is idempotent: safe to call multiple times; each call upserts all items"

requirements-completed:
  - GATE-01
  - GATE-02
  - GATE-03
  - GATE-04
  - GATE-05

# Metrics
duration: 12min
completed: 2026-03-07
---

# Phase 6 Plan 01: Gate System — Gate Tools Summary

**34-query SQL audit system in gate.py: GateAuditReport model, GATE_QUERIES/GATE_ITEM_META dicts, and 5 MCP gate tools (get_gate_status, get_gate_checklist, run_gate_audit, update_checklist_item, certify_gate)**

## Performance

- **Duration:** ~12 min
- **Started:** 2026-03-07T22:44:52Z
- **Completed:** 2026-03-07T22:56:00Z
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments

- Created `src/novel/tools/gate.py` with all 5 MCP gate tools following the established `register(mcp: FastMCP) -> None` pattern
- Authored 34 relational SQL evidence queries in `GATE_QUERIES` — each returns `missing_count` column (0=passing); queries span all architecture domains: population, structure, scenes, plot, relationships, world, pacing, voice, names, and canon
- `run_gate_audit` executes all 34 queries and upserts results via `ON CONFLICT(gate_id, item_key) DO UPDATE`, returning a typed `GateAuditReport`
- `certify_gate` reads current item states independently and refuses if any item has `is_passing=False`

## Task Commits

Each task was committed atomically:

1. **Task 1 + 2: Create gate.py with GATE_QUERIES, GATE_ITEM_META, GateAuditReport, and register()** - `00173a8` (feat)

**Plan metadata:** _(committed with this SUMMARY — see final commit below)_

## Files Created/Modified

- `/Users/gary/writing/drafter/src/novel/tools/gate.py` — GateAuditReport model, GATE_ITEM_META (34 items), GATE_QUERIES (34 SQL queries), register() with 5 gate tools

## Decisions Made

- Implemented 34 gate checklist items, not 33. The plan's GATE_QUERIES dict and GATE_ITEM_META listing both contain 34 entries. The "33" in plan prose and verification asserts was a documentation error (categories: population=4, structure=6, scenes=4, plot=6, relationships=2, world=3, pacing=2, voice=1, names=2, canon=4 → total=34).
- `run_gate_audit` stores `max(missing, 0)` in DB for errored queries to avoid any DB constraint issues; `is_passing` is still set to 0 so it shows as failing.
- Module-level `assert` enforces that GATE_QUERIES and GATE_ITEM_META have identical key sets — any drift is caught at import time with a clear error message.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Corrected item count from 33 to 34**
- **Found during:** Task 1 (GATE_QUERIES dict creation)
- **Issue:** Plan prose says 33 items throughout, but the provided GATE_QUERIES dict literal and GATE_ITEM_META key listing both enumerate 34 distinct keys (population=4, structure=6, scenes=4, plot=6, relationships=2, world=3, pacing=2, voice=1, names=2, canon=4). The must_haves truth also said `total_items=33`. The verification assert `assert len(GATE_QUERIES) == 33` would fail with the dict given in the plan.
- **Fix:** Implemented all 34 keys as shown in the plan's dict, used `_GATE_ITEM_COUNT = len(GATE_QUERIES)` (= 34) as the authoritative count, and `run_gate_audit` returns `total_items=len(items)` dynamically rather than hard-coding 33.
- **Files modified:** src/novel/tools/gate.py
- **Verification:** `uv run python -c "from novel.tools.gate import GATE_QUERIES; assert len(GATE_QUERIES) == 34"` passes
- **Committed in:** 00173a8 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 documentation error / bug in plan's count assertion)
**Impact on plan:** The fix implements the actual content the plan provided — no content was added or removed. The "33" was a stale number from an earlier PRD draft; the actual query dict in the plan contained 34 entries.

## Issues Encountered

None — module loaded cleanly, all 5 tools registered, no print() statements.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `src/novel/tools/gate.py` is ready to be wired into `server.py` (Plan 06-02)
- `gate.register(mcp)` call needed in server.py alongside other domain registrations
- `check_gate()` async helper (Plan 06-02) will live in `novel/mcp/gate.py` to avoid circular imports
- Gate-ready seed profile (Plan 06-02) must populate gate_checklist_items and add data satisfying all 34 checks

---
*Phase: 06-gate-system*
*Completed: 2026-03-07*
