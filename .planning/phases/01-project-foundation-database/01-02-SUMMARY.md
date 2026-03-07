---
phase: 01-project-foundation-database
plan: "02"
subsystem: database
tags: [sqlite, sql, migrations, ddl, schema]

# Dependency graph
requires:
  - phase: 01-project-foundation-database/01-01
    provides: src/novel/migrations/ directory, project scaffold, pyproject.toml, uv setup
provides:
  - 21 SQLite migration files covering all 69 narrative database tables
  - Complete schema for all 14 domains (characters, world, plot, arcs, sessions, canon, publishing, etc.)
  - FK-dependency-safe migration order resolving circular references
affects:
  - 01-project-foundation-database/01-03 (DB migration runner and CLI depend on these files)
  - Phase 2 (Pydantic models map to these exact table columns)
  - Phase 3-10 (every MCP tool and CLI command depends on this schema)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "SQLite DDL: INTEGER PRIMARY KEY AUTOINCREMENT for PKs, TEXT for varchar/enum/json/timestamp, INTEGER NOT NULL DEFAULT 0 for booleans"
    - "Idempotent migrations: CREATE TABLE IF NOT EXISTS throughout"
    - "Circular FK resolution: nullable forward-references (acts.start_chapter_id, factions.leader_character_id)"
    - "All entity tables include created_at and updated_at TEXT NOT NULL DEFAULT (datetime('now'))"

key-files:
  created:
    - src/novel/migrations/001_schema_tracking.sql
    - src/novel/migrations/002_core_books_eras.sql
    - src/novel/migrations/003_acts.sql
    - src/novel/migrations/004_cultures.sql
    - src/novel/migrations/005_factions.sql
    - src/novel/migrations/006_locations.sql
    - src/novel/migrations/007_characters.sql
    - src/novel/migrations/008_chapters.sql
    - src/novel/migrations/009_scenes.sql
    - src/novel/migrations/010_artifacts.sql
    - src/novel/migrations/011_magic.sql
    - src/novel/migrations/012_relationships.sql
    - src/novel/migrations/013_character_state.sql
    - src/novel/migrations/014_voice.sql
    - src/novel/migrations/015_events_timeline.sql
    - src/novel/migrations/016_plot_threads.sql
    - src/novel/migrations/017_arcs_chekhov.sql
    - src/novel/migrations/018_scene_pacing.sql
    - src/novel/migrations/019_sessions.sql
    - src/novel/migrations/020_gate_metrics.sql
    - src/novel/migrations/021_literary_publishing.sql
  modified: []

key-decisions:
  - "Circular FK (acts <-> chapters) resolved via nullable start_chapter_id / end_chapter_id on acts table"
  - "Circular FK (factions <-> characters) resolved via nullable leader_character_id on factions table"
  - "relationship_change_events.event_id references events table (defined 3 migrations later) — SQLite only checks FK at DML time, not DDL time, so this is safe"
  - "Migration 021 bundles 24 tables in a single file to minimize file count for rarely-queried literary/utility domains"

patterns-established:
  - "Migration naming: NNN_description.sql (zero-padded 3 digits)"
  - "FK dependency order: dependency-free tables first, then dependent tables in order"
  - "Nullable FK pattern: forward-referenced FKs are nullable to avoid circular dependency violations"
  - "Index naming: idx_{table}_{column} for single-column, idx_{table}_{col1}_{col2} for composite"

requirements-completed:
  - SETUP-02

# Metrics
duration: 8min
completed: 2026-03-07
---

# Phase 1 Plan 02: Database Migrations Summary

**21 SQLite migration files creating 69 narrative database tables across all domains, with circular FK resolution and verified clean sequential application**

## Performance

- **Duration:** 8 min
- **Started:** 2026-03-07T19:30:32Z
- **Completed:** 2026-03-07T19:38:00Z
- **Tasks:** 2
- **Files modified:** 21

## Accomplishments

