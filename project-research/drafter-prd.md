# Product Requirements Document
## Epic Fantasy Novel — Claude Code Plugin Ecosystem
### Version 1.1 — Updated for Official Plugin Architecture

---

## Changelog from v1.0

- **Single plugin structure**: The entire ecosystem ships as one Claude Code plugin (`novel-plugin/`), not as a separate tooling repo with a bolted-on plugin. The Python implementation repo still exists, but it's the engine — the plugin is the interface.
- **Correct MCP placement**: `.mcp.json` lives at the plugin root, not inside `.mcp/novel-server/`.
- **Skills vs Agents split**: Architects and editors are `agents/` (deliberate invocation). Craft and continuity roles are `skills/` (auto-activate on context). See Section 5 for the full mapping.
- **Slash commands**: Key CLI operations are exposed as both slash commands (inside the plugin) and terminal commands (via the Python `novel` CLI). They share the same underlying implementation.
- **Build tooling**: The plugin is scaffolded with `/plugin-dev:create-plugin`. Individual skills are built and evaluated with `skill-creator`. Both are official Anthropic plugins installed separately before build begins.

---

## 1. Executive Summary

This document specifies the complete system for building, operating, and maintaining a 250,000-word epic fantasy novel using Claude Code as the primary development environment. The system treats a novel at this scale the same way a senior engineer treats a large software project: structured data, version control, modular tooling, and specialized agents with narrow responsibilities.

The ecosystem has four integrated layers:

1. **One Claude Code Plugin (`novel-plugin/`)** — Contains all 40 agent roles, split between `agents/` (architects and editors, deliberately invoked) and `skills/` (craft and continuity, auto-activated by context). Also contains slash commands and MCP server configuration. This is what you install into Claude Code.
2. **A Python MCP Server** — Exposes the SQLite narrative database as structured tool calls. Lives in the Python implementation repo, referenced by the plugin's `.mcp.json`.
3. **A SQLite Narrative Database** — The single authoritative source of truth for all story data. Markdown files are generated outputs, not editable sources.
4. **A UV/Python CLI** — `novel` command with subcommands for migrations, exports, imports, backups, and queries. Runs from the terminal. Key operations are also available as plugin slash commands.

**Core workflow constraint embedded throughout this spec**: No prose is written until the architecture is 100% complete and certified by the Architecture Completeness Auditor agent. Agent and skill definitions enforce this — prose-phase roles will refuse to operate without a gate certification in the database.

---

## 2. Reference Documents

- `./plugin-ecosystem.md` — Original ecosystem overview
- `./agent-roster.md` — Full definitions for all 40 agents, phasing, handoff points, sample invocations
- `./database-schema.md` — Complete SQLite schema: all tables, fields, relationships, agent ownership map

This PRD does not re-document those systems. It specifies how to build them.

---

## 3. Technology Decisions

### 3.1 Database: SQLite

Single-file database that lives in the project repo. No server setup, travels with git, queryable directly from the terminal. Migration-based rebuild: the `.db/` directory is git-tracked, the database file itself is in `.gitignore`. Schema lives in numbered migration files; `novel db migrate` rebuilds from scratch on any machine.

### 3.2 MCP Server: Python + UV

Implemented as a Python package using the `mcp` SDK. Managed and run via `uv` — no global installs required. The plugin's `.mcp.json` points to the server with a `uv run` invocation and a `NOVEL_DB_PATH` environment variable.

Agents and skills never write raw SQL. They call named MCP tools with typed parameters and receive structured JSON responses.

### 3.3 Scripts: UV/Python CLI

The `novel` command wraps all operational scripts as subcommands. Individual script files remain directly runnable for development. Key `novel` subcommands are mirrored as plugin slash commands for Claude Code access.

### 3.4 Plugin: Official Claude Code Plugin Structure

The entire Claude Code integration is packaged as a single plugin using the official structure from `anthropics/claude-plugins-official`. The plugin is built using the `/plugin-dev:create-plugin` guided workflow (8 phases: Discovery → Component Planning → Detailed Design → Structure Creation → Implementation → Validation → Testing → Documentation). Individual skills are built and optimized using the `skill-creator` plugin.

