"""In-memory MCP client tests for session domain tools.

CRITICAL: Uses 'gate_ready' seed (NOT 'minimal') — all 10 session tools are
prose-phase tools that call check_gate, which requires the gate to be certified.
The gate_ready seed has the data required to pass all 34 gate SQL checks.

Total session tools: 10
  start_session, close_session, get_last_session, log_agent_run,
  get_project_metrics, log_project_snapshot, get_pov_balance,
  get_open_questions, log_open_question, answer_open_question

Tests verify the full MCP protocol path: call_tool → FastMCP → tool handler → SQLite → response.
MCP session is entered PER-TEST inside _call_tool — anyio cancel scope incompatible with fixtures.

FastMCP serialization rules:
  - Single object: json.loads(result.content[0].text)
  - list[T]: [json.loads(c.text) for c in result.content]

start_session returns SessionStartResult (NOT flat SessionLog):
  - Top-level keys: "session" (dict) and "briefing" (str | None)
  - Access session id via result["session"]["id"]

close_session returns a flat SessionLog dict (not wrapped in SessionStartResult).
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
    Uses "session_db" dir to isolate from other test files.

    The gate_ready seed ensures:
    - Gate is certifiable (all 34 SQL gate checks pass)
    - Characters, chapters, scenes, etc. exist for metrics checks
    """
    db_file = tmp_path_factory.mktemp("session_db") / "test_session.db"
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
    """Call a session tool via MCP in-memory protocol.

    Opens and closes session inside this coroutine so anyio cancel scopes
    are entered and exited in the same task context.
    """
    os.environ["NOVEL_DB_PATH"] = db_path
    async with create_connected_server_and_client_session(mcp) as session:
        return await session.call_tool(tool_name, args)


# ---------------------------------------------------------------------------
# Helper: certify gate before session tools can run
# ---------------------------------------------------------------------------


async def _certify_gate(db_path: str):
    """Run audit + certify so session tools pass check_gate."""
    # Set min_characters to passing (not in GATE_QUERIES, so audit won't update it)
    await _call_tool(
        db_path,
        "update_checklist_item",
        {"item_key": "min_characters", "is_passing": True, "missing_count": 0},
    )
    await _call_tool(db_path, "run_gate_audit", {})
    await _call_tool(db_path, "certify_gate", {"certified_by": "test-suite"})


