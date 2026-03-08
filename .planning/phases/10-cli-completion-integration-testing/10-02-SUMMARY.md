---
phase: 10-cli-completion-integration-testing
plan: "02"
subsystem: cli
tags: [typer, sqlite3, export, name-registry, markdown]

# Dependency graph
requires:
  - phase: 01-project-foundation-database
    provides: get_connection() sync sqlite3 helper, chapters/scenes/name_registry tables
  - phase: 06-gate-system
    provides: gate/cli.py canonical error handling pattern (except typer.Exit: raise)
  - phase: 09-names-voice-publishing
    provides: name_registry table, names MCP tools SQL reference
provides:
  - novel export chapter [n] — write chapter_{n:03d}.md with header + scenes
  - novel export all — write one .md file per chapter in DB
  - novel name check [name] — conflict check against name_registry
  - novel name register [name] — insert name into name_registry with prompts or flags
  - novel name suggest [faction] — show existing names for a culture/faction
affects: [10-cli-completion-integration-testing]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "sync sqlite3 via get_connection() for all CLI database access (never novel.mcp.db)"
    - "except typer.Exit: raise pattern for error propagation (from gate/cli.py)"
    - "_write_chapter helper shared between chapter and all commands to avoid duplication"
    - "culture resolution: try cultures.name first, fall back to factions.culture_id"

key-files:
  created:
    - src/novel/export/__init__.py
    - src/novel/export/cli.py
    - src/novel/name/__init__.py
    - src/novel/name/cli.py
  modified:
    - src/novel/cli.py

key-decisions:
  - "Plan context had wrong column names for chapters (start_day/end_day/primary_location do not exist) — use time_marker and resolve location via JOIN to scenes+locations"
  - "Plan context had wrong columns for name_registry (character_id/character_role/faction do not exist) — actual columns are entity_type, culture_id, linguistic_notes"
  - "Scene title column does not exist — use scene_number as markdown section heading"
  - "name suggest resolves culture by checking cultures.name then factions.culture_id, then queries name_registry by culture_id"
  - "name register prompts for entity_type/culture/notes if not provided via CLI flags; culture name resolved to culture_id before INSERT"

patterns-established:
  - "CLI export module pattern: _write_chapter(conn, chapter_row, output_dir) helper decouples markdown logic from command handlers"
  - "Schema verification: always check actual migration SQL before writing column references in CLI code"

requirements-completed: [CLEX-01, CLEX-02, CLNM-01, CLNM-02, CLNM-03]

# Metrics
duration: 4min
completed: 2026-03-08
---

# Phase 10 Plan 02: Export and Name CLI Summary

**Five CLI commands — novel export chapter/all and novel name check/register/suggest — wired to root CLI using sync sqlite3 and actual migration schema**

## Performance

- **Duration:** ~4 min
- **Started:** 2026-03-08T22:55:57Z
- **Completed:** 2026-03-08T22:59:55Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- `novel export chapter [n]` writes `chapter_{n:03d}.md` with chapter header, POV/Timeline/Location metadata, and scene sections using sync sqlite3
- `novel export all` iterates all chapters in DB order and writes one file per chapter
- `novel name check/register/suggest` mirror names MCP tool SQL via sync sqlite3, resolving culture by name before querying name_registry
- Root `cli.py` updated with export and name Typer subcommand groups, docstring updated

## Task Commits

Each task was committed atomically:

1. **Task 1: Create export CLI module** - `037d0c7` (feat)
2. **Task 2: Create name CLI module and wire all groups** - `6520959` (feat)
3. **Auto-fix: Schema bug fixes for export and name CLIs** - `006fb0a` (fix)

**Plan metadata:** (docs commit follows)

## Files Created/Modified

- `src/novel/export/__init__.py` — empty package marker
- `src/novel/export/cli.py` — chapter and all commands; _write_chapter/_build_chapter_markdown/_resolve_location helpers
- `src/novel/name/__init__.py` — empty package marker
- `src/novel/name/cli.py` — check, register, suggest commands using actual name_registry schema
- `src/novel/cli.py` — added export and name Typer registrations; updated docstring

## Decisions Made

- Plan context referenced chapters columns `start_day`, `end_day`, `primary_location` — none exist in migration 008. Used `time_marker` for Timeline; resolved location via JOIN to scenes/locations table.
- Plan context referenced name_registry columns `character_id`, `character_role`, `faction` — none exist in migration 021. Actual schema: `entity_type`, `culture_id`, `linguistic_notes`.
- Scene `title` column does not exist in migration 009 — use `scene_number` as the markdown section heading.
- `novel name suggest` resolves culture_id via `cultures.name` first, then falls back to `factions.culture_id`, then queries `name_registry.culture_id`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Wrong column names in export/cli.py — chapters table schema mismatch**
- **Found during:** Task 1 verification (end-to-end smoke test)
- **Issue:** Plan context said chapters has `start_day`, `end_day`, `primary_location`. Actual migration 008 has `time_marker`, `elapsed_days_from_start`; no location column on chapters.
- **Fix:** Use `time_marker` for Timeline field; resolve location name by JOINing first scene to locations table; use `scene_number` as heading (scenes have no `title` column).
- **Files modified:** `src/novel/export/cli.py`
- **Verification:** `novel export chapter 1` writes correct markdown, `novel export all` writes 3 files
- **Committed in:** `006fb0a`

**2. [Rule 1 - Bug] Wrong column names in name/cli.py — name_registry schema mismatch**
- **Found during:** Task 2 verification (smoke test for `novel name check Aeryn`)
- **Issue:** Plan context said name_registry has `character_id`, `character_role`, `faction`. Actual migration 021 has `entity_type`, `culture_id`, `linguistic_notes`, `introduced_chapter_id`.
- **Fix:** Rewrite all three commands (check/register/suggest) using actual columns. Register now takes `--entity-type` and `--culture` flags instead of `--role` and `--faction`. Suggest queries by `culture_id` after name lookup.
- **Files modified:** `src/novel/name/cli.py`
- **Verification:** `novel name check Aeryn` outputs "No conflict.", `novel name suggest Kaelthari` shows "Aeryn Vael"
- **Committed in:** `006fb0a`

---

**Total deviations:** 2 auto-fixed (both Rule 1 - Bug)
**Impact on plan:** Both fixes necessary for correctness — plan context described a different schema than what the migrations actually implemented. No scope creep.

## Issues Encountered

Plan context (CONTEXT.md/INTERFACES section) had column names that did not match the actual migration SQL. The project's documented pattern ("Migration SQL files are ground truth for field names") from prior phases (02-01, 02-02, 02-03, 06-02) applied here — migration SQL took precedence over plan prose descriptions.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- All five export and name CLI commands operational
- Root CLI now has db, gate, export, name subcommand groups registered
- Phase 10 integration testing plan (10-03) can verify CLI e2e behavior against seeded DB

## Self-Check: PASSED

- src/novel/export/__init__.py: FOUND
- src/novel/export/cli.py: FOUND
- src/novel/name/__init__.py: FOUND
- src/novel/name/cli.py: FOUND
- 10-02-SUMMARY.md: FOUND
- Commit 037d0c7: FOUND
- Commit 6520959: FOUND
- Commit 006fb0a: FOUND

---
*Phase: 10-cli-completion-integration-testing*
*Completed: 2026-03-08*
