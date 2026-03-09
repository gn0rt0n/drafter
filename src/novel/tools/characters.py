"""Character domain MCP tools.

All 8 character tools are registered via the register(mcp) function pattern.
This module is standalone — it does not modify server.py; wiring happens in
the server module (Plan 03).

IMPORTANT: Never use the print function in this module. All logging goes to
stderr via the logging module — using print corrupts the stdio protocol.
"""

import logging

from mcp.server.fastmcp import FastMCP

from novel.mcp.db import get_connection
from novel.models.characters import (
    Character,
    CharacterBelief,
    CharacterKnowledge,
    CharacterLocation,
    InjuryState,
    TitleState,
)
from novel.models.shared import NotFoundResponse, ValidationFailure

logger = logging.getLogger(__name__)


def register(mcp: FastMCP) -> None:
    """Register all 19 character domain tools with the given FastMCP instance.

    Tools are defined as local async functions and decorated with @mcp.tool().
    The FastMCP instance is always the one passed in — never imported globally.

    Includes 9 new write tools added in Plans 01 and 07:
    delete_character, delete_character_knowledge (Plan 01),
    log_character_belief, delete_character_belief, log_character_location,
    get_current_character_location, delete_character_location,
    log_injury_state, delete_injury_state, log_title_state,
    delete_title_state (Plan 07).

    Args:
        mcp: The FastMCP server instance to register tools against.
    """

    # ------------------------------------------------------------------
    # get_character
    # ------------------------------------------------------------------

    @mcp.tool()
    async def get_character(character_id: int) -> Character | NotFoundResponse:
        """Look up a single character by ID.

        Args:
            character_id: Primary key of the character to retrieve.

        Returns:
            Character with all fields populated, or NotFoundResponse if the
            character does not exist.
        """
        async with get_connection() as conn:
            row = await conn.execute_fetchall(
                "SELECT * FROM characters WHERE id = ?", (character_id,)
            )
            if not row:
                logger.debug("Character %d not found", character_id)
                return NotFoundResponse(not_found_message=f"Character {character_id} not found")
            return Character(**dict(row[0]))

    # ------------------------------------------------------------------
    # list_characters
    # ------------------------------------------------------------------

    @mcp.tool()
    async def list_characters() -> list[Character]:
        """Return all characters ordered alphabetically by name.

        Returns:
            List of Character objects (may be empty if no characters exist).
        """
        async with get_connection() as conn:
            rows = await conn.execute_fetchall(
                "SELECT * FROM characters ORDER BY name"
            )
            return [Character(**dict(row)) for row in rows]

    # ------------------------------------------------------------------
    # upsert_character
    # ------------------------------------------------------------------

    @mcp.tool()
    async def upsert_character(
        character_id: int | None,
        name: str,
        role: str = "supporting",
        faction_id: int | None = None,
        culture_id: int | None = None,
        home_era_id: int | None = None,
        age: int | None = None,
        physical_description: str | None = None,
        personality_core: str | None = None,
        backstory_summary: str | None = None,
        secret: str | None = None,
        motivation: str | None = None,
        fear: str | None = None,
        flaw: str | None = None,
        strength: str | None = None,
        arc_summary: str | None = None,
        voice_signature: str | None = None,
        notes: str | None = None,
        canon_status: str = "draft",
    ) -> Character | ValidationFailure:
        """Create or update a character.

        When character_id is None, a new character is inserted and the
        AUTOINCREMENT primary key is assigned. When character_id is provided,
        the existing row is updated via ON CONFLICT(id) DO UPDATE.

        Args:
            character_id: Existing character ID to update, or None to create.
            name: Character's full name (required).
            role: Narrative role — e.g. "protagonist", "antagonist", "supporting".
            faction_id: FK to factions table (optional).
            culture_id: FK to cultures table (optional).
            home_era_id: FK to eras table (optional).
            age: Character age in story-time (optional).
            physical_description: Appearance notes (optional).
            personality_core: Core personality summary (optional).
            backstory_summary: Brief backstory (optional).
            secret: Hidden information about the character (optional).
            motivation: What drives the character (optional).
            fear: What the character fears most (optional).
            flaw: Character's primary flaw (optional).
            strength: Character's primary strength (optional).
            arc_summary: Arc trajectory summary (optional).
            voice_signature: Distinctive speech patterns (optional).
            notes: Free-form notes (optional).
            canon_status: Approval status — "draft" or "approved".

        Returns:
            The created or updated Character, or ValidationFailure on DB error.
        """
        async with get_connection() as conn:
            try:
                if character_id is None:
                    # INSERT without id — let AUTOINCREMENT fire
                    cursor = await conn.execute(
                        """INSERT INTO characters (
                            name, role, faction_id, culture_id, home_era_id,
                            age, physical_description, personality_core,
                            backstory_summary, secret, motivation, fear,
                            flaw, strength, arc_summary, voice_signature,
                            notes, canon_status, updated_at
                        ) VALUES (
                            ?, ?, ?, ?, ?,
                            ?, ?, ?,
                            ?, ?, ?, ?,
                            ?, ?, ?, ?,
                            ?, ?, datetime('now')
                        )""",
                        (
                            name, role, faction_id, culture_id, home_era_id,
                            age, physical_description, personality_core,
                            backstory_summary, secret, motivation, fear,
                            flaw, strength, arc_summary, voice_signature,
                            notes, canon_status,
                        ),
                    )
                    new_id = cursor.lastrowid
                    await conn.commit()
                    row = await conn.execute_fetchall(
                        "SELECT * FROM characters WHERE id = ?", (new_id,)
                    )
                else:
                    # UPSERT — update existing row
                    await conn.execute(
                        """INSERT INTO characters (
                            id, name, role, faction_id, culture_id, home_era_id,
                            age, physical_description, personality_core,
                            backstory_summary, secret, motivation, fear,
                            flaw, strength, arc_summary, voice_signature,
                            notes, canon_status, updated_at
                        ) VALUES (
                            ?, ?, ?, ?, ?, ?,
                            ?, ?, ?,
                            ?, ?, ?, ?,
                            ?, ?, ?, ?,
                            ?, ?, datetime('now')
                        )
                        ON CONFLICT(id) DO UPDATE SET
                            name=excluded.name,
                            role=excluded.role,
                            faction_id=excluded.faction_id,
                            culture_id=excluded.culture_id,
                            home_era_id=excluded.home_era_id,
                            age=excluded.age,
                            physical_description=excluded.physical_description,
                            personality_core=excluded.personality_core,
                            backstory_summary=excluded.backstory_summary,
                            secret=excluded.secret,
                            motivation=excluded.motivation,
                            fear=excluded.fear,
                            flaw=excluded.flaw,
                            strength=excluded.strength,
                            arc_summary=excluded.arc_summary,
                            voice_signature=excluded.voice_signature,
                            notes=excluded.notes,
                            canon_status=excluded.canon_status,
                            updated_at=datetime('now')
                        """,
                        (
                            character_id,
                            name, role, faction_id, culture_id, home_era_id,
                            age, physical_description, personality_core,
                            backstory_summary, secret, motivation, fear,
                            flaw, strength, arc_summary, voice_signature,
                            notes, canon_status,
                        ),
                    )
                    await conn.commit()
                    row = await conn.execute_fetchall(
                        "SELECT * FROM characters WHERE id = ?", (character_id,)
                    )
            except Exception as exc:
                logger.error("upsert_character failed: %s", exc)
                return ValidationFailure(is_valid=False, errors=[str(exc)])

            return Character(**dict(row[0]))

    # ------------------------------------------------------------------
    # get_character_injuries
    # ------------------------------------------------------------------

    @mcp.tool()
    async def get_character_injuries(
        character_id: int,
        chapter_id: int | None = None,
    ) -> list[InjuryState] | NotFoundResponse:
        """Return injury records for a character, optionally scoped by chapter.

        Args:
            character_id: ID of the character whose injuries to retrieve.
            chapter_id: If provided, returns only injuries with chapter_id <= this value.

        Returns:
            List of InjuryState records ordered by chapter_id descending, or
            NotFoundResponse if the character does not exist.
        """
        async with get_connection() as conn:
            exists = await conn.execute_fetchall(
                "SELECT id FROM characters WHERE id = ?", (character_id,)
            )
            if not exists:
                return NotFoundResponse(not_found_message=f"Character {character_id} not found")

            if chapter_id is not None:
                rows = await conn.execute_fetchall(
                    "SELECT * FROM injury_states "
                    "WHERE character_id = ? AND chapter_id <= ? "
                    "ORDER BY chapter_id DESC",
                    (character_id, chapter_id),
                )
            else:
                rows = await conn.execute_fetchall(
                    "SELECT * FROM injury_states "
                    "WHERE character_id = ? "
                    "ORDER BY chapter_id DESC",
                    (character_id,),
                )
            return [InjuryState(**dict(row)) for row in rows]

    # ------------------------------------------------------------------
    # get_character_beliefs
    # ------------------------------------------------------------------

    @mcp.tool()
    async def get_character_beliefs(
        character_id: int,
    ) -> list[CharacterBelief] | NotFoundResponse:
        """Return all belief records for a character.

        Args:
            character_id: ID of the character whose beliefs to retrieve.

        Returns:
            List of CharacterBelief records ordered by created_at descending, or
            NotFoundResponse if the character does not exist.
        """
        async with get_connection() as conn:
            exists = await conn.execute_fetchall(
                "SELECT id FROM characters WHERE id = ?", (character_id,)
            )
            if not exists:
                return NotFoundResponse(not_found_message=f"Character {character_id} not found")

            rows = await conn.execute_fetchall(
                "SELECT * FROM character_beliefs "
                "WHERE character_id = ? "
                "ORDER BY created_at DESC",
                (character_id,),
            )
            return [CharacterBelief(**dict(row)) for row in rows]

    # ------------------------------------------------------------------
    # get_character_knowledge
    # ------------------------------------------------------------------

    @mcp.tool()
    async def get_character_knowledge(
        character_id: int,
        chapter_id: int | None = None,
    ) -> list[CharacterKnowledge] | NotFoundResponse:
        """Return knowledge records for a character, optionally scoped by chapter.

        Args:
            character_id: ID of the character whose knowledge to retrieve.
            chapter_id: If provided, returns only records with chapter_id <= this value.

        Returns:
            List of CharacterKnowledge records ordered by chapter_id descending, or
            NotFoundResponse if the character does not exist.
        """
        async with get_connection() as conn:
            exists = await conn.execute_fetchall(
                "SELECT id FROM characters WHERE id = ?", (character_id,)
            )
            if not exists:
                return NotFoundResponse(not_found_message=f"Character {character_id} not found")

            if chapter_id is not None:
                rows = await conn.execute_fetchall(
                    "SELECT * FROM character_knowledge "
                    "WHERE character_id = ? AND chapter_id <= ? "
                    "ORDER BY chapter_id DESC",
                    (character_id, chapter_id),
                )
            else:
                rows = await conn.execute_fetchall(
                    "SELECT * FROM character_knowledge "
                    "WHERE character_id = ? "
                    "ORDER BY chapter_id DESC",
                    (character_id,),
                )
            return [CharacterKnowledge(**dict(row)) for row in rows]

    # ------------------------------------------------------------------
    # log_character_knowledge
    # ------------------------------------------------------------------

    @mcp.tool()
    async def log_character_knowledge(
        character_id: int,
        chapter_id: int,
        knowledge_type: str = "fact",
        content: str = "",
        source: str | None = None,
        is_secret: bool = False,
        notes: str | None = None,
    ) -> CharacterKnowledge | NotFoundResponse | ValidationFailure:
        """Insert a new knowledge record for a character.

        Args:
            character_id: ID of the character acquiring knowledge.
            chapter_id: Chapter at which this knowledge was acquired.
            knowledge_type: Type of knowledge — "fact", "rumor", "secret", etc.
            content: The knowledge content.
            source: Where the character learned this (optional).
            is_secret: Whether this knowledge is secret.
            notes: Free-form notes (optional).

        Returns:
            The newly created CharacterKnowledge with its assigned id, or
            NotFoundResponse if the character does not exist, or
            ValidationFailure on DB error.
        """
        async with get_connection() as conn:
            exists = await conn.execute_fetchall(
                "SELECT id FROM characters WHERE id = ?", (character_id,)
            )
            if not exists:
                return NotFoundResponse(not_found_message=f"Character {character_id} not found")

            try:
                cursor = await conn.execute(
                    """INSERT INTO character_knowledge
                        (character_id, chapter_id, knowledge_type, content,
                         source, is_secret, notes, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))""",
                    (character_id, chapter_id, knowledge_type, content,
                     source, is_secret, notes),
                )
                await conn.commit()
                new_id = cursor.lastrowid
                row = await conn.execute_fetchall(
                    "SELECT * FROM character_knowledge WHERE id = ?", (new_id,)
                )
                return CharacterKnowledge(**dict(row[0]))
            except Exception as exc:
                logger.error("log_character_knowledge failed: %s", exc)
                return ValidationFailure(is_valid=False, errors=[str(exc)])

    # ------------------------------------------------------------------
    # get_character_location
    # ------------------------------------------------------------------

    @mcp.tool()
    async def get_character_location(
        character_id: int,
        chapter_id: int | None = None,
    ) -> list[CharacterLocation] | NotFoundResponse:
        """Return location records for a character, optionally scoped by chapter.

        Args:
            character_id: ID of the character whose locations to retrieve.
            chapter_id: If provided, returns only records with chapter_id <= this value.

        Returns:
            List of CharacterLocation records ordered by chapter_id descending, or
            NotFoundResponse if the character does not exist.
        """
        async with get_connection() as conn:
            exists = await conn.execute_fetchall(
                "SELECT id FROM characters WHERE id = ?", (character_id,)
            )
            if not exists:
                return NotFoundResponse(not_found_message=f"Character {character_id} not found")

            if chapter_id is not None:
                rows = await conn.execute_fetchall(
                    "SELECT * FROM character_locations "
                    "WHERE character_id = ? AND chapter_id <= ? "
                    "ORDER BY chapter_id DESC",
                    (character_id, chapter_id),
                )
            else:
                rows = await conn.execute_fetchall(
                    "SELECT * FROM character_locations "
                    "WHERE character_id = ? "
                    "ORDER BY chapter_id DESC",
                    (character_id,),
                )
            return [CharacterLocation(**dict(row)) for row in rows]

    # ------------------------------------------------------------------
    # delete_character
    # ------------------------------------------------------------------

    @mcp.tool()
    async def delete_character(character_id: int) -> NotFoundResponse | ValidationFailure | dict:
        """Delete a character by ID.

        Idempotent: returns NotFoundResponse if the character does not exist.
        Refuses with ValidationFailure if dependent records (scenes, relationships,
        character_knowledge, etc.) reference this character.

        Args:
            character_id: Primary key of the character to delete.

        Returns:
            {"deleted": True, "id": character_id} on success.
            NotFoundResponse if not found.
            ValidationFailure if FK constraint blocks deletion.
        """
        async with get_connection() as conn:
            row = await conn.execute_fetchall(
                "SELECT id FROM characters WHERE id = ?", (character_id,)
            )
            if not row:
                return NotFoundResponse(not_found_message=f"Character {character_id} not found")
            try:
                await conn.execute("DELETE FROM characters WHERE id = ?", (character_id,))
                await conn.commit()
                return {"deleted": True, "id": character_id}
            except Exception as exc:
                logger.error("delete_character failed: %s", exc)
                return ValidationFailure(is_valid=False, errors=[str(exc)])

    # ------------------------------------------------------------------
    # delete_character_knowledge
    # ------------------------------------------------------------------

    @mcp.tool()
    async def delete_character_knowledge(
        character_knowledge_id: int,
    ) -> NotFoundResponse | dict:
        """Delete a character knowledge record by ID.

        Idempotent: returns NotFoundResponse if the record does not exist.
        character_knowledge is a log table with no FK children, so no FK
        constraint check is needed.

        Args:
            character_knowledge_id: Primary key of the character_knowledge record.

        Returns:
            {"deleted": True, "id": character_knowledge_id} on success.
            NotFoundResponse if not found.
        """
        async with get_connection() as conn:
            row = await conn.execute_fetchall(
                "SELECT id FROM character_knowledge WHERE id = ?",
                (character_knowledge_id,),
            )
            if not row:
                return NotFoundResponse(
                    not_found_message=f"Character knowledge {character_knowledge_id} not found"
                )
            await conn.execute(
                "DELETE FROM character_knowledge WHERE id = ?", (character_knowledge_id,)
            )
            await conn.commit()
            return {"deleted": True, "id": character_knowledge_id}

    # ------------------------------------------------------------------
    # log_character_belief
    # ------------------------------------------------------------------

    @mcp.tool()
    async def log_character_belief(
        character_id: int,
        content: str,
        belief_type: str = "worldview",
        strength: int = 5,
        formed_chapter_id: int | None = None,
        challenged_chapter_id: int | None = None,
        notes: str | None = None,
    ) -> CharacterBelief | NotFoundResponse | ValidationFailure:
        """Log a new belief held by a character.

        Beliefs are append-only records tracking a character's worldview,
        personal convictions, or moral stances as they evolve through the story.

        Args:
            character_id: ID of the character whose belief to log.
            content: The belief statement (required).
            belief_type: Category of belief — "worldview", "personal", "moral", etc.
            strength: Conviction strength 1-10 (default 5).
            formed_chapter_id: Chapter at which this belief was formed (optional).
            challenged_chapter_id: Chapter at which this belief was challenged (optional).
            notes: Free-form notes (optional).

        Returns:
            The newly created CharacterBelief with its assigned id, or
            NotFoundResponse if the character does not exist, or
            ValidationFailure on DB error.
        """
        async with get_connection() as conn:
            exists = await conn.execute_fetchall(
                "SELECT id FROM characters WHERE id = ?", (character_id,)
            )
            if not exists:
                return NotFoundResponse(not_found_message=f"Character {character_id} not found")

            if formed_chapter_id is not None:
                ch_row = await conn.execute_fetchall(
                    "SELECT id FROM chapters WHERE id = ?", (formed_chapter_id,)
                )
                if not ch_row:
                    return NotFoundResponse(
                        not_found_message=f"Chapter {formed_chapter_id} not found"
                    )

            try:
                cursor = await conn.execute(
                    """INSERT INTO character_beliefs
                        (character_id, belief_type, content, strength,
                         formed_chapter_id, challenged_chapter_id, notes,
                         created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))""",
                    (character_id, belief_type, content, strength,
                     formed_chapter_id, challenged_chapter_id, notes),
                )
                await conn.commit()
                new_id = cursor.lastrowid
                row = await conn.execute_fetchall(
                    "SELECT * FROM character_beliefs WHERE id = ?", (new_id,)
                )
                return CharacterBelief(**dict(row[0]))
            except Exception as exc:
                logger.error("log_character_belief failed: %s", exc)
                return ValidationFailure(is_valid=False, errors=[str(exc)])

    # ------------------------------------------------------------------
    # delete_character_belief
    # ------------------------------------------------------------------

    @mcp.tool()
    async def delete_character_belief(belief_id: int) -> NotFoundResponse | dict:
        """Delete a character belief record by ID.

        Idempotent: returns NotFoundResponse if the record does not exist.
        character_beliefs is a log table with no FK children, so no FK
        constraint check is needed.

        Args:
            belief_id: Primary key of the character_beliefs record.

        Returns:
            {"deleted": True, "id": belief_id} on success.
            NotFoundResponse if not found.
        """
        async with get_connection() as conn:
            row = await conn.execute_fetchall(
                "SELECT id FROM character_beliefs WHERE id = ?", (belief_id,)
            )
            if not row:
                return NotFoundResponse(
                    not_found_message=f"Character belief {belief_id} not found"
                )
            await conn.execute(
                "DELETE FROM character_beliefs WHERE id = ?", (belief_id,)
            )
            await conn.commit()
            return {"deleted": True, "id": belief_id}

    # ------------------------------------------------------------------
    # log_character_location
    # ------------------------------------------------------------------

    @mcp.tool()
    async def log_character_location(
        character_id: int,
        chapter_id: int,
        location_id: int | None = None,
        location_note: str | None = None,
    ) -> CharacterLocation | NotFoundResponse | ValidationFailure:
        """Log a character's location at a specific chapter.

        Location records are append-only and chapter-scoped, tracking where
        a character is as the story progresses.

        Args:
            character_id: ID of the character whose location to log.
            chapter_id: Chapter at which this location applies.
            location_id: FK to locations table (optional — use if a named location exists).
            location_note: Free-text location description (optional).

        Returns:
            The newly created CharacterLocation with its assigned id, or
            NotFoundResponse if the character or chapter does not exist, or
            ValidationFailure on DB error.
        """
        async with get_connection() as conn:
            char_row = await conn.execute_fetchall(
                "SELECT id FROM characters WHERE id = ?", (character_id,)
            )
            if not char_row:
                return NotFoundResponse(not_found_message=f"Character {character_id} not found")

            ch_row = await conn.execute_fetchall(
                "SELECT id FROM chapters WHERE id = ?", (chapter_id,)
            )
            if not ch_row:
                return NotFoundResponse(not_found_message=f"Chapter {chapter_id} not found")

            try:
                cursor = await conn.execute(
                    """INSERT INTO character_locations
                        (character_id, chapter_id, location_id, location_note, created_at)
                       VALUES (?, ?, ?, ?, datetime('now'))""",
                    (character_id, chapter_id, location_id, location_note),
                )
                await conn.commit()
                new_id = cursor.lastrowid
                row = await conn.execute_fetchall(
                    "SELECT * FROM character_locations WHERE id = ?", (new_id,)
                )
                return CharacterLocation(**dict(row[0]))
            except Exception as exc:
                logger.error("log_character_location failed: %s", exc)
                return ValidationFailure(is_valid=False, errors=[str(exc)])

    # ------------------------------------------------------------------
    # get_current_character_location
    # ------------------------------------------------------------------

    @mcp.tool()
    async def get_current_character_location(
        character_id: int,
    ) -> CharacterLocation | NotFoundResponse:
        """Return the most recent location record for a character.

        Selects the location with the highest chapter_id to represent the
        character's current known position.

        Args:
            character_id: ID of the character whose current location to retrieve.

        Returns:
            The most recent CharacterLocation, or NotFoundResponse if no
            location records exist for this character.
        """
        async with get_connection() as conn:
            rows = await conn.execute_fetchall(
                "SELECT * FROM character_locations "
                "WHERE character_id = ? "
                "ORDER BY chapter_id DESC LIMIT 1",
                (character_id,),
            )
            if not rows:
                return NotFoundResponse(
                    not_found_message=f"No location found for character {character_id}"
                )
            return CharacterLocation(**dict(rows[0]))

    # ------------------------------------------------------------------
    # delete_character_location
    # ------------------------------------------------------------------

    @mcp.tool()
    async def delete_character_location(location_id: int) -> NotFoundResponse | dict:
        """Delete a character location record by ID.

        Idempotent: returns NotFoundResponse if the record does not exist.
        character_locations is a log table with no FK children, so no FK
        constraint check is needed.

        Args:
            location_id: Primary key of the character_locations record.

        Returns:
            {"deleted": True, "id": location_id} on success.
            NotFoundResponse if not found.
        """
        async with get_connection() as conn:
            row = await conn.execute_fetchall(
                "SELECT id FROM character_locations WHERE id = ?", (location_id,)
            )
            if not row:
                return NotFoundResponse(
                    not_found_message=f"Character location {location_id} not found"
                )
            await conn.execute(
                "DELETE FROM character_locations WHERE id = ?", (location_id,)
            )
            await conn.commit()
            return {"deleted": True, "id": location_id}