- Created all 21 migration files (001-021) covering the complete narrative database schema
- Resolved two circular foreign key dependencies via nullable columns (acts.start_chapter_id, factions.leader_character_id)
- All 69 expected tables verified present and FK-check clean via automated Python verification

## Task Commits

Each task was committed atomically:

1. **Task 1: Migrations 001-010 (core entities)** - `01a9aff` (feat)
2. **Task 2: Migrations 011-021 (domain tables)** - `f098653` (feat)

**Plan metadata:** (docs commit to follow)

## Files Created/Modified

- `src/novel/migrations/001_schema_tracking.sql` - schema_migrations tracking table (version, name, applied_at)
- `src/novel/migrations/002_core_books_eras.sql` - eras and books tables
- `src/novel/migrations/003_acts.sql` - acts with nullable chapter FKs (circular FK resolution)
- `src/novel/migrations/004_cultures.sql` - cultures table
- `src/novel/migrations/005_factions.sql` - factions with nullable leader_character_id (circular FK resolution)
- `src/novel/migrations/006_locations.sql` - locations with self-referential parent_location_id
- `src/novel/migrations/007_characters.sql` - characters with nullable FKs to factions/cultures/eras
- `src/novel/migrations/008_chapters.sql` - chapters with FK to books/acts/characters
- `src/novel/migrations/009_scenes.sql` - scenes with FK to chapters/locations
- `src/novel/migrations/010_artifacts.sql` - artifacts with nullable FKs
- `src/novel/migrations/011_magic.sql` - magic_system_elements, supernatural_elements
- `src/novel/migrations/012_relationships.sql` - character_relationships, relationship_change_events, perception_profiles
- `src/novel/migrations/013_character_state.sql` - 5 character state tables (knowledge, beliefs, locations, injuries, titles)
- `src/novel/migrations/014_voice.sql` - voice_profiles, voice_drift_log
- `src/novel/migrations/015_events_timeline.sql` - 5 timeline tables (events, participants, artifacts, travel, pov positions)
- `src/novel/migrations/016_plot_threads.sql` - plot_threads, chapter_plot_threads, chapter_structural_obligations
- `src/novel/migrations/017_arcs_chekhov.sql` - 5 arc/chekhov tables (arcs, chapter arcs, health log, guns, subplot touchpoints)
- `src/novel/migrations/018_scene_pacing.sql` - scene_character_goals, pacing_beats, tension_measurements
- `src/novel/migrations/019_sessions.sql` - session_logs, agent_run_log
- `src/novel/migrations/020_gate_metrics.sql` - architecture_gate, gate_checklist_items, project_metrics_snapshots, pov_balance_snapshots
- `src/novel/migrations/021_literary_publishing.sql` - 24 literary/continuity/canon/publishing/utility tables

## Decisions Made

- Resolved acts<->chapters circular FK by making acts.start_chapter_id and acts.end_chapter_id nullable — acts are created before chapters, so these columns are populated later
- Resolved factions<->characters circular FK by making factions.leader_character_id nullable — factions can be defined before their leader character is created
- relationship_change_events.event_id forward-references events (defined 3 migrations later): SQLite defers FK validation to DML time, so the DDL is valid even before the events table exists
- Migration 021 bundles 24 tables rather than splitting into separate files, keeping the count at exactly 21 while covering all remaining literary/utility domains

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- All 21 migration files ready for the migration runner (Plan 03)
- Schema is the definitive source of truth for Phase 2 Pydantic models
- All 14 MCP tool domains have their backing tables defined
- Zero FK violations confirmed on empty database — safe to build migration runner against

## Self-Check: PASSED

- All 21 migration files confirmed present on disk
- Commits 01a9aff and f098653 confirmed in git log
- SUMMARY.md created at .planning/phases/01-project-foundation-database/01-02-SUMMARY.md
- STATE.md, ROADMAP.md, REQUIREMENTS.md updated

---
*Phase: 01-project-foundation-database*
*Completed: 2026-03-07*
