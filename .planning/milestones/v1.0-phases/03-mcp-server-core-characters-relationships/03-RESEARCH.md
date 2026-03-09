# Phase 3: MCP Server Core, Characters & Relationships - Research

**Researched:** 2026-03-07
**Domain:** FastMCP server, aiosqlite async tools, MCP in-memory testing, SQLite upsert patterns
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Tool registration architecture**
- Each domain tool module (`tools/characters.py`, `tools/relationships.py`) exposes a `register(mcp: FastMCP) -> None` function
- `server.py` calls each module's `register(mcp)` at startup: `from novel.tools import characters, relationships; characters.register(mcp); relationships.register(mcp)`
- Inside `register()`, tools are defined as local async functions and decorated with `mcp.tool()` — the FastMCP instance is passed in, never imported globally from tools modules
- This avoids circular imports, keeps each module self-contained, and scales identically for all 7 remaining domain phases (just add another `register(mcp)` call)
- `tools/__init__.py` stays minimal — no auto-discovery magic, explicit registration only

**Tool naming convention**
- Verb-first snake_case: `get_character`, `list_characters`, `create_character`, `update_character`
- Pattern: `{verb}_{noun}` for single-entity tools, `{verb}_{noun}s` for list/collection tools
- State-query tools: `get_character_injuries`, `get_character_knowledge`, `get_character_beliefs`, `get_character_location`
- Logging tools: `log_character_knowledge`
- Relationship tools: `get_relationship`, `list_character_relationships`, `create_relationship`, `update_relationship`, `log_relationship_change`, `get_perception_profile`, `upsert_perception_profile`

**Character state queries (time-varying tables)**
- 4 state tables (injuries, knowledge, beliefs, character_locations) get separate tools — not bundled into `get_character`
- Each state tool takes `character_id` as required param; `chapter_id` as optional param where the schema supports time scoping
- `get_character` returns the core characters table row only (no state embedded)
- State tools: `get_character_injuries(character_id, chapter_id)`, `get_character_knowledge(character_id, chapter_id=None)`, `get_character_beliefs(character_id)`, `get_character_location(character_id, chapter_id=None)`
- Knowledge logging: `log_character_knowledge(character_id, chapter_id, knowledge_type, content, ...)`
- This keeps each tool mapping 1:1 with a table/query — Claude requests exactly what it needs

**Error contract enforcement**
- Carried forward from Phase 1: every tool returns `NotFoundResponse` (not raises) for missing records
- Validation failures return `ValidationFailure(is_valid=False, errors=[...])` — never raise HTTPException or similar
- No `print()` anywhere in `novel/mcp/` or `novel/tools/` — all logging via `logging.getLogger(__name__)`
- Gate violations return `GateViolation(requires_action=...)` — relevant for prose-phase tools in Phase 6+, not needed in Phase 3

**Test database strategy**
- Tests use in-memory SQLite (`:memory:`) — fast, isolated, zero cleanup
- `conftest.py` creates a test database by running migrations programmatically against `:memory:`, then seeding with Phase 2's minimal seed profile via `load_seed_profile`
- Tests use the FastMCP in-memory client to call tools (not raw function calls) — verifies the actual MCP callable interface
- No mocking of DB connections — real SQL against real schema is the reliability guarantee
- Test discovery: `tests/test_characters.py` and `tests/test_relationships.py`

