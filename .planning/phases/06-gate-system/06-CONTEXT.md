# Phase 6: Gate System - Context

**Gathered:** 2026-03-07
**Status:** Ready for planning

<domain>
## Phase Boundary

Architecture gate enforcement: 5 MCP gate tools (get_gate_status, get_gate_checklist, run_gate_audit, update_checklist_item, certify_gate), shared check_gate() helper called by prose-phase tools, gate-ready seed profile that satisfies all 33 checklist items, and 3 CLI commands (novel gate check, novel gate status, novel gate certify). Phase 3–5 architecture tools are NOT retrofitted — gating applies to Phase 7+ tools only.

</domain>

<decisions>
## Implementation Decisions

### 33 checklist queries — adapt to actual schema
- Write queries as "all existing X must have Y" — NOT hard-coded counts (not "all 55 chapters", not "6 POV characters")
- This makes the gate correctly validate completeness of whatever story architecture exists, scalable to any novel size
- Several PRD items reference schema constructs that weren't built; adapt as follows:
  - Acts: check start_chapter_id and end_chapter_id are non-null (not inciting_incident/midpoint/climax — these fields don't exist)
  - Plot threads: check all thread_type='main' threads have non-null stakes (not is_primary — field doesn't exist)
  - Chapter plans: check chapters.opening_hook_note and closing_hook_note non-null (ChapterPlan is a projection, not a separate table)
  - Supernatural scenes: check that at least one supernatural_voice_guidelines entry exists when supernatural_elements exist (no direct scene-to-supernatural link table)
  - Battle scenes: check all scenes with scene_type='action' have non-null summary (no battle_action_coordinator table)
  - Prophecy fulfillment: check all active prophecies have non-null text (no fulfillment path column)
  - Tension: check all chapters have at least one tension_measurements row (not per-scene null check)
- All 33 items stored in gate_checklist_items table (one row per item, item_key as identifier)
- run_gate_audit executes all 33 SQL queries, updates is_passing and missing_count on each item

### check_gate() scope — Phase 7+ tools only
- Phase 3–5 tools (characters, chapters, scenes, world, magic, plot, arcs) are architecture-phase tools — they MUST work before gate passes so the architecture can be built; NO gate enforcement
- Phase 7+ tools (session, timeline, canon, knowledge, foreshadowing, names, voice, publishing) are prose-phase tools — called WHILE writing; these get check_gate() at the top
- check_gate() lives in novel/mcp/gate.py as a standalone async function — not in tools/gate.py
- Signature: async def check_gate(conn) -> GateViolation | None — returns GateViolation if not certified, None if certified
- Prose-phase tools call: violation = await check_gate(conn); if violation: return violation
- GateViolation already defined in models/shared.py: requires_action: str

### gate-ready seed strategy — extend minimal, satisfy relationally
- "gate_ready" seed profile extends minimal seed by adding the missing entries for existing data
- Does NOT add 55 chapters or 6 POV characters — seed stays small and testable
- Checks written as relational ("all chapters that exist must have...") so 3 seed chapters satisfy them
- gate_ready seed additions needed over minimal:
  - voice_profiles for all 5 characters (minimal has 0 extra voices beyond protagonist)
  - character_relationships for all POV character pairs (minimal has 3; need all pairs)
  - perception_profiles for all POV-to-POV pairs (minimal has 1; need all pairs)
  - opening_hook_note and closing_hook_note on all 3 chapters (currently null)
  - chapter_structural_obligations for chapters 2 and 3 (minimal has only chapter 1)
  - scene_character_goals for all 6 scenes (minimal has only 1)
  - tension_measurements for chapter 3 (minimal has 1+2)
  - canon_facts for politics, religion, geography domains (minimal has only world)
  - name_registry entry for every character and location (minimal has only protagonist)
  - faction_political_state for the Obsidian Court (minimal has one from Phase 13 of seed)
  - gate certification row set to is_certified=0 (already present in minimal)
  - All 33 gate_checklist_items populated with their item_key, category, description

### update_checklist_item — full manual override allowed
- update_checklist_item can set is_passing, missing_count, and notes directly
- run_gate_audit is the recommended path (SQL evidence drives passing status)
- Manual override exists for edge cases where SQL can't capture a fact (e.g., narrative completeness that requires human judgment)
- certify_gate reads current item states — trusts whatever run_gate_audit (or manual override) set
- certify_gate refuses if any item has is_passing=False; does NOT re-run audit itself

### Plan split (3 plans)
- 06-01: tools/gate.py with all 5 MCP gate tools + 33 SQL evidence queries + GateAuditReport model (Wave 1)
- 06-02: novel/mcp/gate.py check_gate() helper + gate-ready seed in seed.py + server.py wiring (Wave 2)
- 06-03: CLI gate commands (novel gate check/status/certify) + MCP tests for all 5 gate tools (Wave 3)

### Claude's Discretion
- Exact SQL for each of the 33 checklist queries
- GateAuditReport model structure (fields, nesting)
- How run_gate_audit batches 33 queries (sequential vs parallel)
- CLI output formatting for gap report

</decisions>

<specifics>
## Specific Ideas

No specific requirements — user delegated all implementation decisions. Follow established patterns from Phases 3–5.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `novel.models.gate`: `ArchitectureGate`, `GateChecklistItem` — already built in Phase 2, ready to use
- `novel.models.shared`: `GateViolation(requires_action: str)` — already defined, return from check_gate()
- `novel.mcp.db.get_connection()`: async context manager — all 5 gate tools use this unchanged
- `novel.mcp.server.mcp`: FastMCP instance — add `gate.register(mcp)` call in Phase 6 wiring
- `novel.db.seed.load_seed_profile()`: extend with "gate_ready" profile entry in profiles dict
- Phase 2 minimal seed: already inserts architecture_gate row (id=1, is_certified=0) and one gate_checklist_item

### Established Patterns
- `register(mcp: FastMCP) -> None` with local async functions decorated with `@mcp.tool()`
- Error contract: NotFoundResponse for missing records, ValidationFailure for bad input
- No print() anywhere — logging.getLogger(__name__) only
- Verb-first snake_case: get_gate_status, run_gate_audit, get_gate_checklist, update_checklist_item, certify_gate
- In-memory FastMCP client tests — same conftest pattern from Phases 3–5
- CLI commands: Typer app in novel/db/cli.py pattern; gate CLI likely in novel/gate/cli.py or similar

### Integration Points
- server.py: Add `from novel.tools import gate; gate.register(mcp)` — Phase 6 wiring
- check_gate() location: novel/mcp/gate.py (separate from tools/gate.py to avoid circular imports)
- Phase 7+ tools will import: `from novel.mcp.gate import check_gate`
- CLI entry: novel/cli.py has a gate subcommand group — add gate commands to existing Typer structure
- gate_checklist_items table uses UNIQUE(gate_id, item_key) — upsert or INSERT OR REPLACE safe

### Schema Notes
- architecture_gate: id, is_certified, certified_at, certified_by, checklist_version, notes (migration 020)
- gate_checklist_items: id, gate_id, item_key, category, description, is_passing, missing_count, last_checked_at, notes (migration 020)
- check_gate() queries architecture_gate WHERE id=1 (or latest) for is_certified
- 33 items need to be seeded into gate_checklist_items by gate-ready seed profile OR by run_gate_audit initialization logic

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 06-gate-system*
*Context gathered: 2026-03-07*
