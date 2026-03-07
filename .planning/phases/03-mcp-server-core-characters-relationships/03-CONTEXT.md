# Phase 3: MCP Server Core, Characters & Relationships - Context

**Gathered:** 2026-03-07
**Status:** Ready for planning

<domain>
## Phase Boundary

First working MCP server callable from Claude Code: FastMCP instance wired with 13 tools across two domains (characters and relationships), error contract enforced on every tool, and in-memory FastMCP client tests verifying the callable interface. No other domain tools (chapters, world, plot, etc.) — those are Phase 4+.

</domain>

<decisions>
## Implementation Decisions

### Tool registration architecture
- Each domain tool module (`tools/characters.py`, `tools/relationships.py`) exposes a `register(mcp: FastMCP) -> None` function
- `server.py` calls each module's `register(mcp)` at startup: `from novel.tools import characters, relationships; characters.register(mcp); relationships.register(mcp)`
- Inside `register()`, tools are defined as local async functions and decorated with `mcp.tool()` — the FastMCP instance is passed in, never imported globally from tools modules
- This avoids circular imports, keeps each module self-contained, and scales identically for all 7 remaining domain phases (just add another `register(mcp)` call)
- `tools/__init__.py` stays minimal — no auto-discovery magic, explicit registration only

### Tool naming convention
- Verb-first snake_case: `get_character`, `list_characters`, `create_character`, `update_character`
- Pattern: `{verb}_{noun}` for single-entity tools, `{verb}_{noun}s` for list/collection tools
- State-query tools: `get_character_injuries`, `get_character_knowledge`, `get_character_beliefs`, `get_character_location`
- Logging tools: `log_character_knowledge`
- Relationship tools: `get_relationship`, `list_character_relationships`, `create_relationship`, `update_relationship`, `log_relationship_change`, `get_perception_profile`, `upsert_perception_profile`

### Character state queries (time-varying tables)
- 4 state tables (injuries, knowledge, beliefs, character_locations) get separate tools — not bundled into `get_character`
- Each state tool takes `character_id` as required param; `chapter_id` as optional param where the schema supports time scoping
- `get_character` returns the core characters table row only (no state embedded)
- State tools: `get_character_injuries(character_id, chapter_id)`, `get_character_knowledge(character_id, chapter_id=None)`, `get_character_beliefs(character_id)`, `get_character_location(character_id, chapter_id=None)`
- Knowledge logging: `log_character_knowledge(character_id, chapter_id, knowledge_type, content, ...)`
- This keeps each tool mapping 1:1 with a table/query — Claude requests exactly what it needs

### Error contract enforcement
- Carried forward from Phase 1: every tool returns `NotFoundResponse` (not raises) for missing records
- Validation failures return `ValidationFailure(is_valid=False, errors=[...])` — never raise HTTPException or similar
- No `print()` anywhere in `novel/mcp/` or `novel/tools/` — all logging via `logging.getLogger(__name__)`
- Gate violations return `GateViolation(requires_action=...)` — relevant for prose-phase tools in Phase 6+, not needed in Phase 3

### Test database strategy
- Tests use in-memory SQLite (`:memory:`) — fast, isolated, zero cleanup
- `conftest.py` creates a test database by running migrations programmatically against `:memory:`, then seeding with Phase 2's minimal seed profile via `load_seed_profile`
- Tests use the FastMCP in-memory client to call tools (not raw function calls) — verifies the actual MCP callable interface
- No mocking of DB connections — real SQL against real schema is the reliability guarantee
- Test discovery: `tests/test_characters.py` and `tests/test_relationships.py`

### Claude's Discretion
- Exact SQL query patterns for each tool (joins, CTEs, etc.)
- aiosqlite row-to-model mapping implementation details
- Specific `chapter_id` scoping logic for state tables (latest-before-chapter vs exact-match)
- Whether to add any DB indexes in Phase 3 to support common tool queries
- conftest.py fixture scope (session vs function level for test DB)

</decisions>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches. User delegated all implementation decisions to Claude.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `novel.mcp.db.get_connection()`: async context manager, WAL + FK pragmas already set, `aiosqlite.Row` row_factory set — every tool uses this
- `novel.mcp.server.mcp`: FastMCP instance already instantiated — tools register against this instance
- All domain Pydantic models ready: `Character`, `CharacterKnowledge`, `CharacterBelief`, `CharacterLocation`, `InjuryState`, `TitleState`, `CharacterRelationship`, `RelationshipChangeEvent`, `PerceptionProfile` (from `novel.models`)
- `NotFoundResponse`, `ValidationFailure`, `GateViolation` in `novel.models.shared` — import and return these, never raise
- Phase 2 seed profile: `load_seed_profile(conn, "minimal")` populates all tables — used by test conftest

### Established Patterns
- Nullable FK pattern: `int | None = None` for optional FK fields (established Phase 2)
- Boolean mapping: `INTEGER NOT NULL DEFAULT 0` → `bool` in Pydantic (Pydantic v2 coerces)
- Timestamp: `created_at`, `updated_at` as `str | None` in models
- `str | None = None` nullable syntax throughout
- No global state in MCP server code — context managers, not module-level connections

### Integration Points
- `server.py`: `register(mcp)` calls go here, after FastMCP instantiation, before `mcp.run()`
- `novel.tools.__init__.py`: stays minimal, just the namespace package
- Phase 4 will add `from novel.tools import chapters, world; chapters.register(mcp); world.register(mcp)` following the same pattern

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 03-mcp-server-core-characters-relationships*
*Context gathered: 2026-03-07*
