# Phase 8: Canon, Knowledge & Foreshadowing - Context

**Gathered:** 2026-03-07
**Status:** Ready for planning

<domain>
## Phase Boundary

20 prose-phase MCP tools across 3 sub-domains: Canon (7 tools — facts, decisions, continuity), Knowledge/Reader State (5 tools — reader info state, dramatic irony, reveals), and Foreshadowing/Literary (8 tools — foreshadowing, prophecies, motifs, motif occurrences, thematic mirrors, opposition pairs). All tools call check_gate() at the top. Server.py wiring for all 3 modules in the final plan. No CLI subcommands in this phase.

</domain>

<decisions>
## Implementation Decisions

### Module organization
- Three separate tool files following established domain separation pattern: `src/novel/tools/canon.py`, `src/novel/tools/knowledge.py`, `src/novel/tools/foreshadowing.py`
- Models already exist in `src/novel/models/canon.py` — all 12 model classes ready to use
- `StoryDecision` model is missing from `src/novel/models/canon.py` — must be added in 08-01 before canon tools are written. Schema from migration 021 decisions_log table: `id, decision_type, description, rationale, alternatives (TEXT nullable), session_id (FK nullable), chapter_id (FK nullable), created_at`

### Reader state query semantics — cumulative
- `get_reader_state(chapter_id)` queries `WHERE chapter_id <= X` — returns cumulative reader knowledge UP TO that chapter, not AT that exact chapter
- This gives Claude a complete snapshot of what readers know at any story point in a single call
- Returns list of `ReaderInformationState` records ordered by chapter_id ASC

### Foreshadowing: upsert, not append-only
- `log_foreshadowing` implements upsert behavior (two-branch: None-id INSERT + lastrowid; provided-id ON CONFLICT(id) DO UPDATE)
- Rationale: foreshadowing entries start as "planted" with only plant_chapter_id; payoff_chapter_id and status="paid_off" must be fillable later as the story progresses
- Despite the "log_" prefix in the requirement, append-only INSERT would prevent tracking payoff
- `log_motif_occurrence` (FORE-08) IS append-only — motif occurrences are historical events, not updateable records

### Dramatic irony — unresolved by default
- `get_dramatic_irony_inventory` returns only unresolved entries (`resolved = FALSE`) by default
- Accepts optional `include_resolved: bool = False` parameter
- Optional `chapter_id` filter to scope to entries created at a specific chapter
- Returns list of `DramaticIronyEntry` records

### Continuity issues — open by default, severity optional
- `get_continuity_issues` returns only open issues (`is_resolved = FALSE`) by default
- Accepts optional `severity: str | None = None` filter (minor/major/critical)
- Accepts optional `include_resolved: bool = False` parameter
- `resolve_continuity_issue(id, resolution_note)` UPDATE sets `is_resolved=True, resolution_note=now, updated_at=now`; returns updated `ContinuityIssue` or `NotFoundResponse`

### Canon tools behavior
- `get_canon_facts(domain)` — required `domain` parameter; returns all `CanonFact` rows for that domain ordered by created_at
- `log_canon_fact` — append-only INSERT; `CanonFact` with parent_fact_id support for building fact hierarchies
- `log_decision` — append-only INSERT into decisions_log; returns `StoryDecision`
- `get_decisions(decision_type=None, chapter_id=None)` — optional filters; returns list of `StoryDecision` ordered by created_at DESC

### Knowledge domain — reader reveals
- `get_reader_reveals(chapter_id=None)` — optional chapter_id filter; returns all `ReaderReveal` records (planned_reveal and actual_reveal may be null for planned-but-not-yet-written reveals)
- `upsert_reader_state` — two-branch: None-id INSERT + lastrowid; provided-id ON CONFLICT(id) DO UPDATE on `reader_information_states`

### Foreshadowing read tools
- `get_foreshadowing(status=None, chapter_id=None)` — optional `status` filter (planted/paid_off); optional `chapter_id` filters on `plant_chapter_id`; returns list of `ForeshadowingEntry`
- `get_prophecies()` — returns all `ProphecyEntry` records; no required filter (prophecy registry is small)
- `get_motifs()` — returns all `MotifEntry` records
- `get_motif_occurrences(motif_id=None, chapter_id=None)` — optional filters by motif or chapter; returns list of `MotifOccurrence`
- `get_thematic_mirrors()` — returns all `ThematicMirror` records
- `get_opposition_pairs()` — returns all `OppositionPair` records

### Plan split (3 plans)
- **08-01**: Canon domain — add `StoryDecision` model to `canon.py`, then `src/novel/tools/canon.py` with all 7 tools (get_canon_facts, log_canon_fact, log_decision, get_decisions, log_continuity_issue, get_continuity_issues, resolve_continuity_issue)
- **08-02**: Knowledge domain — `src/novel/tools/knowledge.py` with all 5 tools (get_reader_state, get_dramatic_irony_inventory, get_reader_reveals, upsert_reader_state, log_dramatic_irony)
- **08-03**: Foreshadowing domain — `src/novel/tools/foreshadowing.py` with all 8 tools (get_foreshadowing, get_prophecies, get_motifs, get_motif_occurrences, get_thematic_mirrors, get_opposition_pairs, log_foreshadowing, log_motif_occurrence) + server.py wiring for all 3 modules + in-memory FastMCP tests for all 20 tools

