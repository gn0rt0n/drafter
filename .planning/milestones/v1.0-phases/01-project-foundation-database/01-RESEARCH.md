# Phase 1: Project Foundation & Database - Research

**Researched:** 2026-03-07
**Domain:** Python packaging (hatchling/uv), Typer CLI, SQLite (sync + async), FastMCP minimal setup, migration runner design
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Schema source**
- Use `project-research/database-schema.md` as the authoritative base for all 21 migration files
- Implement exactly as documented; where modifications are needed for FK dependency ordering or missing tracking tables, apply them
- Add `schema_migrations` tracking table (migration 001) — not in the schema doc but required by the migration runner

**Migration file naming**
- Format: `NNN_descriptive_name.sql` (zero-padded 3 digits + snake_case description)
- Example: `001_schema_tracking.sql`, `002_core_books_eras.sql`, `007_chapters.sql`
- Migration files bundled as package data inside the `novel` package (not shipped separately)

**Migration behavior**
- `novel db migrate` = **incremental**: reads `schema_migrations` table, applies only unapplied migrations in order
- `novel db reset` = **clean rebuild**: drops all tables, then runs full migrate from scratch
- `schema_migrations` table: `(version INT PRIMARY KEY, name TEXT NOT NULL, applied_at TEXT NOT NULL)`

**Migration grouping (21 migrations)**
- `001` — schema_migrations tracking table
- `002` — eras, books
- `003` — acts (FK to books; start/end chapter FKs nullable)
- `004` — cultures
- `005` — factions (leader_character_id nullable)
- `006` — locations (FK to cultures, factions)
- `007` — characters (FK to factions, cultures, eras)
- `008` — chapters (FK to books, acts, characters)
- `009` — scenes (FK to chapters, locations)
- `010` — artifacts (FK to characters, locations, eras)
- `011` — magic_system_elements, supernatural_elements
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

**Database path**
- `NOVEL_DB_PATH` env var is canonical — both CLI and MCP server read it
- Development fallback: `./novel.db` in current directory when `NOVEL_DB_PATH` is not set
- Database file itself is gitignored; migration SQL files are tracked

**Package structure** (locked)
```
src/
  novel/
    __init__.py
    cli.py
    db/
      __init__.py
      connection.py
      migrations.py
      seed.py
    mcp/
      __init__.py
      server.py
      db.py
    models/
    tools/
```

Entry points:
- `novel` → `novel.cli:app`
- `novel-mcp` → `novel.mcp.server:run`

**Connection factory design**
- Sync: context manager, `sqlite3.Connection`, WAL + `PRAGMA foreign_keys=ON` on every open
- Async: async context manager, `aiosqlite.Connection`, same pragmas applied immediately after open
- No global pool — fresh connection per context manager call

**CLI behavior**
- `novel db migrate` — incremental, prints each applied migration name
- `novel db seed [profile]` — stub in Phase 1 (returns "no seed profiles defined")
- `novel db reset` — confirmation prompt then drop + migrate
- `novel db status` — migration version, table count, row counts for books/chapters/characters/scenes

### Claude's Discretion

- Exact SQL for each migration (column types, constraints, indexes)
- Whether to add indexes in Phase 1 vs. later
- Error message text for CLI commands
- Internal migration file discovery implementation (glob vs. hardcoded list vs. importlib.resources)

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| SETUP-01 | `pyproject.toml` configures `novel` and `novel-mcp` entry points, both invocable via `uv run` | Hatchling src layout pattern + `[project.scripts]` entry point format verified |
| SETUP-02 | All 21 SQL migration files exist and define the complete narrative schema | 21 migration groups mapped to all tables from `database-schema.md`; FK dependency order confirmed |
| SETUP-03 | `novel db migrate` runs all migrations in order with clean-rebuild support, under 5 seconds | Incremental migration runner pattern with `schema_migrations` tracking table documented |
| SETUP-04 | Database connection factory enables WAL mode and `PRAGMA foreign_keys=ON` on every connection | Both sync (`sqlite3`) and async (`aiosqlite`) PRAGMA patterns documented with code examples |
| CLDB-01 | `novel db migrate` builds clean database from 21 migrations in under 5 seconds | Migration runner design verified; SQLite is fast enough for 21 migrations |
| CLDB-02 | `novel db seed [profile]` loads a named seed profile | Stub only in Phase 1; Typer optional argument pattern documented |
| CLDB-03 | `novel db reset` drops and rebuilds the database | Drop-all-tables pattern + confirmation prompt in Typer documented |
| CLDB-04 | `novel db status` displays migration version, table count, and row counts | sqlite_master query for table count + per-table SELECT COUNT(*) pattern |
</phase_requirements>

