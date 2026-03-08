"""In-memory MCP client tests for names domain tools.

These tools are gate-free — they work before gate certification (pre-prose worldbuilding).
Uses 'minimal' seed profile. Name-specific test data is inserted inline per test as needed.

Total name tools: 4
  check_name, register_name, get_name_registry, generate_name_suggestions

Tests verify the full MCP protocol path: call_tool -> FastMCP -> tool handler -> SQLite -> response.
MCP session is entered PER-TEST inside _call_tool — anyio cancel scope incompatible with fixtures.

FastMCP serialization rules:
  - Single object: json.loads(result.content[0].text)
  - list[T]: [json.loads(c.text) for c in result.content]
  - Empty list: result.content is empty (no TextContent blocks)

Single-object tools: check_name (when found), register_name
List tools: get_name_registry, generate_name_suggestions (existing_names part)
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
# Session-scoped DB fixture — minimal seed
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def test_db_path(tmp_path_factory):
    """Create a temp SQLite file with all migrations + minimal seed.

    Session-scoped: created once for all tests in this file.
    Uses "names_db" dir to isolate from other test files.

    Name tools are gate-free so minimal seed (no gate certification) is fine.
    """
    db_file = tmp_path_factory.mktemp("names_db") / "test_names.db"
    conn = sqlite3.connect(str(db_file))
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA journal_mode=WAL")
    apply_migrations(conn)
    load_seed_profile(conn, "minimal")
    conn.commit()
    conn.close()
    return str(db_file)


# ---------------------------------------------------------------------------
# Helper: open/close MCP session inside each test coroutine
# ---------------------------------------------------------------------------


async def _call_tool(db_path: str, tool_name: str, args: dict):
    """Call a name tool via MCP in-memory protocol.

    Opens and closes session inside this coroutine so anyio cancel scopes
    are entered and exited in the same task context.
    """
    os.environ["NOVEL_DB_PATH"] = db_path
    async with create_connected_server_and_client_session(mcp) as session:
        return await session.call_tool(tool_name, args)


# ---------------------------------------------------------------------------
# Tests: check_name
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_check_name_found(test_db_path):
    """check_name returns NameRegistryEntry when name exists (exact, case-insensitive).

    Seed (minimal) has 'Aeryn Vael' in name_registry. Query with 'Aeryn Vael'.
    Expect: returned object has name='Aeryn Vael'.
    """
    result = await _call_tool(test_db_path, "check_name", {"name": "Aeryn Vael"})
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["name"] == "Aeryn Vael"
    assert "id" in data


@pytest.mark.anyio
async def test_check_name_case_insensitive(test_db_path):
    """check_name is case-insensitive — 'AERYN VAEL' matches 'Aeryn Vael'.

    Seed (minimal) has 'Aeryn Vael'. Query with uppercase 'AERYN VAEL'.
    Expect: returned object has name='Aeryn Vael' (stored form).
    """
    result = await _call_tool(test_db_path, "check_name", {"name": "AERYN VAEL"})
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["name"] == "Aeryn Vael"


@pytest.mark.anyio
async def test_check_name_not_found(test_db_path):
    """check_name returns NotFoundResponse with 'safe to use' when name absent.

    ZZZunknown is not in the minimal seed name_registry.
    Expect: not_found_message containing 'safe to use'.
    """
    result = await _call_tool(test_db_path, "check_name", {"name": "ZZZunknown"})
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "not_found_message" in data
    assert "safe to use" in data["not_found_message"]


# ---------------------------------------------------------------------------
# Tests: register_name
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_register_name_success(test_db_path):
    """register_name inserts a new name and returns NameRegistryEntry with id set.

    Uses a unique name (with timestamp-like uniquifier) to avoid cross-test collision.
    Expect: returned object has id (not None) and name as given.
    """
    result = await _call_tool(
        test_db_path,
        "register_name",
        {"name": "Zyndra Osk", "entity_type": "character"},
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["id"] is not None
    assert data["name"] == "Zyndra Osk"
    assert data["entity_type"] == "character"


@pytest.mark.anyio
async def test_register_name_duplicate_returns_validation_failure(test_db_path):
    """register_name returns ValidationFailure when name already exists.

    First registers 'Dupl Cass', then tries again. Second call must return
    ValidationFailure with is_valid=False.
    """
    # Insert first time — should succeed
    first = await _call_tool(
        test_db_path,
        "register_name",
        {"name": "Dupl Cass", "entity_type": "character"},
    )
    assert not first.isError
    first_data = json.loads(first.content[0].text)
    assert first_data.get("id") is not None  # success

    # Insert second time — should return ValidationFailure
    result = await _call_tool(
        test_db_path,
        "register_name",
        {"name": "Dupl Cass", "entity_type": "character"},
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["is_valid"] is False
    assert len(data["errors"]) > 0


# ---------------------------------------------------------------------------
# Tests: get_name_registry
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_get_name_registry_returns_all(test_db_path):
    """get_name_registry returns all NameRegistryEntry records ordered by name ASC.

    Minimal seed has at least 'Aeryn Vael'. Verify list is non-empty and ordered.
    """
    result = await _call_tool(test_db_path, "get_name_registry", {})
    assert not result.isError
    items = [json.loads(c.text) for c in result.content]
    assert isinstance(items, list)
    assert len(items) >= 1
    # Verify ascending name order
    names = [item["name"] for item in items]
    assert names == sorted(names)


@pytest.mark.anyio
async def test_get_name_registry_filter_entity_type(test_db_path):
    """get_name_registry(entity_type='character') returns only character entries.

    All seed entries are type 'character'. Filter by 'character', then by 'nonexistent_type'.
    """
    result = await _call_tool(
        test_db_path, "get_name_registry", {"entity_type": "character"}
    )
    assert not result.isError
    items = [json.loads(c.text) for c in result.content]
    assert len(items) >= 1
    for item in items:
        assert item["entity_type"] == "character"

    # No entries with a nonsense entity_type
    result2 = await _call_tool(
        test_db_path, "get_name_registry", {"entity_type": "zzz_nonexistent"}
    )
    assert not result2.isError
    empty = [json.loads(c.text) for c in result2.content]
    assert empty == []


@pytest.mark.anyio
async def test_get_name_registry_filter_culture_id(test_db_path):
    """get_name_registry(culture_id=1) returns only entries for that culture.

    Minimal seed has 'Aeryn Vael' with culture_id set (Kaelthari culture, id=1).
    Verify at least one result. Filter by culture_id=999 returns empty list.
    """
    result = await _call_tool(
        test_db_path, "get_name_registry", {"culture_id": 1}
    )
    assert not result.isError
    items = [json.loads(c.text) for c in result.content]
    assert len(items) >= 1
    for item in items:
        assert item["culture_id"] == 1

    # No culture with id=999
    result2 = await _call_tool(
        test_db_path, "get_name_registry", {"culture_id": 999}
    )
    assert not result2.isError
    empty = [json.loads(c.text) for c in result2.content]
    assert empty == []


# ---------------------------------------------------------------------------
# Tests: generate_name_suggestions
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_generate_name_suggestions_known_culture(test_db_path):
    """generate_name_suggestions returns existing_names and linguistic_context for culture 1.

    Minimal seed has 'Aeryn Vael' in name_registry with culture_id=1 (Kaelthari).
    Kaelthari culture has naming_conventions populated.
    Expect: existing_names list has at least 1 item; linguistic_context is a string.
    """
    result = await _call_tool(
        test_db_path, "generate_name_suggestions", {"culture_id": 1}
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "existing_names" in data
    assert "linguistic_context" in data
    assert "culture_id" in data
    assert data["culture_id"] == 1
    assert isinstance(data["existing_names"], list)
    assert len(data["existing_names"]) >= 1
    assert data["linguistic_context"] is not None
    assert isinstance(data["linguistic_context"], str)


@pytest.mark.anyio
async def test_generate_name_suggestions_unknown_culture(test_db_path):
    """generate_name_suggestions returns empty names and None context for nonexistent culture.

    Culture id=999 does not exist. No name_registry rows for it either.
    Expect: existing_names=[] and linguistic_context=None (not an error).
    """
    result = await _call_tool(
        test_db_path, "generate_name_suggestions", {"culture_id": 999}
    )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["existing_names"] == []
    assert data["linguistic_context"] is None
    assert data["culture_id"] == 999
