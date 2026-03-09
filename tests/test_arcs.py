"""In-memory MCP client tests for arc domain tools.

Tests verify the full MCP protocol path: call_tool → FastMCP → tool handler → SQLite → response.
Uses a session-scoped DB fixture with minimal seed data and an in-memory MCP session per test.

CRITICAL: MCP session is entered PER-TEST (inside each async def test_*) via _call_tool helper —
anyio cancel scope teardown is incompatible with pytest-asyncio fixture lifecycle.

FastMCP serializes list[T] as N separate TextContent blocks — multi-item results use
[json.loads(c.text) for c in result.content].

Seed data constants:
    ARC_ID = 1               # character_id=1 (Aeryn), arc_type="transformation"
    CHARACTER_WITH_ARC = 1   # character_id=1 has arc id=1
    ARC_HEALTH_ID = 1        # arc_id=1, chapter_id=1, health_status="on-track"
    CHEKOV_ID = 1            # name="The Scratch Marks", status="planted", payoff_chapter_id=NULL
    NOT_FOUND_ID = 9999

Note: test_get_subplot_touchpoint_gaps inserts a subplot thread directly via raw SQL
because the minimal seed only contains thread_type="main" threads.
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
    Uses unique dir name "arcs_db" to avoid cross-file fixture collisions.
    """
    db_file = tmp_path_factory.mktemp("arcs_db") / "test_arcs.db"
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
# get_chekovs_guns
# ---------------------------------------------------------------------------


async def test_get_chekovs_guns_all(test_db_path):
    result = await _call_tool(test_db_path, "get_chekovs_guns", {})
    assert not result.isError
    guns = [json.loads(c.text) for c in result.content]
    assert len(guns) >= 1
    assert guns[0]["name"] == "The Scratch Marks"


async def test_get_chekovs_guns_status_filter(test_db_path):
    result = await _call_tool(test_db_path, "get_chekovs_guns", {"status": "planted"})
    assert not result.isError
    guns = [json.loads(c.text) for c in result.content]
    assert len(guns) >= 1
    assert all(g["status"] == "planted" for g in guns)


async def test_get_chekovs_guns_unresolved_only(test_db_path):
    result = await _call_tool(test_db_path, "get_chekovs_guns", {"unresolved_only": True})
    assert not result.isError
    guns = [json.loads(c.text) for c in result.content]
    assert len(guns) >= 1
    assert all(g["status"] == "planted" and g["payoff_chapter_id"] is None for g in guns)


# ---------------------------------------------------------------------------
# get_arc
# ---------------------------------------------------------------------------


async def test_get_arc_by_id(test_db_path):
    result = await _call_tool(test_db_path, "get_arc", {"arc_id": 1})
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["id"] == 1
    assert data["character_id"] == 1
    assert data["arc_type"] == "transformation"


async def test_get_arc_by_id_not_found(test_db_path):
    result = await _call_tool(test_db_path, "get_arc", {"arc_id": 9999})
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "not_found_message" in data


async def test_get_arc_by_character(test_db_path):
    result = await _call_tool(test_db_path, "get_arc", {"character_id": 1})
    assert not result.isError
    arcs = [json.loads(c.text) for c in result.content]
    assert len(arcs) >= 1
    assert all(a["character_id"] == 1 for a in arcs)


async def test_get_arc_neither_validation_failure(test_db_path):
    result = await _call_tool(test_db_path, "get_arc", {})
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["is_valid"] is False
    assert len(data["errors"]) > 0


# ---------------------------------------------------------------------------
# get_arc_health
# ---------------------------------------------------------------------------


async def test_get_arc_health(test_db_path):
    result = await _call_tool(test_db_path, "get_arc_health", {"character_id": 1})
    assert not result.isError
    logs = [json.loads(c.text) for c in result.content]
    assert len(logs) >= 1
    assert logs[0]["arc_id"] == 1
    assert logs[0]["health_status"] == "on-track"


# ---------------------------------------------------------------------------
# get_subplot_touchpoint_gaps
# ---------------------------------------------------------------------------


