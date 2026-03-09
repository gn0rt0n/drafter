# Phase 11: Update schema, CLI, MCP, and planning docs to support 7-point structure and 3-act/7-point integration - Context

**Gathered:** 2026-03-09
**Status:** Ready for planning

<domain>
## Phase Boundary

Add 7-point structure tracking (Hook, Plot Turn 1, Pinch 1, Midpoint, Pinch 2, Plot Turn 2, Resolution) to the data model at two levels: story-level (one record per book) and per-POV-character arc (one record per beat per arc). Add gate checklist checks to enforce that both levels are fully populated before the architecture gate can be certified. Update Pydantic models, MCP tools, gate SQL queries, and the reference planning doc (`project-research/database-schema.md`).

**Out of scope:** CLI changes (no new `novel` subcommands needed — the existing query/gate CLI is sufficient), new domains beyond 7-point structure, changes to existing tables other than what the gate SQL requires.

</domain>

<decisions>
## Implementation Decisions

### Story-level beat storage
- New `story_structure` table (not adding columns to `books` or `acts`)
- One row per book (`UNIQUE(book_id)`)
- 7 chapter FK columns: `hook_chapter_id`, `plot_turn_1_chapter_id`, `pinch_1_chapter_id`, `midpoint_chapter_id`, `pinch_2_chapter_id`, `plot_turn_2_chapter_id`, `resolution_chapter_id` — all nullable (populated progressively during architecture phase)
- 3 additional chapter FKs for 3-act alignment markers: `act_1_inciting_incident_chapter_id`, `act_2_midpoint_chapter_id`, `act_3_climax_chapter_id` — these satisfy PRD gate item 12's mention of `inciting_incident`, `midpoint`, `climax` fields (stored here, not on `acts`)
- `notes` text column for structural annotations
- Standard `created_at` / `updated_at` timestamps
- New migration: `022_seven_point_structure.sql`

### Character arc beat storage
- New `arc_seven_point_beats` junction table (not adding columns to `character_arcs`)
- `UNIQUE(arc_id, beat_type)` — one row per beat per arc, upsertable
- `beat_type` TEXT enum values: `'hook'`, `'plot_turn_1'`, `'pinch_1'`, `'midpoint'`, `'pinch_2'`, `'plot_turn_2'`, `'resolution'`
- `chapter_id` FK nullable — beat can be recorded before the chapter is locked
- `notes` text for per-beat annotations (e.g. "reactive-to-proactive shift happens here")
- `created_at` / `updated_at` timestamps
- In same migration `022_seven_point_structure.sql` as `story_structure`

### Gate checklist expansion
- Add 2 new gate items to `GATE_ITEM_META` and `GATE_QUERIES` in `src/novel/tools/gate.py`:
  1. `struct_story_beats` (category: `"structure"`) — "Story-level 7-point beats are defined (story_structure row exists with all 7 beats populated)" — SQL: count books that have no story_structure row, or have any of the 7 beat chapter FKs as NULL
  2. `arcs_seven_point_beats` (category: `"plot"`) — "All POV character arcs have all 7-point beat chapters defined" — SQL: count character_arcs for POV characters missing any of the 7 `arc_seven_point_beats` rows
- Total gate items becomes 36 (was 34)
- The `_GATE_ITEM_COUNT` constant updates accordingly
- The `assert set(GATE_QUERIES) == set(GATE_ITEM_META)` sanity check keeps both dicts in sync

### New MCP tools
Four new tools in a new `src/novel/tools/structure.py` module (not crowded into `arcs.py` or `chapters.py`):
1. `get_story_structure(book_id: int)` → `StoryStructure | NotFoundResponse` — retrieve story-level 7-point structure for a book
2. `upsert_story_structure(book_id, hook_chapter_id, plot_turn_1_chapter_id, pinch_1_chapter_id, midpoint_chapter_id, pinch_2_chapter_id, plot_turn_2_chapter_id, resolution_chapter_id, act_1_inciting_incident_chapter_id, act_2_midpoint_chapter_id, act_3_climax_chapter_id, notes)` → `StoryStructure | ValidationFailure` — create or update
3. `get_arc_beats(arc_id: int)` → `list[ArcSevenPointBeat]` — retrieve all 7 beat records for an arc (may be partial — empty list is valid)
4. `upsert_arc_beat(arc_id: int, beat_type: str, chapter_id: int | None, notes: str | None)` → `ArcSevenPointBeat | ValidationFailure` — create or update a single beat (ON CONFLICT(arc_id, beat_type) DO UPDATE)

