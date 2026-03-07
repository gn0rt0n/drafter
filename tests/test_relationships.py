"""Tests for the relationship domain MCP tools (REL-01 through REL-06, ERRC-01/02/04).

Uses a file-backed SQLite database with migrations applied and minimal seed
data loaded. Tests call tools via FastMCP.call_tool() to verify the MCP
callable interface. Return values are reconstructed from the structured dict
payload that FastMCP yields.

pytest-asyncio mode is set to "auto" in pyproject.toml so @pytest.mark.asyncio
is not required on each test function.
"""

import sqlite3

import aiosqlite
import pytest
from mcp.server.fastmcp import FastMCP

from novel.db.migrations import apply_migrations
from novel.db.seed import load_seed_profile
from novel.models.relationships import (
    CharacterRelationship,
    PerceptionProfile,
    RelationshipChangeEvent,
)
from novel.models.shared import NotFoundResponse, ValidationFailure


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def seeded_db_path(tmp_path_factory) -> str:
    """Create a seeded SQLite DB file and return its path for async tests."""
    db_path = str(tmp_path_factory.mktemp("db_rel") / "test_rel.db")
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys=ON")
    apply_migrations(conn)
    load_seed_profile(conn, "minimal")
    conn.commit()
    conn.close()
    return db_path


@pytest.fixture(scope="module")
def mcp_instance(seeded_db_path, monkeypatch_module_fixture):
    """Return a FastMCP instance with relationship tools registered, pointing to seeded DB."""
    import novel.mcp.db as db_module

    _orig = db_module._get_db_path
    db_module._get_db_path = lambda: seeded_db_path

    mcp = FastMCP("test-novel-mcp-rel")
    from novel.tools.relationships import register
    register(mcp)

    yield mcp

    db_module._get_db_path = _orig


@pytest.fixture(scope="module")
def monkeypatch_module_fixture():
    """Stub fixture — actual patching is done inline in mcp_instance."""
    yield


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


async def call_tool(mcp: FastMCP, tool_name: str, **kwargs):
    """Call an MCP tool and return the structured result.

    FastMCP.call_tool returns (content_blocks, structured_dict).
    structured_dict has the shape {"result": <value>}.
    """
    _, structured = await mcp.call_tool(tool_name, kwargs)
    return structured.get("result")


def try_parse(data, *model_classes):
    """Attempt to parse data as one of the given Pydantic model classes.

    Returns the first successful parse, or raises if none match.
    """
    if data is None:
        return None
    if isinstance(data, dict):
        for cls in model_classes:
            try:
                return cls(**data)
            except Exception:
                pass
    return data


# ---------------------------------------------------------------------------
# Helpers — insert test data via aiosqlite
# ---------------------------------------------------------------------------


async def insert_relationship(db_path: str, a_id: int, b_id: int, rel_type: str = "ally") -> int:
    """Insert or update a character_relationships row (canonical order) and return the row id.

    Uses ON CONFLICT DO UPDATE to avoid UNIQUE conflicts when the seed already
    inserted a row for the same pair without deleting the existing row (which
    would cascade-fail FK children in relationship_change_events).
    """
    ca, cb = min(a_id, b_id), max(a_id, b_id)
    async with aiosqlite.connect(db_path) as conn:
        await conn.execute("PRAGMA foreign_keys=ON")
        cursor = await conn.execute(
            """INSERT INTO character_relationships
               (character_a_id, character_b_id, relationship_type,
                bond_strength, trust_level, current_status, canon_status, updated_at)
               VALUES (?, ?, ?, 50, 50, 'active', 'draft', datetime('now'))
               ON CONFLICT(character_a_id, character_b_id) DO UPDATE SET
                   relationship_type=excluded.relationship_type,
                   updated_at=datetime('now')""",
            (ca, cb, rel_type),
        )
        await conn.commit()
        # Fetch the actual row id since lastrowid is 0 on DO UPDATE
        cur2 = await conn.execute(
            "SELECT id FROM character_relationships WHERE character_a_id = ? AND character_b_id = ?",
            (ca, cb),
        )
        row = await cur2.fetchone()
        return row[0]


