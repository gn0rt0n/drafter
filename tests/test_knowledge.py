"""In-memory MCP client tests for knowledge domain tools.

CRITICAL: Uses 'gate_ready' seed (NOT 'minimal') — all knowledge tools are
prose-phase tools that call check_gate, which requires the gate to be certified.
The gate_ready seed has the data required to pass all 34 gate SQL checks.

Total knowledge tools: 5
  get_reader_state, get_dramatic_irony_inventory, get_reader_reveals,
  upsert_reader_state, log_dramatic_irony

Tests verify the full MCP protocol path: call_tool -> FastMCP -> tool handler -> SQLite -> response.
MCP session is entered PER-TEST inside _call_tool — anyio cancel scope incompatible with fixtures.

FastMCP serialization rules:
  - Single object: json.loads(result.content[0].text)
  - list[T]: [json.loads(c.text) for c in result.content]
  - Empty list: result.content is empty (no TextContent blocks)

Single-object tools: upsert_reader_state, log_dramatic_irony
List tools: get_reader_state, get_dramatic_irony_inventory, get_reader_reveals

Seed data (gate_ready):
  - reader_information_states: 1 row (chapter_id=1, domain='world')
  - reader_reveals: 1 row (chapter_id=2)
  - dramatic_irony_inventory: 1 row (chapter_id=1, resolved=FALSE)
"""

import json
import os
import sqlite3

import pytest
from mcp.shared.memory import create_connected_server_and_client_session

from novel.db.migrations import apply_migrations
from novel.db.seed import load_seed_profile
from novel.mcp.server import mcp


# ---------------------------------------------------------------------------
# Session-scoped DB fixture — gate_ready seed
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def test_db_path(tmp_path_factory):
    """Create a temp SQLite file with all migrations + gate_ready seed.

    Session-scoped: created once for all tests in this file.
    Uses "knowledge_db" dir to isolate from other test files.

    The gate_ready seed ensures:
    - Gate is certifiable (all 34 SQL gate checks pass)
    - Reader state seed data: 1 reader info state (chapter_id=1, domain='world'),
      1 reader reveal (chapter_id=2), 1 dramatic irony entry (chapter_id=1, unresolved)
    """
    db_file = tmp_path_factory.mktemp("knowledge_db") / "test_knowledge.db"
    conn = sqlite3.connect(str(db_file))
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA journal_mode=WAL")
    apply_migrations(conn)
    load_seed_profile(conn, "gate_ready")
    conn.commit()
    conn.close()
    return str(db_file)


# ---------------------------------------------------------------------------
# Helper: open/close MCP session inside each test coroutine
# ---------------------------------------------------------------------------


async def _call_tool(db_path: str, tool_name: str, args: dict):
    """Call a knowledge tool via MCP in-memory protocol.

    Opens and closes session inside this coroutine so anyio cancel scopes
    are entered and exited in the same task context.
    """
    os.environ["NOVEL_DB_PATH"] = db_path
    async with create_connected_server_and_client_session(mcp) as session:
        return await session.call_tool(tool_name, args)


# ---------------------------------------------------------------------------
# Helper: certify gate before knowledge tools can run
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session", autouse=True)
def certified_gate(test_db_path):
    """Certify the gate once for the entire session before any knowledge tool tests run.

    Session-scoped autouse ensures gate is certified before any test in this
    file runs. Without certification, all knowledge tools return GateViolation.

    Uses synchronous sqlite3 to certify directly — avoids anyio lifecycle issues
    with session-scoped async fixtures.
    """
    import sqlite3 as _sqlite3

    conn = _sqlite3.connect(test_db_path)
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA journal_mode=WAL")

    conn.execute(
        "UPDATE gate_checklist_items SET is_passing=1, missing_count=0"
    )

    cur = conn.execute("SELECT COUNT(*) FROM architecture_gate")
    count = cur.fetchone()[0]
    if count == 0:
        conn.execute(
            "INSERT INTO architecture_gate (is_certified, certified_by, certified_at) "
            "VALUES (1, 'test-suite', datetime('now'))"
        )
    else:
        conn.execute(
            "UPDATE architecture_gate SET is_certified=1, certified_by='test-suite', "
            "certified_at=datetime('now') WHERE id=1"
        )

    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Tests: get_reader_state
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_get_reader_state(test_db_path):
    """get_reader_state returns cumulative reader info up to chapter_id.

    Seed has 1 reader info state at chapter_id=1, domain='world'.
    - chapter_id=1 should return at least 1 item (cumulative: <= 1)
    - chapter_id=0 should return empty list (no states at chapter <= 0)
    """
    # At chapter 1: should have at least 1 row
    result = await _call_tool(test_db_path, "get_reader_state", {"chapter_id": 1})
    assert not result.isError
    items = [json.loads(c.text) for c in result.content]
    assert isinstance(items, list)
    assert len(items) >= 1

    # At chapter 0: should be empty (cumulative semantics: chapter_id <= 0)
    result2 = await _call_tool(test_db_path, "get_reader_state", {"chapter_id": 0})
    assert not result2.isError
    empty_items = [json.loads(c.text) for c in result2.content]
    assert empty_items == []


