# Project Research Summary

**Project:** Drafter
**Domain:** Python MCP Server + SQLite Narrative Database + UV-Managed CLI
**Researched:** 2026-03-07
**Confidence:** HIGH

## Executive Summary

Drafter is a Python MCP server with ~80 tools across 14 domains, backed by a SQLite narrative database (21 migration files) and a UV-managed CLI. It gives Claude Code structured, typed access to all story data for a 250,000-word epic fantasy novel. The recommended stack is well-established: Python 3.12+, the official MCP Python SDK (v1.26.x with built-in FastMCP), Pydantic v2 for type safety, aiosqlite for async database access in the MCP server, Typer for the CLI, and uv for project/dependency management. Every technology choice has HIGH confidence from verified official sources. There are no exotic dependencies or unproven libraries in the stack.

The architecture follows a strict layered build order: SQL migrations first, then database connection layer, then Pydantic models, then validators, then MCP tools, then CLI. The MCP server uses a single FastMCP instance with 14 domain files registering tools via decorators -- not 14 separate mounted servers. The CLI and MCP server share a database layer and Pydantic models but have independent execution paths (sync sqlite3 for CLI, async aiosqlite for MCP). The gate system (33 SQL-verifiable checklist items blocking prose operations) is the project's most distinctive architectural feature and must be enforced at the tool level, not just in agent prompt instructions.

The primary risks are well-understood and preventable. The biggest danger is 80 tools flooding Claude's context window -- mitigated by writing keyword-rich, search-optimized tool descriptions (Claude Code's Tool Search handles filtering). SQLite concurrency issues (database locked errors) are solved by WAL mode and aiosqlite. Schema drift between SQL migrations and Pydantic models is caught by a validation test comparing model fields against `PRAGMA table_info`. stdout corruption of MCP protocol messages is prevented by banning `print()` from server code. Every critical pitfall has a concrete prevention strategy and a clear phase where it must be addressed.

## Key Findings

### Recommended Stack

The stack is conventional Python with no surprises. All dependencies are mature, well-documented, and used by the MCP SDK project itself. The only version constraint that matters is pinning `mcp>=1.26.0,<2.0.0` because v2 is in pre-alpha with breaking changes.

**Core technologies:**
- **Python 3.12+**: Runtime -- mature, fast, best dependency compatibility
- **mcp SDK 1.26.x** (built-in FastMCP): MCP server framework -- official Anthropic SDK, decorator-based tool registration
- **Pydantic v2 (>=2.11)**: Data validation and models -- required by MCP SDK, drives JSON schema generation for tool parameters
- **aiosqlite 0.22.x**: Async SQLite bridge for MCP server -- wraps sqlite3 in thread executor for async correctness
- **Typer 0.24.x**: CLI framework -- type-hint-driven, includes Rich for formatting
- **uv 0.10.x**: Package/project management -- replaces pip, poetry, pyenv in a single binary
- **Hatchling**: Build backend -- required for `[project.scripts]` entry points (`novel`, `novel-mcp`)
- **SQLite (stdlib)**: Database -- single-file, git-trackable, migration-based rebuild

**Critical version constraint:** Pin `mcp<2.0.0`. Do NOT use the standalone `fastmcp` PyPI package (diverged from SDK built-in). Do NOT use SQLAlchemy, Flask, Django, or any web framework.

### Expected Features

**Must have (table stakes):**
- 21 SQL migrations + forward-only migration runner with clean-rebuild support
- DB connection manager enforcing WAL mode, foreign keys, and env-var-based path
- Pydantic input/output models for all 14 domains
- Core MCP tools for 5 priority domains: Characters, Chapters/Scenes, World, Relationships, Plot/Arcs
- Gate tools: `get_gate_status`, `run_gate_audit`, `get_gate_checklist`, `certify_gate`
- Consistent error contract across all tools: `null` for not-found, `is_valid: false` for validation, `requires_action` for gate violations
- `novel db migrate` and `novel db seed` CLI commands
- Minimal seed data (1 profile) exercising all v1 tools
- Basic pytest suite with in-memory FastMCP client
- Tool descriptions written as LLM instructions (search-optimized, action-oriented)

**Should have (differentiators):**
- Remaining 9 domain MCP tools (Canon, Knowledge, Foreshadowing, Names, Voice, Session, Publishing)
- Full CLI subcommands (export, import, query, session, gate, name)
- Tool tags and annotations (`readOnlyHint`, `destructiveHint`)
- Context-aware error messages with suggestions for LLM self-correction
- Gate enforcement at tool level via shared helper function (not just prompt instructions)
- Multiple seed profiles (minimal, full, gate-ready)
- `novel db reset` and `novel db status` convenience commands
- Parametrized test suite across all tools