---

## 4. Repository and Plugin Structure

### 4.1 Novel Content Repo (`/your-novel-name/`)

Your existing project, extended with the database directory. The plugin and Python tools live elsewhere; this repo stays focused on story content.

```
/your-novel-name/
│
├── .db/
│   ├── novel.sqlite               # Database (gitignored)
│   └── migrations/
│       ├── 001_core_entities.sql
│       ├── 002_characters.sql
│       └── ...                    # 21 migration files total
│
├── .claude/
│   └── settings.json              # Registers the novel-plugin
│
├── CLAUDE.md                      # Updated root context (see Section 9)
│
├── 00-Dashboard/
├── 01-Story-Bible/                # Generated from DB after initial import
├── 02-Structure/                  # Generated from DB after initial import
├── 03-Chapters/                   # Generated from DB after initial import
├── 04-Scene-Work/
├── 05-Style/                      # Authoritative source — NOT generated
├── 06-Research/                   # Authoritative source — NOT generated
├── 07-Artwork/
└── 08-Publishing/                 # Generated from DB after initial import
```

### 4.2 Python Implementation Repo (`/novel-tools/`)

The engine. Contains the MCP server, CLI, migrations, and import/export scripts. No story content lives here.

```
/novel-tools/
│
├── pyproject.toml
├── uv.lock
│
├── novel/                         # The `novel` CLI package
│   ├── cli.py
│   ├── db/                        # migrate, backup, connection
│   ├── export/                    # characters, chapters, world, timeline, publishing
│   ├── import_/                   # parse existing markdown, map to schema
│   ├── queries/                   # pov_balance, arc_health, thread_gaps, etc.
│   ├── gate/                      # check, status, certify
│   └── session/                   # start, close
│
└── mcp/
    └── novel_server/
        ├── server.py              # MCP entry point, tool registration
        ├── db.py                  # Connection management
        ├── models.py              # Pydantic input/output types
        ├── tools/                 # One file per domain (14 domains)
        └── validators/            # magic, timeline, names, gate
```

### 4.3 The Plugin (`/novel-plugin/`)

The Claude Code integration layer. This is what gets installed into Claude Code. It wraps and exposes the Python tools.

```
/novel-plugin/
│
├── .claude-plugin/
│   └── plugin.json                # Plugin manifest
│
├── .mcp.json                      # Points to novel_server via uv run
│
├── commands/                      # Slash commands (mirrors key novel CLI ops)
│   ├── session-start.md           # /novel:session-start
│   ├── session-close.md           # /novel:session-close
│   ├── gate-check.md              # /novel:gate-check
│   ├── gate-status.md             # /novel:gate-status
│   ├── pov-balance.md             # /novel:pov-balance
│   ├── arc-health.md              # /novel:arc-health
│   ├── thread-gaps.md             # /novel:thread-gaps
│   ├── export-chapter.md          # /novel:export-chapter [n]
│   └── export-all.md              # /novel:export-all
│
├── agents/                        # Architects + editors (explicit invocation)
│   ├── story-architect.md
│   ├── plot-systems-engineer.md
│   ├── subplot-coordinator.md
│   ├── chapter-architect.md
│   ├── scene-builder.md
│   ├── arc-tracker.md
│   ├── pov-manager.md
│   ├── character-architect.md
│   ├── world-architect.md
│   ├── magic-system-engineer.md
│   ├── political-systems-analyst.md
│   ├── canon-keeper.md
│   ├── developmental-editor.md
│   ├── reader-experience-simulator.md
│   ├── architecture-completeness-auditor.md
│   ├── session-continuity-manager.md
│   ├── project-manager.md
│   ├── publishing-preparation-agent.md
│   ├── genre-analyst.md
│   └── research-agent.md
│
├── skills/                        # Craft + continuity (auto-activate)
│   ├── pacing-tension-analyst/
│   │   └── SKILL.md
│   ├── timeline-manager/
│   │   └── SKILL.md
│   ├── names-linguistics/
│   │   └── SKILL.md
│   ├── character-voice-auditor/
│   │   └── SKILL.md
│   ├── relationship-dynamics/
│   │   └── SKILL.md
│   ├── perception-profiles/
│   │   └── SKILL.md
│   ├── continuity-editor/
│   │   └── SKILL.md
│   ├── foreshadowing-tracker/
│   │   └── SKILL.md
│   ├── symbolism-motif-tracker/
│   │   └── SKILL.md
│   ├── thematic-architecture/
│   │   └── SKILL.md
│   ├── information-state-tracker/
│   │   └── SKILL.md
│   ├── prose-writer/
│   │   └── SKILL.md
│   ├── dialogue-specialist/
│   │   └── SKILL.md
│   ├── battle-action-coordinator/
│   │   └── SKILL.md
│   ├── sensory-atmosphere/
│   │   └── SKILL.md
│   ├── supernatural-voice/
│   │   └── SKILL.md
│   ├── line-editor/
│   │   └── SKILL.md
│   ├── copy-editor/
│   │   └── SKILL.md
│   ├── chapter-hook-specialist/
│   │   └── SKILL.md
│   └── lore-keeper/
│       └── SKILL.md
│
└── README.md
```

