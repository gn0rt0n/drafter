---
phase: 11-update-schema-cli-mcp-and-planning-docs-to-support-7-point-structure-and-3-act-7-point-integration
plan: "01"
subsystem: database
tags: [sqlite, pydantic, migrations, seven-point-structure, story-structure]

# Dependency graph
requires:
  - phase: 01-project-foundation-database
    provides: migration system (apply_migrations), books/chapters/character_arcs tables
  - phase: 02-pydantic-models-seed-data
    provides: Pydantic v2 BaseModel pattern, models/__init__.py re-export pattern
provides:
  - Migration 022: story_structure table (book-level 7-point beats + 3-act alignment chapter FKs)
  - Migration 022: arc_seven_point_beats table (per-arc 7-point beat junction with UNIQUE(arc_id, beat_type))
  - StoryStructure Pydantic model (15 fields)
  - ArcSevenPointBeat Pydantic model (7 fields)
  - Both models exported from novel.models
affects: [11-02, 11-03, 11-04, 11-05]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Migration 022 follows identical FK pattern to prior migrations: INTEGER REFERENCES table(id), no ON DELETE"
    - "No to_db_dict() on structure models — neither has JSON TEXT columns, use model.model_dump() directly"

key-files:
  created:
    - src/novel/migrations/022_seven_point_structure.sql
    - src/novel/models/structure.py
  modified:
    - src/novel/models/__init__.py

key-decisions:
  - "story_structure UNIQUE(book_id) enforces one structure record per book — upsert pattern is ON CONFLICT(book_id)"
  - "arc_seven_point_beats UNIQUE(arc_id, beat_type) prevents duplicate beats per arc — same beat type cannot appear twice"
  - "beat_type is plain TEXT NOT NULL with no CHECK constraint — enum validation is Python-side per codebase pattern"
  - "No to_db_dict() on StoryStructure or ArcSevenPointBeat — neither model has JSON TEXT columns"

patterns-established:
  - "Structure models: field names match SQL column names exactly (migration SQL is ground truth)"
  - "Structure models: nullable FK fields declared as int | None = None, required FKs as int"

requirements-completed: [STRUCT-01, STRUCT-02]

# Metrics
duration: 2min
completed: 2026-03-09
---

# Phase 11 Plan 01: Schema Foundation for 7-Point Structure Summary

**SQLite migration 022 adds story_structure (10 chapter FKs, UNIQUE per book) and arc_seven_point_beats (7-point beat junction, UNIQUE per arc+type), with matching StoryStructure and ArcSevenPointBeat Pydantic v2 models exported from novel.models**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-09T14:29:23Z
- **Completed:** 2026-03-09T14:30:25Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Migration 022 creates story_structure with 7 beat FKs + 3 act-alignment FKs + UNIQUE(book_id)
- Migration 022 creates arc_seven_point_beats junction with UNIQUE(arc_id, beat_type) for per-arc beat tracking
- StoryStructure (15 fields) and ArcSevenPointBeat (7 fields) importable from novel.models

## Task Commits

Each task was committed atomically:

1. **Task 1: Create migration 022_seven_point_structure.sql** - `b0e72c1` (feat)
2. **Task 2: Create models/structure.py and extend models/__init__.py** - `1635bd9` (feat)

**Plan metadata:** (docs commit — see below)

## Files Created/Modified
- `src/novel/migrations/022_seven_point_structure.sql` - Two-table migration: story_structure (book-level 7-point + 3-act chapter FKs) and arc_seven_point_beats (per-arc beat junction)
- `src/novel/models/structure.py` - StoryStructure and ArcSevenPointBeat Pydantic v2 models with exact SQL column name mapping
- `src/novel/models/__init__.py` - Added structure import line and __all__ entries under "# structure domain" comment

## Decisions Made
- `story_structure` has UNIQUE(book_id) — exactly one structure record per book; upsert tools should target this
- `arc_seven_point_beats` has UNIQUE(arc_id, beat_type) — prevents duplicate beat types per arc
- `beat_type` is plain TEXT NOT NULL (no CHECK constraint) — enum validation is Python-side per established codebase pattern
- Neither model gets `to_db_dict()` — no JSON TEXT columns, `model.model_dump()` is sufficient

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Initial verification used bare `python -c` instead of `uv run python -c` — module not found. Corrected immediately.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Migration 022 and models ready for Plan 02 (CLI commands for story_structure) and Plan 03 (MCP tools)
- No blockers

---
*Phase: 11-update-schema-cli-mcp-and-planning-docs-to-support-7-point-structure-and-3-act-7-point-integration*
*Completed: 2026-03-09*
