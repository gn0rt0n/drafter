# Architecture Research

**Domain:** Python MCP server with SQLite backend and UV-managed CLI
**Researched:** 2026-03-07
**Confidence:** HIGH

## System Overview

```
┌──────────────────────────────────────────────────────────────────────────┐
│                     Claude Code (MCP Client)                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐     │
│  │ Agents   │  │ Skills   │  │ Commands │  │ Direct tool calls    │     │
│  │ (20)     │  │ (20)     │  │ (9)      │  │ from conversation    │     │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └─────────┬───────────┘     │
│       │              │             │                   │                 │
├───────┴──────────────┴─────────────┴───────────────────┴─────────────────┤
│                        MCP Protocol (stdio)                              │
├──────────────────────────────────────────────────────────────────────────┤
│                     MCP Server (novel-mcp)                               │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐    │
│  │                    FastMCP Server (server.py)                     │    │
│  │  - Tool registration          - Error contract enforcement       │    │
│  │  - Protocol compliance        - Lifespan / context management    │    │
│  └───────────────────────────┬──────────────────────────────────────┘    │
│                              │                                           │
│  ┌───────────────────────────┼──────────────────────────────────────┐    │
│  │              Tool Domain Modules (14 files)                       │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐    │    │
│  │  │characters│ │chapters  │ │ gate     │ │ world            │    │    │
│  │  │ (7 tools)│ │ (8 tools)│ │ (5 tools)│ │ (10 tools)       │    │    │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────────────┘    │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐    │    │
│  │  │relations │ │plot_arcs │ │timeline  │ │ canon            │    │    │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────────────┘    │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐    │    │
│  │  │knowledge │ │literary  │ │names     │ │ voice            │    │    │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────────────┘    │    │
│  │  ┌──────────┐ ┌──────────┐                                      │    │
│  │  │session   │ │publishing│                                      │    │
│  │  └──────────┘ └──────────┘                                      │    │
│  └───────────────────────────┬──────────────────────────────────────┘    │
│                              │                                           │
│  ┌───────────────────────────┼──────────────────────────────────────┐    │
│  │                     Shared Infrastructure                         │    │
│  │  ┌──────────────┐ ┌──────────────┐ ┌────────────────────────┐   │    │
│  │  │ models.py    │ │ db.py        │ │ validators/            │   │    │
│  │  │ (Pydantic)   │ │ (connection) │ │ (magic, timeline,      │   │    │
│  │  │              │ │              │ │  names, gate)           │   │    │
│  │  └──────────────┘ └──────┬───────┘ └────────────────────────┘   │    │
│  └──────────────────────────┼──────────────────────────────────────┘    │
├─────────────────────────────┼────────────────────────────────────────────┤
│                      SQLite Database                                     │
│  ┌──────────────────────────┴──────────────────────────────────────┐    │
│  │                   novel.sqlite (21 migrations)                    │    │
│  │  Core entities │ Character state │ World │ Plot │ Timeline       │    │
│  │  Pacing │ Knowledge │ Canon │ Literary │ Thematic │ Voice        │    │
│  │  Arc health │ Publishing │ Project │ Gate │ Research              │    │
│  └─────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────────┘

            ┌─────────────────────────────────────────┐
            │          novel CLI (separate)             │
            │  novel db migrate │ novel export          │
            │  novel import     │ novel query            │
            │  novel session    │ novel gate              │
            │  novel name       │                         │
            └────────────┬────────────────────────────────┘
                         │
                    Same SQLite DB
```

### Component Responsibilities

| Component | Responsibility | Implementation |
|-----------|----------------|----------------|
| **FastMCP Server** (`server.py`) | Entry point, tool registration, protocol compliance, lifespan management | `mcp.server.fastmcp.FastMCP` with lifespan context for DB connection |
| **Tool Domain Modules** (14 files in `tools/`) | Business logic for each domain's tools; decorated with `@mcp.tool()` | One Python file per domain, tools registered on a shared `mcp` instance |
| **Pydantic Models** (`models.py`) | Input/output type definitions for all tools; drives JSON schema generation | Pydantic `BaseModel` subclasses, one per tool response shape |
| **DB Connection** (`db.py`) | SQLite connection lifecycle, WAL mode, parameterized queries | `aiosqlite` async context manager, initialized in lifespan |
| **Validators** (`validators/`) | Cross-domain validation (magic compliance, travel realism, name similarity, gate checks) | Pure functions that take DB connection + input, return validation results |
| **CLI** (`novel/cli.py`) | User-facing terminal commands for DB operations, import/export, queries | Click or Typer CLI, shares DB connection logic with MCP server |
| **Migrations** (`.db/migrations/`) | Schema definition as numbered SQL files | 21 sequential `.sql` files, idempotent runner |