---

## 5. Agents vs Skills — The Design Rationale

### 5.1 Why the Split

**Agents** are invoked deliberately. You call them when you need a structured work session with a clear start, defined inputs, and a specific output. Architects produce documents. Editors produce assessments. Gate agents produce certifications or gap reports. These are not ambient — you sit down and say "I'm working with the Story Architect right now."

**Skills** are ambient. They activate when the context matches. When you're writing a scene, the Continuity Editor, Timeline Manager, and Voice Auditor should be watching passively — flagging issues without being explicitly summoned. Craft skills fire when you're doing craft work. Tracking skills fire when you're creating story content that touches their domain.

### 5.2 The 20 Agents (Architects + Editors)

| Agent | Role | Phase |
|---|---|---|
| `story-architect` | Act structure, thematic throughline, turning points | 1, 2 |
| `plot-systems-engineer` | Cause/effect chains, Chekhov's gun registry | 2 |
| `subplot-coordinator` | Subplot lifecycle, touchpoint gaps | 2 |
| `chapter-architect` | Chapter pre-write plans, structural obligations | 3 |
| `scene-builder` | Scene briefs, dramatic questions, character goal mapping | 3 |
| `arc-tracker` | Arc shape/progress, stall detection, health logs | 2, 5+ |
| `pov-manager` | POV balance, dramatic irony inventory, thread sync | 2 |
| `character-architect` | Character sheets, emotional state, physical continuity | 1 |
| `world-architect` | Locations, factions, cultures, geographic consistency | 1 |
| `magic-system-engineer` | Magic rules, practitioner abilities, compliance | 1 |
| `political-systems-analyst` | Faction political states, dynamic political map | 1, 2 |
| `canon-keeper` | Authoritative canon facts, decisions log | Ongoing |
| `developmental-editor` | Big-picture story health, Phase 4 gate review | 4 |
| `reader-experience-simulator` | First-time reader perspective, confusion flags | 4 |
| `architecture-completeness-auditor` | Gate certification, blocking gap report | 4 (gate) |
| `session-continuity-manager` | Session start/close, open items, handoffs | Ongoing |
| `project-manager` | Progress metrics, word count, scope drift | Ongoing |
| `publishing-preparation-agent` | Query letters, synopses, submission tracker | 7 |
| `genre-analyst` | Comp titles, genre conventions, market positioning | 7 |
| `research-agent` | Real-world research with web search | All |

### 5.3 The 20 Skills (Craft + Continuity)