---

## Summary

Phase 1 is a pure infrastructure phase: Python packaging, SQLite schema deployment, and CLI scaffolding. All technical decisions are locked in CONTEXT.md; research confirms they are sound and documents the exact implementation patterns needed.

The three interlocking challenges are: (1) correctly configuring `pyproject.toml` so hatchling bundles the SQL migration files inside the `novel` package and exposes two `uv run`-able entry points; (2) writing the 21 migration SQL files in strict FK-dependency order, using SQLite-compatible DDL (INTEGER PRIMARY KEY instead of BIGINT, TEXT for enums, etc.); and (3) building the connection factory so every connection — sync and async — applies WAL mode and `PRAGMA foreign_keys=ON` before any user code runs.

The migration runner is hand-rolled (a deliberate project decision; no ORM or migration library). This is appropriate for SQLite at this scale. The pattern is well-understood: a `schema_migrations` tracking table, ordered discovery of `.sql` files via `importlib.resources.files()`, and a simple apply-if-not-present loop. The hardest part of this phase is correctly ordering the 21 migrations to satisfy all FK constraints, since SQLite enforces FK constraints at insert time (when `PRAGMA foreign_keys=ON`), not at DDL time — but this means the table creation order still matters for tables with circular-looking references (acts ↔ chapters), which are resolved by making those FKs nullable.

**Primary recommendation:** Write the pyproject.toml and package structure first (Wave 1), then author all 21 SQL migrations in dependency order (Wave 2), then wire up connection factories and CLI commands (Wave 3).

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| hatchling | >=1.27 | Build backend | Required by project decision; supports `[project.scripts]` entry points and src layout natively |
| uv | 0.10.x | Package manager / task runner | Project decision; `uv run` is the invocation mechanism for both entry points |
| typer | 0.24.x | CLI framework | Project decision; declarative subcommand groups via `app.add_typer()` |
| aiosqlite | >=0.17 | Async SQLite driver | Project decision; wraps sqlite3 for asyncio use in the MCP server |
| mcp | >=1.26.0,<2.0.0 | MCP SDK (includes FastMCP) | Project decision; bundled `mcp.server.fastmcp` — NOT standalone `fastmcp` PyPI package |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| sqlite3 | stdlib | Sync DB driver for CLI | Used in all CLI commands and the sync connection factory |
| importlib.resources | stdlib (3.12+) | Loading bundled SQL files | Used in `migrations.py` to discover and read `.sql` files from inside the package |
| contextlib | stdlib | Context manager utilities | Used to create the sync connection context manager |
| os | stdlib | Environment variable access | `os.environ.get("NOVEL_DB_PATH", "./novel.db")` |
| logging | stdlib | MCP server logging | All server-side output must go to stderr via logging — never `print()` |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Hand-rolled migration runner | Alembic, sqlite-migrate | Alembic pulls in SQLAlchemy (out of scope); sqlite-migrate adds dependency; hand-rolled is 50 lines |
| `importlib.resources.files()` | glob on `__file__` | `__file__` breaks inside zip packages; `importlib.resources` is the correct stdlib approach |
| `hatchling` | `uv_build`, `setuptools` | Project already decided hatchling; all three work for this use case |

**Installation:**

```bash
uv add typer aiosqlite "mcp>=1.26.0,<2.0.0"
uv add --dev pytest
```

---

## Architecture Patterns

### Recommended Project Structure

```
src/
  novel/
    __init__.py          # package marker, version
    cli.py               # root typer app; registers db_app subgroup
    db/
      __init__.py
      connection.py      # sync get_connection() context manager
      migrations.py      # discover_migrations(), apply_migrations(), drop_all_tables()
      seed.py            # load_seed_profile() stub
    mcp/
      __init__.py
      server.py          # FastMCP instance + run() entry point
      db.py              # async get_connection() context manager
    models/              # empty in Phase 1 — populated Phase 2
    tools/               # empty in Phase 1 — populated Phase 3+
    migrations/          # 21 .sql files bundled as package data
      001_schema_tracking.sql
      002_core_books_eras.sql
      ...
      021_literary_and_publishing.sql
pyproject.toml
```

### Pattern 1: pyproject.toml — src layout with two entry points

**What:** Single `pyproject.toml` using hatchling as build backend, src layout, two CLI entry points, bundled SQL files.

**Key insight:** Hatchling automatically includes everything under `src/novel/` in the wheel — including `.sql` files in `src/novel/migrations/`. No explicit `[tool.hatch.build.targets.wheel]` configuration is needed as long as the migrations directory lives inside the package directory.

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "drafter"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "typer>=0.24.0",
    "aiosqlite>=0.17.0",
    "mcp>=1.26.0,<2.0.0",
]