# ---------------------------------------------------------------------------
# get_relationship
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_relationship_found_canonical(mcp_instance, seeded_db_path):
    """get_relationship returns CharacterRelationship for an existing pair (a,b order)."""
    await insert_relationship(seeded_db_path, 1, 2, "rival")
    raw = await call_tool(mcp_instance, "get_relationship", character_a_id=1, character_b_id=2)
    result = try_parse(raw, CharacterRelationship, NotFoundResponse)
    assert isinstance(result, CharacterRelationship), (
        f"Expected CharacterRelationship, got {type(result)}: {result}"
    )
    assert result.relationship_type == "rival"


@pytest.mark.asyncio
async def test_get_relationship_found_reversed(mcp_instance, seeded_db_path):
    """get_relationship finds the row when queried with (b,a) reversed order."""
    # The row was inserted in canonical order (1,2) by prior test.
    raw = await call_tool(mcp_instance, "get_relationship", character_a_id=2, character_b_id=1)
    result = try_parse(raw, CharacterRelationship, NotFoundResponse)
    assert isinstance(result, CharacterRelationship), (
        f"Expected CharacterRelationship even when queried reversed, got {type(result)}: {result}"
    )


@pytest.mark.asyncio
async def test_get_relationship_not_found(mcp_instance):
    """get_relationship returns NotFoundResponse when the pair has no row."""
    raw = await call_tool(mcp_instance, "get_relationship", character_a_id=1, character_b_id=9999)
    result = try_parse(raw, CharacterRelationship, NotFoundResponse)
    assert isinstance(result, NotFoundResponse), (
        f"Expected NotFoundResponse, got {type(result)}: {result}"
    )
    assert "9999" in result.not_found_message


# ---------------------------------------------------------------------------
# list_relationships
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_relationships_returns_all_for_character(mcp_instance, seeded_db_path):
    """list_relationships returns all rows where character appears as a_id OR b_id."""
    # Character 3 has no relationships yet — insert two (3,4) and (1,3)
    await insert_relationship(seeded_db_path, 3, 4, "acquaintance")
    await insert_relationship(seeded_db_path, 1, 3, "mentor")

    raw = await call_tool(mcp_instance, "list_relationships", character_id=3)
    assert isinstance(raw, list), f"Expected list, got {type(raw)}"
    # Character 3 should appear in both (3,4) and (1,3) rows
    parsed = [try_parse(r, CharacterRelationship) for r in raw]
    assert len(parsed) >= 2, f"Expected >= 2 relationships for character 3, got {len(parsed)}"
    assert all(isinstance(r, CharacterRelationship) for r in parsed)


@pytest.mark.asyncio
async def test_list_relationships_empty_for_isolated_character(mcp_instance):
    """list_relationships returns empty list when character has no relationships."""
    raw = await call_tool(mcp_instance, "list_relationships", character_id=9999)
    assert isinstance(raw, list), f"Expected list, got {type(raw)}"
    assert raw == [], f"Expected empty list for character with no relationships, got {raw}"


# ---------------------------------------------------------------------------
# upsert_relationship
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_upsert_relationship_create(mcp_instance):
    """upsert_relationship creates a new row and returns CharacterRelationship."""
    raw = await call_tool(
        mcp_instance,
        "upsert_relationship",
        character_a_id=4,
        character_b_id=5,
        relationship_type="enemy",
        bond_strength=-30,
        trust_level=-20,
        current_status="hostile",
    )
    result = try_parse(raw, CharacterRelationship, ValidationFailure)
    assert isinstance(result, CharacterRelationship), (
        f"Expected CharacterRelationship, got {type(result)}: {result}"
    )
    assert result.relationship_type == "enemy"
    assert result.current_status == "hostile"


@pytest.mark.asyncio
async def test_upsert_relationship_canonical_ordering(mcp_instance, seeded_db_path):
    """upsert_relationship with (b,a) arguments still stores as (min,max) canonical order."""
    # Pass 5 then 4 — reversed. Canonical should be (4,5).
    raw = await call_tool(
        mcp_instance,
        "upsert_relationship",
        character_a_id=5,
        character_b_id=4,
        relationship_type="ally",
        bond_strength=40,
        trust_level=40,
        current_status="warm",
    )
    result = try_parse(raw, CharacterRelationship, ValidationFailure)
    assert isinstance(result, CharacterRelationship), (
        f"Expected CharacterRelationship, got {type(result)}: {result}"
    )
    assert result.character_a_id < result.character_b_id, (
        f"Canonical order violated: a={result.character_a_id}, b={result.character_b_id}"
    )
    assert result.character_a_id == 4
    assert result.character_b_id == 5


