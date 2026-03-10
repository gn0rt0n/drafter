# Phase 14: MCP API Completeness - Research

**Researched:** 2026-03-09
**Domain:** FastMCP tool authoring — SQLite FK-safe delete pattern, full CRUD coverage audit
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- Only two tables are intentionally read-only: `schema_migrations` (managed by migration runner) and `architecture_gate` (managed exclusively through the `certify_gate` tool flow)
- All other 69 tables get full CRUD: read, list, upsert/log, delete
- World-building tables previously treated as seed-only (`eras`, `cultures`, `magic_system_elements`, `supernatural_elements`, `practitioner_abilities`, `supernatural_voice_guidelines`) are writable — Claude Code should be able to create/update world-building entries during active novel work
- Auto-generated tables (`chapter_structural_obligations`, `pov_balance_snapshots`) and dev-internal tables (`documentation_tasks`, `research_notes`) also get write tools — policy is "all non-system tables are writable"
- Every non-system table gets: `get_{entity}`, `list_{entities}` (where browsable), `upsert_{entity}` or `log_{entity}` (append-only log for historical state), `delete_{entity}`
- Hard deletes only — no soft delete / `deleted_at` pattern
- FK-safe deletes: if deleting a row would orphan records in dependent tables, refuse with a clear error message describing the FK constraint; do NOT cascade
- Delete tool naming: always `delete_{table_singular}` (e.g., `delete_canon_fact`, `delete_character`, `delete_arc_beat`)
- `character_beliefs`, `character_locations`, `injury_states`, `title_states` use the `log_*` pattern; also add `get_current_*` helper where useful
- `books`, `acts`, `eras` have zero MCP tools; add full CRUD
- `artifacts` has NO tools at all — full CRUD in world.py
- `supernatural_elements`, `object_states`, `pacing_beats`, `tension_measurements`, `reader_experience_notes`, `documentation_tasks`, `research_notes` — full CRUD
- `motif_registry` — add `upsert_motif` + `delete_motif`
- `thematic_mirrors`, `opposition_pairs`, `prophecy_registry`, `reader_reveals` — add upsert + delete
- `subplot_touchpoint_log` — add `log_subplot_touchpoint` + `delete_subplot_touchpoint`
- `faction_political_states` — add `log_faction_political_state` + `delete_faction_political_state`
- `chapter_plot_threads`, `chapter_character_arcs`, `event_participants`, `event_artifacts` get dedicated association tools: `link_{a}_to_{b}` / `unlink_{a}_from_{b}` + `get_{b}s_for_{a}`
- All 18 existing tool modules get delete tools for their tables
- Error contract: `null` for not-found, `is_valid: false` for validation failures, `requires_action` for gate violations
- Delete tools: return `null` if record doesn't exist (idempotent), return FK-conflict error dict if dependent records block deletion

### Claude's Discretion

- Which module each new table's tools live in (world.py expansion vs new module for books/acts/eras)
- Whether to add `list_*` to every table or only browsable entity tables (junction/log tables may not need listing)
- Exact argument shape for junction tools (positional IDs vs keyword)
- Whether to add `get_current_*` helpers beyond character state tables

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| MCP-01 | Every schema table either has an MCP write tool, or is documented as intentionally read-only with justification | Full 71-table audit below documents current coverage gaps and prescribes new tools |
| MCP-02 | New write tools implement the established error contract (null for not-found, is_valid: false for validation failures, requires_action for gate violations) | Error contract shapes verified in shared.py; delete pattern with FK-safe refuse documented |
</phase_requirements>

## Summary

Phase 14 is an API completeness sweep across 71 schema tables. The codebase has 18 tool modules (~103 existing tools), all following the `register(mcp: FastMCP) -> None` pattern. The critical gap is that **zero delete tools exist** anywhere in the codebase, and several entire entity domains have no tools at all: `books`, `acts`, `eras`, `artifacts`, and several literary/tracking tables.

The work divides into three categories: (1) add delete tools to all 18 existing modules — roughly 30+ deletes matching the existing upsert/log tools; (2) add full CRUD for the ~15 tables with zero or partial coverage; (3) add dedicated junction/association tools for 4 junction tables. The existing error contract (`NotFoundResponse`, `ValidationFailure`, `GateViolation`) is established in `novel/models/shared.py` and used consistently — all new tools follow the same shapes.

**Primary recommendation:** Plan in parallel domain waves since modules are independent. Tackle delete-tool additions to existing modules in one wave, new entity CRUD in a second wave, and junction/association tools in a third wave. The FK-safe delete pattern (catch `IntegrityError`, return a descriptive error dict) is the only new code pattern introduced this phase.

## Complete 71-Table Audit

### System Tables (Read-Only — Intentional)

