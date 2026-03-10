---
phase: 14-mcp-api-completeness
plan: "12"
subsystem: api
tags: [mcp, sqlite, aiosqlite, knowledge, reader-reveals, reader-experience-notes, gate]

# Dependency graph
requires:
  - phase: 14-05
    provides: delete_reader_state and delete_dramatic_irony added to knowledge.py; NotFoundResponse and ValidationFailure in imports
provides:
  - upsert_reader_reveal gate-gated two-branch upsert in knowledge.py
  - delete_reader_reveal gate-gated FK-safe delete in knowledge.py
  - get_reader_experience_notes gate-gated list query in knowledge.py
  - log_reader_experience_note gate-gated append-only insert with FK checks in knowledge.py
  - delete_reader_experience_note gate-gated log-style delete in knowledge.py
affects: [Phase 15 docs, any future knowledge domain tools]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - gate-gated two-branch upsert (reveal_id None vs provided) with optional FK pre-check
    - gate-gated log-style append-only insert with multi-FK pre-check (chapter + scene)
    - gate-gated log-style delete (no try/except, no FK children)
    - gate-gated FK-safe delete (try/except ValidationFailure, potential FK children)

key-files:
  created: []
  modified:
    - src/novel/tools/knowledge.py

key-decisions:
  - "reader_reveals upsert uses real schema columns (planned_reveal, actual_reveal, reader_impact) not the simplified plan interface description field"
  - "log_reader_experience_note checks both chapter_id and scene_id FKs when provided (both are optional in schema)"
  - "delete_reader_reveal uses FK-safe try/except (reader_reveals may have FK children in future); delete_reader_experience_note uses simpler log-delete (no FK children)"

patterns-established:
  - "gate-gated two-branch upsert: None-id branch INSERTs, provided-id branch uses ON CONFLICT(id) DO UPDATE"
  - "log-style insert: gate check, optional FK pre-checks, INSERT, select back by lastrowid, return model"

requirements-completed:
  - MCP-01
  - MCP-02

# Metrics
duration: 2min
completed: 2026-03-09
---

# Phase 14 Plan 12: Reader Reveals & Experience Notes Write Tools Summary

**5 gate-gated knowledge tools added: upsert/delete for reader_reveals and full CRUD for reader_experience_notes**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-09T20:04:56Z
- **Completed:** 2026-03-09T20:05:45Z
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments

- upsert_reader_reveal and delete_reader_reveal added — reader_reveals now has full CRUD (combined with existing get_reader_reveals)
- get_reader_experience_notes, log_reader_experience_note, delete_reader_experience_note added — reader_experience_notes goes from zero coverage to full CRUD
- ReaderExperienceNote imported from novel.models.canon alongside existing imports
- All 5 new tools are gate-gated (check_gate first), matching the knowledge.py module pattern

## Task Commits

Each task was committed atomically:

1. **Task 1: Add upsert_reader_reveal and delete_reader_reveal** - `3641436` (feat)
2. **Task 2: Add reader_experience_notes full CRUD** - `7b01c4f` (feat)

**Plan metadata:** _(final docs commit — see below)_

## Files Created/Modified

- `src/novel/tools/knowledge.py` - Added 5 gate-gated tools and ReaderExperienceNote import; updated module and register() docstrings to reflect 12 tools

## Decisions Made

- reader_reveals upsert uses real schema columns (`planned_reveal`, `actual_reveal`, `reader_impact`) not the simplified `description` field shown in the plan interface — matched to actual migration 021 schema
- log_reader_experience_note checks both `chapter_id` and `scene_id` FKs when provided (both optional in schema)
- delete_reader_reveal uses FK-safe try/except (reader_reveals may have FK children in future); delete_reader_experience_note uses simpler log-delete (no FK children confirmed from schema)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Used real schema columns for upsert_reader_reveal**
- **Found during:** Task 1 (upsert_reader_reveal implementation)
- **Issue:** Plan interface showed `description` as a parameter but the real `reader_reveals` table has `planned_reveal`, `actual_reveal`, `reader_impact` — no `description` column
- **Fix:** Implemented upsert with the actual schema columns from migration 021, making all optional and consistent with the ReaderReveal Pydantic model
- **Files modified:** src/novel/tools/knowledge.py
- **Verification:** `uv run python -c "from novel.tools.knowledge import register; print('OK')"` passes
- **Committed in:** 3641436 (Task 1 commit)

**2. [Rule 1 - Bug] Used `content` field name for log_reader_experience_note**
- **Found during:** Task 2 (log_reader_experience_note implementation)
- **Issue:** Plan spec used `note_text` as the parameter name but the real `reader_experience_notes` table has `content` as the column (confirmed from migration 021 and ReaderExperienceNote model)
- **Fix:** Used `content` as both parameter name and column name, consistent with the model and schema
- **Files modified:** src/novel/tools/knowledge.py
- **Verification:** `uv run python -c "from novel.tools.knowledge import register; print('OK')"` passes
- **Committed in:** 7b01c4f (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (both Rule 1 - schema mismatch corrections)
**Impact on plan:** Both fixes necessary for correctness — plan interface showed simplified/incorrect column names vs actual migration 021 schema.

## Issues Encountered

None — both schema mismatches detected immediately from migration file inspection and corrected inline.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- knowledge.py now has 12 tools covering reader_information_states, dramatic_irony_inventory, reader_reveals, and reader_experience_notes
- All tables in the knowledge domain have full CRUD coverage
- Ready for Phase 15 documentation phase

---
*Phase: 14-mcp-api-completeness*
*Completed: 2026-03-09*
