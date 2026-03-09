---
phase: 02-pydantic-models-seed-data
plan: "04"
subsystem: testing
tags: [pytest, pydantic, sqlite, schema-validation, fk-integrity, tdd]

# Dependency graph
requires:
  - phase: 02-pydantic-models-seed-data
    provides: "All 68 Pydantic model files (shared, world, characters, relationships, chapters, scenes, plot, arcs, voice, sessions, timeline, canon, gate, publishing, magic, pacing) plus minimal seed profile"
provides:
  - "Public model imports via `from novel.models import Character, Scene, ...` (all 68+ classes in __init__.py)"
  - "TEST-01: parametrized schema validation for all 68 table/model pairs (test_schema_validation.py)"
  - "TEST-02: clean-rebuild FK integrity + seed coverage test (test_clean_rebuild.py)"
  - "pytest dev dependency added to pyproject.toml"
affects:
  - phase-03-mcp-server-characters
  - phase-04-chapters-scenes-world
  - phase-05-plot-arcs
  - all-future-phases

# Tech tracking
tech-stack:
  added: [pytest>=9.0.2]
  patterns:
    - "Parametrized schema validation: TABLE_MODEL_MAP dict drives test_model_matches_schema for each domain table"
    - "In-memory SQLite for fast test isolation: sqlite3.connect(':memory:') + apply_migrations + PRAGMA foreign_key_check"
    - "Session-scoped db_conn fixture for schema tests avoids redundant migration overhead"

key-files:
  created:
    - tests/__init__.py
    - tests/test_schema_validation.py
    - tests/test_clean_rebuild.py
  modified:
    - src/novel/models/__init__.py  # already complete from 02-01/02/03; no changes needed
    - pyproject.toml  # added [tool.uv.dev-dependencies] pytest entry
    - uv.lock  # updated with pytest and dependencies

key-decisions:
  - "pytest added as dev dependency (uv add --dev pytest) — plan assumed it was installed, auto-fixed as Rule 3 blocking issue"
  - "TABLE_MODEL_MAP covers all 68 production tables — registry-driven so new tables are caught by extending the map"
  - "test_seed_minimal_coverage uses the plan-specified required_tables list exactly — 51 tables verified"

patterns-established:
  - "Schema regression guard: any model field rename that doesn't match SQL column will fail test_model_matches_schema immediately"
  - "FK integrity gate: test_migrate_and_fk_check and test_seed_minimal_fk_check run before any Phase 3+ work"

requirements-completed: [TEST-01, TEST-02]

# Metrics
duration: 2min
completed: 2026-03-07
---

# Phase 02 Plan 04: Wire Models and Write Test Suite Summary

**71-test suite validating all 68 Pydantic model-schema alignments plus FK-clean migrate/seed cycle using pytest + in-memory SQLite**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-03-07T20:19:42Z
- **Completed:** 2026-03-07T20:21:22Z
- **Tasks:** 2
- **Files modified:** 5 (tests/__init__.py, test_schema_validation.py, test_clean_rebuild.py, pyproject.toml, uv.lock)

## Accomplishments
- Public import surface `from novel.models import Character, Scene, ...` confirmed working — all 68+ model classes accessible
- TEST-01: 68 parametrized schema tests passing — every Pydantic model's field names match its SQL table's PRAGMA table_info columns exactly
- TEST-02: 3 clean-rebuild tests passing — migrations apply clean, FK enforcement zero violations, minimal seed covers all 51 required tables

## Task Commits

Each task was committed atomically:

1. **Task 1: Write __init__.py re-exports** - `9de35d8` (feat) — tests/__init__.py created; __init__.py was already complete from plans 02-01 through 02-03
2. **Task 2: Write schema validation and clean-rebuild tests** - `04598d2` (feat) — test_schema_validation.py + test_clean_rebuild.py + pytest dev dependency

**Plan metadata:** (docs commit pending)

_Note: TDD task ran tests immediately — all 71 passed on first run because models from 02-01/02/03 were already correctly aligned to SQL_

## Files Created/Modified
- `tests/__init__.py` - Empty package marker for pytest discovery
- `tests/test_schema_validation.py` - TEST-01: TABLE_MODEL_MAP with 68 entries, parametrized test comparing model_fields vs PRAGMA table_info
- `tests/test_clean_rebuild.py` - TEST-02: test_migrate_and_fk_check, test_seed_minimal_fk_check, test_seed_minimal_coverage (51 tables)
- `pyproject.toml` - Added pytest as dev dependency
- `uv.lock` - Updated lockfile

## Decisions Made
- pytest added as dev dependency (Rule 3 auto-fix): plan assumed pytest was installed; uv add --dev pytest resolved it
- TABLE_MODEL_MAP covers all 68 production tables, not just spot-checks, giving maximum regression coverage
- test_seed_minimal_coverage checks exactly the 51 tables specified in the plan — acceptance gate is fully in place

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] pytest not installed in virtual environment**
- **Found during:** Task 2 (schema validation and clean-rebuild tests)
- **Issue:** `uv run pytest` failed with "No such file or directory"; `python -m pytest` failed with "No module named pytest"
- **Fix:** Ran `uv add --dev pytest` — added pytest 9.0.2 with iniconfig, packaging, pluggy dependencies
- **Files modified:** pyproject.toml, uv.lock
- **Verification:** `uv run pytest tests/ -v` ran successfully, 71 tests collected and passed
- **Committed in:** 04598d2 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Auto-fix required for test execution. No scope creep.

## Issues Encountered
None — all 71 tests passed on first run, confirming model files from plans 02-01 through 02-03 were correctly aligned to SQL migrations.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All Pydantic models importable via `from novel.models import ClassName`
- Schema validation and FK integrity tests act as regression guards for Phase 3+
- Phase 3 (MCP Server Core — Characters & Relationships) can begin immediately
- `uv run pytest tests/` is the verification command for all future phases

---
*Phase: 02-pydantic-models-seed-data*
*Completed: 2026-03-07*