| Table | Justification |
|-------|--------------|
| `schema_migrations` | Managed by migration runner (`novel db migrate`); no user writes |
| `architecture_gate` | Managed exclusively via `certify_gate` tool flow; users never write directly |

### Tables With Existing FULL CRUD (read + write, missing only delete)

These tables have get/list + upsert/log tools already. **Only delete tool is missing.**

| Table | Module | Existing Tools | Missing |
|-------|--------|---------------|---------|
| `characters` | characters.py | get_character, list_characters, upsert_character | delete_character |
| `character_knowledge` | characters.py | get_character_knowledge, log_character_knowledge | delete_character_knowledge |
| `character_relationships` | relationships.py | get_relationship, list_relationships, upsert_relationship | delete_relationship |
| `relationship_change_events` | relationships.py | log_relationship_change | delete_relationship_change |
| `perception_profiles` | relationships.py | get_perception_profile, upsert_perception_profile | delete_perception_profile |
| `chapters` | chapters.py | get_chapter, list_chapters, upsert_chapter | delete_chapter |
| `scenes` | scenes.py | get_scene, upsert_scene | delete_scene |
| `scene_character_goals` | scenes.py | get_scene_character_goals, upsert_scene_goal | delete_scene_goal |
| `locations` | world.py | get_location, upsert_location | delete_location |
| `factions` | world.py | get_faction, upsert_faction | delete_faction |
| `events` | timeline.py | get_event, list_events, upsert_event | delete_event |
| `pov_chronological_position` | timeline.py | get_pov_position, get_pov_positions, upsert_pov_position | delete_pov_position |
| `plot_threads` | plot.py | get_plot_thread, list_plot_threads, upsert_plot_thread | delete_plot_thread |
| `character_arcs` | arcs.py | get_arc | delete_arc (upsert_arc also missing) |
| `arc_health_log` | arcs.py | get_arc_health, log_arc_health | delete_arc_health_log |
| `chekovs_gun_registry` | arcs.py | get_chekovs_guns, upsert_chekov | delete_chekov |
| `foreshadowing_registry` | foreshadowing.py | get_foreshadowing, log_foreshadowing | delete_foreshadowing |
| `motif_occurrences` | foreshadowing.py | get_motif_occurrences, log_motif_occurrence | delete_motif_occurrence |
| `canon_facts` | canon.py | get_canon_facts, log_canon_fact | delete_canon_fact |
| `continuity_issues` | canon.py | get_continuity_issues, log_continuity_issue | delete_continuity_issue |
| `decisions_log` | canon.py | get_decisions, log_decision | delete_decision |
| `reader_information_states` | knowledge.py | get_reader_state, upsert_reader_state | delete_reader_state |
| `dramatic_irony_inventory` | knowledge.py | get_dramatic_irony_inventory, log_dramatic_irony | delete_dramatic_irony |
| `voice_profiles` | voice.py | get_voice_profile, upsert_voice_profile | delete_voice_profile |
| `voice_drift_log` | voice.py | get_voice_drift_log, log_voice_drift | delete_voice_drift |
| `publishing_assets` | publishing.py | get_publishing_assets, upsert_publishing_asset | delete_publishing_asset |
| `submission_tracker` | publishing.py | get_submissions, log_submission, update_submission | delete_submission |
| `session_logs` | session.py | get_last_session (+ start_session which creates) | delete_session_log |
| `agent_run_log` | session.py | log_agent_run | delete_agent_run_log |
| `open_questions` | session.py | get_open_questions, log_open_question | delete_open_question |
| `project_metrics_snapshots` | session.py | get_project_metrics, log_project_snapshot | delete_project_snapshot |
| `story_structure` | structure.py | get_story_structure, upsert_story_structure | delete_story_structure |
| `arc_seven_point_beats` | structure.py | get_arc_beats, upsert_arc_beat | delete_arc_beat |
| `magic_use_log` | magic.py | log_magic_use | delete_magic_use_log |
| `travel_segments` | timeline.py | get_travel_segments | delete_travel_segment (upsert also missing) |

### Tables With PARTIAL Coverage (read only, missing write tools)

