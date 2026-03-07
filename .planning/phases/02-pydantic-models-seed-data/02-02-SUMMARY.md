---
phase: 02-pydantic-models-seed-data
plan: "02"
subsystem: database
tags: [pydantic, sqlite, models, chapters, scenes, plot, arcs, voice]

# Dependency graph
requires:
  - phase: 02-pydantic-models-seed-data/02-01
    provides: "BaseModel patterns, field_validator JSON pattern, to_db_dict() pattern"
provides:
  - "Chapter and ChapterStructuralObligation Pydantic models (migration 008/016)"
  - "Scene and SceneCharacterGoal Pydantic models (migration 009/018)"
  - "PlotThread, ChapterPlotThread, ChapterCharacterArc Pydantic models (migration 016/017)"
  - "CharacterArc, ArcHealthLog, ChekhovGun, SubplotTouchpoint Pydantic models (migration 017)"
  - "VoiceProfile, VoiceDriftLog, SupernaturalVoiceGuideline Pydantic models (migration 014/021)"
affects:
  - "Phase 4: Chapters, Scenes & World MCP tools"
  - "Phase 5: Plot & Arcs MCP tools"
  - "Phase 9: Voice & Publishing MCP tools"

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "JSON TEXT list field: narrative_functions uses field_validator + to_db_dict() (list[str] not dict)"
    - "SupernaturalVoiceGuideline placed in voice.py despite migration 021 — semantic grouping over migration grouping"

key-files:
  created:
    - src/novel/models/chapters.py
    - src/novel/models/scenes.py
    - src/novel/models/plot.py
    - src/novel/models/arcs.py
    - src/novel/models/voice.py
  modified: []

key-decisions:
  - "Migration columns are ground truth: plan descriptions that diverged from actual SQL were corrected (e.g. Chapter uses actual_word_count not word_count_actual; ChapterStructuralObligation is in migration 016 not 008)"
  - "ChapterCharacterArc placed in plot.py because it is a plot-structure junction even though it references character_arcs — follows plan spec"
  - "SupernaturalVoiceGuideline placed in voice.py (migration 021) — semantic grouping matches prior FactionPoliticalState/ObjectState pattern in world.py"
  - "VoiceProfile uses migration 014 actual columns: sentence_length, avoids, internal_voice_notes, dialogue_sample (plan description had different names)"
  - "CharacterArc uses migration 017 actual columns: wound, lie_believed, truth_to_learn (plan had arc_title/current_state not in schema)"

patterns-established:
  - "JSON list fields (list[str]): same validator+to_db_dict pattern as JSON dict fields, but returns list not dict"

requirements-completed: [TEST-01]

# Metrics
duration: 10min
completed: 2026-03-07
---

# Phase 2 Plan 02: Narrative Structure Domain Models Summary

**14 Pydantic models across 5 files covering chapters, scenes, plot threads, character arcs, and voice profiles — all fields derived from migration SQL as ground truth**

## Performance

- **Duration:** ~10 min
- **Started:** 2026-03-07T20:09:30Z
- **Completed:** 2026-03-07T20:09:55Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- Created `chapters.py` with Chapter (23 fields from migration 008) and ChapterStructuralObligation (migration 016)
- Created `scenes.py` with Scene (narrative_functions JSON round-trip) and SceneCharacterGoal (migration 018)
- Created `plot.py`, `arcs.py`, `voice.py` with 10 models covering plot threads, arcs, Chekhov's guns, subplot touchpoints, and voice profiles

## Task Commits

1. **Task 1: Create chapters.py and scenes.py** - `9471902` (feat)
2. **Task 2: Create plot.py, arcs.py, and voice.py** - `e1d528f` (feat)

## Files Created/Modified
- `src/novel/models/chapters.py` - Chapter (23 fields) + ChapterStructuralObligation (migration 016)
- `src/novel/models/scenes.py` - Scene (narrative_functions JSON list) + SceneCharacterGoal
- `src/novel/models/plot.py` - PlotThread + ChapterPlotThread + ChapterCharacterArc
- `src/novel/models/arcs.py` - CharacterArc + ArcHealthLog + ChekhovGun + SubplotTouchpoint
- `src/novel/models/voice.py` - VoiceProfile + VoiceDriftLog + SupernaturalVoiceGuideline

