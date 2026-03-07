# Phase 5: Plot & Arcs - Context

**Gathered:** 2026-03-07
**Status:** Ready for planning

<domain>
## Phase Boundary

9 MCP tools across two domains: plot thread management (PLOT-01, PLOT-02, PLOT-07) and arc/Chekhov tracking (PLOT-03, PLOT-04, PLOT-05, PLOT-06, PLOT-08, PLOT-09). Covers retrieval, upsert, and health logging for plot threads, character arcs, Chekhov's gun registry, and subplot gap detection. Gate system, session management, and timeline tools are separate phases.

</domain>

<decisions>
## Implementation Decisions

### Tool module split
- 2 modules: `tools/plot.py` and `tools/arcs.py` — matches model file organization (`models/plot.py`, `models/arcs.py`)
- `tools/plot.py`: `get_plot_thread`, `list_plot_threads`, `upsert_plot_thread`
- `tools/arcs.py`: `get_arc`, `get_arc_health`, `get_chekovs_guns`, `upsert_chekov`, `get_subplot_touchpoint_gaps`, `log_arc_health`
- `server.py` gets 2 more `register(mcp)` calls: `from novel.tools import plot, arcs`

### `get_arc` — dual-mode lookup (PLOT-04)
- Signature: `get_arc(arc_id: int | None = None, character_id: int | None = None)`
- If `arc_id` provided: return single `CharacterArc` or `NotFoundResponse`
- If `character_id` provided: return list of all `CharacterArc` rows for that character (empty list if none)
- If both provided: `arc_id` takes precedence
- If neither provided: `ValidationFailure` — at least one required
- This covers both direct lookup and character-based discovery without adding a separate list tool

### `get_arc_health` — full history (PLOT-05)
- Signature: `get_arc_health(character_id: int, arc_id: int | None = None)`
- Returns full `arc_health_log` history ordered by chapter_id ascending — not just the latest entry
- If `arc_id` provided: filter to that arc only; else return health for all arcs of that character
- Claude can read the last entry for current status, or scan the sequence for trajectory
- Returns empty list (not `NotFoundResponse`) when no health logs exist yet — log is optional

### `get_subplot_touchpoint_gaps` — configurable threshold (PLOT-06)
- Signature: `get_subplot_touchpoint_gaps(threshold_chapters: int = 5)`
- Finds plot threads where `thread_type = 'subplot'` AND `status = 'active'` AND the most recent `subplot_touchpoint_log` entry is more than `threshold_chapters` chapters ago (by chapter_id ordering)
- Also includes active subplots with zero touchpoints logged (never touched since opened)
- Returns list of `{plot_thread_id, name, last_touchpoint_chapter_id, chapters_since_touchpoint}` — structured enough for Claude to act on
- Default 5 chapters is a sensible novel pacing cadence; caller can tighten or loosen

### `get_chekovs_guns` — status filter + unresolved flag (PLOT-03)
- Signature: `get_chekovs_guns(status: str | None = None, unresolved_only: bool = False)`
- `status` filter: matches `chekovs_gun_registry.status` column (planted/fired/misfired) — `None` returns all
- `unresolved_only=True`: returns only entries where `status = 'planted'` AND `payoff_chapter_id IS NULL` — guns introduced but not yet paid off
- `unresolved_only` takes precedence over `status` when both are provided
- Returns list of `ChekhovGun` models

### `list_plot_threads` — optional filters (PLOT-02)
- Signature: `list_plot_threads(thread_type: str | None = None, status: str | None = None)`
- Filters on `plot_threads.thread_type` (main/subplot/backstory) and/or `status` (active/closed/dormant)
- Both optional — no args returns all threads

### Claude's Discretion
- All SQL query patterns and join strategies
- `upsert_plot_thread` and `upsert_chekov` conflict resolution (INSERT OR REPLACE vs ON CONFLICT UPDATE)
- Whether `upsert_plot_thread` touches `chapter_plot_threads` junction table or just `plot_threads` (recommend: just plot_threads — junction management is implicit via chapter tools)
- Test fixture scope (session vs function)
- Plan file split across the 2 plan slots

</decisions>

<specifics>
## Specific Ideas

No specific requirements — user delegated all implementation decisions. Open to standard approaches following Phase 4 patterns.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `novel.mcp.db.get_connection()`: async context manager, WAL + FK pragmas set — every tool uses this unchanged
- `novel.mcp.server.mcp`: FastMCP instance, has 6 domain modules registered (characters, relationships, chapters, scenes, world, magic)
- `novel.models.plot`: `PlotThread`, `ChapterPlotThread`, `ChapterCharacterArc` — ready for use
- `novel.models.arcs`: `CharacterArc`, `ArcHealthLog`, `ChekhovGun`, `SubplotTouchpoint` — ready for use
- `novel.models.shared`: `NotFoundResponse`, `ValidationFailure` — import and return, never raise
- Phase 2 seed profile: `load_seed_profile(conn, "minimal")` populates all tables — test conftest uses this

### Established Patterns
- `register(mcp: FastMCP) -> None` with local async functions decorated by `@mcp.tool()` — no deviation
- Error contract: return `NotFoundResponse` for missing records, `ValidationFailure` for bad input
- No `print()` anywhere — `logging.getLogger(__name__)` only
- Verb-first snake_case tool names: get_, list_, upsert_, log_
- `str | None = None` nullable syntax throughout
- `int | None = None` for optional FK fields
- Tests: in-memory FastMCP client, real SQL against real schema (no mocking)

### Integration Points
- `server.py`: Add 2 `register(mcp)` calls — `from novel.tools import plot, arcs; plot.register(mcp); arcs.register(mcp)`
- Tests: `tests/test_plot.py`, `tests/test_arcs.py` — same in-memory FastMCP client pattern from Phases 3–4
- `get_subplot_touchpoint_gaps` queries both `plot_threads` and `subplot_touchpoint_log` — needs JOIN across migration 016 and 017 tables
- `get_arc_health` queries `arc_health_log` joined to `character_arcs` to filter by `character_id`

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 05-plot-arcs*
*Context gathered: 2026-03-07*
