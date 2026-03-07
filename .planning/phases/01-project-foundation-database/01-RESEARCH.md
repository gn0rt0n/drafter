# Phase 1: Project Foundation & Database - Research

**Researched:** 2026-03-07
**Domain:** Python project scaffolding, uv/Hatchling packaging, SQLite migrations, sync/async connection factory, Typer CLI
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

All implementation choices delegated to Claude. The following represent Claude's settled decisions for this phase:

**Migration file convention**
- Numbered SQL files with descriptive names: `001_books.sql`, `002_characters.sql`, ... `021_xxx.sql`
- One migration = one logical domain group (not one table per file)
- Clean rebuild = delete the `.db` file and re-run all migrations in order (simplest, no DROP complexity)
- Migration runner reads files in numeric sort order from a single `drafter/db/migrations/` directory
- No migration version table needed for v1 — migrations are idempotent via `CREATE TABLE IF NOT EXISTS`

**Seed data format**
- Python modules in `drafter/seeds/` — e.g., `minimal.py` exports a `SEED_DATA` dict
- Python over SQL/YAML: IDE support, easy to read, no parsing overhead, can express relationships naturally
- `novel db seed minimal` imports the module and uses `executemany` with the dict data
- Seed modules are pure data — no database imports in seed files themselves

**Project directory layout**
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

**DB status output**
- Plain text, tabular — no Rich/color for v1 (Rich CLI is v2)
- Shows: migration count applied, total table count, and row counts for key tables (books, characters, chapters, scenes)
- Format: simple aligned columns, no box-drawing chars

### Claude's Discretion