## Decisions Made
- Migration SQL files used as ground truth; plan descriptions that differed from actual columns were corrected (e.g. `actual_word_count` not `word_count_actual`, `wound`/`lie_believed`/`truth_to_learn` in CharacterArc, `sentence_length`/`avoids` in VoiceProfile)
- `ChapterStructuralObligation` placed in `chapters.py` despite being in migration 016 — semantically belongs with chapters
- `ChapterCharacterArc` placed in `plot.py` per plan spec (plot-structure junction table)
- `SupernaturalVoiceGuideline` placed in `voice.py` despite migration 021 — semantic grouping matches existing pattern

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Corrected Chapter field names to match migration 008**
- **Found during:** Task 1 (Create chapters.py)
- **Issue:** Plan described `word_count_actual`, `writing_plan`, `in_story_date`, `in_story_time`, `scene_count` — none of these exist in migration 008. Actual columns are `actual_word_count`, `opening_state`, `closing_state`, `hook_strength_rating`, `elapsed_days_from_start`, `structural_function`
- **Fix:** Used migration 008 column names as authoritative source
- **Files modified:** src/novel/models/chapters.py
- **Verification:** Import succeeds, all column names match migration
- **Committed in:** 9471902 (Task 1 commit)

**2. [Rule 1 - Bug] Corrected PlotThread field names to match migration 016**
- **Found during:** Task 2 (Create plot.py)
- **Issue:** Plan described `title`, `description`, `introduced_in_chapter_id`, `resolved_in_chapter_id` — migration 016 uses `name`, `summary`, `resolution`, `opened_chapter_id`, `closed_chapter_id`
- **Fix:** Used migration 016 column names as authoritative source
- **Files modified:** src/novel/models/plot.py
- **Verification:** Import succeeds, field names match migration
- **Committed in:** e1d528f (Task 2 commit)

**3. [Rule 1 - Bug] Corrected CharacterArc field names to match migration 017**
- **Found during:** Task 2 (Create arcs.py)
- **Issue:** Plan described `arc_title`, `current_state`, `desired_state` — migration 017 has `wound`, `lie_believed`, `truth_to_learn` and `opened_chapter_id`/`closed_chapter_id` (not introduced/resolved)
- **Fix:** Used migration 017 column names as authoritative source
- **Files modified:** src/novel/models/arcs.py
- **Committed in:** e1d528f (Task 2 commit)

**4. [Rule 1 - Bug] Corrected VoiceProfile/VoiceDriftLog fields to match migration 014**
- **Found during:** Task 2 (Create voice.py)
- **Issue:** Plan described `speech_patterns`, `avoided_words`, `sentence_rhythm`, `emotional_expression_style`, `formality_level` — migration 014 uses `sentence_length`, `avoids`, `internal_voice_notes`, `dialogue_sample`; VoiceDriftLog has `drift_type`/`is_resolved` not `drift_description`/`severity`/`corrective_note`
- **Fix:** Used migration 014 column names as authoritative source
- **Files modified:** src/novel/models/voice.py
- **Committed in:** e1d528f (Task 2 commit)

**5. [Rule 2 - Missing] Added SupernaturalVoiceGuideline from migration 021**
- **Found during:** Task 2 (Create voice.py)
- **Issue:** Plan specified SupernaturalVoiceGuideline in voice.py but it's not in migration 014 — it exists in migration 021 with columns: `element_name`, `element_type`, `writing_rules`, `avoid`, `example_phrases`
- **Fix:** Added model using migration 021 columns, placed in voice.py per semantic grouping pattern
- **Files modified:** src/novel/models/voice.py
- **Committed in:** e1d528f (Task 2 commit)

---

**Total deviations:** 5 auto-fixed (4 field name corrections, 1 missing model located in different migration)
**Impact on plan:** All corrections necessary for models to match actual database schema. No scope creep.

## Issues Encountered
- Plan field descriptions diverged from actual SQL in multiple places — migration files used as authoritative source throughout (established pattern from 02-01)

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All 14 narrative structure models ready for Phase 4 (Chapters/Scenes/World MCP tools) and Phase 5 (Plot/Arcs MCP tools)
- Voice models ready for Phase 9 (Voice & Publishing tools)
- Full model inventory: characters.py (6), relationships.py (4), world.py (9), shared.py, chapters.py (2), scenes.py (2), plot.py (3), arcs.py (4), voice.py (3) = 33 models across 8 files

---
*Phase: 02-pydantic-models-seed-data*
*Completed: 2026-03-07*
