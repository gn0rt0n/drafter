# Stack Research

**Domain:** Python MCP Server + SQLite Narrative Database + UV-Managed CLI
**Researched:** 2026-03-07
**Confidence:** HIGH

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended | Confidence |
|------------|---------|---------|-----------------|------------|
| Python | >=3.12 | Runtime | 3.12 is the sweet spot: mature, fast, widely deployed. 3.13 works but 3.12 is safer for dependency compatibility. The MCP SDK requires >=3.10, but there is no reason to target anything older than 3.12. | HIGH |
| uv | 0.10.x | Package/project manager | The standard Python project manager for 2025/2026. Replaces pip, pip-tools, pipx, poetry, pyenv, and virtualenv in a single Rust-built binary. No global Python installs required. The PRD already specifies uv. | HIGH |
| mcp (Python SDK) | 1.26.0 | MCP server framework | The official Anthropic MCP Python SDK. Includes FastMCP (high-level decorator API) at `mcp.server.fastmcp`. Pin to `>=1.26.0,<2.0.0` because v2 is in pre-alpha and will have breaking changes. | HIGH |
| Pydantic | >=2.11.0,<3.0.0 | Data validation / models | Required by the MCP SDK. Use Pydantic v2 models for all tool input/output types. The MCP SDK v1.26.0 pins `pydantic>=2.11.0,<3.0.0`. | HIGH |
| SQLite (stdlib) | sqlite3 | Database | Python's built-in `sqlite3` module. No external driver needed. Single-file, git-trackable schema, migration-based rebuild. Already specified in the PRD. | HIGH |
| Typer | 0.24.x | CLI framework | The standard Python CLI framework for 2025/2026. Built on Click but uses type hints for automatic interface generation. Produces the `novel` command with subcommands. The MCP SDK itself uses Typer for its CLI optional dependency. | HIGH |
| Hatchling | latest | Build backend | The default build backend for uv projects. Lightweight, fast, PEP-compliant. Used by the MCP SDK itself. Required to expose `[project.scripts]` entry points. | HIGH |

### Supporting Libraries

| Library | Version | Purpose | When to Use | Confidence |
|---------|---------|---------|-------------|------------|
| aiosqlite | 0.22.x | Async SQLite bridge | For the MCP server, which runs in an async event loop (anyio). Wraps stdlib `sqlite3` in a thread executor. Use for all database access from MCP tool handlers. | HIGH |
| anyio | >=4.5 | Async I/O | Already a transitive dependency of the MCP SDK. Use for any async patterns in the server. Do not import asyncio directly -- anyio is the abstraction layer. | HIGH |
| Rich | >=13.9.4 | Terminal formatting | Already a dependency of Typer. Use for CLI output formatting, progress bars, tables. Do not add separately -- comes with Typer. | HIGH |
| pydantic-settings | >=2.5.2 | Configuration | Already a transitive dependency of MCP SDK. Use for loading `NOVEL_DB_PATH` and other environment variables with type validation. | MEDIUM |
| pytest | >=8.3.4 | Testing | Standard Python test framework. Use for all unit and integration tests. | HIGH |
| pytest-asyncio | >=1.3.0 | Async test support | Required for testing async MCP tool handlers. Use `@pytest.mark.asyncio` for async test functions. | HIGH |
| ruff | >=0.8.5 | Linting + formatting | The standard Python linter/formatter for 2025/2026. Replaces flake8, isort, black. Used by the MCP SDK project itself. | HIGH |
| pyright | >=1.1.400 | Type checking | Static type checker. Preferred over mypy for Pydantic v2 projects due to better inference. Used by the MCP SDK project itself. | MEDIUM |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| uv | Project management, dependency resolution, virtual envs | Run everything through `uv run`, `uv add`, `uv sync`. Never use pip directly. |
| ruff | Lint + format | Configure in `pyproject.toml` under `[tool.ruff]`. Single tool replaces flake8 + isort + black. |
| pyright | Type checking | Configure in `pyproject.toml` under `[tool.pyright]`. Set `typeCheckingMode = "standard"`. |
| pytest | Test runner | Configure in `pyproject.toml` under `[tool.pytest.ini_options]`. |
| mcp dev | MCP Inspector | Run `uv run mcp dev src/drafter/mcp/server.py` to launch the MCP Inspector for interactive tool testing during development. Requires `mcp[cli]` extra. |

