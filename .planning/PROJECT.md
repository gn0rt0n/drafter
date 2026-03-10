# Drafter

## What This Is

Drafter is the Python engine for a Claude Code–native novel management system. It provides a SQLite narrative database (22 migration files, 71 tables), a Python MCP server (231 tools across 18 domains), and a UV/Python CLI (`novel` command) that gives Claude Code structured, queryable access to all story data for a 250,000-word epic fantasy novel.

This repo is the engine layer. The Claude Code plugin (`novel-plugin/`, separate repo) wraps it. The actual novel content repo lives separately and stays untouched during development — all testing uses minimal seed files.

**v1.1 shipped 2026-03-10.** All 15 phases complete. Engine has full CRUD coverage and per-domain documentation.

## Core Value

Claude Code can query and update all story data through typed MCP tool calls — no raw SQL, no markdown parsing — enabling consistent AI collaboration at novel scale.

## Requirements

### Validated

- ✓ 21 SQL migration files define the complete narrative schema — v1.0 Phase 1 (69 tables initially, FK-safe, 0 violations)
- ✓ `novel db migrate` builds a clean database from scratch in under 5 seconds — v1.0 Phase 1 (~20ms, idempotent)
- ✓ All 103 MCP tools across 18 domains are callable from Claude Code with correct return types — v1.0 Phases 3–11
- ✓ `novel` CLI wraps all operational subcommands (db, export, import, query, session, gate, name) — v1.0 Phase 10
- ✓ Seed data files enable fast test/verify cycles without touching the real manuscript — v1.0 Phase 2
- ✓ MCP error contract enforced: `null` for not-found, `is_valid: false` for validation failures, `requires_action` for gate violations — v1.0 Phase 3
- ✓ Gate system (`get_gate_status`, `run_gate_audit`, `certify_gate`) correctly blocks prose-phase operations when 36-item checklist is incomplete — v1.0 Phase 6
- ✓ 7-point structure tracking at story level and per-POV-character arc, with 2 gate items added — v1.0 Phase 11
- ✓ Complete reference documentation: schema.md (71 tables), mcp-tools.md (103 tools), README.md — v1.0 Phase 12
- ✓ Fix stale gate count strings ("33"/"34") → 36 in gate.py, cli.py — v1.1 Phase 13
- ✓ Fix `novel db seed gate-ready` CLI help text (hyphen → underscore) — v1.1 Phase 13
- ✓ Fix 4 doc bugs in docs/README.md (migration claim, export command, GateViolation type, table names) — v1.1 Phase 13
- ✓ Add pydantic as direct dependency in pyproject.toml — v1.1 Phase 13
- ✓ Fix gate audit/certify count inconsistency (audit: 36, certify: 36) — v1.1 Phase 13
- ✓ Audit and add missing MCP write tools for all 71 schema tables — v1.1 Phase 14 (128 tools added, 231 total)
- ✓ Split docs/mcp-tools.md into 18 per-domain tool files under docs/tools/ — v1.1 Phase 15
- ✓ Split docs/schema.md into 18 per-domain schema files under docs/schema/ — v1.1 Phase 15
- ✓ Master navigation index at docs/README.md linking all 37 documentation files — v1.1 Phase 15

### Active

<!-- v1.2+: plugin integration, real-world validation, performance tuning -->

(None defined — start next milestone with `/gsd:new-milestone`)

### Out of Scope

- Real novel manuscript content — seed files only for development and testing
- `novel-plugin/` (Claude Code plugin) — separate repo, built after this engine is stable
- Novel content repo (the actual story) — untouched during this build
- Any web UI or API layer — CLI + MCP only

## Context

**v1.1 shipped 2026-03-10** — 3 phases, 26 plans, 1 day of execution.

**Current state:**
- 22 migration files, 71 tables across 16 domains
- 231 MCP tools across 18 domains (18 tool modules in `src/novel/tools/`)
- `novel` CLI with 7 subcommand groups (db, session, gate, export, import, query, name)
- Architecture gate: 36 SQL-verifiable items, enforced at MCP tool level via `check_gate()`
- Gate-ready seed profile: "Age of Embers" fantasy world, 2 books, 5 characters, 3 chapters, 6 scenes
- Full per-domain documentation: `docs/tools/` (18 files), `docs/schema/` (18 files), `docs/README.md` (master index)
- ~16,841 Python LOC, UV-managed, Hatchling build, pytest test suite

**Known tech debt:** None — all v1.0 and v1.1 debt cleared.

**User feedback:** None yet — engine pre-release, plugin integration next.

