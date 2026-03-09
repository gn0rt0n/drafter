"""In-memory MCP client tests for scene domain tools.

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
    Uses unique dir name "scene_db" to avoid cross-file fixture collisions.
    """
    db_file = tmp_path_factory.mktemp("scene_db") / "test_scenes.db"
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
# get_scene
# ---------------------------------------------------------------------------


async def test_get_scene_found(test_db_path):
    result = await _call_tool(test_db_path, "get_scene", {"scene_id": 1})
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["chapter_id"] == 1
    assert data["scene_number"] == 1


async def test_get_scene_not_found(test_db_path):
    result = await _call_tool(test_db_path, "get_scene", {"scene_id": 9999})
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "not_found_message" in data


# ---------------------------------------------------------------------------
# get_scene_character_goals
# ---------------------------------------------------------------------------


async def test_get_scene_character_goals(test_db_path):
    result = await _call_tool(test_db_path, "get_scene_character_goals", {"scene_id": 1})
    assert not result.isError
    goals = [json.loads(c.text) for c in result.content]
    assert len(goals) >= 1
    assert goals[0]["character_id"] == 1


async def test_get_scene_character_goals_not_found(test_db_path):
    result = await _call_tool(test_db_path, "get_scene_character_goals", {"scene_id": 9999})
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "not_found_message" in data


# ---------------------------------------------------------------------------
# upsert_scene
# ---------------------------------------------------------------------------


async def test_upsert_scene_create(test_db_path):
    result = await _call_tool(
        test_db_path,
        "upsert_scene",
        {
            "scene_id": None,
            "chapter_id": 1,
            "scene_number": 99,
            "summary": "New scene",
        },
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["id"] is not None
    assert isinstance(data["id"], int)
    assert data["scene_number"] == 99


# ---------------------------------------------------------------------------
# upsert_scene_goal
# ---------------------------------------------------------------------------


async def test_upsert_scene_goal(test_db_path):
    result = await _call_tool(
        test_db_path,
        "upsert_scene_goal",
        {
            "scene_id": 1,
            "character_id": 1,
            "goal": "Updated goal",
        },
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["scene_id"] == 1
    assert data["character_id"] == 1
    assert data["goal"] == "Updated goal"


# ---------------------------------------------------------------------------
# delete_scene
# ---------------------------------------------------------------------------


async def test_delete_scene_not_found(test_db_path):
    """delete_scene returns NotFoundResponse for a non-existent scene ID."""
    result = await _call_tool(test_db_path, "delete_scene", {"scene_id": 99999})
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "not_found_message" in data


async def test_delete_scene_success(test_db_path):
    """delete_scene removes a scene with no FK dependents and returns deleted=True."""
    # Create a fresh scene with no dependents
    create_result = await _call_tool(
        test_db_path,
        "upsert_scene",
        {
            "scene_id": None,
            "chapter_id": 1,
            "scene_number": 888,
            "summary": "Temp scene to delete",
        },
    )
    assert not create_result.isError
    created = json.loads(create_result.content[0].text)
    new_id = created["id"]

    # Delete it
    del_result = await _call_tool(test_db_path, "delete_scene", {"scene_id": new_id})
    assert not del_result.isError
    data = json.loads(del_result.content[0].text)
    assert data.get("deleted") is True
    assert data.get("id") == new_id

    # Confirm it's gone
    get_result = await _call_tool(test_db_path, "get_scene", {"scene_id": new_id})
    assert not get_result.isError
    gone = json.loads(get_result.content[0].text)
    assert "not_found_message" in gone


# ---------------------------------------------------------------------------
# delete_scene_goal
# ---------------------------------------------------------------------------


async def test_delete_scene_goal_not_found(test_db_path):
    """delete_scene_goal returns NotFoundResponse for a non-existent goal ID."""
    result = await _call_tool(test_db_path, "delete_scene_goal", {"scene_goal_id": 99999})
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "not_found_message" in data


async def test_delete_scene_goal_success(test_db_path):
    """delete_scene_goal removes a goal record and returns deleted=True."""
    # Upsert a goal to get an ID
    upsert_result = await _call_tool(
        test_db_path,
        "upsert_scene_goal",
        {
            "scene_id": 1,
            "character_id": 2,
            "goal": "Goal to be deleted",
        },
    )
    assert not upsert_result.isError
    goal_data = json.loads(upsert_result.content[0].text)
    goal_id = goal_data["id"]

    # Delete it
    del_result = await _call_tool(test_db_path, "delete_scene_goal", {"scene_goal_id": goal_id})
    assert not del_result.isError
    data = json.loads(del_result.content[0].text)
    assert data.get("deleted") is True
    assert data.get("id") == goal_id
