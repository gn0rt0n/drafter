# Feature Research

**Domain:** Python MCP server + CLI for database-backed narrative management (~80 tools, 14 domains)
**Researched:** 2026-03-07
**Confidence:** HIGH (MCP spec verified against official docs; FastMCP patterns verified against gofastmcp.com)

## Feature Landscape

### Table Stakes (Must Have or MCP Integration Breaks)

Features that are non-negotiable. Without these, the MCP server will not function correctly with Claude Code, or the developer experience will be so poor that iteration stalls.

#### MCP Protocol Compliance

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| `tools/list` with pagination | MCP spec requirement; clients discover tools via this endpoint | LOW | FastMCP handles this automatically. With ~80 tools, pagination matters for clients that batch-load. |
| `isError` flag on tool execution failures | MCP spec separates protocol errors from tool execution errors; LLMs need this to know retry vs. abandon | LOW | Return `isError: true` in CallToolResult, not Python exceptions. FastMCP's `ToolError` class handles this. |
| Typed input schemas via Pydantic | LLMs construct tool calls from JSON Schema; no schema = hallucinated arguments | MEDIUM | Every tool parameter needs a type annotation. Use `Annotated[int, Field(ge=1)]` for constraints. FastMCP auto-generates schemas from type hints. |
| Structured output (JSON in `structuredContent`) | MCP 2025-06-18 spec added `structuredContent` alongside `content` for machine-readable returns | MEDIUM | Return Pydantic models or dicts from tools; FastMCP auto-serializes to structured content. Also emit a `TextContent` block for backwards compatibility. |
| Tool descriptions as LLM instructions | Docstrings ARE the instructions the model reads to decide tool selection and argument formatting | LOW | Every tool needs a docstring specifying when to use it, what arguments mean, and what to expect back. This is not documentation for humans -- it is prompt engineering for the model. |
| Consistent error contract | The PRD defines: `null` for not-found, `is_valid: false` for validation failures, `requires_action` for gate violations. Agents depend on this contract to branch behavior. | MEDIUM | Enforce via shared response models. Every tool in every domain must follow the same contract -- one domain returning different shapes breaks agent logic. |
| Tool name prefixing by domain | With ~80 tools from one server, LLMs need disambiguation. The MCP best practice is `{service}_{action}_{resource}`. | LOW | Already designed in the PRD (e.g., `get_character`, `upsert_chapter`). Verify no name collisions across domains. Consider whether `novel_` prefix is needed since there is only one MCP server. |

#### Database Foundation

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Forward-only SQL migrations with version tracking | Reproducible schema on any machine; `novel db migrate` must build from scratch | MEDIUM | 21 migration files, applied in order. Track applied migrations in a `_migrations` table with timestamps. No rollback migrations -- forward-only is simpler and safer for SQLite. |
| WAL mode for SQLite | Write-Ahead Logging enables concurrent reads during writes; prevents "database is locked" errors when CLI and MCP server access the same file | LOW | Set `PRAGMA journal_mode=WAL` on every connection open. Single line, massive impact. |
| Connection management via context manager | Prevent leaked connections, ensure transactions commit/rollback properly | LOW | Wrap `sqlite3.connect()` in a context manager. Share the pattern between CLI and MCP server. |
| Foreign key enforcement | SQLite has foreign keys OFF by default; without `PRAGMA foreign_keys=ON`, referential integrity is a lie | LOW | Set on every connection open. The 21-migration schema has extensive FK relationships; they must actually be enforced. |
| Database path from environment variable | `NOVEL_DB_PATH` env var set in `.mcp.json`. The server must not hardcode paths. | LOW | Already specified in the PRD. Use `os.environ["NOVEL_DB_PATH"]` with a clear error if missing. |