## Project Structure

The PRD specifies a `novel-tools/` repo. For this build (the `drafter` repo), the recommended layout:

```
drafter/
|-- pyproject.toml                    # Single project config
|-- uv.lock                          # Committed lockfile
|-- README.md
|
|-- src/
|   `-- drafter/                     # The importable package
|       |-- __init__.py
|       |
|       |-- cli/                     # Typer CLI (`novel` command)
|       |   |-- __init__.py
|       |   |-- main.py             # Typer app, top-level command group
|       |   |-- db.py               # `novel db migrate`, `novel db backup`
|       |   |-- export.py           # `novel export chapter`, `novel export all`
|       |   |-- import_.py          # `novel import world`, etc.
|       |   |-- query.py            # `novel query pov-balance`, etc.
|       |   |-- session.py          # `novel session start/close`
|       |   |-- gate.py             # `novel gate check/status/certify`
|       |   `-- name.py             # `novel name check/register`
|       |
|       |-- mcp/                    # MCP server
|       |   |-- __init__.py
|       |   |-- server.py           # FastMCP instance + tool imports
|       |   |-- db.py               # Async connection pool / manager
|       |   |-- models.py           # Pydantic input/output models
|       |   |-- tools/              # One file per domain (14 domains)
|       |   |   |-- __init__.py
|       |   |   |-- characters.py
|       |   |   |-- relationships.py
|       |   |   |-- chapters.py
|       |   |   |-- plot.py
|       |   |   |-- timeline.py
|       |   |   |-- world.py
|       |   |   |-- canon.py
|       |   |   |-- knowledge.py
|       |   |   |-- foreshadowing.py
|       |   |   |-- names.py
|       |   |   |-- voice.py
|       |   |   |-- gate.py
|       |   |   |-- session.py
|       |   |   `-- publishing.py
|       |   `-- validators/         # Business logic validators
|       |       |-- __init__.py
|       |       |-- magic.py
|       |       |-- timeline.py
|       |       |-- names.py
|       |       `-- gate.py
|       |
|       |-- db/                     # Shared database layer
|       |   |-- __init__.py
|       |   |-- connection.py       # Sync connection for CLI
|       |   |-- async_connection.py # Async connection for MCP
|       |   |-- migrations.py       # Migration runner
|       |   `-- migrations/         # 21 SQL migration files
|       |       |-- 001_core_entities.sql
|       |       |-- 002_characters.sql
|       |       `-- ...
|       |
|       `-- models/                 # Shared Pydantic models
|           |-- __init__.py
|           |-- characters.py
|           |-- chapters.py
|           `-- ...                 # One per domain
|
|-- tests/
|   |-- conftest.py                 # Fixtures: in-memory DB, test client
|   |-- test_cli/
|   |-- test_mcp/
|   `-- test_db/
|
`-- seed/                           # Seed data for testing
    |-- characters.json
    |-- chapters.json
    `-- ...
```

### Key Structural Decisions

**src layout**: Use `src/drafter/` not flat `drafter/`. The src layout prevents accidental imports from the project root, which matters for a package with entry points. Both uv and hatchling support it natively.

**Shared `db/` layer**: Both CLI (sync) and MCP server (async) need database access. The `db/` module provides both sync (`sqlite3`) and async (`aiosqlite`) connection managers. SQL queries live close to their callers in the tool/CLI modules, not centralized in a query repository.

**Shared `models/` layer**: Pydantic models used by both CLI output formatting and MCP tool responses live in a shared location. Avoids duplication.

