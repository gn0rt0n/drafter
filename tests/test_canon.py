"""In-memory MCP client tests for canon domain tools.

CRITICAL: Uses 'gate_ready' seed (NOT 'minimal') — all canon tools are
prose-phase tools that call check_gate, which requires the gate to be certified.
The gate_ready seed has the data required to pass all 34 gate SQL checks.

Total canon tools: 7
  get_canon_facts, log_canon_fact, log_decision, get_decisions,
  log_continuity_issue, get_continuity_issues, resolve_continuity_issue

Tests verify the full MCP protocol path: call_tool -> FastMCP -> tool handler -> SQLite -> response.
MCP session is entered PER-TEST inside _call_tool — anyio cancel scope incompatible with fixtures.

FastMCP serialization rules:
  - Single object: json.loads(result.content[0].text)
  - list[T]: [json.loads(c.text) for c in result.content]
  - Empty list: result.content is empty (no TextContent blocks)

Single-object tools: log_canon_fact, log_decision, log_continuity_issue, resolve_continuity_issue
List tools: get_canon_facts, get_decisions, get_continuity_issues
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
    Uses "canon_db" dir to isolate from other test files.

    The gate_ready seed ensures:
    - Gate is certifiable (all 34 SQL gate checks pass)
    - Canon seed data: 1 canon fact (domain="world"), 1 decision (type="plot"),
      1 continuity issue (severity="minor", is_resolved=FALSE)
    """
    db_file = tmp_path_factory.mktemp("canon_db") / "test_canon.db"
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
    """Call a canon tool via MCP in-memory protocol.

    Opens and closes session inside this coroutine so anyio cancel scopes
    are entered and exited in the same task context.
    """
    os.environ["NOVEL_DB_PATH"] = db_path
    async with create_connected_server_and_client_session(mcp) as session:
        return await session.call_tool(tool_name, args)


