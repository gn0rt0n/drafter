"""In-memory MCP client tests for plot domain tools.

Tests verify the full MCP protocol path: call_tool → FastMCP → tool handler → SQLite → response.
Uses a session-scoped DB fixture with minimal seed data and an in-memory MCP session per test.

CRITICAL: MCP session is entered PER-TEST (inside each async def test_*) via _call_tool helper —
anyio cancel scope teardown is incompatible with pytest-asyncio fixture lifecycle.

FastMCP serializes list[T] as N separate TextContent blocks — multi-item results use
[json.loads(c.text) for c in result.content].

Seed data constants:
    PLOT_THREAD_ID = 1   # name="The Hidden Vault", thread_type="main", status="active"
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
    Uses unique dir name "plot_db" to avoid cross-file fixture collisions.
    """
    db_file = tmp_path_factory.mktemp("plot_db") / "test_plot.db"
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
# get_plot_thread
# ---------------------------------------------------------------------------


async def test_get_plot_thread_found(test_db_path):
    result = await _call_tool(test_db_path, "get_plot_thread", {"plot_thread_id": 1})
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["name"] == "The Hidden Vault"
    assert data["thread_type"] == "main"


async def test_get_plot_thread_not_found(test_db_path):
    result = await _call_tool(test_db_path, "get_plot_thread", {"plot_thread_id": 9999})
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "not_found_message" in data


# ---------------------------------------------------------------------------
# list_plot_threads
# ---------------------------------------------------------------------------


async def test_list_plot_threads_all(test_db_path):
    result = await _call_tool(test_db_path, "list_plot_threads", {})
    assert not result.isError
    threads = [json.loads(c.text) for c in result.content]
    assert len(threads) >= 1
    assert any(t["name"] == "The Hidden Vault" for t in threads)


async def test_list_plot_threads_filtered(test_db_path):
    result = await _call_tool(
        test_db_path, "list_plot_threads", {"thread_type": "main", "status": "active"}
    )
    assert not result.isError
    threads = [json.loads(c.text) for c in result.content]
    assert len(threads) >= 1
    assert all(t["thread_type"] == "main" for t in threads)
    assert all(t["status"] == "active" for t in threads)


# ---------------------------------------------------------------------------
# upsert_plot_thread
# ---------------------------------------------------------------------------


async def test_upsert_plot_thread_create(test_db_path):
    result = await _call_tool(
        test_db_path,
        "upsert_plot_thread",
        {"plot_thread_id": None, "name": "New Subplot", "thread_type": "subplot"},
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["id"] is not None
    assert data["name"] == "New Subplot"
    assert data["thread_type"] == "subplot"


async def test_upsert_plot_thread_update(test_db_path):
    result = await _call_tool(
        test_db_path,
        "upsert_plot_thread",
        {"plot_thread_id": 1, "name": "Updated Hidden Vault", "thread_type": "main"},
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["id"] == 1
    assert data["name"] == "Updated Hidden Vault"


# ---------------------------------------------------------------------------
# link_chapter_to_plot_thread / unlink_chapter_from_plot_thread / get_plot_threads_for_chapter
# ---------------------------------------------------------------------------


async def test_link_chapter_to_plot_thread(test_db_path):
    """Linking a chapter to a plot thread returns ChapterPlotThread."""
    result = await _call_tool(
        test_db_path,
        "link_chapter_to_plot_thread",
        {"chapter_id": 1, "plot_thread_id": 1, "thread_role": "advance"},
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["chapter_id"] == 1
    assert data["plot_thread_id"] == 1
    assert data["thread_role"] == "advance"


async def test_link_chapter_to_plot_thread_idempotent(test_db_path):
    """Re-linking updates thread_role without error."""
    result = await _call_tool(
        test_db_path,
        "link_chapter_to_plot_thread",
        {"chapter_id": 1, "plot_thread_id": 1, "thread_role": "resolve"},
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["thread_role"] == "resolve"


async def test_link_chapter_to_plot_thread_missing_chapter(test_db_path):
    """Returns NotFoundResponse when chapter_id does not exist."""
    result = await _call_tool(
        test_db_path,
        "link_chapter_to_plot_thread",
        {"chapter_id": 9999, "plot_thread_id": 1},
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "not_found_message" in data


async def test_link_chapter_to_plot_thread_missing_plot_thread(test_db_path):
    """Returns NotFoundResponse when plot_thread_id does not exist."""
    result = await _call_tool(
        test_db_path,
        "link_chapter_to_plot_thread",
        {"chapter_id": 1, "plot_thread_id": 9999},
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "not_found_message" in data


async def test_get_plot_threads_for_chapter(test_db_path):
    """Returns list of ChapterPlotThread entries for a chapter."""
    result = await _call_tool(
        test_db_path,
        "get_plot_threads_for_chapter",
        {"chapter_id": 1},
    )
    assert not result.isError
    links = [json.loads(c.text) for c in result.content]
    assert len(links) >= 1
    assert all(lnk["chapter_id"] == 1 for lnk in links)


async def test_unlink_chapter_from_plot_thread(test_db_path):
    """Unlink removes the association and returns unlinked=True."""
    result = await _call_tool(
        test_db_path,
        "unlink_chapter_from_plot_thread",
        {"chapter_id": 1, "plot_thread_id": 1},
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["unlinked"] is True
    assert data["chapter_id"] == 1
    assert data["plot_thread_id"] == 1


async def test_unlink_chapter_from_plot_thread_not_found(test_db_path):
    """Unlinking a non-existent link returns NotFoundResponse."""
    result = await _call_tool(
        test_db_path,
        "unlink_chapter_from_plot_thread",
        {"chapter_id": 9999, "plot_thread_id": 9999},
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "not_found_message" in data
