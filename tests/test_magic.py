"""In-memory MCP client tests for magic domain tools.

Tests verify the full MCP protocol path: call_tool → FastMCP → tool handler → SQLite → response.
Uses a session-scoped DB fixture with minimal seed data and an in-memory MCP session per test.

CRITICAL: MCP session is entered PER-TEST (inside each async def test_*) via _call_tool helper —
anyio cancel scope teardown is incompatible with pytest-asyncio fixture lifecycle.

FastMCP serializes list[T] as N separate TextContent blocks — multi-item results use
[json.loads(c.text) for c in result.content].
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
# Session-scoped DB fixture
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def test_db_path(tmp_path_factory):
    """Create a temp SQLite file with all migrations + minimal seed.

    Session-scoped: created once, reused for all tests in the file.
    Uses unique dir name "magic_db" to avoid cross-file fixture collisions.
    """
    db_file = tmp_path_factory.mktemp("magic_db") / "test_magic.db"
    conn = sqlite3.connect(str(db_file))
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA journal_mode=WAL")
    apply_migrations(conn)
    load_seed_profile(conn, "minimal")
    conn.commit()
    conn.close()
    return str(db_file)


# ---------------------------------------------------------------------------
# Helper: enter MCP session within each test coroutine to avoid anyio issues
# ---------------------------------------------------------------------------


async def _call_tool(db_path: str, tool_name: str, args: dict):
    """Call a tool via the MCP in-memory protocol and return the result.

    Opens and closes the MCP session within this coroutine so anyio cancel
    scopes are entered and exited in the same task.
    """
    os.environ["NOVEL_DB_PATH"] = db_path
    async with create_connected_server_and_client_session(mcp) as session:
        return await session.call_tool(tool_name, args)


# ---------------------------------------------------------------------------
# get_magic_element
# ---------------------------------------------------------------------------


async def test_get_magic_element_found(test_db_path):
    result = await _call_tool(test_db_path, "get_magic_element", {"magic_element_id": 1})
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["name"] == "Ember-Binding"
    assert data["rules"] is not None


async def test_get_magic_element_not_found(test_db_path):
    result = await _call_tool(test_db_path, "get_magic_element", {"magic_element_id": 9999})
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "not_found_message" in data


# ---------------------------------------------------------------------------
# get_practitioner_abilities
# ---------------------------------------------------------------------------


async def test_get_practitioner_abilities(test_db_path):
    # character_id=1 has practitioner ability for element 1 (proficiency_level=3)
    result = await _call_tool(
        test_db_path, "get_practitioner_abilities", {"character_id": 1}
    )
    assert not result.isError
    abilities = [json.loads(c.text) for c in result.content]
    assert len(abilities) >= 1
    assert abilities[0]["magic_element_id"] == 1
    assert abilities[0]["proficiency_level"] == 3


# ---------------------------------------------------------------------------
# log_magic_use
# ---------------------------------------------------------------------------


async def test_log_magic_use(test_db_path):
    result = await _call_tool(
        test_db_path,
        "log_magic_use",
        {
            "chapter_id": 1,
            "character_id": 1,
            "action_description": "Test ember binding",
            "magic_element_id": 1,
        },
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["id"] is not None
    assert data["character_id"] == 1
    assert data["compliance_status"] == "compliant"


# ---------------------------------------------------------------------------
# check_magic_compliance
# ---------------------------------------------------------------------------


async def test_check_magic_compliance_has_ability(test_db_path):
    # character_id=1 has registered ability for magic_element_id=1 → compliant
    result = await _call_tool(
        test_db_path,
        "check_magic_compliance",
        {
            "character_id": 1,
            "magic_element_id": 1,
            "action_description": "Bind ember",
        },
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["compliant"] is True
    assert data["character_has_ability"] is True
    assert isinstance(data["applicable_rules"], list)
    assert len(data["applicable_rules"]) >= 1


async def test_check_magic_compliance_no_ability(test_db_path):
    # character_id=2 has no registered ability for magic_element_id=1 → non-compliant
    result = await _call_tool(
        test_db_path,
        "check_magic_compliance",
        {
            "character_id": 2,
            "magic_element_id": 1,
            "action_description": "Bind ember",
        },
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["compliant"] is False
    assert data["character_has_ability"] is False
    assert len(data["violations"]) >= 1