All implementation choices delegated to Claude.

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| SETUP-01 | `pyproject.toml` configures two entry points — `novel` (CLI) and `novel-mcp` (MCP server) — both invocable via `uv run` with no global installs | pyproject.toml structure with `[project.scripts]` and `[build-system]` documented with working code example |
| SETUP-02 | All 21 SQL migration files exist and define the complete narrative schema | 21-domain schema documented; migration naming convention and ordering rules established |
| SETUP-03 | `novel db migrate` runs all migrations in order, with clean-rebuild support, completing in under 5 seconds | Migration runner pattern with `CREATE TABLE IF NOT EXISTS` idempotency; 21 small SQL files are well within 5-second budget |
| SETUP-04 | Database connection factory enables WAL mode and `PRAGMA foreign_keys=ON` on every connection (both sync sqlite3 and async aiosqlite) | Exact PRAGMA sequence documented; both sync and async connection factory code examples verified |
| CLDB-01 | `novel db migrate` builds a clean database from all 21 migrations in under 5 seconds | Migration runner logic with glob-sorted file execution; performance is not a concern for local SQLite + small SQL files |
| CLDB-02 | `novel db seed [profile]` loads a named seed profile (minimal or gate-ready) | Seed loading via Python module import + executemany; Phase 1 only scaffolds this command (seed data is Phase 2's deliverable) |
| CLDB-03 | `novel db reset` drops and rebuilds the database (migrate + optional seed) | Delete `.db` file + re-run migrate; no DROP TABLE complexity needed |
| CLDB-04 | `novel db status` displays migration version, table count, and row counts for key tables | Simple sqlite3 queries against `sqlite_master` and COUNT(*) per key table |
</phase_requirements>

---

## Summary

Phase 1 builds the project skeleton: a working `pyproject.toml` with both entry points, 21 SQL migration files covering all schema domains, a migration runner, a connection factory enforcing WAL mode and foreign key constraints, and four CLI database commands. It is a "plumbing and wiring" phase — no MCP tools, no Pydantic models, no seed data content.

The stack is entirely conventional and well-documented. Every technology choice (uv, Hatchling, Typer, aiosqlite, sqlite3) has been verified from official sources with HIGH confidence. The two highest-risk items are: (1) getting the `pyproject.toml` `[build-system]` block right so `uv run novel` and `uv run novel-mcp` resolve correctly, and (2) ensuring the connection factory executes PRAGMAs before any other SQL on every connection. Both risks are easily verified against concrete test criteria.

The project uses a **flat src layout** (not `src/drafter/`). The CONTEXT.md specifies the package lives at the repo root as `drafter/` with a `pyproject.toml` alongside it. This differs from the prior research's `src/drafter/` recommendation — the CONTEXT.md layout is authoritative. The `pyproject.toml` must configure Hatchling accordingly.

The 21 migration files cover all 14 narrative domains in dependency order: core entities first (books, acts, chapters, scenes, characters, locations), then world-building (factions, cultures, eras, magic), then relational and state tables (relationships, character state, plot threads, arcs), then supporting domains (timeline, gate, session, publishing, names, voice, literary, canon, knowledge). Each migration file uses `CREATE TABLE IF NOT EXISTS` for idempotency.

**Primary recommendation:** Build pyproject.toml first and verify both entry points immediately — before writing a single migration file. Entry point misconfiguration is the fastest way to lose hours.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | >=3.12 | Runtime | 3.12 is the stable sweet spot; MCP SDK requires >=3.10 but 3.12 has best dependency compatibility |
| uv | 0.10.x | Project/package manager | 2025/2026 standard; replaces pip, poetry, pyenv; all commands run via `uv run` |
| Hatchling | latest | Build backend | Required for `[project.scripts]` entry points; used by MCP SDK itself; PEP-compliant |
| Typer | >=0.24.0 | CLI framework | Type-hint-driven subcommands; Rich included as dependency; `novel` entry point |
| sqlite3 | stdlib | Sync database access (CLI) | Built-in; no extra dependency; correct for sync CLI context |
| aiosqlite | >=0.22.0 | Async SQLite bridge (MCP server) | Wraps sqlite3 in thread executor; needed for async FastMCP context; Phase 1 scaffolds async connection |
| mcp | >=1.26.0,<2.0.0 | MCP server (scaffold only in Phase 1) | Pin `<2.0.0`; use bundled `mcp.server.fastmcp`, NOT standalone `fastmcp` PyPI package |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pydantic | >=2.11.0,<3.0.0 | Required by mcp SDK | Transitive; listed in dependencies; not directly used in Phase 1 |
| pytest | >=8.3.4 | Test runner | Phase 1 does not require tests, but dev dependency configured here |
| ruff | >=0.8.5 | Linting + formatting | Configure in `pyproject.toml`; single tool replaces flake8+isort+black |

### Installation

```bash
# Initialize project (if not already done)
uv init drafter --package

# Add core dependencies
uv add "mcp>=1.26.0,<2.0.0"
uv add "typer>=0.24.0"
uv add "aiosqlite>=0.22.0"
uv add "pydantic>=2.11.0,<3.0.0"

# Add dev dependencies
uv add --group dev pytest pytest-asyncio ruff
uv add --group dev "mcp[cli]>=1.26.0,<2.0.0"

# Verify entry points work
uv run novel --help
uv run novel-mcp --help
```

---

## Architecture Patterns

### Project Directory Structure (from CONTEXT.md — authoritative)

```
drafter/                     # repo root
  pyproject.toml
  uv.lock
  drafter/                   # the importable package
    __init__.py
    db/
      __init__.py
      migrations/            # 001_books.sql ... 021_xxx.sql
      connection.py          # get_connection() (sync) + get_async_connection() (async)
      migrate.py             # migration runner
      seed.py                # seed loader (scaffold in Phase 1)
    seeds/
      __init__.py
      minimal.py             # SEED_DATA dict (scaffold in Phase 1, content in Phase 2)
    cli/
      __init__.py
      main.py                # Typer app, top-level command group
      db.py                  # `novel db` subcommands
    mcp/
      __init__.py
      server.py              # FastMCP server (scaffold only in Phase 1)
  tests/                     # (Phase 2+)
```

**Note:** The CONTEXT.md specifies a flat package layout (`drafter/drafter/...`), not a `src/drafter/` layout. Hatchling must be configured to find the package at the correct path.

### Pattern 1: pyproject.toml with Two Entry Points

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

[tool.hatch.build.targets.wheel]
packages = ["drafter"]

[dependency-groups]
dev = [
    "pytest>=8.3.4",
    "pytest-asyncio>=1.3.0",
    "ruff>=0.8.5",
    "mcp[cli]>=1.26.0,<2.0.0",
]

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "SIM"]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
```

**Critical:** `[build-system]` block is required. Without it, uv does not install the project as a package, and `[project.scripts]` entry points are never created.

### Pattern 2: Typer CLI Entry Point

```python
# drafter/cli/main.py
import typer