### Claude's Discretion
- Exact SQL query patterns for each tool (joins, CTEs, etc.)
- aiosqlite row-to-model mapping implementation details
- Specific `chapter_id` scoping logic for state tables (latest-before-chapter vs exact-match)
- Whether to add any DB indexes in Phase 3 to support common tool queries
- conftest.py fixture scope (session vs function level for test DB)

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| ERRC-01 | Every MCP tool returns `null` with `not_found_message` when record not found — never raises | `NotFoundResponse` model exists in `novel.models.shared`; pattern: `if row is None: return NotFoundResponse(not_found_message=...)` |
| ERRC-02 | Every MCP tool returns `is_valid: false` + `errors` on validation failure — never raises | `ValidationFailure` model exists in `novel.models.shared`; Pydantic v2 `model_validate` raises `ValidationError` — catch and return `ValidationFailure` |
| ERRC-03 | Prose-phase tools return `requires_action` when gate not certified | `GateViolation` model exists; NOT needed for Phase 3 tools (non-prose-phase) |
| ERRC-04 | No `print()` in MCP server code — all logging via `logging` module | Grep-verifiable; `logging.getLogger(__name__)` in every module |
| CHAR-01 | `get_character` — retrieve character profile by ID | `SELECT * FROM characters WHERE id = ?`; return `Character` or `NotFoundResponse` |
| CHAR-02 | `get_character_state` — retrieve character state at given chapter | Compound tool wrapping 4 state table queries: injuries, knowledge, beliefs, location |
| CHAR-03 | `list_characters` — list all characters in book | `SELECT * FROM characters ORDER BY name`; return `list[Character]` |
| CHAR-04 | `upsert_character` — create or update character record | `INSERT OR REPLACE` or `INSERT ... ON CONFLICT DO UPDATE` |
| CHAR-05 | `log_character_knowledge` — log what character learns at chapter | `INSERT INTO character_knowledge` |
| CHAR-06 | `get_character_injuries` — retrieve character injury history | `SELECT * FROM injury_states WHERE character_id = ?` with optional chapter filter |
| CHAR-07 | `get_character_beliefs` — retrieve character current beliefs | `SELECT * FROM character_beliefs WHERE character_id = ?` |
| REL-01 | `get_relationship` — retrieve relationship between two characters | `SELECT * FROM character_relationships WHERE (character_a_id=? AND character_b_id=?) OR (...)` |
| REL-02 | `get_perception_profile` — retrieve how one character perceives another | `SELECT * FROM perception_profiles WHERE observer_id=? AND subject_id=?` |
| REL-03 | `list_relationships` — list all relationships for a character | `SELECT * FROM character_relationships WHERE character_a_id=? OR character_b_id=?` |
| REL-04 | `upsert_relationship` — create or update relationship | `INSERT ... ON CONFLICT(character_a_id, character_b_id) DO UPDATE` |
| REL-05 | `upsert_perception_profile` — create or update perception profile | `INSERT ... ON CONFLICT(observer_id, subject_id) DO UPDATE` |
| REL-06 | `log_relationship_change` — log change event in relationship | `INSERT INTO relationship_change_events` |
</phase_requirements>

---

## Summary

Phase 3 wires a working FastMCP server: 13 tools across two domains, full error contract, and in-memory pytest coverage. The infrastructure is already in place — `server.py` has a `FastMCP("novel-mcp")` instance and a `run()` entry point; `mcp/db.py` has an async connection factory; all Pydantic models are built; seed data is ready. The work is purely additive: create `tools/characters.py` and `tools/relationships.py` with `register(mcp)` functions, call them in `server.py`, and add test files.

The key architectural challenge is the test strategy. The CONTEXT.md specifies using the FastMCP in-memory client, which the MCP SDK provides via `mcp.shared.memory.create_connected_server_and_client_session`. This creates a real ClientSession connected to the running server over in-memory streams — so tests exercise the full MCP protocol stack, not just raw function calls. The complication is that async tests require either `pytest-asyncio` or `anyio[trio]` as a test dependency, and the conftest must wire the in-memory DB path into `NOVEL_DB_PATH` so `get_connection()` routes to the test database.

The in-memory DB isolation challenge: `get_connection()` reads `NOVEL_DB_PATH` from env and opens a fresh file connection. For tests to use an in-memory DB that has seed data pre-loaded, the conftest must either (a) write seed data to a temp file that tests point to, or (b) override `get_connection()` itself. Option (b) is cleaner and avoids filesystem coupling — monkeypatching `novel.mcp.db.get_connection` with a fixture that returns a pre-seeded async in-memory connection. This gives real SQL execution against the real schema with zero file I/O.

**Primary recommendation:** Use `mcp.shared.memory.create_connected_server_and_client_session` for MCP-protocol-level testing; monkeypatch `novel.mcp.db.get_connection` in conftest to inject an in-memory aiosqlite connection pre-loaded with migrations + minimal seed.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `mcp.server.fastmcp.FastMCP` | 1.26.0 (bundled) | Tool registration and server lifecycle | Already installed; diverged from standalone `fastmcp` PyPI package |
| `aiosqlite` | >=0.17.0 | Async SQLite for MCP tool handlers | Established in Phase 1; `get_connection()` already uses it |
| `pydantic` | v2 (>=2.11) | Model validation and serialization | All domain models already defined |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `mcp.shared.memory.create_connected_server_and_client_session` | 1.26.0 | In-memory MCP client for testing | All tool tests — creates real ClientSession over memory streams |
| `pytest-asyncio` | latest | Run async test functions with pytest | Required for any `async def test_*` function |
| `mcp.client.session.ClientSession` | 1.26.0 | Client interface for calling tools in tests | Accessed through `create_connected_server_and_client_session` |

