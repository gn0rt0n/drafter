---
phase: 08-canon-knowledge-foreshadowing
plan: "02"
subsystem: database
tags: [mcp, fastmcp, aiosqlite, reader-state, dramatic-irony, knowledge-domain]

# Dependency graph
requires:
  - phase: 08-01
    provides: canon.py tool pattern and gate integration
  - phase: 06-gate-system
    provides: check_gate() helper in novel.mcp.gate
  - phase: 02-pydantic-models-seed-data
    provides: ReaderInformationState, ReaderReveal, DramaticIronyEntry models in canon.py
provides:
  - "get_reader_state: cumulative reader knowledge snapshot up to any chapter"
  - "get_dramatic_irony_inventory: unresolved-by-default irony tracking with filters"
  - "get_reader_reveals: planned and actual reveal retrieval with optional chapter filter"
  - "upsert_reader_state: two-branch upsert by (chapter_id,domain) key or by primary key"
  - "log_dramatic_irony: append-only irony entry creation"
affects: [08-03, server-wiring, foreshadowing-domain]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Dynamic WHERE clause construction with conditions list and params list"
    - "Two-branch upsert: None-id ON CONFLICT(chapter_id, domain), provided-id ON CONFLICT(id)"
    - "Append-only INSERT for audit/log tools (no ON CONFLICT)"
    - "Cumulative semantics: WHERE chapter_id <= ? for reader state"

key-files:
  created:
    - src/novel/tools/knowledge.py
  modified: []

key-decisions:
  - "get_reader_state uses WHERE chapter_id <= ? (cumulative semantics) — gives Claude complete snapshot of reader knowledge at any story point"
  - "get_dramatic_irony_inventory returns only unresolved entries by default (include_resolved=False) — matches established pattern from CONTEXT.md"
  - "upsert_reader_state None-id branch uses ON CONFLICT(chapter_id, domain) — matches UNIQUE constraint on reader_information_states table"
  - "log_dramatic_irony is append-only (no ON CONFLICT) — irony entries are discrete events, each is a distinct record"

patterns-established:
  - "Dynamic WHERE: build conditions list + params list, join with AND, append at end"

requirements-completed: [KNOW-01, KNOW-02, KNOW-03, KNOW-04, KNOW-05]

# Metrics
duration: 2min
completed: 2026-03-08
---

# Phase 8 Plan 02: Knowledge Domain Summary

**5 knowledge domain MCP tools with cumulative reader-state semantics, two-branch upsert, and unresolved-by-default dramatic irony inventory**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-08T02:08:42Z
- **Completed:** 2026-03-08T02:10:11Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments
- Implemented all 5 knowledge domain tools in `src/novel/tools/knowledge.py` following established patterns from Phases 3-7
- `get_reader_state` uses cumulative `WHERE chapter_id <= ?` semantics — single call gives Claude full reader knowledge snapshot at any story point
- `upsert_reader_state` uses two-branch upsert: None-id branch deduplicates by UNIQUE(chapter_id, domain) constraint; provided-id branch updates specific row by PK
- `get_dramatic_irony_inventory` builds dynamic WHERE clause using conditions list pattern for clean optional filter composition
- `log_dramatic_irony` is append-only (no ON CONFLICT) — each irony entry is a discrete historical event

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement knowledge domain tools in src/novel/tools/knowledge.py** - `c650e98` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified
- `src/novel/tools/knowledge.py` - 5 knowledge domain MCP tools: get_reader_state, get_dramatic_irony_inventory, get_reader_reveals, upsert_reader_state, log_dramatic_irony

## Decisions Made
- `get_reader_state` cumulative semantics (`WHERE chapter_id <= ?`) — locked decision from CONTEXT.md, preserved exactly
- `get_dramatic_irony_inventory` unresolved-by-default — locked decision from CONTEXT.md, preserved exactly
- `upsert_reader_state` None-id branch uses `ON CONFLICT(chapter_id, domain)` matching the table's UNIQUE constraint — both branches cover the full upsert contract
- `log_dramatic_irony` is append-only — irony entries are discrete events, not updatable records (consistent with log_ naming convention across codebase)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Knowledge domain tools are complete and importable
- `knowledge.register(mcp)` ready to be wired into server.py in 08-03 alongside canon.register and foreshadowing.register
- No blockers

---
*Phase: 08-canon-knowledge-foreshadowing*
*Completed: 2026-03-08*
