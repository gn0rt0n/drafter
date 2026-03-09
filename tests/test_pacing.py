"""In-memory MCP client tests for pacing_beats and tension_measurements tools.

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
    Uses unique dir name "pacing_db" to avoid cross-file fixture collisions.
    """
    db_file = tmp_path_factory.mktemp("pacing_db") / "test_pacing.db"
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
# get_pacing_beats
# ---------------------------------------------------------------------------


async def test_get_pacing_beats_empty(test_db_path):
    """get_pacing_beats returns empty list when no beats exist for chapter."""
    # Use a chapter_id that has no seed data (999 does not exist but tool returns empty not error)
    result = await _call_tool(test_db_path, "get_pacing_beats", {"chapter_id": 9999})
    assert not result.isError
    # Empty list means no content blocks
    assert len(result.content) == 0


async def test_get_pacing_beats_after_log(test_db_path):
    """get_pacing_beats returns beats after logging one."""
    # Log a beat first
    log_result = await _call_tool(
        test_db_path,
        "log_pacing_beat",
        {
            "chapter_id": 1,
            "beat_type": "action",
            "description": "Hero enters the forest",
            "sequence_order": 1,
        },
    )
    assert not log_result.isError
    logged = json.loads(log_result.content[0].text)
    assert logged["chapter_id"] == 1
    assert logged["beat_type"] == "action"
    assert logged["description"] == "Hero enters the forest"

    # Now get_pacing_beats should return it
    result = await _call_tool(test_db_path, "get_pacing_beats", {"chapter_id": 1})
    assert not result.isError
    beats = [json.loads(c.text) for c in result.content]
    assert len(beats) >= 1
    assert any(b["description"] == "Hero enters the forest" for b in beats)


# ---------------------------------------------------------------------------
# log_pacing_beat
# ---------------------------------------------------------------------------


