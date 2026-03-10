---
phase: 14-mcp-api-completeness
plan: "05"
subsystem: mcp-tools
tags: [delete-tools, gate-gated, canon, knowledge, foreshadowing]
dependency_graph:
  requires: []
  provides: [delete_canon_fact, delete_continuity_issue, delete_decision, delete_reader_state, delete_dramatic_irony, delete_foreshadowing, delete_motif_occurrence]
  affects: [canon.py, knowledge.py, foreshadowing.py]
tech_stack:
  added: []
  patterns: [gate-gated-delete, fk-safe-delete, log-delete]
key_files:
  created: []
  modified:
    - src/novel/tools/canon.py
    - src/novel/tools/knowledge.py
    - src/novel/tools/foreshadowing.py
decisions:
  - "ValidationFailure added to canon.py and knowledge.py shared imports to support FK-safe delete pattern for canon_facts (self-ref) and reader_information_states (reader_reveals child)"
  - "delete_continuity_issue, delete_decision, delete_dramatic_irony, delete_foreshadowing, delete_motif_occurrence use log-delete pattern (no try/except) as confirmed leaf tables with no FK children"
metrics:
  duration: "~2 minutes"
  completed: "2026-03-09"
  tasks_completed: 3
  files_modified: 3
---

# Phase 14 Plan 05: Gate-Gated Delete Tools for Canon, Knowledge, Foreshadowing Summary

Gate-gated FK-safe delete tools added to three literary domain modules (canon.py, knowledge.py, foreshadowing.py) — 7 new tools that all call check_gate() before any DB operation and return GateViolation if gate not certified.

## What Was Built

7 new gate-gated delete tools across 3 modules:

**canon.py (3 tools):**
- `delete_canon_fact` — FK-safe (self-referencing parent_fact_id); returns ValidationFailure on IntegrityError
- `delete_continuity_issue` — log-delete (no FK children)
- `delete_decision` — log-delete (decisions_log, no FK children)

**knowledge.py (2 tools):**
- `delete_reader_state` — FK-safe (reader_reveals references reader_information_state_id); returns ValidationFailure on IntegrityError
- `delete_dramatic_irony` — log-delete (dramatic_irony_inventory, no FK children)

**foreshadowing.py (2 tools):**
- `delete_foreshadowing` — log-delete (foreshadowing_registry append-only, no FK children)
- `delete_motif_occurrence` — log-delete (motif_occurrences, no FK children)

## Decisions Made

- `ValidationFailure` added to canon.py and knowledge.py shared imports to support FK-safe delete pattern for canon_facts (self-ref parent_fact_id) and reader_information_states (reader_reveals child FK).
- `delete_continuity_issue`, `delete_decision`, `delete_dramatic_irony`, `delete_foreshadowing`, `delete_motif_occurrence` all use log-delete pattern (simple delete, no try/except) as confirmed leaf tables with no FK children.

## Deviations from Plan

None - plan executed exactly as written.

## Task Commits

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Add gate-gated delete tools to canon.py | 3e2863f | src/novel/tools/canon.py |
| 2 | Add gate-gated delete tools to knowledge.py | 47134d0 | src/novel/tools/knowledge.py |
| 3 | Add gate-gated delete tools to foreshadowing.py | 8319986 | src/novel/tools/foreshadowing.py |

## Self-Check: PASSED

- FOUND: src/novel/tools/canon.py
- FOUND: src/novel/tools/knowledge.py
- FOUND: src/novel/tools/foreshadowing.py
- FOUND: .planning/phases/14-mcp-api-completeness/14-05-SUMMARY.md
- FOUND: commit 3e2863f (canon.py delete tools)
- FOUND: commit 47134d0 (knowledge.py delete tools)
- FOUND: commit 8319986 (foreshadowing.py delete tools)