# ---------------------------------------------------------------------------
# Helper: certify gate before canon tools can run
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session", autouse=True)
def certified_gate(test_db_path):
    """Certify the gate once for the entire session before any canon tool tests run.

    Session-scoped autouse ensures gate is certified before any test in this
    file runs. Without certification, all canon tools return GateViolation.

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
# Tests: get_canon_facts
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_get_canon_facts(test_db_path):
    """get_canon_facts returns canon facts filtered by domain.

    Seed has 1 canon fact with domain='world'. Verifying the filter works
    and returned items have the expected domain and fact keys.
    """
    result = await _call_tool(test_db_path, "get_canon_facts", {"domain": "world"})
    assert not result.isError
    items = [json.loads(c.text) for c in result.content]
    assert isinstance(items, list)
    assert len(items) >= 1
    for item in items:
        assert item["domain"] == "world"
        assert "fact" in item


# ---------------------------------------------------------------------------
# Tests: log_canon_fact
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_log_canon_fact(test_db_path):
    """log_canon_fact creates a new canon fact and returns the created record.

    Verifies the returned object has an id and correct domain.
    """
    result = await _call_tool(
        test_db_path,
        "log_canon_fact",
        {"fact": "Test fact", "domain": "magic"},
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "id" in data
    assert data["id"] is not None
    assert data["domain"] == "magic"
    assert data["fact"] == "Test fact"


# ---------------------------------------------------------------------------
# Tests: log_decision
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_log_decision(test_db_path):
    """log_decision creates a new decisions_log entry and returns it.

    Verifies the returned object has an id and correct decision_type.
    """
    result = await _call_tool(
        test_db_path,
        "log_decision",
        {"description": "Use silver ink", "decision_type": "worldbuilding"},
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "id" in data
    assert data["id"] is not None
    assert data["decision_type"] == "worldbuilding"
    assert data["description"] == "Use silver ink"


# ---------------------------------------------------------------------------
# Tests: get_decisions
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_get_decisions(test_db_path):
    """get_decisions returns decisions list; decision_type filter works.

    Seed has 1 decision with decision_type='plot'. Verify the unfiltered list
    has at least 1 item, and the filtered list contains only 'plot' decisions.
    """
    # Unfiltered — at least the seed decision
    result = await _call_tool(test_db_path, "get_decisions", {})
    assert not result.isError
    items = [json.loads(c.text) for c in result.content]
    assert isinstance(items, list)
    assert len(items) >= 1

    # Filtered by decision_type='plot'
    result2 = await _call_tool(test_db_path, "get_decisions", {"decision_type": "plot"})
    assert not result2.isError
    plot_items = [json.loads(c.text) for c in result2.content]
    assert isinstance(plot_items, list)
    for item in plot_items:
        assert item["decision_type"] == "plot"


# ---------------------------------------------------------------------------
# Tests: log_continuity_issue
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_log_continuity_issue(test_db_path):
    """log_continuity_issue creates a new issue and returns it.

    Verifies the returned object has an id and correct severity.
    """
    result = await _call_tool(
        test_db_path,
        "log_continuity_issue",
        {"description": "Eye color inconsistency", "severity": "major"},
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "id" in data
    assert data["id"] is not None
    assert data["severity"] == "major"
    assert data["description"] == "Eye color inconsistency"


# ---------------------------------------------------------------------------
# Tests: get_continuity_issues
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_get_continuity_issues(test_db_path):
    """get_continuity_issues returns unresolved issues; severity filter works.

    Seed has 1 unresolved minor continuity issue. Verify:
    - Unfiltered list has at least 1 item.
    - Filtered by severity='minor' returns only minor-severity items.
    """
    result = await _call_tool(test_db_path, "get_continuity_issues", {})
    assert not result.isError
    items = [json.loads(c.text) for c in result.content]
    assert isinstance(items, list)
    assert len(items) >= 1

    # Filtered by severity='minor'
    result2 = await _call_tool(
        test_db_path, "get_continuity_issues", {"severity": "minor"}
    )
    assert not result2.isError
    minor_items = [json.loads(c.text) for c in result2.content]
    for item in minor_items:
        assert item["severity"] == "minor"


# ---------------------------------------------------------------------------
# Tests: resolve_continuity_issue
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_resolve_continuity_issue(test_db_path):
    """resolve_continuity_issue marks an issue as resolved and returns it.

    First logs a new issue to get a known id, then resolves it. Verifies
    the returned object has is_resolved=True.
    """
    # Log a fresh issue so we have a known ID
    log_result = await _call_tool(
        test_db_path,
        "log_continuity_issue",
        {"description": "Hair color inconsistency", "severity": "minor"},
    )
    assert not log_result.isError
    log_data = json.loads(log_result.content[0].text)
    issue_id = log_data["id"]

    # Resolve the issue
    result = await _call_tool(
        test_db_path,
        "resolve_continuity_issue",
        {"issue_id": issue_id, "resolution_note": "Fixed in ch3"},
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["is_resolved"] is True
    assert data["id"] == issue_id


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
async def test_get_canon_facts_gate_violation(uncertified_db_path):
    """get_canon_facts returns requires_action when gate is uncertified.

    Uses a fresh DB with no gate certification. All canon tools call check_gate,
    which must return a GateViolation response (not raise an error).
    """
    result = await _call_tool(uncertified_db_path, "get_canon_facts", {"domain": "magic"})
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "requires_action" in data


# ---------------------------------------------------------------------------
# Error contract tests: not-found responses
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_resolve_continuity_issue_not_found(test_db_path):
    """resolve_continuity_issue returns not_found_message for missing issue_id.

    issue_id=99999 cannot exist in seed data. resolve_continuity_issue does a
    SELECT-back after UPDATE — if no row found it returns NotFoundResponse.
    resolution_note is a required parameter for the tool.
    """
    result = await _call_tool(
        test_db_path,
        "resolve_continuity_issue",
        {"issue_id": 99999, "resolution_note": "No such issue"},
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data is None or "not_found_message" in data