| Skill | Auto-activates when... | Phase |
|---|---|---|
| `pacing-tension-analyst` | Discussing chapter rhythm, tension curves, beat patterns | 2+ |
| `timeline-manager` | Working with chronology, travel, time jumps, POV positions | 1+ |
| `names-linguistics` | Naming characters, places, factions; cultural consistency | 1+ |
| `character-voice-auditor` | Writing or reviewing dialogue; checking voice consistency | 3+ |
| `relationship-dynamics` | Discussing how characters interact, change, affect each other | 2+ |
| `perception-profiles` | Describing how one character perceives another | 2+ |
| `continuity-editor` | Creating new story content; reviewing scenes or chapters | 3+ |
| `foreshadowing-tracker` | Planting or paying off story elements | 2+ |
| `symbolism-motif-tracker` | Working with recurring imagery, symbols, objects | 2+ |
| `thematic-architecture` | Discussing mirrors, foils, opposition pairs | 2+ |
| `information-state-tracker` | Working with reveals, reader knowledge, dramatic irony | 2+ |
| `prose-writer` | Drafting actual prose (requires gate certification) | 5 |
| `dialogue-specialist` | Writing or reviewing conversation | 3+ |
| `battle-action-coordinator` | Planning or writing action sequences | 3+ |
| `sensory-atmosphere` | Writing scene settings; establishing place and mood | 3+ |
| `supernatural-voice` | Writing scenes involving supernatural elements | 3+ |
| `line-editor` | Reviewing or polishing existing prose | 6 |
| `copy-editor` | Final mechanical review, name consistency, grammar | 6 |
| `chapter-hook-specialist` | Writing or reviewing chapter openings and closings | 3+ |
| `lore-keeper` | After any content change that affects the story bible | 5+ |

---

## 6. Plugin Components in Detail

### 6.1 Plugin Manifest (`.claude-plugin/plugin.json`)

```json
{
  "name": "novel-plugin",
  "description": "Epic fantasy novel management system. Skills, agents, commands, and MCP tools for managing a long-form novel project with Claude Code.",
  "version": "1.0.0",
  "author": {
    "name": "Odin Development Corporation"
  }
}
```

### 6.2 MCP Server Registration (`.mcp.json`)

```json
{
  "mcpServers": {
    "novel": {
      "command": "uv",
      "args": [
        "run",
        "--project",
        "/path/to/novel-tools",
        "novel-mcp"
      ],
      "env": {
        "NOVEL_DB_PATH": "/path/to/your-novel/.db/novel.sqlite"
      }
    }
  }
}
```

Note: The path values are set once during installation and are local to each machine. The plugin repo itself stores placeholder values; actual paths are configured per-machine in the novel project's `.claude/settings.json` which overrides the plugin defaults.

### 6.3 Slash Commands

Commands mirror the most commonly needed `novel` CLI operations so they're accessible without leaving Claude Code. Each command file is a markdown file with YAML frontmatter that invokes the corresponding CLI subcommand via bash.

Format for each command:

```markdown
---
description: Start a new writing session with briefing from the last session
---

Run `novel session start` and display the output.
```

Full command list:

| Slash Command | CLI Equivalent | Description |
|---|---|---|
| `/novel:session-start` | `novel session start` | Brief from last session, log new session |
| `/novel:session-close` | `novel session close` | Write session log, carry open items |
| `/novel:gate-check` | `novel gate check` | Full architecture completeness audit |
| `/novel:gate-status` | `novel gate status` | Current gate status + blocking count |
| `/novel:pov-balance` | `novel query pov-balance` | POV distribution by chapter and word count |
| `/novel:arc-health` | `novel query arc-health` | Arc progression for all POV characters |
| `/novel:thread-gaps` | `novel query thread-gaps` | Subplots overdue for a touchpoint |
| `/novel:export-chapter` | `novel export chapter $ARGUMENTS` | Regenerate a single chapter's markdown |
| `/novel:export-all` | `novel export all` | Full story bible regeneration |

### 6.4 Agent Files

Each agent is a markdown file in `agents/` with YAML frontmatter specifying role and capabilities. Claude Code can select agents automatically for subtasks, or you invoke them directly.

Agent file format:

```markdown
---
description: Story Architect — responsible for act-level structure, thematic throughline, and major turning points
capabilities:
  - Evaluate three-act health and structural integrity — act boundaries, escalation ceilings, word count proportions
  - Design key turning points using 7-point structure: Hook, Plot Turn 1, Pinch 1, Midpoint, Pinch 2, Plot Turn 2, Resolution — each mapped to a specific chapter
  - Define or revise act boundaries and map 7-point beats to specific chapters
  - Map thematic throughline to structural beats
  - Identify structural gaps and escalation failures
  - Produce chapter-level structural obligation maps
---

# Story Architect

## Role and Scope
[Full agent instructions and MCP tool guidance]
```