The system treats a 250,000-word epic fantasy novel (55 chapters, 6 POV characters, 20+ named agents) like a software project: structured data, version control, modular tooling. The SQLite database is the authoritative source of truth — markdown files are generated outputs, not editable sources.

Reference documents in `project-overview/`:
- `drafter-prd.md` — Full PRD with build sequence (Phases A–I)
- `agent-roster.md` — All 40 agent/skill definitions
- `plugin-ecosystem.md` — Ecosystem overview

Live docs in `docs/`:
- `docs/README.md` — Master navigation index (18 tool links, 18 schema links, error contract)
- `docs/tools/` — Per-domain tool reference (18 files, 231 tools total)
- `docs/schema/` — Per-domain schema reference (18 files, 71 tables, read-only justifications)

## Constraints

- **Runtime**: UV/Python — no global installs required; `uv run` invocation from plugin's `.mcp.json`
- **Database**: SQLite only — single-file, git-trackable schema, migration-based rebuild
- **MCP protocol**: `mcp` SDK — tools must conform to MCP tool call format with typed Pydantic models
- **Testing**: Seed files only — no dependency on real manuscript content
- **Separation**: This repo is engine-only; plugin and novel content repos stay separate

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| drafter = novel-tools Python repo only | Plugin is separate; engine must be stable first | ✓ v1.0 — engine stable, plugin integration next |
| Seed files for all testing | Keeps dev loop fast; real manuscript untouched | ✓ v1.0 — "Age of Embers" seed profile covers all 71 tables |
| Build order: DB → MCP → CLI → Plugin (separate) | Each layer depends on the previous | ✓ v1.0 — full build completed in dependency order |
| SQLite over Postgres | Single-file, travels with git, no server setup | ✓ v1.0 — FK enforcement verified, 20ms migrations |
| UV over pip/venv | No global installs, reproducible, fast | ✓ v1.0 — 38 packages, uv.lock tracked in git |
| mcp>=1.26.0,<2.0.0 bundled FastMCP (not standalone PyPI) | Standalone fastmcp diverged from SDK | ✓ Phase 1 — server stub starts cleanly on stdio |
| Nullable FKs for acts↔chapters and factions↔characters | Circular FK dependencies can't be avoided | ✓ Phase 1 — resolves DDL ordering, DML enforcement intact |
| `run()` function as novel-mcp entry point (not FastMCP instance) | Allows logging config before server loop | ✓ Phase 1 — no print() in server code |
| Migration 021 bundles 24 tables in single file | Keeps total at exactly 21 migration files | ✓ Phase 1 — Phase 11 added migration 022 for 7-point structure |
| register(mcp: FastMCP) -> None domain pattern | Clean separation of tool modules | ✓ Phase 3 — all 18 tool modules use this pattern |
| check_gate() in novel.mcp not novel.tools | Prevents circular import (tools import from mcp.gate) | ✓ Phase 6 — gate enforcement works cleanly |
| Gate has 36 items (not 33 as originally planned) | Implementation truth: 34 in Phase 6, +2 in Phase 11 | ✓ v1.0 — gate-ready seed matches actual count |
| CLI SQL intentionally duplicated from MCP tools | Isolation between sync CLI and async MCP layers | ✓ Phase 10 — no shared code, no async-in-sync bugs |
| Python source files as single source of truth for tool names | REQUIREMENTS.md confirmed to drift from implementation | ✓ Phase 12 — docs/mcp-tools.md accurate at 103 tools |
| 7-point structure tracked at story level + per-POV arc | Required for 6-POV epic fantasy with distinct character journeys | ✓ Phase 11 — 4 MCP tools, 2 gate items, 2 migrations |
| pydantic>=2.11 declared as direct dependency | Was pulled transitively only; explicit declaration ensures version contract | ✓ Phase 13 — pyproject.toml matches >=major.minor style |
| FK-safe pattern for parent-table deletes; log-delete for leaf tables | Parent tables with FK children need ValidationFailure on FK violation; leaf tables don't | ✓ Phase 14 — consistent error contract across all 128 new tools |
| No gate check on Phase 14 delete tools | Deletes are administrative ops; gate guards existing read/write tools in same modules | ✓ Phase 14 — consistent with module-level gate patterns |
| Per-domain doc files (docs/tools/, docs/schema/) over monoliths | Monoliths hit context limits and become stale; per-domain files are scoped and AI-navigable | ✓ Phase 15 — 37 files replace 2 monoliths; master index at docs/README.md |
| docs/README.md as condensed master index (not architecture doc) | Full architecture detail lives in project-overview/; README.md should be navigation-focused | ✓ Phase 15 — 79-line index with tool + schema links and error contract |

---
*Last updated: 2026-03-10 after v1.1 milestone*