**Defer (v2+):**
- Gate status caching (optimization)
- Dynamic toolset loading (context window optimization)
- `--dry-run` flags on destructive commands
- Rich colored CLI output
- Import scripts for existing markdown content

### Architecture Approach

The system is a single Python package (`drafter`) with two entry points: `novel` (CLI via Typer) and `novel-mcp` (MCP server via FastMCP). Both share a database layer (`db/`) and Pydantic models (`models/`), but run independently. The MCP server uses a lifespan pattern for a single shared database connection with WAL mode. Tools are organized as 14 domain files registering on one shared FastMCP instance via explicit imports in `tools/__init__.py`. The build order is strictly layered (migrations -> db -> models -> validators -> tools -> server -> CLI) with no circular dependencies.

**Major components:**
1. **FastMCP Server** (`server/app.py`) -- entry point, tool registration, lifespan DB connection, protocol compliance
2. **Tool Domain Modules** (14 files in `server/tools/`) -- business logic for ~80 tools, one file per domain
3. **Shared Database Layer** (`db/`) -- sync (sqlite3) and async (aiosqlite) connection managers, migration runner, query helpers
4. **Pydantic Models** (`models/`) -- input/output types for all tools, shared between MCP and CLI
5. **Validators** (`validators/`) -- cross-domain business logic (gate checks, magic compliance, timeline validation, name similarity)
6. **CLI** (`cli/`) -- Typer-based terminal commands for db ops, import/export, queries, gate management

### Critical Pitfalls

1. **80 tools flooding context window** -- Write keyword-rich, specific tool descriptions. Claude Code's Tool Search auto-filters when tools exceed 10% of context. Test tool selection accuracy with representative queries before moving past core tool implementation. Do NOT split into multiple servers prematurely.

2. **SQLite "database is locked" errors** -- Enable WAL mode on database creation (persists to file). Use aiosqlite in MCP server, sqlite3 in CLI. Connection-per-request pattern with context managers. Set `busy_timeout=5000` as safety net.

3. **Pydantic models drifting from SQL schema** -- Never use `SELECT *`. Name columns explicitly. Write a schema validation test comparing Pydantic fields against `PRAGMA table_info`. Run after every migration change. Checklist: migration SQL + Pydantic model + tool query + seed data.

4. **Gate system bypassable through direct tool calls** -- Enforce gate at the MCP tool level, not just in agent/skill markdown. Use a shared `check_gate()` helper called at the top of prose-phase tools. Define explicitly which tools are gate-blocked vs. architecture-phase tools.

5. **stdout corruption of MCP protocol** -- Ban `print()` from all MCP server code. Configure logging to stderr. Test in stdio mode early and often. Add a lint rule flagging `print(` in server directories.

6. **PRAGMA foreign_keys not enabled** -- SQLite disables FK enforcement by default. Single connection factory must run `PRAGMA foreign_keys=ON` on every connection. Validate with `PRAGMA foreign_key_check` after migrations. Test by inserting invalid FK references.

7. **UV entry point misconfiguration** -- Include `[build-system]` (hatchling) in pyproject.toml from day one. Test `uv run novel-mcp` and `uv run novel` immediately after project setup, not after building tools.

## Implications for Roadmap

Based on research, suggested phase structure:

### Phase 1: Project Foundation and Database Schema

**Rationale:** Everything depends on the database schema and project scaffolding. The migration files define every table that tools will query. The pyproject.toml with build system and entry points must work before any server code is written. This is the only phase with zero external dependencies.
**Delivers:** Working `pyproject.toml` with both entry points verified, all 21 SQL migration files, migration runner with clean-rebuild test, database connection factory (both sync and async) with WAL + FK enforcement, `novel db migrate` CLI command.
**Addresses:** SQL migrations + runner (P1), DB connection manager (P1), `novel db migrate` (P1), entry point configuration
**Avoids:** Migration ordering failures (clean-rebuild test), PRAGMA foreign_keys not enabled (connection factory), UV entry point misconfiguration (verify immediately)

### Phase 2: Pydantic Models and Seed Data

**Rationale:** Models must exist before tools can be written. Seed data must exist before tools can be tested. These are both "data definition" tasks with no server logic, and they naturally pair together.
**Delivers:** Pydantic models for all 14 domains + common types (NotFoundResponse, ValidationFailure, GateViolation), minimal seed data profile, `novel db seed` CLI command, seed data FK validation.
**Addresses:** Pydantic models for all domains (P1), minimal seed data (P1), error contract types (P1)
**Avoids:** Pydantic/schema drift (establish model-per-domain convention and schema validation test from the start)

