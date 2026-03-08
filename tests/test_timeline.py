"""In-memory MCP client tests for timeline domain tools.

CRITICAL: Uses 'gate_ready' seed (NOT 'minimal') — all 8 timeline tools are
prose-phase tools that call check_gate, which requires the gate to be certified.
The gate_ready seed has the data required to pass all 34 gate SQL checks.

Total timeline tools: 8
  get_pov_positions, get_pov_position, get_event, list_events, get_travel_segments,
  validate_travel_realism, upsert_event, upsert_pov_position

Tests verify the full MCP protocol path: call_tool → FastMCP → tool handler → SQLite → response.
MCP session is entered PER-TEST inside _call_tool — anyio cancel scope incompatible with fixtures.

FastMCP serialization rules:
  - Single object: json.loads(result.content[0].text)
  - list[T]: [json.loads(c.text) for c in result.content]
  - Empty list: result.content is empty (no TextContent blocks)

Single-object tools: validate_travel_realism, upsert_event, upsert_pov_position,
                     get_event, get_pov_position
List tools: list_events, get_pov_positions, get_travel_segments
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
# Session-scoped DB fixture — gate_ready seed
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def test_db_path(tmp_path_factory):
    """Create a temp SQLite file with all migrations + gate_ready seed.

    Session-scoped: created once for all tests in this file.
    Uses "timeline_db" dir to isolate from other test files.

    The gate_ready seed ensures:
    - Gate is certifiable (all 34 SQL gate checks pass)
    - Characters, chapters, scenes, etc. exist for timeline operations
    """
    db_file = tmp_path_factory.mktemp("timeline_db") / "test_timeline.db"
    conn = sqlite3.connect(str(db_file))
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA journal_mode=WAL")
    apply_migrations(conn)
    load_seed_profile(conn, "gate_ready")
    conn.commit()
    conn.close()
    return str(db_file)


# ---------------------------------------------------------------------------
# Helper: open/close MCP session inside each test coroutine
# ---------------------------------------------------------------------------


async def _call_tool(db_path: str, tool_name: str, args: dict):
    """Call a timeline tool via MCP in-memory protocol.

    Opens and closes session inside this coroutine so anyio cancel scopes
    are entered and exited in the same task context.
    """
    os.environ["NOVEL_DB_PATH"] = db_path
    async with create_connected_server_and_client_session(mcp) as session:
        return await session.call_tool(tool_name, args)


# ---------------------------------------------------------------------------
# Helper: certify gate before timeline tools can run
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session", autouse=True)
def certified_gate(test_db_path):
    """Certify the gate once for the entire session before any timeline tool tests run.

    Session-scoped autouse ensures gate is certified before any test in this
    file runs. Without certification, all timeline tools return GateViolation.

    Uses synchronous sqlite3 to certify directly — avoids anyio lifecycle issues
    with session-scoped async fixtures.
    """
    import sqlite3 as _sqlite3

    conn = _sqlite3.connect(test_db_path)
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA journal_mode=WAL")

    # Set all gate_checklist_items to passing (gate_ready seed ensures all SQL checks pass)
    conn.execute(
        "UPDATE gate_checklist_items SET is_passing=1, missing_count=0"
    )

    # Set architecture_gate.is_certified = 1 (certify the gate in DB)
    # check_gate looks at architecture_gate WHERE id = 1
    cur = conn.execute("SELECT COUNT(*) FROM architecture_gate")
    count = cur.fetchone()[0]
    if count == 0:
        conn.execute(
            "INSERT INTO architecture_gate (is_certified, certified_by, certified_at) "
            "VALUES (1, 'test-suite', datetime('now'))"
        )
    else:
        conn.execute(
            "UPDATE architecture_gate SET is_certified=1, certified_by='test-suite', "
            "certified_at=datetime('now') WHERE id=1"
        )

    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Tests: upsert_event (create)
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_upsert_event_create(test_db_path):
    """upsert_event without event_id creates a new event row."""
    result = await _call_tool(
        test_db_path,
        "upsert_event",
        {"name": "The Battle of Dawn", "event_type": "conflict", "chapter_id": 1},
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["name"] == "The Battle of Dawn"
    assert data["id"] > 0
    assert data["event_type"] == "conflict"


# ---------------------------------------------------------------------------
# Tests: upsert_event (update)
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_upsert_event_update(test_db_path):
    """upsert_event with event_id updates the existing event row."""
    # Create event first
    create_result = await _call_tool(
        test_db_path,
        "upsert_event",
        {"name": "The Battle of Dawn", "event_type": "conflict", "chapter_id": 1},
    )
    create_data = json.loads(create_result.content[0].text)
    event_id = create_data["id"]

    # Update with the same id, new name
    result = await _call_tool(
        test_db_path,
        "upsert_event",
        {"name": "The Battle of Dusk", "event_type": "conflict", "chapter_id": 1, "event_id": event_id},
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["name"] == "The Battle of Dusk"
    assert data["id"] == event_id


# ---------------------------------------------------------------------------
# Tests: get_event
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_get_event(test_db_path):
    """get_event retrieves an event by primary key."""
    # Create an event to retrieve
    create_result = await _call_tool(
        test_db_path,
        "upsert_event",
        {"name": "The Storm Arrives", "event_type": "plot"},
    )
    create_data = json.loads(create_result.content[0].text)
    event_id = create_data["id"]

    result = await _call_tool(test_db_path, "get_event", {"event_id": event_id})
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["id"] == event_id
    assert data["name"] == "The Storm Arrives"


@pytest.mark.anyio
async def test_get_event_not_found(test_db_path):
    """get_event returns not_found_message for a nonexistent event_id."""
    result = await _call_tool(test_db_path, "get_event", {"event_id": 99999})
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "not_found_message" in data


# ---------------------------------------------------------------------------
# Tests: list_events
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_list_events(test_db_path):
    """list_events returns all events as a list (may be empty or populated)."""
    result = await _call_tool(test_db_path, "list_events", {})
    assert not result.isError
    # list[Event] serializes as N TextContent blocks
    items = [json.loads(c.text) for c in result.content]
    assert isinstance(items, list)


@pytest.mark.anyio
async def test_list_events_by_chapter(test_db_path):
    """list_events filtered by chapter_id returns only events for that chapter."""
    # Ensure at least one event exists for chapter_id=1
    await _call_tool(
        test_db_path,
        "upsert_event",
        {"name": "Chapter 1 Event", "event_type": "plot", "chapter_id": 1},
    )

    result = await _call_tool(test_db_path, "list_events", {"chapter_id": 1})
    assert not result.isError
    items = [json.loads(c.text) for c in result.content]
    assert len(items) > 0
    for item in items:
        assert item["chapter_id"] == 1


# ---------------------------------------------------------------------------
# Tests: upsert_pov_position (create)
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_upsert_pov_position_create(test_db_path):
    """upsert_pov_position creates a new POV position row."""
    result = await _call_tool(
        test_db_path,
        "upsert_pov_position",
        {"character_id": 1, "chapter_id": 1, "day_number": 1},
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["character_id"] == 1
    assert data["chapter_id"] == 1
    assert data["day_number"] == 1


# ---------------------------------------------------------------------------
# Tests: upsert_pov_position (update via ON CONFLICT)
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_upsert_pov_position_update(test_db_path):
    """upsert_pov_position with same character_id+chapter_id updates via ON CONFLICT DO UPDATE."""
    # First upsert to ensure row exists
    await _call_tool(
        test_db_path,
        "upsert_pov_position",
        {"character_id": 1, "chapter_id": 1, "day_number": 1},
    )

    # Update with day_number=5
    result = await _call_tool(
        test_db_path,
        "upsert_pov_position",
        {"character_id": 1, "chapter_id": 1, "day_number": 5},
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["character_id"] == 1
    assert data["chapter_id"] == 1
    assert data["day_number"] == 5


# ---------------------------------------------------------------------------
# Tests: get_pov_positions
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_get_pov_positions(test_db_path):
    """get_pov_positions returns POV positions for a chapter as a list."""
    # Ensure at least one position exists for chapter_id=1
    await _call_tool(
        test_db_path,
        "upsert_pov_position",
        {"character_id": 1, "chapter_id": 1, "day_number": 1},
    )

    result = await _call_tool(test_db_path, "get_pov_positions", {"chapter_id": 1})
    assert not result.isError
    items = [json.loads(c.text) for c in result.content]
    assert isinstance(items, list)
    assert len(items) > 0
    for item in items:
        assert item["chapter_id"] == 1


# ---------------------------------------------------------------------------
# Tests: get_pov_position
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_get_pov_position(test_db_path):
    """get_pov_position retrieves a specific character's position at a chapter."""
    # Ensure the position exists
    await _call_tool(
        test_db_path,
        "upsert_pov_position",
        {"character_id": 1, "chapter_id": 1, "day_number": 1},
    )

    result = await _call_tool(
        test_db_path,
        "get_pov_position",
        {"character_id": 1, "chapter_id": 1},
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["character_id"] == 1
    assert data["chapter_id"] == 1


@pytest.mark.anyio
async def test_get_pov_position_not_found(test_db_path):
    """get_pov_position returns not_found_message for nonexistent pair."""
    result = await _call_tool(
        test_db_path,
        "get_pov_position",
        {"character_id": 99999, "chapter_id": 99999},
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "not_found_message" in data


# ---------------------------------------------------------------------------
# Tests: get_travel_segments
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_get_travel_segments(test_db_path):
    """get_travel_segments returns a list for a character (may be empty — valid state)."""
    result = await _call_tool(test_db_path, "get_travel_segments", {"character_id": 1})
    assert not result.isError
    # Returns list[TravelSegment] — empty list if no segments (no TextContent blocks)
    items = [json.loads(c.text) for c in result.content]
    assert isinstance(items, list)


# ---------------------------------------------------------------------------
# Tests: validate_travel_realism
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_validate_travel_realism_no_args(test_db_path):
    """validate_travel_realism with no args returns is_realistic=False with error message."""
    result = await _call_tool(test_db_path, "validate_travel_realism", {})
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["is_realistic"] is False
    assert len(data["issues"]) > 0


@pytest.mark.anyio
async def test_validate_travel_realism_segment_not_found(test_db_path):
    """validate_travel_realism with nonexistent travel_segment_id returns not found result."""
    result = await _call_tool(
        test_db_path,
        "validate_travel_realism",
        {"travel_segment_id": 99999},
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["is_realistic"] is False
    assert len(data["issues"]) > 0
    assert "not found" in data["issues"][0].lower()