[project.scripts]
novel = "novel.cli:app"
novel-mcp = "novel.mcp.server:run"

[tool.hatch.build.targets.wheel]
packages = ["src/novel"]
```

Note: `novel = "novel.cli:app"` works because a `typer.Typer()` instance is callable. No wrapper function is needed.

Note: `novel-mcp = "novel.mcp.server:run"` requires a `run` function (not the FastMCP instance directly), because FastMCP's entry point needs to call `mcp.run(transport="stdio")`.

### Pattern 2: Sync connection factory (sqlite3)

**What:** Context manager that opens a sync sqlite3 connection, applies pragmas, yields it, and closes on exit.

**When to use:** All CLI commands (`novel db migrate`, `novel db status`, etc.)

```python
# Source: Official sqlite3 docs + production PRAGMA recommendations
import sqlite3
import os
from contextlib import contextmanager

def _get_db_path() -> str:
    return os.environ.get("NOVEL_DB_PATH", "./novel.db")

@contextmanager
def get_connection():
    """Sync SQLite connection with WAL mode and FK enforcement."""
    conn = sqlite3.connect(_get_db_path())
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.row_factory = sqlite3.Row  # dict-like rows
        yield conn
    finally:
        conn.close()
```

**Critical:** `PRAGMA foreign_keys=ON` is connection-level, not database-level. It defaults OFF and must be set on every connection. `PRAGMA journal_mode=WAL` persists at the database file level once set, but setting it on every open is harmless and ensures correctness on first run.

### Pattern 3: Async connection factory (aiosqlite)

**What:** Async context manager for use in MCP tool handlers.

**When to use:** All MCP tool implementations (Phase 3+). `novel/mcp/db.py` sets this up in Phase 1 as a stub.

```python
# Source: aiosqlite docs + WAL/FK pattern
import aiosqlite
import os
from contextlib import asynccontextmanager

def _get_db_path() -> str:
    return os.environ.get("NOVEL_DB_PATH", "./novel.db")

@asynccontextmanager
async def get_connection():
    """Async SQLite connection with WAL mode and FK enforcement."""
    async with aiosqlite.connect(_get_db_path()) as conn:
        await conn.execute("PRAGMA journal_mode=WAL")
        await conn.execute("PRAGMA foreign_keys=ON")
        conn.row_factory = aiosqlite.Row
        yield conn
```

### Pattern 4: Migration runner

**What:** Discovers `.sql` files from the bundled `novel/migrations/` package directory, compares against `schema_migrations` tracking table, applies unapplied migrations in sorted order.

**When to use:** `novel db migrate` command calls `apply_migrations()`.

```python
# Source: importlib.resources docs + custom pattern
from importlib.resources import files
import sqlite3

def discover_migrations() -> list[tuple[int, str, str]]:
    """Returns list of (version, name, sql_text) sorted by version."""
    migration_dir = files("novel").joinpath("migrations")
    results = []
    for resource in migration_dir.iterdir():
        name = resource.name
        if name.endswith(".sql"):
            version = int(name.split("_")[0])
            sql_text = resource.read_text(encoding="utf-8")
            results.append((version, name, sql_text))
    return sorted(results, key=lambda x: x[0])

def get_applied_versions(conn: sqlite3.Connection) -> set[int]:
    """Get set of already-applied migration version numbers."""
    conn.execute(
        "CREATE TABLE IF NOT EXISTS schema_migrations "
        "(version INTEGER PRIMARY KEY, name TEXT NOT NULL, applied_at TEXT NOT NULL)"
    )
    rows = conn.execute("SELECT version FROM schema_migrations").fetchall()
    return {row[0] for row in rows}

def apply_migrations(conn: sqlite3.Connection) -> list[str]:
    """Apply unapplied migrations. Returns list of applied migration names."""
    applied = get_applied_versions(conn)
    migrations = discover_migrations()
    newly_applied = []
    for version, name, sql_text in migrations:
        if version not in applied:
            conn.executescript(sql_text)  # runs all statements in file
            conn.execute(
                "INSERT INTO schema_migrations (version, name, applied_at) VALUES (?, ?, datetime('now'))",
                (version, name)
            )
            conn.commit()
            newly_applied.append(name)
    return newly_applied
```

**Important:** `conn.executescript()` automatically commits any pending transaction before executing. It handles multi-statement SQL files (each migration file may contain multiple `CREATE TABLE` statements).

### Pattern 5: Typer CLI with subcommand group

**What:** Root `app` in `cli.py` registers `db_app` as the `db` subcommand group.

```python
# Source: typer.tiangolo.com/tutorial/subcommands/add-typer/
import typer
from novel.db import cli as db_cli