async def test_log_pacing_beat_returns_model(test_db_path):
    """log_pacing_beat creates a pacing beat and returns PacingBeat model."""
    result = await _call_tool(
        test_db_path,
        "log_pacing_beat",
        {
            "chapter_id": 1,
            "beat_type": "dialogue",
            "description": "Conversation with mentor",
            "sequence_order": 2,
            "notes": "Important foreshadowing",
        },
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["id"] is not None
    assert isinstance(data["id"], int)
    assert data["chapter_id"] == 1
    assert data["beat_type"] == "dialogue"
    assert data["description"] == "Conversation with mentor"
    assert data["notes"] == "Important foreshadowing"


async def test_log_pacing_beat_chapter_not_found(test_db_path):
    """log_pacing_beat returns NotFoundResponse for non-existent chapter_id."""
    result = await _call_tool(
        test_db_path,
        "log_pacing_beat",
        {
            "chapter_id": 99999,
            "beat_type": "action",
            "description": "Ghost beat",
            "sequence_order": 0,
        },
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "not_found_message" in data


async def test_log_pacing_beat_with_optional_scene_id(test_db_path):
    """log_pacing_beat accepts optional scene_id."""
    result = await _call_tool(
        test_db_path,
        "log_pacing_beat",
        {
            "chapter_id": 1,
            "beat_type": "reflection",
            "description": "Quiet moment",
            "sequence_order": 3,
            "scene_id": 1,
        },
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["chapter_id"] == 1
    assert data["scene_id"] == 1


# ---------------------------------------------------------------------------
# delete_pacing_beat
# ---------------------------------------------------------------------------


async def test_delete_pacing_beat_not_found(test_db_path):
    """delete_pacing_beat returns NotFoundResponse for non-existent ID."""
    result = await _call_tool(
        test_db_path, "delete_pacing_beat", {"pacing_beat_id": 99999}
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "not_found_message" in data


async def test_delete_pacing_beat_success(test_db_path):
    """delete_pacing_beat removes a beat and returns deleted=True."""
    # Log a beat to get an ID
    log_result = await _call_tool(
        test_db_path,
        "log_pacing_beat",
        {
            "chapter_id": 1,
            "beat_type": "action",
            "description": "Beat to delete",
            "sequence_order": 99,
        },
    )
    assert not log_result.isError
    beat_id = json.loads(log_result.content[0].text)["id"]

    # Delete it
    del_result = await _call_tool(
        test_db_path, "delete_pacing_beat", {"pacing_beat_id": beat_id}
    )
    assert not del_result.isError
    data = json.loads(del_result.content[0].text)
    assert data.get("deleted") is True
    assert data.get("id") == beat_id


# ---------------------------------------------------------------------------
# get_tension_measurements
# ---------------------------------------------------------------------------


async def test_get_tension_measurements_empty(test_db_path):
    """get_tension_measurements returns empty list when none exist for chapter."""
    # Use a chapter_id with no seed data (9999 doesn't exist, tool returns empty not error)
    result = await _call_tool(
        test_db_path, "get_tension_measurements", {"chapter_id": 9999}
    )
    assert not result.isError
    assert len(result.content) == 0


async def test_get_tension_measurements_after_log(test_db_path):
    """get_tension_measurements returns measurements after logging one."""
    log_result = await _call_tool(
        test_db_path,
        "log_tension_measurement",
        {
            "chapter_id": 1,
            "tension_level": 7,
            "measurement_type": "emotional",
            "notes": "Climax approaching",
        },
    )
    assert not log_result.isError
    logged = json.loads(log_result.content[0].text)
    assert logged["chapter_id"] == 1
    assert logged["tension_level"] == 7

    result = await _call_tool(
        test_db_path, "get_tension_measurements", {"chapter_id": 1}
    )
    assert not result.isError
    measurements = [json.loads(c.text) for c in result.content]
    assert len(measurements) >= 1
    assert any(m["tension_level"] == 7 for m in measurements)


# ---------------------------------------------------------------------------
# log_tension_measurement
# ---------------------------------------------------------------------------


async def test_log_tension_measurement_returns_model(test_db_path):
    """log_tension_measurement creates a measurement and returns TensionMeasurement."""
    result = await _call_tool(
        test_db_path,
        "log_tension_measurement",
        {
            "chapter_id": 1,
            "tension_level": 5,
            "measurement_type": "overall",
            "notes": "Steady tension",
        },
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["id"] is not None
    assert isinstance(data["id"], int)
    assert data["chapter_id"] == 1
    assert data["tension_level"] == 5
    assert data["measurement_type"] == "overall"
    assert data["notes"] == "Steady tension"


async def test_log_tension_measurement_chapter_not_found(test_db_path):
    """log_tension_measurement returns NotFoundResponse for non-existent chapter_id."""
    result = await _call_tool(
        test_db_path,
        "log_tension_measurement",
        {
            "chapter_id": 99999,
            "tension_level": 5,
            "measurement_type": "overall",
        },
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "not_found_message" in data


# ---------------------------------------------------------------------------
# delete_tension_measurement
# ---------------------------------------------------------------------------


async def test_delete_tension_measurement_not_found(test_db_path):
    """delete_tension_measurement returns NotFoundResponse for non-existent ID."""
    result = await _call_tool(
        test_db_path, "delete_tension_measurement", {"tension_id": 99999}
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "not_found_message" in data


async def test_delete_tension_measurement_success(test_db_path):
    """delete_tension_measurement removes a measurement and returns deleted=True."""
    # Log a measurement to get an ID
    log_result = await _call_tool(
        test_db_path,
        "log_tension_measurement",
        {
            "chapter_id": 1,
            "tension_level": 3,
            "measurement_type": "physical",
            "notes": "Low stakes moment",
        },
    )
    assert not log_result.isError
    tension_id = json.loads(log_result.content[0].text)["id"]

    # Delete it
    del_result = await _call_tool(
        test_db_path, "delete_tension_measurement", {"tension_id": tension_id}
    )
    assert not del_result.isError
    data = json.loads(del_result.content[0].text)
    assert data.get("deleted") is True
    assert data.get("id") == tension_id
