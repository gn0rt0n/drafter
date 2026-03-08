"""In-memory MCP client tests for foreshadowing domain tools.

CRITICAL: Uses 'gate_ready' seed (NOT 'minimal') — all foreshadowing tools are
prose-phase tools that call check_gate, which requires the gate to be certified.
The gate_ready seed has the data required to pass all 34 gate SQL checks.

Total foreshadowing tools: 8
  get_foreshadowing, get_prophecies, get_motifs, get_motif_occurrences,
  get_thematic_mirrors, get_opposition_pairs, log_foreshadowing, log_motif_occurrence

Tests verify the full MCP protocol path: call_tool -> FastMCP -> tool handler -> SQLite -> response.
MCP session is entered PER-TEST inside _call_tool — anyio cancel scope incompatible with fixtures.

FastMCP serialization rules:
  - Single object: json.loads(result.content[0].text)
  - list[T]: [json.loads(c.text) for c in result.content]
  - Empty list: result.content is empty (no TextContent blocks)

Single-object tools: log_foreshadowing, log_motif_occurrence
List tools: get_foreshadowing, get_prophecies, get_motifs, get_motif_occurrences,
            get_thematic_mirrors, get_opposition_pairs

Seed data (gate_ready):
  - foreshadowing_registry: 1 row (status='planted', plant_chapter_id=1)
  - prophecy_registry: 1 row (status='active')
  - motif_registry: 1 row (name='Dying Embers', id=1)
  - motif_occurrences: 1 row (motif_id=1, chapter_id=1)
  - thematic_mirrors: 1 row
  - opposition_pairs: 1 row
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
    Uses "foreshadowing_db" dir to isolate from other test files.

    The gate_ready seed ensures:
    - Gate is certifiable (all 34 SQL gate checks pass)
    - Foreshadowing seed data populated in all 6 foreshadowing tables
    """
    db_file = tmp_path_factory.mktemp("foreshadowing_db") / "test_foreshadowing.db"
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
    """Call a foreshadowing tool via MCP in-memory protocol.

    Opens and closes session inside this coroutine so anyio cancel scopes
    are entered and exited in the same task context.
    """
    os.environ["NOVEL_DB_PATH"] = db_path
    async with create_connected_server_and_client_session(mcp) as session:
        return await session.call_tool(tool_name, args)


