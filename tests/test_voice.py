"""In-memory MCP client tests for voice domain tools.

CRITICAL: Uses 'gate_ready' seed — all voice tools are prose-phase tools that
call check_gate, which requires the gate to be certified. The certified_gate
autouse fixture sets up certification before any test runs.

Total voice tools: 5
  get_voice_profile, upsert_voice_profile, get_supernatural_voice_guidelines,
  log_voice_drift, get_voice_drift_log

Tests verify the full MCP protocol path: call_tool -> FastMCP -> tool handler -> SQLite -> response.
MCP session is entered PER-TEST inside _call_tool — anyio cancel scope incompatible with fixtures.

FastMCP serialization rules:
  - Single object: json.loads(result.content[0].text)
  - list[T]: [json.loads(c.text) for c in result.content]
  - Empty list: result.content is empty (no TextContent blocks)

Single-object tools: get_voice_profile, upsert_voice_profile, log_voice_drift
List tools: get_supernatural_voice_guidelines, get_voice_drift_log

Seed data (gate_ready + voice seed inserts):
  - voice_profiles: 1 row (character_id=1)
  - supernatural_voice_guidelines: 1 row (Wraith)
  - voice_drift_log: 1 row (character_id=1)
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
    Uses "voice_db" dir to isolate from other test files.

    The gate_ready seed provides: Characters (id 1-5), Chapters (id 1-3),
    Cultures (id 1), and all data needed to certify the gate.
    """
    db_file = tmp_path_factory.mktemp("voice_db") / "test_voice.db"
    conn = sqlite3.connect(str(db_file))
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA journal_mode=WAL")
    apply_migrations(conn)
    load_seed_profile(conn, "gate_ready")
    conn.commit()
    conn.close()
    return str(db_file)


