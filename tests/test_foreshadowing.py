"""In-memory MCP client tests for foreshadowing domain tools.

CRITICAL: Uses 'gate_ready' seed (NOT 'minimal') — all foreshadowing tools are
prose-phase tools that call check_gate, which requires the gate to be certified.
The gate_ready seed has the data required to pass all 34 gate SQL checks.

Total foreshadowing tools: 18 (10 original + 8 new)
  get_foreshadowing, get_prophecies, get_motifs, get_motif_occurrences,
  get_thematic_mirrors, get_opposition_pairs, log_foreshadowing, log_motif_occurrence,
  delete_foreshadowing, delete_motif_occurrence,
  upsert_motif, delete_motif, upsert_prophecy, delete_prophecy,
  upsert_thematic_mirror, delete_thematic_mirror,
  upsert_opposition_pair, delete_opposition_pair

Tests verify the full MCP protocol path: call_tool -> FastMCP -> tool handler -> SQLite -> response.
MCP session is entered PER-TEST inside _call_tool — anyio cancel scope incompatible with fixtures.

FastMCP serialization rules:
  - Single object: json.loads(result.content[0].text)
  - list[T]: [json.loads(c.text) for c in result.content]
  - Empty list: result.content is empty (no TextContent blocks)

Single-object tools: log_foreshadowing, log_motif_occurrence
List tools: get_foreshadowing, get_prophecies, get_motifs, get_motif_occurrences,
            get_thematic_mirrors, get_opposition_pairs

Seed data (gate_ready):
  - foreshadowing_registry: 1 row (status='planted', plant_chapter_id=1)
  - prophecy_registry: 1 row (status='active')
  - motif_registry: 1 row (name='Dying Embers', id=1)
  - motif_occurrences: 1 row (motif_id=1, chapter_id=1)
  - thematic_mirrors: 1 row
  - opposition_pairs: 1 row
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
    Uses "foreshadowing_db" dir to isolate from other test files.

    The gate_ready seed ensures:
    - Gate is certifiable (all 34 SQL gate checks pass)
    - Foreshadowing seed data populated in all 6 foreshadowing tables
    """
    db_file = tmp_path_factory.mktemp("foreshadowing_db") / "test_foreshadowing.db"
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
    """Call a foreshadowing tool via MCP in-memory protocol.

    Opens and closes session inside this coroutine so anyio cancel scopes
    are entered and exited in the same task context.
    """
    os.environ["NOVEL_DB_PATH"] = db_path
    async with create_connected_server_and_client_session(mcp) as session:
        return await session.call_tool(tool_name, args)


# ---------------------------------------------------------------------------
# Helper: certify gate before foreshadowing tools can run
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session", autouse=True)
def certified_gate(test_db_path):
    """Certify the gate once for the entire session before any foreshadowing tool tests run.

    Session-scoped autouse ensures gate is certified before any test in this
    file runs. Without certification, all foreshadowing tools return GateViolation.

    Uses synchronous sqlite3 to certify directly — avoids anyio lifecycle issues
    with session-scoped async fixtures.
    """
    import sqlite3 as _sqlite3

    conn = _sqlite3.connect(test_db_path)
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
# Tests: get_foreshadowing
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_get_foreshadowing(test_db_path):
    """get_foreshadowing returns foreshadowing entries; status filter works.

    Seed has 1 entry with status='planted'. Verify:
    - Unfiltered: at least 1 item
    - status='planted': items have status='planted'
    """
    result = await _call_tool(test_db_path, "get_foreshadowing", {})
    assert not result.isError
    items = [json.loads(c.text) for c in result.content]
    assert isinstance(items, list)
    assert len(items) >= 1

    # Filtered by status='planted'
    result2 = await _call_tool(
        test_db_path, "get_foreshadowing", {"status": "planted"}
    )
    assert not result2.isError
    planted = [json.loads(c.text) for c in result2.content]
    for item in planted:
        assert item["status"] == "planted"


# ---------------------------------------------------------------------------
# Tests: get_prophecies
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_get_prophecies(test_db_path):
    """get_prophecies returns all prophecy registry entries.

    Seed has 1 active prophecy. Verify list has at least 1 item.
    """
    result = await _call_tool(test_db_path, "get_prophecies", {})
    assert not result.isError
    items = [json.loads(c.text) for c in result.content]
    assert isinstance(items, list)
    assert len(items) >= 1


