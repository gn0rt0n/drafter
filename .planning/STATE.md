---
gsd_state_version: 1.0
milestone: v1.1
milestone_name: Tech Debt & API Completeness
status: planning
stopped_at: Completed 15-02-PLAN.md
last_updated: "2026-03-10T02:18:40.014Z"
last_activity: 2026-03-09 — v1.1 roadmap created, 3 phases defined (13–15)
progress:
  total_phases: 3
  completed_phases: 2
  total_plans: 26
  completed_plans: 22
  percent: 0
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-09 after v1.0 milestone)

**Core value:** Claude Code can query and update all story data through typed MCP tool calls — no raw SQL, no markdown parsing — enabling consistent AI collaboration at novel scale.
**Current focus:** Phase 13 — Tech Debt Clearance (ready to plan)

## Current Position

Phase: 13 of 15 (Tech Debt Clearance)
Plan: — (not yet planned)
Status: Ready to plan
Last activity: 2026-03-09 — v1.1 roadmap created, 3 phases defined (13–15)

Progress: [░░░░░░░░░░░░░░░░░░░░] 0/TBD plans (0%)

## Performance Metrics

**Velocity:**
- Total plans completed: 0
- Average duration: -
- Total execution time: 0 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| - | - | - | - |

**Recent Trend:**
- Last 5 plans: -
- Trend: -

