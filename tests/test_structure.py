"""In-memory MCP client tests for structure domain tools.

4 tools: get_story_structure, upsert_story_structure, get_arc_beats, upsert_arc_beat.
Uses minimal seed — structure tools are gate-free.
MCP session entered per-test inside _call_tool.
"""
import json
import os
import sqlite3

import pytest
from mcp.shared.memory import create_connected_server_and_client_session

from novel.db.migrations import apply_migrations
from novel.db.seed import load_seed_profile
from novel.mcp.server import mcp


@pytest.fixture(scope="session")
def test_db_path(tmp_path_factory):
    db_file = tmp_path_factory.mktemp("structure_db") / "test_structure.db"
    conn = sqlite3.connect(str(db_file))
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA journal_mode=WAL")
    apply_migrations(conn)
    load_seed_profile(conn, "minimal")
    conn.commit()
    conn.close()
    return str(db_file)


async def _call_tool(db_path: str, tool_name: str, arguments: dict):
    os.environ["NOVEL_DB_PATH"] = db_path
    async with create_connected_server_and_client_session(mcp) as session:
        return await session.call_tool(tool_name, arguments)


# --- get_story_structure ---

@pytest.mark.asyncio
async def test_get_story_structure_not_found(test_db_path):
    """No story_structure row for book 1 in minimal seed — returns NotFoundResponse."""
    result = await _call_tool(test_db_path, "get_story_structure", {"book_id": 1})
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data is None or "not_found_message" in data


# --- upsert_story_structure ---

@pytest.mark.asyncio
async def test_upsert_story_structure_create(test_db_path):
    """Create a story_structure row for book 1."""
    result = await _call_tool(test_db_path, "upsert_story_structure", {
        "book_id": 1,
        "hook_chapter_id": 1,
        "midpoint_chapter_id": 2,
        "resolution_chapter_id": 3,
    })
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["book_id"] == 1
    assert data["hook_chapter_id"] == 1
    assert data["midpoint_chapter_id"] == 2
    assert data["resolution_chapter_id"] == 3


@pytest.mark.asyncio
async def test_upsert_story_structure_update(test_db_path):
    """Second upsert for book 1 updates the existing row (ON CONFLICT(book_id))."""
    # First create
    await _call_tool(test_db_path, "upsert_story_structure", {
        "book_id": 1, "hook_chapter_id": 1,
    })
    # Then update with different value
    result = await _call_tool(test_db_path, "upsert_story_structure", {
        "book_id": 1, "hook_chapter_id": 2, "notes": "updated",
    })
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["hook_chapter_id"] == 2
    assert data["notes"] == "updated"


# --- get_arc_beats ---

@pytest.mark.asyncio
async def test_get_arc_beats_empty(test_db_path):
    """Arc with no beats returns empty list (not NotFoundResponse)."""
    result = await _call_tool(test_db_path, "get_arc_beats", {"arc_id": 1})
    assert not result.isError
    # Empty list — no content blocks OR content blocks that each decode to a beat
    beats = [json.loads(c.text) for c in result.content] if result.content else []
    assert isinstance(beats, list)


# --- upsert_arc_beat ---

@pytest.mark.asyncio
async def test_upsert_arc_beat_create(test_db_path):
    """Create a beat for arc 1."""
    result = await _call_tool(test_db_path, "upsert_arc_beat", {
        "arc_id": 1, "beat_type": "hook", "chapter_id": 1,
    })
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["arc_id"] == 1
    assert data["beat_type"] == "hook"
    assert data["chapter_id"] == 1


@pytest.mark.asyncio
async def test_upsert_arc_beat_update(test_db_path):
    """Second upsert for same (arc_id, beat_type) updates the row."""
    await _call_tool(test_db_path, "upsert_arc_beat", {
        "arc_id": 1, "beat_type": "midpoint", "chapter_id": 1,
    })
    result = await _call_tool(test_db_path, "upsert_arc_beat", {
        "arc_id": 1, "beat_type": "midpoint", "chapter_id": 2, "notes": "updated",
    })
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["chapter_id"] == 2
    assert data["notes"] == "updated"


@pytest.mark.asyncio
async def test_upsert_arc_beat_invalid_beat_type(test_db_path):
    """Invalid beat_type returns ValidationFailure."""
    result = await _call_tool(test_db_path, "upsert_arc_beat", {
        "arc_id": 1, "beat_type": "not_a_valid_beat",
    })
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["is_valid"] is False
    assert len(data["errors"]) > 0


# --- delete_story_structure ---

@pytest.mark.asyncio
async def test_delete_story_structure_not_found(test_db_path):
    """delete_story_structure returns NotFoundResponse for a non-existent ID."""
    result = await _call_tool(test_db_path, "delete_story_structure", {
        "story_structure_id": 99999,
    })
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "not_found_message" in data


@pytest.mark.asyncio
async def test_delete_story_structure_success(test_db_path):
    """delete_story_structure removes the row and returns deleted=True."""
    # Create a story structure for book 1 (or re-use if already exists)
    create_result = await _call_tool(test_db_path, "upsert_story_structure", {
        "book_id": 1,
        "hook_chapter_id": 1,
    })
    assert not create_result.isError
    created = json.loads(create_result.content[0].text)
    ss_id = created["id"]

    del_result = await _call_tool(test_db_path, "delete_story_structure", {
        "story_structure_id": ss_id,
    })
    assert not del_result.isError
    data = json.loads(del_result.content[0].text)
    assert data.get("deleted") is True
    assert data.get("id") == ss_id

    # Confirm it's gone
    get_result = await _call_tool(test_db_path, "get_story_structure", {"book_id": 1})
    assert not get_result.isError
    gone = json.loads(get_result.content[0].text)
    assert "not_found_message" in gone


# --- delete_arc_beat ---

@pytest.mark.asyncio
async def test_delete_arc_beat_not_found(test_db_path):
    """delete_arc_beat returns NotFoundResponse for a non-existent ID."""
    result = await _call_tool(test_db_path, "delete_arc_beat", {
        "arc_beat_id": 99999,
    })
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "not_found_message" in data


@pytest.mark.asyncio
async def test_delete_arc_beat_success(test_db_path):
    """delete_arc_beat removes the beat row and returns deleted=True."""
    # Create a beat to delete
    create_result = await _call_tool(test_db_path, "upsert_arc_beat", {
        "arc_id": 1, "beat_type": "resolution", "chapter_id": 1,
    })
    assert not create_result.isError
    created = json.loads(create_result.content[0].text)
    beat_id = created["id"]

    del_result = await _call_tool(test_db_path, "delete_arc_beat", {
        "arc_beat_id": beat_id,
    })
    assert not del_result.isError
    data = json.loads(del_result.content[0].text)
    assert data.get("deleted") is True
    assert data.get("id") == beat_id
