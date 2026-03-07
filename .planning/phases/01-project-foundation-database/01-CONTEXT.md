# Phase 1: Project Foundation & Database - Context

**Gathered:** 2026-03-07
**Status:** Ready for planning

<domain>
## Phase Boundary

Python project scaffolding with both entry points verified, all 21 SQL migrations executing cleanly in order, a database connection factory enforcing WAL mode and foreign key constraints, and 4 database CLI commands (`migrate`, `seed`, `reset`, `status`). Everything downstream depends on this layer — no MCP tools, no Pydantic models, no seed profiles are built here.

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion

User delegated all implementation choices to Claude. Decisions below reflect best practices for long-term maintainability and developer experience.

#### Migration file convention
- Numbered SQL files with descriptive names: `001_books.sql`, `002_characters.sql`, ... `021_xxx.sql`
- One migration = one logical domain group (not one table per file)
- Clean rebuild = delete the `.db` file and re-run all migrations in order (simplest, no DROP complexity)
- Migration runner reads files in numeric sort order from a single `drafter/db/migrations/` directory
- No migration version table needed for v1 — migrations are idempotent via `CREATE TABLE IF NOT EXISTS`

#### Seed data format
- Python modules in `drafter/seeds/` — e.g., `minimal.py` exports a `SEED_DATA` dict
- Python over SQL/YAML: IDE support, easy to read, no parsing overhead, can express relationships naturally
- `novel db seed minimal` imports the module and uses `executemany` with the dict data
- Seed modules are pure data — no database imports in seed files themselves

#### Project directory layout
```
drafter/
  __init__.py
  db/
    __init__.py
    migrations/          # 001_books.sql ... 021_xxx.sql
    connection.py        # get_connection() (sync) + get_async_connection() (async)
    migrate.py           # migration runner logic
    seed.py              # seed loader logic
  seeds/
    __init__.py
    minimal.py           # SEED_DATA dict for minimal profile
  cli/
    __init__.py
    main.py              # Typer app entry point (novel)
    db.py                # novel db subcommands
  mcp/
    __init__.py
    server.py            # FastMCP server entry point (novel-mcp)
pyproject.toml
```

#### DB status output
- Plain text, tabular — no Rich/color for v1 (Rich CLI is v2)
- Shows: migration count applied, total table count, and row counts for key tables (books, characters, chapters, scenes)
- Format: simple aligned columns, no box-drawing chars — works cleanly in any terminal and in CI logs

</decisions>

<specifics>
## Specific Ideas

No specific requirements — user deferred all choices to Claude's discretion.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- None — fresh project, no existing code

### Established Patterns
- MCP SDK: `mcp>=1.26.0,<2.0.0` with bundled `mcp.server.fastmcp` (not standalone fastmcp PyPI package)
- Python: 3.12+, aiosqlite for async (MCP server), sync sqlite3 for CLI
- Build backend: Hatchling (required for `[project.scripts]` entry points in pyproject.toml)
- CLI framework: Typer 0.24.x
- Package manager: uv 0.10.x

### Integration Points
- `connection.py` is the critical shared dependency: both the CLI (sync) and the MCP server (async) must use it, and it must enforce `PRAGMA foreign_keys=ON` and WAL mode on every connection
- The `drafter/mcp/server.py` module is the Phase 3 entry point — Phase 1 only scaffolds it enough to pass `--help`

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 01-project-foundation-database*
*Context gathered: 2026-03-07*