# ---------------------------------------------------------------------------
# Tests: get_motifs
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_get_motifs(test_db_path):
    """get_motifs returns all motif registry entries.

    Seed has 1 motif ('Dying Embers', id=1). Verify list has at least 1 item.
    """
    result = await _call_tool(test_db_path, "get_motifs", {})
    assert not result.isError
    items = [json.loads(c.text) for c in result.content]
    assert isinstance(items, list)
    assert len(items) >= 1


# ---------------------------------------------------------------------------
# Tests: get_motif_occurrences
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_get_motif_occurrences(test_db_path):
    """get_motif_occurrences returns occurrences; chapter_id filter works.

    Seed has 1 occurrence (motif_id=1, chapter_id=1).
    - Unfiltered: at least 1 item
    - chapter_id=999: empty list
    """
    result = await _call_tool(test_db_path, "get_motif_occurrences", {})
    assert not result.isError
    items = [json.loads(c.text) for c in result.content]
    assert isinstance(items, list)
    assert len(items) >= 1

    # Nonexistent chapter: empty
    result2 = await _call_tool(
        test_db_path, "get_motif_occurrences", {"chapter_id": 999}
    )
    assert not result2.isError
    empty = [json.loads(c.text) for c in result2.content]
    assert empty == []


# ---------------------------------------------------------------------------
# Tests: get_thematic_mirrors
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_get_thematic_mirrors(test_db_path):
    """get_thematic_mirrors returns all thematic mirror pairs.

    Seed has 1 thematic mirror. Verify list has at least 1 item.
    """
    result = await _call_tool(test_db_path, "get_thematic_mirrors", {})
    assert not result.isError
    items = [json.loads(c.text) for c in result.content]
    assert isinstance(items, list)
    assert len(items) >= 1


# ---------------------------------------------------------------------------
# Tests: get_opposition_pairs
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_get_opposition_pairs(test_db_path):
    """get_opposition_pairs returns all opposition pairs.

    Seed has 1 opposition pair. Verify list has at least 1 item.
    """
    result = await _call_tool(test_db_path, "get_opposition_pairs", {})
    assert not result.isError
    items = [json.loads(c.text) for c in result.content]
    assert isinstance(items, list)
    assert len(items) >= 1


