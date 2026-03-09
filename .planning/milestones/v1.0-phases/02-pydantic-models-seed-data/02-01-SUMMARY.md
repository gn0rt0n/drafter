---
phase: 02-pydantic-models-seed-data
plan: "01"
subsystem: database
tags: [pydantic, sqlite, models, domain-models, json-fields]

# Dependency graph
requires:
  - phase: 01-project-foundation-database
    provides: SQLite migrations (002-013, 021) as schema ground truth for field names
provides:
  - "NotFoundResponse, ValidationFailure, GateViolation error contract types in shared.py"
  - "9 world domain models: Book, Era, Act, Culture, Faction, Location, Artifact, ObjectState, FactionPoliticalState"
  - "6 character domain models: Character, CharacterKnowledge, CharacterBelief, CharacterLocation, InjuryState, TitleState"
  - "3 relationship domain models: CharacterRelationship, RelationshipChangeEvent, PerceptionProfile"
  - "models/__init__.py re-exports all 22 classes for 'from novel.models import Character' usage"
affects:
  - "03-mcp-server-characters-relationships"
  - "04-chapters-scenes-world"
  - "05-plot-arcs"
  - "All phases using MCP tools (Phase 3+)"

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Pydantic v2 BaseModel with id: int | None = None for create/read dual use"
    - "@field_validator(mode='before') @classmethod for JSON TEXT column coercion"
    - "to_db_dict() method on models with JSON fields for SQLite INSERT/UPDATE serialisation"
    - "X | None syntax throughout (no Optional[X]) per Python 3.12 project standard"
    - "bool fields coerce SQLite INTEGER 0/1 automatically in Pydantic v2"

key-files:
  created:
    - src/novel/models/shared.py
    - src/novel/models/world.py
    - src/novel/models/characters.py
    - src/novel/models/relationships.py
  modified:
    - src/novel/models/__init__.py

key-decisions:
  - "SQL migration files are ground truth for field names — plan descriptions that diverged from actual SQL columns were corrected to match migrations exactly"
  - "FactionPoliticalState and ObjectState placed in world.py even though their tables are defined in migration 021 (they are world-state entities semantically)"
  - "Artifact uses origin_era_id (not home_era_id) matching migration 010 actual column name"
  - "CharacterBelief uses content + strength fields (not belief_text + confidence_level) matching migration 013"
  - "PerceptionProfile uses observer_id + subject_id (not perceiver_id + target_id) matching migration 012"
  - "InjuryState uses is_resolved (not is_active) and injury_type + description fields matching migration 013"
  - "TitleState uses title (not title_text) and has no is_active field matching migration 013"

patterns-established:
  - "Pattern: JSON TEXT fields — @field_validator + to_db_dict() on Location.sensory_profile"
  - "Pattern: Error contract — NotFoundResponse/ValidationFailure/GateViolation returned (never raised) by MCP tools"
  - "Pattern: Dual-purpose models — id: int | None = None allows same class for INSERT (no id) and SELECT (has id)"

requirements-completed: [TEST-01]

# Metrics
duration: 20min
completed: 2026-03-07
---

# Phase 2 Plan 01: Pydantic Domain Models (World, Characters, Relationships) Summary

**22 Pydantic v2 models across 4 files — error contract types, 9 world entities, 6 character state models, 3 relationship models — all field names verified against SQLite migrations**

## Performance

- **Duration:** ~20 min
- **Started:** 2026-03-07T20:04:49Z
- **Completed:** 2026-03-07T20:24:00Z
- **Tasks:** 2 + __init__.py update
- **Files modified:** 5

## Accomplishments

- Created `shared.py` with 3 MCP error contract types (NotFoundResponse, ValidationFailure, GateViolation)
- Created `world.py` with 9 models covering migrations 002-006, 010, 021 including Location with JSON sensory_profile field
- Created `characters.py` with 6 models covering migration 007, 013 with correct boolean coercion
- Created `relationships.py` with 3 models covering migration 012
- Updated `__init__.py` to re-export all 22 classes for convenient `from novel.models import Character` access

## Task Commits

