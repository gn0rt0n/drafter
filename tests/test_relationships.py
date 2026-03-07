"""In-memory MCP client tests for relationship domain tools.

Tests verify the full MCP protocol path: call_tool → FastMCP → tool handler → SQLite → response.
Uses create_connected_server_and_client_session within each test coroutine to avoid
anyio cancel scope teardown issues with pytest-asyncio.
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

    Session-scoped: created once, reused for all tests in the session.
    """
    db_file = tmp_path_factory.mktemp("rel_db") / "test_rels.db"
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
    """Call a tool via the MCP in-memory protocol and return the result."""
    os.environ["NOVEL_DB_PATH"] = db_path
    async with create_connected_server_and_client_session(mcp) as session:
        return await session.call_tool(tool_name, args)


# ---------------------------------------------------------------------------
# get_relationship
# ---------------------------------------------------------------------------


async def test_get_relationship_found(test_db_path):
    # Seed has (1,3) mentor-student relationship, not (1,2)
    result = await _call_tool(
        test_db_path, "get_relationship", {"character_a_id": 1, "character_b_id": 3}
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "character_a_id" in data
    assert "relationship_type" in data


async def test_get_relationship_reversed_order(test_db_path):
    """get_relationship must return the same row regardless of argument order."""
    # Seed has (1,3) mentor-student relationship — test both orderings
    result_forward = await _call_tool(
        test_db_path, "get_relationship", {"character_a_id": 1, "character_b_id": 3}
    )
    result_reversed = await _call_tool(
        test_db_path, "get_relationship", {"character_a_id": 3, "character_b_id": 1}
    )
    assert not result_forward.isError
    assert not result_reversed.isError
    data_forward = json.loads(result_forward.content[0].text)
    data_reversed = json.loads(result_reversed.content[0].text)
    assert data_forward["id"] == data_reversed["id"]


async def test_get_relationship_not_found(test_db_path):
    result = await _call_tool(
        test_db_path, "get_relationship", {"character_a_id": 1, "character_b_id": 9999}
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "not_found_message" in data


# ---------------------------------------------------------------------------
# list_relationships
# ---------------------------------------------------------------------------


async def test_list_relationships(test_db_path):
    result = await _call_tool(test_db_path, "list_relationships", {"character_id": 1})
    assert not result.isError
    # FastMCP returns each list item as a separate content block
    relationships = [json.loads(c.text) for c in result.content]
    assert isinstance(relationships, list)
    assert len(relationships) >= 3  # Aeryn has 3 seeded relationships


# ---------------------------------------------------------------------------
# upsert_relationship
# ---------------------------------------------------------------------------


async def test_upsert_relationship_create(test_db_path):
    result = await _call_tool(
        test_db_path,
        "upsert_relationship",
        {
            "character_a_id": 4,
            "character_b_id": 5,
            "relationship_type": "rivals",
            "bond_strength": -2,
            "trust_level": -1,
            "current_status": "tense",
        },
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "character_a_id" in data
    assert data["relationship_type"] == "rivals"


# ---------------------------------------------------------------------------
# get_perception_profile
# ---------------------------------------------------------------------------


async def test_get_perception_profile_not_found(test_db_path):
    result = await _call_tool(
        test_db_path, "get_perception_profile", {"observer_id": 9999, "subject_id": 1}
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "not_found_message" in data


# ---------------------------------------------------------------------------
# upsert_perception_profile
# ---------------------------------------------------------------------------


async def test_upsert_perception_profile(test_db_path):
    result = await _call_tool(
        test_db_path,
        "upsert_perception_profile",
        {
            "observer_id": 1,
            "subject_id": 2,
            "trust_level": -3,
            "emotional_valence": "hostile",
        },
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["observer_id"] == 1
    assert data["subject_id"] == 2
    assert data["emotional_valence"] == "hostile"


# ---------------------------------------------------------------------------
# log_relationship_change
# ---------------------------------------------------------------------------


async def test_log_relationship_change(test_db_path):
    result = await _call_tool(
        test_db_path,
        "log_relationship_change",
        {
            "relationship_id": 1,
            "chapter_id": 1,
            "change_type": "shift",
            "description": "Trust eroded after the ambush.",
        },
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "id" in data
    assert data["relationship_id"] == 1
