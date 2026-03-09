"""In-memory MCP client tests for world domain tools.

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
    Uses unique dir name "world_db" to avoid cross-file fixture collisions.
    """
    db_file = tmp_path_factory.mktemp("world_db") / "test_world.db"
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
# get_location
# ---------------------------------------------------------------------------


async def test_get_location_found(test_db_path):
    result = await _call_tool(test_db_path, "get_location", {"location_id": 1})
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["name"] == "The Ashen Citadel"
    # sensory_profile field_validator parses JSON string → dict
    assert isinstance(data["sensory_profile"], dict)


async def test_get_location_not_found(test_db_path):
    result = await _call_tool(test_db_path, "get_location", {"location_id": 9999})
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "not_found_message" in data


# ---------------------------------------------------------------------------
# get_faction
# ---------------------------------------------------------------------------


async def test_get_faction_found(test_db_path):
    result = await _call_tool(test_db_path, "get_faction", {"faction_id": 1})
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["name"] == "The Obsidian Court"
    assert data["leader_character_id"] == 2


async def test_get_faction_not_found(test_db_path):
    result = await _call_tool(test_db_path, "get_faction", {"faction_id": 9999})
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "not_found_message" in data


# ---------------------------------------------------------------------------
# get_faction_political_state
# ---------------------------------------------------------------------------


