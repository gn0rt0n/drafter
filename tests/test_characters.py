"""In-memory MCP client tests for character domain tools.

Tests verify the full MCP protocol path: call_tool → FastMCP → tool handler → SQLite → response.
Uses mcp_session fixture (from conftest.py) which provides a ClientSession connected to
the novel MCP server pointing at a temp SQLite DB with minimal seed data loaded.

The mcp_session fixture uses create_connected_server_and_client_session for full MCP protocol
tests. Each test enters and exits the MCP session within the test coroutine to avoid
anyio cancel scope teardown issues with pytest-asyncio.
"""
import json
import os
import sqlite3
import tempfile
from pathlib import Path

import pytest
import pytest_asyncio
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

    Session-scoped: created once, reused for all tests in the session.
    """
    db_file = tmp_path_factory.mktemp("char_db") / "test_chars.db"
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
# get_character
# ---------------------------------------------------------------------------


async def test_get_character_found(test_db_path):
    result = await _call_tool(test_db_path, "get_character", {"character_id": 1})
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["name"] == "Aeryn Vael"
    assert data["id"] == 1
    assert data["role"] == "protagonist"


async def test_get_character_not_found(test_db_path):
    result = await _call_tool(test_db_path, "get_character", {"character_id": 9999})
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "not_found_message" in data


# ---------------------------------------------------------------------------
# list_characters
# ---------------------------------------------------------------------------


async def test_list_characters(test_db_path):
    result = await _call_tool(test_db_path, "list_characters", {})
    assert not result.isError
    # FastMCP returns each list item as a separate content block
    characters = [json.loads(c.text) for c in result.content]
    assert isinstance(characters, list)
    assert len(characters) >= 5
    names = [c["name"] for c in characters]
    assert "Aeryn Vael" in names


# ---------------------------------------------------------------------------
# upsert_character
# ---------------------------------------------------------------------------


async def test_upsert_character_create(test_db_path):
    result = await _call_tool(
        test_db_path,
        "upsert_character",
        {"character_id": None, "name": "Test Hero", "role": "supporting"},
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["name"] == "Test Hero"
    assert data["id"] is not None
    assert isinstance(data["id"], int)


async def test_upsert_character_update(test_db_path):
    result = await _call_tool(
        test_db_path,
        "upsert_character",
        {"character_id": 1, "name": "Aeryn Vael Updated", "role": "protagonist"},
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["name"] == "Aeryn Vael Updated"
    assert data["id"] == 1


# ---------------------------------------------------------------------------
# get_character_injuries
# ---------------------------------------------------------------------------


async def test_get_character_injuries_returns_list(test_db_path):
    result = await _call_tool(test_db_path, "get_character_injuries", {"character_id": 1})
    assert not result.isError
    # Empty list returns empty content; non-empty returns one block per item
    injuries = [json.loads(c.text) for c in result.content]
    assert isinstance(injuries, list)


async def test_get_character_injuries_not_found(test_db_path):
    result = await _call_tool(test_db_path, "get_character_injuries", {"character_id": 9999})
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "not_found_message" in data


# ---------------------------------------------------------------------------
# get_character_beliefs
# ---------------------------------------------------------------------------


async def test_get_character_beliefs_returns_list(test_db_path):
    result = await _call_tool(test_db_path, "get_character_beliefs", {"character_id": 1})
    assert not result.isError
    beliefs = [json.loads(c.text) for c in result.content]
    assert isinstance(beliefs, list)


# ---------------------------------------------------------------------------
# get_character_knowledge
# ---------------------------------------------------------------------------


async def test_get_character_knowledge_returns_list(test_db_path):
    result = await _call_tool(test_db_path, "get_character_knowledge", {"character_id": 1})
    assert not result.isError
    items = [json.loads(c.text) for c in result.content]
    assert isinstance(items, list)


async def test_get_character_knowledge_chapter_scoped(test_db_path):
    result = await _call_tool(
        test_db_path, "get_character_knowledge", {"character_id": 1, "chapter_id": 5}
    )
    assert not result.isError
    items = [json.loads(c.text) for c in result.content]
    assert isinstance(items, list)
    # All returned records must have chapter_id <= 5
    for record in items:
        assert record["chapter_id"] <= 5


async def test_get_character_knowledge_not_found(test_db_path):
    result = await _call_tool(test_db_path, "get_character_knowledge", {"character_id": 9999})
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "not_found_message" in data


# ---------------------------------------------------------------------------
# log_character_knowledge
# ---------------------------------------------------------------------------


async def test_log_character_knowledge(test_db_path):
    result = await _call_tool(
        test_db_path,
        "log_character_knowledge",
        {
            "character_id": 1,
            "chapter_id": 1,
            "knowledge_type": "fact",
            "content": "The star-forges were hidden beneath the capital.",
        },
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "id" in data
    assert data["character_id"] == 1
    assert data["content"] == "The star-forges were hidden beneath the capital."


# ---------------------------------------------------------------------------
# get_character_location
# ---------------------------------------------------------------------------


async def test_get_character_location_returns_list(test_db_path):
    result = await _call_tool(test_db_path, "get_character_location", {"character_id": 1})
    assert not result.isError
    locations = [json.loads(c.text) for c in result.content]
    assert isinstance(locations, list)


# ---------------------------------------------------------------------------
# log_character_belief
# ---------------------------------------------------------------------------


async def test_log_character_belief_success(test_db_path):
    result = await _call_tool(
        test_db_path,
        "log_character_belief",
        {
            "character_id": 1,
            "belief_type": "worldview",
            "content": "The old empire was corrupt and deserved to fall.",
        },
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "id" in data
    assert data["character_id"] == 1
    assert data["content"] == "The old empire was corrupt and deserved to fall."
    assert data["belief_type"] == "worldview"


async def test_log_character_belief_character_not_found(test_db_path):
    result = await _call_tool(
        test_db_path,
        "log_character_belief",
        {"character_id": 9999, "belief_type": "worldview", "content": "Test belief"},
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "not_found_message" in data


# ---------------------------------------------------------------------------
# delete_character_belief
# ---------------------------------------------------------------------------


async def test_delete_character_belief_success(test_db_path):
    # First create a belief to delete
    log_result = await _call_tool(
        test_db_path,
        "log_character_belief",
        {"character_id": 1, "belief_type": "personal", "content": "Belief to delete"},
    )
    assert not log_result.isError
    created = json.loads(log_result.content[0].text)
    belief_id = created["id"]

    result = await _call_tool(
        test_db_path, "delete_character_belief", {"belief_id": belief_id}
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["deleted"] is True
    assert data["id"] == belief_id


async def test_delete_character_belief_not_found(test_db_path):
    result = await _call_tool(
        test_db_path, "delete_character_belief", {"belief_id": 99999}
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "not_found_message" in data


# ---------------------------------------------------------------------------
# log_character_location
# ---------------------------------------------------------------------------


async def test_log_character_location_success(test_db_path):
    result = await _call_tool(
        test_db_path,
        "log_character_location",
        {
            "character_id": 1,
            "chapter_id": 1,
            "location_note": "Arrived at the northern watchtower.",
        },
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "id" in data
    assert data["character_id"] == 1
    assert data["chapter_id"] == 1
    assert data["location_note"] == "Arrived at the northern watchtower."


async def test_log_character_location_character_not_found(test_db_path):
    result = await _call_tool(
        test_db_path,
        "log_character_location",
        {"character_id": 9999, "chapter_id": 1, "location_note": "Somewhere"},
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "not_found_message" in data


async def test_log_character_location_chapter_not_found(test_db_path):
    result = await _call_tool(
        test_db_path,
        "log_character_location",
        {"character_id": 1, "chapter_id": 99999, "location_note": "Somewhere"},
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "not_found_message" in data


# ---------------------------------------------------------------------------
# get_current_character_location
# ---------------------------------------------------------------------------


async def test_get_current_character_location_success(test_db_path):
    # Log a location first so we have something to retrieve
    await _call_tool(
        test_db_path,
        "log_character_location",
        {
            "character_id": 1,
            "chapter_id": 1,
            "location_note": "Base camp.",
        },
    )
    result = await _call_tool(
        test_db_path, "get_current_character_location", {"character_id": 1}
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "id" in data
    assert data["character_id"] == 1


async def test_get_current_character_location_not_found(test_db_path):
    # Use a character with no locations (character 9999 doesn't exist, expect not_found)
    result = await _call_tool(
        test_db_path, "get_current_character_location", {"character_id": 9999}
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "not_found_message" in data


# ---------------------------------------------------------------------------
# delete_character_location
# ---------------------------------------------------------------------------


async def test_delete_character_location_success(test_db_path):
    # Create a location record to delete
    log_result = await _call_tool(
        test_db_path,
        "log_character_location",
        {"character_id": 1, "chapter_id": 1, "location_note": "Location to delete"},
    )
    assert not log_result.isError
    created = json.loads(log_result.content[0].text)
    location_id = created["id"]

    result = await _call_tool(
        test_db_path, "delete_character_location", {"location_id": location_id}
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["deleted"] is True
    assert data["id"] == location_id


async def test_delete_character_location_not_found(test_db_path):
    result = await _call_tool(
        test_db_path, "delete_character_location", {"location_id": 99999}
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "not_found_message" in data