### Installation
```bash
uv add --dev pytest-asyncio
```

Note: `pytest`, `aiosqlite`, `mcp`, `pydantic` are already installed.

---

## Architecture Patterns

### Recommended Project Structure
```
src/novel/
├── mcp/
│   ├── __init__.py
│   ├── db.py              # get_connection() — already exists
│   └── server.py          # FastMCP instance + run() — already exists; add register() calls here
├── models/
│   ├── shared.py          # NotFoundResponse, ValidationFailure, GateViolation — already exists
│   ├── characters.py      # Character, CharacterKnowledge, etc. — already exists
│   └── relationships.py   # CharacterRelationship, etc. — already exists
└── tools/
    ├── __init__.py        # stays minimal — already exists
    ├── characters.py      # NEW: register(mcp) + 7 character tools
    └── relationships.py   # NEW: register(mcp) + 6 relationship tools

tests/
├── conftest.py            # NEW: async DB fixture + MCP server fixture
├── test_characters.py     # NEW: character tool tests
└── test_relationships.py  # NEW: relationship tool tests
```

### Pattern 1: Tool Module with register() Function

**What:** Each domain module defines tools as local async functions inside `register()` and decorates them with the passed-in `mcp.tool()` decorator.
**When to use:** Every tool module. The FastMCP instance is never imported from tools modules — always passed in.

```python
# Source: CONTEXT.md + mcp.server.fastmcp.FastMCP.tool() API
import logging
from mcp.server.fastmcp import FastMCP
from novel.mcp.db import get_connection
from novel.models.characters import Character
from novel.models.shared import NotFoundResponse, ValidationFailure

logger = logging.getLogger(__name__)


def register(mcp: FastMCP) -> None:
    """Register all character tools with the MCP server."""

    @mcp.tool()
    async def get_character(character_id: int) -> Character | NotFoundResponse:
        """Retrieve a character's full profile by ID."""
        async with get_connection() as conn:
            cursor = await conn.execute(
                "SELECT * FROM characters WHERE id = ?", (character_id,)
            )
            row = await cursor.fetchone()
        if row is None:
            return NotFoundResponse(
                not_found_message=f"Character {character_id} not found"
            )
        return Character(**dict(row))
```

### Pattern 2: aiosqlite Row-to-Model Mapping

**What:** `aiosqlite.Row` (which is `sqlite3.Row`) supports `dict(row)` to convert to a plain dict, then `Model(**dict(row))` to construct a Pydantic model.
**When to use:** Every tool that returns a single record.

```python
# Source: aiosqlite docs + sqlite3.Row behavior (Python 3.12+)
async with get_connection() as conn:
    cursor = await conn.execute("SELECT * FROM characters WHERE id = ?", (character_id,))
    row = await cursor.fetchone()

if row is None:
    return NotFoundResponse(not_found_message=f"Character {character_id} not found")

return Character(**dict(row))
```

For list results:
```python
async with get_connection() as conn:
    cursor = await conn.execute("SELECT * FROM characters ORDER BY name")
    rows = await cursor.fetchall()

return [Character(**dict(row)) for row in rows]
```

### Pattern 3: SQLite UPSERT (INSERT OR REPLACE / ON CONFLICT DO UPDATE)

**What:** SQLite supports two upsert forms. The safer form for partial updates is `ON CONFLICT DO UPDATE`.
**When to use:** `upsert_character`, `upsert_relationship`, `upsert_perception_profile`.

```python
# Source: SQLite documentation — ON CONFLICT DO UPDATE (SQLite 3.24+)
# For tables with UNIQUE constraints:
await conn.execute("""
    INSERT INTO character_relationships
        (character_a_id, character_b_id, relationship_type, bond_strength, trust_level, current_status, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
    ON CONFLICT(character_a_id, character_b_id) DO UPDATE SET
        relationship_type = excluded.relationship_type,
        bond_strength = excluded.bond_strength,
        trust_level = excluded.trust_level,
        current_status = excluded.current_status,
        updated_at = datetime('now')
""", (char_a_id, char_b_id, rel_type, bond, trust, status))
await conn.commit()
```