## Recommended Project Structure

```
/drafter/                              # This repo (novel-tools)
│
├── pyproject.toml                     # UV project config, entry points
├── uv.lock                           # Lock file
│
├── src/
│   └── drafter/                       # Main package
│       ├── __init__.py
│       │
│       ├── db/                        # Database layer (shared by MCP + CLI)
│       │   ├── __init__.py
│       │   ├── connection.py          # get_connection(), lifespan manager
│       │   ├── migrate.py             # Migration runner
│       │   └── queries.py             # Reusable parameterized query helpers
│       │
│       ├── models/                    # Pydantic models (shared by MCP + CLI)
│       │   ├── __init__.py
│       │   ├── characters.py          # Character, CharacterState, etc.
│       │   ├── chapters.py            # Chapter, Scene, ChapterPlan, etc.
│       │   ├── world.py               # Location, Faction, Culture, etc.
│       │   ├── plot.py                # PlotThread, Arc, ChekhovsGun, etc.
│       │   ├── timeline.py            # Event, PovPosition, TravelSegment
│       │   ├── canon.py               # CanonFact, Decision, ContinuityIssue
│       │   ├── knowledge.py           # ReaderState, DramaticIrony, Reveal
│       │   ├── literary.py            # Foreshadowing, Prophecy, Motif, etc.
│       │   ├── names.py               # NameEntry, NameSuggestion
│       │   ├── voice.py               # VoiceProfile, VoiceDrift
│       │   ├── gate.py                # GateStatus, ChecklistItem
│       │   ├── session.py             # SessionLog, AgentRun, ProjectMetrics
│       │   ├── publishing.py          # PublishingAsset, Submission
│       │   └── common.py              # Shared types (CanonStatus, ErrorResponse)
│       │
│       ├── server/                    # MCP server
│       │   ├── __init__.py
│       │   ├── app.py                 # FastMCP instance, lifespan, run()
│       │   └── tools/                 # One file per domain
│       │       ├── __init__.py        # Registers all domain modules
│       │       ├── characters.py
│       │       ├── relationships.py
│       │       ├── chapters.py
│       │       ├── plot_arcs.py
│       │       ├── timeline.py
│       │       ├── world.py
│       │       ├── canon.py
│       │       ├── knowledge.py
│       │       ├── literary.py
│       │       ├── names.py
│       │       ├── voice.py
│       │       ├── gate.py
│       │       ├── session.py
│       │       └── publishing.py
│       │
│       ├── validators/                # Cross-domain validation logic
│       │   ├── __init__.py
│       │   ├── magic.py               # Magic compliance checker
│       │   ├── timeline.py            # Travel realism validator
│       │   ├── names.py               # Name similarity / cultural fit
│       │   └── gate.py                # 33-item gate audit queries
│       │
│       └── cli/                       # CLI layer
│           ├── __init__.py
│           ├── main.py                # CLI entry point, group definitions
│           ├── db.py                  # novel db migrate, novel db backup
│           ├── export_.py             # novel export chapter, novel export all
│           ├── import_.py             # novel import world, characters, etc.
│           ├── query.py               # novel query pov-balance, arc-health
│           ├── session.py             # novel session start, novel session close
│           ├── gate.py                # novel gate check, novel gate status
│           └── name.py               # novel name check, novel name register
│
├── migrations/                        # SQL migration files
│   ├── 001_core_entities.sql
│   ├── 002_characters.sql
│   └── ... (21 total)
│
├── seeds/                             # Seed data for testing
│   ├── minimal.sql                    # Bare minimum for tool testing
│   └── full.sql                       # Complete test dataset
│
└── tests/
    ├── conftest.py                    # Fixtures: in-memory DB, seeded DB
    ├── test_db/
    ├── test_models/
    ├── test_tools/                    # One test file per domain
    └── test_cli/
```

### Structure Rationale

