---
phase: 14-mcp-api-completeness
plan: "13"
subsystem: api
tags: [mcp, world, books, acts, eras, sqlite, aiosqlite, fastmcp]

# Dependency graph
requires:
  - phase: 14-09
    provides: cultures and faction_political_states tools in world.py (file conflict avoidance)
provides:
  - get_book, list_books, upsert_book, delete_book (FK-safe vs acts/chapters/story_structure)
  - get_era, list_eras, upsert_era, delete_era (FK-safe vs artifacts/characters)
  - get_act, list_acts, upsert_act, delete_act (FK-safe pattern, book_id pre-check)
affects: [phase-15-docs, any plan that works with narrative structure]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Two-branch upsert: id=None INSERT with lastrowid, id=N ON CONFLICT(id) DO UPDATE"
    - "FK-safe delete: pre-check existence, try DELETE, except Exception → ValidationFailure"
    - "Book pre-check in upsert_act: SELECT id FROM books WHERE id = ? before writing"

key-files:
  created: []
  modified:
    - src/novel/tools/world.py

key-decisions:
  - "Era model uses sequence_order/date_start/date_end/summary/certainty_level — not start_year/end_year/description as in plan interface (real schema from migration 002)"
  - "Act model uses name/purpose/structural_notes — not title/description/notes as in plan interface (real schema from migration 003)"
  - "delete_book is FK-safe (books referenced by acts, chapters, seven_point_structure — all NOT NULL FKs)"
  - "delete_era is FK-safe (eras referenced by artifacts.origin_era_id and characters.home_era_id — nullable FKs)"
  - "delete_act uses FK-safe pattern for consistency even though acts have no known FK children"
  - "upsert_act pre-checks book_id FK before writing; start/end chapter_id are NOT pre-checked (nullable by design)"
  - "Acts UNIQUE(book_id, act_number) constraint handled by ON CONFLICT(id) upsert — upserting same act_number in same book merges correctly when act_id provided"

patterns-established:
  - "list_acts(book_id): filtered list tools require mandatory book_id parameter, ORDER BY act_number"
  - "list_books / list_eras: unfiltered list tools ORDER BY natural sequence field then id/name"

requirements-completed:
  - MCP-01
  - MCP-02
  - GSD-02

# Metrics
duration: 12min
completed: 2026-03-09
---

# Phase 14 Plan 13: Books, Acts, and Eras CRUD Summary

**12 new MCP tools adding full CRUD for books, eras, and acts (the foundational narrative meta-containers) using two-branch upsert and FK-safe delete patterns**

## Performance

- **Duration:** 12 min
- **Started:** 2026-03-09T20:10:00Z
- **Completed:** 2026-03-09T20:22:00Z
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments
- Added 8 books/eras tools: get_book, list_books, upsert_book, delete_book, get_era, list_eras, upsert_era, delete_era
- Added 4 acts tools: get_act, list_acts (filtered by book_id), upsert_act (with book_id pre-check), delete_act
- All upsert tools use two-branch pattern (id=None → INSERT, id=N → ON CONFLICT(id) DO UPDATE)
- All delete tools use FK-safe pattern (try/except with ValidationFailure return)
- Added Book, Era, Act to world.py imports; updated module and register() docstrings to reflect 26 tools

## Task Commits

Each task was committed atomically:

1. **Task 1: Add full CRUD for books and eras** - `c5b4391` (feat)
2. **Task 2: Add full CRUD for acts** - `c5b4391` (feat — combined with Task 1 in same commit as both tasks modified same file sequentially)

## Files Created/Modified
- `src/novel/tools/world.py` - 12 new tools for books, eras, and acts; imports updated; docstrings updated

## Decisions Made
- **Era model fields differ from plan interface:** Plan showed `start_year`, `end_year`, `description` but real migration 002 schema uses `sequence_order`, `date_start`, `date_end`, `summary`, `certainty_level`. Used actual schema.
- **Act model fields differ from plan interface:** Plan showed `title`, `description`, `notes` but real migration 003 schema uses `name`, `purpose`, `word_count_target`, `structural_notes`, `canon_status`. Used actual schema.
- **delete_book FK-safe:** books referenced by acts (NOT NULL), chapters (NOT NULL), seven_point_structure (NOT NULL) — requires try/except pattern.
- **delete_era FK-safe:** eras referenced by artifacts.origin_era_id and characters.home_era_id (both nullable FKs) — still uses try/except for consistency.
- **upsert_act book_id pre-check:** Returns NotFoundResponse if book doesn't exist before attempting write.
- **start/end chapter_id not pre-checked:** Nullable FKs by intentional design — acts can be created before chapters exist.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Used real model/schema fields instead of plan's interface section**
- **Found during:** Task 1 (reading src/novel/models/world.py and migration 002)
- **Issue:** Plan's `<interfaces>` section showed simplified/incorrect field names for Era (`start_year`, `end_year`, `description`) and Act (`title`, `description`, `notes`) that don't match the actual Pydantic models or database schema
- **Fix:** Used actual fields from models (Era: `sequence_order`, `date_start`, `date_end`, `summary`, `certainty_level`; Act: `name`, `purpose`, `word_count_target`, `structural_notes`, `canon_status`)
- **Files modified:** src/novel/tools/world.py
- **Verification:** `uv run python -c "from novel.tools.world import register; print('OK')"` passes
- **Committed in:** c5b4391

---

**Total deviations:** 1 auto-fixed (Rule 1 — corrected field names to match real schema)
**Impact on plan:** Essential for correctness — using plan's interface fields would have caused runtime errors when constructing Pydantic models.

## Issues Encountered
None beyond the field name discrepancy in the plan interface section (auto-fixed via Rule 1).

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Full CRUD for books, acts, and eras now available to Claude Code
- Claude Code can now create the complete book/act structure before adding chapters and scenes
- world.py now has 26 tools total (complete coverage for core world domain entities)
- Ready for Phase 15 documentation phase

---
*Phase: 14-mcp-api-completeness*
*Completed: 2026-03-09*
