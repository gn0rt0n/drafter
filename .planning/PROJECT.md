# Drafter

## What This Is

Drafter is the Python engine for a Claude Code–native novel management system. It provides a SQLite narrative database (21 migration files), a Python MCP server (~80 tools across 14 domains), and a UV/Python CLI (`novel` command) that gives Claude Code structured, queryable access to all story data for a 250,000-word epic fantasy novel.

This repo is the engine layer. The Claude Code plugin (`novel-plugin/`, separate repo) wraps it. The actual novel content repo also lives separately and stays untouched during development — all testing uses minimal seed files.

## Core Value

Claude Code can query and update all story data through typed MCP tool calls — no raw SQL, no markdown parsing — enabling consistent AI collaboration at novel scale.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] 21 SQL migration files define the complete narrative schema
- [ ] `novel db migrate` builds a clean database from scratch in under 5 seconds
- [ ] All ~80 MCP tools across 14 domains are callable from Claude Code with correct return types
- [ ] `novel` CLI wraps all operational subcommands (db, export, import, query, session, gate, name)
- [ ] Seed data files enable fast test/verify cycles without touching the real manuscript
- [ ] MCP error contract enforced: `null` for not-found, `is_valid: false` for validation failures, `requires_action` for gate violations
- [ ] Gate system (`get_gate_status`, `run_gate_audit`, `certify_gate`) correctly blocks prose-phase operations when 33-item checklist is incomplete

### Out of Scope

- Real novel manuscript content — seed files only for development and testing
- `novel-plugin/` (Claude Code plugin) — separate repo, built after this engine is stable
- Novel content repo (the actual story) — untouched during this build
- Any web UI or API layer — CLI + MCP only

## Context

The system treats a 250,000-word epic fantasy novel (55 chapters, 6 POV characters, 20+ named agents) like a software project: structured data, version control, modular tooling. The SQLite database is the authoritative source of truth — markdown files are generated outputs, not editable sources.

The architecture gate (33 SQL-verifiable checklist items) blocks prose writing until story architecture is provably complete. Prose-phase MCP tools return `requires_action` if gate status is not `passed`.

Reference documents in `project-overview/`:
- `drafter-prd.md` — Full PRD with build sequence (Phases A–I)
- `database-schema.md` — Complete SQLite schema, all 21 migrations
- `agent-roster.md` — All 40 agent/skill definitions
- `plugin-ecosystem.md` — Ecosystem overview

## Constraints

- **Runtime**: UV/Python — no global installs required; `uv run` invocation from plugin's `.mcp.json`
- **Database**: SQLite only — single-file, git-trackable schema, migration-based rebuild
- **MCP protocol**: `mcp` SDK — tools must conform to MCP tool call format with typed Pydantic models
- **Testing**: Seed files only — no dependency on real manuscript content
- **Separation**: This repo is engine-only; plugin and novel content repos stay separate

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| drafter = novel-tools Python repo only | Plugin is separate; engine must be stable first | — Pending |
| Seed files for all testing | Keeps dev loop fast; real manuscript untouched | — Pending |
| Build order: DB → MCP → CLI → Plugin (separate) | Each layer depends on the previous | — Pending |
| SQLite over Postgres | Single-file, travels with git, no server setup | — Pending |
| UV over pip/venv | No global installs, reproducible, fast | — Pending |

---
*Last updated: 2026-03-07 after initialization*