Agents have access to all MCP tools. Their markdown files specify which tools are primary for their role.

### 6.5 Skill Files

Each skill follows the three-level loading pattern:

- **Level 1**: Frontmatter (name + description) — always in context
- **Level 2**: SKILL.md body — loaded when skill triggers, target under 500 lines
- **Level 3**: `references/` subdirectory — loaded on demand

Skill directory structure:

```
skills/prose-writer/
├── SKILL.md
└── references/
    ├── mcp-tools.md         # Which tools this skill uses and how
    ├── gate-protocol.md     # How to check gate status before writing
    └── no-improvisation.md  # What to do when spec data is missing
```

**Gate enforcement in Phase 5 skills**: Any skill that writes prose must begin by calling `get_gate_status()`. If the status is not `passed`, it refuses and reports the current gap count. This is specified in each prose skill's `references/gate-protocol.md`, which all relevant skills load before executing.

---

## 7. MCP Server — Tool Domains

All MCP tools follow this error contract:
- Record not found → return `null` with a `not_found_message` field, never raise
- Validation failure → return a record with `is_valid: false` and `errors: []`
- Missing gate precondition → return `requires_action` field describing what must happen first

### Domain listing (14 domains, ~80 tools total)

**Characters**: `get_character`, `get_character_state`, `list_characters`, `upsert_character`, `log_character_knowledge`, `get_character_injuries`, `get_character_beliefs`

**Relationships**: `get_relationship`, `get_perception_profile`, `list_relationships`, `upsert_relationship`, `upsert_perception_profile`, `log_relationship_change`

**Chapters and Scenes**: `get_chapter`, `get_chapter_plan`, `get_chapter_obligations`, `get_scene`, `get_scene_character_goals`, `list_chapters`, `upsert_chapter`, `upsert_scene`, `upsert_scene_goal`

**Plot and Arcs**: `get_plot_thread`, `list_plot_threads`, `get_chekovs_guns`, `get_arc`, `get_arc_health`, `get_subplot_touchpoint_gaps`, `upsert_plot_thread`, `upsert_chekov`, `log_arc_health`

**Timeline**: `get_pov_positions`, `get_pov_position`, `get_event`, `list_events`, `get_travel_segments`, `validate_travel_realism`, `upsert_event`, `upsert_pov_position`

**World**: `get_location`, `get_faction`, `get_faction_political_state`, `get_culture`, `get_magic_element`, `get_practitioner_abilities`, `log_magic_use`, `check_magic_compliance`, `upsert_location`, `upsert_faction`

**Canon and Continuity**: `get_canon_facts`, `log_canon_fact`, `log_decision`, `get_decisions`, `log_continuity_issue`, `get_continuity_issues`, `resolve_continuity_issue`

**Knowledge and Reader State**: `get_reader_state`, `get_dramatic_irony_inventory`, `get_reader_reveals`, `upsert_reader_state`, `log_dramatic_irony`

**Foreshadowing and Literary**: `get_foreshadowing`, `get_prophecies`, `get_motifs`, `get_motif_occurrences`, `get_thematic_mirrors`, `get_opposition_pairs`, `log_foreshadowing`, `log_motif_occurrence`

**Names**: `check_name`, `register_name`, `get_name_registry`, `generate_name_suggestions`

**Voice and Style**: `get_voice_profile`, `get_supernatural_voice_guidelines`, `log_voice_drift`, `get_voice_drift_log`, `upsert_voice_profile`

**Gate and Architecture**: `get_gate_status`, `run_gate_audit`, `get_gate_checklist`, `update_checklist_item`, `certify_gate`

**Session and Project**: `start_session`, `close_session`, `get_last_session`, `log_agent_run`, `get_project_metrics`, `log_project_snapshot`, `get_pov_balance`, `get_open_questions`, `log_open_question`, `answer_open_question`

