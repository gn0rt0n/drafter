# Phase 15: Documentation Restructure - Research

**Researched:** 2026-03-09
**Domain:** Markdown documentation authoring, file-split refactoring, tool inventory extraction
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Domain taxonomy:**
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

**Output directory structure:**
- `docs/tools/` — 18 per-domain tool reference files (e.g., `docs/tools/characters.md`)
- `docs/schema/` — 18 per-domain schema files (e.g., `docs/schema/characters.md`)
- `docs/README.md` — master index (overhauled from current 170-line architecture overview)

**Monolith fate:**
- Delete `docs/mcp-tools.md` and `docs/schema.md` entirely after the split
- No redirect stubs — the master index at `docs/README.md` serves as the navigation entry point
- Clean break: no zombie monoliths that could go stale alongside per-domain files

**Master index:**
- Overhaul existing `docs/README.md` (currently 170 lines of architecture overview) into the master index
- Keep architecture overview content — condense it and move it to a brief preamble
- Add a full links section: every per-domain tool file and every per-domain schema file, organized by domain
- No separate `docs/index.md` — README.md is the universally understood entry point
- Structure: preamble (what Drafter is) → Tools Reference section (18 domain links) → Schema Reference section (18 domain links) → quick stats (total tools, total tables)

**Content update before split (critical):**
- mcp-tools.md must be updated to document all Phase 14 new tools BEFORE splitting
  - Current state: 103 tools (as of Phase 11); Phase 14 added 128 new tools
  - Each tool's documentation: name, parameters, return type, gate status (Free/Gated), one-line description — matching existing mcp-tools.md format
- schema.md must be updated to add read-only justifications BEFORE splitting
  - Two tables are intentionally read-only: `schema_migrations` (managed by migration runner) and `architecture_gate` (managed exclusively through `certify_gate` tool flow)
  - Each read-only table entry should include a "Read-only: [justification]" note in the schema docs
  - All other 69 tables now have write tools (Phase 14 complete)

**Per-domain file content scope:**
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

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| DOCS-01 | docs/mcp-tools.md updated to reflect newly added write tools from MCP phase, then split into per-domain files | 128 new tools identified from source audit; exact tool list per domain and gate status documented in this research |
| DOCS-02 | docs/schema.md updated to reflect read-only justifications and any new write tools from MCP phase, then split into per-domain files | 2 read-only tables identified (schema_migrations, architecture_gate); schema section-to-domain mapping resolved; utility table assignment resolved |
| DOCS-03 | Master index file (docs/README.md or docs/index.md) links to all per-domain doc files | docs/README.md is the target; 18 tool domains + 18 schema domains = 36 links required |
</phase_requirements>

---

## Summary

Phase 15 is a pure documentation task — no Python source changes. The monolithic `docs/mcp-tools.md` (2615 lines, 103 tools documented) and `docs/schema.md` (2741 lines) are out of date and need restructuring into 18 per-domain files each. The primary content gap is that Phase 14 added 128 new tools that are not yet documented anywhere.

The work proceeds in three sequential steps: (1) update `docs/mcp-tools.md` with all 128 Phase 14 additions, (2) update `docs/schema.md` with read-only justifications for the 2 intentionally read-only tables, (3) split both monoliths into `docs/tools/{domain}.md` and `docs/schema/{domain}.md` — 36 new files total — then delete the two monoliths and overhaul `docs/README.md` into the master index.

The tool source files in `src/novel/tools/` are the authoritative source for tool count, names, signatures, and gate status. The existing monolith format (per-tool entries with Parameters table, Returns, Invocation reason, Gate status, Tables touched) is the template to replicate for all 128 new tool entries.

**Primary recommendation:** Treat the split as a mechanical extraction task. All content already exists in the monolith or the source code. No new content is invented — every piece of documentation comes from either the existing monolith (pre-Phase-14 tools) or the Python source (Phase 14 additions).

---

## Current State Audit

### Tool Count: Source vs. Documentation