**Two entry points, one package**: The CLI (`novel`) and MCP server (`novel-mcp`) are separate entry points in the same package. They share the database layer and models but have distinct execution paths.

## pyproject.toml Reference

```toml
[project]
name = "drafter"
version = "0.1.0"
description = "Novel management engine: MCP server + CLI for SQLite narrative database"
requires-python = ">=3.12"
dependencies = [
    "mcp>=1.26.0,<2.0.0",
    "typer>=0.24.0",
    "aiosqlite>=0.22.0",
    "pydantic>=2.11.0,<3.0.0",
]

[project.scripts]
novel = "drafter.cli.main:app"
novel-mcp = "drafter.mcp.server:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[dependency-groups]
dev = [
    "pytest>=8.3.4",
    "pytest-asyncio>=1.3.0",
    "ruff>=0.8.5",
    "pyright>=1.1.400",
    "mcp[cli]>=1.26.0,<2.0.0",
]

[tool.hatch.build.targets.wheel]
packages = ["src/drafter"]

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "SIM", "TCH"]

[tool.pyright]
pythonVersion = "3.12"
typeCheckingMode = "standard"
venvPath = "."
venv = ".venv"

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
```

### Entry Point Details

**`novel` CLI entry point:**
```python
# src/drafter/cli/main.py
import typer

app = typer.Typer(name="novel", help="Novel management CLI")

# Import and register subcommands
from drafter.cli import db, export, import_, query, session, gate, name

app.add_typer(db.app, name="db")
app.add_typer(export.app, name="export")
app.add_typer(import_.app, name="import")
app.add_typer(query.app, name="query")
app.add_typer(session.app, name="session")
app.add_typer(gate.app, name="gate")
app.add_typer(name.app, name="name")

if __name__ == "__main__":
    app()
```

**`novel-mcp` server entry point:**
```python
# src/drafter/mcp/server.py
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("novel")

# Import tool modules to trigger @mcp.tool() registration
from drafter.mcp.tools import (  # noqa: F401, E402
    characters,
    relationships,
    chapters,
    plot,
    timeline,
    world,
    canon,
    knowledge,
    foreshadowing,
    names,
    voice,
    gate,
    session,
    publishing,
)


def main():
    """Entry point for the novel-mcp command."""
    mcp.run()  # Defaults to stdio transport


if __name__ == "__main__":
    main()
```

**Tool registration pattern (per domain file):**
```python
# src/drafter/mcp/tools/characters.py
from drafter.mcp.server import mcp
from drafter.mcp.db import get_db
from drafter.models.characters import Character, CharacterState


@mcp.tool()
async def get_character(character_id: int) -> Character | None:
    """Get a character by ID. Returns null if not found."""
    async with get_db() as db:
        row = await db.execute_fetchone(
            "SELECT * FROM characters WHERE id = ?", (character_id,)
        )
        if row is None:
            return None
        return Character.model_validate(dict(row))


@mcp.tool()
async def list_characters(book_id: int = 1) -> list[Character]:
    """List all characters for a book."""
    async with get_db() as db:
        rows = await db.execute_fetchall(
            "SELECT * FROM characters WHERE book_id = ?", (book_id,)
        )
        return [Character.model_validate(dict(row)) for row in rows]
```

**MCP server registration in `.mcp.json` (plugin side):**
```json
{
  "mcpServers": {
    "novel": {
      "command": "uv",
      "args": [
        "run",
        "--project",
        "/path/to/drafter",
        "novel-mcp"
      ],
      "env": {
        "NOVEL_DB_PATH": "/path/to/your-novel/.db/novel.sqlite"
      }
    }
  }
}
```

## Database Connection Patterns

### Async (MCP Server) -- aiosqlite