**Publishing**: `get_publishing_assets`, `upsert_publishing_asset`, `get_submissions`, `log_submission`, `update_submission`

---

## 8. Database — Build Specification

### 8.1 Migration Files (21 total)

```
001_core_entities.sql          -- books, acts, chapters, scenes
002_characters.sql             -- characters, character_arcs, voice_profiles
003_character_state.sql        -- knowledge, beliefs, locations, injuries, titles
004_relationships.sql          -- character_relationships, changes, perception_profiles
005_world.sql                  -- locations, factions, cultures, eras, artifacts
006_magic.sql                  -- magic_system_elements, supernatural_elements, practitioner_abilities
007_plot_arc.sql               -- plot_threads, chapter_plot_threads, character_arcs
008_plot_mechanics.sql         -- chekovs_gun_registry, subplot_touchpoint_log, structural_obligations
009_timeline.sql               -- events, participants, travel_segments, pov_chronological_position
010_pacing.sql                 -- pacing_beats, tension_measurements, scene_character_goals
011_knowledge_reader.sql       -- reader_reveals, reader_information_states, dramatic_irony_inventory
012_canon_continuity.sql       -- canon_facts, decisions_log, continuity_issues, name_registry
013_literary.sql               -- foreshadowing_registry, prophecy_registry, motif_registry, motif_occurrences
014_thematic.sql               -- thematic_mirrors, opposition_pairs, supernatural_voice_guidelines
015_world_state.sql            -- faction_political_states, magic_use_log, object_states
016_voice.sql                  -- voice_profiles, voice_drift_log
017_arc_health.sql             -- arc_health_log, pov_balance_snapshots
018_publishing.sql             -- publishing_assets, submission_tracker
019_project.sql                -- session_logs, agent_run_log, project_metrics_snapshots, open_questions
020_gate.sql                   -- architecture_gate, gate_checklist_items
021_research.sql               -- research_notes
```

### 8.2 Initial Import

After migrations, existing markdown is imported using `novel import all`. Import scripts parse each file's structure, map fields to database columns, and insert with `canon_status = 'draft'`. Unmapped fields are logged to `open_questions` for manual review. Nothing is auto-promoted to `approved` — you review and promote records as you validate them.

Import order respects foreign key dependencies:
```
novel import world        # locations, factions, cultures
novel import characters   # depends on world
novel import themes       # depends on characters
novel import structure    # depends on all above
novel import chapters     # depends on structure
novel import publishing   # standalone
```

---

## 9. Updated CLAUDE.md

```markdown
# [Novel Title] — Claude Code Configuration

## System Overview
This project uses the novel-plugin for all story work.
All canonical story data lives in `.db/novel.sqlite`.
Markdown files in 01-07 are generated outputs — do not edit them directly.

## Authoritative source files (edit these directly)
- `05-Style/` — Narrative style guides, voice guides, scene checklist
- `06-Research/` — Research notes and open questions

## Data access
All story data is available via MCP tools from the `novel` server.
Never parse markdown files for canonical facts — use MCP tool calls.

## Starting a session
Run `/novel:session-start` or `novel session start` before any work.
Run `/novel:session-close` or `novel session close` before ending.

## Checking architecture status
Run `/novel:gate-status` to see if prose writing is unlocked.
Run `/novel:gate-check` for the full completeness audit.

## Useful queries
- `/novel:pov-balance` — POV distribution across chapters
- `/novel:arc-health` — Arc progression status
- `/novel:thread-gaps` — Subplots overdue for a touchpoint

## Agents available
20 architect and editor agents are available for deliberate work sessions.
20 craft and continuity skills activate automatically based on context.
```

---

## 10. Build Sequence

### Prerequisites (Install first)
```bash
/plugin install plugin-dev      # Official plugin development toolkit
/plugin install skill-creator   # Skill authoring and eval loop
```

### Phase A — Python Foundation (Week 1)
1. Initialize `novel-tools` repo with `uv init`
2. Write all 21 migration SQL files
3. Write migration runner (`novel db migrate`) and seed script
4. Run migrations, verify schema in sqlite3 shell
5. Write import scripts in dependency order
6. Run initial import from existing markdown, review and promote records

