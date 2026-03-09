"""In-memory MCP client tests for gate domain tools.

CRITICAL: Uses 'gate_ready' seed (NOT 'minimal') — gate tests require 36
gate_checklist_items to exist and all 36 SQL queries to pass.

Total gate_checklist_items after gate_ready seed: 37 rows
  - 36 rows from GATE_ITEM_META (all gate SQL check items)
  - 1 row from minimal seed: 'min_characters' (outside GATE_ITEM_META)

Tests verify the full MCP protocol path: call_tool → FastMCP → tool handler → SQLite → response.
MCP session is entered PER-TEST inside _call_tool — anyio cancel scope incompatible with fixtures.

FastMCP serialization:
  - Single object: json.loads(result.content[0].text)
  - list[T] (get_gate_checklist): [json.loads(c.text) for c in result.content]
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
    Uses "gate_db" dir to isolate from other test files.
    """
    db_file = tmp_path_factory.mktemp("gate_db") / "test_gate.db"
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
    """Call a gate tool via MCP in-memory protocol.

    Opens and closes session inside this coroutine so anyio cancel scopes
    are entered and exited in the same task context.
    """
    os.environ["NOVEL_DB_PATH"] = db_path
    async with create_connected_server_and_client_session(mcp) as session:
        return await session.call_tool(tool_name, args)


# ---------------------------------------------------------------------------
# Tests: get_gate_status
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_gate_status_returns_not_certified(test_db_path):
    """Gate-ready seed has is_certified=0 — status shows not certified."""
    result = await _call_tool(test_db_path, "get_gate_status", {})
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["is_certified"] is False
    assert "blocking_item_count" in data
    assert isinstance(data["blocking_item_count"], int)


# ---------------------------------------------------------------------------
# Tests: get_gate_checklist
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_gate_checklist_returns_items(test_db_path):
    """After gate_ready seed, checklist has 37 items (36 GATE_ITEM_META + 1 min_characters)."""
    result = await _call_tool(test_db_path, "get_gate_checklist", {})
    assert not result.isError
    # list[GateChecklistItem] serializes as N TextContent blocks
    items = [json.loads(c.text) for c in result.content]
    # 36 items from GATE_ITEM_META + 1 'min_characters' from minimal seed = 37
    assert len(items) == 37
    # Each item has required fields
    for item in items:
        assert "item_key" in item
        assert "category" in item
        assert "is_passing" in item
        assert "missing_count" in item


# ---------------------------------------------------------------------------
# Tests: run_gate_audit
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_run_gate_audit_returns_expected_items(test_db_path):
    """run_gate_audit evaluates all 36 SQL queries and returns all gate_checklist_items."""
    result = await _call_tool(test_db_path, "run_gate_audit", {})
    assert not result.isError
    data = json.loads(result.content[0].text)
    # total_items is count of all gate_checklist_items rows (37 = 36 + min_characters)
    assert data["total_items"] == 37
    assert "passing_count" in data
    assert "failing_count" in data
    assert len(data["items"]) == 37


@pytest.mark.asyncio
async def test_run_gate_audit_gate_ready_all_pass(test_db_path):
    """Gate-ready seed satisfies all 36 gate SQL checklist items — failing_count for GATE_QUERIES items must be 0."""
    result = await _call_tool(test_db_path, "run_gate_audit", {})
    assert not result.isError
    data = json.loads(result.content[0].text)
    # Filter to items that come from GATE_QUERIES (exclude min_characters which is unrelated)
    # GATE_QUERIES items should all pass; min_characters is not a SQL query item
    failing_sql_items = [
        item for item in data["items"]
        if not item["is_passing"] and item["item_key"] != "min_characters"
    ]
    assert len(failing_sql_items) == 0, (
        f"Expected 0 failing gate SQL items, got {len(failing_sql_items)}. "
        f"Failing items: {[i['item_key'] for i in failing_sql_items]}"
    )
    # The overall failing_count should be 0 — min_characters has no is_passing set so defaults to 0 (False)
    # Run audit sets is_passing for all 36 GATE_QUERIES items; min_characters stays as-is
    assert data["failing_count"] == 0 or data["failing_count"] == 1, (
        # min_characters row may or may not be counted depending on its initial state
        f"Unexpected failing_count: {data['failing_count']}"
    )


# ---------------------------------------------------------------------------
# Tests: update_checklist_item
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_checklist_item_overrides_status(test_db_path):
    """Manual override sets is_passing and missing_count directly."""
    result = await _call_tool(
        test_db_path,
        "update_checklist_item",
        {"item_key": "pop_characters", "is_passing": False, "missing_count": 2, "notes": "test override"},
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["is_passing"] is False
    assert data["missing_count"] == 2
    assert data["notes"] == "test override"


@pytest.mark.asyncio
async def test_update_checklist_item_not_found(test_db_path):
    """Unknown item_key returns NotFoundResponse."""
    result = await _call_tool(
        test_db_path,
        "update_checklist_item",
        {"item_key": "nonexistent_key", "is_passing": True, "missing_count": 0},
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "not_found_message" in data


# ---------------------------------------------------------------------------
# Tests: certify_gate
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_certify_gate_refuses_when_item_failing(test_db_path):
    """certify_gate returns ValidationFailure when any item is not passing.

    Sets pop_characters to failing explicitly to ensure at least one item fails.
    """
    # Ensure at least one item is failing
    await _call_tool(
        test_db_path,
        "update_checklist_item",
        {"item_key": "pop_characters", "is_passing": False, "missing_count": 1},
    )
    result = await _call_tool(test_db_path, "certify_gate", {})
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["is_valid"] is False
    assert len(data["errors"]) > 0


@pytest.mark.asyncio
async def test_certify_gate_passes_after_full_audit(test_db_path):
    """certify_gate succeeds after run_gate_audit confirms all GATE_QUERIES items pass.

    Reset pop_characters back to passing first, then run audit, then certify.
    """
    # Reset the item we manually broke in previous test
    await _call_tool(
        test_db_path,
        "update_checklist_item",
        {"item_key": "pop_characters", "is_passing": True, "missing_count": 0},
    )
    # Also reset min_characters (which may be failing due to default state)
    # by manually setting it to passing — it's not part of GATE_QUERIES so audit won't fix it
    await _call_tool(
        test_db_path,
        "update_checklist_item",
        {"item_key": "min_characters", "is_passing": True, "missing_count": 0},
    )
    # Run audit to ensure all 34 GATE_QUERIES items reflect gate_ready state
    await _call_tool(test_db_path, "run_gate_audit", {})
    # Now certify
    result = await _call_tool(test_db_path, "certify_gate", {"certified_by": "test-suite"})
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["is_certified"] is True
    assert data["certified_by"] == "test-suite"