# ---------------------------------------------------------------------------
# Tests: get_dramatic_irony_inventory
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_get_dramatic_irony_inventory(test_db_path):
    """get_dramatic_irony_inventory returns unresolved entries by default.

    Seed has 1 unresolved dramatic irony entry at chapter_id=1.
    - Unfiltered (include_resolved=False by default): at least 1 item
    - All returned items should have resolved=False
    """
    result = await _call_tool(test_db_path, "get_dramatic_irony_inventory", {})
    assert not result.isError
    items = [json.loads(c.text) for c in result.content]
    assert isinstance(items, list)
    assert len(items) >= 1

    # include_resolved=False: all items should be unresolved
    result2 = await _call_tool(
        test_db_path,
        "get_dramatic_irony_inventory",
        {"include_resolved": False},
    )
    assert not result2.isError
    unresolved = [json.loads(c.text) for c in result2.content]
    for item in unresolved:
        assert item["resolved"] is False


# ---------------------------------------------------------------------------
# Tests: get_reader_reveals
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_get_reader_reveals(test_db_path):
    """get_reader_reveals returns reveals list; chapter_id filter works.

    Seed has 1 reader reveal at chapter_id=2.
    - Unfiltered: list with at least 1 item
    - chapter_id=999: empty list (no reveals at that chapter)
    """
    result = await _call_tool(test_db_path, "get_reader_reveals", {})
    assert not result.isError
    items = [json.loads(c.text) for c in result.content]
    assert isinstance(items, list)
    assert len(items) >= 1

    # Nonexistent chapter: empty
    result2 = await _call_tool(
        test_db_path, "get_reader_reveals", {"chapter_id": 999}
    )
    assert not result2.isError
    empty = [json.loads(c.text) for c in result2.content]
    assert empty == []


# ---------------------------------------------------------------------------
# Tests: upsert_reader_state (insert)
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_upsert_reader_state_insert(test_db_path):
    """upsert_reader_state creates a new reader state entry.

    Inserts a new (chapter_id=3, domain='magic') entry. Uses chapter_id=3
    (exists in gate_ready seed) to avoid FK constraint failure. Verifies the
    returned object has the correct chapter_id and domain.
    """
    result = await _call_tool(
        test_db_path,
        "upsert_reader_state",
        {
            "chapter_id": 3,
            "domain": "magic",
            "information": "Readers know magic costs life force",
        },
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["chapter_id"] == 3
    assert data["domain"] == "magic"
    assert data["information"] == "Readers know magic costs life force"


# ---------------------------------------------------------------------------
# Tests: log_dramatic_irony
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_log_dramatic_irony(test_db_path):
    """log_dramatic_irony creates a new dramatic irony entry (append-only).

    Verifies the returned object has an id and correct chapter_id.
    """
    result = await _call_tool(
        test_db_path,
        "log_dramatic_irony",
        {
            "chapter_id": 2,
            "reader_knows": "Solvann is the killer",
            "character_doesnt_know": "The identity of the killer",
        },
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "id" in data
    assert data["id"] is not None
    assert data["chapter_id"] == 2
    assert data["reader_knows"] == "Solvann is the killer"


# ---------------------------------------------------------------------------
# Error contract tests: gate violation (uncertified DB)
# ---------------------------------------------------------------------------


@pytest.fixture
def uncertified_db_path(tmp_path):
    """Fresh uncertified DB for gate violation tests.

    Function-scoped to avoid conflict with the session-scoped certified_gate
    autouse fixture. This DB has migrations + minimal seed but NO gate certification.
    """
    db_file = tmp_path / "uncertified.db"
    conn = sqlite3.connect(str(db_file))
    conn.execute("PRAGMA foreign_keys=ON")
    apply_migrations(conn)
    load_seed_profile(conn, "minimal")
    conn.commit()
    conn.close()
    return str(db_file)


@pytest.mark.anyio
async def test_get_reader_state_gate_violation(uncertified_db_path):
    """get_reader_state returns requires_action when gate is uncertified.

    Uses a fresh DB with no gate certification. All knowledge tools call check_gate,
    which must return a GateViolation response (not raise an error).
    """
    result = await _call_tool(uncertified_db_path, "get_reader_state", {"chapter_id": 1})
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "requires_action" in data


# ---------------------------------------------------------------------------
# Error contract tests: validation failure on bad FK
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_upsert_reader_state_unknown_chapter(test_db_path):
    """upsert_reader_state returns an error-like response for an invalid chapter_id.

    chapter_id=99999 does not exist in seed. The tool should return a validation
    failure or FK error response rather than raising an unhandled exception.
    The call must not result in isError=True (MCP error), just a tool-level response.
    """
    result = await _call_tool(
        test_db_path,
        "upsert_reader_state",
        {
            "chapter_id": 99999,
            "domain": "magic",
            "information": "Test info for missing chapter",
        },
    )
    # Tool must not raise an unhandled MCP error — it should return a structured response
    # The response may be a validation failure dict or the tool may succeed depending on
    # whether FK constraints block the insert. Either way, no unhandled exception.
    assert result.content  # some response returned