- **`src/drafter/` layout:** Using `src/` layout prevents accidental imports from the working directory. Standard for UV-managed packages.
- **`db/` shared between server and CLI:** Both the MCP server and the CLI need database access. Sharing the connection module prevents divergent connection logic. The MCP server uses it through the lifespan context; the CLI opens connections per-command.
- **`models/` as separate package:** Pydantic models are shared between MCP tools (for response types) and CLI (for structured output). Splitting by domain (not by "input" vs "output") keeps related types together.
- **`server/tools/` one file per domain:** Each of the 14 tool domains gets its own file. Tools are registered on the shared `mcp` instance via explicit imports in `tools/__init__.py`. This keeps any single file under 200 lines and makes domain ownership clear.
- **`validators/` separated from tools:** Validators contain pure business logic (e.g., "is this travel time realistic?"). They are used by both MCP tools and CLI commands. Keeping them separate from tool registration prevents circular imports.
- **`migrations/` at project root:** Migrations are not Python code. They are SQL files that get read and executed. Putting them at the root makes them easy to find and edit without navigating deep package paths.

## Architectural Patterns

### Pattern 1: Shared MCP Instance with Domain Registration

**What:** Create one `FastMCP` instance in `app.py`. Each tool domain file imports it and registers tools with `@mcp.tool()`. An `__init__.py` in `tools/` triggers all imports.

**When to use:** Always. This is the standard pattern for the MCP Python SDK.

**Trade-offs:** Explicit imports mean you must remember to add new domain files to `__init__.py`. But this is better than magic auto-discovery, which hides registration order and makes debugging harder.

**Example:**

```python
# src/drafter/server/app.py
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from dataclasses import dataclass
import aiosqlite
import os

from mcp.server.fastmcp import FastMCP


@dataclass
class AppContext:
    db: aiosqlite.Connection


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    db_path = os.environ.get("NOVEL_DB_PATH", ".db/novel.sqlite")
    db = await aiosqlite.connect(db_path)
    await db.execute("PRAGMA journal_mode=WAL")
    await db.execute("PRAGMA foreign_keys=ON")
    db.row_factory = aiosqlite.Row
    try:
        yield AppContext(db=db)
    finally:
        await db.close()


mcp = FastMCP(
    name="novel",
    json_response=True,
    lifespan=app_lifespan,
)

# Import all tool domains to trigger registration
from drafter.server import tools  # noqa: E402, F401


def main():
    mcp.run(transport="stdio")
```

```python
# src/drafter/server/tools/__init__.py
"""Import all tool domain modules to register their tools on the mcp instance."""
from drafter.server.tools import characters      # noqa: F401
from drafter.server.tools import relationships   # noqa: F401
from drafter.server.tools import chapters        # noqa: F401
from drafter.server.tools import plot_arcs       # noqa: F401
from drafter.server.tools import timeline        # noqa: F401
from drafter.server.tools import world           # noqa: F401
from drafter.server.tools import canon           # noqa: F401
from drafter.server.tools import knowledge       # noqa: F401
from drafter.server.tools import literary        # noqa: F401
from drafter.server.tools import names           # noqa: F401
from drafter.server.tools import voice           # noqa: F401
from drafter.server.tools import gate            # noqa: F401
from drafter.server.tools import session         # noqa: F401
from drafter.server.tools import publishing      # noqa: F401
```

```python
# src/drafter/server/tools/characters.py
from mcp.server.fastmcp import Context

from drafter.server.app import mcp, AppContext
from drafter.models.characters import Character, CharacterState
from drafter.models.common import NotFoundResponse


@mcp.tool()
async def get_character(
    character_id: int,
    ctx: Context,
) -> Character | NotFoundResponse:
    """Get a character by ID with full details."""
    db = ctx.request_context.lifespan_context.db
    row = await db.execute_fetchone(
        "SELECT * FROM characters WHERE id = ?", (character_id,)
    )
    if row is None:
        return NotFoundResponse(not_found_message=f"Character {character_id} not found")
    return Character.model_validate(dict(row))
```

### Pattern 2: Error Contract via Union Return Types

**What:** Every tool returns either a success type or an error type. The PRD defines three error shapes: `null` for not-found (wrapped as `NotFoundResponse`), `is_valid: false` for validation failures, and `requires_action` for gate violations. Use Pydantic discriminated unions.

**When to use:** Every tool. No exceptions.

**Trade-offs:** Slightly more verbose than raising exceptions. But MCP tools should never raise -- they should return structured error data that Claude Code can reason about.

**Example:**