@pytest.mark.asyncio
async def test_upsert_relationship_update(mcp_instance):
    """upsert_relationship updates an existing row on conflict."""
    # First upsert to create (2,3) relationship
    await call_tool(
        mcp_instance,
        "upsert_relationship",
        character_a_id=2,
        character_b_id=3,
        relationship_type="neutral",
        bond_strength=0,
        trust_level=0,
        current_status="neutral",
    )
    # Now update it
    raw = await call_tool(
        mcp_instance,
        "upsert_relationship",
        character_a_id=2,
        character_b_id=3,
        relationship_type="friend",
        bond_strength=60,
        trust_level=70,
        current_status="warm",
    )
    result = try_parse(raw, CharacterRelationship, ValidationFailure)
    assert isinstance(result, CharacterRelationship), (
        f"Expected CharacterRelationship, got {type(result)}: {result}"
    )
    assert result.relationship_type == "friend"
    assert result.bond_strength == 60


# ---------------------------------------------------------------------------
# get_perception_profile
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def seeded_perception_db_path(tmp_path_factory) -> str:
    """Separate DB for perception tests to avoid fixture-order coupling."""
    db_path = str(tmp_path_factory.mktemp("db_perc") / "test_perc.db")
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys=ON")
    apply_migrations(conn)
    load_seed_profile(conn, "minimal")
    conn.commit()
    conn.close()
    return db_path


@pytest.fixture(scope="module")
def perc_mcp(seeded_perception_db_path, monkeypatch_module_fixture):
    """FastMCP pointing at the perception test DB."""
    import novel.mcp.db as db_module

    _orig = db_module._get_db_path
    db_module._get_db_path = lambda: seeded_perception_db_path

    mcp = FastMCP("test-novel-perc")
    from novel.tools.relationships import register
    register(mcp)

    yield mcp

    db_module._get_db_path = _orig


@pytest.mark.asyncio
async def test_get_perception_profile_not_found(perc_mcp):
    """get_perception_profile returns NotFoundResponse when no profile exists."""
    raw = await call_tool(perc_mcp, "get_perception_profile", observer_id=9999, subject_id=1)
    result = try_parse(raw, PerceptionProfile, NotFoundResponse)
    assert isinstance(result, NotFoundResponse), (
        f"Expected NotFoundResponse, got {type(result)}: {result}"
    )
    assert "9999" in result.not_found_message


@pytest.mark.asyncio
async def test_get_perception_profile_found(perc_mcp, seeded_perception_db_path):
    """get_perception_profile returns PerceptionProfile for an existing (observer, subject) pair."""
    async with aiosqlite.connect(seeded_perception_db_path) as conn:
        await conn.execute("PRAGMA foreign_keys=ON")
        # Use OR REPLACE to handle the case where seed already inserted (1,2).
        await conn.execute(
            """INSERT OR REPLACE INTO perception_profiles
               (observer_id, subject_id, trust_level, emotional_valence, updated_at)
               VALUES (1, 2, 30, 'suspicious', datetime('now'))"""
        )
        await conn.commit()

    raw = await call_tool(perc_mcp, "get_perception_profile", observer_id=1, subject_id=2)
    result = try_parse(raw, PerceptionProfile, NotFoundResponse)
    assert isinstance(result, PerceptionProfile), (
        f"Expected PerceptionProfile, got {type(result)}: {result}"
    )
    assert result.observer_id == 1
    assert result.subject_id == 2
    assert result.emotional_valence == "suspicious"


# ---------------------------------------------------------------------------
# upsert_perception_profile
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_upsert_perception_profile_create(perc_mcp):
    """upsert_perception_profile creates a new profile and returns PerceptionProfile."""
    raw = await call_tool(
        perc_mcp,
        "upsert_perception_profile",
        observer_id=2,
        subject_id=3,
        trust_level=40,
        emotional_valence="neutral",
        perceived_traits="Brave, reckless",
    )
    result = try_parse(raw, PerceptionProfile, ValidationFailure)
    assert isinstance(result, PerceptionProfile), (
        f"Expected PerceptionProfile, got {type(result)}: {result}"
    )
    assert result.observer_id == 2
    assert result.subject_id == 3
    assert result.trust_level == 40
    assert result.perceived_traits == "Brave, reckless"