### Claude's Discretion
- Exact SQL for all queries
- conftest.py extension for canon/knowledge/foreshadowing seed data
- Fixture scope and test helpers
- Whether get_prophecies/get_motifs accept optional filters beyond what's listed
- `get_decisions` ordering and pagination approach

</decisions>

<specifics>
## Specific Ideas

No specific requirements — user delegated all implementation decisions to Claude. Follow established patterns from Phases 3–7.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `novel.models.canon`: `CanonFact`, `ContinuityIssue`, `ForeshadowingEntry`, `ProphecyEntry`, `MotifEntry`, `MotifOccurrence`, `ThematicMirror`, `OppositionPair`, `ReaderInformationState`, `ReaderReveal`, `DramaticIronyEntry`, `ReaderExperienceNote` — all defined, ready to use
- **MISSING**: `StoryDecision` model — must be added to `novel/models/canon.py` in 08-01 (decisions_log table exists in migration 021)
- `novel.mcp.gate.check_gate(conn)` — import and call at top of every tool
- `novel.mcp.db.get_connection()` — async context manager; WAL + FK pragmas already set
- `novel.models.shared`: `NotFoundResponse`, `ValidationFailure`, `GateViolation` — error contract types
- `novel.db.seed.load_seed_profile("minimal")` — loads test data; conftest.py uses this for in-memory tests

### Established Patterns
- `register(mcp: FastMCP) -> None` with local async functions decorated with `@mcp.tool()`
- `check_gate()` first, before any DB read logic — return violation immediately if not None
- Append-only INSERT (no ON CONFLICT) for audit/log tools: log_canon_fact, log_decision, log_continuity_issue, log_dramatic_irony, log_motif_occurrence
- Upsert pattern (two-branch) for upsert_reader_state and log_foreshadowing
- Error contract: `NotFoundResponse` for missing single records, empty list for missing collections
- No `print()` — `logging.getLogger(__name__)` only
- Cursor.lastrowid for INSERT row ID (aiosqlite pattern)
- FastMCP serializes `list[T]` as N TextContent blocks — tests use `[json.loads(c.text) for c in result.content]`
- MCP session entered per-test (not per-fixture) — anyio cancel scope teardown issue

### Integration Points
- `server.py`: add `from novel.tools import canon, knowledge, foreshadowing; canon.register(mcp); knowledge.register(mcp); foreshadowing.register(mcp)` in 08-03
- `src/novel/models/canon.py`: add `StoryDecision` model before writing tools
- Create `src/novel/tools/canon.py`, `src/novel/tools/knowledge.py`, `src/novel/tools/foreshadowing.py` (new files)
- `tests/`: add `test_canon.py`, `test_knowledge.py`, `test_foreshadowing.py` in 08-03

### Schema Notes (migration 021)
- `canon_facts`: id, domain, fact, source_chapter_id, source_event_id, parent_fact_id, certainty_level, canon_status, notes, created_at, updated_at
- `continuity_issues`: id, severity, description, chapter_id, scene_id, canon_fact_id, is_resolved, resolution_note, created_at, updated_at
- `decisions_log`: id, decision_type, description, rationale, alternatives, session_id, chapter_id, created_at
- `reader_information_states`: id, chapter_id, domain, information, revealed_how, notes, created_at
- `reader_reveals`: id, chapter_id, scene_id, character_id, reveal_type, planned_reveal, actual_reveal, reader_impact, notes, created_at, updated_at
- `dramatic_irony_inventory`: id, chapter_id, reader_knows, character_id, character_doesnt_know, irony_type, tension_level, resolved, resolved_chapter_id, notes, created_at
- `foreshadowing_registry`: id, description, plant_chapter_id, plant_scene_id, payoff_chapter_id, payoff_scene_id, foreshadowing_type, status, notes, created_at, updated_at
- `prophecy_registry`: id, name, text, subject_character_id, source_character_id, uttered_chapter_id, fulfilled_chapter_id, status, interpretation, notes, canon_status, created_at, updated_at
- `motif_registry`: id, name, motif_type, description, thematic_role, first_appearance_chapter_id, notes, created_at, updated_at
- `motif_occurrences`: id, motif_id, chapter_id, scene_id, description, occurrence_type, notes, created_at
- `thematic_mirrors`: id, name, mirror_type, element_a_id, element_a_type, element_b_id, element_b_type, mirror_description, thematic_purpose, notes, created_at
- `opposition_pairs`: id, name, concept_a, concept_b, manifested_in, resolved_chapter_id, notes, created_at

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 08-canon-knowledge-foreshadowing*
*Context gathered: 2026-03-07*