app = typer.Typer(name="novel", help="Novel management CLI")

from drafter.cli import db  # noqa: E402

app.add_typer(db.app, name="db")

if __name__ == "__main__":
    app()
```

```python
# drafter/cli/db.py
import typer

app = typer.Typer(help="Database management commands")


@app.command()
def migrate(db_path: str = typer.Option(..., envvar="NOVEL_DB_PATH", help="Path to SQLite database")):
    """Run all pending migrations."""
    from drafter.db.migrate import run_migrations
    run_migrations(db_path)
    typer.echo("Migrations complete.")


@app.command()
def seed(profile: str = "minimal", db_path: str = typer.Option(..., envvar="NOVEL_DB_PATH")):
    """Load a seed profile into the database."""
    from drafter.db.seed import load_seed
    load_seed(db_path, profile)
    typer.echo(f"Seed profile '{profile}' loaded.")


@app.command()
def reset(db_path: str = typer.Option(..., envvar="NOVEL_DB_PATH"), seed_profile: str = ""):
    """Drop and rebuild the database."""
    import os
    if os.path.exists(db_path):
        os.remove(db_path)
    from drafter.db.migrate import run_migrations
    run_migrations(db_path)
    if seed_profile:
        from drafter.db.seed import load_seed
        load_seed(db_path, seed_profile)
    typer.echo("Database reset complete.")


@app.command()
def status(db_path: str = typer.Option(..., envvar="NOVEL_DB_PATH")):
    """Show migration version and table/row counts."""
    from drafter.db.connection import get_connection
    with get_connection(db_path) as conn:
        table_count = conn.execute(
            "SELECT count(*) FROM sqlite_master WHERE type='table'"
        ).fetchone()[0]
        typer.echo(f"Tables:     {table_count}")
        for table in ["books", "characters", "chapters", "scenes"]:
            try:
                count = conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
                typer.echo(f"  {table:<15} {count}")
            except Exception:
                typer.echo(f"  {table:<15} (not yet created)")
```

### Pattern 3: FastMCP Server Scaffold (Phase 1 minimum)

```python
# drafter/mcp/server.py
import logging

from mcp.server.fastmcp import FastMCP

# Never use print() in MCP server code — corrupts stdio protocol
logging.basicConfig(level=logging.INFO, stream=__import__("sys").stderr)
logger = logging.getLogger(__name__)

mcp = FastMCP("novel")

# Phase 1: scaffold only — tools added in Phase 3+


def main():
    """Entry point for the novel-mcp command."""
    mcp.run()  # Defaults to stdio transport


if __name__ == "__main__":
    main()
```

### Pattern 4: Database Connection Factory

Both sync and async connections must enforce WAL mode and `PRAGMA foreign_keys=ON` on every connection. The PRAGMA sequence must come before any other SQL.

```python
# drafter/db/connection.py
import os
import sqlite3
from contextlib import contextmanager, asynccontextmanager

import aiosqlite


def get_db_path() -> str:
    """Get database path from environment variable."""
    path = os.environ.get("NOVEL_DB_PATH")
    if not path:
        raise RuntimeError("NOVEL_DB_PATH environment variable is not set")
    return path