Register via `register(mcp)` pattern. Wire into `server.py`. These are all gate-free tools (no `check_gate()` needed — they populate data that the gate checks).

### Pydantic models
Two new models in `src/novel/models/` (likely `src/novel/models/structure.py` or added to `src/novel/models/arcs.py`):
- `StoryStructure` — mirrors `story_structure` table columns
- `ArcSevenPointBeat` — mirrors `arc_seven_point_beats` table columns

### Planning doc updates
- `project-research/database-schema.md` — add `story_structure` and `arc_seven_point_beats` table definitions in the appropriate sections; note the 3-act/7-point relationship explicitly

### Claude's Discretion
- Exact SQL for the 2 new gate queries (query shape — just follow existing gate query patterns)
- Whether `StoryStructure` and `ArcSevenPointBeat` models live in a new file or are added to `models/arcs.py`
- Whether to add `structure.py` to tools or colocate with arcs — either is fine, prefer clarity
- Seed data additions for the gate-ready seed profile (add one `story_structure` row + 7 `arc_seven_point_beats` rows per test arc)

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/novel/migrations/` — new file `022_seven_point_structure.sql` following existing naming; no ALTER TABLE needed (new tables only)
- `src/novel/tools/arcs.py` — existing `register(mcp)` pattern to follow for `structure.py`
- `src/novel/models/arcs.py` — `CharacterArc`, `ArcHealthLog`, `ChekhovGun` models; new models follow same pattern
- `src/novel/tools/gate.py` — `GATE_ITEM_META` + `GATE_QUERIES` dicts + `_GATE_ITEM_COUNT`; add 2 new keys to both
- `src/novel/mcp/server.py` — `from novel.tools import structure; structure.register(mcp)` wiring

### Established Patterns
- Upsert: `ON CONFLICT(unique_key) DO UPDATE SET ...` — matches `upsert_chekov`, `upsert_arc_beat` follows same shape
- Gate queries: return `SELECT COUNT(*) AS missing_count` — 0 = passing, >0 = blocking
- Models: Pydantic v2, field names match SQL column names exactly (no aliasing)
- Tool registration: all tools in `register(mcp: FastMCP)` local-function pattern, never `@app.tool()` at module level

### Integration Points
- `src/novel/mcp/server.py` — add `from novel.tools import structure; structure.register(mcp)` (one line, follows existing pattern)
- `src/novel/tools/gate.py` `GATE_ITEM_META` / `GATE_QUERIES` — add 2 new items; update `_GATE_ITEM_COUNT` comment
- Gate-ready seed profile — add seed rows for `story_structure` (1 row) and `arc_seven_point_beats` (7 rows × number of test arcs)
- `tests/test_structure.py` — new domain test file (follows `tests/test_arcs.py` pattern)

</code_context>

<specifics>
## Specific Ideas

- "I don't like to crowd tables when possible" — user preference for separate tables over adding columns to existing tables. Apply this principle consistently: when in doubt, new table.
- Arc beats junction table (`arc_seven_point_beats`) stores one row per beat per arc — makes it easy to partially populate (add beats progressively as architecture develops) and query individual beats without parsing a JSON blob.
- The 3 act-alignment fields (`act_1_inciting_incident_chapter_id`, `act_2_midpoint_chapter_id`, `act_3_climax_chapter_id`) on `story_structure` satisfy PRD gate item 12's mention of "inciting_incident, midpoint, climax fields" without adding columns to `acts`.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 11-update-schema-cli-mcp-and-planning-docs-to-support-7-point-structure-and-3-act-7-point-integration*
*Context gathered: 2026-03-09*