### Phase B — MCP Server (Week 2)
1. Scaffold MCP server with `mcp` SDK
2. Implement tool domains in priority order: `characters` → `chapters` → `gate` → `world` → `relationships` → `plot` → `timeline` → `canon` → remaining domains
3. Write validators (magic compliance, travel realism, name similarity)
4. Test all tools callable from Claude Code via temporary `.claude/settings.json` registration

### Phase C — CLI Completion (Week 3)
1. Implement all `novel export`, `novel import`, `novel query`, `novel session`, `novel gate` subcommands
2. Implement `novel name` subcommands
3. Write configuration file loading

### Phase D — Plugin Scaffold (Week 3, parallel with C)
Run `/plugin-dev:create-plugin` and walk through all 8 phases:
1. **Discovery** — Describe plugin purpose: novel management system, 20 agents, 20 skills, 9 commands
2. **Component Planning** — Confirm component list: commands, agents, skills, `.mcp.json`; no hooks initially
3. **Detailed Design** — Specify each component; resolve MCP path configuration approach
4. **Structure Creation** — Scaffold all directories and manifest
5. **Component Implementation** — Use `agent-creator` for agent files; stub skill directories
6. **Validation** — Run `plugin-validator`
7. **Testing** — Verify plugin loads in Claude Code; confirm MCP tools accessible
8. **Documentation** — Write README

### Phase E — Agents (Week 4)
Write the 20 agent markdown files. Each agent file specifies:
- Role description and scope boundaries
- Phase(s) of operation
- Primary MCP tools with usage patterns
- Output format (what the agent produces)
- Escalation behavior (what to do when data is missing)
- For gate-blocked agents: the exact gate check call and refusal message

Use `plugin-dev`'s `agent-creator` and `agent-development` skill for AI-assisted generation of agent system prompts.

### Phase F — Skills, Tier 1 (Week 5–6)
Build and evaluate the 8 highest-priority skills using `skill-creator`:

Priority order (most other content depends on these triggering reliably):
1. `continuity-editor` — fires on all content creation
2. `timeline-manager` — fires on all chronological content
3. `prose-writer` — primary drafting skill (gate-enforced)
4. `character-voice-auditor` — fires on all dialogue
5. `pacing-tension-analyst` — fires on chapter and scene work
6. `foreshadowing-tracker` — fires on all planted elements
7. `names-linguistics` — fires on all naming decisions
8. `lore-keeper` — fires after all content changes

For each skill:
- Write SKILL.md draft
- Define 3–5 eval test cases
- Run `skill-creator` eval loop
- Run description optimizer
- Verify reliable triggering

### Phase G — Skills, Tier 2 (Week 7–8)
Build remaining 12 skills:
9. `relationship-dynamics`
10. `perception-profiles`
11. `information-state-tracker`
12. `thematic-architecture`
13. `symbolism-motif-tracker`
14. `dialogue-specialist`
15. `sensory-atmosphere`
16. `supernatural-voice`
17. `battle-action-coordinator`
18. `chapter-hook-specialist`
19. `line-editor`
20. `copy-editor`

### Phase H — Architecture Gate (Week 9)
1. Populate the 33 gate checklist items with their SQL evidence queries
2. Run `/novel:gate-check` against the existing project
3. Work through all blocking items with the appropriate architect agents
4. Certify the gate
5. Verify prose-phase skills now operate normally

#### Gate Checklist

The 33 checklist items are SQL-verifiable assertions that prove the story architecture is complete before prose begins. Think of them as your "definition of done" for the architecture phase — each one has a query that runs against the database and either passes or fails with a count of missing records.

Here's the full set, organized by domain:

---

**World Foundation — 6 items**

1. All major locations have records with a non-null `sensory_profile`
2. All factions have a current `faction_political_state` record
3. All `magic_system_elements` have rules, limitations, and cost documented
4. All `supernatural_elements` have constraints and narrative behavior documented
5. The `name_registry` has an entry for every named character and location
6. At least one `era` record exists establishing the historical calendar

