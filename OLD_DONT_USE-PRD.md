# Drafter — Product Requirements Document
## Epic Fantasy Novel Plugin Ecosystem

**Status**: Draft
**Last Updated**: 2026-03-07
**Stack**: Python/UV · SQLite · Claude Code Plugin · MCP Server

---

## 1. Vision

Build a complete Claude Code plugin ecosystem — `drafter` — for writing a 250,000-word epic fantasy novel. The system treats a novel like a software project: structured data, specialized agents, CLI tooling, and an MCP server that gives agents queryable access to a single authoritative SQLite database.

**Core principle**: The database is the source of truth. Markdown files are generated outputs. Agents never write prose directly to markdown — they write to the database; markdown is regenerated on demand.

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      AUTHOR (You)                            │
│                                                              │
│  Claude Code CLI ──► drafter plugin (agents/commands/skills) │
│  drafter CLI    ──► SQLite DB ◄──── MCP Server              │
│                          │                                   │
│                          ▼                                   │
│              Generated Markdown Files                         │
│                          │                                   │
│                          ▼                                   │
│              Obsidian Vault (read-only sync)                  │
└─────────────────────────────────────────────────────────────┘
```

**Data flow**:
1. Author or agent writes to SQLite (via MCP tools or CLI)
2. `drafter export` regenerates markdown from DB state
3. Claude Code agents load markdown as file context
4. Obsidian reads the generated markdown directory

---

## 3. Repository / Directory Structure

### Tool Repository (`/Users/gary/writing/drafter/`)

This is where the plugin, CLI, and MCP server live.

```
/drafter/
├── PRD.md
├── epic-fantasy-claude-ecosystem.md
├── narrative-database-schema-complete.md
│
├── plugin/                          # Claude Code plugin
│   ├── plugin.json                  # Plugin manifest
│   ├── agents/
│   │   ├── world-builder.md
│   │   ├── character-architect.md
│   │   ├── plot-architect.md
│   │   ├── prose-writer.md
│   │   ├── continuity-editor.md
│   │   ├── lore-keeper.md
│   │   ├── developmental-editor.md
│   │   ├── line-editor.md
│   │   ├── research-agent.md
│   │   └── pov-manager.md
│   ├── commands/
│   │   ├── draft-chapter.md
│   │   ├── continuity-check.md
│   │   ├── lore-update.md
│   │   ├── word-count.md
│   │   ├── pov-status.md
│   │   ├── export.md
│   │   └── story-status.md
│   ├── skills/
│   │   ├── story-bible-query.md
│   │   ├── chapter-drafting-workflow.md
│   │   └── continuity-check-workflow.md
│   └── hooks/
│       ├── chapter-finalized.md     # PostToolUse: triggers lore sync
│       └── name-guard.md            # PreToolUse: validates proper nouns
│
├── mcp/                             # MCP server (Python/UV)
│   ├── pyproject.toml
│   ├── server.py                    # Entry point
│   ├── tools/
│   │   ├── characters.py
│   │   ├── chapters.py
│   │   ├── locations.py
│   │   ├── timeline.py
│   │   ├── continuity.py
│   │   └── export.py
│   └── db/
│       ├── connection.py
│       └── migrations/
│           └── 001_initial_schema.sql
│
└── cli/                             # drafter CLI (Python/UV)
    ├── pyproject.toml
    ├── drafter/
    │   ├── __init__.py
    │   ├── main.py                  # Entry point (typer/click)
    │   ├── commands/
    │   │   ├── init.py
    │   │   ├── export.py
    │   │   ├── import_.py
    │   │   ├── status.py
    │   │   ├── word_count.py
    │   │   └── check_names.py
    │   └── db/
    │       └── connection.py        # Shared with mcp/ (or symlink)