@contextmanager
def get_connection(db_path: str | None = None):
    """Sync SQLite connection for CLI use. Enforces WAL + FK on every connection."""
    path = db_path or get_db_path()
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    # CRITICAL: These PRAGMAs must be set before any other SQL
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=5000")
    try:
        yield conn
    finally:
        conn.close()


@asynccontextmanager
async def get_async_connection(db_path: str | None = None):
    """Async SQLite connection for MCP server use. Enforces WAL + FK on every connection."""
    path = db_path or get_db_path()
    conn = await aiosqlite.connect(path)
    conn.row_factory = aiosqlite.Row
    # CRITICAL: These PRAGMAs must be set before any other SQL
    await conn.execute("PRAGMA journal_mode=WAL")
    await conn.execute("PRAGMA foreign_keys=ON")
    await conn.execute("PRAGMA busy_timeout=5000")
    try:
        yield conn
    finally:
        await conn.close()
```

### Pattern 5: Migration Runner

```python
# drafter/db/migrate.py
import os
import sqlite3
import glob

MIGRATIONS_DIR = os.path.join(os.path.dirname(__file__), "migrations")


def run_migrations(db_path: str) -> int:
    """Run all SQL migration files in numeric order. Returns count of files applied."""
    # Use plain sqlite3 (not the connection factory) — WAL PRAGMA outside transaction
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")

    migration_files = sorted(glob.glob(os.path.join(MIGRATIONS_DIR, "*.sql")))

    applied = 0
    for filepath in migration_files:
        with open(filepath, "r") as f:
            sql = f.read()
        conn.executescript(sql)  # executescript runs each statement; handles multi-statement files
        applied += 1

    # Validate FK integrity after all migrations applied
    violations = conn.execute("PRAGMA foreign_key_check").fetchall()
    conn.close()

    if violations:
        raise RuntimeError(f"Foreign key violations after migration: {violations}")

    return applied
```

**Note on `executescript`:** SQLite's `executescript()` issues an implicit `COMMIT` before running, then runs all statements as a transaction. It is the correct method for applying multi-statement `.sql` files. It also resets PRAGMAs set outside the transaction — call `PRAGMA foreign_keys=ON` and `PRAGMA journal_mode=WAL` before `executescript` (as shown above).

### Pattern 6: Seed Loader Scaffold

```python
# drafter/db/seed.py
import importlib
from drafter.db.connection import get_connection


def load_seed(db_path: str, profile: str = "minimal") -> None:
    """Load a named seed profile into the database."""
    module_path = f"drafter.seeds.{profile}"
    try:
        module = importlib.import_module(module_path)
    except ModuleNotFoundError:
        raise ValueError(f"Unknown seed profile: '{profile}'. "
                        f"Available: minimal, gate_ready")

    seed_data: dict = module.SEED_DATA

    with get_connection(db_path) as conn:
        for table, rows in seed_data.items():
            if not rows:
                continue
            columns = list(rows[0].keys())
            placeholders = ", ".join(["?"] * len(columns))
            sql = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
            conn.executemany(sql, [list(r.values()) for r in rows])
        conn.commit()
