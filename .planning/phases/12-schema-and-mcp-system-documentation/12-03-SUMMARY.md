---
phase: 12-schema-and-mcp-system-documentation
plan: "03"
subsystem: documentation
tags: [mcp, tools, reference, fastmcp, sqlite, gate]

# Dependency graph
requires:
  - phase: 01-11 (all implementation phases)
    provides: Python tool module source files that are the ground truth for this documentation

provides:
  - docs/mcp-tools.md — complete implementation-accurate MCP tool reference for all 103 tools

affects:
  - any future agent developers or system administrators using the MCP server
  - plugin developers building on the MCP interface

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Documentation derived directly from Python source (@mcp.tool() decorated functions) — REQUIREMENTS.md explicitly excluded as source of truth due to known drift"
    - "Error contract documented at the top level before the per-domain tool cards — GateViolation, NotFoundResponse, ValidationFailure"
    - "Index table provides O(1) lookup of all 103 tools with domain, gate status, and one-line description"

key-files:
  created:
    - docs/mcp-tools.md
  modified: []

key-decisions:
  - "Used Python source files as the single source of truth — not REQUIREMENTS.md, which has confirmed drift (e.g., CHAR-02 describes get_character_state but implementation has four separate tools)"
  - "Ordered domain sections: gate-free group first (Characters through Structure), gated group second (Session through Publishing)"
  - "Error contract and gate check pattern documented before the index table — architectural context before tool lookup"

patterns-established:
  - "Tool documentation format: purpose, parameters table (with types from Python annotations), returns (all variants including error types), invocation reason (narrative workflow context), gate status, tables touched"
  - "Invocation reason written in specific narrative workflow context — not 'when the agent wants to' but 'called at the start of each chapter draft to...'"

requirements-completed: []  # Phase 12 has no formal requirement IDs (documentation-only phase)

# Metrics
duration: 8min
completed: 2026-03-09
---

# Phase 12 Plan 03: MCP Tools Reference Summary

**2,615-line implementation-accurate MCP tool reference documenting all 103 tools across 18 domains with index table, error contract, and per-tool cards derived from Python source**

## Performance

- **Duration:** 8 min
- **Started:** 2026-03-09T15:58:41Z
- **Completed:** 2026-03-09T16:06:22Z
- **Tasks:** 1 of 1
- **Files modified:** 1

## Accomplishments

- Created `docs/mcp-tools.md` with 2,615 lines covering all 103 MCP tools
- Index table at top with 103 rows (tool name, domain, gate status, one-line description)
- Error contract section documents all three error response types plus gate check pattern
- 18 domain sections in order (gate-free group: Characters, Relationships, Chapters, Scenes, World, Magic, Plot, Arcs, Gate, Names, Structure; gated group: Session, Timeline, Canon, Knowledge, Foreshadowing, Voice, Publishing)
- Per-tool documentation: purpose, parameters table with Python type annotations, return variants including error types, narrative invocation reason, gate status, and tables touched
- Characters domain correctly documents 4 separate state tools (get_character_location, get_character_injuries, get_character_beliefs, get_character_knowledge) — not a single get_character_state
- Gate tools documented as independent: run_gate_audit does not certify; certify_gate reads current state without re-auditing
- Canon/foreshadowing append-only vs upsert patterns accurately captured from source SQL

## Task Commits

1. **Task 1: Read all tool module files and produce docs/mcp-tools.md** - `4b612a3` (feat)

**Plan metadata:** (this commit)

## Files Created/Modified

- `/Users/gary/writing/drafter/docs/mcp-tools.md` — Complete MCP tool reference (2,615 lines, 103 tool cards)

## Decisions Made

- Used Python source files as the single source of truth — not REQUIREMENTS.md which has confirmed drift
- Ordered domain sections with gate-free group first to orient readers to the worldbuilding tools before the gated prose-phase tools
- Documented error contract and gate check pattern before the index — architectural context first, lookup table second

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- Phase 12 plan 03 complete
- `docs/mcp-tools.md` is the definitive implementation-accurate tool reference
- Ready for Phase 12 plan 04 (if any) or phase completion

---
*Phase: 12-schema-and-mcp-system-documentation*
*Completed: 2026-03-09*