*Updated after each plan completion*
| Phase 13 P02 | 2 | 2 tasks | 2 files |
| Phase 13-tech-debt-clearance P01 | 2 | 3 tasks | 2 files |
| Phase 14-mcp-api-completeness P01 | 2 | 3 tasks | 3 files |
| Phase 14 P02 | 259 | 3 tasks | 6 files |
| Phase 14 P03 | 8 | 2 tasks | 2 files |
| Phase 14-mcp-api-completeness P04 | 2 | 3 tasks | 3 files |
| Phase 14 P05 | 2 | 3 tasks | 3 files |
| Phase 14 P06 | 3 | 3 tasks | 4 files |
| Phase 14 P07 | 5 | 2 tasks | 2 files |
| Phase 14 P08 | 242 | 2 tasks | 4 files |
| Phase 14 P09 | 3 | 2 tasks | 2 files |
| Phase 14-mcp-api-completeness P10 | 15 | 2 tasks | 3 files |
| Phase 14 P11 | 10 | 2 tasks | 2 files |
| Phase 14 P12 | 2 | 2 tasks | 1 files |
| Phase 14-mcp-api-completeness P13 | 12 | 2 tasks | 1 files |
| Phase 14-mcp-api-completeness P15 | 8 | 1 tasks | 1 files |
| Phase 14-mcp-api-completeness P16 | 3 | 2 tasks | 2 files |
| Phase 14-mcp-api-completeness P17 | 4 | 2 tasks | 2 files |
| Phase 14-mcp-api-completeness P14 | 2 | 2 tasks | 1 files |
| Phase 14-mcp-api-completeness P18 | 3 | 2 tasks | 4 files |
| Phase 14-mcp-api-completeness P19 | 4 | 3 tasks | 2 files |
| Phase 15-documentation-restructure P02 | 18 | 2 tasks | 1 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [Roadmap v1.1]: 3 phases derived from 13 requirements at fine granularity — DEBT (13), MCP (14), DOCS (15)
- [Roadmap v1.1]: DOCS phase depends on both DEBT and MCP — README bug fixes land in Phase 13, new write tools land in Phase 14, docs split happens in Phase 15
- [Roadmap v1.1]: Phase numbering continues from v1.0 (v1.0 ended at 12, v1.1 starts at 13)
- [Phase 13]: DEBT-04: export subcommand confirmed as 'all' (not 'export-all') — source-verified from src/novel/export/cli.py line 149
- [Phase 13]: DEBT-07: pydantic pinned at >=2.11 with no patch version, matching >=major.minor style used by typer and aiosqlite
- [Phase 13-tech-debt-clearance]: REQUIREMENTS.md confirmed clean on execution — no stale 33/34 gate count references; Task 3 required zero edits
- [Phase 14-mcp-api-completeness]: FK-safe pattern used for all parent tables (characters, character_arcs, character_relationships, perception_profiles, chekovs_gun_registry); log-table (simpler) pattern for append-only log tables with no FK children
- [Phase 14-mcp-api-completeness]: No gate checks on delete tools in characters, relationships, arcs modules — these modules have no gate guards on any existing tools
- [Phase 14]: FK-safe pattern (try/except ValidationFailure) for delete_chapter, delete_scene, delete_story_structure; log-delete for delete_scene_goal and delete_arc_beat (confirmed leaf tables)
- [Phase 14]: Delete tools in timeline.py do not call check_gate even though read/write tools in the same module do — consistent with phase 14 no-gate pattern for deletes
- [Phase 14]: ValidationFailure added to timeline.py shared import (was missing) to support delete_event and delete_pov_position FK-safe pattern
- [Phase 14]: delete_travel_segment uses simpler log-delete (no try/except) since travel_segments has no FK children; delete_pov_position uses integer primary key (id), not composite key
- [Phase 14-mcp-api-completeness]: delete_magic_use_log uses simpler log-delete pattern (no try/except) since magic_use_log is an append-only log with no FK children
- [Phase 14-mcp-api-completeness]: delete_name_registry_entry uses integer primary key (id) not name string for unambiguous deletion
- [Phase 14-mcp-api-completeness]: No gate checks added to delete tools in world, magic, names modules — consistent with phase 14 no-gate pattern for deletes
- [Phase 14]: ValidationFailure added to canon.py and knowledge.py imports for FK-safe delete pattern; log-delete (no try/except) used for leaf tables without FK children
- [Phase 14]: voice.py and session.py delete tools are gate-gated; publishing.py and gate.py delete tools are not gate-gated (gate management tools exempt from gate requirement)
- [Phase 14]: delete_gate_checklist_item added to gate.py as admin cleanup tool — not gate-gated, FK-safe pattern, analogous to update_checklist_item
- [Phase 14]: character_beliefs log_* tool checks optional formed_chapter_id FK only (no required chapter_id — table schema has formed_chapter_id as optional)
- [Phase 14]: TitleState added to characters.py imports — model existed in models but was not imported in tools file
- [Phase 14]: log-style delete (no try/except) used for character_beliefs, character_locations, injury_states, title_states — all append-only logs with no FK children
- [Phase 14]: log_travel_segment is NOT gate-gated per plan spec (no GateViolation return type)
- [Phase 14]: pov_balance_snapshots uses chapter_count + word_count fields (not pov_percentage) — real schema from migration 020 used
- [Phase 14]: cultures UNIQUE(name) confirmed in migration 004 — upsert uses ON CONFLICT(name) pattern like upsert_faction
- [Phase 14]: faction_political_states.chapter_id is NOT NULL — log_faction_political_state makes chapter_id required (not optional)
- [Phase 14]: delete_culture is FK-safe (locations and name_registry reference cultures); delete_faction_political_state is log-style (no FK children)
- [Phase 14-mcp-api-completeness]: magic_system_elements columns are rules/limitations/costs/exceptions (not description) — confirmed from migration 011; upsert uses correct column names
- [Phase 14-mcp-api-completeness]: supernatural_voice_guidelines upsert uses ON CONFLICT(id) (not element_name) to allow element_name edits after creation
- [Phase 14-mcp-api-completeness]: upsert_supernatural_voice_guideline and delete_supernatural_voice_guideline are gate-gated; upsert_name_registry_entry is gate-free — consistent with existing module patterns
- [Phase 14]: upsert_motif/prophecy/thematic_mirror/opposition_pair all use id-based ON CONFLICT(id) upsert to allow field edits after creation; ValidationFailure added to foreshadowing.py imports
- [Phase 14]: reader_reveals upsert uses real schema columns (planned_reveal, actual_reveal, reader_impact) not simplified plan interface; log_reader_experience_note checks both chapter_id and scene_id FKs; delete_reader_reveal FK-safe vs delete_reader_experience_note log-delete (no FK children)
- [Phase 14-mcp-api-completeness]: Era model uses sequence_order/date_start/date_end/summary/certainty_level — not start_year/end_year/description as in plan interface (real schema from migration 002)
- [Phase 14-mcp-api-completeness]: Act model uses name/purpose/structural_notes — not title/description/notes as in plan interface (real schema from migration 003)
- [Phase 14-mcp-api-completeness]: delete_book FK-safe (books referenced by acts, chapters, seven_point_structure); delete_era FK-safe (eras referenced by artifacts.origin_era_id and characters.home_era_id)
- [Phase 14-mcp-api-completeness]: upsert_act pre-checks book_id FK; start/end chapter_id are NOT pre-checked (nullable by design — acts can be created before chapters exist)
- [Phase 14-mcp-api-completeness]: get_supernatural_element added to magic.py — plan assumed it existed but tool was absent; SupernaturalElement import also added
- [Phase 14-mcp-api-completeness]: supernatural_elements delete uses FK-safe try/except even though table has no FK children — follows plan spec and is safe pattern
- [Phase 14-mcp-api-completeness]: PacingBeat real schema uses description + sequence_order + optional scene_id (not intensity as in plan interface) — confirmed from migration 018
- [Phase 14-mcp-api-completeness]: TensionMeasurement has no scene_id column — chapter-scoped only with measurement_type field (not tension_type as in plan interface)
- [Phase 14-mcp-api-completeness]: pacing_beats and tension_measurements are leaf tables — log-delete pattern (no ValidationFailure) used for both delete tools
- [Phase 14]: ResearchNote uses topic (not title) and relevance (not tags) — real schema from migration 021 used; plan interface was simplified
- [Phase 14]: documentation_tasks and research_notes tools are not gate-gated (dev-internal tables) — publishing_assets and submission_tracker remain gate-gated
- [Phase 14-mcp-api-completeness]: Artifact model uses real schema columns from migration 010 (current_owner_id, significance, magical_properties, history); ObjectState uses owner_id/location_id/condition — not simplified plan interface names
- [Phase 14-mcp-api-completeness]: delete_artifact FK-safe (object_states + event_artifacts reference it); delete_object_state log-style (leaf table)
- [Phase 14-mcp-api-completeness]: log_object_state pre-checks both artifact_id and chapter_id FKs before INSERT; object_states has UNIQUE(artifact_id, chapter_id)
- [Phase 14-mcp-api-completeness]: arc_progression is the real schema column in chapter_character_arcs (not arc_role) — confirmed from migration 017
- [Phase 14-mcp-api-completeness]: ChapterCharacterArc is in novel.models.plot (not novel.models.arcs) — imported cross-module in arcs.py
- [Phase 14-mcp-api-completeness]: chapter_plot_threads and chapter_character_arcs both have surrogate AUTOINCREMENT id + UNIQUE(chapter_id, FK_id) — ON CONFLICT targets composite unique constraint
- [Phase 14-mcp-api-completeness]: event_participants.role column used (not participant_role as in plan interface) — real schema from migration 015
- [Phase 14-mcp-api-completeness]: event_artifacts.involvement column used (not artifact_role) — EventArtifact has no notes column in real schema
- [Phase 14-mcp-api-completeness]: delete_gate_checklist_item Task 2 was no-op — tool fully implemented in Plan 06 (commit 79aad80)
- [Phase 15-02]: schema.md corrected for all 28 tables with stale Populated-by notes — full-file audit rather than only the 5 explicitly listed
- [Phase 15-02]: architecture_gate gets Read-only note alongside Populated-by certify_gate — clarifies no direct write tool bypasses gate flow

### Pending Todos

None.

### Blockers/Concerns

None.

## Session Continuity

Last session: 2026-03-10T02:18:40.012Z
Stopped at: Completed 15-02-PLAN.md
Resume file: None