@pytest.mark.asyncio
async def test_upsert_perception_profile_update(perc_mcp):
    """upsert_perception_profile updates existing profile on conflict."""
    # Create (3,4) first
    await call_tool(
        perc_mcp,
        "upsert_perception_profile",
        observer_id=3,
        subject_id=4,
        trust_level=10,
        emotional_valence="wary",
    )
    # Update
    raw = await call_tool(
        perc_mcp,
        "upsert_perception_profile",
        observer_id=3,
        subject_id=4,
        trust_level=80,
        emotional_valence="trusting",
        perceived_traits="Loyal, dependable",
    )
    result = try_parse(raw, PerceptionProfile, ValidationFailure)
    assert isinstance(result, PerceptionProfile), (
        f"Expected PerceptionProfile, got {type(result)}: {result}"
    )
    assert result.trust_level == 80
    assert result.emotional_valence == "trusting"
    assert result.perceived_traits == "Loyal, dependable"


# ---------------------------------------------------------------------------
# log_relationship_change
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def seeded_log_db_path(tmp_path_factory) -> str:
    """Separate DB for log_relationship_change tests."""
    db_path = str(tmp_path_factory.mktemp("db_log") / "test_log.db")
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys=ON")
    apply_migrations(conn)
    load_seed_profile(conn, "minimal")
    conn.commit()
    conn.close()
    return db_path


@pytest.fixture(scope="module")
def log_mcp(seeded_log_db_path, monkeypatch_module_fixture):
    """FastMCP pointing at the log test DB."""
    import novel.mcp.db as db_module

    _orig = db_module._get_db_path
    db_module._get_db_path = lambda: seeded_log_db_path

    mcp = FastMCP("test-novel-log")
    from novel.tools.relationships import register
    register(mcp)

    yield mcp

    db_module._get_db_path = _orig


@pytest.mark.asyncio
async def test_log_relationship_change_not_found(log_mcp):
    """log_relationship_change returns NotFoundResponse when relationship_id doesn't exist."""
    raw = await call_tool(
        log_mcp,
        "log_relationship_change",
        relationship_id=9999,
        change_type="shift",
        description="Non-existent relationship change",
        bond_delta=5,
        trust_delta=5,
    )
    result = try_parse(raw, RelationshipChangeEvent, NotFoundResponse, ValidationFailure)
    assert isinstance(result, NotFoundResponse), (
        f"Expected NotFoundResponse, got {type(result)}: {result}"
    )
    assert "9999" in result.not_found_message


@pytest.mark.asyncio
async def test_log_relationship_change_inserts_and_returns(log_mcp, seeded_log_db_path):
    """log_relationship_change inserts a row and returns RelationshipChangeEvent with new id."""
    # Insert a relationship to log against
    async with aiosqlite.connect(seeded_log_db_path) as conn:
        await conn.execute("PRAGMA foreign_keys=ON")
        cursor = await conn.execute(
            """INSERT INTO character_relationships
               (character_a_id, character_b_id, relationship_type,
                bond_strength, trust_level, current_status, canon_status, updated_at)
               VALUES (1, 2, 'ally', 50, 50, 'active', 'draft', datetime('now'))"""
        )
        await conn.commit()
        rel_id = cursor.lastrowid

    raw = await call_tool(
        log_mcp,
        "log_relationship_change",
        relationship_id=rel_id,
        change_type="breakthrough",
        description="Characters forged a blood oath",
        bond_delta=20,
        trust_delta=15,
    )
    result = try_parse(raw, RelationshipChangeEvent, NotFoundResponse, ValidationFailure)
    assert isinstance(result, RelationshipChangeEvent), (
        f"Expected RelationshipChangeEvent, got {type(result)}: {result}"
    )
    assert result.id is not None
    assert result.relationship_id == rel_id
    assert result.description == "Characters forged a blood oath"
    assert result.bond_delta == 20
    assert result.trust_delta == 15
    assert result.change_type == "breakthrough"


# ---------------------------------------------------------------------------
# Error contract — no print() in implementation
# ---------------------------------------------------------------------------


def test_no_print_statements():
    """Confirm zero print() calls in tools/relationships.py."""
    import inspect
    import novel.tools.relationships as mod
    source = inspect.getsource(mod)
    assert "print(" not in source, "Found print() call in tools/relationships.py — use logger instead"
