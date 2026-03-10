---
phase: 15-documentation-restructure
plan: 04
subsystem: documentation
tags: [schema, docs, split, per-domain, navigation]

# Dependency graph
requires:
  - phase: 15-documentation-restructure
    plan: 02
    provides: Accurate docs/schema.md with Read-only justifications and corrected Populated-by notes
provides:
  - docs/schema/ directory with 18 per-domain schema files
  - chapter_plot_threads in plot.md (correct domain ownership)
  - chapter_character_arcs in arcs.md (correct domain ownership)
  - research_notes and documentation_tasks in publishing.md (Utility merged)
  - Read-only justifications for schema_migrations (structure.md) and architecture_gate (gate.md)
affects:
  - 15-05-PLAN (README.md master index links to all 18 schema files)
  - docs/schema.md monolith (ready for deletion in Phase 15 cleanup plan)

# Tech tracking
tech-stack:
  added: []
  patterns: []

key-files:
  created:
    - docs/schema/arcs.md
    - docs/schema/canon.md
    - docs/schema/chapters.md
    - docs/schema/characters.md
    - docs/schema/foreshadowing.md
    - docs/schema/gate.md
    - docs/schema/knowledge.md
    - docs/schema/magic.md
    - docs/schema/names.md
    - docs/schema/plot.md
    - docs/schema/publishing.md
    - docs/schema/relationships.md
    - docs/schema/scenes.md
    - docs/schema/session.md
    - docs/schema/structure.md
    - docs/schema/timeline.md
    - docs/schema/voice.md
    - docs/schema/world.md
  modified: []

key-decisions:
  - "chapter_plot_threads placed in plot.md — junction owned by plot domain (mirrors arc_seven_point_beats in structure.md, not chapters.md)"
  - "chapter_character_arcs placed in arcs.md — character arcs are the primary entity"
  - "research_notes and documentation_tasks merged into publishing.md — publishing.py owns all 6 MCP write tools for both tables"
  - "magic_system_elements, supernatural_elements, practitioner_abilities in magic.md — magic.py owns all their MCP tools, not world.py"
  - "magic_use_log included in magic.md — was in World section of schema.md but belongs in magic domain by tool ownership"

patterns-established: []

requirements-completed:
  - DOCS-02

# Metrics
duration: 9min
completed: 2026-03-10
---

# Phase 15 Plan 04: Schema Domain Split Summary

**docs/schema.md monolith split into 18 per-domain schema files in docs/schema/, matching the tool module domain taxonomy — all files have back-links, correct table assignments, and preserved Read-only justifications**

## Performance

- **Duration:** 9 min
- **Started:** 2026-03-10T02:47:59Z
- **Completed:** 2026-03-10
- **Tasks:** 2
- **Files created:** 18

## Accomplishments

- Created `docs/schema/` directory with 18 per-domain .md files, one per tool module domain
- All 18 files start with `[← Documentation Index](../README.md)` back-link
- Mermaid ER diagrams included in all multi-table domains, pruned to domain-only tables
- Cross-domain FK notes added to every file that references tables in other domains
- schema_migrations in structure.md with Read-only justification (exact text from Plan 02)
- architecture_gate in gate.md with Read-only justification (exact text from Plan 02)
- research_notes and documentation_tasks merged into publishing.md with Phase 14 tool references
- chapter_plot_threads placed in plot.md per research recommendation (plot threads are the entity)
- chapter_character_arcs placed in arcs.md per research recommendation (arcs are the entity)
- Chapters.md includes cross-domain notes pointing readers to plot.md and arcs.md for junction tables
- magic_use_log added to magic.md (was in World section of schema.md but magic.py owns the tools)
- No stale "Not writable via MCP" or "CLI seed data only" notes in any file

## Task Commits

Each task was committed atomically:

1. **Task 1: structure, world, characters, relationships, gate, session** - `a0e7c30` (feat)
2. **Task 2: remaining 12 domains — timeline, plot, arcs, chapters, scenes, canon, knowledge, foreshadowing, voice, names, magic, publishing** - `7491f00` (feat)

**Plan metadata:** _(created in final commit)_

## Files Created