| Table | Module | Existing | Missing |
|-------|--------|---------|---------|
| `cultures` | world.py | get_culture | upsert_culture, list_cultures, delete_culture |
| `faction_political_states` | world.py | get_faction_political_state | log_faction_political_state, delete_faction_political_state |
| `motif_registry` | foreshadowing.py | get_motifs | upsert_motif, delete_motif |
| `prophecy_registry` | foreshadowing.py | get_prophecies | upsert_prophecy, delete_prophecy |
| `thematic_mirrors` | foreshadowing.py | get_thematic_mirrors | upsert_thematic_mirror, delete_thematic_mirror |
| `opposition_pairs` | foreshadowing.py | get_opposition_pairs | upsert_opposition_pair, delete_opposition_pair |
| `reader_reveals` | knowledge.py | get_reader_reveals | upsert_reader_reveal, delete_reader_reveal |
| `magic_system_elements` | magic.py | get_magic_element | upsert_magic_element, list_magic_elements, delete_magic_element |
| `practitioner_abilities` | magic.py | get_practitioner_abilities | upsert_practitioner_ability, delete_practitioner_ability |
| `supernatural_voice_guidelines` | voice.py | get_supernatural_voice_guidelines | upsert_supernatural_voice_guideline, delete_supernatural_voice_guideline |
| `name_registry` | names.py | check_name, get_name_registry | upsert_name_registry_entry, delete_name_registry_entry |
| `chapter_structural_obligations` | chapters.py | get_chapter_obligations | upsert_chapter_obligation, delete_chapter_obligation |
| `subplot_touchpoint_log` | arcs.py | get_subplot_touchpoint_gaps (analysis only) | log_subplot_touchpoint, delete_subplot_touchpoint |
| `character_beliefs` | characters.py | get_character_beliefs | log_character_belief, delete_character_belief |
| `character_locations` | characters.py | get_character_location | log_character_location, delete_character_location |
| `injury_states` | characters.py | get_character_injuries | log_injury_state, delete_injury_state |
| `pov_balance_snapshots` | session.py | get_pov_balance | log_pov_balance_snapshot, delete_pov_balance_snapshot |

### Tables With ZERO Coverage (no tools at all)

| Table | Belongs In | Required Tools |
|-------|-----------|----------------|
| `books` | world.py or new meta module | get_book, list_books, upsert_book, delete_book |
| `acts` | world.py or new meta module | get_act, list_acts, upsert_act, delete_act |
| `eras` | world.py or new meta module | get_era, list_eras, upsert_era, delete_era |
| `artifacts` | world.py | get_artifact, list_artifacts, upsert_artifact, delete_artifact |
| `supernatural_elements` | magic.py or world.py | get_supernatural_element, list_supernatural_elements, upsert_supernatural_element, delete_supernatural_element |
| `object_states` | world.py or timeline.py | get_object_states, log_object_state, delete_object_state |
| `pacing_beats` | scenes.py or session.py | get_pacing_beats, log_pacing_beat, delete_pacing_beat |
| `tension_measurements` | scenes.py or session.py | get_tension_measurements, log_tension_measurement, delete_tension_measurement |
| `reader_experience_notes` | knowledge.py | get_reader_experience_notes, log_reader_experience_note, delete_reader_experience_note |
| `title_states` | characters.py | get_title_states, log_title_state, delete_title_state |
| `documentation_tasks` | publishing.py | get_documentation_tasks, upsert_documentation_task, delete_documentation_task |
| `research_notes` | publishing.py | get_research_notes, upsert_research_note, delete_research_note |

### Junction Tables (need association tools, not plain CRUD)

| Table | Current Coverage | Required Tools |
|-------|-----------------|----------------|
| `chapter_plot_threads` | None | link_chapter_to_plot_thread, unlink_chapter_from_plot_thread, get_plot_threads_for_chapter |
| `chapter_character_arcs` | None | link_chapter_to_arc, unlink_chapter_from_arc, get_arcs_for_chapter |
| `event_participants` | None | add_event_participant, remove_event_participant, get_event_participants |
| `event_artifacts` | None | add_event_artifact, remove_event_artifact, get_event_artifacts |
| `gate_checklist_items` | get_gate_checklist (read only) | Managed by gate system — write via certify_gate; add delete_gate_checklist_item for cleanup |

### Missing Upsert on Arc

`character_arcs` has `get_arc` and `get_arc_health` but no upsert. An `upsert_arc` tool is needed alongside `delete_arc` — without it there is no way to create arcs from Claude Code.

### Missing Upsert on Travel Segments

`travel_segments` has `get_travel_segments` and `validate_travel_realism` (read/compute) but no write tool. Add `log_travel_segment` (append-only, travel events are discrete) + `delete_travel_segment`.

## Standard Stack

### Core (all verified from codebase — HIGH confidence)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `mcp.server.fastmcp` | bundled with mcp>=1.26.0 | MCP tool registration | Already established; all 18 modules use it |
| `aiosqlite` | established | Async SQLite | `get_connection()` context manager wraps it |
| `pydantic` | >=2.11 | Return type models | All existing tools return Pydantic models |

### Error Contract Types (verified in `src/novel/models/shared.py`)

```python
class NotFoundResponse(BaseModel):
    not_found_message: str

class ValidationFailure(BaseModel):
    is_valid: bool = False
    errors: list[str]

class GateViolation(BaseModel):
    requires_action: str
```

### No New Dependencies Needed

Phase 14 adds zero new Python dependencies. All patterns are established in the existing codebase.

## Architecture Patterns

### Recommended Module Assignments (Claude's Discretion)

Based on existing module structure:

