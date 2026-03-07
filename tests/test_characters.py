"""Tests for the character domain MCP tools (CHAR-01 through CHAR-07, ERRC-01/02/04).

Uses a file-backed SQLite database with migrations applied and minimal seed
data loaded. Tests call tools via FastMCP.call_tool() to verify the MCP
callable interface. Return values are reconstructed from the structured dict
payload that FastMCP yields.

pytest-asyncio mode is set to "auto" in pyproject.toml so @pytest.mark.asyncio
is not required on each test function.
"""

import asyncio
import sqlite3

import aiosqlite
import pytest
from mcp.server.fastmcp import FastMCP

from novel.db.migrations import apply_migrations
from novel.db.seed import load_seed_profile
from novel.models.characters import (
    Character,
    CharacterBelief,
    CharacterKnowledge,
    CharacterLocation,
    InjuryState,
)
from novel.models.shared import NotFoundResponse, ValidationFailure


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def seeded_db_path(tmp_path_factory) -> str:
    """Create a seeded SQLite DB file and return its path for async tests."""
    db_path = str(tmp_path_factory.mktemp("db") / "test.db")
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys=ON")
    apply_migrations(conn)
    load_seed_profile(conn, "minimal")
    conn.commit()
    conn.close()
    return db_path


@pytest.fixture(scope="module")
def mcp_instance(seeded_db_path, monkeypatch_module_fixture):
    """Return a FastMCP instance with character tools registered, pointing to seeded DB."""
    import novel.mcp.db as db_module

    _orig = db_module._get_db_path
    db_module._get_db_path = lambda: seeded_db_path

    mcp = FastMCP("test-novel-mcp")
    from novel.tools.characters import register
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
    """Call an MCP tool and return the structured result (second element of tuple).

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
# get_character
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_character_valid(mcp_instance):
    """get_character returns a Character for a valid ID (id=1 from minimal seed)."""
    raw = await call_tool(mcp_instance, "get_character", character_id=1)
    result = try_parse(raw, Character, NotFoundResponse)
    assert isinstance(result, Character), f"Expected Character, got {type(result)}: {result}"
    assert result.id == 1
    assert result.name  # not empty


@pytest.mark.asyncio
async def test_get_character_not_found(mcp_instance):
    """get_character returns NotFoundResponse for id=9999."""
    raw = await call_tool(mcp_instance, "get_character", character_id=9999)
    result = try_parse(raw, Character, NotFoundResponse)
    assert isinstance(result, NotFoundResponse), f"Expected NotFoundResponse, got {type(result)}: {result}"
    assert "9999" in result.not_found_message


# ---------------------------------------------------------------------------
# list_characters
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_characters_returns_seeded(mcp_instance):
    """list_characters returns at least 5 entries (minimal seed has 5 characters)."""
    raw = await call_tool(mcp_instance, "list_characters")
    assert isinstance(raw, list), f"Expected list, got {type(raw)}"
    assert len(raw) >= 5, f"Expected >= 5 characters, got {len(raw)}"
    parsed = [try_parse(c, Character) for c in raw]
    assert all(isinstance(c, Character) for c in parsed), "Not all items are Character instances"


# ---------------------------------------------------------------------------
# upsert_character
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_upsert_character_create(mcp_instance):
    """upsert_character with character_id=None creates a new row."""
    raw = await call_tool(
        mcp_instance,
        "upsert_character",
        character_id=None,
        name="Test Hero",
        role="supporting",
    )
    result = try_parse(raw, Character, ValidationFailure)
    assert isinstance(result, Character), f"Expected Character, got {type(result)}: {result}"
    assert result.id is not None
    assert result.name == "Test Hero"


@pytest.mark.asyncio
async def test_upsert_character_update(mcp_instance):
    """upsert_character with an existing character_id updates the row."""
    # Create first
    raw_created = await call_tool(
        mcp_instance,
        "upsert_character",
        character_id=None,
        name="Updateable Character",
        role="supporting",
    )
    created = try_parse(raw_created, Character, ValidationFailure)
    assert isinstance(created, Character)
    char_id = created.id

    # Update
    raw_updated = await call_tool(
        mcp_instance,
        "upsert_character",
        character_id=char_id,
        name="Updateable Character (Updated)",
        role="protagonist",
    )
    updated = try_parse(raw_updated, Character, ValidationFailure)
    assert isinstance(updated, Character), f"Expected Character, got {type(updated)}: {updated}"
    assert updated.id == char_id
    assert updated.name == "Updateable Character (Updated)"
    assert updated.role == "protagonist"


# ---------------------------------------------------------------------------
# get_character_injuries
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_character_injuries_not_found(mcp_instance):
    """get_character_injuries returns NotFoundResponse for missing character."""
    raw = await call_tool(mcp_instance, "get_character_injuries", character_id=9999)
    result = try_parse(raw, NotFoundResponse)
    assert isinstance(result, NotFoundResponse), f"Expected NotFoundResponse, got {type(result)}: {result}"


@pytest.mark.asyncio
async def test_get_character_injuries_returns_list(mcp_instance):
    """get_character_injuries returns a list for a valid character (may be empty)."""
    raw = await call_tool(mcp_instance, "get_character_injuries", character_id=1)
    assert isinstance(raw, list), f"Expected list, got {type(raw)}"


@pytest.mark.asyncio
async def test_get_character_injuries_chapter_scoping(mcp_instance, seeded_db_path):
    """get_character_injuries with chapter_id filters to chapter_id <= N."""
    # Insert test fixtures
    async with aiosqlite.connect(seeded_db_path) as conn:
        await conn.execute("PRAGMA foreign_keys=ON")
        await conn.execute(
            "INSERT INTO injury_states (character_id, chapter_id, injury_type, description, severity) "
            "VALUES (1, 1, 'wound', 'Arrow wound ch1', 'minor')"
        )
        await conn.execute(
            "INSERT INTO injury_states (character_id, chapter_id, injury_type, description, severity) "
            "VALUES (1, 3, 'wound', 'Sword wound ch3', 'serious')"
        )
        await conn.commit()

    raw = await call_tool(mcp_instance, "get_character_injuries", character_id=1, chapter_id=2)
    assert isinstance(raw, list)
    injuries = [try_parse(i, InjuryState) for i in raw]
    descriptions = [i.description for i in injuries if isinstance(i, InjuryState)]
    assert "Arrow wound ch1" in descriptions, f"Expected arrow wound in {descriptions}"
    assert "Sword wound ch3" not in descriptions, f"Chapter 3 wound should not appear: {descriptions}"


# ---------------------------------------------------------------------------
# get_character_beliefs
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_character_beliefs_not_found(mcp_instance):
    """get_character_beliefs returns NotFoundResponse for missing character."""
    raw = await call_tool(mcp_instance, "get_character_beliefs", character_id=9999)
    result = try_parse(raw, NotFoundResponse)
    assert isinstance(result, NotFoundResponse), f"Expected NotFoundResponse, got {type(result)}: {result}"


@pytest.mark.asyncio
async def test_get_character_beliefs_returns_list(mcp_instance, seeded_db_path):
    """get_character_beliefs returns a list of CharacterBelief records."""
    # Insert a belief record
    async with aiosqlite.connect(seeded_db_path) as conn:
        await conn.execute("PRAGMA foreign_keys=ON")
        await conn.execute(
            "INSERT INTO character_beliefs (character_id, belief_type, content, strength) "
            "VALUES (1, 'worldview', 'The ember that outlasts the blaze is worthy', 8)"
        )
        await conn.commit()

    raw = await call_tool(mcp_instance, "get_character_beliefs", character_id=1)
    assert isinstance(raw, list)
    beliefs = [try_parse(b, CharacterBelief) for b in raw]
    assert len(beliefs) >= 1
    assert all(isinstance(b, CharacterBelief) for b in beliefs)


# ---------------------------------------------------------------------------
# get_character_knowledge
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_character_knowledge_not_found(mcp_instance):
    """get_character_knowledge returns NotFoundResponse for missing character."""
    raw = await call_tool(mcp_instance, "get_character_knowledge", character_id=9999)
    result = try_parse(raw, NotFoundResponse)
    assert isinstance(result, NotFoundResponse), f"Expected NotFoundResponse, got {type(result)}: {result}"


@pytest.mark.asyncio
async def test_get_character_knowledge_chapter_scoping(mcp_instance, seeded_db_path):
    """get_character_knowledge with chapter_id filters to chapter_id <= N.

    Uses chapters 1 and 3 (both exist in minimal seed). Queries with chapter_id=2
    so chapter 3 is excluded.
    """
    async with aiosqlite.connect(seeded_db_path) as conn:
        await conn.execute("PRAGMA foreign_keys=ON")
        await conn.execute(
            "INSERT INTO character_knowledge (character_id, chapter_id, knowledge_type, content) "
            "VALUES (1, 1, 'fact', 'Knowledge at chapter 1')"
        )
        await conn.execute(
            "INSERT INTO character_knowledge (character_id, chapter_id, knowledge_type, content) "
            "VALUES (1, 3, 'fact', 'Knowledge at chapter 3')"
        )
        await conn.commit()

    raw = await call_tool(mcp_instance, "get_character_knowledge", character_id=1, chapter_id=2)
    assert isinstance(raw, list)
    knowledge_items = [try_parse(k, CharacterKnowledge) for k in raw]
    contents = [k.content for k in knowledge_items if isinstance(k, CharacterKnowledge)]
    assert "Knowledge at chapter 1" in contents, f"Expected ch1 knowledge in {contents}"
    assert "Knowledge at chapter 3" not in contents, f"Ch3 knowledge should not appear at chapter_id=2: {contents}"


# ---------------------------------------------------------------------------
# log_character_knowledge
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_log_character_knowledge_inserts_and_returns(mcp_instance):
    """log_character_knowledge inserts a record and returns CharacterKnowledge with new id."""
    raw = await call_tool(
        mcp_instance,
        "log_character_knowledge",
        character_id=1,
        chapter_id=2,
        knowledge_type="rumor",
        content="The old forge still burns beneath the citadel.",
        source="tavern gossip",
        is_secret=True,
        notes=None,
    )
    result = try_parse(raw, CharacterKnowledge, NotFoundResponse, ValidationFailure)
    assert isinstance(result, CharacterKnowledge), f"Expected CharacterKnowledge, got {type(result)}: {result}"
    assert result.id is not None
    assert result.character_id == 1
    assert result.content == "The old forge still burns beneath the citadel."
    assert result.is_secret is True


@pytest.mark.asyncio
async def test_log_character_knowledge_not_found(mcp_instance):
    """log_character_knowledge returns NotFoundResponse for missing character."""
    raw = await call_tool(
        mcp_instance,
        "log_character_knowledge",
        character_id=9999,
        chapter_id=1,
        knowledge_type="fact",
        content="irrelevant content",
        source=None,
        is_secret=False,
        notes=None,
    )
    result = try_parse(raw, CharacterKnowledge, NotFoundResponse, ValidationFailure)
    assert isinstance(result, NotFoundResponse), f"Expected NotFoundResponse, got {type(result)}: {result}"


# ---------------------------------------------------------------------------
# get_character_location
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_character_location_not_found(mcp_instance):
    """get_character_location returns NotFoundResponse for missing character."""
    raw = await call_tool(mcp_instance, "get_character_location", character_id=9999)
    result = try_parse(raw, NotFoundResponse)
    assert isinstance(result, NotFoundResponse), f"Expected NotFoundResponse, got {type(result)}: {result}"


@pytest.mark.asyncio
async def test_get_character_location_chapter_scoping(mcp_instance, seeded_db_path):
    """get_character_location with chapter_id filters to chapter_id <= N.

    Uses chapters 1 and 3 (both exist in minimal seed). Queries with chapter_id=2
    so chapter 3 is excluded.
    """
    async with aiosqlite.connect(seeded_db_path) as conn:
        await conn.execute("PRAGMA foreign_keys=ON")
        await conn.execute(
            "INSERT INTO character_locations (character_id, chapter_id, location_note) "
            "VALUES (1, 1, 'Location at chapter 1')"
        )
        await conn.execute(
            "INSERT INTO character_locations (character_id, chapter_id, location_note) "
            "VALUES (1, 3, 'Location at chapter 3')"
        )
        await conn.commit()

    raw = await call_tool(mcp_instance, "get_character_location", character_id=1, chapter_id=2)
    assert isinstance(raw, list)
    locations = [try_parse(loc, CharacterLocation) for loc in raw]
    notes = [loc.location_note for loc in locations if isinstance(loc, CharacterLocation)]
    assert "Location at chapter 1" in notes, f"Expected ch1 location in {notes}"
    assert "Location at chapter 3" not in notes, f"Ch3 location should not appear at chapter_id=2: {notes}"


# ---------------------------------------------------------------------------
# Error contract — no print() in implementation
# ---------------------------------------------------------------------------


def test_no_print_statements():
    """Confirm zero print() calls in tools/characters.py."""
    import inspect
    import novel.tools.characters as mod
    source = inspect.getsource(mod)
    assert "print(" not in source, "Found print() call in tools/characters.py — use logger instead"