#### CLI Foundation

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| `novel db migrate` -- build from scratch | The core developer loop: delete db, run migrate, get a clean schema | LOW | Apply all .sql files in order, skip already-applied ones. Must complete in under 5 seconds (PRD requirement). |
| `novel db seed` -- load test data | Development and testing require sample data without touching real manuscript | MEDIUM | Seed files are YAML or SQL fixtures covering all 14 domains. Must be minimal but sufficient to exercise every MCP tool. |
| Entry point via `pyproject.toml` `[project.scripts]` | `uv run novel` must work without `python -m` invocation | LOW | Standard Python packaging. One line in pyproject.toml: `novel = "novel.cli:app"`. |
| Subcommand structure (`novel db`, `novel export`, `novel query`, etc.) | The PRD defines 7 subcommand groups. Users expect consistent `noun verb` or `group action` patterns. | MEDIUM | Use Click or Typer. Typer is more Pythonic (type hints drive the CLI), but Click is more battle-tested. Recommend Click for the nested subcommand groups this project needs. |

### Differentiators (What Makes This Server Robust vs. Fragile)

These features separate a production-quality MCP server from a prototype. They are not required for basic functionality, but without them, the system will be brittle, hard to debug, and frustrating to iterate on.

#### Tool Discoverability and Context Efficiency

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Tool tags for domain grouping | With ~80 tools, LLMs waste tokens loading all tool schemas. FastMCP tags (`@mcp.tool(tags={"characters"})`) enable selective loading. Clients can filter by domain. | LOW | Tag every tool with its domain name. This costs nothing at registration time and enables future dynamic toolset patterns. |
| Concise, action-oriented tool descriptions | Research shows 66% of MCP servers have "smelly" descriptions. Concise descriptions reduce token usage by 30-60% and improve tool selection accuracy. | MEDIUM | Write descriptions as instructions: "Get a character's full sheet including voice profile and current emotional state. Use when you need comprehensive character info for a scene." NOT "This function retrieves character data from the database." |
| Tool annotations (`readOnlyHint`, `destructiveHint`) | MCP spec supports `annotations` on tools. Clients can auto-approve read-only tools and prompt for confirmation on destructive ones. | LOW | Mark all `get_*` and `list_*` tools as `readOnlyHint: true`. Mark `upsert_*` and `log_*` as `destructiveHint: false` (they create/update but are not destructive). Mark `certify_gate` as `destructiveHint: true` (irreversible state change). |

#### Error Messages That Enable LLM Self-Correction

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Context-aware error responses | When an MCP tool fails, the error message is consumed by an LLM, not a human. "Character not found" is useless. "Character 'Kael' not found. Available characters: Aelara, Brennan, Cira, Dorath, Elira, Fenn. Did you mean one of these?" enables self-correction. | MEDIUM | For not-found errors, include suggestions. For validation errors, include the specific field and constraint that failed. For gate violations, include the current gap count and what to do next. |
| Validation errors with field-level detail | `is_valid: false` with `errors: [{"field": "chapter_number", "error": "Must be between 1 and 55", "got": 99}]` lets the LLM fix and retry. | MEDIUM | Use Pydantic validation and catch `ValidationError`, then transform to the structured error format. |
| Timeout handling with `asyncio.timeout` | A tool that hangs blocks the entire MCP session. SQLite queries on a 250K-word novel's database could be slow. | LOW | Wrap database operations in `async with asyncio.timeout(30)`. Return a clear timeout error with the operation that timed out. |

#### Gate System (Architecture Completeness Enforcement)

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| 33-item SQL-verifiable gate checklist | The core workflow constraint: no prose until architecture is provably complete. Each checklist item is a SQL query returning a count of missing records. | HIGH | Already designed in the PRD (Section 7, Phase H). The complexity is in writing 33 correct SQL queries that cover world, characters, structure, chapters, scenes, and continuity. |
| `requires_action` response from prose-phase tools | When gate status is not `passed`, prose-phase tools (write scene, draft chapter) return `requires_action` instead of executing. The LLM sees what must happen first. | MEDIUM | Implement as a decorator or middleware: check gate status before tool execution. Cache the gate status per-session to avoid 33 SQL queries on every tool call. |
| Gate status caching | Running 33 SQL queries on every prose-phase tool call is wasteful. Cache the gate result and invalidate on `update_checklist_item` or `certify_gate`. | LOW | In-memory cache with explicit invalidation. The gate status changes infrequently (only during architecture work). |