| New Domain | Recommended Module | Rationale |
|-----------|-------------------|-----------|
| books, acts, eras | world.py | Already has factions, locations, cultures — narrative structure fits; OR new `meta.py` if world.py grows unwieldy |
| artifacts, object_states | world.py | Artifacts are world entities alongside locations |
| supernatural_elements | magic.py | Naturally pairs with magic_system_elements |
| pacing_beats, tension_measurements | scenes.py | Scene-level pacing belongs with scene tools |
| reader_experience_notes | knowledge.py | Reader-facing data alongside reader_reveals, reader_state |
| documentation_tasks, research_notes | publishing.py | Already has ResearchNote, DocumentationTask Pydantic models |
| junction tools (chapter_plot_threads, chapter_character_arcs) | plot.py / arcs.py respectively | Junction belongs with the "many" side entity |
| event_participants, event_artifacts | timeline.py | Event-scoped associations belong with events |

### Pattern 1: FK-Safe Delete (NEW pattern this phase)

**What:** Delete a record only if no other tables reference it via FK. When FK constraint would be violated, return a descriptive error dict instead of raising.

**When to use:** Every delete tool for any table that other tables FK into.

**The SQLite behavior:** With `PRAGMA foreign_keys=ON` (already set in `get_connection()`), attempting to `DELETE` a parent row that has child rows raises `aiosqlite.IntegrityError` with message containing "FOREIGN KEY constraint failed". Catch this and return a `ValidationFailure`.

```python
# Source: verified from existing get_connection() in src/novel/mcp/db.py
# and SQLite FK enforcement behavior (HIGH confidence)

@mcp.tool()
async def delete_character(character_id: int) -> NotFoundResponse | ValidationFailure | dict:
    """Delete a character by ID.

    Returns null-equivalent if not found (idempotent). Returns ValidationFailure
    if dependent records exist in scenes, character_relationships, etc.

    Args:
        character_id: Primary key of the character to delete.

    Returns:
        {"deleted": True, "id": character_id} on success.
        NotFoundResponse if the character does not exist.
        ValidationFailure if dependent records block deletion.
    """
    async with get_connection() as conn:
        row = await conn.execute_fetchall(
            "SELECT id FROM characters WHERE id = ?", (character_id,)
        )
        if not row:
            return NotFoundResponse(not_found_message=f"Character {character_id} not found")
        try:
            await conn.execute("DELETE FROM characters WHERE id = ?", (character_id,))
            await conn.commit()
            return {"deleted": True, "id": character_id}
        except Exception as exc:
            logger.error("delete_character failed: %s", exc)
            return ValidationFailure(is_valid=False, errors=[str(exc)])
```

**Key insight:** The pre-existence check with `NotFoundResponse` (for the "not found" case) and the FK `IntegrityError` catch (for the "has dependents" case) together implement the specified error contract.

### Pattern 2: Log-Only Delete (append-only tables)

For tables with `log_*` tools (no unique key, audit trail semantics): still add delete so erroneous entries can be corrected, but the return is simpler since there are no FK children in most log tables.

```python
# Pattern for log tables like arc_health_log, voice_drift_log, magic_use_log
@mcp.tool()
async def delete_arc_health_log(arc_health_log_id: int) -> NotFoundResponse | dict:
    async with get_connection() as conn:
        row = await conn.execute_fetchall(
            "SELECT id FROM arc_health_log WHERE id = ?", (arc_health_log_id,)
        )
        if not row:
            return NotFoundResponse(not_found_message=f"Arc health log {arc_health_log_id} not found")
        await conn.execute("DELETE FROM arc_health_log WHERE id = ?", (arc_health_log_id,))
        await conn.commit()
        return {"deleted": True, "id": arc_health_log_id}
```

### Pattern 3: Junction Association Tools

**What:** Dedicated link/unlink tools for M:N junction tables with UNIQUE(a_id, b_id) constraints.

