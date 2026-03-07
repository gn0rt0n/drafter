---
phase: 02-pydantic-models-seed-data
plan: "03"
subsystem: database
tags: [pydantic, sqlite, seed-data, models, json-fields]

# Dependency graph
requires:
  - phase: 02-pydantic-models-seed-data/02-02
    provides: "First 7 domain model files (world, characters, relationships, chapters, scenes, plot, arcs, voice)"
  - phase: 01-project-foundation
    provides: "21 migrations defining all table schemas; CLI commands (novel db reset/seed/status)"
provides:
  - "7 remaining domain model files: sessions, timeline, canon, gate, publishing, magic, pacing"
  - "29 Pydantic model classes covering remaining 14 domain tables"
  - "Fully implemented load_seed_profile() with _load_minimal() covering all 69 tables"
  - "Named fantasy world (Age of Embers) seeded with 2 books, 5 characters, 3 chapters, 6 scenes"
affects: [03-mcp-characters-relationships, 04-chapters-scenes-world, 05-plot-arcs, 06-gate-system, 07-session-timeline, 08-canon-knowledge, 09-names-voice-publishing, 10-cli-integration]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "field_validator(mode='before') with JSON string detection for JSON TEXT columns"
    - "to_db_dict() method on models with JSON fields for round-trip SQLite serialisation"
    - "bool coercion via field_validator for INTEGER 0/1 columns"
    - "cursor.lastrowid for all FK ID capture (no hardcoded IDs in seed)"
    - "conn.commit() after each logical insertion group"
    - "faction leader_character_id updated after characters inserted (nullable FK resolution pattern)"

key-files:
  created:
    - src/novel/models/sessions.py
    - src/novel/models/timeline.py
    - src/novel/models/canon.py
    - src/novel/models/gate.py
    - src/novel/models/publishing.py
    - src/novel/models/magic.py
    - src/novel/models/pacing.py
  modified:
    - src/novel/models/__init__.py
    - src/novel/db/seed.py

key-decisions:
  - "Migration SQL files are ground truth for column names — plan description divergences corrected: magic_system_elements uses 'name' not 'element_name'; 'costs' not 'cost'; 'exceptions' not a plan-listed field but present in SQL; pacing uses 'sequence_order' not 'beat_order'; gate uses 'is_passing'/'missing_count' not 'is_passed'/'evidence_query'; timeline uses 'duration' not 'duration_description', 'name' not 'title'; submission_tracker uses 'asset_id'/'agency_or_publisher' not plan field names"
  - "open_questions and decisions_log placed in sessions.py (semantic fit — session-context tables) rather than canon.py"
  - "Sessions domain covers both migration 019 (session_logs, agent_run_log) and session-adjacent tables from 020 (project_metrics_snapshots, pov_balance_snapshots) and 021 (open_questions, decisions_log)"
  - "ThematicMirror.element_a_id and element_b_id typed as plain int (no FK annotation) — table has no FK constraints due to polymorphic references; documented in class docstring"

patterns-established:
  - "Pattern: JSON TEXT fields always get @field_validator(mode='before') + to_db_dict() — consistent with Session and Scene models"
  - "Pattern: All SQLite INTEGER 0/1 boolean columns get @field_validator(mode='before') coercer"
  - "Pattern: Seed inserts in 18 explicit phases with conn.commit() boundaries; each phase handles one FK dependency tier"
  - "Pattern: Named fantasy content throughout seed — no placeholder fixture names"

requirements-completed: [SEED-01, SEED-03]

# Metrics
duration: 6min
completed: 2026-03-07
---

# Phase 2 Plan 03: Remaining Domain Models + Minimal Seed Summary

**29 Pydantic models across 7 domain files plus fully implemented _load_minimal() seeding all 69 tables with a named fantasy world (Age of Embers, Obsidian Court, 5 characters, 2 books, 3 chapters, 6 scenes)**

## Performance

- **Duration:** ~6 min
- **Started:** 2026-03-07T20:11:52Z
- **Completed:** 2026-03-07T20:17:42Z
- **Tasks:** 2
- **Files modified:** 9

## Accomplishments
- Created all 7 remaining domain model files with correct column names derived from migration SQL
- SessionLog implements @field_validator for carried_forward and chapters_touched JSON TEXT fields plus to_db_dict() re-encoding; ArchitectureGate and GateChecklistItem implement bool coercers for INTEGER 0/1 columns
- Replaced Phase 1 seed.py stub with 300-line _load_minimal() covering all 69 tables in 18 FK-ordered phases using cursor.lastrowid throughout
- `novel db seed minimal` completes without error; `novel db status` shows 2 books, 5 characters, 3 chapters, 6 scenes

## Task Commits

Each task was committed atomically:

1. **Task 1: Create 7 remaining domain model files** - `9e31813` (feat)
2. **Task 2: Implement minimal seed profile in seed.py** - `d84845b` (feat)

**Plan metadata:** (see final commit below)

## Files Created/Modified
- `src/novel/models/sessions.py` - SessionLog (JSON validators + to_db_dict), AgentRunLog, ProjectMetricsSnapshot, PovBalanceSnapshot, OpenQuestion, DecisionsLogEntry
- `src/novel/models/timeline.py` - Event, EventParticipant, EventArtifact, TravelSegment, PovChronologicalPosition
- `src/novel/models/canon.py` - CanonFact, ContinuityIssue, ForeshadowingEntry, ProphecyEntry, MotifEntry, MotifOccurrence, ThematicMirror (polymorphic no-FK), OppositionPair, ReaderInformationState, ReaderReveal, DramaticIronyEntry, ReaderExperienceNote
- `src/novel/models/gate.py` - ArchitectureGate, GateChecklistItem (bool coercers)
- `src/novel/models/publishing.py` - PublishingAsset, SubmissionEntry, ResearchNote, DocumentationTask
- `src/novel/models/magic.py` - MagicSystemElement, SupernaturalElement, MagicUseLog, PractitionerAbility, NameRegistryEntry
- `src/novel/models/pacing.py` - PacingBeat, TensionMeasurement
- `src/novel/models/__init__.py` - Added exports for all 29 new classes plus all existing Phase 02-01/02-02 models
- `src/novel/db/seed.py` - Full _load_minimal() implementation replacing Phase 1 stub

## Decisions Made
- SQL migration files are the authoritative column-name source; plan descriptions that diverged were corrected (reinforcing pattern established in 02-01 and 02-02). Notable corrections: magic_system_elements.name (not element_name), magic_system_elements.costs (not cost), pacing_beats.sequence_order (not beat_order), gate_checklist_items.is_passing (not is_passed), travel_segments.elapsed_days (not duration_days), events.name (not title)
- open_questions and decisions_log placed in sessions.py for semantic fit (session-context planning tables) — consistent with world.py / voice.py semantic-over-migration-file grouping pattern
- ThematicMirror uses plain int for element_a_id/element_b_id (no FK annotation) because the SQL table has no FK constraints on these columns (polymorphic references)

## Deviations from Plan

None - plan executed exactly as written. Column-name corrections were made at the point of writing each model by reading the actual SQL, which is the plan-specified process.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All 14 domain model files now exist and are fully importable
- `novel db seed minimal` provides real data for every Phase 3+ MCP tool to return
- Ready for Phase 2 Plan 04 (schema validation tests) and Phase 3 (MCP server: Characters & Relationships)

---
*Phase: 02-pydantic-models-seed-data*
*Completed: 2026-03-07*

## Self-Check: PASSED

All 9 created/modified files confirmed present on disk. Task commits 9e31813 and d84845b confirmed in git log.