1. **Task 1: Create shared.py** - `dcaae45` (feat)
2. **Task 2: Create world/characters/relationships** - `ddbef96` (feat)
3. **__init__.py re-exports** - `91b83be` (feat)

## Files Created/Modified

- `src/novel/models/shared.py` - NotFoundResponse, ValidationFailure, GateViolation error types
- `src/novel/models/world.py` - Book, Era, Act, Culture, Faction, Location (JSON field), Artifact, ObjectState, FactionPoliticalState
- `src/novel/models/characters.py` - Character, CharacterKnowledge, CharacterBelief, CharacterLocation, InjuryState, TitleState
- `src/novel/models/relationships.py` - CharacterRelationship, RelationshipChangeEvent, PerceptionProfile
- `src/novel/models/__init__.py` - Re-exports all 22 model classes with __all__

## Decisions Made

Field names corrected to match actual SQL column names from migrations (migrations are the ground truth, plan descriptions were secondary):

- `Era` uses `date_start`/`date_end`/`summary` (not `start_marker`/`end_marker`/`description`)
- `Act` uses `name`/`purpose`/`structural_notes` (not `title`/`summary`)
- `Culture` uses `values_beliefs`/`aesthetic_style`/`source_file` (not `values`/`aesthetics`)
- `Faction` uses `headquarters`/`size_estimate`/`resources`/`weaknesses`/`alliances`/`conflicts` (not `ideology`/`territory`)
- `Artifact` uses `origin_era_id` (not `home_era_id`), has `magical_properties`/`history` fields
- `CharacterRelationship` uses `bond_strength`/`current_status`/`history_summary`/`first_meeting_chapter_id` (not `dynamic`/`power_dynamic`/`shared_history`/`conflict_source`)
- `RelationshipChangeEvent` uses `description`/`bond_delta` (not `event_description`)
- `PerceptionProfile` uses `observer_id`/`subject_id`/`perceived_traits`/`misperceptions` (not `perceiver_id`/`target_id`/`key_assumptions`/`blind_spots`)
- `CharacterBelief` uses `content`/`strength`/`formed_chapter_id`/`challenged_chapter_id` (not `belief_text`/`confidence_level`/`resolved_in_chapter_id`)
- `CharacterLocation` uses `location_note` (not `arrival_context`/`departure_context`)
- `InjuryState` uses `injury_type`/`description`/`is_resolved`/`resolved_chapter_id` (not `injury_description`/`is_active`/`recovery_notes`)
- `TitleState` uses `title` (not `title_text`), no `is_active` field
- `FactionPoliticalState` uses `alliances`/`conflicts`/`internal_state`/`noted_by_character_id` (not `territory_size`/`active_conflicts`/`internal_stability`/`notable_events`)
- `ObjectState` uses `owner_id` (not `owner_character_id`)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Field names in plan descriptions diverged from actual SQL columns**
- **Found during:** Task 2 (reading migration files)
- **Issue:** The plan's field name specifications for multiple models did not match the actual SQL column names in the migration files. Since TEST-01 compares `model.model_fields` against `PRAGMA table_info` column names, mismatched names would cause test failures.
- **Fix:** Used actual SQL column names from migration files as the ground truth for all field definitions. Corrected 14+ field name discrepancies across Era, Act, Culture, Faction, Artifact, CharacterRelationship, RelationshipChangeEvent, PerceptionProfile, CharacterBelief, CharacterLocation, InjuryState, TitleState, FactionPoliticalState, ObjectState.
- **Files modified:** `world.py`, `characters.py`, `relationships.py`
- **Verification:** `PRAGMA table_info` column names match model field names exactly.
- **Committed in:** `ddbef96` (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - Bug — plan field names vs actual SQL)
**Impact on plan:** Necessary for correctness — TEST-01 (plan 02-04) validates model fields against `PRAGMA table_info`. Using wrong field names would cause test failures. No scope creep.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 2 Plan 02 can proceed: chapters.py, scenes.py, plot.py, arcs.py models
- Phase 3 MCP server can import `from novel.models import Character` immediately
- All 22 models ready for use; `__init__.py` re-exports established

---
*Phase: 02-pydantic-models-seed-data*
*Completed: 2026-03-07*