For characters (no UNIQUE constraint, upsert by ID):
```python
# INSERT with explicit id=None triggers AUTOINCREMENT; INSERT with id= updates
await conn.execute("""
    INSERT INTO characters (id, name, role, ..., updated_at)
    VALUES (?, ?, ?, ..., datetime('now'))
    ON CONFLICT(id) DO UPDATE SET
        name = excluded.name,
        role = excluded.role,
        ...
        updated_at = datetime('now')
""", (character_id_or_none, name, role, ...))
```

### Pattern 4: In-Memory MCP Testing

**What:** `create_connected_server_and_client_session` connects a real `ClientSession` to the FastMCP server over anyio memory streams. Tests call tools via `session.call_tool(name, args)` and check `result.content[0].text` (for JSON string payloads).
**When to use:** All MCP tool tests in `test_characters.py` and `test_relationships.py`.

```python
# Source: mcp/shared/memory.py — create_connected_server_and_client_session
import json
import pytest
import pytest_asyncio
import anyio
from mcp.shared.memory import create_connected_server_and_client_session
from novel.mcp.server import mcp  # the FastMCP instance

@pytest.mark.anyio
async def test_get_character(mcp_session):
    result = await mcp_session.call_tool("get_character", {"character_id": 1})
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["name"] == "Aeryn Vael"
```

**Critical detail:** `CallToolResult.content` is a `list[ContentBlock]`. For Pydantic model returns, FastMCP serializes them as JSON in a `TextContent` block. Access with `result.content[0].text`.

For `NotFoundResponse` returns, the same `result.content[0].text` will contain `{"not_found_message": "..."}`. The test must parse JSON and check for the key.

### Pattern 5: conftest.py — In-Memory DB Injection

**What:** The conftest patches `novel.mcp.db.get_connection` with an async context manager that returns a pre-seeded in-memory aiosqlite connection. This is the cleanest way to isolate tests from the filesystem.
**When to use:** All MCP tool tests require this fixture.

```python
# Source: design based on mcp/db.py structure and pytest-asyncio patterns
import sqlite3
import json
import pytest
import anyio
import aiosqlite
from contextlib import asynccontextmanager
from unittest.mock import patch

from novel.db.migrations import apply_migrations
from novel.db.seed import load_seed_profile
from novel.mcp.server import mcp
from mcp.shared.memory import create_connected_server_and_client_session


@pytest.fixture(scope="session")
def seed_db_path(tmp_path_factory):
    """Create a temp SQLite file with migrations + minimal seed for MCP tests."""
    db_path = tmp_path_factory.mktemp("db") / "test.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA journal_mode=WAL")
    apply_migrations(conn)
    load_seed_profile(conn, "minimal")
    conn.close()
    return str(db_path)


@pytest_asyncio.fixture
async def mcp_session(seed_db_path, monkeypatch):
    """Yield a ClientSession connected to the novel MCP server using the test DB."""
    monkeypatch.setenv("NOVEL_DB_PATH", seed_db_path)
    async with create_connected_server_and_client_session(mcp) as session:
        yield session
```

**Note on pure in-memory approach:** A pure `:memory:` aiosqlite DB cannot be shared across the `get_connection()` call boundary because each `aiosqlite.connect(":memory:")` opens a NEW independent database. Migrations and seed run in one connection object but every tool call opens a new one. The solution: use a temp file (session-scoped), which is still fast and disposable. The `tmp_path_factory` session fixture creates it once for the test session.

### Anti-Patterns to Avoid

