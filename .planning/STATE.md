---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: planning
stopped_at: Completed 12-02-PLAN.md (docs/schema.md)
last_updated: "2026-03-09T16:25:51.850Z"
last_activity: 2026-03-07 -- Roadmap created with 10 phases covering 131 requirements
progress:
  total_phases: 12
  completed_phases: 12
  total_plans: 40
  completed_plans: 40
  percent: 100
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-07)

**Core value:** Claude Code can query and update all story data through typed MCP tool calls -- no raw SQL, no markdown parsing -- enabling consistent AI collaboration at novel scale.
**Current focus:** Phase 2: Pydantic Models & Seed Data

## Current Position

Phase: 1 of 10 (Project Foundation & Database)
Plan: 0 of 0 in current phase
Status: Ready to plan
Last activity: 2026-03-07 -- Roadmap created with 10 phases covering 131 requirements

Progress: [████████████████████] 3/3 plans (100%)

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
| Phase 01 P01 | 2 | 2 tasks | 16 files |
| Phase 01 P02 | 8 | 2 tasks | 21 files |
| Phase 01 P03 | 4 | 1 tasks | 1 files |
| Phase 02-pydantic-models-seed-data P01 | 20 | 2 tasks | 5 files |
| Phase 02-pydantic-models-seed-data P02 | 10 | 2 tasks | 5 files |
| Phase 02-pydantic-models-seed-data P03 | 6 | 2 tasks | 9 files |
| Phase 02-pydantic-models-seed-data P04 | 2 | 2 tasks | 5 files |
| Phase 03-mcp-server-core-characters-relationships P01 | 5 | 1 tasks | 3 files |
| Phase 03-mcp-server-core-characters-relationships P02 | 4 | 1 tasks | 2 files |
| Phase 03-mcp-server-core-characters-relationships P03 | 15 | 2 tasks | 4 files |
| Phase 04-chapters-scenes-world P01 | 1 | 2 tasks | 2 files |
| Phase 04-chapters-scenes-world P02 | 2 | 1 tasks | 1 files |
| Phase 04-chapters-scenes-world P03 | 2 | 1 tasks | 1 files |
| Phase 04-chapters-scenes-world P04 | 2 | 2 tasks | 2 files |
| Phase 04-chapters-scenes-world P05 | 3 | 3 tasks | 5 files |
| Phase 05-plot-arcs P01 | 2 | 1 tasks | 1 files |
| Phase 05-plot-arcs P02 | 2 | 1 tasks | 1 files |
| Phase 05-plot-arcs P03 | 5 | 2 tasks | 3 files |
| Phase 06-gate-system P01 | 12 | 2 tasks | 1 files |
| Phase 06-gate-system P02 | 10 | 2 tasks | 3 files |
| Phase 06-gate-system P03 | 12 | 2 tasks | 5 files |
| Phase 07-session-timeline P01 | 2 | 1 tasks | 2 files |
| Phase 07-session-timeline P02 | 5 | 2 tasks | 2 files |
| Phase 07-session-timeline P03 | 7 | 2 tasks | 6 files |
| Phase 08-canon-knowledge-foreshadowing P01 | 4 | 2 tasks | 2 files |
| Phase 08-canon-knowledge-foreshadowing P02 | 2 | 1 tasks | 1 files |
| Phase 08-canon-knowledge-foreshadowing P03 | 5 | 2 tasks | 5 files |
| Phase 09-names-voice-publishing P02 | 1 | 1 tasks | 1 files |
| Phase 09-names-voice-publishing P01 | 3 | 1 tasks | 3 files |
| Phase 09-names-voice-publishing P03 | 6 | 2 tasks | 4 files |
| Phase 10-cli-completion-integration-testing P01 | 3 | 2 tasks | 5 files |
| Phase 10-cli-completion-integration-testing P02 | 4 | 2 tasks | 5 files |
| Phase 10-cli-completion-integration-testing P03 | 4 | 2 tasks | 7 files |
| Phase 11 P01 | 2 | 2 tasks | 3 files |
| Phase 11-update-schema-cli-mcp-and-planning-docs-to-support-7-point-structure-and-3-act-7-point-integration P02 | 4 | 2 tasks | 2 files |
| Phase 11 P03 | 5 | 2 tasks | 7 files |
| Phase 11 P04 | 5 | 1 tasks | 1 files |
| Phase 12-schema-and-mcp-system-documentation P01 | 2 | 2 tasks | 2 files |
| Phase 12-schema-and-mcp-system-documentation P03 | 8 | 1 tasks | 1 files |
| Phase 12 P02 | 26 | 1 tasks | 1 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [Roadmap]: 10 phases derived from 131 requirements at fine granularity
- [Roadmap]: Core MCP domains split into 3 phases (Characters+Relationships, Chapters+World, Plot) for focused delivery
- [Roadmap]: Gate system isolated in Phase 6 after all core tools exist so there are actual tools to gate-block
- [Roadmap]: TEST requirements distributed to phases where the tested thing is built (TEST-01/02 in Phase 2, TEST-03/04 in Phase 10)
- [Phase 01]: mcp entry point is a run() function to allow logging config before server loop starts
- [Phase 01]: uv.lock tracked in git for reproducible installs
- [Phase 01]: db/cli.py stub created in Plan 01 so cli.py import resolves; full implementation deferred to Plan 03
- [Phase 01]: Circular FK (acts<->chapters) resolved via nullable start/end_chapter_id on acts; circular FK (factions<->characters) resolved via nullable leader_character_id on factions
- [Phase 01]: Migration 021 bundles 24 tables in a single file to keep total at exactly 21 migration files while covering all literary/utility domains
- [Phase 01]: seed raises Exit(code=0) on Phase 1 ValueError - expected stub behavior, not an error
- [Phase 01]: reset uses single get_connection() context for both drop_all_tables and apply_migrations - keeps reset atomic
- [Phase 02-01]: SQL migration files are ground truth for field names — plan descriptions that diverged from actual SQL were corrected to match migrations exactly
- [Phase 02-01]: FactionPoliticalState and ObjectState placed in world.py even though defined in migration 021 — semantic grouping preferred over migration file grouping
- [Phase 02-01]: Only models with JSON TEXT columns get to_db_dict() — non-JSON models use model.model_dump() directly for INSERT construction
- [Phase 02-02]: Migration SQL files are ground truth for field names — plan descriptions that diverged from actual SQL were corrected to match migrations exactly (pattern reinforced from 02-01)
- [Phase 02-02]: SupernaturalVoiceGuideline placed in voice.py despite migration 021 — semantic grouping over migration file grouping (same as FactionPoliticalState in world.py)
- [Phase 02-02]: ChapterCharacterArc placed in plot.py (plot-structure junction table) even though it references character_arcs table
- [Phase 02-03]: Migration SQL files are ground truth for column names — plan descriptions that diverged corrected to match SQL (pattern reinforced from 02-01, 02-02)
- [Phase 02-03]: open_questions and decisions_log placed in sessions.py — session-context planning tables (semantic grouping over migration file grouping)
- [Phase 02-03]: ThematicMirror.element_a_id/b_id are plain int (no FK annotation) — polymorphic references with no SQL FK constraints
- [Phase 02-04]: pytest added as dev dependency (uv add --dev pytest) — plan assumed it was installed, auto-fixed as Rule 3 blocking issue
- [Phase 02-04]: TABLE_MODEL_MAP covers all 68 production tables — registry-driven so new tables are caught by extending the map
- [Phase 03-01]: cursor.lastrowid used for aiosqlite INSERT row ID — aiosqlite Connection does not expose lastrowid, only the cursor from execute() does
- [Phase 03-01]: register(mcp: FastMCP) -> None domain tool registration pattern established — tools as local async functions inside register(), each decorated with @mcp.tool()
- [Phase 03-02]: get_relationship queries both orderings via OR clause — caller never needs to know canonical storage order
- [Phase 03-02]: upsert_relationship canonicalizes (min, max) before INSERT to prevent duplicate dyad rows
- [Phase 03-02]: TDD test helpers must use ON CONFLICT DO UPDATE not INSERT OR REPLACE when target table has FK children
- [Phase 03-03]: MCP session entered per-test (not per-fixture) — anyio cancel scope teardown incompatible with pytest-asyncio fixture lifecycle
- [Phase 03-03]: FastMCP serializes list[T] as N separate TextContent blocks — tests use [json.loads(c.text) for c in result.content]
- [Phase 03-03]: Seed relationship pairs are (1,3), (1,4), (1,5) not (1,2) as plan context stated — corrected in tests
- [Phase 04-chapters-scenes-world]: ChapterPlan is a projection model defined in models/chapters.py alongside Chapter for semantic grouping — not inside the tools module
- [Phase 04-chapters-scenes-world]: upsert_scene uses Scene.to_db_dict() to serialise narrative_functions before writing to SQLite — ensures JSON encoding is always correct
- [Phase 04-chapters-scenes-world]: upsert_scene_goal uses ON CONFLICT(scene_id, character_id) DO UPDATE — consistent with Phase 03 decision against INSERT OR REPLACE on tables with FK children
- [Phase 04-chapters-scenes-world]: upsert_location two-branch: None id INSERT + lastrowid, provided id ON CONFLICT(id) DO UPDATE (locations has no UNIQUE beyond PK)
- [Phase 04-chapters-scenes-world]: upsert_faction uses ON CONFLICT(name) for None-id branch; always SELECT back by name since lastrowid=0 on conflict
- [Phase 04-chapters-scenes-world]: upsert_faction does NOT write to faction_political_states — that is a separate time-stamped log table
- [Phase 04-chapters-scenes-world]: MagicComplianceResult defined in models/magic.py alongside other magic domain models — semantic grouping over module locality
- [Phase 04-chapters-scenes-world]: check_magic_compliance is read-only: no conn.commit() call — logging is always a separate log_magic_use call
- [Phase 04-chapters-scenes-world]: log_magic_use is append-only with no ON CONFLICT clause — magic_use_log is an audit trail, not an upsertable record
- [Phase 05-plot-arcs]: upsert_plot_thread uses ON CONFLICT(id) DO UPDATE (not INSERT OR REPLACE) — plot_threads has FK children in chapter_plot_threads and subplot_touchpoint_log
- [Phase 05-plot-arcs]: upsert_plot_thread does NOT touch chapter_plot_threads junction table — junction management is via chapter tools
- [Phase 05-plot-arcs]: upsert_chekov two-branch: no ON CONFLICT(name) since chekovs_gun_registry has no UNIQUE name constraint; None-id uses INSERT+lastrowid, provided-id uses ON CONFLICT(id) DO UPDATE
- [Phase 05-plot-arcs]: get_arc returns ValidationFailure (not NotFoundResponse) when neither arc_id nor character_id provided; get_arc_health returns empty list (not NotFoundResponse) when no health logs exist
- [Phase 05-plot-arcs]: test_get_subplot_touchpoint_gaps inserts subplot thread via raw sqlite3 inside test body — minimal seed has only main threads
- [Phase 05-plot-arcs]: log_arc_health test uses chapter_id=2 (seed has chapter_id=1) to confirm append-only INSERT behavior
- [Phase 06-01]: Implemented 34 gate checklist items not 33 — plan GATE_QUERIES dict had 34 entries; the '33' in prose was a documentation error
- [Phase 06-01]: run_gate_audit and certify_gate are independent — audit does not certify, certify reads current item states and does not re-audit
- [Phase 06-02]: check_gate() placed in novel.mcp not novel.tools — prevents circular import since Phase 7+ tools in novel.tools will import from novel.mcp.gate
- [Phase 06-02]: gate_ready seed correctly targets 34 GATE_ITEM_META items — plan prose said 33 but 06-01 implementation confirmed 34
- [Phase 06-02]: Migration SQL is ground truth for column names — plan sample code had 3 schema mismatches (voice_profiles, name_registry, scene_character_goals) all auto-fixed
- [Phase 06-gate-system]: gate_ready seed had 3 missing data items auto-fixed: chapter 2 pacing_beats, Ithrel Cass character_arc, chapter 3 plot_thread coverage
- [Phase 06-gate-system]: test assertions use actual item count (35 = 34 GATE_ITEM_META + 1 min_characters) not plan prose value of 33
- [Phase 06-gate-system]: certify test must set min_characters to passing before certify call since run_gate_audit does not update rows outside GATE_QUERIES
- [Phase 07-session-timeline]: SessionStartResult carries briefing in MCP tool response body so Claude reads prior session context as MCP caller — not via stderr
- [Phase 07-session-timeline]: start_session auto-closes open sessions before inserting new one; close_session auto-populates carried_forward from unanswered open_questions
- [Phase 07-session-timeline]: get_project_metrics is live-only aggregate — does not write to project_metrics_snapshots; log_project_snapshot is the explicit persist tool
- [Phase 07-session-timeline]: get_travel_segments returns empty list not NotFoundResponse — character with no travel is valid state, locked in CONTEXT.md
- [Phase 07-session-timeline]: list_events prioritises exact chapter_id over start/end_chapter range when both provided — unambiguous semantics
- [Phase 07-session-timeline]: get_open_questions filters answered_at IS NULL — only unanswered questions returned to Claude
- [Phase 07-03]: TravelValidationResult uses segment: TravelSegment | None — single-segment validations include the segment; character-level aggregation sets segment=None
- [Phase 07-03]: upsert_event and log_open_question apply Python-level defaults before INSERT to avoid NOT NULL constraint failures when caller passes None
- [Phase 07-03]: Gate certification uses session-scoped autouse synchronous sqlite3 fixture — avoids anyio cancel scope lifecycle issues with async session fixtures
- [Phase 07-03]: chapters table uses actual_word_count not word_count — session.py get_project_metrics and log_project_snapshot bugs fixed
- [Phase 08-01]: resolve_continuity_issue returns NotFoundResponse after UPDATE+SELECT — SQLite UPDATE does not error on missing row so SELECT-back is required to detect missing IDs
- [Phase 08-01]: Canon tools use append-only INSERT (no ON CONFLICT) for canon_facts, decisions_log, continuity_issues — all are audit log tables
- [Phase 08-02]: get_reader_state uses WHERE chapter_id <= ? (cumulative semantics) — complete reader knowledge snapshot at any story point in one call
- [Phase 08-02]: log_dramatic_irony is append-only (no ON CONFLICT) — irony entries are discrete events consistent with log_ naming convention
- [Phase 08-03]: log_foreshadowing is upsert (two-branch): allows payoff to be filled in later without creating a duplicate plant entry
- [Phase 08-03]: log_motif_occurrence is append-only: each motif appearance is a discrete historical event
- [Phase 08-03]: Test FK compliance: use seed chapter IDs (1-3) not arbitrary chapter numbers
- [Phase 09-02]: upsert_voice_profile ON CONFLICT targets character_id (UNIQUE column) not id — one profile per character, character_id is the business key
- [Phase 09-02]: log_voice_drift is append-only (no ON CONFLICT) — each drift event is a discrete immutable audit log entry
- [Phase 09-02]: get_voice_drift_log returns empty list not NotFoundResponse — no drift is valid state for a character
- [Phase 09-names-voice-publishing]: NameSuggestionsResult defined inline in names.py (not in models/) — result type is tool-local, no cross-domain use
- [Phase 09-names-voice-publishing]: No check_gate() in names.py — gate-free by locked design decision (name tools must work during worldbuilding phase)
- [Phase 09-names-voice-publishing]: register_name wraps INSERT in try/except aiosqlite.IntegrityError — avoids TOCTOU race vs pre-flight SELECT
- [Phase 09-03]: upsert_publishing_asset ON CONFLICT targets id (PK) not a named UNIQUE — publishing_assets has no UNIQUE beyond PK
- [Phase 09-03]: update_submission SELECT-back after UPDATE required — SQLite does not error on UPDATE of missing row (matches resolve_continuity_issue pattern from Phase 08-01)
- [Phase 09-03]: gate_ready seed has voice_profiles for all 5 characters — test fixture inserts 6th character (Tessan Vel) to test None-id CREATE branch of upsert_voice_profile
- [Phase 10-01]: open_questions uses column 'question' not 'question_text' — migration 021 is ground truth, plan prose was incorrect
- [Phase 10-01]: CLI SQL intentionally duplicated from MCP tools — isolation between sync CLI and async MCP layers by design
- [Phase 10-02]: Plan context column names did not match actual migrations for chapters (no start_day/end_day/primary_location) and name_registry (no character_id/character_role/faction) — auto-fixed using migration SQL as ground truth
- [Phase 10-02]: novel name register uses --entity-type and --culture flags (not --role/--faction) to match actual name_registry schema; suggest resolves culture_id via cultures.name then factions.culture_id
- [Phase 10-03]: Gate-violation tests use function-scoped uncertified_db_path to avoid session-scoped certified_gate autouse fixture interference
- [Phase 10-03]: FastMCP 1.26.x stores tools in _tool_manager._tools not _tool_manager.tools — test_tool_selection.py updated to use correct internal attribute
- [Phase 11-01]: story_structure UNIQUE(book_id) enforces one record per book; arc_seven_point_beats UNIQUE(arc_id, beat_type) prevents duplicate beat types; beat_type is plain TEXT (no CHECK constraint, Python-side enum validation); no to_db_dict() on structure models (no JSON TEXT columns)
- [Phase 11-02]: gate.py goes from 34 to 36 items — struct_story_beats (structure category) and arcs_seven_point_beats (plot category) added to both GATE_ITEM_META and GATE_QUERIES simultaneously to keep assert passing
- [Phase 11-02]: seed uses chapter_id=1 for all 14 arc_seven_point_beats rows — seed needs valid FK values, not narrative accuracy
- [Phase 11-02]: story_structure seed row maps all 7 structural beats to existing seed chapters (1, 2, 3) plus all 3 act-level FKs — satisfies gate query which checks all 7 beat FKs are non-null
- [Phase 11-03]: test_structure.py uses create_connected_server_and_client_session(mcp) not mcp._mcp_server — matches test_arcs.py pattern established in Phase 03-03
- [Phase 11-03]: gate_ready seed inserts story_structure rows for both books (book_id=1 and 2) — minimal seed has 2 books, gate query checks ALL books without status filter
- [Phase Phase 11-04]: Gap closure only: REQUIREMENTS.md updated with STRUCT-01 through STRUCT-07 to reflect Phase 11 implementation; no code changes
- [Phase Phase 11-04]: SEED-02 count corrected from 33 to 36: Phase 06-01 had 34 items, Phase 11-02 added 2 more bringing total gate items to 36
- [Phase 12-01]: Tool count documented as 121 (grep count from @mcp.tool() decorators) not plan-prose estimates of ~80/103
- [Phase 12-01]: Migration count documented as 22 (actual glob count); Phase 11 added migration 022 for seven-point structure
- [Phase 12-schema-and-mcp-system-documentation]: Python source files used as single source of truth for tool names — REQUIREMENTS.md excluded due to confirmed drift from implementation
- [Phase 12]: docs/schema.md field names derived from migration SQL files — not from project-research/database-schema.md

### Roadmap Evolution

- Phase 11 added: Update schema, CLI, MCP, and planning docs to support 7-point structure and 3-act/7-point integration
- Phase 12 added: Schema and MCP System Documentation

### Pending Todos

None yet.

### Blockers/Concerns

None yet.

## Session Continuity

Last session: 2026-03-09T16:25:51.847Z
Stopped at: Completed 12-02-PLAN.md (docs/schema.md)
Resume file: None