| Metric | Value |
|--------|-------|
| Tools in `docs/mcp-tools.md` (documented) | 103 |
| Tools in `src/novel/tools/` (implemented) | 231 |
| Tools not yet documented (Phase 14 additions) | 128 |
| Gate-free tools total | 153 |
| Gated tools total | 78 |

### Phase 14 New Tools by Domain

These 128 tools are implemented in source but absent from `docs/mcp-tools.md` and must be documented before the split.

| Domain | New Tools | Gate |
|--------|-----------|------|
| world | 27 | Free |
| characters | 11 | Free |
| foreshadowing | 10 | Gated (all) |
| magic | 10 | Free |
| timeline | 10 | Mixed (see per-tool note) |
| scenes | 8 | Free |
| publishing | 8 | Mixed (see per-tool note) |
| arcs | 9 | Free |
| knowledge | 7 | Gated (all) |
| session | 6 | Gated (all) |
| voice | 4 | Gated (all) |
| plot | 4 | Free |
| canon | 3 | Gated (all) |
| chapters | 3 | Free |
| relationships | 3 | Free |
| names | 2 | Free |
| structure | 2 | Free |
| gate | 1 | Free |

**Total: 128 new tools across 18 domains**

### Timeline Module: Per-Tool Gate Status (Mixed)

The timeline module is unique — delete and junction tools are gate-free, CRUD tools are gated.

| New Tool | Gate Status |
|----------|-------------|
| `log_travel_segment` | Free |
| `delete_event` | Free |
| `delete_pov_position` | Free |
| `delete_travel_segment` | Free |
| `add_event_participant` | Free |
| `remove_event_participant` | Free |
| `get_event_participants` | Free |
| `add_event_artifact` | Free |
| `remove_event_artifact` | Free |
| `get_event_artifacts` | Free |

### Publishing Module: Per-Tool Gate Status (Mixed)

| New Tool | Gate Status |
|----------|-------------|
| `delete_publishing_asset` | Free |
| `delete_submission` | Free |
| `get_documentation_tasks` | Free |
| `upsert_documentation_task` | Free |
| `delete_documentation_task` | Free |
| `get_research_notes` | Free |
| `upsert_research_note` | Free |
| `delete_research_note` | Free |

### Complete Post-Phase-14 Tool Roster by Domain

| Domain | Total Tools | Free | Gated |
|--------|------------|------|-------|
| arcs | 15 | 15 | 0 |
| canon | 10 | 0 | 10 |
| chapters | 8 | 8 | 0 |
| characters | 19 | 19 | 0 |
| foreshadowing | 18 | 0 | 18 |
| gate | 6 | 6 | 0 |
| knowledge | 12 | 0 | 12 |
| magic | 14 | 14 | 0 |
| names | 6 | 6 | 0 |
| plot | 7 | 7 | 0 |
| publishing | 13 | 8 | 5 |
| relationships | 9 | 9 | 0 |
| scenes | 12 | 12 | 0 |
| session | 16 | 0 | 16 |
| structure | 6 | 6 | 0 |
| timeline | 18 | 10 | 8 |
| voice | 9 | 0 | 9 |
| world | 33 | 33 | 0 |
| **TOTAL** | **231** | **153** | **78** |

### Schema Read-Only Tables (for DOCS-02)

From `14-READ-ONLY-AUDIT.md` (HIGH confidence — source document from Phase 14):

| Table | Read-Only Justification |
|-------|------------------------|
| `schema_migrations` | Managed exclusively by the migration runner (`novel db migrate`). Writing outside the runner corrupts migration state and could cause destructive re-runs or skipped migrations. No MCP read or write tool exposed. |
| `architecture_gate` | Managed exclusively through the `certify_gate` tool flow. Exposing a direct write tool would bypass the gate enforcement mechanism. Note: `gate_checklist_items` (child table) DOES have write coverage via `delete_gate_checklist_item`. |

All other 69 tables have at least one MCP write tool as of Phase 14 completion.

### Schema Section → Domain File Mapping

