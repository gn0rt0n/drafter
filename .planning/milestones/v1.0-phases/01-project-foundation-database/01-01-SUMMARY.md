---
phase: 01-project-foundation-database
plan: "01"
subsystem: database

tags: [python, sqlite, aiosqlite, typer, mcp, fastmcp, hatchling, uv]

# Dependency graph
requires: []
provides:
  - Installable drafter package (uv sync, hatchling build)
  - Two entry points: novel CLI (novel.cli:app) and novel-mcp server (novel.mcp.server:run)
  - Sync SQLite connection factory (get_connection) with WAL + FK pragmas enforced
  - Async SQLite connection factory (get_connection) with WAL + FK pragmas enforced
  - Migration runner (discover_migrations, apply_migrations, drop_all_tables)
  - Root Typer CLI app with db subcommand group (migrate/seed/reset/status stubs)
  - FastMCP server scaffold on stdio transport with logging to stderr
  - Full src/novel package hierarchy for all downstream phases
affects:
  - 01-02-PLAN.md (adds .sql migration files to src/novel/migrations/)
  - 01-03-PLAN.md (implements db CLI commands using connection factories)
  - All Phase 3+ plans (register MCP tools on the FastMCP instance)

# Tech tracking
tech-stack:
  added:
    - hatchling (build backend)
    - typer>=0.24.0 (CLI framework)
    - aiosqlite>=0.17.0 (async SQLite)
    - mcp>=1.26.0,<2.0.0 (bundled FastMCP — NOT standalone fastmcp PyPI package)
    - uv 0.10.x (package manager)
  patterns:
    - Context manager pattern for sync DB connections (contextmanager + get_connection)
    - Async context manager pattern for MCP DB connections (asynccontextmanager + get_connection)
    - WAL + FK pragmas enforced on every connection open (connection-level, not persistent)
    - No print() in MCP server code — all logging to stderr via logging module
    - Entry points via hatchling [project.scripts] not __main__ blocks

key-files:
  created:
    - pyproject.toml
    - src/novel/__init__.py
    - src/novel/cli.py
    - src/novel/db/__init__.py
    - src/novel/db/cli.py
    - src/novel/db/connection.py
    - src/novel/db/migrations.py
    - src/novel/db/seed.py
    - src/novel/migrations/.gitkeep
    - src/novel/mcp/__init__.py
    - src/novel/mcp/db.py
    - src/novel/mcp/server.py
    - src/novel/models/__init__.py
    - src/novel/tools/__init__.py
    - .gitignore
    - uv.lock
  modified: []

key-decisions:
  - "mcp entry point is a run() function (not the FastMCP instance) to allow logging config before server loop"
  - "novel-mcp does not expose --help; it speaks JSON-RPC stdio — starting without errors is correct behavior"
  - "uv.lock tracked in git for reproducible installs (not gitignored)"
  - "db/cli.py stub created in Plan 01 so cli.py import resolves; full implementation deferred to Plan 03"

patterns-established:
  - "Connection pattern: every sync connection uses `with get_connection() as conn` from novel.db.connection"
  - "Async connection pattern: `async with get_connection() as conn` from novel.mcp.db"
  - "WAL pragma: always set on connection open — PRAGMA journal_mode=WAL"
  - "FK pragma: always set on connection open — PRAGMA foreign_keys=ON"
  - "No print() rule: all MCP server-side output via logging.getLogger(__name__) to stderr"

requirements-completed: [SETUP-01, SETUP-04]

# Metrics
duration: 2min
completed: 2026-03-07
---

# Phase 1 Plan 01: Project Foundation Summary

**drafter package scaffold with pyproject.toml entry points, sync/async SQLite connection factories enforcing WAL+FK pragmas, Typer CLI with db subgroup, and FastMCP stdio server stub**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-07T19:26:10Z
- **Completed:** 2026-03-07T19:28:16Z
- **Tasks:** 2
- **Files modified:** 16

## Accomplishments

- Full `src/novel/` package hierarchy created, installable via `uv sync` (38 packages, drafter 0.1.0)
- Sync and async SQLite connection factories both enforce `PRAGMA journal_mode=WAL` and `PRAGMA foreign_keys=ON` on every connection open — verified by automated pragma checks
- `uv run novel --help` shows db subcommand group; `uv run novel-mcp` starts FastMCP server on stdio transport
- Migration runner with `discover_migrations`, `apply_migrations`, `drop_all_tables` ready for Plan 02's .sql files
- db CLI stubs (migrate/seed/reset/status) in place so `novel.cli` import resolves; full implementation in Plan 03

## Task Commits

Each task was committed atomically:

1. **Task 1: pyproject.toml and package skeleton** - `537eb3f` (feat)
2. **Task 2: Connection factories, CLI, and MCP server stub** - `f601409` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified

- `pyproject.toml` — hatchling build, typer/aiosqlite/mcp deps, novel and novel-mcp entry points
- `src/novel/__init__.py` — package root, `__version__ = "0.1.0"`
- `src/novel/cli.py` — root Typer app, registers db subgroup via `app.add_typer(db_cli.app, name="db")`
- `src/novel/db/connection.py` — sync `get_connection()` context manager with WAL+FK pragmas
- `src/novel/db/migrations.py` — `discover_migrations`, `apply_migrations`, `drop_all_tables`
- `src/novel/db/cli.py` — db subcommand stubs (migrate/seed/reset/status)
- `src/novel/db/seed.py` — stub `load_seed_profile()` raises ValueError until Phase 2
- `src/novel/mcp/__init__.py` — mcp subpackage init
- `src/novel/mcp/db.py` — async `get_connection()` context manager with WAL+FK pragmas
- `src/novel/mcp/server.py` — FastMCP("novel-mcp") instance + `run()` entry point with stderr logging
- `src/novel/models/__init__.py` — placeholder for Phase 2 Pydantic models
- `src/novel/tools/__init__.py` — placeholder for Phase 3+ MCP tools
- `src/novel/migrations/.gitkeep` — tracks empty migrations directory (Plan 02 adds .sql files)
- `.gitignore` — extended with Python/SQLite/uv patterns
- `uv.lock` — tracked for reproducible installs

## Decisions Made

- Used `run()` function as the novel-mcp entry point (not the FastMCP instance directly) to allow logging configuration before the server event loop starts
- `novel-mcp --help` is not supported by design — FastMCP stdio servers speak JSON-RPC; starting without errors is correct behavior
- `uv.lock` tracked in git (not gitignored) for reproducible installs per plan instruction
- `src/novel/db/cli.py` stub created in this plan so `novel.cli` import resolves; full db command implementation deferred to Plan 03 as specified

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- Package is fully installable via `uv sync`
- Connection factories verified with pragma checks — ready for Plan 02 migrations to consume
- Migration runner (`discover_migrations`, `apply_migrations`) ready — Plan 02 adds .sql files to `src/novel/migrations/`
- db CLI stubs in place — Plan 03 implements migrate/seed/reset/status commands
- FastMCP instance ready — Phase 3+ registers MCP tools via `@mcp.tool()` decorators

---
*Phase: 01-project-foundation-database*
*Completed: 2026-03-07*

## Self-Check: PASSED

- All 16 files present on disk
- Commits 537eb3f and f601409 confirmed in git log
- Pragma verification: sync WAL=OK, FK=OK; async WAL=OK, FK=OK