#### Testing Infrastructure

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| In-memory FastMCP client testing | FastMCP 2.0+ supports direct in-memory connections between test clients and servers -- no subprocess, no network. Tests are fast and deterministic. | MEDIUM | Use `Client(transport=mcp)` fixture pattern. Test every tool with at least one success path and one error path. |
| Seed data as pytest fixtures | Reusable database states for testing: empty db, minimal seed, full seed, gate-passing seed. | MEDIUM | Create fixture functions that run migrations and load specific seed data sets. Use `tmp_path` for isolated test databases. |
| Parametrized tool testing | With ~80 tools, manual test writing does not scale. Parametrize tests across tool names with expected input/output patterns. | MEDIUM | Use `@pytest.mark.parametrize` to test all tools in a domain with a single test function. Test not-found, validation-failure, and success paths. |

#### Seed Data System

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Minimal but complete seed data | Every MCP tool must be exercisable without the real manuscript. Seed data covers all 14 domains with a tiny fictional world (2-3 characters, 3-5 chapters, 1 location set). | MEDIUM | YAML or JSON fixtures loaded by `novel db seed`. Keep seed files in the repo alongside migration files. |
| Seed data validates FK relationships | Seed data that violates foreign keys means tools will fail in tests but work in production (or vice versa). Seed loading must run with `PRAGMA foreign_keys=ON`. | LOW | Run seeds through the same connection configuration as production. |
| Multiple seed profiles | `novel db seed --profile minimal` for unit tests, `novel db seed --profile full` for integration tests, `novel db seed --profile gate-ready` for gate testing | LOW | Different YAML files per profile. The `gate-ready` profile has data satisfying all 33 checklist items. |

#### CLI Ergonomics for Developer Iteration

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| `novel db reset` (migrate + seed in one command) | The most common developer action: blow away the database and start fresh. Should be one command, not two. | LOW | `novel db reset` = delete db file + `novel db migrate` + `novel db seed`. Add `--profile` flag for seed selection. |
| `novel db status` (show migration state) | "Which migrations have been applied?" is a frequent question during development. | LOW | Query `_migrations` table, show applied vs. pending. |
| Colored CLI output with status indicators | Developers scan terminal output visually. Green checkmarks for applied migrations, red X for failures, yellow warnings. | LOW | Use `rich` or `click.style()`. Small effort, large UX improvement. |
| `--dry-run` flag on destructive operations | `novel db reset --dry-run` shows what would happen. `novel import all --dry-run` shows what would be imported without writing. | LOW | Print planned actions, then exit. Prevents accidental data loss during development. |

### Anti-Features (Deliberately NOT Building)