The existing `schema.md` has 16 numbered sections. The locked decision splits these into 18 domain files matching tool module names.

| schema.md Section | Target Domain File | Notes |
|-------------------|--------------------|-------|
| System Integration (intro flowchart) | `docs/schema/README.md` or preamble in master index | Cross-domain — may become master index intro |
| 1. Foundation | Split: `structure.md` | eras, books → structure domain owns these |
| 2. Structure | `structure.md` | acts, story_structure, arc_seven_point_beats |
| 3. World | `world.md` | cultures, factions, locations, artifacts, magic_system_elements, supernatural_elements, faction_political_states, object_states |
| 4. Characters | `characters.md` | characters, character_knowledge, character_beliefs, character_locations, injury_states, title_states |
| 5. Chapters & Scenes | `chapters.md` + `scenes.md` | Split: chapters/pacing_beats/tension_measurements/chapter_obligations/chapter_plot_threads → chapters.md; scenes/scene_character_goals → scenes.md |
| 6. Relationships | `relationships.md` | character_relationships, relationship_change_events, perception_profiles |
| 7. Timeline & Events | `timeline.md` | events, event_participants, event_artifacts, travel_segments, pov_chronological_position |
| 8. Plot & Arcs | `plot.md` + `arcs.md` | Split: plot_threads/chapter_plot_threads → plot.md; character_arcs/chapter_character_arcs/arc_health_log/chekovs_gun_registry/subplot_touchpoint_log → arcs.md |
| 9. Gate & Metrics | `gate.md` | architecture_gate, gate_checklist_items, project_metrics_snapshots, pov_balance_snapshots |
| 10. Session | `session.md` | session_logs, agent_run_log, open_questions, decisions_log |
| 11. Canon & Continuity | `canon.md` | canon_facts, continuity_issues |
| 12. Knowledge & Reader | `knowledge.md` | reader_information_states, reader_reveals, dramatic_irony_inventory, reader_experience_notes |
| 13. Foreshadowing & Literary | `foreshadowing.md` | foreshadowing_registry, prophecy_registry, motif_registry, motif_occurrences, thematic_mirrors, opposition_pairs |
| 14. Voice & Names | `voice.md` + `names.md` | Split: voice_profiles/voice_drift_log/supernatural_voice_guidelines → voice.md; name_registry → names.md |
| 15. Publishing | `publishing.md` | publishing_assets, submission_tracker |
| 16. Utility | Merge into `publishing.md` | research_notes, documentation_tasks now have MCP write tools in publishing.py |