- **Calling tools directly as functions:** `await get_character(1)` bypasses FastMCP's schema validation and type coercion. Always go through the MCP client.
- **Importing `mcp` from `novel.mcp.server` inside tool modules:** Creates circular imports. The FastMCP instance is always passed into `register(mcp)`.
- **Using `print()` anywhere in `novel/mcp/` or `novel/tools/`:** Corrupts stdio transport. Use `logging.getLogger(__name__)`.
- **Raising exceptions in tool handlers:** Return `NotFoundResponse` or `ValidationFailure` objects — never raise. FastMCP catches unhandled exceptions and returns `isError=True`, which breaks the error contract.
- **Using `fetchone()` without `conn.row_factory = aiosqlite.Row`:** The connection factory already sets `conn.row_factory = aiosqlite.Row`, so `dict(row)` works. Don't reset it in tool code.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| MCP protocol handling | Custom stdio message loop | `FastMCP.run(transport="stdio")` | Handles initialize, list_tools, call_tool protocol messages |
| Tool parameter schema | Manual JSON schema dicts | FastMCP auto-derives from type annotations | FastMCP calls `func_metadata()` and builds JSON schema from function signature |
| In-memory test transport | Custom socket/pipe code | `mcp.shared.memory.create_connected_server_and_client_session` | Bidirectional anyio memory streams wired to a real `ClientSession` |
| SQL UPSERT logic | Custom "check then insert or update" | SQLite `ON CONFLICT DO UPDATE` | Atomic, no race condition, requires SQLite 3.24+ (which macOS/Python ships) |
| Async test runner | `asyncio.run()` in test | `pytest-asyncio` with `@pytest.mark.anyio` or `asyncio_mode = "auto"` | FastMCP uses anyio internally; tests must use the same event loop backend |

**Key insight:** FastMCP handles all MCP wire protocol details. Tool functions only need to do: validate inputs, query DB, return Pydantic model or error response.

---

## Common Pitfalls

### Pitfall 1: In-Memory SQLite Isolation Failure
**What goes wrong:** `aiosqlite.connect(":memory:")` opens a fresh empty database on every call. The test conftest seeds a connection, but each tool invocation calls `get_connection()` which opens ANOTHER `:memory:` connection — seeing an empty database.
**Why it happens:** SQLite `:memory:` databases are per-connection. There is no shared in-memory database across connections (without the `file::memory:?cache=shared` URI trick, which has its own concurrency issues).
**How to avoid:** Use a temp file (via `tmp_path_factory`) as the test database. Session-scoped fixture creates it once; all tool invocations in the test session read from the same file.
**Warning signs:** Tools return `NotFoundResponse` for records that were seeded; tests pass in isolation but fail together.

### Pitfall 2: pytest-asyncio / anyio Mode Mismatch
**What goes wrong:** `async def test_*` functions fail with `RuntimeError: no event loop` or `PytestUnraisableExceptionWarning` when the async backend doesn't match FastMCP's anyio usage.
**Why it happens:** `pytest-asyncio` defaults to strict mode (requires explicit `@pytest.mark.asyncio`). FastMCP uses anyio which supports both asyncio and trio backends.
**How to avoid:** Add `asyncio_mode = "auto"` to `pyproject.toml` under `[tool.pytest.ini_options]`, or use `@pytest.mark.anyio` on each async test.
**Warning signs:** `pytest.PytestUnraisableExceptionWarning: Exception ignored in...` or coroutine-never-awaited warnings.