```python
# src/drafter/mcp/db.py
import os
from contextlib import asynccontextmanager

import aiosqlite


def get_db_path() -> str:
    path = os.environ.get("NOVEL_DB_PATH")
    if not path:
        raise RuntimeError("NOVEL_DB_PATH environment variable is not set")
    return path


@asynccontextmanager
async def get_db():
    """Async context manager for database connections."""
    db = await aiosqlite.connect(get_db_path())
    db.row_factory = aiosqlite.Row
    try:
        yield db
    finally:
        await db.close()
```

### Sync (CLI) -- sqlite3

```python
# src/drafter/db/connection.py
import os
import sqlite3
from contextlib import contextmanager


def get_db_path() -> str:
    path = os.environ.get("NOVEL_DB_PATH")
    if not path:
        raise RuntimeError("NOVEL_DB_PATH environment variable is not set")
    return path


@contextmanager
def get_db():
    """Sync context manager for database connections."""
    db = sqlite3.connect(get_db_path())
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA foreign_keys=ON")
    try:
        yield db
    finally:
        db.close()
```

## Installation

```bash
# Initialize the project (already done)
uv init --package drafter

# Add core dependencies
uv add "mcp>=1.26.0,<2.0.0"
uv add "typer>=0.24.0"
uv add "aiosqlite>=0.22.0"
uv add "pydantic>=2.11.0,<3.0.0"

# Add dev dependencies
uv add --group dev pytest pytest-asyncio ruff pyright
uv add --group dev "mcp[cli]>=1.26.0,<2.0.0"

# Sync and verify
uv sync

# Verify entry points work
uv run novel --help
uv run novel-mcp  # Starts stdio server (will hang waiting for input -- Ctrl+C)

# Run the MCP Inspector for interactive testing
uv run mcp dev src/drafter/mcp/server.py
```

## Alternatives Considered

| Category | Recommended | Alternative | When to Use Alternative |
|----------|-------------|-------------|-------------------------|
| CLI Framework | Typer 0.24.x | Click 8.x | Only if you need deeply custom parameter types or multi-level command composition that Typer cannot express. Since Typer wraps Click, you can drop to Click APIs within a Typer app when needed. |
| CLI Framework | Typer 0.24.x | argparse (stdlib) | Never for this project. argparse lacks subcommand UX quality, Rich integration, and type-hint-driven interface generation. |
| Build Backend | Hatchling | uv_build | uv_build is newer and faster, but Hatchling is more mature, better documented, and used by the MCP SDK itself. Use uv_build only for trivially simple packages with no custom build needs. |
| Build Backend | Hatchling | Poetry-core | Only if the team already standardizes on Poetry. For greenfield projects, Hatchling is lighter and more PEP-compliant. |
| Async SQLite | aiosqlite 0.22.x | sqlite3 (sync in async handler) | If you wrap sync sqlite3 calls in `anyio.to_thread.run_sync()` yourself. aiosqlite does exactly this internally but provides a cleaner API. Use raw sqlite3 only in the CLI (sync context). |
| MCP Framework | mcp SDK (built-in FastMCP) | Standalone FastMCP 3.x package | FastMCP 3.x (the standalone `pip install fastmcp`) has diverged from the SDK's built-in `mcp.server.fastmcp`. The standalone is more feature-rich but adds a dependency and potential version conflicts. For this project, the built-in FastMCP in the `mcp` SDK is sufficient -- we need tool registration, not OpenAPI providers or component versioning. |
| Type Checker | Pyright | mypy | Mypy works but Pyright has better Pydantic v2 inference, faster execution, and is used by the MCP SDK project itself. |
| Linter | Ruff | flake8 + isort + black | Ruff replaces all three in a single Rust-built tool. Faster, simpler config. No reason to use the trio for new projects. |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| Standalone `fastmcp` package (PyPI) | Diverged from the official MCP SDK's built-in FastMCP. Adds dependency conflicts and confusion about which API to use. The standalone version targets advanced use cases (OpenAPI providers, component versioning) that this project does not need. | `from mcp.server.fastmcp import FastMCP` (built into the `mcp` SDK) |
| SQLAlchemy | Massive ORM overhead for a project that needs direct SQL control. The 21 migration files are hand-written SQL. The PRD explicitly states "agents never write raw SQL" but the engine layer runs direct SQL through sqlite3/aiosqlite. An ORM adds indirection without value here. | `sqlite3` (CLI) + `aiosqlite` (MCP server) |
| Flask/Django/FastAPI | No web API layer exists in this project. The MCP server uses stdio transport (subprocess), not HTTP. The CLI is a terminal tool. Web frameworks add unnecessary weight and wrong execution model. | MCP SDK's built-in server with stdio transport |
| pip / pipenv / poetry (as package manager) | uv is the 2025/2026 standard. Faster, simpler, more capable. The PRD already mandates uv. | `uv` |
| MCP SDK v2 | Still in pre-alpha on the `main` branch. Breaking changes expected. The `v1.x` branch is the stable production line. Pin `<2.0.0`. | `mcp>=1.26.0,<2.0.0` |
| Pydantic v1 | End-of-life. The MCP SDK requires Pydantic v2 (>=2.11.0). Do not use v1-style model definitions (`class Config:`, `.dict()`, `.parse_obj()`). | Pydantic v2 with `.model_validate()`, `.model_dump()`, `model_config = ConfigDict(...)` |
| asyncio directly | The MCP SDK uses anyio as its async abstraction. Mixing raw asyncio imports can cause compatibility issues. | `anyio` (already a transitive dependency) |
| Global Python installs | The entire point of uv is avoiding this. Everything runs through `uv run`. | `uv run novel ...`, `uv run novel-mcp` |