Features that seem appealing but create problems for this specific project.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Raw SQL execution tool | "Let the LLM write arbitrary SQL queries" | SQL injection risk. The LLM can hallucinate table/column names. Violates the "no raw SQL" design principle. Every valid query should be a named tool. | Build specific query tools for each use case. If a query pattern recurs, add a new MCP tool for it. |
| Dynamic tool generation from schema | "Auto-generate CRUD tools from the migration files" | Produces generic, undocumented tools with no domain logic. Tool descriptions would be meaningless. Gate enforcement and validation cannot be auto-generated. | Hand-write each tool with proper docstrings, validation, and error handling. 80 tools is manageable when organized by domain. |
| Web UI or REST API layer | "Add a web dashboard for viewing story data" | Out of scope per PRD. Adds a maintenance surface with no user. The consumer is Claude Code via MCP, not a human via browser. | Use `novel query` CLI commands for human-readable reports. Use `novel export` for markdown generation. |
| Real-time database change notifications | "Push updates when data changes" | SQLite does not support native change notifications. Polling or file watchers add complexity. The MCP session is request/response, not subscription-based. | Tools return current state on each call. The LLM re-queries when it needs fresh data. |
| ORM (SQLAlchemy, etc.) | "Use an ORM for type-safe database access" | Adds a heavy dependency for a single-file SQLite database. The schema is fixed (21 migrations), not evolving rapidly. Raw SQL with parameterized queries is simpler and more predictable for this use case. | Write a thin data access layer: parameterized SQL queries in Python functions, Pydantic models for input/output serialization. |
| Rollback migrations | "Support `novel db rollback` for undoing schema changes" | SQLite's ALTER TABLE is limited (no DROP COLUMN before 3.35). Rollback migrations are error-prone and rarely used. The database is rebuiltable from scratch in under 5 seconds. | `novel db reset` deletes and rebuilds. No rollback needed when rebuild is instant. |
| Plugin system for custom tools | "Let users add their own MCP tools" | This is a single-user system for one novel. Plugin architecture adds complexity with no audience. | If new tools are needed, add them directly to the codebase. |
| Async SQLite driver (aiosqlite) | "Use async I/O for database operations" | SQLite is a local file -- there is no I/O wait. `aiosqlite` runs SQLite in a thread pool, adding complexity without real concurrency benefit for local file access. | Use synchronous `sqlite3` module. Wrap blocking calls in `asyncio.to_thread()` if the MCP server framework requires async tool functions. |
| Multi-database support | "Support PostgreSQL as an alternative" | The PRD explicitly chose SQLite for single-file, git-trackable, no-server-setup properties. Multi-DB abstractions leak and add testing burden. | SQLite only. If Postgres is ever needed (it will not be), that is a rewrite, not a feature. |

## Feature Dependencies

```
[SQL Migrations (001-021)]
    |
    +--requires--> [Migration Runner (novel db migrate)]
    |                  |
    |                  +--requires--> [Seed Data System (novel db seed)]
    |                  |                  |
    |                  |                  +--enables--> [Test Fixtures (pytest)]
    |                  |                  |
    |                  |                  +--enables--> [Gate-Ready Seed Profile]
    |                  |
    |                  +--requires--> [DB Connection Manager (WAL, FK, ctx mgr)]
    |                                     |
    |                                     +--requires--> [Data Access Layer (parameterized SQL)]
    |                                                        |
    |                                                        +--requires--> [Pydantic Models (input/output)]
    |                                                        |                  |
    |                                                        |                  +--requires--> [MCP Tool Registration (FastMCP)]
    |                                                        |                  |                  |
    |                                                        |                  |                  +--enables--> [Tool Tags & Annotations]
    |                                                        |                  |                  |
    |                                                        |                  |                  +--enables--> [Structured Output]
    |                                                        |                  |
    |                                                        |                  +--requires--> [Error Contract (null/is_valid/requires_action)]
    |                                                        |
    |                                                        +--requires--> [Gate Queries (33 SQL checks)]
    |                                                                           |
    |                                                                           +--enables--> [Gate Enforcement Decorator]
    |                                                                           |
    |                                                                           +--enables--> [Gate Status Caching]

[CLI Framework (Click/Typer)]
    |
    +--requires--> [DB Connection Manager]
    +--requires--> [Data Access Layer]
    +--enables--> [novel db reset / status]
    +--enables--> [novel export / import / query commands]
    +--enables--> [novel session start / close]
    +--enables--> [novel gate check / status / certify]

[MCP Tool Registration] --conflicts--> [Dynamic Tool Generation]
    (hand-written tools with domain logic vs. auto-generated CRUD)

[In-Memory Testing] --requires--> [FastMCP Client fixture + Seed Data Fixtures]
```

### Dependency Notes