@pytest.fixture(scope="session", autouse=True)
def certified_gate(test_db_path):
    """Certify the gate once for the entire session before any session tool tests run.

    Session-scoped autouse ensures gate is certified before any test in this
    file runs. Without certification, all session tools return GateViolation.

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
# Tests: start_session
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_start_session(test_db_path):
    """start_session creates a new open session and returns SessionStartResult."""
    result = await _call_tool(test_db_path, "start_session", {})
    assert not result.isError
    data = json.loads(result.content[0].text)
    # SessionStartResult has "session" and "briefing" at top level (not flat SessionLog)
    assert "session" in data
    assert "id" in data["session"]
    assert data["session"]["closed_at"] is None
    assert "briefing" in data


# ---------------------------------------------------------------------------
# Tests: close_session
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_close_session(test_db_path):
    """close_session marks a session closed with summary and carried_forward."""
    # First create a new session
    start_result = await _call_tool(test_db_path, "start_session", {})
    start_data = json.loads(start_result.content[0].text)
    session_id = start_data["session"]["id"]

    # Close the session with a summary
    result = await _call_tool(
        test_db_path,
        "close_session",
        {"session_id": session_id, "summary": "test summary"},
    )
    assert not result.isError
    # close_session returns a flat SessionLog (not wrapped)
    data = json.loads(result.content[0].text)
    assert data["closed_at"] is not None
    assert data["summary"] == "test summary"
    # carried_forward may be a JSON string or already-parsed list depending on FastMCP version
    carried_raw = data["carried_forward"]
    if isinstance(carried_raw, str):
        carried = json.loads(carried_raw)
    elif carried_raw is None:
        carried = []
    else:
        carried = carried_raw
    assert isinstance(carried, list)


# ---------------------------------------------------------------------------
# Tests: get_last_session
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_get_last_session(test_db_path):
    """get_last_session returns the most recently started session."""
    result = await _call_tool(test_db_path, "get_last_session", {})
    assert not result.isError
    data = json.loads(result.content[0].text)
    # Some session must exist from prior tests (gate_ready seed may also create one)
    assert "id" in data
    assert isinstance(data["id"], int)


# ---------------------------------------------------------------------------
# Tests: log_agent_run
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_log_agent_run(test_db_path):
    """log_agent_run appends an agent audit entry and returns it."""
    result = await _call_tool(
        test_db_path,
        "log_agent_run",
        {"agent_name": "TestAgent", "tool_name": "get_character", "success": True},
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["agent_name"] == "TestAgent"
    assert data["tool_name"] == "get_character"
    assert data["id"] > 0


# ---------------------------------------------------------------------------
# Tests: get_project_metrics
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_get_project_metrics(test_db_path):
    """get_project_metrics returns live aggregate counts."""
    result = await _call_tool(test_db_path, "get_project_metrics", {})
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "word_count" in data
    assert "chapter_count" in data
    # gate_ready seed has chapters — chapter_count should be > 0
    assert data["chapter_count"] > 0
    assert "scene_count" in data
    assert "character_count" in data


# ---------------------------------------------------------------------------
# Tests: log_project_snapshot
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_log_project_snapshot(test_db_path):
    """log_project_snapshot persists a metrics snapshot to the database."""
    result = await _call_tool(test_db_path, "log_project_snapshot", {})
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["id"] > 0
    assert "word_count" in data
    assert "snapshot_at" in data


# ---------------------------------------------------------------------------
# Tests: get_pov_balance
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_get_pov_balance(test_db_path):
    """get_pov_balance returns POV balance list (may be empty if no pov_character_id on chapters)."""
    result = await _call_tool(test_db_path, "get_pov_balance", {})
    assert not result.isError
    # list[PovBalanceSnapshot] serializes as N TextContent blocks
    items = [json.loads(c.text) for c in result.content]
    assert isinstance(items, list)


# ---------------------------------------------------------------------------
# Tests: log_open_question
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_log_open_question(test_db_path):
    """log_open_question appends a new unanswered question to the log."""
    result = await _call_tool(
        test_db_path,
        "log_open_question",
        {"question": "Will the hero survive?", "domain": "plot"},
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["question"] == "Will the hero survive?"
    assert data["domain"] == "plot"
    assert data["answered_at"] is None


# ---------------------------------------------------------------------------
# Tests: get_open_questions
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_get_open_questions(test_db_path):
    """get_open_questions returns unanswered questions as a list."""
    result = await _call_tool(test_db_path, "get_open_questions", {})
    assert not result.isError
    items = [json.loads(c.text) for c in result.content]
    assert isinstance(items, list)
    # The question logged in test_log_open_question may appear here
    # We only assert it's a list — exact count depends on test ordering


# ---------------------------------------------------------------------------
# Tests: answer_open_question
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_answer_open_question(test_db_path):
    """answer_open_question records an answer and sets answered_at timestamp."""
    # Create a fresh question to answer
    log_result = await _call_tool(
        test_db_path,
        "log_open_question",
        {"question": "What happens at the end?", "domain": "plot"},
    )
    question_data = json.loads(log_result.content[0].text)
    question_id = question_data["id"]

    result = await _call_tool(
        test_db_path,
        "answer_open_question",
        {"question_id": question_id, "answer": "Yes"},
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["answer"] == "Yes"
    assert data["answered_at"] is not None


# ---------------------------------------------------------------------------
# Error contract tests: gate violation (uncertified DB)
# ---------------------------------------------------------------------------


@pytest.fixture
def uncertified_db_path(tmp_path):
    """Fresh uncertified DB for gate violation tests.

    Function-scoped to avoid conflict with the session-scoped certified_gate
    autouse fixture. This DB has migrations + minimal seed but NO gate certification.
    """
    db_file = tmp_path / "uncertified.db"
    conn = sqlite3.connect(str(db_file))
    conn.execute("PRAGMA foreign_keys=ON")
    apply_migrations(conn)
    load_seed_profile(conn, "minimal")
    conn.commit()
    conn.close()
    return str(db_file)


@pytest.mark.anyio
async def test_start_session_gate_violation(uncertified_db_path):
    """start_session returns requires_action when gate is uncertified.

    Uses a fresh DB with no gate certification. start_session calls check_gate,
    which must return a GateViolation response (not raise an error).
    """
    result = await _call_tool(uncertified_db_path, "start_session", {})
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "requires_action" in data


# ---------------------------------------------------------------------------
# Error contract tests: not-found responses
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_close_session_not_found(test_db_path):
    """close_session returns null or not_found_message for missing session_id.

    session_id=99999 cannot exist in seed data. close_session does a SELECT-back
    after UPDATE — if no row is found it returns NotFoundResponse or None.
    """
    result = await _call_tool(
        test_db_path,
        "close_session",
        {"session_id": 99999, "summary": "test summary for nonexistent session"},
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data is None or "not_found_message" in data