**Characters — 5 items**

7. All 6 POV characters have complete character sheets (no null fields on required columns)
8. All 6 POV characters have a `voice_profile` record
9. All POV character pairs (15 pairs for 6 characters) have a `character_relationship` record
10. All 6 POV characters have at least one `perception_profile` record for each other POV character
11. All major non-POV characters appearing in 3+ chapters have character records

**Structural Architecture — 9 items**

12. The three acts have defined boundary chapters and are not null on `inciting_incident`, `midpoint`, `climax` fields
13. All `plot_threads` marked `is_primary = true` have defined resolution plans
14. All `chekovs_gun_registry` entries have a non-null `planned_payoff_chapter`
15. All 6 POV characters have a `character_arc` record with all 7-point beat chapters defined (Hook, Plot Turn 1, Pinch 1, Midpoint, Pinch 2, Plot Turn 2, Resolution) and beats verified against act-structure alignment
16. All 55 chapters have a POV character assignment in `chapters.pov_character_id`
17. The `foreshadowing_registry` has no entries with `planted_chapter` but null `payoff_chapter`
18. All `prophecy_registry` entries have at least one fulfillment path documented
19. All `thematic_mirrors` have both poles identified and mapped to specific chapters
20. The `dramatic_irony_inventory` has at least one active entry (proving the system is populated)

**Chapter Plans — 6 items**

21. All 55 chapters have a `chapter_plan` record (not just a stub `chapters` row)
22. All 55 chapters have at least one entry in `chapter_structural_obligations`
23. All 55 chapters have a non-null opening hook spec
24. All 55 chapters have a non-null closing hook spec
25. No chapter has zero scenes in the `scenes` table
26. The `pov_chronological_position` table has an entry for every POV character × chapter combination where that character appears

**Scene Architecture — 5 items**

27. All scenes have a non-null `dramatic_question`
28. All scenes have at least one `scene_character_goals` entry for the POV character
29. All action/battle scenes have a `battle_action_coordinator` notes record
30. All scenes involving supernatural elements have a `supernatural_voice_guidelines` reference
31. No scene has `tension_level` = null (Pacing Agent must have reviewed every scene)

**Continuity and Canon — 4 items**

32. No open `continuity_issues` with `severity = 'blocking'`
33. The `canon_facts` table has at least one entry per major world-building domain (magic, politics, religion, geography)

---

The gate audit runs all 33 queries. Any that return a failing count get flagged as blocking items with the specific records missing. The Architecture Completeness Auditor agent formats this as a gap report: domain, item description, count of missing records, and the IDs or names of what's missing so you know exactly what work remains.

Once all 33 pass, the auditor writes the gate certification record and prose-phase skills stop refusing.

The SQL for something like item 21 looks like:

```sql
SELECT COUNT(*) as missing_count
FROM chapters c
LEFT JOIN chapter_plans cp ON cp.chapter_id = c.id
WHERE c.book_id = 1
  AND cp.id IS NULL;
```

Pass condition: `missing_count = 0`. If it comes back as 12, you know 12 chapters still need plans written before gate certification is possible.


### Phase I — Slash Commands (Week 9, parallel with H)
Write the 9 command markdown files. Test each against the `novel` CLI to confirm output matches.

---

## 11. Success Criteria

- [ ] `novel db migrate` builds a clean database from scratch in under 5 seconds
- [ ] `novel import all` imports all existing project markdown with less than 10% unmapped fields
- [ ] All MCP tools are callable from Claude Code with correct return types
- [ ] `/novel:gate-check` produces an accurate gap report identifying all known incomplete sections
- [ ] All 20 skills trigger reliably on natural-language task descriptions (verified by `skill-creator` eval loop)
- [ ] All 20 agents are invokable and produce their specified outputs
- [ ] Prose-phase skills (`prose-writer`, `line-editor`, `copy-editor`) refuse to operate without gate certification
- [ ] `/novel:session-start` produces a useful briefing from the previous session's log
- [ ] The entire system rebuilds from scratch on a new machine using only the repos, plugin, and config files
