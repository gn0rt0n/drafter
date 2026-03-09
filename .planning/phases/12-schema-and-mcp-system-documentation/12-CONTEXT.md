# Phase 12: Schema and MCP System Documentation - Context

**Gathered:** 2026-03-09
**Status:** Ready for planning

<domain>
## Phase Boundary

Create authoritative, implementation-accurate reference documentation for the built system:
- `docs/schema.md` — the SQLite database schema (22 migrations, ~70 tables) with field annotations, FK relationships, lifecycle notes, and gate flags
- `docs/mcp-tools.md` — all ~80 MCP tools across 14 domains with full tool cards (purpose, parameters, return types, invocation reason, gate status, tables touched)
- `docs/README.md` — architecture overview linking the three layers (schema, MCP, CLI)

Target audience: system-admin level reader who needs to understand implementation, not just usage.

The existing `project-research/database-schema.md` is a pre-build design document and remains as design history — these new docs are the implementation-accurate reference. A pointer note will be added to the old doc.

</domain>

<decisions>
## Implementation Decisions

### Document location and structure
- Live in `docs/` directory at the project root (new directory)
- Three files: `docs/README.md`, `docs/schema.md`, `docs/mcp-tools.md`
- `project-research/database-schema.md` stays as historical design doc; add a note pointing to `docs/` as the authoritative reference
- Do NOT merge or replace the existing design doc

### Schema documentation (docs/schema.md)
- Organized by domain (not by migration file number), with migration order preserved within each domain section
- Each domain section opens with a Mermaid ER diagram showing tables and FK arrows in that domain
- Each table entry includes:
  1. 1-2 sentence purpose statement
  2. All fields: type + purpose sentence for non-obvious fields; standard fields (id, created_at, updated_at, notes, source_file) annotated briefly or noted as standard
  3. FK relationships in prose (e.g., `character_id → characters.id`)
  4. Cross-domain FK notes inline where they reference another domain's table
  5. "Populated by" lifecycle note (which MCP tools write to it, when in the workflow it's populated)
  6. Gate flag (⚠️ Gate-enforced writes) for tables whose MCP write tools require gate certification
- Top of schema.md has a "System Integration" section — how domains connect, cross-domain dependency map (prose or Mermaid)
- Standard fields annotation style: self-evident fields get type only; business-logic fields get a descriptive sentence; FK fields note what they reference

### MCP tool documentation (docs/mcp-tools.md)
- Index table at the top: all ~80 tools with tool name, domain, one-line description
- Organized into 14 domain sections (one per tool module), matching the codebase structure
- Each tool entry includes:
  1. Tool name (as callable MCP tool)
  2. Purpose: what it does
  3. Parameters: name + type + required/optional + description per param
  4. Return type: what the tool returns (including error contract responses: null/not_found, is_valid:false/ValidationFailure, requires_action/GateViolation)
  5. Invocation reason: when and why an agent would call this tool
  6. Gate status: "Gate-free" or "Requires gate certification" with brief note on what happens if gate is not certified
  7. Tables touched: which DB tables the tool reads from and writes to

### Relationship representation
- FK relationships: prose inline per table ("character_id → characters.id — the character this state belongs to") + Mermaid ER diagram per domain section
- Cross-domain FK relationships: noted inline at the table entry + covered in the top-level "System Integration" section of schema.md
- docs/README.md: architecture overview — what the system is, how schema + MCP + CLI connect, where to find what. Links to schema.md and mcp-tools.md. This is the entry point for a new system admin.

### Claude's Discretion
- Exact Mermaid diagram style and layout
- Level of prose detail for truly obvious fields (id, timestamps)
- Whether to include a table count summary at the top of each domain section
- Exact formatting of tool parameter tables (markdown table vs definition list)

</decisions>

<specifics>
## Specific Ideas

- User wants "system-admin level" framing — this means: someone who needs to understand implementation (not just usage), can read SQL and Python types, wants to know why the system is designed a certain way, not just what it does
- The "when included/invoked" requirement applies to both schema (lifecycle notes per table) and MCP (invocation reason per tool)
- The MCP error contract must be clearly documented — null for not-found, is_valid:false for validation failures, requires_action for gate violations — so an admin understands what every tool can return

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/novel/migrations/001-022.sql`: Ground truth for all table definitions, field names, types, and FK constraints — schema.md must be derived from these, not from design docs
- `src/novel/tools/*.py`: Ground truth for all MCP tool signatures, parameters, and return types — mcp-tools.md must reflect actual implementation
- `project-research/database-schema.md`: 1674-line pre-build design doc — useful as reference for intent, NOT as source of truth for field names (known to have drifted from actual migrations)

### Established Patterns
- Migration SQL files are ground truth — plan descriptions and design docs have historically diverged from actual column names (confirmed across Phases 02-10)
- Error contract: null/not_found_message for missing records, is_valid:false/errors for validation failures, requires_action/GateViolation for gate violations
- Gate-free tools: names domain (all 4 tools); all other domains have gated write tools
- Tool registration pattern: register(mcp: FastMCP) → None in each tools/*.py module

### Integration Points
- docs/ is a new directory at project root — no existing docs infrastructure
- The existing project-research/database-schema.md needs a pointer note added (not replaced)
- Phase 11 added migration 022 (seven_point_structure tables) — docs must cover these too

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 12-schema-and-mcp-system-documentation*
*Context gathered: 2026-03-09*
