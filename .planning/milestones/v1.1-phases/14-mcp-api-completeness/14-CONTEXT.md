# Phase 14: MCP API Completeness - Context

**Gathered:** 2026-03-09
**Status:** Ready for planning

<domain>
## Phase Boundary

Audit all 71 schema tables against existing MCP tools. Add missing write tools (and read tools where absent). Add delete tools to all domains. Document the two system tables that are intentionally read-only with justification. No new schema tables, no new domains.

</domain>

<decisions>
## Implementation Decisions

### Read-only table policy
- Only two tables are intentionally read-only: `schema_migrations` (managed by migration runner) and `architecture_gate` (managed exclusively through the `certify_gate` tool flow)
- All other 69 tables get full CRUD: read, list, upsert/log, delete
- World-building tables previously treated as seed-only (`eras`, `cultures`, `magic_system_elements`, `supernatural_elements`, `practitioner_abilities`, `supernatural_voice_guidelines`) are writable — Claude Code should be able to create/update world-building entries during active novel work
- Auto-generated tables (`chapter_structural_obligations`, `pov_balance_snapshots`) and dev-internal tables (`documentation_tasks`, `research_notes`) also get write tools — policy is "all non-system tables are writable"

### Full CRUD everywhere
- Every non-system table gets: `get_{entity}`, `list_{entities}` (where table is browsable), `upsert_{entity}` or `log_{entity}` (append-only log pattern for historical state), `delete_{entity}`
- Hard deletes only — no soft delete / `deleted_at` pattern; schema doesn't have these columns and adding them everywhere is out of scope
- FK-safe deletes: if deleting a row would orphan records in dependent tables, refuse with a clear error message describing the FK constraint; do NOT cascade
- Delete tool naming: always `delete_{table_singular}` (e.g., `delete_canon_fact`, `delete_character`, `delete_arc_beat`)

### Character state tables (log + helpers pattern)
- `character_beliefs`, `character_locations`, `injury_states`, `title_states` use the `log_*` pattern (append-only history, each entry is chapter-scoped)
- Pattern: `log_character_belief` + `get_character_beliefs` (already exists) + `delete_character_belief`; same for injuries, locations, titles
- Also add `get_current_*` helper where useful (e.g., `get_current_character_location` returns the most recent location for a character)

### Missing core tables — books, acts, eras
- `books`, `acts`, `eras` have zero MCP tools; add full CRUD: `get_book`/`list_books`/`upsert_book`/`delete_book`, etc.
- These are fundamental narrative containers; the planner should determine which module they belong in (world.py or a new structure/meta module)
- `acts` FK depends on `books`; `acts.start_chapter_id` and `end_chapter_id` are nullable to avoid circular FK — delete_act must respect this

### Artifacts — zero coverage
- `artifacts` table (magic items, relics, key objects) has NO tools at all — can't even read an artifact
- Full CRUD: `get_artifact`, `list_artifacts`, `upsert_artifact`, `delete_artifact`
- Belongs in world.py alongside locations and factions

### Other fully uncovered tables
- `supernatural_elements` — full CRUD, belongs in magic.py or world.py (planner decides)
- `object_states` — tracks item state changes during the story (e.g., sword broken at ch 10, reforged at ch 20); full CRUD; belongs in world.py or timeline.py
- `pacing_beats`, `tension_measurements` — narrative rhythm tracking; full CRUD; belongs in session.py or structure.py (planner decides)
- `reader_experience_notes` — editorial notes per chapter/scene; full CRUD; belongs in knowledge.py
- `documentation_tasks`, `research_notes` — full CRUD (all non-system tables writable)

### Literary planning tables — write tools needed
- `motif_registry` — only occurrence logging exists (`log_motif_occurrence`); add `upsert_motif` + `delete_motif` so Claude can define new motifs, not just log occurrences
- `thematic_mirrors`, `opposition_pairs`, `prophecy_registry` — have read tools only; add upsert + delete
- `reader_reveals` — has `get_reader_reveals` only; add `upsert_reader_reveal` + `delete_reader_reveal`
- `subplot_touchpoint_log` — has gap-analysis read tool only; add `log_subplot_touchpoint` + `delete_subplot_touchpoint`
- `faction_political_states` — has read tool only; add `log_faction_political_state` + `delete_faction_political_state`
- Module placement: Claude's discretion (stay in foreshadowing.py and knowledge.py, or split to new module if foreshadowing.py becomes too large)