```python
# src/drafter/models/common.py
from pydantic import BaseModel
from typing import Literal
from enum import Enum


class CanonStatus(str, Enum):
    draft = "draft"
    approved = "approved"
    provisional = "provisional"
    deprecated = "deprecated"


class NotFoundResponse(BaseModel):
    """Returned when a requested record does not exist."""
    not_found_message: str


class ValidationFailure(BaseModel):
    """Returned when input fails validation."""
    is_valid: Literal[False] = False
    errors: list[str]


class GateViolation(BaseModel):
    """Returned when an operation requires gate certification."""
    requires_action: str
    gate_status: str
    blocking_count: int
```

```python
# In a tool that enforces the gate
@mcp.tool()
async def upsert_scene_prose(
    scene_id: int,
    prose: str,
    ctx: Context,
) -> SceneProseResult | GateViolation | NotFoundResponse:
    """Write or update prose for a scene. Requires gate certification."""
    db = ctx.request_context.lifespan_context.db

    # Gate check first
    gate_row = await db.execute_fetchone(
        "SELECT status, blocking_count FROM architecture_gate ORDER BY id DESC LIMIT 1"
    )
    if gate_row is None or gate_row["status"] != "passed":
        return GateViolation(
            requires_action="Architecture gate must be certified before writing prose",
            gate_status=gate_row["status"] if gate_row else "unchecked",
            blocking_count=gate_row["blocking_count"] if gate_row else 33,
        )

    # ... proceed with upsert
```

### Pattern 3: Gate as a Cross-Cutting Concern

**What:** The gate system (33 SQL-verifiable checklist items) blocks prose-phase tools. Rather than checking the gate inline in every prose tool, use a decorator or shared helper that tools call before executing.

**When to use:** Any tool that writes or modifies prose, scene content, or chapter drafts. Approximately 10-15 tools across characters (arc state changes during prose), chapters (draft status), and scene-level operations.

**Trade-offs:** A decorator feels clean but hides the gate check from the tool's return type. A shared helper function called at the top of the tool body is more explicit and keeps the GateViolation visible in the return type annotation.

**Recommendation:** Use a shared helper, not a decorator. Explicitness matters more than DRY here.

**Example:**

```python
# src/drafter/validators/gate.py
import aiosqlite
from drafter.models.common import GateViolation


async def check_gate(db: aiosqlite.Connection) -> GateViolation | None:
    """Returns a GateViolation if gate is not passed, None if clear."""
    row = await db.execute_fetchone(
        "SELECT status, blocking_count FROM architecture_gate "
        "ORDER BY certified_at DESC LIMIT 1"
    )
    if row is None or row["status"] != "passed":
        return GateViolation(
            requires_action="Architecture gate must be certified before prose operations",
            gate_status=row["status"] if row else "unchecked",
            blocking_count=row["blocking_count"] if row else 33,
        )
    return None
```

```python
# In any prose-phase tool:
@mcp.tool()
async def write_scene_draft(scene_id: int, prose: str, ctx: Context):
    """Write a scene draft. Requires architecture gate certification."""
    db = ctx.request_context.lifespan_context.db

    violation = await check_gate(db)
    if violation:
        return violation

    # ... write the prose
```

### Pattern 4: DB Query Helpers for Consistent Patterns

**What:** The 80 tools will execute hundreds of SQL queries. Rather than writing raw SQL in every tool, create a thin query layer in `db/queries.py` that provides typed helpers for common operations: get-by-id, list-with-filter, upsert, log-event.

**When to use:** For repeated query shapes. Not for one-off complex queries (those stay in the tool).

**Trade-offs:** Adding a query layer adds indirection. But the alternative is 80 files each with inline SQL, making schema changes a nightmare.

**Example:**

```python
# src/drafter/db/queries.py
import aiosqlite
from typing import Any


async def get_by_id(
    db: aiosqlite.Connection,
    table: str,
    record_id: int,
) -> dict[str, Any] | None:
    """Fetch a single record by ID. Returns dict or None."""
    row = await db.execute_fetchone(
        f"SELECT * FROM {table} WHERE id = ?", (record_id,)
    )
    return dict(row) if row else None


async def list_records(
    db: aiosqlite.Connection,
    table: str,
    filters: dict[str, Any] | None = None,
    order_by: str = "id",
    limit: int = 100,
) -> list[dict[str, Any]]:
    """List records with optional filters."""
    query = f"SELECT * FROM {table}"
    params: list[Any] = []
    if filters:
        clauses = [f"{k} = ?" for k in filters]
        query += " WHERE " + " AND ".join(clauses)
        params.extend(filters.values())
    query += f" ORDER BY {order_by} LIMIT ?"
    params.append(limit)
    cursor = await db.execute(query, params)
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]


async def upsert(
    db: aiosqlite.Connection,
    table: str,
    data: dict[str, Any],
    conflict_column: str = "id",
) -> int:
    """Insert or update a record. Returns the row ID."""
    columns = list(data.keys())
    placeholders = ", ".join(["?"] * len(columns))
    updates = ", ".join([f"{c} = excluded.{c}" for c in columns if c != conflict_column])

    query = (
        f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders}) "
        f"ON CONFLICT({conflict_column}) DO UPDATE SET {updates}, "
        f"updated_at = CURRENT_TIMESTAMP"
    )
    cursor = await db.execute(query, list(data.values()))
    await db.commit()
    return cursor.lastrowid
```