# ---------------------------------------------------------------------------
# Tests: log_foreshadowing (insert)
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_log_foreshadowing_insert(test_db_path):
    """log_foreshadowing creates a new foreshadowing entry (None-id branch).

    Verifies the returned object has an id and default status='planted'.
    """
    result = await _call_tool(
        test_db_path,
        "log_foreshadowing",
        {"description": "Crow on windowsill", "plant_chapter_id": 1},
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "id" in data
    assert data["id"] is not None
    assert data["status"] == "planted"
    assert data["description"] == "Crow on windowsill"


# ---------------------------------------------------------------------------
# Tests: log_foreshadowing (update / upsert)
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_log_foreshadowing_update(test_db_path):
    """log_foreshadowing upserts an existing entry when foreshadowing_id is provided.

    First inserts a new entry (getting its id), then updates with payoff_chapter_id=5
    and status='paid_off'. Verifies the returned object has the updated values.
    """
    # Insert first
    insert_result = await _call_tool(
        test_db_path,
        "log_foreshadowing",
        {"description": "Raven feather left on doorstep", "plant_chapter_id": 2},
    )
    assert not insert_result.isError
    insert_data = json.loads(insert_result.content[0].text)
    entry_id = insert_data["id"]

    # Update with payoff info — use chapter_id=3 (exists in gate_ready seed)
    result = await _call_tool(
        test_db_path,
        "log_foreshadowing",
        {
            "foreshadowing_id": entry_id,
            "description": "Raven feather left on doorstep",
            "plant_chapter_id": 2,
            "payoff_chapter_id": 3,
            "status": "paid_off",
        },
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["payoff_chapter_id"] == 3
    assert data["status"] == "paid_off"
    assert data["id"] == entry_id


# ---------------------------------------------------------------------------
# Tests: log_motif_occurrence
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_log_motif_occurrence(test_db_path):
    """log_motif_occurrence creates a new motif occurrence (append-only).

    Uses motif_id=1 (seed 'Dying Embers' motif). Verifies the returned object
    has the correct motif_id and chapter_id.
    """
    result = await _call_tool(
        test_db_path,
        "log_motif_occurrence",
        {
            "motif_id": 1,
            "chapter_id": 2,
            "description": "Crow motif recurs",
        },
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["motif_id"] == 1
    assert data["chapter_id"] == 2
    assert data["description"] == "Crow motif recurs"


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
async def test_get_foreshadowing_gate_violation(uncertified_db_path):
    """get_foreshadowing returns requires_action when gate is uncertified.

    Uses a fresh DB with no gate certification. All foreshadowing tools call check_gate,
    which must return a GateViolation response (not raise an error).
    """
    result = await _call_tool(uncertified_db_path, "get_foreshadowing", {})
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "requires_action" in data


# ---------------------------------------------------------------------------
# Tests: upsert_motif (Task 1)
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_upsert_motif_create(test_db_path):
    """upsert_motif creates a new motif when motif_id is None.

    Uses required fields: name, description. Verifies returned object has an id
    and matches the provided name.
    """
    result = await _call_tool(
        test_db_path,
        "upsert_motif",
        {
            "name": "Dark Water",
            "description": "Recurring imagery of still, dark water signifying death",
            "motif_type": "symbol",
        },
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "id" in data
    assert data["id"] is not None
    assert data["name"] == "Dark Water"


@pytest.mark.anyio
async def test_upsert_motif_update(test_db_path):
    """upsert_motif updates an existing motif when motif_id is provided.

    First creates a motif, then updates its description. Verifies the
    same id is returned with the updated description.
    """
    # Create first
    create_result = await _call_tool(
        test_db_path,
        "upsert_motif",
        {
            "name": "Broken Mirror",
            "description": "Original description",
        },
    )
    assert not create_result.isError
    create_data = json.loads(create_result.content[0].text)
    motif_id = create_data["id"]

    # Update with id
    result = await _call_tool(
        test_db_path,
        "upsert_motif",
        {
            "motif_id": motif_id,
            "name": "Broken Mirror",
            "description": "Updated description about shattered identity",
        },
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["id"] == motif_id
    assert data["description"] == "Updated description about shattered identity"


@pytest.mark.anyio
async def test_upsert_motif_gate_violation(uncertified_db_path):
    """upsert_motif returns GateViolation on uncertified gate."""
    result = await _call_tool(
        uncertified_db_path,
        "upsert_motif",
        {"name": "Test", "description": "Test desc"},
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "requires_action" in data


# ---------------------------------------------------------------------------
# Tests: delete_motif (Task 1)
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_delete_motif_success(test_db_path):
    """delete_motif deletes an existing motif by id.

    Creates a new motif (to avoid affecting seed data), then deletes it.
    Verifies {"deleted": True, "id": N} is returned.
    """
    create_result = await _call_tool(
        test_db_path,
        "upsert_motif",
        {"name": "Ephemeral Shadow", "description": "To be deleted"},
    )
    assert not create_result.isError
    motif_id = json.loads(create_result.content[0].text)["id"]

    result = await _call_tool(test_db_path, "delete_motif", {"motif_id": motif_id})
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["deleted"] is True
    assert data["id"] == motif_id


@pytest.mark.anyio
async def test_delete_motif_not_found(test_db_path):
    """delete_motif returns NotFoundResponse for a non-existent motif id."""
    result = await _call_tool(test_db_path, "delete_motif", {"motif_id": 99999})
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "not_found_message" in data


@pytest.mark.anyio
async def test_delete_motif_gate_violation(uncertified_db_path):
    """delete_motif returns GateViolation on uncertified gate."""
    result = await _call_tool(uncertified_db_path, "delete_motif", {"motif_id": 1})
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "requires_action" in data


# ---------------------------------------------------------------------------
# Tests: upsert_prophecy (Task 1)
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_upsert_prophecy_create(test_db_path):
    """upsert_prophecy creates a new prophecy when prophecy_id is None.

    Uses required fields: name, text. Verifies returned object has an id
    and matches the provided name.
    """
    result = await _call_tool(
        test_db_path,
        "upsert_prophecy",
        {
            "name": "The Fallen Star",
            "text": "When the last star falls, darkness shall reign for an age",
        },
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "id" in data
    assert data["id"] is not None
    assert data["name"] == "The Fallen Star"


@pytest.mark.anyio
async def test_upsert_prophecy_update(test_db_path):
    """upsert_prophecy updates an existing prophecy when prophecy_id is provided.

    First creates a prophecy, then updates its status to 'fulfilled'.
    Verifies the same id is returned with the updated status.
    """
    create_result = await _call_tool(
        test_db_path,
        "upsert_prophecy",
        {"name": "The Turning Tide", "text": "The tide will turn at the new moon"},
    )
    assert not create_result.isError
    create_data = json.loads(create_result.content[0].text)
    prophecy_id = create_data["id"]

    result = await _call_tool(
        test_db_path,
        "upsert_prophecy",
        {
            "prophecy_id": prophecy_id,
            "name": "The Turning Tide",
            "text": "The tide will turn at the new moon",
            "status": "fulfilled",
        },
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["id"] == prophecy_id
    assert data["status"] == "fulfilled"


@pytest.mark.anyio
async def test_upsert_prophecy_gate_violation(uncertified_db_path):
    """upsert_prophecy returns GateViolation on uncertified gate."""
    result = await _call_tool(
        uncertified_db_path,
        "upsert_prophecy",
        {"name": "Test prophecy", "text": "test text"},
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "requires_action" in data


# ---------------------------------------------------------------------------
# Tests: delete_prophecy (Task 1)
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_delete_prophecy_success(test_db_path):
    """delete_prophecy deletes an existing prophecy by id.

    Creates a new prophecy, then deletes it. Verifies {"deleted": True, "id": N}.
    """
    create_result = await _call_tool(
        test_db_path,
        "upsert_prophecy",
        {"name": "To Be Deleted Prophecy", "text": "This will be deleted"},
    )
    assert not create_result.isError
    prophecy_id = json.loads(create_result.content[0].text)["id"]

    result = await _call_tool(
        test_db_path, "delete_prophecy", {"prophecy_id": prophecy_id}
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["deleted"] is True
    assert data["id"] == prophecy_id


@pytest.mark.anyio
async def test_delete_prophecy_not_found(test_db_path):
    """delete_prophecy returns NotFoundResponse for a non-existent prophecy id."""
    result = await _call_tool(
        test_db_path, "delete_prophecy", {"prophecy_id": 99999}
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "not_found_message" in data


@pytest.mark.anyio
async def test_delete_prophecy_gate_violation(uncertified_db_path):
    """delete_prophecy returns GateViolation on uncertified gate."""
    result = await _call_tool(
        uncertified_db_path, "delete_prophecy", {"prophecy_id": 1}
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "requires_action" in data


# ---------------------------------------------------------------------------
# Tests: upsert_thematic_mirror (Task 2)
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_upsert_thematic_mirror_create(test_db_path):
    """upsert_thematic_mirror creates a new mirror when mirror_id is None.

    Uses required fields: name, element_a_id, element_b_id. Verifies returned
    object has an id and matches the provided name.
    """
    result = await _call_tool(
        test_db_path,
        "upsert_thematic_mirror",
        {
            "name": "Hero-Shadow Mirror",
            "element_a_id": 1,
            "element_b_id": 2,
            "mirror_type": "character",
        },
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "id" in data
    assert data["id"] is not None
    assert data["name"] == "Hero-Shadow Mirror"


@pytest.mark.anyio
async def test_upsert_thematic_mirror_update(test_db_path):
    """upsert_thematic_mirror updates an existing mirror when mirror_id is provided."""
    create_result = await _call_tool(
        test_db_path,
        "upsert_thematic_mirror",
        {"name": "Original Mirror Name", "element_a_id": 1, "element_b_id": 2},
    )
    assert not create_result.isError
    mirror_id = json.loads(create_result.content[0].text)["id"]

    result = await _call_tool(
        test_db_path,
        "upsert_thematic_mirror",
        {
            "mirror_id": mirror_id,
            "name": "Updated Mirror Name",
            "element_a_id": 1,
            "element_b_id": 2,
            "mirror_description": "Deeper analysis of contrast",
        },
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["id"] == mirror_id
    assert data["name"] == "Updated Mirror Name"


@pytest.mark.anyio
async def test_upsert_thematic_mirror_gate_violation(uncertified_db_path):
    """upsert_thematic_mirror returns GateViolation on uncertified gate."""
    result = await _call_tool(
        uncertified_db_path,
        "upsert_thematic_mirror",
        {"name": "Test Mirror", "element_a_id": 1, "element_b_id": 2},
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "requires_action" in data


# ---------------------------------------------------------------------------
# Tests: delete_thematic_mirror (Task 2)
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_delete_thematic_mirror_success(test_db_path):
    """delete_thematic_mirror deletes an existing mirror by id."""
    create_result = await _call_tool(
        test_db_path,
        "upsert_thematic_mirror",
        {"name": "Mirror To Delete", "element_a_id": 1, "element_b_id": 2},
    )
    assert not create_result.isError
    mirror_id = json.loads(create_result.content[0].text)["id"]

    result = await _call_tool(
        test_db_path, "delete_thematic_mirror", {"mirror_id": mirror_id}
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["deleted"] is True
    assert data["id"] == mirror_id


@pytest.mark.anyio
async def test_delete_thematic_mirror_not_found(test_db_path):
    """delete_thematic_mirror returns NotFoundResponse for non-existent id."""
    result = await _call_tool(
        test_db_path, "delete_thematic_mirror", {"mirror_id": 99999}
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "not_found_message" in data


@pytest.mark.anyio
async def test_delete_thematic_mirror_gate_violation(uncertified_db_path):
    """delete_thematic_mirror returns GateViolation on uncertified gate."""
    result = await _call_tool(
        uncertified_db_path, "delete_thematic_mirror", {"mirror_id": 1}
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "requires_action" in data


# ---------------------------------------------------------------------------
# Tests: upsert_opposition_pair (Task 2)
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_upsert_opposition_pair_create(test_db_path):
    """upsert_opposition_pair creates a new pair when pair_id is None.

    Uses required fields: name, concept_a, concept_b. Verifies returned object
    has an id and matches the provided name.
    """
    result = await _call_tool(
        test_db_path,
        "upsert_opposition_pair",
        {
            "name": "Order vs Chaos",
            "concept_a": "Order",
            "concept_b": "Chaos",
        },
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "id" in data
    assert data["id"] is not None
    assert data["name"] == "Order vs Chaos"
    assert data["concept_a"] == "Order"


@pytest.mark.anyio
async def test_upsert_opposition_pair_update(test_db_path):
    """upsert_opposition_pair updates an existing pair when pair_id is provided."""
    create_result = await _call_tool(
        test_db_path,
        "upsert_opposition_pair",
        {"name": "Original Pair", "concept_a": "Light", "concept_b": "Dark"},
    )
    assert not create_result.isError
    pair_id = json.loads(create_result.content[0].text)["id"]

    result = await _call_tool(
        test_db_path,
        "upsert_opposition_pair",
        {
            "pair_id": pair_id,
            "name": "Original Pair",
            "concept_a": "Light",
            "concept_b": "Dark",
            "manifested_in": "The duel in chapter 15",
        },
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["id"] == pair_id
    assert data["manifested_in"] == "The duel in chapter 15"


@pytest.mark.anyio
async def test_upsert_opposition_pair_gate_violation(uncertified_db_path):
    """upsert_opposition_pair returns GateViolation on uncertified gate."""
    result = await _call_tool(
        uncertified_db_path,
        "upsert_opposition_pair",
        {"name": "Test Pair", "concept_a": "A", "concept_b": "B"},
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "requires_action" in data


# ---------------------------------------------------------------------------
# Tests: delete_opposition_pair (Task 2)
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_delete_opposition_pair_success(test_db_path):
    """delete_opposition_pair deletes an existing pair by id."""
    create_result = await _call_tool(
        test_db_path,
        "upsert_opposition_pair",
        {"name": "Pair To Delete", "concept_a": "X", "concept_b": "Y"},
    )
    assert not create_result.isError
    pair_id = json.loads(create_result.content[0].text)["id"]

    result = await _call_tool(
        test_db_path, "delete_opposition_pair", {"pair_id": pair_id}
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["deleted"] is True
    assert data["id"] == pair_id


@pytest.mark.anyio
async def test_delete_opposition_pair_not_found(test_db_path):
    """delete_opposition_pair returns NotFoundResponse for non-existent id."""
    result = await _call_tool(
        test_db_path, "delete_opposition_pair", {"pair_id": 99999}
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "not_found_message" in data


@pytest.mark.anyio
async def test_delete_opposition_pair_gate_violation(uncertified_db_path):
    """delete_opposition_pair returns GateViolation on uncertified gate."""
    result = await _call_tool(
        uncertified_db_path, "delete_opposition_pair", {"pair_id": 1}
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "requires_action" in data
