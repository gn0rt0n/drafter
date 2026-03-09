---
phase: 11-update-schema-cli-mcp-and-planning-docs-to-support-7-point-structure-and-3-act-7-point-integration
plan: "02"
subsystem: database
tags: [gate-system, seed-data, 7-point-structure, sqlite, story_structure, arc_seven_point_beats]

# Dependency graph
requires:
  - phase: 11-01
    provides: story_structure and arc_seven_point_beats tables (migration 022)
provides:
  - 36-item gate with struct_story_beats and arcs_seven_point_beats enforcement
  - gate_ready seed with 1 story_structure row + 14 arc_seven_point_beats rows satisfying new gate checks
affects:
  - Any phase testing gate certification (all gate checks must pass)
  - Integration tests that load gate_ready seed profile

# Tech tracking
tech-stack:
  added: []
  patterns:
    - INSERT OR IGNORE for idempotent gate-ready seed rows (carried forward from existing pattern)
    - GATE_ITEM_META / GATE_QUERIES dual-dict with assert set check at import time (maintained)

key-files:
  created: []
  modified:
    - src/novel/tools/gate.py
    - src/novel/db/seed.py

key-decisions:
  - "Phase 11-02: gate.py goes from 34 to 36 items — struct_story_beats (structure category) and arcs_seven_point_beats (plot category) added to both GATE_ITEM_META and GATE_QUERIES simultaneously to keep assert passing"
  - "Phase 11-02: seed uses chapter_id=1 for all 14 arc_seven_point_beats rows — seed needs valid FK values, not narrative accuracy"
  - "Phase 11-02: story_structure seed row maps all 7 structural beats to existing seed chapters (1, 2, 3) plus all 3 act-level FKs — satisfies gate query which checks all 7 beat FKs are non-null"

patterns-established:
  - "Gate extension pattern: always add new keys to BOTH GATE_ITEM_META and GATE_QUERIES in the same edit — the assert fires at import time and will catch any mismatch"

requirements-completed: [STRUCT-03, STRUCT-04]

# Metrics
duration: 4min
completed: 2026-03-09
---

# Phase 11 Plan 02: Gate Extension for 7-Point Structure Summary

**36-item gate enforcing story_structure beat completeness and POV arc 7-point beat coverage, with gate_ready seed satisfying both new checks**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-09T14:29:42Z
- **Completed:** 2026-03-09T14:34:00Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Extended GATE_ITEM_META and GATE_QUERIES from 34 to 36 items; import-time assert still passes
- Added struct_story_beats gate check: every book must have a story_structure row with all 7 beat chapter FKs populated
- Added arcs_seven_point_beats gate check: every POV character arc must have 7 arc_seven_point_beats rows with non-null chapter_id
- Extended gate_ready seed with 1 story_structure row for book_id=1 and 14 arc_seven_point_beats rows (7 x 2 POV arcs)

## Task Commits

Each task was committed atomically:

1. **Task 1: Extend gate.py with 2 new gate items** - `3b0cece` (feat)
2. **Task 2: Add story_structure and arc_seven_point_beats rows to gate_ready seed** - `de1ad91` (feat)

**Plan metadata:** _(final docs commit — see below)_

## Files Created/Modified

- `src/novel/tools/gate.py` - Added struct_story_beats and arcs_seven_point_beats to GATE_ITEM_META and GATE_QUERIES; updated count comments from 34 to 36
- `src/novel/db/seed.py` - Added INSERT OR IGNORE into story_structure and 14-row INSERT OR IGNORE loop for arc_seven_point_beats in _load_gate_ready

## Decisions Made

- Gate item count goes from 34 to 36 (not 35) — two new checks added in one plan per the 11-02 objective.
- struct_story_beats uses category "structure" and arcs_seven_point_beats uses category "plot" to match their semantic domains.
- Seed uses chapter_id=1 for all beat rows — narrative accuracy is irrelevant for gate-readiness; any valid FK satisfies the query.
- story_structure row maps beat columns to chapters 1, 2, 3 (repeating as needed) plus the three act-level FK columns — satisfies the gate query which only checks the 7 structural beat FKs are non-null.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None. The virtual environment needed to be activated for Python verification commands (`source .venv/bin/activate`), but this is standard project setup, not an error.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Gate now enforces 7-point story structure coverage at the architecture certification level
- gate_ready seed passes all 36 gate checks when loaded against the migrated schema
- Ready for 11-03 (MCP tools for the new tables) and subsequent gate-certification integration tests

## Self-Check: PASSED

- `src/novel/tools/gate.py` — FOUND
- `src/novel/db/seed.py` — FOUND
- `11-02-SUMMARY.md` — FOUND
- Commit `3b0cece` — FOUND (Task 1: gate.py extension)
- Commit `de1ad91` — FOUND (Task 2: seed.py extension)

---
*Phase: 11-update-schema-cli-mcp-and-planning-docs-to-support-7-point-structure-and-3-act-7-point-integration*
*Completed: 2026-03-09*