### Phase 3: MCP Server Core + Priority Domain Tools

**Rationale:** The MCP server is the primary value delivery mechanism. Start with the FastMCP instance, lifespan pattern, and the 5 most-used domains during architecture work (Characters, Chapters/Scenes, World, Relationships, Plot/Arcs). This is enough to validate the entire tool registration pipeline end-to-end with Claude Code.
**Delivers:** Working MCP server with stdio transport, lifespan DB connection, ~30-40 tools across 5 core domains, error contract enforced across all tools, tool descriptions optimized for Tool Search, basic pytest suite with in-memory FastMCP client.
**Addresses:** Core domain MCP tools (P1), error contract enforcement (P1), tool descriptions as LLM instructions (P1), basic pytest (P1)
**Avoids:** 80 tools flooding context (validate tool selection accuracy with 5 domains first), stdout corruption (establish logging config and print() ban from first tool), database locked errors (aiosqlite + WAL in lifespan)

### Phase 4: Gate System

**Rationale:** The gate system is this project's most distinctive feature and the primary workflow constraint. It requires its own phase because: (a) the 33 SQL check queries are complex and need individual testing, (b) gate enforcement must be validated end-to-end (tool-level, not just prompt-level), and (c) it cross-cuts prose-phase tools. Build it after core tools exist so there are actual tools to gate-block.
**Delivers:** Gate tools (get_gate_status, run_gate_audit, get_gate_checklist, update_checklist_item, certify_gate), 33 SQL evidence queries, `check_gate()` helper function, gate enforcement on prose-phase tools, gate-ready seed profile, `novel gate check/status/certify` CLI commands.
**Addresses:** Gate tools (P1), gate enforcement decorator (P2), gate-ready seed profile (P2)
**Avoids:** Gate system bypassable (tool-level enforcement, not just skill markdown)

### Phase 5: Remaining Domain Tools

**Rationale:** With core domains and gate system proven, build out the remaining 9 domains. These are lower-risk because the patterns are established. Some domains (Names, Voice, Session) are simpler; others (Canon, Knowledge, Literary/Foreshadowing) involve cross-domain queries.
**Delivers:** ~40-50 additional tools across Canon, Knowledge/Reader, Foreshadowing/Literary, Names, Voice/Style, Timeline (full), Session/Project, Publishing. Tool tags and annotations. Parametrized test suite.
**Addresses:** Remaining 9 domain tools (P2), tool tags and annotations (P2), parametrized test suite (P2)
**Avoids:** N+1 queries in composite tools (use JOINs, verify with EXPLAIN QUERY PLAN), ambiguous tool descriptions (test selection accuracy at 80-tool scale)

### Phase 6: CLI Completion and Polish

**Rationale:** The CLI is secondary to the MCP server (Claude Code is the primary consumer). Build remaining CLI subcommands after all MCP tools work correctly. CLI commands can reuse the same database layer and models.
**Delivers:** Full CLI: export, import, query, session, name subcommands. `novel db reset` and `novel db status`. Context-aware error messages with suggestions. Colored output with Rich.
**Addresses:** Full CLI subcommands (P2), `novel db reset/status` (P2), context-aware errors (P2), colored output (P3)
**Avoids:** CLI/MCP code duplication (shared db/ and models/ layers already built)

### Phase Ordering Rationale

- **Foundation before tools:** The migration schema defines every table. No tool can be written without knowing what it queries. Database connection patterns (WAL, FK, env var) prevent three critical pitfalls.
- **Models before tools:** Pydantic models define tool input/output contracts. Writing tools without models means rewriting them later to match.
- **Core domains before all domains:** 5 domains (~35 tools) is enough to validate the entire pipeline (registration, protocol, error contract, testing) without the complexity of 80 tools. Tool selection accuracy can be measured at manageable scale.
- **Gate as a separate phase:** The gate system has unique complexity (33 SQL queries, cross-cutting enforcement) and is the project's differentiating feature. Rushing it into the core tools phase risks under-testing.
- **CLI last:** The CLI is a developer convenience layer. The MCP server is the production interface. CLI commands are straightforward Typer wrappers around the same database queries.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 3 (MCP Server Core):** The lifespan pattern for database connections, FastMCP tool registration order, and in-memory testing fixtures are documented but have nuances in practice. Research the exact `ctx.request_context.lifespan_context` access pattern and verify it works with aiosqlite.
- **Phase 4 (Gate System):** The 33 SQL evidence queries need to be designed against the actual schema. Each query must be indexed and performant. Research phase should verify query patterns against the migration DDL.
- **Phase 5 (Remaining Tools):** Canon and Knowledge domains involve cross-domain queries (joining characters, chapters, world data). Verify JOIN performance and consider denormalization if needed.