- **MCP Tools require Data Access Layer:** Tools cannot be implemented until the SQL queries and Pydantic models exist. Build bottom-up: migrations -> connection -> DAL -> models -> tools.
- **Gate enforcement requires gate queries:** The 33 SQL check queries must be written and tested before the gate decorator can wrap prose-phase tools.
- **Seed data requires migrations:** Seeds insert into tables that migrations create. Seed development happens after schema is stable.
- **Testing requires seeds + FastMCP:** In-memory testing needs both the FastMCP Client fixture pattern and seed data to exercise tools against.
- **CLI and MCP share the Data Access Layer:** Both the `novel` CLI commands and the MCP tools call the same Python functions for database access. Build the DAL as a shared library, not duplicated code.

## MVP Definition

### Launch With (v1)

Minimum viable product -- what is needed to validate that the MCP server works with Claude Code for real story architecture work.

- [ ] **21 SQL migrations + migration runner** -- the entire schema must exist before any tool can work
- [ ] **DB connection manager with WAL, FK enforcement, env var path** -- foundational infrastructure
- [ ] **Pydantic input/output models for all 14 domains** -- type safety for every tool call
- [ ] **Core MCP tools: Characters, Chapters/Scenes, World, Relationships, Plot/Arcs** -- the 5 most-used domains during architecture work
- [ ] **Gate tools: get_gate_status, run_gate_audit, get_gate_checklist, certify_gate** -- the workflow constraint that defines this system
- [ ] **Error contract enforced across all tools** -- `null`/`is_valid: false`/`requires_action` consistently
- [ ] **`novel db migrate` and `novel db seed` CLI commands** -- developer iteration loop
- [ ] **Minimal seed data (1 profile)** -- enough to exercise all v1 tools
- [ ] **Basic pytest suite with in-memory FastMCP client** -- at least smoke tests for each tool

### Add After Validation (v1.x)

Features to add once the core tools are confirmed working in Claude Code.

- [ ] **Remaining MCP tools: Canon, Knowledge/Reader, Foreshadowing/Literary, Names, Voice/Style, Session/Project, Publishing** -- the other 9 domains
- [ ] **Full CLI: export, import, query, session, name subcommands** -- human-facing commands
- [ ] **Tool tags and annotations** -- context efficiency for ~80 tools
- [ ] **Context-aware error messages with suggestions** -- LLM self-correction
- [ ] **Gate enforcement decorator on prose-phase tools** -- requires_action responses
- [ ] **Multiple seed profiles (minimal, full, gate-ready)** -- testing flexibility
- [ ] **`novel db reset` and `novel db status` commands** -- developer convenience
- [ ] **Parametrized test suite across all tools** -- comprehensive coverage

### Future Consideration (v2+)

Features to defer until the system is stable and in daily use.

- [ ] **Gate status caching** -- optimization, not needed until prose phase begins
- [ ] **Dynamic toolset loading (lazy tool schemas)** -- optimization for context window, not needed with Claude's current window size
- [ ] **`--dry-run` flags on all destructive commands** -- convenience, not critical
- [ ] **Colored CLI output with rich formatting** -- polish
- [ ] **Import scripts for existing markdown** -- needed for the novel content repo, but not for the engine development itself

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| SQL migrations + runner | HIGH | LOW | P1 |
| DB connection manager (WAL, FK, env var) | HIGH | LOW | P1 |
| Pydantic models for all domains | HIGH | MEDIUM | P1 |
| Core domain MCP tools (5 domains) | HIGH | HIGH | P1 |
| Error contract enforcement | HIGH | MEDIUM | P1 |
| Gate tools (4 tools) | HIGH | MEDIUM | P1 |
| `novel db migrate` + `novel db seed` | HIGH | LOW | P1 |
| Minimal seed data | HIGH | MEDIUM | P1 |
| Basic pytest smoke tests | HIGH | MEDIUM | P1 |
| Tool descriptions as LLM instructions | HIGH | LOW | P1 |
| Remaining 9 domain MCP tools | HIGH | HIGH | P2 |
| Full CLI subcommands | MEDIUM | MEDIUM | P2 |
| Tool tags and annotations | MEDIUM | LOW | P2 |
| Context-aware error messages | MEDIUM | MEDIUM | P2 |
| Gate enforcement decorator | HIGH | LOW | P2 |
| Multiple seed profiles | MEDIUM | LOW | P2 |
| `novel db reset` / `novel db status` | MEDIUM | LOW | P2 |
| Parametrized test suite | MEDIUM | MEDIUM | P2 |
| Gate status caching | LOW | LOW | P3 |
| Dynamic toolset loading | LOW | HIGH | P3 |
| `--dry-run` flags | LOW | LOW | P3 |
| Colored CLI output | LOW | LOW | P3 |
| Import scripts | MEDIUM | HIGH | P3 |

