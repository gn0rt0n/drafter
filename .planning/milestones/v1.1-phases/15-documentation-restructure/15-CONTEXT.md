# Phase 15: Documentation Restructure - Context

**Gathered:** 2026-03-09
**Status:** Ready for planning

<domain>
## Phase Boundary

Update mcp-tools.md and schema.md to reflect Phase 14 additions, then split both monoliths into per-domain files under `docs/tools/` and `docs/schema/`. Overhaul `docs/README.md` into a master index linking all per-domain files. The original monoliths are deleted. No new documentation content beyond what already exists in source code and Phase 14 plan outputs.

</domain>

<decisions>
## Implementation Decisions

### Domain taxonomy
- Use the 18 tool module names as the authoritative domain taxonomy for BOTH `docs/tools/` and `docs/schema/` filenames
- Tool module domains (source of truth): characters, relationships, chapters, scenes, world, magic, plot, arcs, gate, names, structure, session, timeline, canon, knowledge, foreshadowing, voice, publishing
- Schema sections that currently span multiple tool domains are split to match:
  - "Chapters & Scenes" → `chapters.md` + `scenes.md`
  - "Plot & Arcs" → `plot.md` + `arcs.md`
  - "Voice & Names" → `voice.md` + `names.md`
  - "Timeline & Events" → `timeline.md` (events table belongs to timeline domain)
  - "Foundation" + "Structure" → `structure.md` (books, acts, eras, 7-point structure — all in structure tool module)
  - "Canon & Continuity" → `canon.md`
  - "Knowledge & Reader" → `knowledge.md`
  - "Gate & Metrics" → `gate.md`
  - "World" → `world.md`
  - "Utility" → merge into `gate.md` or `session.md` (planner determines which module owns the utility schema tables)
- Result: both `docs/tools/` and `docs/schema/` contain the same 18 domain filenames — consistent navigation across both doc types

### Output directory structure
- `docs/tools/` — 18 per-domain tool reference files (e.g., `docs/tools/characters.md`)
- `docs/schema/` — 18 per-domain schema files (e.g., `docs/schema/characters.md`)
- `docs/README.md` — master index (overhauled from current 170-line architecture overview)

### Monolith fate
- Delete `docs/mcp-tools.md` and `docs/schema.md` entirely after the split
- No redirect stubs — the master index at `docs/README.md` serves as the navigation entry point
- Clean break: no zombie monoliths that could go stale alongside per-domain files

### Master index
- Overhaul existing `docs/README.md` (currently 170 lines of architecture overview) into the master index
- Keep architecture overview content — condense it and move it to a brief preamble
- Add a full links section: every per-domain tool file and every per-domain schema file, organized by domain
- No separate `docs/index.md` — README.md is the universally understood entry point
- Structure: preamble (what Drafter is) → Tools Reference section (18 domain links) → Schema Reference section (18 domain links) → quick stats (total tools, total tables)

### Content update before split (critical)
- mcp-tools.md must be updated to document all Phase 14 new tools BEFORE splitting
  - Current state: 103 tools (as of Phase 11); Phase 14 added ~60-80 new tools (delete tools, upsert tools, junction tools, world-building tools, books/acts/eras)
  - Researcher must audit `src/novel/tools/` source files to extract all current tool signatures and descriptions
  - Each tool's documentation: name, parameters, return type, gate status (Free/Gated), one-line description — matching existing mcp-tools.md format
- schema.md must be updated to add read-only justifications BEFORE splitting
  - Two tables are intentionally read-only: `schema_migrations` (managed by migration runner) and `architecture_gate` (managed exclusively through `certify_gate` tool flow)
  - Each read-only table entry should include a "Read-only: [justification]" note in the schema docs
  - All other 69 tables now have write tools (Phase 14 complete)

### Per-domain file content scope
- **Tools files** (`docs/tools/{domain}.md`): domain header, gate status note if gated, tool table (name | parameters | return | gate | description), then individual tool entries with full parameter docs
  - Match existing mcp-tools.md format — just scoped to the domain
  - Include a "Back to index" link at the top (`[← Documentation Index](../README.md)`)
- **Schema files** (`docs/schema/{domain}.md`): domain header, table list, per-table: columns (name, type, constraints), FK references, read-only justification if applicable, Mermaid ER diagram if the existing schema.md has one for this domain
  - Match existing schema.md format — just scoped to the domain
  - Include a "Back to index" link at the top (`[← Documentation Index](../README.md)`)

### Claude's Discretion
- Exact module assignment for "Utility" schema tables (gate.md vs session.md)
- Whether to add a brief one-paragraph domain description at the top of each per-domain file
- Mermaid diagram retention: include existing diagrams if they render cleanly at domain scope; omit if cross-domain references make them misleading
- Exact preamble length and wording in the overhauled README.md master index

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `docs/mcp-tools.md` — 2615 lines, 18 domain sections (Characters through Publishing); Index table at top maps all 103 current tools; format is source of truth for per-domain tool file format
- `docs/schema.md` — 2741 lines, 16 numbered sections with Mermaid ER diagrams; format is source of truth for per-domain schema file format
- `docs/README.md` — 170 lines, existing architecture overview; will become master index
- `src/novel/tools/` — 18 Python modules; source of truth for current tool count, names, and signatures after Phase 14

### Established Patterns
- mcp-tools.md format: global index table → domain sections → per-tool entries with parameters table
- schema.md format: TOC → numbered domain sections → table descriptions → Mermaid ER diagrams
- Tool module naming matches domain names exactly (characters.py → Characters domain)

### Integration Points
- `src/novel/tools/*.py` — researcher must read all 18 modules to extract Phase 14 additions not yet in mcp-tools.md
- `.planning/phases/14-mcp-api-completeness/` — plan files document which tools were added per domain; researcher can use these to enumerate Phase 14 additions systematically
- Phase 14 plans are in `.planning/phases/14-mcp-api-completeness/` — 19 plans total (P01–P19)

### Tool Count Context
- Pre-Phase 14: 103 tools (18 domains)
- Phase 14 added: ~60-80 new tools (delete tools everywhere + upsert/log tools for uncovered tables + junction tools + books/acts/eras CRUD)
- Post-Phase 14 estimated total: ~165-183 tools
- Researcher should count actual tools from source to get precise total before documentation

</code_context>

<specifics>
## Specific Ideas

- User deferred all implementation decisions to Claude — "best for long-term project management and best user experience"
- The 18 tool module domain names provide a consistent taxonomy that makes `docs/tools/characters.md` and `docs/schema/characters.md` obviously paired — navigability win
- Deleting the monoliths is the right call: per-domain files are only useful if the monolith is gone; otherwise per-domain files just become another stale copy

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 15-documentation-restructure*
*Context gathered: 2026-03-09*