# ---------------------------------------------------------------------------
# Helper: certify gate before foreshadowing tools can run
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session", autouse=True)
def certified_gate(test_db_path):
    """Certify the gate once for the entire session before any foreshadowing tool tests run.

    Session-scoped autouse ensures gate is certified before any test in this
    file runs. Without certification, all foreshadowing tools return GateViolation.

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
# Tests: get_foreshadowing
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_get_foreshadowing(test_db_path):
    """get_foreshadowing returns foreshadowing entries; status filter works.

    Seed has 1 entry with status='planted'. Verify:
    - Unfiltered: at least 1 item
    - status='planted': items have status='planted'
    """
    result = await _call_tool(test_db_path, "get_foreshadowing", {})
    assert not result.isError
    items = [json.loads(c.text) for c in result.content]
    assert isinstance(items, list)
    assert len(items) >= 1

    # Filtered by status='planted'
    result2 = await _call_tool(
        test_db_path, "get_foreshadowing", {"status": "planted"}
    )
    assert not result2.isError
    planted = [json.loads(c.text) for c in result2.content]
    for item in planted:
        assert item["status"] == "planted"


# ---------------------------------------------------------------------------
# Tests: get_prophecies
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_get_prophecies(test_db_path):
    """get_prophecies returns all prophecy registry entries.

    Seed has 1 active prophecy. Verify list has at least 1 item.
    """
    result = await _call_tool(test_db_path, "get_prophecies", {})
    assert not result.isError
    items = [json.loads(c.text) for c in result.content]
    assert isinstance(items, list)
    assert len(items) >= 1


# ---------------------------------------------------------------------------
# Tests: get_motifs
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_get_motifs(test_db_path):
    """get_motifs returns all motif registry entries.

    Seed has 1 motif ('Dying Embers', id=1). Verify list has at least 1 item.
    """
    result = await _call_tool(test_db_path, "get_motifs", {})
    assert not result.isError
    items = [json.loads(c.text) for c in result.content]
    assert isinstance(items, list)
    assert len(items) >= 1


# ---------------------------------------------------------------------------
# Tests: get_motif_occurrences
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_get_motif_occurrences(test_db_path):
    """get_motif_occurrences returns occurrences; chapter_id filter works.

    Seed has 1 occurrence (motif_id=1, chapter_id=1).
    - Unfiltered: at least 1 item
    - chapter_id=999: empty list
    """
    result = await _call_tool(test_db_path, "get_motif_occurrences", {})
    assert not result.isError
    items = [json.loads(c.text) for c in result.content]
    assert isinstance(items, list)
    assert len(items) >= 1

    # Nonexistent chapter: empty
    result2 = await _call_tool(
        test_db_path, "get_motif_occurrences", {"chapter_id": 999}
    )
    assert not result2.isError
    empty = [json.loads(c.text) for c in result2.content]
    assert empty == []


# ---------------------------------------------------------------------------
# Tests: get_thematic_mirrors
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_get_thematic_mirrors(test_db_path):
    """get_thematic_mirrors returns all thematic mirror pairs.

    Seed has 1 thematic mirror. Verify list has at least 1 item.
    """
    result = await _call_tool(test_db_path, "get_thematic_mirrors", {})
    assert not result.isError
    items = [json.loads(c.text) for c in result.content]
    assert isinstance(items, list)
    assert len(items) >= 1


# ---------------------------------------------------------------------------
# Tests: get_opposition_pairs
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_get_opposition_pairs(test_db_path):
    """get_opposition_pairs returns all opposition pairs.

    Seed has 1 opposition pair. Verify list has at least 1 item.
    """
    result = await _call_tool(test_db_path, "get_opposition_pairs", {})
    assert not result.isError
    items = [json.loads(c.text) for c in result.content]
    assert isinstance(items, list)
    assert len(items) >= 1


# ---------------------------------------------------------------------------
# Tests: log_foreshadowing (insert)
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_log_foreshadowing_insert(test_db_path):
    """log_foreshadowing creates a new foreshadowing entry (None-id branch).

    Verifies the returned object has an id and default status='planted'.
    """
    result = await _call_tool(
        test_db_path,
        "log_foreshadowing",
        {"description": "Crow on windowsill", "plant_chapter_id": 1},
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "id" in data
    assert data["id"] is not None
    assert data["status"] == "planted"
    assert data["description"] == "Crow on windowsill"


# ---------------------------------------------------------------------------
# Tests: log_foreshadowing (update / upsert)
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_log_foreshadowing_update(test_db_path):
    """log_foreshadowing upserts an existing entry when foreshadowing_id is provided.

    First inserts a new entry (getting its id), then updates with payoff_chapter_id=5
    and status='paid_off'. Verifies the returned object has the updated values.
    """
    # Insert first
    insert_result = await _call_tool(
        test_db_path,
        "log_foreshadowing",
        {"description": "Raven feather left on doorstep", "plant_chapter_id": 2},
    )
    assert not insert_result.isError
    insert_data = json.loads(insert_result.content[0].text)
    entry_id = insert_data["id"]

    # Update with payoff info — use chapter_id=3 (exists in gate_ready seed)
    result = await _call_tool(
        test_db_path,
        "log_foreshadowing",
        {
            "foreshadowing_id": entry_id,
            "description": "Raven feather left on doorstep",
            "plant_chapter_id": 2,
            "payoff_chapter_id": 3,
            "status": "paid_off",
        },
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["payoff_chapter_id"] == 3
    assert data["status"] == "paid_off"
    assert data["id"] == entry_id


# ---------------------------------------------------------------------------
# Tests: log_motif_occurrence
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_log_motif_occurrence(test_db_path):
    """log_motif_occurrence creates a new motif occurrence (append-only).

    Uses motif_id=1 (seed 'Dying Embers' motif). Verifies the returned object
    has the correct motif_id and chapter_id.
    """
    result = await _call_tool(
        test_db_path,
        "log_motif_occurrence",
        {
            "motif_id": 1,
            "chapter_id": 2,
            "description": "Crow motif recurs",
        },
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["motif_id"] == 1
    assert data["chapter_id"] == 2
    assert data["description"] == "Crow motif recurs"


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
async def test_get_foreshadowing_gate_violation(uncertified_db_path):
    """get_foreshadowing returns requires_action when gate is uncertified.

    Uses a fresh DB with no gate certification. All foreshadowing tools call check_gate,
    which must return a GateViolation response (not raise an error).
    """
    result = await _call_tool(uncertified_db_path, "get_foreshadowing", {})
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "requires_action" in data
