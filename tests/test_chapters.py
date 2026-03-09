"""In-memory MCP client tests for chapter domain tools.

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
    Uses unique dir name "chap_db" to avoid cross-file fixture collisions.
    """
    db_file = tmp_path_factory.mktemp("chap_db") / "test_chapters.db"
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
# get_chapter
# ---------------------------------------------------------------------------


async def test_get_chapter_found(test_db_path):
    result = await _call_tool(test_db_path, "get_chapter", {"chapter_id": 1})
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["chapter_number"] == 1
    assert data["title"] == "The Last Ember Watch"


async def test_get_chapter_not_found(test_db_path):
    result = await _call_tool(test_db_path, "get_chapter", {"chapter_id": 9999})
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "not_found_message" in data


# ---------------------------------------------------------------------------
# get_chapter_plan
# ---------------------------------------------------------------------------


async def test_get_chapter_plan(test_db_path):
    result = await _call_tool(test_db_path, "get_chapter_plan", {"chapter_id": 1})
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "chapter_id" in data
    assert "summary" in data
    assert "hook_strength_rating" in data
    # ChapterPlan is a focused subset — must NOT have "id" field
    assert "id" not in data


# ---------------------------------------------------------------------------
# get_chapter_obligations
# ---------------------------------------------------------------------------


async def test_get_chapter_obligations_found(test_db_path):
    result = await _call_tool(test_db_path, "get_chapter_obligations", {"chapter_id": 1})
    assert not result.isError
    obligations = [json.loads(c.text) for c in result.content]
    assert len(obligations) >= 1
    assert obligations[0]["obligation_type"] == "setup"


async def test_get_chapter_obligations_not_found(test_db_path):
    result = await _call_tool(test_db_path, "get_chapter_obligations", {"chapter_id": 9999})
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "not_found_message" in data


# ---------------------------------------------------------------------------
# list_chapters
# ---------------------------------------------------------------------------


async def test_list_chapters(test_db_path):
    result = await _call_tool(test_db_path, "list_chapters", {"book_id": 1})
    assert not result.isError
    chapters = [json.loads(c.text) for c in result.content]
    assert len(chapters) == 3
    assert all(c["book_id"] == 1 for c in chapters)


# ---------------------------------------------------------------------------
# upsert_chapter
# ---------------------------------------------------------------------------


async def test_upsert_chapter_create(test_db_path):
    result = await _call_tool(
        test_db_path,
        "upsert_chapter",
        {
            "chapter_id": None,
            "book_id": 1,
            "chapter_number": 99,
            "title": "New Chapter",
        },
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["id"] is not None
    assert isinstance(data["id"], int)
    assert data["title"] == "New Chapter"


async def test_upsert_chapter_update(test_db_path):
    result = await _call_tool(
        test_db_path,
        "upsert_chapter",
        {
            "chapter_id": 1,
            "book_id": 1,
            "chapter_number": 1,
            "title": "Updated Title",
        },
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["id"] == 1
    assert data["title"] == "Updated Title"


# ---------------------------------------------------------------------------
# delete_chapter
# ---------------------------------------------------------------------------


async def test_delete_chapter_not_found(test_db_path):
    """delete_chapter returns NotFoundResponse for a non-existent chapter ID."""
    result = await _call_tool(test_db_path, "delete_chapter", {"chapter_id": 99999})
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "not_found_message" in data


async def test_delete_chapter_success(test_db_path):
    """delete_chapter removes a chapter with no FK dependents and returns deleted=True."""
    # Create a fresh chapter with no dependents
    create_result = await _call_tool(
        test_db_path,
        "upsert_chapter",
        {
            "chapter_id": None,
            "book_id": 1,
            "chapter_number": 888,
            "title": "Temp Chapter To Delete",
        },
    )
    assert not create_result.isError
    created = json.loads(create_result.content[0].text)
    new_id = created["id"]

    # Now delete it
    del_result = await _call_tool(test_db_path, "delete_chapter", {"chapter_id": new_id})
    assert not del_result.isError
    data = json.loads(del_result.content[0].text)
    assert data.get("deleted") is True
    assert data.get("id") == new_id

    # Confirm it's gone
    get_result = await _call_tool(test_db_path, "get_chapter", {"chapter_id": new_id})
    assert not get_result.isError
    gone = json.loads(get_result.content[0].text)
    assert "not_found_message" in gone