**Security note:** The `table` and column names in these helpers come from application code, not user input. They are safe from injection. Parameter values always use `?` placeholders.

## Data Flow

### MCP Tool Call Flow

```
Claude Code (or agent/skill)
    │
    │  MCP tool call: get_character(character_id=42)
    │  (JSON-RPC over stdio)
    ▼
FastMCP Server (app.py)
    │
    │  Routes to registered tool function
    │  Validates input against Pydantic model (automatic)
    ▼
Tool Function (tools/characters.py)
    │
    │  Accesses DB via ctx.request_context.lifespan_context.db
    │  Calls query helpers or writes inline SQL
    ▼
DB Connection (aiosqlite)
    │
    │  Executes parameterized SQL against novel.sqlite
    │  Returns Row objects
    ▼
Tool Function
    │
    │  Converts Row → Pydantic model (model_validate)
    │  Returns model instance (or NotFoundResponse)
    ▼
FastMCP Server
    │
    │  Serializes Pydantic model to JSON
    │  Wraps in MCP protocol response
    ▼
Claude Code
    │
    │  Receives structured JSON
    │  Agent/skill reasons about result
```

### Gate-Enforced Tool Call Flow

```
Claude Code: write_scene_draft(scene_id=7, prose="...")
    ▼
Tool Function (tools/chapters.py)
    │
    │  FIRST: await check_gate(db)
    │
    ├── Gate NOT passed ──────────────────────────┐
    │                                              ▼
    │                              Return GateViolation {
    │                                requires_action: "...",
    │                                gate_status: "incomplete",
    │                                blocking_count: 12
    │                              }
    │                                              ▼
    │                              Claude Code sees requires_action,
    │                              agent/skill refuses to proceed
    │
    ├── Gate passed ─────────────────────────────┐
    │                                             ▼
    │                              Execute the write operation
    │                              Return SceneProseResult
    ▼
Claude Code: receives success or gate violation
```

### CLI Command Flow

```
Terminal: novel query pov-balance
    ▼
CLI Entry Point (cli/main.py)
    │
    │  Click/Typer routes to subcommand
    ▼
CLI Handler (cli/query.py)
    │
    │  Opens DB connection (sync wrapper around aiosqlite,
    │  or use standard sqlite3 since CLI is synchronous)
    │  Executes query
    │  Formats output for terminal
    ▼
Terminal: prints formatted table
```

### Key Data Flows

1. **Tool read path:** MCP call -> tool function -> `db.execute_fetchone/fetchall` -> Row -> Pydantic model -> JSON response. Every read follows this exact chain. No exceptions.

2. **Tool write path:** MCP call -> tool function -> validate input (Pydantic) -> optional gate check -> `db.execute` + `db.commit` -> return success model. Writes always commit immediately (no deferred transactions across tool calls).

3. **Migration path:** `novel db migrate` -> reads `migrations/` directory -> sorts by number prefix -> executes each `.sql` file in a transaction -> records applied migrations in a tracking table.

4. **Import path:** `novel import [domain]` -> reads markdown files from the novel content repo -> parses structure -> maps fields to table columns -> inserts with `canon_status = 'draft'` -> logs unmapped fields to `open_questions`.

5. **Export path:** `novel export [target]` -> queries DB for domain data -> renders Jinja2 (or f-string) templates -> writes markdown files to novel content repo directories.

## Build Order and Dependencies

The build order is strictly layered. Each layer depends only on layers below it.

```
Layer 0: migrations/           SQL files (no Python dependencies)
    ▼
Layer 1: db/                   Connection, migration runner, query helpers
    ▼
Layer 2: models/               Pydantic models (depends on nothing except pydantic)
    ▼
Layer 3: validators/           Business logic (depends on db/ + models/)
    ▼
Layer 4: server/tools/         MCP tool functions (depends on db/ + models/ + validators/)
    ▼
Layer 5: server/app.py         FastMCP instance, lifespan, entry point
    ▼
Layer 6: cli/                  CLI commands (depends on db/ + models/, parallel to server/)
```

