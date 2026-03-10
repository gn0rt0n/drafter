---
phase: 14-mcp-api-completeness
plan: "11"
subsystem: foreshadowing-tools
tags: [mcp-tools, foreshadowing, upsert, delete, gate-gated, tdd]
dependency_graph:
  requires: ["14-05"]
  provides: ["upsert_motif", "delete_motif", "upsert_prophecy", "delete_prophecy", "upsert_thematic_mirror", "delete_thematic_mirror", "upsert_opposition_pair", "delete_opposition_pair"]
  affects: ["novel.tools.foreshadowing"]
tech_stack:
  added: []
  patterns: ["gate-gated two-branch upsert", "FK-safe delete with try/except"]
key_files:
  created: []
  modified:
    - src/novel/tools/foreshadowing.py
    - tests/test_foreshadowing.py
decisions:
  - "motif_registry.UNIQUE(name) not used for upsert — used id-based ON CONFLICT(id) to allow name edits after creation"
  - "thematic_mirrors and opposition_pairs have no FK children — FK-safe try/except still used for consistency with pattern"
  - "ValidationFailure added to foreshadowing.py shared imports (was missing, needed for new upsert/delete tools)"
  - "All 8 new tools are gate-gated (check_gate returns GateViolation if not certified)"
metrics:
  duration: "~10 minutes"
  completed_date: "2026-03-09"
  tasks_completed: 2
  files_modified: 2
---

# Phase 14 Plan 11: Foreshadowing Upsert and Delete Tools Summary

**One-liner:** Gate-gated upsert and delete CRUD tools for all four literary planning tables (motif_registry, prophecy_registry, thematic_mirrors, opposition_pairs) using two-branch upsert and FK-safe delete patterns.

## What Was Built

Added 8 new MCP tools to `src/novel/tools/foreshadowing.py`, completing CRUD coverage for all four foreshadowing registry tables. Previously, these tables had read tools only — Claude Code could read motifs, prophecies, thematic mirrors, and opposition pairs but had no way to define them.

### New Tools

| Tool | Table | Pattern | Returns |
|------|-------|---------|---------|
| `upsert_motif` | motif_registry | two-branch upsert | GateViolation \| MotifEntry \| ValidationFailure |
| `delete_motif` | motif_registry | FK-safe delete | GateViolation \| NotFoundResponse \| ValidationFailure \| dict |
| `upsert_prophecy` | prophecy_registry | two-branch upsert | GateViolation \| ProphecyEntry \| ValidationFailure |
| `delete_prophecy` | prophecy_registry | FK-safe delete | GateViolation \| NotFoundResponse \| ValidationFailure \| dict |
| `upsert_thematic_mirror` | thematic_mirrors | two-branch upsert | GateViolation \| ThematicMirror \| ValidationFailure |
| `delete_thematic_mirror` | thematic_mirrors | FK-safe delete | GateViolation \| NotFoundResponse \| ValidationFailure \| dict |
| `upsert_opposition_pair` | opposition_pairs | two-branch upsert | GateViolation \| OppositionPair \| ValidationFailure |
| `delete_opposition_pair` | opposition_pairs | FK-safe delete | GateViolation \| NotFoundResponse \| ValidationFailure \| dict |

### Total tool count

`register()` docstring updated from 10 to 18 tools.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| RED | TDD failing tests (24 new tests) | 27b1fa8 | tests/test_foreshadowing.py |
| 1 | upsert_motif, delete_motif, upsert_prophecy, delete_prophecy | 8dd1f4b | src/novel/tools/foreshadowing.py |
| 2 | upsert_thematic_mirror, delete_thematic_mirror, upsert_opposition_pair, delete_opposition_pair | f6d5671 | src/novel/tools/foreshadowing.py |

## Verification

```
uv run python -c "from novel.tools.foreshadowing import register; print('OK')"
# OK

uv run pytest tests/test_foreshadowing.py -q
# 34 passed in 1.02s
```

All 8 function definitions confirmed present with check_gate calls:
- async def upsert_motif (line 477)
- async def delete_motif (line 574)
- async def upsert_prophecy (line 618)
- async def delete_prophecy (line 737)
- async def upsert_thematic_mirror (line 781)
- async def delete_thematic_mirror (line 894)
- async def upsert_opposition_pair (line 937)
- async def delete_opposition_pair (line 1033)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing import] Added ValidationFailure to foreshadowing.py shared imports**
- **Found during:** Task 1 implementation
- **Issue:** `ValidationFailure` was missing from `from novel.models.shared import ...` in foreshadowing.py
- **Fix:** Added `ValidationFailure` to the existing shared import line
- **Files modified:** src/novel/tools/foreshadowing.py
- **Commit:** 8dd1f4b

**2. [Rule 1 - Schema alignment] Used actual schema column names vs plan pseudocode**
- **Found during:** Task 1 design
- **Issue:** Plan's interface section used `motif_name` as parameter name, but actual DB schema uses `name`. Similarly, plan showed simplified ProphecyEntry, MotifEntry fields that didn't match actual migration 021 schema.
- **Fix:** Used actual schema column names from migration 021 verification: motif_registry (name, motif_type, description, thematic_role), prophecy_registry (name, text, subject_character_id, source_character_id, uttered_chapter_id, fulfilled_chapter_id, status, interpretation, notes, canon_status), thematic_mirrors (name, mirror_type, element_a_id, element_a_type, element_b_id, element_b_type, mirror_description, thematic_purpose, notes), opposition_pairs (name, concept_a, concept_b, manifested_in, resolved_chapter_id, notes).
- **Files modified:** src/novel/tools/foreshadowing.py

## Decisions Made

- Used id-based ON CONFLICT(id) upsert for all four tables (rather than UNIQUE constraint on name) — this allows name edits after creation and is consistent with the upsert pattern used elsewhere in the codebase.
- FK-safe try/except pattern used for all four delete tools even though thematic_mirrors and opposition_pairs have no FK children — provides consistent error contract and future-proofs against schema changes.
- `ValidationFailure` added to foreshadowing.py imports (was absent before this plan).

## Self-Check: PASSED

Files exist:
- FOUND: src/novel/tools/foreshadowing.py
- FOUND: tests/test_foreshadowing.py

Commits exist:
- 27b1fa8 — TDD RED tests
- 8dd1f4b — Task 1 implementation
- f6d5671 — Task 2 implementation