async def test_get_faction_political_state_latest(test_db_path):
    # No chapter_id — returns most recent state for faction
    result = await _call_tool(
        test_db_path,
        "get_faction_political_state",
        {"faction_id": 1},
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["faction_id"] == 1
    assert data["power_level"] == 8


async def test_get_faction_political_state_by_chapter(test_db_path):
    # chapter_id=1 — returns state at that specific chapter
    result = await _call_tool(
        test_db_path,
        "get_faction_political_state",
        {"faction_id": 1, "chapter_id": 1},
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["chapter_id"] == 1


# ---------------------------------------------------------------------------
# get_culture
# ---------------------------------------------------------------------------


async def test_get_culture_found(test_db_path):
    result = await _call_tool(test_db_path, "get_culture", {"culture_id": 1})
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["name"] == "Kaelthari"


# ---------------------------------------------------------------------------
# upsert_location
# ---------------------------------------------------------------------------


async def test_upsert_location_create(test_db_path):
    result = await _call_tool(
        test_db_path,
        "upsert_location",
        {
            "location_id": None,
            "name": "New Keep",
            "sensory_profile": {"sight": "dark stone"},
        },
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["id"] is not None
    assert isinstance(data["id"], int)
    assert data["name"] == "New Keep"
    # sensory_profile returned as dict (not JSON string)
    assert isinstance(data["sensory_profile"], dict)


# ---------------------------------------------------------------------------
# upsert_faction
# ---------------------------------------------------------------------------


async def test_upsert_faction_create(test_db_path):
    result = await _call_tool(
        test_db_path,
        "upsert_faction",
        {
            "faction_id": None,
            "name": "New Guild",
        },
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["id"] is not None
    assert isinstance(data["id"], int)
    assert data["name"] == "New Guild"


# ---------------------------------------------------------------------------
# upsert_culture
# ---------------------------------------------------------------------------


async def test_upsert_culture_create(test_db_path):
    """upsert_culture with no id creates a new culture row."""
    result = await _call_tool(
        test_db_path,
        "upsert_culture",
        {
            "culture_id": None,
            "name": "TestCulture_New",
            "region": "Northern Wastes",
        },
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["id"] is not None
    assert isinstance(data["id"], int)
    assert data["name"] == "TestCulture_New"
    assert data["region"] == "Northern Wastes"


async def test_upsert_culture_update_by_id(test_db_path):
    """upsert_culture with a provided id updates an existing culture."""
    # First create
    r1 = await _call_tool(
        test_db_path,
        "upsert_culture",
        {"culture_id": None, "name": "TestCulture_Update"},
    )
    culture_id = json.loads(r1.content[0].text)["id"]

    # Then update
    result = await _call_tool(
        test_db_path,
        "upsert_culture",
        {
            "culture_id": culture_id,
            "name": "TestCulture_Update",
            "notes": "Updated notes",
        },
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["id"] == culture_id
    assert data["notes"] == "Updated notes"


# ---------------------------------------------------------------------------
# list_cultures
# ---------------------------------------------------------------------------


async def test_list_cultures_returns_list(test_db_path):
    """list_cultures returns a non-empty list with Culture objects."""
    result = await _call_tool(test_db_path, "list_cultures", {})
    assert not result.isError
    # FastMCP returns list items as separate TextContent blocks
    assert len(result.content) >= 1
    first = json.loads(result.content[0].text)
    assert "name" in first
    assert "id" in first


# ---------------------------------------------------------------------------
# delete_culture
# ---------------------------------------------------------------------------


async def test_delete_culture_success(test_db_path):
    """delete_culture removes a culture and returns deleted=True."""
    # Create a fresh culture to delete
    r1 = await _call_tool(
        test_db_path,
        "upsert_culture",
        {"culture_id": None, "name": "TestCulture_ToDelete"},
    )
    culture_id = json.loads(r1.content[0].text)["id"]

    result = await _call_tool(
        test_db_path, "delete_culture", {"culture_id": culture_id}
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["deleted"] is True
    assert data["id"] == culture_id


async def test_delete_culture_not_found(test_db_path):
    """delete_culture returns NotFoundResponse for non-existent id."""
    result = await _call_tool(
        test_db_path, "delete_culture", {"culture_id": 99999}
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "not_found_message" in data


# ---------------------------------------------------------------------------
# log_faction_political_state
# ---------------------------------------------------------------------------


async def test_log_faction_political_state_success(test_db_path):
    """log_faction_political_state inserts and returns FactionPoliticalState."""
    # Seed has faction_id=1 and chapter_id=1
    # Use chapter_id=3 to avoid UNIQUE(faction_id, chapter_id) collision with seed data
    result = await _call_tool(
        test_db_path,
        "log_faction_political_state",
        {
            "faction_id": 1,
            "chapter_id": 3,
            "power_level": 7,
            "internal_state": "Strained",
        },
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["faction_id"] == 1
    assert data["chapter_id"] == 3
    assert data["power_level"] == 7


async def test_log_faction_political_state_faction_not_found(test_db_path):
    """log_faction_political_state returns NotFoundResponse for missing faction."""
    result = await _call_tool(
        test_db_path,
        "log_faction_political_state",
        {
            "faction_id": 99999,
            "chapter_id": 1,
            "power_level": 5,
        },
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "not_found_message" in data


# ---------------------------------------------------------------------------
# get_current_faction_political_state
# ---------------------------------------------------------------------------


async def test_get_current_faction_political_state_found(test_db_path):
    """get_current_faction_political_state returns most recent entry by id."""
    # Seed has faction 1 with at least one political state
    result = await _call_tool(
        test_db_path,
        "get_current_faction_political_state",
        {"faction_id": 1},
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["faction_id"] == 1
    assert "id" in data


async def test_get_current_faction_political_state_not_found(test_db_path):
    """get_current_faction_political_state returns NotFoundResponse for faction with no states."""
    result = await _call_tool(
        test_db_path,
        "get_current_faction_political_state",
        {"faction_id": 99999},
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "not_found_message" in data


# ---------------------------------------------------------------------------
# delete_faction_political_state
# ---------------------------------------------------------------------------


async def test_delete_faction_political_state_success(test_db_path):
    """delete_faction_political_state removes entry and returns deleted=True."""
    # Log a new state entry to delete (use chapter_id=2 — seed only uses chapter_id=1 for faction 1)
    r1 = await _call_tool(
        test_db_path,
        "log_faction_political_state",
        {
            "faction_id": 1,
            "chapter_id": 2,
            "power_level": 3,
        },
    )
    state_id = json.loads(r1.content[0].text)["id"]

    result = await _call_tool(
        test_db_path,
        "delete_faction_political_state",
        {"political_state_id": state_id},
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["deleted"] is True
    assert data["id"] == state_id


async def test_delete_faction_political_state_not_found(test_db_path):
    """delete_faction_political_state returns NotFoundResponse for missing id."""
    result = await _call_tool(
        test_db_path,
        "delete_faction_political_state",
        {"political_state_id": 99999},
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "not_found_message" in data