app = typer.Typer(help="Novel writing toolkit CLI")
app.add_typer(db_cli.app, name="db")

if __name__ == "__main__":
    app()
```

```python
# novel/db/cli.py  (or inline in db/__init__.py)
import typer

app = typer.Typer(help="Database management commands")

@app.command()
def migrate():
    """Apply all pending migrations."""
    ...

@app.command()
def reset(yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation")):
    """Drop all tables and rebuild from migrations."""
    ...

@app.command()
def status():
    """Show migration version and table/row counts."""
    ...

@app.command()
def seed(profile: str = typer.Argument("minimal")):
    """Load a named seed profile (stub in Phase 1)."""
    typer.echo("No seed profiles defined yet.")
```

### Pattern 6: FastMCP minimal server (Phase 1 stub)

**What:** Minimal `server.py` that declares the FastMCP instance and a `run()` function. No tools registered in Phase 1.

```python
# Source: github.com/modelcontextprotocol/python-sdk
from mcp.server.fastmcp import FastMCP
import logging

logger = logging.getLogger(__name__)

mcp = FastMCP("novel-mcp")

def run():
    """Entry point for novel-mcp command."""
    logging.basicConfig(level=logging.INFO, stream=__import__("sys").stderr)
    mcp.run(transport="stdio")

if __name__ == "__main__":
    run()
```

**Important:** The `novel-mcp` pyproject.toml entry point must point to `novel.mcp.server:run` (a function), not to `novel.mcp.server:mcp` (the FastMCP instance). The `run()` wrapper is required to control the transport and configure logging before the server loop starts.

### Pattern 7: Loading bundled SQL files

**What:** Using `importlib.resources.files()` to read `.sql` files packaged inside `novel/migrations/`.

```python
# Source: docs.python.org/3.12/library/importlib.resources.html
from importlib.resources import files

# Read a single migration
sql = files("novel").joinpath("migrations/001_schema_tracking.sql").read_text()

# Iterate all migrations
migration_dir = files("novel").joinpath("migrations")
for resource in sorted(migration_dir.iterdir(), key=lambda r: r.name):
    if resource.name.endswith(".sql"):
        sql_text = resource.read_text(encoding="utf-8")
```

**Note:** For Python 3.12+, `files("novel")` uses the package name as a string (not the `anchor` parameter). The migrations directory must be inside `src/novel/` (not a sibling), so hatchling includes it automatically.

### Anti-Patterns to Avoid

- **Using `__file__` to locate SQL files:** Breaks when the package is installed as a wheel or inside a zip. Use `importlib.resources.files()` instead.
- **Setting `PRAGMA foreign_keys=ON` only once globally:** It is connection-level, not persistent. Set it in every `get_connection()` call.
- **Using `conn.execute()` for multi-statement SQL:** `execute()` only runs one statement. Use `conn.executescript()` for migration files that contain multiple `CREATE TABLE` statements.
- **Calling `print()` anywhere in MCP server code:** Corrupts the stdio protocol. All output from the MCP server goes through `logging` to stderr.
- **Making `acts.start_chapter_id` NOT NULL:** Creates a circular FK (books → acts → chapters → acts). Make it nullable; populate after chapters exist.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Async SQLite | Custom thread pool wrapper | `aiosqlite` | aiosqlite wraps sqlite3 in a thread pool correctly; getting the thread safety right manually is error-prone |
| CLI argument parsing | argparse, click directly | `typer` | Already a project decision; Typer gives type-safe args, auto --help, and composable subcommands |
| Resource loading from package | `__file__`-based path construction | `importlib.resources.files()` | Works in all installation modes (editable, wheel, zip); `__file__` breaks in some |
| MCP protocol | Custom JSON-RPC over stdio | `mcp.server.fastmcp` | The protocol has edge cases; FastMCP is the official SDK implementation |

**Key insight:** The migration runner itself is appropriately hand-rolled — it's 50-100 lines and adding sqlite-migrate or Alembic would introduce an ORM dependency the project explicitly rejects.

---

## Common Pitfalls

### Pitfall 1: SQLite integer primary keys

**What goes wrong:** Schema document uses `bigint PK` notation (PostgreSQL-style). SQLite ignores column types — but `INTEGER PRIMARY KEY` has special meaning in SQLite (it becomes the rowid alias). If you write `id BIGINT PRIMARY KEY`, SQLite creates a separate B-tree for the PK rather than using the rowid, which is slower.

**Why it happens:** Schema document was written for readability, not for a specific database.

**How to avoid:** In all migration SQL, use `id INTEGER PRIMARY KEY AUTOINCREMENT` or `id INTEGER PRIMARY KEY` (rowid alias is faster and sufficient).

**Warning signs:** Column defined as `BIGINT PRIMARY KEY` instead of `INTEGER PRIMARY KEY`.

### Pitfall 2: Enum columns in SQLite

**What goes wrong:** Schema document uses `enum(val1, val2, ...)` syntax. SQLite has no native ENUM type. If you try to run this DDL directly, it creates a column typed as `enum` (SQLite treats unknown types as NUMERIC affinity, then TEXT for most values — it will not reject invalid values).

**Why it happens:** Schema document was written for readability.

**How to avoid:** Use `TEXT` for all enum columns in SQLite DDL. Optionally add a `CHECK` constraint:

```sql
status TEXT NOT NULL CHECK(status IN ('draft', 'approved', 'provisional', 'deprecated'))
```

For Phase 1, using TEXT without CHECK constraints is acceptable — validation is enforced at the Pydantic model layer (Phase 2). Document this choice.

### Pitfall 3: Circular FK dependency between acts and chapters

**What goes wrong:** `acts.start_chapter_id` → `chapters.id` AND `chapters.act_id` → `acts.id`. If you try to create both as NOT NULL FKs with FK enforcement on, you cannot insert either record first.

**Why it happens:** Real-world bidirectional relationship.

**How to avoid:** Create `acts` before `chapters` (migration 003 before 008). Make `acts.start_chapter_id` and `acts.end_chapter_id` NULLABLE. This matches the schema document ("nullable" is already stated there).

**Warning signs:** Migration runner fails with FK constraint violation on insert.

### Pitfall 4: executescript() auto-commits

**What goes wrong:** `conn.executescript(sql)` issues an implicit `COMMIT` before executing. If you are running migration SQL inside an explicit transaction (e.g., `conn.execute("BEGIN")`), executescript will commit that transaction before running the migration.

**Why it happens:** CPython sqlite3 module behavior — executescript always commits first.

**How to avoid:** Do not wrap migration SQL in explicit transactions in Python. Let each migration file contain its own transaction if needed, or rely on the default autocommit behavior. The migration tracking INSERT (`INSERT INTO schema_migrations`) is committed after `executescript` returns.

### Pitfall 5: WAL mode not inherited by new processes

**What goes wrong:** WAL mode set on the database file persists — but the MCP server and CLI are separate processes. A test that opens the database without setting WAL will work fine (WAL persists), but a test that sets `isolation_level=None` (autocommit) without WAL may have different locking behavior.

**Why it happens:** WAL persists at the file level, but `PRAGMA foreign_keys` does not.

**How to avoid:** Always call both pragmas in every `get_connection()`. This is idempotent and takes <1ms.

### Pitfall 6: importlib.resources and editable installs

**What goes wrong:** When installed with `uv sync` in development mode (editable), `importlib.resources.files("novel")` may resolve to the `src/novel` directory directly. When installed as a wheel, it resolves inside the wheel. Both work correctly — but the migrations directory must be inside `src/novel/migrations/`, not `src/novel_migrations/` or a project-root `migrations/`.

**Why it happens:** Hatchling's src layout puts only `src/novel/` inside the package namespace.

**How to avoid:** Put migration files at `src/novel/migrations/NNN_name.sql`. Verify with `python -c "from importlib.resources import files; print(list(files('novel').joinpath('migrations').iterdir()))"` after install.

### Pitfall 7: novel-mcp entry point must be a function, not the FastMCP instance

**What goes wrong:** `novel-mcp = "novel.mcp.server:mcp"` — pointing at the FastMCP instance — may work with some MCP SDK versions but does not allow you to control transport type, configure logging, or run setup code before the server loop.

**Why it happens:** FastMCP instances are callable, so setuptools/hatchling accepts the entry point. But calling it directly uses default transport.

**How to avoid:** Always define `def run(): mcp.run(transport="stdio")` and point the entry point at `novel.mcp.server:run`.

---

## Code Examples

### Complete pyproject.toml

```toml
# Source: packaging.python.org + hatch.pypa.io/latest/config/build/
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "drafter"
version = "0.1.0"
description = "Python MCP server and CLI for novel-scale writing projects"
requires-python = ">=3.12"
dependencies = [
    "typer>=0.24.0",
    "aiosqlite>=0.17.0",
    "mcp>=1.26.0,<2.0.0",
]

[project.scripts]
novel = "novel.cli:app"
novel-mcp = "novel.mcp.server:run"

[tool.hatch.build.targets.wheel]
packages = ["src/novel"]

[tool.hatch.build.targets.sdist]
include = ["src/", "pyproject.toml"]
```

### migration 001 — schema_migrations table

```sql
-- 001_schema_tracking.sql
-- Tracks applied migrations. Applied first, before all domain tables.
CREATE TABLE IF NOT EXISTS schema_migrations (
    version    INTEGER PRIMARY KEY,
    name       TEXT    NOT NULL,
    applied_at TEXT    NOT NULL  -- ISO-8601 datetime string
);
```

### migration 002 — eras and books (no cross-dependencies)

```sql
-- 002_core_books_eras.sql
CREATE TABLE IF NOT EXISTS eras (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    name           TEXT    NOT NULL,
    sequence_order INTEGER,
    date_start     TEXT,
    date_end       TEXT,
    summary        TEXT,
    certainty_level TEXT   NOT NULL DEFAULT 'established',
    notes          TEXT,
    canon_status   TEXT    NOT NULL DEFAULT 'draft',
    created_at     TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at     TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS books (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    title              TEXT    NOT NULL,
    series_order       INTEGER,
    word_count_target  INTEGER,
    actual_word_count  INTEGER DEFAULT 0,
    status             TEXT    NOT NULL DEFAULT 'planning',
    notes              TEXT,
    canon_status       TEXT    NOT NULL DEFAULT 'draft',
    created_at         TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at         TEXT    NOT NULL DEFAULT (datetime('now'))
);
```

### drop_all_tables() for db reset

```sql
-- Introspect all user tables and drop them
-- Used by novel db reset before re-running migrate
```

```python
def drop_all_tables(conn: sqlite3.Connection) -> None:
    """Drop all user-created tables for clean reset."""
    # Must disable FK enforcement temporarily to drop tables in any order
    conn.execute("PRAGMA foreign_keys=OFF")
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    ).fetchall()
    for (table_name,) in tables:
        conn.execute(f'DROP TABLE IF EXISTS "{table_name}"')
    conn.commit()
    conn.execute("PRAGMA foreign_keys=ON")
```

### novel db status query

```python
def get_status(conn: sqlite3.Connection) -> dict:
    """Gather migration version and key table row counts."""
    # Migration version
    try:
        row = conn.execute(
            "SELECT MAX(version) as ver FROM schema_migrations"
        ).fetchone()
        version = row[0] if row and row[0] is not None else 0
    except sqlite3.OperationalError:
        version = 0  # schema_migrations does not exist yet

    # Table count
    table_count = conn.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    ).fetchone()[0]

    # Row counts for key tables
    counts = {}
    for table in ("books", "chapters", "characters", "scenes"):
        try:
            counts[table] = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        except sqlite3.OperationalError:
            counts[table] = 0

    return {"version": version, "table_count": table_count, "row_counts": counts}
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `pkg_resources` for data files | `importlib.resources.files()` | Python 3.9 (stable in 3.12) | Works in zip installs, no setuptools dependency |
| `setup.py` + `MANIFEST.in` | `pyproject.toml` + hatchling | PEP 517/518, ~2022 | Declarative, no setup.py |
| `standalone fastmcp` PyPI package | `mcp.server.fastmcp` (bundled) | 2024 | Packages have diverged; bundled version is maintained with the SDK |
| `sqlite3.connect()` with manual close | `contextmanager` + `sqlite3.connect()` | Stable pattern | Ensures connection cleanup on exceptions |
| Global WAL pragma set once | WAL pragma set on every connection | Always | WAL persists but foreign_keys does not; setting both is idempotent and safe |