```python
# Source: verified from existing junction table schemas in migrations
@mcp.tool()
async def link_chapter_to_plot_thread(
    chapter_id: int,
    plot_thread_id: int,
    thread_role: str = "advance",
    notes: str | None = None,
) -> ChapterPlotThread | NotFoundResponse | ValidationFailure:
    """Link a chapter to a plot thread."""
    async with get_connection() as conn:
        # verify both FKs exist first
        ch = await conn.execute_fetchall("SELECT id FROM chapters WHERE id = ?", (chapter_id,))
        if not ch:
            return NotFoundResponse(not_found_message=f"Chapter {chapter_id} not found")
        pt = await conn.execute_fetchall("SELECT id FROM plot_threads WHERE id = ?", (plot_thread_id,))
        if not pt:
            return NotFoundResponse(not_found_message=f"Plot thread {plot_thread_id} not found")
        try:
            cursor = await conn.execute(
                "INSERT INTO chapter_plot_threads (chapter_id, plot_thread_id, thread_role, notes) "
                "VALUES (?, ?, ?, ?) ON CONFLICT(chapter_id, plot_thread_id) DO UPDATE SET "
                "thread_role=excluded.thread_role, notes=excluded.notes",
                (chapter_id, plot_thread_id, thread_role, notes),
            )
            await conn.commit()
            row = await conn.execute_fetchall(
                "SELECT * FROM chapter_plot_threads WHERE chapter_id=? AND plot_thread_id=?",
                (chapter_id, plot_thread_id),
            )
            return ChapterPlotThread(**dict(row[0]))
        except Exception as exc:
            return ValidationFailure(is_valid=False, errors=[str(exc)])

@mcp.tool()
async def unlink_chapter_from_plot_thread(
    chapter_id: int,
    plot_thread_id: int,
) -> NotFoundResponse | dict:
    async with get_connection() as conn:
        row = await conn.execute_fetchall(
            "SELECT id FROM chapter_plot_threads WHERE chapter_id=? AND plot_thread_id=?",
            (chapter_id, plot_thread_id),
        )
        if not row:
            return NotFoundResponse(
                not_found_message=f"No link between chapter {chapter_id} and plot thread {plot_thread_id}"
            )
        await conn.execute(
            "DELETE FROM chapter_plot_threads WHERE chapter_id=? AND plot_thread_id=?",
            (chapter_id, plot_thread_id),
        )
        await conn.commit()
        return {"unlinked": True, "chapter_id": chapter_id, "plot_thread_id": plot_thread_id}
```

### Pattern 4: Upsert for New Entity Tables

Same two-branch upsert used everywhere in the codebase. No new pattern needed — copy the shape from `upsert_character` or `upsert_location`.

```python
# Standard upsert branch logic (verified from upsert_character, upsert_faction, etc.)
# Branch on whether primary key is provided:
#   id=None  → plain INSERT, use cursor.lastrowid
#   id=N     → INSERT ... ON CONFLICT(id) DO UPDATE SET ..., select back by id
# Always: SELECT back after insert/update and return Pydantic model
# Always: wrap in try/except Exception; return ValidationFailure on error
```

### Pattern 5: Gate-Gated vs. Non-Gated Write Tools

**Which new tools need `check_gate(conn)`?**

Matching existing module behavior:
- **Gate-gated** (call `check_gate` at top): all tools in foreshadowing.py, knowledge.py, session.py, canon.py, voice.py — these are prose-phase tools
- **Not gated**: characters.py, world.py, magic.py, arcs.py, plot.py, chapters.py, scenes.py, structure.py, timeline.py, relationships.py, names.py, publishing.py

New tools added to existing modules follow the module's existing gate policy.

### Anti-Patterns to Avoid

- **Cascade delete:** Never. Always refuse with FK error instead.
- **print() calls:** Never in MCP tool code — corrupts stdio protocol. Use `logger.error()`.
- **Missing `await conn.commit()`:** Every write operation must commit. Reads do not need commit.
- **Not selecting back after insert:** Always select the row back and return a typed Pydantic model, not just `{"id": new_id}`.
- **Missing FK pre-check:** For log tools that take FK references, check the referenced row exists before inserting. See `log_magic_use` → checks chapter exists before insert.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| FK constraint detection | Custom FK query | Let SQLite raise IntegrityError with `PRAGMA foreign_keys=ON` (already set) | Already enabled in get_connection(); catching the exception is the correct pattern |
| Soft delete tracking | `deleted_at` column | Hard delete only | Schema has no deleted_at columns; adding them everywhere is out of scope |
| Row existence check | Complex EXISTS subquery | `SELECT id FROM table WHERE id = ?` and check empty result | Already the established pattern across all existing tools |
| Return type serialization | Custom JSON dict building | Pydantic model `**dict(row[0])` | Already works with aiosqlite.Row + Pydantic v2 |

## Common Pitfalls

### Pitfall 1: `lastrowid` Returns 0 on Conflict

**What goes wrong:** When using `ON CONFLICT ... DO UPDATE`, if the row already exists and SQLite updates it, `cursor.lastrowid` can return 0 (not the real row id).

**Why it happens:** SQLite `lastrowid` is undefined behavior on UPDATE branch of upsert.

**How to avoid:** After the upsert, SELECT the row back by the unique key rather than by `lastrowid`. See `upsert_faction` (no id branch): "always re-query by name" comment. For id-based upserts: select back by the provided id.

**Warning signs:** Tools returning id=0 in the model.

### Pitfall 2: Missing Gate Call in Prose-Phase Delete Tools

**What goes wrong:** A delete tool in foreshadowing.py or knowledge.py forgets to call `check_gate(conn)` at the top, allowing deletes before the gate is certified.

**How to avoid:** Match the existing module's gate policy exactly. Every tool in gate-gated modules must call check_gate.