**Utility table decision (Claude's Discretion — recommendation):** Place `research_notes` and `documentation_tasks` in `docs/schema/publishing.md`. The publishing.py module owns the MCP tools for these tables (`get_research_notes`, `upsert_research_note`, `delete_research_note`, `get_documentation_tasks`, `upsert_documentation_task`, `delete_documentation_task`). Co-locating the schema tables with their tool documentation produces a single, self-contained publishing domain file. The schema.md description calling them "not writable via MCP" is now stale — Phase 14 added full MCP write coverage.

### Tables in the "Chapters & Scenes" Split

The chapters module in source owns several schema tables beyond just chapters/scenes:

**`docs/schema/chapters.md` should include:**
- `chapters`
- `chapter_structural_obligations` (owned by `upsert_chapter_obligation`/`delete_chapter_obligation` in chapters.py)
- `chapter_plot_threads` (junction table; the plot module uses it but chapters module also manages it; see note below)
- `pacing_beats` (owned by `log_pacing_beat`/`delete_pacing_beat` in scenes.py)
- `tension_measurements` (owned by `log_tension_measurement`/`delete_tension_measurement` in scenes.py)

**`docs/schema/scenes.md` should include:**
- `scenes`
- `scene_character_goals`

Note: `chapter_plot_threads` is a junction table referenced by both chapters.py and plot.py. The planner should decide whether it lives in `chapters.md` (chapters own the chapter FK side) or `plot.md` (plot threads are the core entity). Recommendation: put it in `plot.md` since plot threads are the entity being linked — mirrors how `arc_seven_point_beats` lives in `structure.md` (the arc side) not `arcs.md`.

Similarly, `chapter_character_arcs` (junction table) should live in `arcs.md` since character arcs are the entity being tracked across chapters.

---

## Architecture Patterns

### Recommended File Structure After Split

```
docs/
├── README.md                  # Master index (overhauled)
├── tools/
│   ├── arcs.md
│   ├── canon.md
│   ├── chapters.md
│   ├── characters.md
│   ├── foreshadowing.md
│   ├── gate.md
│   ├── knowledge.md
│   ├── magic.md
│   ├── names.md
│   ├── plot.md
│   ├── publishing.md
│   ├── relationships.md
│   ├── scenes.md
│   ├── session.md
│   ├── structure.md
│   ├── timeline.md
│   ├── voice.md
│   └── world.md
└── schema/
    ├── arcs.md
    ├── canon.md
    ├── chapters.md
    ├── characters.md
    ├── foreshadowing.md
    ├── gate.md
    ├── knowledge.md
    ├── magic.md
    ├── names.md
    ├── plot.md
    ├── publishing.md
    ├── relationships.md
    ├── scenes.md
    ├── session.md
    ├── structure.md
    ├── timeline.md
    ├── voice.md
    └── world.md
```

### Pattern 1: Per-Domain Tools File Format

Each `docs/tools/{domain}.md` follows this structure (matching existing mcp-tools.md sections):

```markdown
[← Documentation Index](../README.md)

# {Domain} Tools

{Optional one-paragraph domain description}

**Gate status:** {All tools gate-free | All tools gated | Mixed — see individual entries}

**{N} tools**

## Index

| Tool Name | Gate | Description |
|-----------|------|-------------|
| `tool_name` | Free/Gated | One-line description |

---

## `tool_name`

**Purpose:** {description}

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|

**Returns:** {type} — {description}

**Invocation reason:** {when an AI agent would call this tool}

**Gate status:** Gate-free. / Gated — returns GateViolation if gate not certified.

**Tables touched:** Reads `x`. Writes `y`.

---
```

### Pattern 2: Per-Domain Schema File Format

Each `docs/schema/{domain}.md` follows this structure (matching existing schema.md sections):

```markdown
[← Documentation Index](../README.md)

# {Domain} Schema

{Optional one-paragraph description of what these tables model}

```mermaid
erDiagram
    {tables and relationships}
```

> **Cross-domain FKs:** {list FKs that cross domain boundaries, or "None."}

## `table_name`

{One-sentence description of table purpose}

| Field | Type | Description |
|-------|------|-------------|

**Constraints:** {UNIQUE, CHECK constraints if any}

**Populated by:** {which MCP tools write this table, or "Read-only: {justification}"}

---
```

### Pattern 3: Master Index (docs/README.md) Structure

```markdown
# Drafter Documentation

{Brief preamble: what Drafter is, 3 layers, link to architecture overview}

## Tools Reference

| Domain | Tools | Gate |
|--------|-------|------|
| [Characters](tools/characters.md) | 19 | Free |
...

## Schema Reference

| Domain | Tables | File |
|--------|--------|------|
| [Characters](schema/characters.md) | 6 | characters, character_knowledge, ... |
...

## Quick Stats

- **Total MCP tools:** 231 (153 Free, 78 Gated)
- **Total schema tables:** 71 (69 with MCP write coverage, 2 intentionally read-only)
- **Migrations:** 22
```

### Anti-Patterns to Avoid

- **Zombie monolith:** Leaving `docs/mcp-tools.md` or `docs/schema.md` in place after creating per-domain files. Per decision: delete both monoliths after split.
- **Stale "Populated by" notes in schema.md:** Several schema sections still say "Not writable via MCP — CLI seed data or direct DB insert only" for tables that Phase 14 gave full MCP write coverage (eras, books, acts — now owned by world.py). These must be corrected.
- **Wrong tool count in headers:** Current mcp-tools.md says "8 tools" for Characters domain but source has 19. Every per-domain file header must state the correct current tool count.
- **Missing navigation links:** Each per-domain file must include the `[← Documentation Index](../README.md)` back-link at the top so readers can always return to the index.
- **Cross-domain Mermaid diagrams:** The top-level System Integration Mermaid in schema.md shows all 16 domains. Do not copy this into individual domain files — it won't be accurate at domain scope. Per-domain Mermaid diagrams should only show tables within that domain (with FK stubs to external tables).
- **Splitting before updating:** Do not split the monoliths before adding Phase 14 content. The update must come first; otherwise the per-domain files will be created with the 103-tool stale content.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Tool signature extraction | Manual reading of all 18 Python files | Python AST via `python3 -c "import ast..."` | 18 files × many parameters each; AST is exact, manual is error-prone |
| Markdown link generation | Hand-typing 36 relative links | Pattern: `[Domain](tools/{domain}.md)` | Consistent relative paths from `docs/` root |
| Tool count verification | Counting by hand | `grep -c "@mcp.tool()" src/novel/tools/{domain}.py` | 231 tools; manual count will drift |

---

## Common Pitfalls

### Pitfall 1: Stale "Populated by" Claims in Schema

**What goes wrong:** Several schema.md sections still document tables as "Not writable via MCP" (eras, books, acts, research_notes, documentation_tasks). These tables now have Phase 14 MCP write tools. Copying these sections verbatim into per-domain schema files propagates inaccurate documentation.

**Why it happens:** schema.md was accurate as of Phase 11. Phase 14 added write tools for previously read-only tables.

**How to avoid:** Before splitting, check every "Populated by" note. If a table now has an MCP write tool in source, update the note to reference the correct tool name. Tables that need correction: `eras` (now: `upsert_era`, `delete_era` in world.py), `books` (now: `upsert_book`, `delete_book` in world.py), `acts` (now: `upsert_act`, `delete_act` in world.py), `research_notes` (now: `upsert_research_note`, `delete_research_note` in publishing.py), `documentation_tasks` (now: `upsert_documentation_task`, `delete_documentation_task` in publishing.py).

**Warning signs:** Any "Populated by" note containing "CLI seed data only" or "Not writable via MCP" for non-system tables.

### Pitfall 2: Wrong Tool Count in Domain Headers

**What goes wrong:** mcp-tools.md currently shows "8 tools" for Characters domain. After Phase 14 additions, Characters has 19 tools. Copying the header verbatim produces incorrect counts.

**Why it happens:** The old per-domain header counts were accurate for Phase 11. Phase 14 added 11 new tools to Characters alone.

**How to avoid:** Set domain tool counts from the source, not from the old documentation. Reference the Complete Post-Phase-14 Tool Roster table in this research document.

**Warning signs:** Any domain header showing a count that matches the pre-Phase-14 totals (Characters: 8, Scenes: 4, World: 6, etc.).

### Pitfall 3: Missing Tools in Index Tables

**What goes wrong:** If a per-domain tools file is created by copying the relevant mcp-tools.md section without first adding Phase 14 tools, the index table at the top of each domain file will be incomplete.

**Why it happens:** It's easy to copy the existing section and forget that 128 new tools aren't in the monolith yet.

**How to avoid:** The update-before-split approach prevents this. Add all Phase 14 tools to the global index in mcp-tools.md first; then the split extracts complete content.

**Warning signs:** Domain tool counts in per-domain file headers that don't match the source counts above.

### Pitfall 4: Mermaid Diagram Accuracy After Schema Split

**What goes wrong:** Some schema.md Mermaid ER diagrams show FKs to tables in other domains (e.g., the World domain diagram shows `characters` and `chapters` entities for FK lines). If copied directly into domain-scoped files, diagrams show tables that don't belong to the domain — misleading readers.

**Why it happens:** The monolith could show all cross-domain FKs in context. Per-domain files can't.

**How to avoid:** When copying Mermaid diagrams, include only tables that belong to the domain. For cross-domain FKs, add a `> **Cross-domain FKs:**` prose note (already the pattern in schema.md). If a diagram becomes too sparse after removing external tables, omit the diagram and rely on the table-by-table prose format.

### Pitfall 5: relative path errors in navigation links

**What goes wrong:** A link written as `[← Documentation Index](docs/README.md)` in a per-domain file under `docs/tools/` resolves to `docs/docs/README.md` — a broken path.

**Why it happens:** Per-domain files live at `docs/tools/{domain}.md`, so the relative path to the parent `docs/README.md` is `../README.md`, not `docs/README.md`.

**How to avoid:** Use `../README.md` for all back-to-index links in both `docs/tools/` and `docs/schema/` files. The master index at `docs/README.md` links forward using relative paths `tools/{domain}.md` and `schema/{domain}.md`.

---

## Code Examples

### Extracting Tool Signatures from Source (Authoritative Technique)

```bash
# Count tools per module
python3 -c "
import ast, os
tools_dir = 'src/novel/tools'
for fname in sorted(os.listdir(tools_dir)):
    if not fname.endswith('.py') or fname.startswith('_'):
        continue
    with open(f'{tools_dir}/{fname}') as f: src = f.read()
    tree = ast.parse(src)
    domain = fname[:-3]
    count = sum(1 for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        for d in node.decorator_list
        if isinstance(d, ast.Call) and hasattr(d.func, 'attr') and d.func.attr == 'tool')
    print(f'{domain}: {count}')
"
```

### Checking Gate Status of a Tool in Source

```bash
# Check if a specific tool calls check_gate()
grep -A 20 "async def delete_session_log" src/novel/tools/session.py | grep "check_gate"
```

### Verifying All Source Tools Are Documented (Diff Check)

```bash
python3 -c "
import ast, os

# Get source tools
tools_dir = 'src/novel/tools'
source_tools = set()
for fname in os.listdir(tools_dir):
    if not fname.endswith('.py') or fname.startswith('_'): continue
    with open(f'{tools_dir}/{fname}') as f: src = f.read()
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for d in node.decorator_list:
                if isinstance(d, ast.Call) and hasattr(d.func, 'attr') and d.func.attr == 'tool':
                    source_tools.add(node.name)

# Get documented tools from updated monolith
with open('docs/mcp-tools.md') as f:
    lines = f.readlines()
documented = set()
in_index = False
for line in lines:
    if line.strip() == '## Index': in_index = True; continue
    if in_index and line.startswith('## '): break
    if in_index and line.startswith('| \`'):
        documented.add(line.split('\`')[1])

undocumented = source_tools - documented
print(f'Undocumented tools: {len(undocumented)}')
if undocumented: print(sorted(undocumented))
"
```

### Per-Domain Tools File Template (Characters example)

```markdown
[← Documentation Index](../README.md)

# Characters Tools

Manages the core character registry and all character-state logs (injuries, beliefs,
knowledge, location, title states). All tools are gate-free — character data is needed
during both worldbuilding and prose phases.

**Gate status:** All tools in this domain are gate-free.

**19 tools**

## Index

| Tool Name | Gate | Description |
|-----------|------|-------------|
| `get_character` | Free | Look up a single character by ID |
| `list_characters` | Free | Return all characters ordered alphabetically |
...

---

## `get_character`

**Purpose:** Look up a single character by primary key, returning all character fields.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `character_id` | `int` | Yes | Primary key of the character to retrieve |

**Returns:** `Character | NotFoundResponse`

**Gate status:** Gate-free.

**Tables touched:** Reads `characters`.

---
```

---

## Execution Order (Critical)

The planner MUST structure plans in this order to avoid creating incomplete per-domain files:

1. **Wave 1: Update mcp-tools.md** — Add all 128 Phase 14 tools to the monolith (global index + per-domain sections). This is a content update, not a split. Verify: tool count in docs equals 231.

2. **Wave 2: Update schema.md** — Add "Read-only: [justification]" notes to `schema_migrations` and `architecture_gate`. Correct stale "Populated by" notes for eras, books, acts, research_notes, documentation_tasks.

3. **Wave 3: Split mcp-tools.md** — Create `docs/tools/` directory, extract each of the 18 domain sections into `docs/tools/{domain}.md`, add `[← Documentation Index](../README.md)` to each file.

4. **Wave 4: Split schema.md** — Create `docs/schema/` directory, extract/merge schema sections per the domain mapping table above, add `[← Documentation Index](../README.md)` to each file. Assign "Utility" tables to `publishing.md`.

5. **Wave 5: Overhaul docs/README.md** — Replace current 170-line architecture overview with master index. Condense architecture content into preamble. Add Tools Reference table (18 rows) and Schema Reference table (18 rows). Update quick stats to 231 tools / 71 tables.

6. **Wave 6: Delete monoliths** — Delete `docs/mcp-tools.md` and `docs/schema.md`. Verify no remaining references in tracked files point to deleted paths.

---

## Open Questions

1. **chapter_plot_threads table assignment**
   - What we know: `chapter_plot_threads` is a junction table with FKs to both `chapters` and `plot_threads`. The plot.py module provides `link_chapter_to_plot_thread` / `unlink_chapter_from_plot_thread` / `get_plot_threads_for_chapter` tools.
   - What's unclear: Whether schema file should live in `chapters.md` or `plot.md`
   - Recommendation: Place in `plot.md`. The junction exists to attach chapters to plot threads — plot threads are the entity. Mirrors the `arc_seven_point_beats` pattern (lives in structure.md because structure.py owns it).

2. **System Integration Mermaid flowchart (top-level schema.md overview)**
   - What we know: The cross-domain dependency flowchart at the top of schema.md is a high-level system view that spans all 16 domains.
   - What's unclear: Whether it belongs in the master index README.md or gets dropped.
   - Recommendation: Include a condensed version in `docs/README.md` master index as part of the architecture preamble. It provides navigation context. Do not include it in any per-domain schema file.

3. **Domain descriptions in per-domain files**
   - What we know: CONTEXT.md gives Claude discretion on whether to add a brief one-paragraph domain description.
   - What's unclear: The effort tradeoff — 36 files × potentially writing fresh descriptions.
   - Recommendation: Yes, add descriptions. The existing mcp-tools.md domain section headers already have good one-paragraph descriptions (example: "Characters domain: Manages the core character registry..."). Copy and adapt these rather than writing from scratch. For new domains (world's expanded scope, structure's expanded scope), the description should note Phase 14 additions.

---

## Sources

### Primary (HIGH confidence)
- `src/novel/tools/*.py` — authoritative source for all 231 tool names, signatures, and gate status; verified via AST parse
- `docs/mcp-tools.md` — authoritative source for existing 103-tool documentation format and content
- `docs/schema.md` — authoritative source for existing 71-table schema documentation format and content
- `.planning/phases/14-mcp-api-completeness/14-READ-ONLY-AUDIT.md` — authoritative list of 2 intentionally read-only tables with justifications

### Secondary (MEDIUM confidence)
- `.planning/phases/15-documentation-restructure/15-CONTEXT.md` — user decisions on domain taxonomy, file structure, and content scope
- `.planning/STATE.md` — Phase 14 implementation decisions; cross-references gate status patterns per domain

### Tertiary (LOW confidence)
- None — all findings verified from source files

---

## Metadata

**Confidence breakdown:**
- Tool inventory (current tools, counts, gate status): HIGH — extracted directly from Python source via AST
- Schema section mapping: HIGH — extracted directly from schema.md structure + tool module ownership
- Read-only table justifications: HIGH — from Phase 14 read-only audit document
- Documentation format patterns: HIGH — extracted from existing monolith files
- Utility table placement: MEDIUM — recommendation based on tool ownership logic; planner may override

**Research date:** 2026-03-09
**Valid until:** Stable — documentation phase. Only invalidated if new tools are added to src/novel/tools/ before Phase 15 executes.