**Deprecated/outdated:**
- `pkg_resources.resource_string()`: Replaced by `importlib.resources`. Avoid.
- `setup.py data_files`: Replaced by hatchling's automatic package inclusion.
- Standalone `fastmcp` PyPI package: Do not install. Use `mcp>=1.26.0,<2.0.0` from the official SDK.

---

## SQLite DDL Conventions for This Project

These conventions resolve the gap between the schema document's PostgreSQL-style notation and SQLite DDL.

| Schema doc notation | SQLite DDL | Notes |
|---------------------|-----------|-------|
| `bigint PK` | `INTEGER PRIMARY KEY AUTOINCREMENT` | Rowid alias; AUTOINCREMENT prevents rowid reuse |
| `bigint FK -> table.id` | `INTEGER REFERENCES table(id)` | FK enforcement via PRAGMA, not DDL |
| `varchar` | `TEXT` | SQLite ignores length limits |
| `text` | `TEXT` | Same |
| `boolean` | `INTEGER NOT NULL DEFAULT 0` | SQLite stores as 0/1 |
| `enum(a, b, c)` | `TEXT NOT NULL DEFAULT 'a'` | Optionally add CHECK constraint |
| `timestamp` | `TEXT NOT NULL DEFAULT (datetime('now'))` | ISO-8601 string |
| `date` | `TEXT` | ISO-8601 date string |
| `tinyint` | `INTEGER` | No range enforcement in SQLite |
| `decimal(m,n)` | `REAL` | Approximate; acceptable for metrics |
| `json` | `TEXT` | Store as JSON string; parse in application layer |
| `UNIQUE(a, b)` | `UNIQUE(a, b)` | Works identically in SQLite |
| `PRIMARY KEY (a, b)` | `PRIMARY KEY (a, b)` | Works identically |