### Concrete Build Sequence

1. **Migrations first** (Layer 0). Write all 21 SQL files. Test them with `sqlite3` shell. These are pure SQL -- no Python involved.

2. **DB connection layer** (Layer 1). Write `connection.py` (aiosqlite connect with WAL + FK pragmas), `migrate.py` (reads and executes SQL files), and `queries.py` (get_by_id, list_records, upsert helpers).

3. **Pydantic models** (Layer 2). Define all input/output models. Start with `common.py` (CanonStatus, NotFoundResponse, ValidationFailure, GateViolation), then domain models. These can be written in any order since they do not depend on each other.

4. **Gate validator** (Layer 3). Write the gate checker first because it is a dependency for prose-phase tools. Then write magic compliance, travel realism, and name similarity validators.

5. **Core tool domains** (Layer 4). Build in dependency order:
   - `gate.py` -- needed to verify gate system works
   - `characters.py` -- most tools depend on characters existing
   - `chapters.py` -- needed for scene-level work
   - `world.py` -- locations, factions, cultures
   - `relationships.py` -- depends on characters
   - `plot_arcs.py` -- depends on characters + chapters
   - `timeline.py` -- depends on characters + chapters + locations
   - `canon.py` -- depends on everything above
   - Remaining domains: `knowledge`, `literary`, `names`, `voice`, `session`, `publishing`

6. **Server entry point** (Layer 5). Wire up `app.py` with lifespan, import all tools, test with Claude Code.

7. **CLI** (Layer 6). Build in parallel with or after MCP tools. The CLI uses the same `db/` and `models/` packages but does not depend on the server.

### Dependency Graph for Tool Domains

```
gate (standalone -- queries gate tables only)
    │
characters ◄────────────── relationships
    │                           │
    ├── chapters ◄──── plot_arcs
    │       │               │
    │       └── timeline ◄──┘
    │
    ├── world (standalone -- queries world tables)
    │
    ├── canon (cross-cutting -- references many tables)
    │
    ├── knowledge (depends on characters + chapters)
    │
    ├── literary (depends on chapters)
    │
    ├── voice (depends on characters)
    │
    ├── names (standalone -- queries name_registry)
    │
    ├── session (standalone -- queries session/project tables)
    │
    └── publishing (standalone -- queries publishing tables)
```

## Organizing 14 Tool Domains Without Import Chaos

The key architectural decision: **tools register on a single shared `mcp` instance via module-level side effects, triggered by explicit imports.**

### The Pattern

1. `app.py` creates the `mcp = FastMCP(...)` instance.
2. Each domain file (`tools/characters.py`, etc.) imports `mcp` from `app.py` and uses `@mcp.tool()` decorators at module level.
3. `tools/__init__.py` imports all 14 domain modules, triggering tool registration.
4. `app.py` imports `tools` (the package) after creating `mcp`, which triggers the chain.

### Import Order Matters

The `mcp` instance MUST be created before any domain module is imported. This means `app.py` must define `mcp` at module level and then import `tools` below the definition:

```python
# app.py -- ORDER MATTERS
mcp = FastMCP(...)  # FIRST: create the instance

# SECOND: import tools (which will import mcp from this module)
from drafter.server import tools  # noqa
```

### Why NOT Use FastMCP's `mount()` for This

FastMCP's `mount()` and `import_server()` are designed for composing separate servers. Using them for 14 domains within a single server would:
- Add unnecessary namespace prefixes to tool names (`characters_get_character` instead of `get_character`)
- Create 14 separate `FastMCP` instances with no shared lifespan context
- Complicate DB connection sharing

The simpler pattern (one `mcp` instance, 14 files importing it) is correct here. `mount()` is for combining independently deployable servers, not for organizing code within one server.

## The Gate/Certification System Architecture

### Data Model