**Priority key:**
- P1: Must have for launch -- without these, the MCP server cannot function with Claude Code
- P2: Should have, add when possible -- these make the system robust and pleasant to use
- P3: Nice to have, future consideration -- optimizations and polish

## Comparable System Analysis

| Feature | Anthropic SQLite MCP Server | GitHub MCP Server | FastMCP Examples | Drafter Approach |
|---------|----------------------------|-------------------|------------------|------------------|
| Tool count | ~10 (generic CRUD) | ~30 (API wrappers) | 5-15 per example | ~80 (domain-specific, hand-written) |
| Error handling | Generic exceptions | `isError` flag | `ToolError` class | Structured contract: `null`/`is_valid`/`requires_action` |
| Schema validation | Minimal | JSON Schema | Pydantic auto-gen | Pydantic with `Annotated[T, Field()]` constraints |
| Tool descriptions | Generic | Action-oriented | Variable | LLM-instruction-style docstrings |
| Database management | Direct SQL exposure | N/A (API-backed) | N/A | Migration-based schema, no raw SQL exposure |
| Testing | Manual | CI integration | In-memory client | In-memory client + seed fixtures + parametrized |
| Tool organization | Flat namespace | Flat namespace | Tags (FastMCP 2.0+) | Domain-prefixed names + tags |
| Gate/workflow enforcement | None | None | None | 33-item SQL-verifiable checklist blocks prose phase |

## Sources

- [MCP Specification: Tools (2025-06-18)](https://modelcontextprotocol.io/specification/2025-06-18/server/tools) -- Official protocol spec for tool listing, calling, annotations, error handling, structured output
- [FastMCP Tool Documentation](https://gofastmcp.com/servers/tools) -- Tool registration, Pydantic integration, tags, annotations, structured output
- [FastMCP Testing Documentation](https://gofastmcp.com/servers/testing) -- In-memory client testing patterns
- [MCP Best Practices (Phil Schmid)](https://www.philschmid.de/mcp-best-practices) -- Outcomes over operations, flatten arguments, curate ruthlessly, name for discovery
- [Stop Vibe-Testing Your MCP Server (Jlowin)](https://www.jlowin.dev/blog/stop-vibe-testing-mcp-servers) -- Why deterministic testing matters for MCP
- [MCP Tool Descriptions Are Smelly (arXiv)](https://arxiv.org/html/2602.14878v1) -- Research on tool description quality affecting LLM tool selection
- [Reducing MCP Token Usage by 100x (Speakeasy)](https://www.speakeasy.com/blog/how-we-reduced-token-usage-by-100x-dynamic-toolsets-v2) -- Dynamic toolset patterns for large tool counts
- [MCP Error Handling Guide (MCPcat)](https://mcpcat.io/guides/error-handling-custom-mcp-servers/) -- Error classification framework, isError patterns
- [MCP Error Handling (Stainless)](https://www.stainless.com/mcp/error-handling-and-debugging-mcp-servers) -- Protocol errors vs. tool execution errors
- [Python MCP SDK (GitHub)](https://github.com/modelcontextprotocol/python-sdk) -- Official Python SDK
- [FastMCP (GitHub)](https://github.com/jlowin/fastmcp) -- FastMCP framework, tool organization patterns

---
*Feature research for: Python MCP server + CLI for narrative database management*
*Researched: 2026-03-07*