```

### Novel Project (`/Users/gary/writing/[novel-name]/`)

Scaffolded by `drafter init`. This is where the actual novel lives.

```
/[novel-name]/
├── CLAUDE.md                        # Root "God file" — loaded by all agents
├── .claude/
│   └── settings.json                # MCP config pointing to drafter MCP server
│
├── manuscript/
│   ├── CLAUDE.md
│   ├── chapters/
│   │   ├── act-1/
│   │   ├── act-2/
│   │   └── act-3/
│   └── drafts/
│
├── story-bible/                     # GENERATED — do not edit manually
│   ├── characters/
│   ├── world/
│   ├── magic/
│   ├── history/
│   └── religions-and-mythology/
│
├── outlines/
│   ├── CLAUDE.md
│   ├── master-outline.md
│   ├── pov-threads/
│   └── chapter-plans/
│
├── continuity/
│   ├── CLAUDE.md
│   ├── master-timeline.md           # GENERATED
│   ├── name-registry.md             # GENERATED
│   ├── contradictions-log.md        # GENERATED
│   └── chapter-summaries/           # GENERATED
│
├── obsidian/                        # Obsidian vault root (read-only)
│   └── [mirrors story-bible/ structure]
│
└── drafter.db                       # SQLite database (source of truth)
```

---

## 4. SQLite Database

Schema is fully defined in `narrative-database-schema-complete.md`. Implemented as SQL migration files in `mcp/db/migrations/`.

### Key design constraints
- `canon_status` enum on every entity: `draft`, `approved`, `provisional`, `deprecated`
- `chapter_id` as temporal anchor (not calendar dates)
- Soft deletes only — no hard deletes during active development
- `agent_run_log` table for full auditability of agent writes
- `source_file` on every entity for traceability

### Primary tables (from schema doc)
`books` · `acts` · `chapters` · `scenes` · `characters` · `locations` · `factions` · `magic_abilities` · `timeline_events` · `character_arcs` · `continuity_issues` · `name_registry` · `agent_run_log`

---

## 5. Python CLI (`drafter`)

**Runtime**: UV (`uv run drafter`) or installed as `drafter` via `uv tool install`.
**Framework**: Typer (preferred) or Click.

### Commands

| Command | Description |
|---------|-------------|
| `drafter init [path]` | Scaffold novel directory structure + seed empty DB |
| `drafter export [entity]` | Regenerate markdown from DB (all, or by entity type) |
| `drafter import [file]` | Parse a markdown file and write records to DB |
| `drafter status` | Dashboard: word count, chapter progress, open continuity issues |
| `drafter word-count` | Breakdown by act, POV character, overall |
| `drafter check-names [chapter_file]` | Compare proper nouns in file against name_registry |
| `drafter pov-balance` | Chapter count per POV character, flagging gaps |
| `drafter db migrate` | Run pending migrations |
| `drafter db seed [fixture_file]` | Load test/starter data |

### Notes
- Database path is resolved from: `$DRAFTER_DB` env var → `./drafter.db` → `~/.drafter/default.db`
- `drafter export` writes to `story-bible/`, `continuity/`, `outlines/` and also to `obsidian/`
- `drafter status` is designed to be fast enough to run as a CLAUDE.md `@include` or shell command

---

## 6. MCP Server

**Runtime**: UV (`uvx drafter-mcp` or `uv run mcp/server.py`)
**Protocol**: stdio (standard Claude Code MCP config)
**Purpose**: Give agents structured, queryable access to the SQLite database without loading entire markdown files.

### Configured in novel's `.claude/settings.json`

```json
{
  "mcpServers": {
    "drafter": {
      "command": "uv",
      "args": ["run", "/Users/gary/writing/drafter/mcp/server.py"],
      "env": {
        "DRAFTER_DB": "/Users/gary/writing/[novel-name]/drafter.db"
      }
    }
  }
}
```

### MCP Tools

#### Character tools
| Tool | Description |
|------|-------------|
| `get_character(name_or_id)` | Full character record with arc summary |
| `list_characters(canon_status?, role?)` | Filtered character list |
| `get_relationship(char_a_id, char_b_id)` | Relationship record between two characters |
| `get_character_state_at(character_id, chapter_id)` | Character's emotional/physical state at a chapter |

#### Chapter / Scene tools
| Tool | Description |
|------|-------------|
| `get_chapter(number_or_id)` | Full chapter record |
| `list_chapters(act?, status?, pov_character_id?)` | Filtered chapter list |
| `get_chapter_summary(chapter_id)` | Summary text only |
| `update_chapter_status(chapter_id, status)` | Move chapter through status pipeline |
| `get_scenes(chapter_id)` | All scenes in a chapter |

#### World tools
| Tool | Description |
|------|-------------|
| `get_location(name_or_id)` | Full location record |
| `get_faction(name_or_id)` | Faction record with relationships |
| `get_magic_ability(name_or_id)` | Magic ability / spell record |
| `get_magic_system_rules()` | All hard + soft magic rules |

#### Timeline tools
| Tool | Description |
|------|-------------|
| `get_timeline(from_chapter?, to_chapter?)` | Events in range |
| `get_character_location_at(character_id, chapter_id)` | Where a character is at a chapter |
| `check_timeline_conflict(character_id, chapter_id)` | Detect location/time contradictions |

#### Continuity tools
| Tool | Description |
|------|-------------|
| `get_name_registry(entity_type?)` | All registered proper nouns |
| `log_continuity_issue(chapter_id, description, severity, agent_name)` | Record a contradiction |
| `list_continuity_issues(resolved?, severity?)` | Query logged issues |
| `resolve_continuity_issue(issue_id, resolution_notes)` | Mark issue resolved |

#### Export / sync tools
| Tool | Description |
|------|-------------|
| `export_entity_markdown(entity_type, entity_id)` | Regenerate markdown for one record |
| `get_project_status()` | Summary stats (word count, chapter status breakdown) |

---

## 7. Claude Code Plugin

Built using the `plugin-dev` plugin. Lives at `~/.claude/plugins/drafter/` or distributed as a plugin package.

### `plugin.json` (manifest)

```json
{
  "name": "drafter",
  "version": "0.1.0",
  "description": "Epic fantasy novel writing ecosystem — agents, commands, and skills for structured long-form fiction",
  "agents": [...],
  "commands": [...],
  "skills": [...],
  "hooks": [...]
}
```

---

### 7a. Agents

Ten specialized agents. Each is a markdown file with a YAML frontmatter block (name, description, tools) followed by a detailed system prompt. The description field is what Claude uses to decide when to auto-invoke the agent.

| Agent | Trigger Description | Key Tools |
|-------|--------------------|----|
| `world-builder` | Worldbuilding creation, expansion, geography, cultures, factions | MCP world tools, Read, Write |
| `character-architect` | Character sheets, arcs, relationships, voice | MCP character tools, Read, Write |
| `plot-architect` | Outlines, structure, pacing, subplot tracking | MCP chapter/scene tools, Read, Write |
| `prose-writer` | Drafting scenes and chapters from a plan | MCP chapter/character tools, Read, Write |
| `continuity-editor` | Consistency checking, contradiction detection | MCP continuity tools, Grep, Read |
| `lore-keeper` | Story bible maintenance, post-chapter updates | All MCP tools, Read, Write |
| `developmental-editor` | Big-picture story feedback, structural assessment | MCP chapter tools, Read |
| `line-editor` | Prose-level editing, sentence quality, voice | Read, Write |
| `research-agent` | Real-world research for worldbuilding accuracy | WebSearch, WebFetch, Write |
| `pov-manager` | Multi-POV coordination, balance, dramatic irony | MCP chapter/character tools, Read |

**Critical constraint on Prose Writer**: Never invents worldbuilding facts. If a fact isn't in the database, it flags the gap rather than improvising.

**Critical constraint on Continuity Editor**: Paranoid by design. Reads everything before writing anything. Logs all issues to DB via MCP `log_continuity_issue`.

---

### 7b. Slash Commands

| Command | Purpose | Key Agent Invoked |
|---------|---------|------------------|
| `/draft-chapter [number]` | Full chapter drafting workflow: load plan → invoke Prose Writer → run Continuity Editor | prose-writer + continuity-editor |
| `/continuity-check [chapter_file]` | Run Continuity Editor against a chapter file | continuity-editor |
| `/lore-update [chapter_file]` | Lore Keeper post-chapter bible sync | lore-keeper |
| `/word-count` | Print word count dashboard from DB + filesystem | (direct `drafter word-count`) |
| `/pov-status` | POV balance chart, gap report | pov-manager |
| `/export [entity_type?]` | Regenerate markdown from DB, sync to Obsidian | (direct MCP export + sync) |
| `/story-status` | Full project dashboard: chapter statuses, open issues, word count | (aggregates DB + filesystem) |

Each command is a markdown file with YAML frontmatter defining arguments and a templated prompt body that assembles context and invokes the appropriate agent(s).

---

### 7c. Skills

Skills auto-trigger based on what the user is doing. Built using the `skill-creator` plugin.

| Skill | Trigger Condition | What It Does |
|-------|------------------|-------------|
| `story-bible-query` | User asks about a character, place, faction, or magic rule | Routes the question to the MCP server for a structured answer instead of loading all markdown files |
| `chapter-drafting-workflow` | User says "draft chapter", "write chapter", "continue chapter" | Ensures chapter plan exists, key context is loaded (character sheets, location, previous chapter summary), then invokes Prose Writer |
| `continuity-check-workflow` | User says "check continuity", "check for errors", "run continuity" | Invokes Continuity Editor with full MCP access, formats the resulting issue list |

---

### 7d. Hooks

| Hook | Event | Behavior |
|------|-------|---------|
| `chapter-finalized` | `PostToolUse` on Write tool when file path matches `manuscript/chapters/**/*.md` | Prompts: "A chapter file was just written. Invoke the Lore Keeper to update the story bible and chapter summary in the database." |
| `name-guard` | `PreToolUse` on Write tool for manuscript files | Extracts proper nouns from the content about to be written. Checks against `name_registry` via MCP. Warns if unregistered names are detected. |

---

## 8. Obsidian Sync

**Direction**: One-way, DB → Obsidian only. No write-back.
**Mechanism**: `drafter export --obsidian` writes generated markdown to the `obsidian/` subdirectory of the novel project, formatted for Obsidian (wikilinks, frontmatter).
**Scope**: `story-bible/` content only. Manuscript chapters do not sync to Obsidian.
**Trigger**: Manual (`drafter export --obsidian`) or as part of `/lore-update` command post-chapter.

---

## 9. Build Phases

Build in this order. Each phase produces a testable, usable increment.

### Phase 1 — Foundation (CLI + DB)
**Goal**: `drafter init` works, schema is live, basic data can be written and read.

- [ ] Set up `cli/` Python/UV project with Typer
- [ ] Implement `mcp/db/migrations/001_initial_schema.sql` from `narrative-database-schema-complete.md`
- [ ] `drafter db migrate` command
- [ ] `drafter init [path]` — scaffold novel directory + seed empty DB
- [ ] `drafter status` — minimal dashboard (chapter count, word count)
- [ ] `drafter word-count` — reads manuscript files, aggregates by act
- [ ] `drafter export` — write minimal markdown stubs for empty DB

**Done when**: Running `drafter init ~/writing/my-novel` creates the full directory tree and a working SQLite database.

---

### Phase 2 — MCP Server
**Goal**: Claude Code agents can query the database via MCP tools.

- [ ] Set up `mcp/` Python/UV project with `mcp` SDK
- [ ] Implement character tools (`get_character`, `list_characters`, `get_relationship`)
- [ ] Implement chapter tools (`get_chapter`, `list_chapters`, `get_chapter_summary`)
- [ ] Implement continuity tools (`log_continuity_issue`, `get_name_registry`)
- [ ] Implement export tools (`get_project_status`, `export_entity_markdown`)
- [ ] Configure `.claude/settings.json` in novel project to load the MCP server
- [ ] Smoke test: manually call MCP tools from Claude Code

**Done when**: From inside the novel project directory, Claude Code can call `get_chapter(1)` and get a structured response.

---

### Phase 3 — Plugin (Agents + Commands)
**Goal**: All 10 agents are defined; core slash commands work.

- [ ] Scaffold plugin structure with `plugin-dev` plugin
- [ ] Write `plugin.json` manifest
- [ ] Write all 10 agent markdown files (system prompts + frontmatter)
- [ ] Wire agents to MCP tools in their frontmatter
- [ ] Implement `/draft-chapter`, `/continuity-check`, `/lore-update` commands
- [ ] Implement `/story-status`, `/word-count` commands
- [ ] Install plugin and test: `claude` picks up agents

**Done when**: `/story-status` returns a formatted project dashboard. Invoking the World Builder agent returns coherent responses grounded in the DB.

---

### Phase 4 — Skills
**Goal**: Skills auto-trigger appropriately. Built with `skill-creator` plugin.

- [ ] Write `story-bible-query` skill; test trigger accuracy
- [ ] Write `chapter-drafting-workflow` skill; test trigger accuracy
- [ ] Write `continuity-check-workflow` skill; test trigger accuracy
- [ ] Evaluate each skill with `skill-creator` eval tools
- [ ] Tune trigger descriptions until false positive/negative rate is acceptable

**Done when**: Saying "tell me about the northern faction" triggers `story-bible-query` without needing `/` invocation.

---

### Phase 5 — Hooks + Automation
**Goal**: Post-write hooks reduce manual lore sync burden.

- [ ] Implement `chapter-finalized` PostToolUse hook
- [ ] Implement `name-guard` PreToolUse hook
- [ ] Test hook: write a chapter → lore-keeper auto-updates DB
- [ ] Test hook: write a chapter with an unregistered name → warning fires

**Done when**: Finalizing a chapter automatically triggers a Lore Keeper pass without the author asking.

---

### Phase 6 — Obsidian Sync + Export Polish
**Goal**: Full markdown generation pipeline with Obsidian-compatible output.

- [ ] `drafter export --obsidian` generates wikilink-formatted markdown
- [ ] Obsidian vault directory structure mirrors story-bible
- [ ] CLAUDE.md files in generated directories contain appropriate agent instructions
- [ ] `drafter check-names [file]` validates against live DB registry
- [ ] `drafter import` handles basic markdown → DB ingestion for initial data entry

**Done when**: After running `drafter export --obsidian`, Obsidian shows a fully navigable story bible.

---

## 10. Non-Goals (This Version)

- **Bidirectional Obsidian sync** — read-only for now
- **Web UI** — no dashboard app; everything is CLI or Claude Code
- **Multi-user collaboration** — single author, local SQLite only
- **Git integration** — no auto-commits; git is manual
- **Publishing pipeline** — no ebook/PDF export tooling
- **Voice input** — not in scope

---

## 11. Open Questions

- **CLI name**: `drafter` is assumed from the project directory. Confirm or change before building.
- **Novel project location**: PRD assumes `~/writing/[novel-name]/` separate from `~/writing/drafter/` (the tool). Confirm this separation makes sense once you have a title.
- **MCP transport**: stdio assumed for simplicity. HTTP transport only needed if you want the MCP server to run persistently (daemon mode). Default to stdio.
- **Word count source**: Does `drafter word-count` read from the filesystem (counting words in `.md` files) or from `chapters.actual_word_count` in the DB? Recommend filesystem-primary with DB as cache.
- **Phase ordering**: Phase 3 (plugin) currently requires Phase 2 (MCP) to be complete for agents to have database access. If you want to start writing agents before MCP is ready, agents can fall back to reading markdown files directly until MCP is available.

---

## 12. Success Criteria

The system is working when:

1. `drafter init ~/writing/[novel-name]` scaffolds a complete project directory in under 5 seconds
2. Claude Code agents can answer "what do we know about [Character X]?" using MCP tools without loading entire markdown files
3. Writing a chapter and running `/lore-update` takes under 2 minutes and produces accurate story bible updates
4. `/continuity-check` on a chapter catches name inconsistencies and timeline violations
5. `drafter export --obsidian` produces a navigable Obsidian vault from database state
6. The system can support drafting from chapter 1 to chapter 55 without re-architecting