**Timestamps pattern:** Use `TEXT NOT NULL DEFAULT (datetime('now'))` for `created_at`. For `updated_at`, use the same default — the application layer is responsible for updating this on writes (no auto-update triggers in SQLite without explicit trigger DDL).

---

## Migration Dependency Map

Critical ordering decisions for FK correctness:

```
001  schema_migrations         (no FKs)
002  eras, books               (no FKs)
003  acts                      (FK: books; start/end chapter FKs nullable)
004  cultures                  (no FKs to other user tables)
005  factions                  (FK: characters nullable — resolved via nullable)
006  locations                 (FK: cultures, factions, locations self-ref nullable)
007  characters                (FK: factions nullable, cultures nullable, eras nullable)
     NOTE: factions(leader_character_id) → characters creates a mutual FK.
     Resolved: factions.leader_character_id is nullable (set after characters exist).
008  chapters                  (FK: books, acts, characters nullable for pov_character_id)
     NOTE: acts.start_chapter_id / end_chapter_id point back to chapters.
     These are nullable and populated after chapters exist — no DDL chicken-and-egg issue.
009  scenes                    (FK: chapters, locations nullable)
010  artifacts                 (FK: characters nullable, locations nullable, eras nullable)
011  magic_system_elements,    (FK: chapters nullable)
     supernatural_elements
012  character_relationships,  (FK: characters, events nullable, chapters nullable)
     relationship_change_events,  NOTE: events is defined in migration 015.
     perception_profiles          The FK to events here is nullable — safe to define
                                  before events table exists ONLY if FK enforcement
                                  is off during DDL (SQLite does NOT check FK targets
                                  at DDL time, only at DML time). Confirmed safe.
013  character_knowledge,      (FK: characters, chapters, events all nullable)
     character_beliefs,
     character_locations,
     injury_states, title_states
014  voice_profiles,           (FK: characters, chapters nullable, scenes nullable)
     voice_drift_log
015  events,                   (FK: locations nullable, chapters nullable)
     event_participants,       (FK: events, characters)
     event_artifacts,          (FK: events, artifacts)
     travel_segments,          (FK: characters, locations, events nullable, chapters nullable)
     pov_chronological_position (FK: characters, chapters)
016  plot_threads,             (FK: chapters nullable, plot_threads self-ref nullable)
     chapter_plot_threads,     (FK: chapters, plot_threads)
     chapter_structural_obligations (FK: chapters)
017  character_arcs,           (FK: characters, chapters nullable)
     chapter_character_arcs,   (FK: chapters, character_arcs)
     arc_health_log,           (FK: character_arcs, chapters)
     chekovs_gun_registry,     (FK: chapters, scenes nullable)
     subplot_touchpoint_log    (FK: plot_threads, chapters)
018  scene_character_goals,    (FK: scenes, characters)
     pacing_beats,             (FK: chapters, scenes nullable)
     tension_measurements      (FK: chapters)
019  session_logs,             (no upstream FKs)
     agent_run_log             (FK: session_logs nullable)
020  architecture_gate,        (no upstream FKs)
     gate_checklist_items,     (FK: architecture_gate)
     project_metrics_snapshots, (no FK)
     pov_balance_snapshots     (FK: chapters, characters)
021  reader_reveals,           (FK: chapters, scenes nullable, characters nullable)
     reader_information_states, (FK: chapters)
     dramatic_irony_inventory, (FK: chapters, characters)
     reader_experience_notes,  (FK: chapters, scenes nullable)
     canon_facts,              (FK: chapters nullable, events nullable, canon_facts self-ref)
     continuity_issues,        (FK: chapters nullable, scenes nullable, canon_facts nullable)
     decisions_log,            (FK: session_logs nullable, chapters nullable)
     foreshadowing_registry,   (FK: chapters, scenes nullable)
     prophecy_registry,        (FK: characters nullable, chapters nullable)
     object_states,            (FK: artifacts, chapters, characters nullable, locations nullable)
     motif_registry,           (FK: chapters nullable)
     motif_occurrences,        (FK: motif_registry, chapters, scenes nullable)
     thematic_mirrors,         (no FK — uses generic element_a_id, element_b_id)
     opposition_pairs,         (FK: chapters nullable)
     supernatural_voice_guidelines, (no FK)
     faction_political_states, (FK: factions, chapters, characters nullable)
     name_registry,            (FK: cultures nullable, chapters nullable)
     magic_use_log,            (FK: chapters, scenes nullable, characters, magic_system_elements nullable)
     practitioner_abilities,   (FK: characters, magic_system_elements, chapters nullable)
     research_notes,           (no FK)
     open_questions,           (FK: session_logs nullable)
     documentation_tasks,      (no FK)
     publishing_assets,        (no FK)
     submission_tracker        (FK: publishing_assets nullable)
```