```sql
-- From migration 020_gate.sql
CREATE TABLE architecture_gate (
    id          INTEGER PRIMARY KEY,
    status      TEXT CHECK(status IN ('unchecked', 'in_progress', 'failed', 'passed')),
    certified_by TEXT,
    certified_at TIMESTAMP,
    blocking_count INTEGER,
    notes       TEXT,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE gate_checklist_items (
    id              INTEGER PRIMARY KEY,
    gate_id         INTEGER REFERENCES architecture_gate(id),
    domain          TEXT,       -- 'world', 'characters', 'structure', etc.
    item_number     INTEGER,    -- 1-33
    description     TEXT,
    evidence_query  TEXT,       -- The SQL query that checks this item
    pass_condition  TEXT,       -- e.g., "missing_count = 0"
    status          TEXT CHECK(status IN ('unchecked', 'passed', 'failed')),
    missing_count   INTEGER,
    missing_details TEXT,       -- JSON array of what's missing
    checked_at      TIMESTAMP,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP
);
```

### How the Gate System Works

```
get_gate_status()
    │
    │  Reads latest architecture_gate record
    │  Returns: { status, blocking_count, certified_at }
    │  Used by: prose-phase skills to decide whether to proceed

run_gate_audit()
    │
    │  For each of 33 checklist items:
    │    1. Execute the evidence_query against the DB
    │    2. Compare result to pass_condition
    │    3. If fails: record missing_count + missing_details
    │    4. Update gate_checklist_items row
    │  After all 33:
    │    Update architecture_gate.blocking_count
    │    Set status = 'passed' if blocking_count == 0, else 'failed'
    │  Returns: full gap report with per-domain breakdown

certify_gate()
    │
    │  Pre-condition: blocking_count == 0
    │  Action: Sets status = 'passed', records certified_by + certified_at
    │  Post-condition: prose-phase tools now return success instead of GateViolation
```

### Gate Tool Interactions

| Tool | Gate Behavior |
|------|--------------|
| `get_gate_status` | Read-only. Returns current status. |
| `run_gate_audit` | Re-evaluates all 33 items. Updates status. |
| `get_gate_checklist` | Returns all 33 items with current pass/fail status. |
| `update_checklist_item` | Manually override an item (for edge cases). |
| `certify_gate` | Final certification. Requires 0 blocking items. |
| Any prose-phase tool | Calls `check_gate()` first. Returns `GateViolation` if not passed. |

### Which Tools Are Gate-Blocked

Not all tools are gate-blocked. Only tools that write prose or advance content into the "drafting" phase:

- Scene prose writing/updating
- Chapter status changes to "drafted" or beyond
- Character arc state changes during prose (actual_arc_end_state)

Architecture-phase tools (upsert_character, upsert_chapter, upsert_scene with status="planned") are NOT gate-blocked. They are how you complete the gate requirements.

## Anti-Patterns

### Anti-Pattern 1: One Giant server.py

**What people do:** Put all 80 tool functions in a single `server.py` file.
**Why it is wrong:** At ~20 lines per tool (docstring, type annotations, SQL, response construction), that is 1600+ lines. Impossible to navigate, review, or maintain.
**Do this instead:** One file per domain in `tools/`. Each file stays under 200 lines. Clear ownership boundaries.

### Anti-Pattern 2: Raw SQL Strings Everywhere

**What people do:** Write full SQL queries inline in every tool function, duplicating patterns like "SELECT * FROM X WHERE id = ?".
**Why it is wrong:** Schema changes require hunting through 14 files. Easy to miss parameterization. Inconsistent column handling.
**Do this instead:** Use query helpers in `db/queries.py` for common patterns. Reserve inline SQL for complex domain-specific queries.

### Anti-Pattern 3: Raising Exceptions from Tools

**What people do:** `raise ValueError("Character not found")` inside an MCP tool.
**Why it is wrong:** MCP tools should return structured data, not crash. An exception becomes an opaque error message in Claude Code. A structured `NotFoundResponse` lets the agent reason about what happened and take corrective action.
**Do this instead:** Return `NotFoundResponse`, `ValidationFailure`, or `GateViolation` models. Never raise from a tool function.

### Anti-Pattern 4: Separate DB Connections per Tool Call

**What people do:** Open a new `aiosqlite.connect()` inside every tool function.
**Why it is wrong:** Connection setup overhead on every call. WAL mode and FK pragmas must be re-set each time. No connection reuse.
**Do this instead:** Use the lifespan pattern. One connection opened at server start, shared via context, closed at shutdown.

### Anti-Pattern 5: Using mount() for Internal Domain Organization

**What people do:** Create 14 separate `FastMCP()` instances and mount them all on a parent server for code organization.
**Why it is wrong:** Adds namespace prefixes to all tool names. Breaks shared lifespan context. Adds unnecessary protocol overhead.
**Do this instead:** One `FastMCP` instance. Fourteen tool files importing it. Explicit registration via `__init__.py`.

