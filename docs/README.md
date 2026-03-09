# Drafter — System Architecture Overview

Drafter is a Python MCP server combined with a SQLite narrative database and a UV-managed CLI,
built to support AI-assisted novel writing at scale. This document is the entry point for
a system-admin-level reader who needs to understand implementation — how the three layers fit
together, how to start each layer, and where to find detailed reference documentation.

---

## Three-Layer Architecture

The system is organized into three distinct layers. Each layer has a single responsibility
and communicates only through the SQLite database.

```
Claude Code (AI agent)
    │
    │  MCP protocol (stdio)
    ▼
Layer 2: MCP Server  (novel-mcp)
    │   121 tools across 19 modules
    │   FastMCP on mcp>=1.26.0
    │
    │  aiosqlite (async)
    ▼
Layer 1: SQLite Database  (novel.db)
    │   22 migrations, ~71 tables
    │   WAL mode, foreign_keys=ON
    ▲
    │  sqlite3 (sync)
Layer 3: CLI  (novel command)
    ▲
    │
Human operator
```

### Layer 1: SQLite Database

The persistence layer. A single SQLite file managed through 22 sequential migration scripts
in `src/novel/migrations/`. All migrations run at startup via `novel db migrate` or are
applied automatically on `uv run novel-mcp`.

Key characteristics:
- WAL mode enabled — required for async MCP + aiosqlite concurrent access
- `PRAGMA foreign_keys=ON` set on every connection — SQLite disables FK enforcement by default
- Migrations are numbered 001–022 and applied in order; the `schema_migrations` table
  tracks which have been applied
- The 22nd migration (022) adds seven-point story structure tables

### Layer 2: MCP Server

The AI-callable API layer. Implemented as a FastMCP server with 121 tools organized into
19 domain modules under `src/novel/tools/`. Each module exposes a `register(mcp: FastMCP)`
function that decorates local async functions with `@mcp.tool()`.

Key characteristics:
- Runs on stdio transport — consumed by Claude Code via MCP configuration
- No `print()` anywhere in the server tree — stdout is the MCP wire protocol
- All logging goes to stderr via the Python `logging` module
- 18 active tool modules plus gate module; tools cover characters, relationships, chapters,
  scenes, world-building, magic, plot, arcs, gate management, sessions, timeline, canon,
  knowledge, foreshadowing, names, voice, publishing, and story structure

### Layer 3: CLI

The human-operated management layer. A Typer application (`src/novel/cli.py`) with six
subcommand groups, all using synchronous `sqlite3` (not aiosqlite). The CLI is intentionally
isolated from MCP tool code — the two layers share only the database file.

Subcommand groups:
- `novel db` — database management: `migrate`, `seed`, `reset`, `status`
- `novel gate` — architecture gate: `check`, `status`, `certify`
- `novel export` — chapter markdown export: `regenerate`
- `novel name` — name registry: `check`, `register`, `suggest`
- `novel session` — session management: `start`, `close`
- `novel query` — narrative queries: `pov-balance`, `arc-health`, `thread-gaps`

---

## Entry Points

Both entry points are defined in `pyproject.toml` under `[project.scripts]` and installed
by `uv sync`.

### MCP Server

```
uv run novel-mcp
```

Starts the MCP server on stdio transport. This is the process Claude Code connects to.
Configure in `.claude/settings.json` or Claude Desktop's MCP config. The server runs
continuously; all 121 tools are available immediately after startup.

### CLI

```
uv run novel [subcommand]
```

Human-operated database management and queries. Does not start a long-running process.
Each invocation opens a connection, executes, and exits.

---

## Gate System

The architecture gate is a 36-item checklist that verifies the narrative database has
sufficient content before the prose-writing phase begins. Most MCP write tools that touch
story content are gate-enforced — they will return a `requires_action` response instead of
executing if the gate is not certified.

Gate certification flow:
1. Populate the database using gate-free tools (characters, world-building, structure, names)
2. Run `novel gate check` to see which checklist items pass or fail
3. Resolve failing items using the appropriate tools
4. Run `novel gate certify` to mark the gate as certified
5. All gated tools are now unlocked

The gate enforces a minimum viable narrative foundation: named characters with goals,
defined world-building, chapter structure, arc assignments, plot threads, and story beats.
Once certified, the gate state is stored in `gate_certifications` and `gate_checklist_log`.
The `check_gate()` helper in `src/novel/mcp/gate.py` is called by gated tools at the
top of their execution.

---

## Error Contract

Every MCP tool returns one of four outcomes. No tool ever raises an unhandled exception.

| Outcome | When | Response shape |
|---------|------|---------------|
| Success | Normal execution | Domain-specific return type (Pydantic model or primitive) |
| Not found | Requested record does not exist | `null` with a `not_found_message` string field |
| Validation failure | Input fails business-logic checks | `is_valid: false` with an `errors: list[str]` field |
| Gate violation | Gated tool called before gate certification | `requires_action: true` with a `message` field |

The `not_found_message` shape means callers can distinguish "tool succeeded, record absent"
from "tool failed" without exception handling. Validation failures are returned as structured
data so callers can inspect which fields were invalid. Gate violations are informational —
the agent can report them to the user rather than treating them as errors.

---

## Documentation Map

| Document | What it covers |
|----------|---------------|
| [`docs/schema.md`](schema.md) | Full schema reference: all 22 migrations, ~71 tables organized by domain, field annotations, FK relationships, lifecycle notes (which tools populate each table), gate flags, and Mermaid ER diagrams per domain |
| [`docs/mcp-tools.md`](mcp-tools.md) | Full MCP tool reference: all 121 tools across 19 domains, with purpose, parameters, return types, invocation reason, gate status, and tables touched per tool |
| [`project-research/database-schema.md`](../project-research/database-schema.md) | Historical pre-build design document — kept as design history. Field names may have drifted from actual implementation; see `docs/schema.md` for implementation-accurate field names |

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.12+ |
| Data validation | Pydantic v2 (>=2.11) |
| MCP framework | FastMCP (`mcp>=1.26.0,<2.0.0`) — bundled `mcp.server.fastmcp` |
| Async DB driver | aiosqlite (MCP server layer) |
| Sync DB driver | sqlite3 stdlib (CLI layer) |
| CLI framework | Typer 0.24.x |
| Build backend | Hatchling (required for `[project.scripts]` entry points) |
| Package manager | uv 0.10.x |

> **Note on MCP SDK:** Uses the bundled `mcp.server.fastmcp` from the `mcp` package — NOT
> the standalone `fastmcp` PyPI package, which has diverged from the bundled version.