async def test_get_subplot_touchpoint_gaps(test_db_path):
    # Insert a subplot thread with no touchpoints — will exceed any threshold.
    # Minimal seed only has thread_type="main" threads so we add one here.
    conn = sqlite3.connect(test_db_path)
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute(
        "INSERT INTO plot_threads (name, thread_type, status, canon_status) "
        "VALUES ('The Rival Subplot', 'subplot', 'active', 'draft')"
    )
    conn.commit()
    conn.close()
    # Gap query with threshold=1 — subplot has zero touchpoints → NULL last touchpoint
    result = await _call_tool(
        test_db_path, "get_subplot_touchpoint_gaps", {"threshold_chapters": 1}
    )
    assert not result.isError
    gaps = [json.loads(c.text) for c in result.content]
    assert len(gaps) >= 1
    assert any(g["name"] == "The Rival Subplot" for g in gaps)


# ---------------------------------------------------------------------------
# upsert_chekov
# ---------------------------------------------------------------------------


async def test_upsert_chekov_create(test_db_path):
    result = await _call_tool(
        test_db_path,
        "upsert_chekov",
        {"chekov_id": None, "name": "The Old Key", "description": "Found in the drawer"},
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["id"] is not None
    assert data["name"] == "The Old Key"
    assert data["status"] == "planted"


async def test_upsert_chekov_update(test_db_path):
    result = await _call_tool(
        test_db_path,
        "upsert_chekov",
        {
            "chekov_id": 1,
            "name": "The Scratch Marks Updated",
            "description": "Claw marks on the vault door",
            "status": "planted",
        },
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["id"] == 1
    assert data["name"] == "The Scratch Marks Updated"
    assert data["status"] == "planted"


# ---------------------------------------------------------------------------
# log_arc_health
# ---------------------------------------------------------------------------


async def test_log_arc_health(test_db_path):
    result = await _call_tool(
        test_db_path,
        "log_arc_health",
        {"arc_id": 1, "chapter_id": 2, "health_status": "stalled"},
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["id"] is not None
    assert data["arc_id"] == 1
    assert data["health_status"] == "stalled"


# ---------------------------------------------------------------------------
# link_chapter_to_arc / unlink_chapter_from_arc / get_arcs_for_chapter
# ---------------------------------------------------------------------------


async def test_link_chapter_to_arc(test_db_path):
    """Linking a chapter to an arc returns ChapterCharacterArc."""
    result = await _call_tool(
        test_db_path,
        "link_chapter_to_arc",
        {"chapter_id": 1, "arc_id": 1, "arc_progression": "advance"},
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["chapter_id"] == 1
    assert data["arc_id"] == 1
    assert data["arc_progression"] == "advance"


async def test_link_chapter_to_arc_idempotent(test_db_path):
    """Re-linking updates arc_progression without error."""
    result = await _call_tool(
        test_db_path,
        "link_chapter_to_arc",
        {"chapter_id": 1, "arc_id": 1, "arc_progression": "climax"},
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["arc_progression"] == "climax"


async def test_link_chapter_to_arc_missing_chapter(test_db_path):
    """Returns NotFoundResponse when chapter_id does not exist."""
    result = await _call_tool(
        test_db_path,
        "link_chapter_to_arc",
        {"chapter_id": 9999, "arc_id": 1},
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "not_found_message" in data


async def test_link_chapter_to_arc_missing_arc(test_db_path):
    """Returns NotFoundResponse when arc_id does not exist."""
    result = await _call_tool(
        test_db_path,
        "link_chapter_to_arc",
        {"chapter_id": 1, "arc_id": 9999},
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "not_found_message" in data


async def test_get_arcs_for_chapter(test_db_path):
    """Returns list of ChapterCharacterArc entries for a chapter."""
    result = await _call_tool(
        test_db_path,
        "get_arcs_for_chapter",
        {"chapter_id": 1},
    )
    assert not result.isError
    links = [json.loads(c.text) for c in result.content]
    assert len(links) >= 1
    assert all(lnk["chapter_id"] == 1 for lnk in links)


async def test_unlink_chapter_from_arc(test_db_path):
    """Unlink removes the association and returns unlinked=True."""
    result = await _call_tool(
        test_db_path,
        "unlink_chapter_from_arc",
        {"chapter_id": 1, "arc_id": 1},
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["unlinked"] is True
    assert data["chapter_id"] == 1
    assert data["arc_id"] == 1


async def test_unlink_chapter_from_arc_not_found(test_db_path):
    """Unlinking a non-existent link returns NotFoundResponse."""
    result = await _call_tool(
        test_db_path,
        "unlink_chapter_from_arc",
        {"chapter_id": 9999, "arc_id": 9999},
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "not_found_message" in data
