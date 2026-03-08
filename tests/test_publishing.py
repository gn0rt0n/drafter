"""In-memory MCP client tests for publishing domain tools.

CRITICAL: Uses 'gate_ready' seed — all publishing tools are prose-phase tools
that call check_gate, which requires the gate to be certified. The certified_gate
autouse fixture sets up certification before any test runs.

Total publishing tools: 5
  get_publishing_assets, upsert_publishing_asset, get_submissions,
  log_submission, update_submission

Tests verify the full MCP protocol path: call_tool -> FastMCP -> tool handler -> SQLite -> response.
MCP session is entered PER-TEST inside _call_tool — anyio cancel scope incompatible with fixtures.

FastMCP serialization rules:
  - Single object: json.loads(result.content[0].text)
  - list[T]: [json.loads(c.text) for c in result.content]
  - Empty list: result.content is empty (no TextContent blocks)

Single-object tools: upsert_publishing_asset, log_submission, update_submission
List tools: get_publishing_assets, get_submissions

Seed data (gate_ready + publishing seed inserts):
  - publishing_assets: 2 rows (query_letter, synopsis)
  - submission_tracker: 1 row (pending, Agent Smith)
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
    Uses "publishing_db" dir to isolate from other test files.

    The gate_ready seed provides: Characters (id 1-5), Chapters (id 1-3),
    and all data needed to certify the gate.
    """
    db_file = tmp_path_factory.mktemp("publishing_db") / "test_publishing.db"
    conn = sqlite3.connect(str(db_file))
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA journal_mode=WAL")
    apply_migrations(conn)
    load_seed_profile(conn, "gate_ready")
    conn.commit()
    conn.close()
    return str(db_file)


# ---------------------------------------------------------------------------
# Helper: certify gate before publishing tools can run
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session", autouse=True)
def certified_gate(test_db_path):
    """Certify the gate once for the entire session before any publishing tool tests run.

    Session-scoped autouse ensures gate is certified before any test in this
    file runs. Without certification, all publishing tools return GateViolation.

    Uses synchronous sqlite3 to certify directly — avoids anyio lifecycle issues
    with session-scoped async fixtures.
    """
    conn = sqlite3.connect(test_db_path)
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA journal_mode=WAL")

    conn.execute(
        "UPDATE gate_checklist_items SET is_passing=1, missing_count=0"
    )

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
# Session-scoped seed fixture — insert publishing domain rows
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session", autouse=True)
def _insert_publishing_seed(test_db_path):
    """Insert publishing domain rows for testing.

    Session-scoped autouse: runs once before any test in this file.
    The gate_ready seed does NOT populate publishing_assets or submission_tracker
    — this fixture inserts the test rows.
    """
    conn = sqlite3.connect(test_db_path)
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA journal_mode=WAL")

    # publishing_assets: 2 rows
    conn.execute(
        "INSERT INTO publishing_assets (asset_type, title, content) "
        "VALUES ('query_letter', 'Test Query', 'Dear Agent...')"
    )
    conn.execute(
        "INSERT INTO publishing_assets (asset_type, title, content) "
        "VALUES ('synopsis', 'Test Synopsis', 'In a world...')"
    )

    # submission_tracker: 1 row
    conn.execute(
        "INSERT INTO submission_tracker "
        "(agency_or_publisher, submitted_at, status) "
        "VALUES ('Agent Smith', '2024-01-01', 'pending')"
    )

    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Helper: open/close MCP session inside each test coroutine
# ---------------------------------------------------------------------------


async def _call_tool(db_path: str, tool_name: str, args: dict):
    """Call a publishing tool via MCP in-memory protocol.

    Opens and closes session inside this coroutine so anyio cancel scopes
    are entered and exited in the same task context.
    """
    os.environ["NOVEL_DB_PATH"] = db_path
    async with create_connected_server_and_client_session(mcp) as session:
        return await session.call_tool(tool_name, args)


# ---------------------------------------------------------------------------
# Tests: get_publishing_assets
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_get_publishing_assets_all(test_db_path):
    """get_publishing_assets returns all assets when no filter is given.

    Seed has 2 publishing assets (query_letter + synopsis).
    Verify list has >= 2 items.
    """
    result = await _call_tool(test_db_path, "get_publishing_assets", {})
    assert not result.isError
    items = [json.loads(c.text) for c in result.content]
    assert isinstance(items, list)
    assert len(items) >= 2


@pytest.mark.anyio
async def test_get_publishing_assets_filtered(test_db_path):
    """get_publishing_assets with asset_type filter returns only matching items.

    Filter asset_type='query_letter'. Seed has 1 query_letter asset.
    All returned items must have asset_type='query_letter'.
    """
    result = await _call_tool(
        test_db_path,
        "get_publishing_assets",
        {"asset_type": "query_letter"},
    )
    assert not result.isError
    items = [json.loads(c.text) for c in result.content]
    assert isinstance(items, list)
    assert len(items) >= 1
    for item in items:
        assert item["asset_type"] == "query_letter"