**Critical note on SQLite FK checking:** SQLite does NOT enforce FK target table existence at DDL time. FK constraints are only checked at DML time (INSERT/UPDATE) when `PRAGMA foreign_keys=ON`. This means migrations 012-014 can reference `events` (defined in 015) as a nullable FK in DDL without error. Inserts into those tables with a non-NULL `event_id` will fail until migration 015 runs — but that is correct behavior.

---

## Open Questions

1. **Index strategy in Phase 1**
   - What we know: Schema document does not specify indexes. Performance is not a Phase 1 requirement.
   - What's unclear: Whether to add indexes on common FK columns (character_id, chapter_id, book_id) in Phase 1 or defer to Phase 2+.
   - Recommendation: Add minimal indexes in Phase 1 on the most-queried FKs (character_id, chapter_id, book_id). These are cheap to add and prevent full-table scans from the first query. Use `CREATE INDEX IF NOT EXISTS idx_table_col ON table(col)` at the end of each migration file that introduces the column.

2. **uv version pinning**
   - What we know: Project uses uv 0.10.x.
   - What's unclear: Whether `pyproject.toml` needs a `[tool.uv]` section or whether `uv.lock` is sufficient.
   - Recommendation: `uv.lock` is generated by `uv sync` and is the source of truth for pinned versions. No manual `[tool.uv]` configuration is needed for Phase 1.