### Pitfall 3: Self-Referencing FK in Delete

**What goes wrong:** `canon_facts` has `parent_fact_id INTEGER REFERENCES canon_facts(id)` (self-ref). Deleting a parent fact that has children will raise an FK error even though both rows are in the same table.

**How to avoid:** The FK catch-and-refuse pattern handles this correctly — the error message from SQLite will indicate the constraint. No special handling needed.

### Pitfall 4: Acts Circular FK (Not Truly Circular)

**What goes wrong:** `acts.start_chapter_id` and `acts.end_chapter_id` reference `chapters(id)`, and `chapters` doesn't reference `acts`. This looks circular but isn't — it's just nullable FKs.

**How to avoid:** `upsert_act` can safely pass `start_chapter_id=None` and `end_chapter_id=None` on initial create. No special handling needed; the nullable design is intentional.

### Pitfall 5: `gate_checklist_items` FK to `architecture_gate`

**What goes wrong:** Attempting to add a `delete_gate_checklist_item` tool when `gate_checklist_items` references `architecture_gate(id)`. Both tables are gate-managed.

**How to avoid:** The decisions are clear — `gate_checklist_items` is managed by the gate system. If adding a delete for cleanup, it goes in gate.py alongside `certify_gate`. Clarify: `gate_checklist_items` is not system-read-only per policy (only `schema_migrations` and `architecture_gate` are). So add `delete_gate_checklist_item` to gate.py.

### Pitfall 6: `execute_fetchall` vs. `async with conn.execute` cursor pattern

**What goes wrong:** Mixing the two async patterns for reading rows leads to inconsistent code that may hold cursors open.

**How to avoid:** Both patterns work in aiosqlite. The codebase uses both:
- `conn.execute_fetchall(sql, params)` — convenience helper, returns list of rows
- `async with conn.execute(sql) as cursor: rows = await cursor.fetchall()` — explicit cursor

Either is fine. Prefer `execute_fetchall` for SELECT (matches most existing tools in the codebase).

### Pitfall 7: Missing `upsert_arc` Alongside `delete_arc`

**What goes wrong:** Adding `delete_arc` but forgetting that `character_arcs` has no upsert tool. Claude Code would be able to delete arcs but not create them.

**How to avoid:** Include `upsert_arc` in the same plan/task as `delete_arc`.

## Code Examples

### Complete Delete Tool with FK Safety

```python
# Pattern for entities that other tables reference (HIGH confidence — derived from
# existing get_connection() FK enforcement and established ValidationFailure pattern)

@mcp.tool()
async def delete_chapter(chapter_id: int) -> NotFoundResponse | ValidationFailure | dict:
    """Delete a chapter by ID.

    Refuses if scenes, acts (start/end chapter), or other tables reference
    this chapter — returns ValidationFailure with the constraint description.
    Idempotent: returns NotFoundResponse if chapter does not exist.

    Args:
        chapter_id: Primary key of the chapter to delete.

    Returns:
        {"deleted": True, "id": chapter_id} on success.
        NotFoundResponse if the chapter does not exist.
        ValidationFailure if dependent records block deletion.
    """
    async with get_connection() as conn:
        row = await conn.execute_fetchall(
            "SELECT id FROM chapters WHERE id = ?", (chapter_id,)
        )
        if not row:
            return NotFoundResponse(
                not_found_message=f"Chapter {chapter_id} not found"
            )
        try:
            await conn.execute("DELETE FROM chapters WHERE id = ?", (chapter_id,))
            await conn.commit()
            return {"deleted": True, "id": chapter_id}
        except Exception as exc:
            logger.error("delete_chapter failed: %s", exc)
            return ValidationFailure(is_valid=False, errors=[str(exc)])
```

### New Entity Upsert (books — zero-coverage table)

```python
# Pattern: two-branch upsert matching upsert_character / upsert_faction conventions

@mcp.tool()
async def upsert_book(
    book_id: int | None,
    title: str,
    series_order: int | None = None,
    word_count_target: int | None = None,
    actual_word_count: int = 0,
    status: str = "planning",
    notes: str | None = None,
    canon_status: str = "draft",
) -> Book | ValidationFailure:
    """Create or update a book record."""
    async with get_connection() as conn:
        try:
            if book_id is None:
                cursor = await conn.execute(
                    """INSERT INTO books (title, series_order, word_count_target,
                       actual_word_count, status, notes, canon_status, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))""",
                    (title, series_order, word_count_target,
                     actual_word_count, status, notes, canon_status),
                )
                new_id = cursor.lastrowid
                await conn.commit()
                row = await conn.execute_fetchall(
                    "SELECT * FROM books WHERE id = ?", (new_id,)
                )
            else:
                await conn.execute(
                    """INSERT INTO books (id, title, series_order, word_count_target,
                       actual_word_count, status, notes, canon_status, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                       ON CONFLICT(id) DO UPDATE SET
                           title=excluded.title,
                           series_order=excluded.series_order,
                           word_count_target=excluded.word_count_target,
                           actual_word_count=excluded.actual_word_count,
                           status=excluded.status,
                           notes=excluded.notes,
                           canon_status=excluded.canon_status,
                           updated_at=datetime('now')""",
                    (book_id, title, series_order, word_count_target,
                     actual_word_count, status, notes, canon_status),
                )
                await conn.commit()
                row = await conn.execute_fetchall(
                    "SELECT * FROM books WHERE id = ?", (book_id,)
                )
            return Book(**dict(row[0]))
        except Exception as exc:
            logger.error("upsert_book failed: %s", exc)
            return ValidationFailure(is_valid=False, errors=[str(exc)])
```

