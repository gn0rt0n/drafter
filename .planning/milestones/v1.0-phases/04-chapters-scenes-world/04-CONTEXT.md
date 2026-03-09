# Phase 4: Chapters, Scenes & World - Context

**Gathered:** 2026-03-07
**Status:** Ready for planning

<domain>
## Phase Boundary

19 MCP tools across two domains: chapter/scene structure (CHAP-01–09) and world-building (WRLD-01–10). Covers retrieval and upsert for chapters, scenes, scene character goals, locations, factions, cultures, magic system elements, practitioner abilities, and magic use logging. Plot threads, character arcs, and the gate system are separate phases.

</domain>

<decisions>
## Implementation Decisions

### Tool module split
- 4 tool modules, matching the existing model file organization: `tools/chapters.py`, `tools/scenes.py`, `tools/world.py`, `tools/magic.py`
- `server.py` gets 4 more `register(mcp)` calls in sequence after Phase 3's two calls
- Each module exposes `register(mcp: FastMCP) -> None` — no deviation from the established pattern

### `get_chapter` vs `get_chapter_plan` distinction (CHAP-01 vs CHAP-02)
- `get_chapter` returns the full `Chapter` model row — all fields including hook notes and structural fields
- `get_chapter_plan` returns a focused writing-guidance subset: `{chapter_id, summary, opening_state, closing_state, opening_hook_note, closing_hook_note, structural_function, hook_strength_rating}` — a TypedDict or small Pydantic model
- Same pattern as `get_character` (full row) vs state tools like `get_character_injuries` (focused subset)

### `check_magic_compliance` behavior (WRLD-08)
- Inputs: `character_id: int`, `magic_element_id: int`, `action_description: str`
- Logic: Query `magic_system_elements` for rules/limitations/costs, query `practitioner_abilities` to check whether the character has the ability registered
- Returns a structured result: `{compliant: bool, violations: list[str], applicable_rules: list[str], character_has_ability: bool | None}`
- `compliant` is derived: True if no violations AND character_has_ability (when ability data exists)
- Does NOT write to `magic_use_log` — logging is a separate tool (`log_magic_use`, WRLD-07)
- This gives Claude structured data to reason about compliance without leaving judgment ambiguous

### Claude's Discretion
- All implementation details: SQL queries, row-to-model mapping, aiosqlite patterns
- Chapter plan response type (TypedDict vs small Pydantic model)
- Exact upsert conflict resolution logic for upsert_chapter, upsert_scene, upsert_scene_goal, upsert_location, upsert_faction
- Test fixture scope (session vs function level)
- Plan file split across the 3 plan slots

</decisions>

<specifics>
## Specific Ideas

No specific requirements — user delegated all implementation decisions. Open to standard approaches following Phase 3 patterns.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `novel.mcp.db.get_connection()`: async context manager — every tool uses this unchanged
- `novel.mcp.server.mcp`: FastMCP instance, already has characters and relationships registered
- `novel.models.chapters`: `Chapter`, `ChapterStructuralObligation` — ready for use
- `novel.models.scenes`: `Scene`, `SceneCharacterGoal` — ready for use (includes `to_db_dict()` for `narrative_functions` JSON)
- `novel.models.world`: `Location`, `Faction`, `Culture`, `FactionPoliticalState`, `Artifact` — ready; `Location` has `to_db_dict()` for `sensory_profile` JSON
- `novel.models.magic`: `MagicSystemElement`, `MagicUseLog`, `PractitionerAbility` — ready for use
- `novel.models.shared`: `NotFoundResponse`, `ValidationFailure` — import and return, never raise
- Phase 2 seed profile: populates all domain tables — test conftest uses `load_seed_profile(conn, "minimal")`

### Established Patterns
- `register(mcp: FastMCP) -> None` with local async functions decorated by `@mcp.tool()`
- Error contract: return `NotFoundResponse` for missing records, `ValidationFailure` for bad input
- No `print()` anywhere — `logging.getLogger(__name__)` only
- Verb-first snake_case tool names: get_, list_, upsert_, log_, check_
- JSON fields: use `to_db_dict()` on write (Scene.narrative_functions, Location.sensory_profile)
- `str | None = None` nullable syntax throughout
- `int | None = None` for optional FK fields

### Integration Points
- `server.py`: Add 4 `register(mcp)` calls — `from novel.tools import chapters, scenes, world, magic`
- Tests: `tests/test_chapters.py`, `tests/test_scenes.py`, `tests/test_world.py`, `tests/test_magic.py` — in-memory FastMCP client pattern from Phase 3
- `upsert_faction` may need to update `faction_political_states` — FK to factions table (migration 021)

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 04-chapters-scenes-world*
*Context gathered: 2026-03-07*