### Junction table coverage — dedicated tools
- `chapter_plot_threads`, `chapter_character_arcs`, `event_participants`, `event_artifacts` get dedicated association tools
- Pattern: `link_{a}_to_{b}` / `unlink_{a}_from_{b}` + `get_{b}s_for_{a}` query
  - e.g., `link_chapter_to_plot_thread`, `unlink_chapter_from_plot_thread`, `get_plot_threads_for_chapter`
  - e.g., `add_event_participant`, `remove_event_participant`, `get_event_participants`
- FK-safe: refuse with error if dependent data exists rather than cascade-deleting

### Delete tools on existing domains
- All 18 existing tool modules get delete tools for their tables
- This includes all `upsert_*` and `log_*` tools — each gets a corresponding `delete_{entity}`
- Existing examples to add: `delete_character`, `delete_relationship`, `delete_chapter`, `delete_scene`, `delete_scene_goal`, `delete_location`, `delete_faction`, `delete_event`, `delete_plot_thread`, `delete_arc_beat`, `delete_canon_fact`, `delete_continuity_issue`, `delete_foreshadowing_entry`, `delete_motif_occurrence`, `delete_chekov`, `delete_dramatic_irony`, `delete_open_question`, `delete_decision`, `delete_voice_profile`, `delete_voice_drift`, `delete_publishing_asset`, `delete_submission`, `delete_name_registry_entry`, `delete_perception_profile`, `delete_reader_state`, `delete_pov_position`, `delete_magic_use_log_entry`, `delete_story_structure`, `delete_session_log`, `delete_agent_run_log`, `delete_project_snapshot`, `delete_arc_health_log`

### Error contract (carried from Phase 13 / v1.0)
- All new write tools implement the established error contract: `null` for not-found, `is_valid: false` for validation failures, `requires_action` for gate violations
- Delete tools: return `null` if the record doesn't exist (idempotent), return FK-conflict error if dependent records block deletion

### Claude's Discretion
- Which module each new table's tools live in (world.py expansion vs new module for books/acts/eras)
- Whether to add `list_*` to every table or only browsable entity tables (junction/log tables may not need listing)
- Exact argument shape for junction tools (positional IDs vs keyword)
- Whether to add `get_current_*` helpers beyond character state tables

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `check_gate()` helper in `novel.mcp` — call in any gate-blocked write tool; already used by upsert tools
- `register(mcp: FastMCP) -> None` pattern — all 18 modules use this; new tools follow same structure
- Error contract helpers (null, is_valid, requires_action shapes) — established across all existing tools; follow same patterns

### Established Patterns
- `upsert_*` — create-or-update by primary key or natural key; returns the upserted record
- `log_*` — append-only insert for historical/event records; returns the new record id
- `get_*` — single record lookup; returns `null` if not found
- `list_*` — browsable entity list; returns list (empty list for no results, not null)
- `delete_*` — hard delete by id; returns `null` if not found (idempotent), error dict if FK conflict

### Integration Points
- New world-building tools → `src/novel/tools/world.py` (already has locations, factions, cultures)
- Character state tools → `src/novel/tools/characters.py` (already has beliefs, injuries, locations read tools)
- Literary planning tools → `src/novel/tools/foreshadowing.py` and `src/novel/tools/knowledge.py`
- Junction tools → either parent entity's module or a new junctions module (planner decides)
- Books/acts/eras → `src/novel/tools/world.py` or new `structure_meta.py` module

### Scope Assessment
- ~30+ new delete tools across 18 existing modules
- ~15-20 new tables need at least one new tool (read or write)
- ~4 junction tables need new dedicated association tools
- Total new tools estimate: 60–80 tools, bringing total from 103 to ~165–183
- Plan should be broken into multiple parallel execution waves by domain

</code_context>

<specifics>
## Specific Ideas

- "All tools are full CRUD — including delete. Make sure to respect Foreign Keys so we don't have orphaned records"
- Hard delete (no soft delete) — git tracks history for recovery if needed
- FK-safe: refuse with clear error message rather than cascade-delete
- Delete naming convention: always `delete_{table_singular}`, no exceptions

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 14-mcp-api-completeness*
*Context gathered: 2026-03-09*