3. **`novel db reset` behavior on missing database**
   - What we know: Reset should prompt for confirmation, drop all tables, then migrate.
   - What's unclear: What happens if the database file does not exist yet (first run).
   - Recommendation: If the database does not exist, skip the drop step and just run migrate. SQLite creates the file on `sqlite3.connect()` — this is expected behavior.

---

## Sources

### Primary (HIGH confidence)
- Python 3.12 official docs — `importlib.resources.files()` API, Traversable pattern, Python 3.12 changes
  - https://docs.python.org/3.12/library/importlib.resources.html
- Typer official docs — `app.add_typer()`, `[project.scripts]` entry point pattern, package tutorial
  - https://typer.tiangolo.com/tutorial/subcommands/add-typer/
  - https://typer.tiangolo.com/tutorial/package/
- aiosqlite official docs — async context manager pattern
  - https://aiosqlite.omnilib.dev/en/latest/
- MCP Python SDK GitHub — FastMCP import path (`mcp.server.fastmcp`), `mcp.run()` API
  - https://github.com/modelcontextprotocol/python-sdk
- Hatch docs — package data inclusion in src layout
  - https://hatch.pypa.io/latest/config/build/
- SQLite official docs — PRAGMA foreign_keys, journal_mode=WAL, executescript behavior
  - https://sqlite.org/pragma.html
  - https://sqlite.org/wal.html
- uv official docs — `[project.scripts]` format, src layout with --package flag
  - https://docs.astral.sh/uv/concepts/projects/config/

### Secondary (MEDIUM confidence)
- Charles Leifer "Going Fast with SQLite and Python" — production PRAGMA settings pattern (WAL + FK + cache_size)
  - https://charlesleifer.com/blog/going-fast-with-sqlite-and-python/
- pypa/hatch GitHub discussion #427 — confirmation that hatchling auto-includes data files under `src/package/`
  - https://github.com/pypa/hatch/discussions/427

### Tertiary (LOW confidence)
- None — all major claims verified against primary or secondary sources.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries are project decisions; versions verified
- Architecture: HIGH — patterns verified against official docs (importlib.resources, aiosqlite, Typer, hatchling)
- SQLite DDL conventions: HIGH — verified against SQLite official docs
- Migration dependency order: MEDIUM — derived by hand from schema doc; FK analysis is correct but the exact grouping may need adjustment for edge cases in migration 021's large batch
- Pitfalls: HIGH — WAL/FK pragma behavior verified via official SQLite docs; executescript behavior verified via CPython docs

**Research date:** 2026-03-07
**Valid until:** 2026-09-07 (stable ecosystem — hatchling, Typer, aiosqlite are slow-moving)