# ---------------------------------------------------------------------------
# Tests: upsert_publishing_asset
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_upsert_publishing_asset_create(test_db_path):
    """upsert_publishing_asset creates a new asset when asset_id is None.

    asset_id=None (default): plain INSERT creates new asset.
    Verify returned object has id set and correct title.
    """
    result = await _call_tool(
        test_db_path,
        "upsert_publishing_asset",
        {
            "title": "New Query Letter",
            "content": "Hi, I have a novel.",
            "asset_type": "query_letter",
        },
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "id" in data
    assert data["id"] is not None
    assert data["title"] == "New Query Letter"
    assert data["asset_type"] == "query_letter"


@pytest.mark.anyio
async def test_upsert_publishing_asset_update(test_db_path):
    """upsert_publishing_asset updates an existing asset when asset_id is provided.

    Use the first seed asset (id=1, title='Test Query'). Update title to
    'Updated Query'. Verify returned object has new title.
    """
    # Fetch the id of the first inserted asset
    conn = sqlite3.connect(test_db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.execute(
        "SELECT id FROM publishing_assets WHERE title = 'Test Query'"
    )
    row = cur.fetchone()
    conn.close()
    assert row is not None, "Test Query asset not found in DB"
    asset_id = row["id"]

    result = await _call_tool(
        test_db_path,
        "upsert_publishing_asset",
        {
            "asset_id": asset_id,
            "title": "Updated Query",
            "content": "Dear Agent, my novel is updated.",
            "asset_type": "query_letter",
        },
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["title"] == "Updated Query"
    assert data["id"] == asset_id


# ---------------------------------------------------------------------------
# Tests: get_submissions
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_get_submissions_all(test_db_path):
    """get_submissions returns all submission entries when no filter is given.

    Seed has 1 submission (Agent Smith, pending). Verify list has >= 1 item.
    """
    result = await _call_tool(test_db_path, "get_submissions", {})
    assert not result.isError
    items = [json.loads(c.text) for c in result.content]
    assert isinstance(items, list)
    assert len(items) >= 1


@pytest.mark.anyio
async def test_get_submissions_filtered(test_db_path):
    """get_submissions with status filter returns only matching submissions.

    Filter status='pending'. Seed has 1 pending submission.
    All returned items must have status='pending'.
    """
    result = await _call_tool(
        test_db_path,
        "get_submissions",
        {"status": "pending"},
    )
    assert not result.isError
    items = [json.loads(c.text) for c in result.content]
    assert isinstance(items, list)
    assert len(items) >= 1
    for item in items:
        assert item["status"] == "pending"


# ---------------------------------------------------------------------------
# Tests: log_submission
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_log_submission(test_db_path):
    """log_submission creates a new submission entry and returns SubmissionEntry with id.

    Append-only: creates a new submission record.
    Verify returned object has id set and correct fields.
    """
    result = await _call_tool(
        test_db_path,
        "log_submission",
        {
            "agency_or_publisher": "Publisher X",
            "submitted_at": "2024-06-01",
            "status": "pending",
        },
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "id" in data
    assert data["id"] is not None
    assert data["agency_or_publisher"] == "Publisher X"
    assert data["submitted_at"] == "2024-06-01"
    assert data["status"] == "pending"


# ---------------------------------------------------------------------------
# Tests: update_submission
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_update_submission_found(test_db_path):
    """update_submission updates an existing submission and returns updated SubmissionEntry.

    Use the seed submission (Agent Smith). Update status to 'accepted'.
    Verify returned object has status='accepted'.
    """
    # Fetch the id of the seeded submission
    conn = sqlite3.connect(test_db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.execute(
        "SELECT id FROM submission_tracker WHERE agency_or_publisher = 'Agent Smith'"
    )
    row = cur.fetchone()
    conn.close()
    assert row is not None, "Agent Smith submission not found in DB"
    submission_id = row["id"]

    result = await _call_tool(
        test_db_path,
        "update_submission",
        {
            "submission_id": submission_id,
            "status": "accepted",
            "response_notes": "Accepted with revisions",
        },
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["status"] == "accepted"
    assert data["id"] == submission_id


@pytest.mark.anyio
async def test_update_submission_not_found(test_db_path):
    """update_submission returns NotFoundResponse when submission_id does not exist.

    submission_id=999 does not exist. Verify response has 'not_found_message'.
    """
    result = await _call_tool(
        test_db_path,
        "update_submission",
        {
            "submission_id": 999,
            "status": "accepted",
        },
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "not_found_message" in data


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
async def test_get_publishing_assets_gate_violation(uncertified_db_path):
    """get_publishing_assets returns requires_action when gate is uncertified.

    Uses a fresh DB with no gate certification. All publishing tools call check_gate,
    which must return a GateViolation response (not raise an error).
    """
    result = await _call_tool(uncertified_db_path, "get_publishing_assets", {})
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "requires_action" in data