### Existing Pydantic Models Available (No New Models Needed for Most Tables)

All Pydantic models exist already — the audit confirmed this by checking `src/novel/models/`:

| Table | Existing Model | Module |
|-------|---------------|--------|
| `books` | `Book` | world.py |
| `eras` | `Era` | world.py |
| `acts` | `Act` | world.py |
| `artifacts` | `Artifact` | world.py |
| `object_states` | `ObjectState` | world.py |
| `supernatural_elements` | `SupernaturalElement` | magic.py |
| `pacing_beats` | `PacingBeat` | pacing.py |
| `tension_measurements` | `TensionMeasurement` | pacing.py |
| `title_states` | `TitleState` | characters.py |
| `reader_experience_notes` | `ReaderExperienceNote` | canon.py |
| `documentation_tasks` | `DocumentationTask` | publishing.py |
| `research_notes` | `ResearchNote` | publishing.py |
| `chapter_plot_threads` | `ChapterPlotThread` | plot.py |
| `chapter_character_arcs` | `ChapterCharacterArc` | plot.py |
| `event_participants` | `EventParticipant` | timeline.py |
| `event_artifacts` | `EventArtifact` | timeline.py |

**Zero new Pydantic models need to be created.** Every table maps to an existing model.

## FK Dependency Graph — Delete Order Matters

Tables that are referenced by many others must be deleted last (or refused if still referenced). Key FKs to know:

```
books  ←  acts (book_id)
       ←  story_structure (book_id)

chapters  ←  scenes (chapter_id)
          ←  acts (start_chapter_id, end_chapter_id — nullable)
          ←  character_knowledge (chapter_id)
          ←  character_beliefs (formed_chapter_id, challenged_chapter_id)
          ←  character_locations (chapter_id)
          ←  injury_states (chapter_id)
          ←  title_states (chapter_id)
          ←  pacing_beats (chapter_id)
          ←  tension_measurements (chapter_id)
          ←  chapter_plot_threads (chapter_id)
          ←  chapter_character_arcs (chapter_id)
          ←  ... many more

characters  ←  character_relationships (character_id_a, character_id_b)
            ←  character_knowledge, character_beliefs, character_locations
            ←  injury_states, title_states
            ←  voice_profiles, voice_drift_log
            ←  magic_use_log, practitioner_abilities
            ←  event_participants
            ←  perception_profiles
            ←  character_arcs

factions  ←  faction_political_states (faction_id)
          ←  characters (faction_id — nullable)

artifacts  ←  object_states (artifact_id)
           ←  event_artifacts (artifact_id)

plot_threads  ←  chapter_plot_threads (plot_thread_id)
              ←  subplot_touchpoint_log (plot_thread_id)

character_arcs  ←  chapter_character_arcs (arc_id)
                ←  arc_health_log (arc_id)
                ←  arc_seven_point_beats (arc_id)
```

**The FK-safe refuse pattern handles all of this automatically** — no need to implement cascades or ordering. SQLite raises `IntegrityError` with FK details; tools catch and return `ValidationFailure`.

## Scope Summary: Tool Count Estimate

| Category | Count Estimate |
|----------|---------------|
| Delete tools for existing upsert/log entities | ~35 delete tools |
| New write tools for partial-coverage tables (upsert/log + delete) | ~25 tools |
| New full CRUD for zero-coverage tables | ~35–40 tools (books/acts/eras/artifacts + others) |
| Junction association tools | ~12–15 tools (link/unlink/get for 4 junction tables) |
| Utility (upsert_arc, log_travel_segment) | ~4 tools |
| **Total new tools** | **~111–120 tools** |
| **Current tool count** | ~103 |
| **Projected total** | **~214–223** |

Note: CONTEXT.md estimated 60–80 new tools. After full audit the number is higher (~111–120) because several partial-coverage tables need both a write tool AND a delete tool counted separately, and zero-coverage tables require 3–4 tools each.

## Planning Recommendations

### Suggested Wave Structure (Parallel)