## MCP SDK Key APIs Reference

### FastMCP Server Instance

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "novel",                    # Server name (shows in MCP Inspector)
)
```

### Tool Decorator

```python
@mcp.tool()
async def tool_name(param: str, optional: int = 10) -> dict:
    """Docstring becomes the tool description shown to LLMs."""
    return {"result": "value"}
```

- Function name becomes the tool name
- Docstring becomes the tool description
- Type hints drive the JSON Schema for parameters
- Return type is serialized as the tool result
- Supports both sync and async functions

### Context Object

```python
from mcp.server.fastmcp import Context

@mcp.tool()
async def tool_with_context(param: str, ctx: Context) -> str:
    """Tool that uses context for logging and progress."""
    ctx.info("Processing...")
    await ctx.report_progress(50, 100)
    return "done"
```

### Resource Decorator (read-only data)

```python
@mcp.resource("novel://schema/{table_name}")
async def get_schema(table_name: str) -> str:
    """Expose database schema as a readable resource."""
    return schema_text
```

### Transport Options

| Transport | Use Case | How to Run |
|-----------|----------|------------|
| stdio (default) | Claude Code integration via subprocess | `mcp.run()` or `mcp.run(transport="stdio")` |
| streamable-http | Remote/networked access | `mcp.run(transport="streamable-http")` |
| SSE | Legacy HTTP streaming | `mcp.run(transport="sse")` -- deprecated in favor of streamable-http |

**For this project, always use stdio.** Claude Code launches the MCP server as a subprocess via `uv run novel-mcp`. The `.mcp.json` configuration handles the invocation.

## MCP Error Contract Implementation

The PRD specifies a specific error contract. Here is how to implement it with the MCP SDK:

```python
from pydantic import BaseModel


class NotFoundResponse(BaseModel):
    not_found_message: str


class ValidationResponse(BaseModel):
    is_valid: bool
    errors: list[str]


class GateBlockedResponse(BaseModel):
    requires_action: str


@mcp.tool()
async def get_character(character_id: int) -> dict | None:
    """Get a character by ID. Returns null with not_found_message if not found."""
    async with get_db() as db:
        row = await db.execute_fetchone(
            "SELECT * FROM characters WHERE id = ?", (character_id,)
        )
        if row is None:
            return {"not_found_message": f"Character {character_id} not found"}
        return dict(row)