# ---------------------------------------------------------------------------
# Helper: certify gate before voice tools can run
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session", autouse=True)
def certified_gate(test_db_path):
    """Certify the gate once for the entire session before any voice tool tests run.

    Session-scoped autouse ensures gate is certified before any test in this
    file runs. Without certification, all voice tools return GateViolation.

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
# Session-scoped seed fixture — insert voice domain rows
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session", autouse=True)
def _insert_voice_seed(test_db_path):
    """Insert voice domain rows for testing.

    Session-scoped autouse: runs once before any test in this file.
    The gate_ready seed does NOT populate voice_profiles, supernatural_voice_guidelines,
    or voice_drift_log — this fixture inserts the test rows.

    Depends on certified_gate (same scope), which is ordered first alphabetically
    by pytest fixture dependency resolution. Both are session-scoped.
    """
    conn = sqlite3.connect(test_db_path)
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA journal_mode=WAL")

    # gate_ready seed already has voice_profiles for character_ids 1-5.
    # Insert a 6th character so we can test the None-id CREATE branch.
    conn.execute(
        "INSERT INTO characters (name, role) "
        "VALUES ('Tessan Vel', 'minor')"
    )

    # supernatural_voice_guidelines: 1 additional row for Wraith (gate_ready has Void-Echoes)
    conn.execute(
        "INSERT INTO supernatural_voice_guidelines "
        "(element_name, element_type, writing_rules) "
        "VALUES ('Wraith', 'creature', 'Use fragmented sentences')"
    )

    # voice_drift_log: 1 additional row for character_id=1 (gate_ready already has 1 row)
    conn.execute(
        "INSERT INTO voice_drift_log "
        "(character_id, drift_type, description, severity) "
        "VALUES (1, 'vocabulary', 'Used anachronistic slang', 'minor')"
    )

    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Helper: open/close MCP session inside each test coroutine
# ---------------------------------------------------------------------------


async def _call_tool(db_path: str, tool_name: str, args: dict):
    """Call a voice tool via MCP in-memory protocol.

    Opens and closes session inside this coroutine so anyio cancel scopes
    are entered and exited in the same task context.
    """
    os.environ["NOVEL_DB_PATH"] = db_path
    async with create_connected_server_and_client_session(mcp) as session:
        return await session.call_tool(tool_name, args)


# ---------------------------------------------------------------------------
# Tests: get_voice_profile
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_get_voice_profile_found(test_db_path):
    """get_voice_profile returns VoiceProfile when character has a profile.

    character_id=1 has a voice profile in seed. Verify returned object has
    character_id=1 and a non-None id.
    """
    result = await _call_tool(
        test_db_path, "get_voice_profile", {"character_id": 1}
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "character_id" in data
    assert data["character_id"] == 1
    assert data["id"] is not None


@pytest.mark.anyio
async def test_get_voice_profile_not_found(test_db_path):
    """get_voice_profile returns NotFoundResponse when no profile exists.

    character_id=999 has no voice profile. Verify response has 'not_found_message'.
    """
    result = await _call_tool(
        test_db_path, "get_voice_profile", {"character_id": 999}
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "not_found_message" in data


# ---------------------------------------------------------------------------
# Tests: upsert_voice_profile
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_upsert_voice_profile_create(test_db_path):
    """upsert_voice_profile creates a new profile when profile_id is None.

    character_id=6 (Tessan Vel, inserted by seed fixture) has no profile.
    Insert with profile_id=None (default). Verify returned object has id set
    and correct character_id.
    """
    # Fetch the id of the character inserted by the seed fixture
    conn = sqlite3.connect(test_db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.execute("SELECT id FROM characters WHERE name = 'Tessan Vel'")
    row = cur.fetchone()
    conn.close()
    assert row is not None, "Tessan Vel character not found in DB"
    new_char_id = row["id"]

    result = await _call_tool(
        test_db_path,
        "upsert_voice_profile",
        {
            "character_id": new_char_id,
            "sentence_length": "long",
            "canon_status": "draft",
        },
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "id" in data
    assert data["id"] is not None
    assert data["character_id"] == new_char_id
    assert data["sentence_length"] == "long"


@pytest.mark.anyio
async def test_upsert_voice_profile_update(test_db_path):
    """upsert_voice_profile updates an existing profile when profile_id is provided.

    First fetch the id of character_id=1's profile, then upsert with that id
    and sentence_length='short'. Verify returned object has sentence_length='short'.
    """
    # Fetch existing profile id for character_id=1
    conn = sqlite3.connect(test_db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.execute(
        "SELECT id FROM voice_profiles WHERE character_id = 1"
    )
    row = cur.fetchone()
    conn.close()
    assert row is not None, "voice profile for character_id=1 not found in DB"
    existing_id = row["id"]

    result = await _call_tool(
        test_db_path,
        "upsert_voice_profile",
        {
            "character_id": 1,
            "profile_id": existing_id,
            "sentence_length": "short",
            "canon_status": "draft",
        },
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["sentence_length"] == "short"
    assert data["character_id"] == 1


# ---------------------------------------------------------------------------
# Tests: get_supernatural_voice_guidelines
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_get_supernatural_voice_guidelines(test_db_path):
    """get_supernatural_voice_guidelines returns all guidelines.

    Seed has 1 guideline (Wraith). Verify list has >= 1 item with element_name='Wraith'.
    """
    result = await _call_tool(
        test_db_path, "get_supernatural_voice_guidelines", {}
    )
    assert not result.isError
    items = [json.loads(c.text) for c in result.content]
    assert isinstance(items, list)
    assert len(items) >= 1
    names = [item["element_name"] for item in items]
    assert "Wraith" in names


# ---------------------------------------------------------------------------
# Tests: log_voice_drift
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_log_voice_drift(test_db_path):
    """log_voice_drift creates a new drift log entry and returns VoiceDriftLog with id.

    Append-only: creates a new entry for character_id=1.
    Verify returned object has id set and correct character_id.
    """
    result = await _call_tool(
        test_db_path,
        "log_voice_drift",
        {
            "character_id": 1,
            "description": "test drift entry",
            "drift_type": "syntax",
            "severity": "minor",
        },
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "id" in data
    assert data["id"] is not None
    assert data["character_id"] == 1
    assert data["drift_type"] == "syntax"


# ---------------------------------------------------------------------------
# Tests: get_voice_drift_log
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_get_voice_drift_log(test_db_path):
    """get_voice_drift_log returns drift entries for a character.

    character_id=1 has at least 1 drift entry in seed. Verify list has >= 1
    item and all items have character_id=1.
    """
    result = await _call_tool(
        test_db_path, "get_voice_drift_log", {"character_id": 1}
    )
    assert not result.isError
    items = [json.loads(c.text) for c in result.content]
    assert isinstance(items, list)
    assert len(items) >= 1
    for item in items:
        assert item["character_id"] == 1


@pytest.mark.anyio
async def test_get_voice_drift_log_empty(test_db_path):
    """get_voice_drift_log returns empty list for character with no drift entries.

    character_id=99 has no drift log entries. Verify result.content is empty.
    """
    result = await _call_tool(
        test_db_path, "get_voice_drift_log", {"character_id": 99}
    )
    assert not result.isError
    assert len(result.content) == 0


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
async def test_get_voice_profile_gate_violation(uncertified_db_path):
    """get_voice_profile returns requires_action when gate is uncertified.

    Uses a fresh DB with no gate certification. All voice tools call check_gate,
    which must return a GateViolation response (not raise an error).
    """
    result = await _call_tool(
        uncertified_db_path, "get_voice_profile", {"character_id": 1}
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "requires_action" in data