### Anti-Pattern 6: Sync SQLite in an Async MCP Server

**What people do:** Use the stdlib `sqlite3` module directly in async tool functions.
**Why it is wrong:** Blocks the event loop. The MCP server handles one tool call at a time over stdio, so it may not cause visible issues initially -- but it prevents future concurrent operation and violates async correctness.
**Do this instead:** Use `aiosqlite` for all DB operations in the MCP server. The CLI can use sync `sqlite3` since it runs one command at a time.

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| Claude Code | MCP over stdio | `.mcp.json` in plugin repo specifies `uv run` command |
| Novel content repo | File system (import/export) | CLI reads/writes markdown; path configured via env var |
| SQLite DB | `aiosqlite` (server), `sqlite3` (CLI) | Path from `NOVEL_DB_PATH` env var |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| MCP server <-> DB | `aiosqlite` via shared connection in lifespan context | All tools share one connection; WAL mode enables concurrent reads |
| CLI <-> DB | `sqlite3` direct (sync) or `aiosqlite` with `asyncio.run()` | CLI opens/closes per command |
| Tool <-> Validator | Direct function call | Validators are pure functions taking DB + input |
| Tool <-> Pydantic model | `Model.model_validate(dict(row))` | Row-to-model conversion at tool boundary |
| MCP server <-> CLI | No direct communication | Share DB package and models, but run independently |

### pyproject.toml Entry Points

```toml
[project.scripts]
novel = "drafter.cli.main:main"
novel-mcp = "drafter.server.app:main"
```

This gives two entry points:
- `novel` -- the CLI, invoked as `uv run novel db migrate`, etc.
- `novel-mcp` -- the MCP server, invoked by Claude Code via `.mcp.json` as `uv run --project /path/to/drafter novel-mcp`

## Scaling Considerations

| Concern | Current Scale (1 user, 1 novel) | Future Scale (multiple novels) |
|---------|---|----|
| DB size | ~5MB SQLite file. No issues. | Still fine for SQLite up to ~1GB. Multiple novels = multiple DB files, one per `NOVEL_DB_PATH`. |
| Tool count | ~80 tools. Claude Code handles this fine. | If tool count grows beyond ~120, consider splitting into multiple MCP servers (one for architecture, one for prose). |
| Query performance | All queries hit indexed columns. Sub-millisecond. | Add indexes on frequently filtered columns (`chapter_id`, `character_id`, `canon_status`). |
| Connection concurrency | MCP stdio is single-threaded. One query at a time. | WAL mode already enables concurrent reads. If multi-client needed, switch to streamable-http transport. |

### Scaling Priorities

1. **First bottleneck:** Tool discoverability. With 80 tools, Claude Code must parse all tool descriptions. Keep descriptions concise (one sentence) and names self-explanatory.
2. **Second bottleneck:** Import performance. Parsing 55 chapters of markdown during `novel import all`. Use bulk inserts with transactions, not one-row-at-a-time commits.

## Sources

- [MCP Python SDK (GitHub)](https://github.com/modelcontextprotocol/python-sdk) -- Official SDK, includes FastMCP -- HIGH confidence
- [MCP Python SDK (PyPI)](https://pypi.org/project/mcp/) -- v1.26.0, confirms FastMCP built-in -- HIGH confidence
- [Build an MCP Server (official docs)](https://modelcontextprotocol.io/docs/develop/build-server) -- Official tutorial -- HIGH confidence
- [FastMCP Server Composition](https://gofastmcp.com/servers/composition) -- mount() vs import_server() patterns -- HIGH confidence
- [FastMCP Discussion #1312](https://github.com/jlowin/fastmcp/discussions/1312) -- Multi-file tool organization -- MEDIUM confidence (community discussion, no official answer)
- [aiosqlite (GitHub)](https://github.com/omnilib/aiosqlite) -- Async SQLite bridge -- HIGH confidence
- [UV Project Configuration](https://docs.astral.sh/uv/concepts/projects/config/) -- pyproject.toml entry points -- HIGH confidence
- [Python MCP Server (Real Python)](https://realpython.com/python-mcp/) -- Project structure patterns -- MEDIUM confidence
- [DigitalOcean MCP Guide](https://www.digitalocean.com/community/tutorials/mcp-server-python) -- Best practices -- MEDIUM confidence

---
*Architecture research for: Drafter (Python MCP server + SQLite + UV CLI)*
*Researched: 2026-03-07*
