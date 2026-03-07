# Phase 1: Project Foundation & Database - Context

**Gathered:** 2026-03-07
**Status:** Ready for planning

<domain>
## Phase Boundary

Set up the Python project scaffold, all 21 SQL migration files (based on `project-research/database-schema.md`), a shared database connection factory, and the `novel db` CLI subcommands (`migrate`, `seed`, `reset`, `status`). No MCP tools, no Pydantic models, no seed data logic beyond the `db seed` command stub. Everything downstream depends on this foundation being correct.

</domain>

<decisions>
## Implementation Decisions

### Schema source
- Use `project-research/database-schema.md` as the authoritative base for all 21 migration files
- Implement exactly as documented; where modifications are needed for FK dependency ordering or missing tracking tables, apply them
- Add `schema_migrations` tracking table (migration 001) — not in the schema doc but required by the migration runner

### Migration file naming
- Format: `NNN_descriptive_name.sql` (zero-padded 3 digits + snake_case description)
- Example: `001_schema_tracking.sql`, `002_core_books_eras.sql`, `007_chapters.sql`
- Migration files bundled as package data inside the `novel` package (not shipped separately)

### Migration behavior
- `novel db migrate` = **incremental**: reads `schema_migrations` table, applies only unapplied migrations in order
- `novel db reset` = **clean rebuild**: drops all tables, then runs full migrate from scratch
- This distinction matters: later dev iterations can add migrations without blowing away seed data
- `schema_migrations` table: `(version INT PRIMARY KEY, name TEXT NOT NULL, applied_at TEXT NOT NULL)`

### Migration grouping strategy (21 migrations)
Grouped by dependency order and domain:
- `001` — schema_migrations tracking table
- `002` — eras, books (no cross-dependencies)
- `003` — acts (FK to books; start/end chapter FKs are nullable — created after chapters)
- `004` — cultures
- `005` — factions (leader_character_id nullable — characters come later)
- `006` — locations (FK to cultures, factions)
- `007` — characters (FK to factions, cultures, eras)
- `008` — chapters (FK to books, acts, characters for pov_character_id)
- `009` — scenes (FK to chapters, locations)
- `010` — artifacts (FK to characters, locations, eras)
- `011` — magic_system_elements, supernatural_elements (FK to chapters, nullable)
- `012` — character_relationships, relationship_change_events, perception_profiles
- `013` — character_knowledge, character_beliefs, character_locations, injury_states, title_states
- `014` — voice_profiles, voice_drift_log
- `015` — events, event_participants, event_artifacts, travel_segments, pov_chronological_position
- `016` — plot_threads, chapter_plot_threads, chapter_structural_obligations
- `017` — character_arcs, chapter_character_arcs, arc_health_log, chekovs_gun_registry, subplot_touchpoint_log
- `018` — scene_character_goals, pacing_beats, tension_measurements
- `019` — session_logs, agent_run_log
- `020` — architecture_gate, gate_checklist_items, project_metrics_snapshots, pov_balance_snapshots
- `021` — reader_reveals, reader_information_states, dramatic_irony_inventory, reader_experience_notes, canon_facts, continuity_issues, decisions_log, foreshadowing_registry, prophecy_registry, object_states, motif_registry, motif_occurrences, thematic_mirrors, opposition_pairs, supernatural_voice_guidelines, faction_political_states, name_registry, magic_use_log, practitioner_abilities, research_notes, open_questions, documentation_tasks, publishing_assets, submission_tracker

### Database path & discovery
- Database file lives OUTSIDE the drafter repo — in the novel content repo (or wherever pointed)
- `NOVEL_DB_PATH` env var is the canonical mechanism for both CLI and MCP server
- Convention (from PRD): database at `.db/novel.sqlite` inside the novel content repo
- Development fallback: `./novel.db` in current directory when `NOVEL_DB_PATH` is not set
- Both the CLI and MCP server read the same env var — no separate config file needed

### Package structure
Single `novel` package with submodules, `src/` layout for hatchling compatibility:
```
src/
  novel/
    __init__.py
    cli.py            # `novel` entry point — Typer root app, registers subcommand groups
    db/
      __init__.py
      connection.py   # sync (sqlite3) and async (aiosqlite) connection factories
      migrations.py   # migration runner (discover, compare, apply)
      seed.py         # seed profile loader (stub for Phase 1)
    mcp/
      __init__.py
      server.py       # `novel-mcp` entry point — FastMCP app setup (no tools yet in Phase 1)
      db.py           # async connection management for MCP tools
    models/           # populated Phase 2 — Pydantic domain models
    tools/            # populated Phase 3+ — one module per domain
```

Entry points in `pyproject.toml`:
- `novel` → `novel.cli:app`
- `novel-mcp` → `novel.mcp.server:run`

### Connection factory design
- **Sync** (`novel.db.connection`): context manager returning `sqlite3.Connection`; sets WAL mode + `PRAGMA foreign_keys=ON` on every connection open
- **Async** (`novel.mcp.db`): async context manager returning `aiosqlite.Connection`; same pragmas applied immediately after open
- No global connection pool — each call creates a fresh connection via context manager (appropriate for SQLite at this scale)

### CLI behavior
- `novel db migrate` — runs incremental migration, prints each applied migration name; reports "already up to date" if none pending
- `novel db seed [profile]` — stub in Phase 1 (returns "no seed profiles defined"); implemented in Phase 2
- `novel db reset` — prompts for confirmation ("This will drop all tables. Continue? [y/N]"), then drops + migrates
- `novel db status` — shows: migration version (last applied), table count, row counts for `books`, `chapters`, `characters`, `scenes`; plain text, no color required (Rich is a v2 requirement)

### Claude's Discretion
- Exact SQL for each migration (researcher/planner figures out column types, constraints, indexes)
- Whether to add any indexes in Phase 1 vs. later
- Error message text for CLI commands
- Internal migration file discovery implementation (glob vs. hardcoded list vs. importlib.resources)

</decisions>

<specifics>
## Specific Ideas

- Database file is gitignored (the file itself), but the migration SQL files that define the schema are tracked in the repo
- `NOVEL_DB_PATH` env var is the canonical mechanism for both CLI and MCP server to find the database — this is how the plugin's `.mcp.json` will wire it up when the plugin is built later
- The `src/` layout with a single `novel` package avoids import confusion and keeps everything cohesive for a 10-phase build

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- None — completely greenfield project. No existing code.

### Established Patterns
- No patterns yet — this phase establishes them for all subsequent phases.

### Integration Points
- Phase 2 will add Pydantic models and seed logic to `novel.db.seed` (stub created here)
- Phase 3 will register MCP tools with the FastMCP app in `novel_mcp.server`
- The connection factory pattern established here is used in every subsequent phase

</code_context>

<deferred>
## Deferred Ideas

- None — discussion stayed within phase scope

</deferred>

---

*Phase: 01-project-foundation-database*
*Context gathered: 2026-03-07*