### Pitfall 3: `dict(row)` Pydantic Coercion Failures
**What goes wrong:** `Character(**dict(row))` raises `ValidationError` because SQLite returns integers for boolean columns (`is_secret INTEGER` → `1/0`), but Pydantic v2 expects `bool`. Or timestamp columns that are `NOT NULL DEFAULT (datetime('now'))` come back as `str` but the model has `str | None`.
**Why it happens:** Pydantic v2 coerces `int` → `bool` correctly, so boolean fields are fine. The real risk is `NOT NULL DEFAULT` columns that always have values (no `None`) conflicting with `str | None` model annotations — this is actually fine, Pydantic accepts non-None for `str | None` fields. The one gotcha: fields in the model but not in `SELECT *` results (can't happen with `SELECT *` but possible with selective queries).
**How to avoid:** Always use `SELECT *` for full record fetches; only use column-specific queries for list/filter operations. Verify model coverage against `PRAGMA table_info` (already done by TEST-01 in Phase 2).
**Warning signs:** `pydantic.ValidationError` on `Character(**dict(row))` — inspect which field triggered it.

### Pitfall 4: Tool Return Type Annotation Required for Structured Output
**What goes wrong:** Tools that return `Character | NotFoundResponse` work fine. But if the return type annotation is missing, FastMCP may not serialize the Pydantic model to JSON correctly — or may wrap it in unexpected `TextContent` structure.
**Why it happens:** FastMCP auto-detects `structured_output` based on the return type annotation. Without annotation, behavior is undefined.
**How to avoid:** Always annotate the return type on tool functions: `async def get_character(...) -> Character | NotFoundResponse:`.
**Warning signs:** `result.content` is an unexpected type; `json.loads(result.content[0].text)` raises `JSONDecodeError`.

### Pitfall 5: Relationship Symmetry — A↔B Order
**What goes wrong:** `get_relationship(character_a_id=1, character_b_id=2)` returns `NotFoundResponse` because the relationship is stored as `(character_a_id=2, character_b_id=1)` in the database. The UNIQUE constraint is on the ordered pair.
**Why it happens:** `character_relationships` has `UNIQUE(character_a_id, character_b_id)` — order matters. The seed data inserts all relationships with protagonist as `character_a_id`.
**How to avoid:** `get_relationship` must query both orderings: `WHERE (character_a_id=? AND character_b_id=?) OR (character_a_id=? AND character_b_id=?)`. `upsert_relationship` should canonicalize the pair (e.g., always store with lower ID as `character_a_id`) or document that callers must pass in the canonical order.
**Warning signs:** `get_relationship` returns `NotFoundResponse` for a relationship that exists; test fails on reverse-order lookup.

### Pitfall 6: `commit()` Required After Write Operations
**What goes wrong:** `INSERT` or `UPDATE` executes without error but the record is not visible to subsequent reads within the same test.
**Why it happens:** aiosqlite does not auto-commit by default (it uses `isolation_level=''` which means manual transaction control for DML).
**How to avoid:** Call `await conn.commit()` after every write operation in tool handlers. Do NOT rely on the context manager exit to commit — aiosqlite rolls back uncommitted transactions on close.
**Warning signs:** Write tool returns successfully but subsequent read tool returns `NotFoundResponse` for the newly created record.

---

## Code Examples

### Complete Tool Module: characters.py skeleton
```python
# Source: mcp.server.fastmcp.FastMCP API + novel project patterns
import logging
from mcp.server.fastmcp import FastMCP
from novel.mcp.db import get_connection
from novel.models.characters import (
    Character, CharacterKnowledge, CharacterBelief,
    CharacterLocation, InjuryState
)
from novel.models.shared import NotFoundResponse, ValidationFailure

logger = logging.getLogger(__name__)


def register(mcp: FastMCP) -> None:
    """Register character domain tools."""

    @mcp.tool()
    async def get_character(character_id: int) -> Character | NotFoundResponse:
        """Retrieve a character's full profile by ID."""
        async with get_connection() as conn:
            cursor = await conn.execute(
                "SELECT * FROM characters WHERE id = ?", (character_id,)
            )
            row = await cursor.fetchone()
        if row is None:
            return NotFoundResponse(
                not_found_message=f"Character with id={character_id} not found"
            )
        return Character(**dict(row))

    @mcp.tool()
    async def list_characters() -> list[Character]:
        """List all characters ordered by name."""
        async with get_connection() as conn:
            cursor = await conn.execute("SELECT * FROM characters ORDER BY name")
            rows = await cursor.fetchall()
        return [Character(**dict(row)) for row in rows]

    @mcp.tool()
    async def get_character_injuries(
        character_id: int,
        chapter_id: int | None = None,
    ) -> list[InjuryState] | NotFoundResponse:
        """Retrieve injury history for a character, optionally scoped to a chapter."""
        async with get_connection() as conn:
            # Verify character exists
            char_row = await (await conn.execute(
                "SELECT id FROM characters WHERE id = ?", (character_id,)
            )).fetchone()
            if char_row is None:
                return NotFoundResponse(
                    not_found_message=f"Character {character_id} not found"
                )
            if chapter_id is not None:
                cursor = await conn.execute(
                    "SELECT * FROM injury_states WHERE character_id = ? AND chapter_id <= ? ORDER BY chapter_id DESC",
                    (character_id, chapter_id),
                )
            else:
                cursor = await conn.execute(
                    "SELECT * FROM injury_states WHERE character_id = ? ORDER BY chapter_id DESC",
                    (character_id,),
                )
            rows = await cursor.fetchall()
        return [InjuryState(**dict(row)) for row in rows]
```

### server.py: Adding register() calls
```python
# Source: CONTEXT.md + novel.mcp.server pattern
from mcp.server.fastmcp import FastMCP
from novel.tools import characters, relationships  # NEW in Phase 3

mcp = FastMCP("novel-mcp")

# Register domain tools — Phase 3
characters.register(mcp)
relationships.register(mcp)
# Phase 4+ will add: chapters.register(mcp); world.register(mcp); etc.
```

### conftest.py: Session-scoped test DB + MCP client fixture
```python
# Source: mcp.shared.memory + pytest-asyncio patterns
import json
import sqlite3
import pytest
import pytest_asyncio
from mcp.shared.memory import create_connected_server_and_client_session
from novel.db.migrations import apply_migrations
from novel.db.seed import load_seed_profile
from novel.mcp.server import mcp


@pytest.fixture(scope="session")
def test_db_path(tmp_path_factory):
    """Create a temp SQLite file with migrations + minimal seed, reused for all tests."""
    db_file = tmp_path_factory.mktemp("db") / "test_mcp.db"
    conn = sqlite3.connect(str(db_file))
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA journal_mode=WAL")
    apply_migrations(conn)
    load_seed_profile(conn, "minimal")
    conn.commit()
    conn.close()
    return str(db_file)


@pytest_asyncio.fixture
async def mcp_session(test_db_path, monkeypatch):
    """Yield a ClientSession connected to novel MCP server using the test DB."""
    monkeypatch.setenv("NOVEL_DB_PATH", test_db_path)
    async with create_connected_server_and_client_session(mcp) as session:
        yield session
```

### test_characters.py: Sample tests
```python
# Source: mcp.client.session.ClientSession.call_tool + CallToolResult structure
import json
import pytest

pytestmark = pytest.mark.anyio


async def test_get_character_found(mcp_session):
    result = await mcp_session.call_tool("get_character", {"character_id": 1})
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["name"] == "Aeryn Vael"
    assert "id" in data


async def test_get_character_not_found(mcp_session):
    result = await mcp_session.call_tool("get_character", {"character_id": 9999})
    assert not result.isError  # not an MCP protocol error
    data = json.loads(result.content[0].text)
    assert "not_found_message" in data


async def test_list_characters(mcp_session):
    result = await mcp_session.call_tool("list_characters", {})
    assert not result.isError
    characters = json.loads(result.content[0].text)
    assert isinstance(characters, list)
    assert len(characters) >= 5  # minimal seed has 5 characters
```

### pyproject.toml: asyncio_mode setting
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Standalone `fastmcp` PyPI package | `mcp.server.fastmcp` (bundled in `mcp` SDK) | After mcp 1.0 | Must use bundled version — packages have diverged |
| `asyncio.run()` in tests | `pytest-asyncio` + `anyio` | Standard since FastMCP adopted anyio | Tests must use `@pytest.mark.anyio` or `asyncio_mode = "auto"` |
| `conn.execute("INSERT OR REPLACE")` | `INSERT ... ON CONFLICT DO UPDATE SET` | SQLite 3.24 (2018) | Partial update without touching unspecified columns |

**Deprecated/outdated:**
- Standalone `fastmcp` PyPI package: do NOT install `fastmcp` from PyPI — use `mcp.server.fastmcp` from the installed `mcp` package.
- `pytest.mark.asyncio` (from pytest-asyncio): works, but project uses anyio; `pytest.mark.anyio` is more portable.

---

## Open Questions

1. **CHAR-02 tool name mismatch**
   - What we know: REQUIREMENTS.md says `get_character_state`, but CONTEXT.md lists separate state tools (`get_character_injuries`, `get_character_knowledge`, etc.)
   - What's unclear: Is CHAR-02 satisfied by registering all 4 separate state tools, or is there a single `get_character_state` wrapper that calls all 4?
   - Recommendation: Implement as 4 separate tools (matching CONTEXT.md decisions) — they satisfy the requirement that "Claude can retrieve character state at a given chapter". The planner should map CHAR-02 → `get_character_injuries + get_character_knowledge + get_character_beliefs + get_character_location`.

2. **`upsert_character` vs `create_character` + `update_character`**
   - What we know: REQUIREMENTS.md says `upsert_character`; CONTEXT.md lists both `create_character` and `update_character` in the tool naming convention
   - What's unclear: Are these two separate tools or one `upsert_character`?
   - Recommendation: Implement `upsert_character(character_id: int | None, ...)` — `None` means create, non-None means update. This maps cleanly to SQLite's `ON CONFLICT(id)` upsert and satisfies CHAR-04.

3. **`get_relationship` symmetry canonical form**
   - What we know: `UNIQUE(character_a_id, character_b_id)` is order-sensitive; seed inserts with protagonist as `character_a_id`
   - What's unclear: Should `upsert_relationship` enforce canonical ordering (lower ID first)?
   - Recommendation: Have `get_relationship` query both orderings; have `upsert_relationship` enforce canonical ordering (min(a,b) as `character_a_id`) to avoid duplicate relationships.

4. **pytest-asyncio anyio backend**
   - What we know: FastMCP uses anyio; `create_connected_server_and_client_session` uses `anyio.create_task_group`
   - What's unclear: Whether `asyncio_mode = "auto"` in pytest.ini is sufficient or if `anyio_backend = "asyncio"` fixture is also needed
   - Recommendation: Add `pytest-anyio` or configure `anyio_backend` fixture in conftest. Test by running `uv run pytest tests/test_characters.py -v` early in the task wave.

---

## Sources

### Primary (HIGH confidence)
- `/Users/gary/writing/drafter/.venv/lib/python3.13/site-packages/mcp/shared/memory.py` — `create_connected_server_and_client_session` implementation confirmed
- `/Users/gary/writing/drafter/.venv/lib/python3.13/site-packages/mcp/server/fastmcp/server.py` — `FastMCP.tool()` decorator API, `call_tool` method confirmed
- `/Users/gary/writing/drafter/.venv/lib/python3.13/site-packages/mcp/client/session.py` — `ClientSession.call_tool()` returns `CallToolResult` confirmed
- `/Users/gary/writing/drafter/.venv/lib/python3.13/site-packages/mcp/types.py` — `CallToolResult.content: list[ContentBlock]`, `isError: bool` confirmed
- `/Users/gary/writing/drafter/src/novel/mcp/db.py` — `get_connection()` reads `NOVEL_DB_PATH` env var, sets `row_factory = aiosqlite.Row`
- `/Users/gary/writing/drafter/src/novel/mcp/server.py` — `mcp = FastMCP("novel-mcp")` instance; `run()` entry point exists
- `/Users/gary/writing/drafter/src/novel/models/shared.py` — `NotFoundResponse`, `ValidationFailure`, `GateViolation` models confirmed
- `/Users/gary/writing/drafter/src/novel/models/characters.py` — All character models confirmed with exact field names
- `/Users/gary/writing/drafter/src/novel/models/relationships.py` — All relationship models confirmed with exact field names
- `/Users/gary/writing/drafter/src/novel/migrations/012_relationships.sql` — `UNIQUE(character_a_id, character_b_id)` and `UNIQUE(observer_id, subject_id)` constraints confirmed
- `/Users/gary/writing/drafter/src/novel/migrations/013_character_state.sql` — `character_knowledge`, `character_beliefs`, `character_locations`, `injury_states` schema confirmed
- `/Users/gary/writing/drafter/src/novel/db/seed.py` — `load_seed_profile(conn, "minimal")` signature confirmed; seed is sync sqlite3

### Secondary (MEDIUM confidence)
- `mcp` package version 1.26.0 confirmed via `uv.lock`
- `pytest-asyncio` + `anyio_mode` configuration: standard pattern, needs early-wave validation

### Tertiary (LOW confidence)
- `dict(row)` as the idiomatic conversion for `sqlite3.Row` / `aiosqlite.Row` — consistent with Python docs, but confirm by running a quick test

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries are installed and verified from source
- Architecture patterns: HIGH — all patterns verified against actual installed source files
- Pitfalls: HIGH — most derived from actual code inspection (e.g., in-memory isolation from `_get_db_path()` reading env var; UNIQUE constraint order from migration SQL)
- Test strategy: MEDIUM — `create_connected_server_and_client_session` is confirmed in source; exact pytest-asyncio/anyio config needs validation by running tests early

**Research date:** 2026-03-07
**Valid until:** 2026-04-07 (stable library versions locked in uv.lock)