```

## Version Compatibility Matrix

| Package | Version Constraint | Compatible With | Notes |
|---------|-------------------|-----------------|-------|
| mcp | >=1.26.0,<2.0.0 | Pydantic >=2.11.0,<3.0.0 | Pin <2.0.0 to avoid breaking changes from v2 pre-alpha |
| mcp | >=1.26.0,<2.0.0 | Python >=3.10 | We target 3.12+ but SDK supports 3.10+ |
| mcp | >=1.26.0,<2.0.0 | anyio >=4.5 | Transitive; do not pin separately |
| mcp | >=1.26.0,<2.0.0 | httpx >=0.27.1 | Transitive; do not pin separately |
| mcp | >=1.26.0,<2.0.0 | starlette >=0.27 | Transitive; only used if HTTP transport enabled |
| Typer | >=0.24.0 | Click 8.x | Typer wraps Click; version managed transitively |
| Typer | >=0.24.0 | Rich >=13.x | Included as dependency; no separate install needed |
| aiosqlite | >=0.22.0 | Python 3.9+ | Pure Python; no native extensions |
| Pydantic | >=2.11.0,<3.0.0 | pydantic-core 2.x | Binary extension; version coupled to Pydantic |
| pytest-asyncio | >=1.3.0 | pytest >=8.3.4 | Use `asyncio_mode = "auto"` in config |

## SQLite Configuration

Both CLI and MCP server should set these PRAGMAs on every connection:

```sql
PRAGMA journal_mode=WAL;      -- Write-Ahead Logging for concurrent reads
PRAGMA foreign_keys=ON;        -- Enforce foreign key constraints
PRAGMA busy_timeout=5000;      -- Wait 5s on lock contention instead of failing
PRAGMA cache_size=-64000;      -- 64MB cache (negative = KB)
```

WAL mode is important because the MCP server may handle concurrent tool calls, and WAL allows concurrent readers without blocking.

## Sources

- [MCP Python SDK PyPI](https://pypi.org/project/mcp/) -- v1.26.0 confirmed, dependencies verified from pyproject.toml (HIGH confidence)
- [MCP Python SDK GitHub](https://github.com/modelcontextprotocol/python-sdk) -- FastMCP API patterns, entry point structure, v2 status (HIGH confidence)
- [MCP SDK v1.26.0 pyproject.toml](https://raw.githubusercontent.com/modelcontextprotocol/python-sdk/refs/tags/v1.26.0/pyproject.toml) -- Exact dependency versions: pydantic>=2.11.0, anyio>=4.5, httpx>=0.27.1 (HIGH confidence)
- [uv Documentation](https://docs.astral.sh/uv/) -- v0.10.9, project structure, entry points (HIGH confidence)
- [uv PyPI](https://pypi.org/project/uv/) -- Current version v0.10.9 (HIGH confidence)
- [Typer PyPI](https://pypi.org/project/typer/) -- v0.24.1, Python >=3.10 (HIGH confidence)
- [aiosqlite PyPI](https://pypi.org/project/aiosqlite/) -- v0.22.1 (HIGH confidence)
- [Pydantic PyPI](https://pypi.org/project/pydantic/) -- v2.12.5 (HIGH confidence)
- [FastMCP 2.0 vs SDK Discussion](https://github.com/modelcontextprotocol/python-sdk/issues/1068) -- Divergence between standalone FastMCP and SDK built-in (HIGH confidence)
- [MCP Server Build Tutorial](https://dev.to/alexmercedcoder/building-a-basic-mcp-server-with-python-5ci7) -- Entry point patterns, tool registration (MEDIUM confidence)
- [pytest-asyncio PyPI](https://pypi.org/project/pytest-asyncio/) -- v1.3.0 (HIGH confidence)

---
*Stack research for: Python MCP Server + SQLite + UV CLI*
*Researched: 2026-03-07*