- `docs/schema/structure.md` — eras, books, schema_migrations (Read-only), acts, story_structure, arc_seven_point_beats
- `docs/schema/world.md` — cultures, factions, locations, artifacts, faction_political_states, object_states
- `docs/schema/characters.md` — characters, character_knowledge, character_beliefs, character_locations, injury_states, title_states
- `docs/schema/relationships.md` — character_relationships, relationship_change_events, perception_profiles
- `docs/schema/gate.md` — architecture_gate (Read-only), gate_checklist_items, project_metrics_snapshots, pov_balance_snapshots
- `docs/schema/session.md` — session_logs, agent_run_log, open_questions, decisions_log
- `docs/schema/timeline.md` — events, event_participants, event_artifacts, travel_segments, pov_chronological_position
- `docs/schema/plot.md` — plot_threads, chapter_plot_threads (junction)
- `docs/schema/arcs.md` — character_arcs, chapter_character_arcs (junction), arc_health_log, chekovs_gun_registry, subplot_touchpoint_log
- `docs/schema/chapters.md` — chapters, chapter_structural_obligations, pacing_beats, tension_measurements
- `docs/schema/scenes.md` — scenes, scene_character_goals
- `docs/schema/canon.md` — canon_facts, continuity_issues
- `docs/schema/knowledge.md` — reader_information_states, reader_reveals, dramatic_irony_inventory, reader_experience_notes
- `docs/schema/foreshadowing.md` — foreshadowing_registry, prophecy_registry, motif_registry, motif_occurrences, thematic_mirrors, opposition_pairs
- `docs/schema/voice.md` — voice_profiles, voice_drift_log, supernatural_voice_guidelines
- `docs/schema/names.md` — name_registry
- `docs/schema/magic.md` — magic_system_elements, supernatural_elements, practitioner_abilities, magic_use_log
- `docs/schema/publishing.md` — publishing_assets, submission_tracker, research_notes, documentation_tasks

## Decisions Made

- **chapter_plot_threads in plot.md** (not chapters.md): The junction exists to attach chapters to plot threads — plot threads are the entity being linked. Mirrors the `arc_seven_point_beats` pattern (lives in structure.md because structure.py owns it). chapters.md includes a cross-domain note pointing to plot.md.
- **chapter_character_arcs in arcs.md** (not chapters.md): Character arcs are the entity being tracked across chapters. Same reasoning as chapter_plot_threads. chapters.md includes a cross-domain note pointing to arcs.md.
- **research_notes and documentation_tasks in publishing.md**: The original schema.md called these "Utility" tables and said they were not writable via MCP. Phase 14 added 6 MCP write tools to publishing.py for both tables. Co-locating their schema docs with publishing.md creates a self-contained domain reference.
- **magic_use_log in magic.md**: The schema.md placed magic_use_log in the World section but magic.py owns `log_magic_use` and `delete_magic_use_log`. Tool ownership takes precedence over the original section placement.
- **supernatural_elements in magic.md**: Though originally in the World section of schema.md, magic.py owns all tools for this table. Consistent with the tool-module-as-domain taxonomy.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] magic_use_log added to magic.md**
- **Found during:** Task 2 (magic.md creation)
- **Issue:** magic_use_log was in the World section of schema.md alongside magic_system_elements and practitioner_abilities, but magic.py owns `log_magic_use` and `delete_magic_use_log`. The plan interface section said "magic.md covers: magic_system_elements, practitioner_abilities, supernatural_elements" but did not list magic_use_log. Including it is required for completeness and accurate tool ownership documentation.
- **Fix:** Added magic_use_log table to magic.md with correct Populated-by references to magic.py
- **Files modified:** docs/schema/magic.md
- **Verification:** magic_use_log documented in magic.md with log_magic_use and delete_magic_use_log tool references

---

None of the 5 success criteria deviated — all satisfied as written.

## Issues Encountered

None — the schema.md source was well-structured after Plan 02 corrections and splitting was straightforward extraction.

## Next Phase Readiness

- docs/schema/ has 18 per-domain files ready for linking from docs/README.md master index
- Plan 05 (README.md master index overhaul) can reference all 18 files
- docs/schema.md monolith still exists and can be deleted in the cleanup plan

---
*Phase: 15-documentation-restructure*
*Completed: 2026-03-10*