**Wave 1 — Delete Tools on Existing Modules (30+ tools, pure additions, low risk)**
- Assign by module: arcs.py, canon.py, chapters.py, foreshadowing.py, knowledge.py, magic.py, names.py, plot.py, publishing.py, relationships.py, scenes.py, session.py, structure.py, timeline.py, voice.py, world.py
- Each task = "add delete tools to module X"
- All follow FK-safe delete pattern

**Wave 2 — New Write Tools for Partial-Coverage Tables (gate-gated and non-gated)**
- Cultures upsert/delete, faction_political_states log/delete
- Motif upsert/delete, prophecy upsert/delete, thematic_mirrors upsert/delete, opposition_pairs upsert/delete
- Reader reveals upsert/delete, reader_experience_notes CRUD
- Magic element upsert/delete, practitioner ability upsert/delete, supernatural_voice_guidelines upsert/delete
- Name registry upsert/delete
- Character state log tools (beliefs, locations, injury, title)
- Chapter obligations upsert/delete, subplot touchpoint log/delete, arc upsert
- Travel segment log/delete, pov_balance_snapshot log/delete

**Wave 3 — Zero-Coverage Tables (new CRUD domains)**
- books, acts, eras: full CRUD (planner decides: add to world.py or new module)
- artifacts: full CRUD in world.py
- supernatural_elements: full CRUD in magic.py
- object_states: full CRUD
- pacing_beats, tension_measurements: full CRUD
- documentation_tasks, research_notes: full CRUD

**Wave 4 — Junction Association Tools**
- chapter_plot_threads: link/unlink/get
- chapter_character_arcs: link/unlink/get
- event_participants: add/remove/get
- event_artifacts: add/remove/get
- gate_checklist_items: delete (for cleanup)

## Open Questions

1. **Module placement for books/acts/eras**
   - What we know: these are fundamental narrative containers; world.py already has factions, cultures, locations
   - What's unclear: whether world.py becomes too large (300+ lines currently) with 12+ new tools
   - Recommendation: planner decides; if world.py exceeds ~600 lines, split to new `meta.py`

2. **`get_current_*` helpers beyond character state**
   - What we know: CONTEXT.md mentions adding these for character state tables (location, injury)
   - What's unclear: whether faction_political_states, object_states also warrant `get_current_*` helpers
   - Recommendation: add `get_current_faction_political_state` and `get_current_object_state` — same pattern, same value

3. **`list_*` for log tables**
   - What we know: CONTEXT.md gives planner discretion on whether log tables need `list_*`
   - Recommendation: log tables (append-only, no unique key) do NOT need `list_*` — use existing pattern of `get_*` with filter params; entity tables with browsable content DO get `list_*`

4. **`gate_checklist_items` write tools**
   - What we know: not listed as system-read-only in CONTEXT.md (only schema_migrations and architecture_gate are)
   - What's unclear: whether checklist items should be user-deleteable or only gate-managed
   - Recommendation: add `delete_gate_checklist_item` to gate.py for cleanup; no upsert (checklist items are created by `certify_gate` logic)

## Sources

### Primary (HIGH confidence)
- `src/novel/models/shared.py` — NotFoundResponse, ValidationFailure, GateViolation shapes
- `src/novel/mcp/db.py` — get_connection() with PRAGMA foreign_keys=ON
- `src/novel/mcp/gate.py` — check_gate() helper
- `src/novel/migrations/001–022` — all 71 table schemas and FK relationships
- `src/novel/models/*.py` — all 14 Pydantic model files, confirmed all models exist
- `src/novel/tools/*.py` — all 18 tool modules, confirmed tool inventory
- `src/novel/tools/characters.py` — upsert pattern with two-branch INSERT
- `src/novel/tools/world.py` — upsert_faction ON CONFLICT(name) pattern; sensory_profile JSON serialization
- `src/novel/tools/foreshadowing.py` — gate-gated tools pattern
- `src/novel/tools/arcs.py` — log_arc_health append-only pattern; upsert_chekov pattern

### Secondary (MEDIUM confidence)
- SQLite documentation on `lastrowid` behavior on upsert conflicts — known behavior, verified against existing code comments in world.py ("lastrowid is 0 on conflict — always re-query by name")

## Metadata

**Confidence breakdown:**
- Table audit: HIGH — directly read all 22 migration files and all 18 tool modules; counts are exact
- Delete pattern: HIGH — SQLite FK behavior with `PRAGMA foreign_keys=ON` is well-established; pattern derived from existing try/except in upsert tools
- Tool count estimate: MEDIUM — count of new tools is approximate (depends on planner's list_* discretion decisions)
- Module placement (books/acts/eras): MEDIUM — Claude's discretion; either approach is valid

**Research date:** 2026-03-09
**Valid until:** Stable — no external dependencies; all patterns are internal to this codebase