Phases with standard patterns (skip research-phase):
- **Phase 1 (Foundation):** pyproject.toml, migration runners, and SQLite connection patterns are thoroughly documented with HIGH confidence sources.
- **Phase 2 (Models + Seed Data):** Pydantic v2 model definition is well-documented. Seed data is straightforward SQL inserts.
- **Phase 6 (CLI):** Typer CLI patterns are standard and well-documented.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All sources are official docs, PyPI metadata, or SDK source code. Every version constraint verified. No ambiguity. |
| Features | HIGH | MCP spec verified against official protocol docs. Feature prioritization based on verified MCP best practices and comparable system analysis. |
| Architecture | HIGH | Patterns verified against MCP Python SDK source, FastMCP documentation, and production MCP server examples. Lifespan pattern confirmed in SDK. |
| Pitfalls | HIGH | All pitfalls verified against official SQLite docs, MCP SDK issues, and community production reports. Prevention strategies are concrete and testable. |

**Overall confidence:** HIGH

### Gaps to Address

- **FastMCP in-memory testing:** The exact fixture pattern for testing tools via `Client(transport=mcp)` needs validation against the specific MCP SDK version (1.26.x). The FastMCP testing docs reference the standalone package, not the SDK built-in. Verify during Phase 3 planning.
- **33 gate evidence queries:** The specific SQL queries for the gate checklist are not yet designed. They depend on the final schema from all 21 migrations. Design these during Phase 4 planning against the actual DDL.
- **Tool count impact on Claude Code:** The 80-tool context window impact is based on general measurements, not Drafter-specific testing. Validate tool selection accuracy during Phase 3 with the first 30-40 tools.
- **aiosqlite connection lifecycle:** Whether to use connection-per-request or a shared lifespan connection needs validation under actual MCP stdio concurrency. The architecture research recommends lifespan (shared), but pitfalls research suggests connection-per-request. Resolve during Phase 3 by testing concurrent tool calls.
- **Import/export format:** The CLI import/export commands need to parse and generate markdown files from the novel content repo. The exact markdown structure is not documented in the research. Defer this to Phase 6 planning when the CLI is built.

## Sources

### Primary (HIGH confidence)
- [MCP Python SDK (GitHub)](https://github.com/modelcontextprotocol/python-sdk) -- SDK source, FastMCP API, v2 status
- [MCP Python SDK (PyPI)](https://pypi.org/project/mcp/) -- v1.26.0 confirmed, dependency versions
- [MCP SDK v1.26.0 pyproject.toml](https://raw.githubusercontent.com/modelcontextprotocol/python-sdk/refs/tags/v1.26.0/pyproject.toml) -- exact dependency pins
- [MCP Specification: Tools (2025-06-18)](https://modelcontextprotocol.io/specification/2025-06-18/server/tools) -- protocol spec for tools, annotations, errors
- [uv Documentation](https://docs.astral.sh/uv/) -- project config, entry points
- [SQLite WAL Documentation](https://sqlite.org/wal.html) -- concurrency behavior
- [SQLite Foreign Key Support](https://sqlite.org/foreignkeys.html) -- PRAGMA enforcement
- [FastMCP Tool Documentation](https://gofastmcp.com/servers/tools) -- tool registration, tags, annotations
- [FastMCP Testing Documentation](https://gofastmcp.com/servers/testing) -- in-memory client patterns

### Secondary (MEDIUM confidence)
- [MCP Best Practices (Phil Schmid)](https://www.philschmid.de/mcp-best-practices) -- tool naming, description quality
- [MCP Tool Descriptions Research (arXiv)](https://arxiv.org/html/2602.14878v1) -- LLM tool selection accuracy
- [Claude Code MCP Tool Search](https://claudefa.st/blog/tools/mcp-extensions/mcp-tool-search) -- context bloat reduction measurements
- [Reducing MCP Token Usage by 100x (Speakeasy)](https://www.speakeasy.com/blog/how-we-reduced-token-usage-by-100x-dynamic-toolsets-v2) -- dynamic toolset patterns
- [Multi-threaded SQLite (Charles Leifer)](https://charlesleifer.com/blog/multi-threaded-sqlite-without-the-operationalerrors/) -- WAL + connection patterns
- [NearForm MCP Pitfalls](https://nearform.com/digital-community/implementing-model-context-protocol-mcp-tips-tricks-and-pitfalls/) -- implementation lessons

### Tertiary (LOW confidence)
- None. All research sources were PRIMARY or SECONDARY quality.

---
*Research completed: 2026-03-07*
*Ready for roadmap: yes*