```

### Pattern 7: The 21 Migration Files

The migrations must be applied in strict numeric order because foreign key references create dependencies. The ordering below reflects the dependency graph — each migration only references tables defined in earlier-numbered migrations.

| File | Domain | Key Tables |
|------|--------|-----------|
| `001_core_entities.sql` | Books, Acts | `books`, `acts` |
| `002_characters.sql` | Characters | `characters` |
| `003_locations.sql` | Locations | `locations` |
| `004_factions.sql` | Factions, Cultures, Eras | `factions`, `cultures`, `eras` |
| `005_magic.sql` | Magic System | `magic_systems`, `magic_elements`, `practitioner_abilities`, `magic_use_log` |
| `006_chapters.sql` | Chapters, Scenes | `chapters`, `scenes`, `chapter_plans`, `chapter_obligations` |
| `007_character_state.sql` | Character State Over Time | `character_state`, `character_injuries`, `character_beliefs`, `character_knowledge` |
| `008_relationships.sql` | Relationships & Perception | `relationships`, `perception_profiles`, `relationship_change_log` |
| `009_plot_threads.sql` | Plot & Arcs | `plot_threads`, `subplot_touchpoints`, `chekovs_guns` |
| `010_character_arcs.sql` | Character Arcs & Health | `character_arcs`, `arc_health_log` |
| `011_scene_goals.sql` | Scene Character Goals | `scene_character_goals` |
| `012_timeline.sql` | Timeline Events, Travel | `timeline_events`, `pov_positions`, `travel_segments` |
| `013_canon.sql` | Canon Facts, Decisions | `canon_facts`, `story_decisions`, `continuity_issues` |
| `014_knowledge.sql` | Reader State & Dramatic Irony | `reader_state`, `dramatic_irony_inventory`, `reader_reveals` |
| `015_literary.sql` | Foreshadowing & Literary Devices | `foreshadowing`, `prophecies`, `motifs`, `motif_occurrences`, `thematic_mirrors`, `opposition_pairs` |
| `016_names.sql` | Name Registry | `name_registry` |
| `017_voice.sql` | Voice Profiles & Drift | `voice_profiles`, `supernatural_voice_guidelines`, `voice_drift_log` |
| `018_publishing.sql` | Publishing Assets | `publishing_assets`, `submissions` |
| `019_session.sql` | Sessions, Agent Runs, Metrics | `session_logs`, `agent_run_log`, `project_snapshots`, `open_questions` |
| `020_gate.sql` | Architecture Gate | `architecture_gate`, `gate_checklist_items` |
| `021_indexes.sql` | Performance Indexes | Indexes on all FK columns and frequently-queried fields |

**Key design rules for migration SQL:**
- Every table: `CREATE TABLE IF NOT EXISTS` for idempotency on re-run
- Every table: `canon_status TEXT CHECK(canon_status IN ('draft','approved','provisional','deprecated'))`
- Every table: `created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP`, `updated_at TIMESTAMP`
- Every table: `notes TEXT` for freeform annotation
- Every foreign key column: explicit FK constraint (enforced because `PRAGMA foreign_keys=ON`)
- Last migration (`021_indexes.sql`): All FK column indexes, slug/name indexes on frequently-searched tables

### Anti-Patterns to Avoid

- **Missing `[build-system]` in pyproject.toml:** Entry points will not be created. Symptom: `uv run novel` says "command not found."
- **Calling `PRAGMA foreign_keys=ON` inside an `executescript()` transaction:** PRAGMAs have no effect inside transactions. Always set before calling `executescript`.
- **Testing migrations only against an existing database:** Migrations that reference tables from later-numbered files work against a populated database but fail on a clean rebuild. Always test against a fresh file.
- **Using `print()` in `drafter/mcp/server.py`:** Corrupts stdio JSON-RPC protocol. Use `logging.getLogger(__name__).info(...)` with `stream=sys.stderr`.
- **Hardcoding the database path:** The path must come from `NOVEL_DB_PATH` environment variable for MCP integration to work.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Multi-statement SQL file execution | Custom SQL parser/splitter | `conn.executescript(sql)` | SQLite stdlib handles multi-statement files correctly; handles semicolons, comments |
| Entry point discovery | Custom `python -m` runner | `[project.scripts]` in pyproject.toml + Hatchling | Standard Python packaging; uv creates scripts in `.venv/bin/` automatically |
| Async SQLite | `asyncio.to_thread(sqlite3_call)` | `aiosqlite` | aiosqlite is exactly this but with a clean async context manager API |
| CLI argument parsing | Custom argparse code | Typer with type hints | Typer generates `--help`, validates types, and supports subcommands with zero boilerplate |
| Glob + sort for migration files | Custom file discovery | `sorted(glob.glob("migrations/*.sql"))` | One line; lexicographic sort of `001_...` files gives correct numeric order |

**Key insight:** Every "plumbing" problem in this phase has a stdlib or single-library solution. The goal is assembling known pieces correctly, not building custom infrastructure.

---

## Common Pitfalls

### Pitfall 1: UV Entry Point Misconfiguration

**What goes wrong:** `uv run novel` or `uv run novel-mcp` returns "command not found" or fails with an import error.

**Why it happens:** Either `[build-system]` is missing from `pyproject.toml` (so uv does not install the project as an editable package), or the entry point path in `[project.scripts]` does not match the actual module and function (`"drafter.cli.main:app"` requires `app = typer.Typer(...)` at module level in `drafter/cli/main.py`).

**How to avoid:** Verify both entry points immediately after setting up `pyproject.toml`, before writing migrations. Run `uv sync` then `uv run novel --help`. Fix before proceeding.

**Warning signs:** "No such command 'novel'" or "ModuleNotFoundError: No module named 'drafter'".

### Pitfall 2: PRAGMA foreign_keys Silently Off

**What goes wrong:** The database accepts INSERT statements that violate foreign key constraints without any error. Schema relationships become decorative.

**Why it happens:** SQLite disables FK enforcement by default. `sqlite3.connect()` and `aiosqlite.connect()` do not enable it. The setting must be made per-connection.

**How to avoid:** The connection factory (`get_connection()` and `get_async_connection()`) must execute `PRAGMA foreign_keys=ON` as the second statement after connect. Verify by inserting a record referencing a nonexistent FK and confirming the error is raised.

**Warning signs:** Invalid FK inserts succeed silently; `PRAGMA foreign_keys` query returns `0`.

### Pitfall 3: PRAGMA Inside executescript Transaction

**What goes wrong:** WAL mode and foreign key enforcement fail to apply when set inside `executescript()`.

**Why it happens:** `executescript()` issues an implicit `COMMIT` and wraps all statements in a transaction. PRAGMAs inside a transaction have no effect.

**How to avoid:** Call `conn.execute("PRAGMA journal_mode=WAL")` and `conn.execute("PRAGMA foreign_keys=ON")` on the raw connection object before calling `conn.executescript(sql)`.

**Warning signs:** `PRAGMA journal_mode` returns `delete` (not `wal`) after migration; FK violations not caught during migration.

### Pitfall 4: Migration Order Breaks on Clean Rebuild

**What goes wrong:** `novel db migrate` succeeds on a development machine (where some tables already exist from previous runs) but fails on a fresh database with "no such table" errors.

**Why it happens:** A migration file references a table from a later-numbered migration — the reference works when the table exists from a previous run but fails when the database is empty.

**How to avoid:** Always test `novel db migrate` against a freshly deleted `.db` file as part of any migration change. The clean rebuild test is a Phase 1 acceptance criterion.

**Warning signs:** `novel db migrate` produces "no such table: X" error on empty database; developers run individual migration files manually.

### Pitfall 5: stdout Print in MCP Server Scaffold

**What goes wrong:** The MCP server produces output on stdout, corrupting the JSON-RPC protocol stream. Claude Code receives malformed responses.

**Why it happens:** Python's default `print()` goes to stdout. Even a single diagnostic print during server startup corrupts the protocol.

**How to avoid:** Configure logging to stderr in the server module (not stdout). Add a ruff rule to flag `print(` in `drafter/mcp/` directory files. The Phase 1 scaffold must establish this pattern even though no tools are registered yet.

**Warning signs:** `uv run novel-mcp --help` shows unexpected text; JSON parse errors in MCP client logs.

---

## Code Examples

### Complete pyproject.toml

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

[tool.hatch.build.targets.wheel]
packages = ["drafter"]

[dependency-groups]
dev = [
    "pytest>=8.3.4",
    "pytest-asyncio>=1.3.0",
    "ruff>=0.8.5",
    "mcp[cli]>=1.26.0,<2.0.0",
]

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "SIM"]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
```

### Migration File Header Convention

Every migration file should start with a comment block for documentation:

```sql
-- Migration: 006_chapters.sql
-- Domain: Chapters & Scenes
-- Depends on: 001_core_entities.sql (books, acts), 002_characters.sql (characters), 003_locations.sql (locations)
-- Tables: chapters, scenes, chapter_plans, chapter_obligations

CREATE TABLE IF NOT EXISTS chapters (
    id                      INTEGER PRIMARY KEY,
    book_id                 INTEGER NOT NULL REFERENCES books(id),
    act_id                  INTEGER REFERENCES acts(id),
    chapter_number          INTEGER NOT NULL,
    title                   TEXT,
    pov_character_id        INTEGER REFERENCES characters(id),
    word_count_target       INTEGER,
    actual_word_count       INTEGER DEFAULT 0,
    status                  TEXT CHECK(status IN ('planned','outlined','architected','approved','drafted','revised','final')) DEFAULT 'planned',
    summary                 TEXT,
    opening_state           TEXT,
    closing_state           TEXT,
    structural_function     TEXT,
    notes                   TEXT,
    canon_status            TEXT CHECK(canon_status IN ('draft','approved','provisional','deprecated')) DEFAULT 'draft',
    created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at              TIMESTAMP,
    reviewed_at             TIMESTAMP
);
```

### SQLite PRAGMA Sequence (verified)

```python
# Source: SQLite official docs + verified against aiosqlite 0.22.x behavior
# This sequence must be used verbatim in the connection factory

# SYNC (CLI)
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
conn.execute("PRAGMA journal_mode=WAL")    # Must be BEFORE foreign_keys and busy_timeout
conn.execute("PRAGMA foreign_keys=ON")     # OFF by default in SQLite
conn.execute("PRAGMA busy_timeout=5000")   # 5s wait on lock contention

# ASYNC (MCP Server)
conn = await aiosqlite.connect(db_path)
conn.row_factory = aiosqlite.Row
await conn.execute("PRAGMA journal_mode=WAL")
await conn.execute("PRAGMA foreign_keys=ON")
await conn.execute("PRAGMA busy_timeout=5000")
```

### Verifying FK Enforcement (acceptance criterion)

```python
# Verification test for SETUP-04 acceptance criterion
# Insert a record with invalid FK — must raise IntegrityError

import sqlite3
import tempfile
import os

def verify_fk_enforcement(db_path: str):
    """Confirms PRAGMA foreign_keys=ON is active by attempting invalid FK insert."""
    from drafter.db.connection import get_connection
    with get_connection(db_path) as conn:
        try:
            conn.execute("INSERT INTO chapters (book_id, chapter_number) VALUES (9999, 1)")
            conn.commit()
            raise AssertionError("FK violation was NOT caught — foreign_keys PRAGMA not active!")
        except sqlite3.IntegrityError as e:
            print(f"FK enforcement verified: {e}")
```

### DB Status Output Format

```
novel db status
```

Expected output (plain text, aligned columns, no Rich):
```
Database: /path/to/novel.sqlite
Tables:   21

Row counts:
  books           1
  characters      0
  chapters        0
  scenes          0
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `pip` + `requirements.txt` | `uv` with `pyproject.toml` | 2024-2025 | No global installs; reproducible lockfile; faster |
| `setup.py` + `setup.cfg` | `pyproject.toml` with `[build-system]` | PEP 518/660 (2020-2021) | Single config file; standard tooling |
| Standalone `fastmcp` PyPI package | Built-in `mcp.server.fastmcp` | MCP SDK 1.x | The packages have diverged; SDK built-in is sufficient |
| `asyncio.run()` wrappers around sqlite3 | `aiosqlite` | 2022+ | Cleaner API; proper async context manager |
| Multiple config files (setup.cfg, tox.ini, .flake8) | Single `pyproject.toml` with `[tool.ruff]` etc. | 2023+ | One file for all tooling config |

**Deprecated / don't use:**
- `mcp>=2.0.0` — pre-alpha, breaking changes; pin `<2.0.0`
- Standalone `fastmcp` PyPI package — diverged from SDK built-in; do not install separately
- `[tool.hatch.build.targets.wheel] packages = ["src/drafter"]` — only if using `src/` layout; this project uses flat layout
- `PRAGMA foreign_keys = ON` inside a transaction — no effect; must be set before `executescript()`

---

## Open Questions

1. **Package path in Hatchling config**
   - What we know: CONTEXT.md specifies `drafter/` at repo root (flat layout, not `src/drafter/`)
   - What's unclear: Whether the repo root already has a `drafter/` directory or uv needs `uv init --package drafter` to scaffold it
   - Recommendation: Run `ls` first; if no `drafter/` package directory exists, scaffold with `uv init --package drafter` and adjust the resulting structure to match the CONTEXT.md layout

2. **WAL journal_mode PRAGMA and executescript interaction**
   - What we know: `executescript()` issues an implicit COMMIT; PRAGMAs inside transactions have no effect
   - What's unclear: Whether `PRAGMA journal_mode=WAL` specifically is transaction-sensitive (vs. being a file-level setting that persists)
   - Recommendation: Set WAL mode before `executescript()` on the raw connection; also set it in the connection factory for every subsequent connection. WAL mode persists to the database file once set, but the PRAGMA must succeed at least once.

3. **`novel-mcp --help` behavior with stdio FastMCP**
   - What we know: `mcp.run()` starts the stdio protocol server (not a help screen)
   - What's unclear: How `--help` should be surfaced for the MCP server entry point — Typer provides it naturally for CLI apps, but FastMCP's `main()` is not a Typer app
   - Recommendation: Wrap `main()` in a minimal Typer command so `novel-mcp --help` produces meaningful output, or accept that `--help` will show FastMCP's own usage. The success criterion requires "output without errors" — any reasonable help/usage text satisfies this.

---

## Sources

### Primary (HIGH confidence)
- `.planning/research/STACK.md` — Stack decisions verified 2026-03-07 against official PyPI metadata, MCP SDK v1.26.0 pyproject.toml, uv docs
- `.planning/research/ARCHITECTURE.md` — Architecture patterns verified 2026-03-07 against MCP Python SDK GitHub, FastMCP docs, uv project config docs
- `.planning/research/PITFALLS.md` — Pitfalls verified 2026-03-07 against SQLite official docs, MCP SDK issues, community production reports
- [SQLite Foreign Key Support](https://sqlite.org/foreignkeys.html) — PRAGMA foreign_keys behavior, transaction interaction
- [SQLite WAL Documentation](https://sqlite.org/wal.html) — WAL mode behavior, persistence
- [uv Documentation](https://docs.astral.sh/uv/) — Entry points, project config, `[build-system]` requirement
- [MCP Python SDK v1.26.0](https://github.com/modelcontextprotocol/python-sdk/tree/v1.26.0) — FastMCP entry point, `mcp.run()` behavior

### Secondary (MEDIUM confidence)
- [sqlite3 executescript docs (Python stdlib)](https://docs.python.org/3/library/sqlite3.html#sqlite3.Connection.executescript) — COMMIT behavior before executescript
- [aiosqlite PyPI](https://pypi.org/project/aiosqlite/) — v0.22.x async context manager API

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all verified from official sources in prior research
- Architecture: HIGH — layout is locked in CONTEXT.md; patterns are standard Python packaging
- Pitfalls: HIGH — all verified against official SQLite docs and MCP SDK source

**Research date:** 2026-03-07
**Valid until:** 2026-06-07 (stable libraries; uv versioning is fast-moving but patch-level changes do not affect these patterns)
