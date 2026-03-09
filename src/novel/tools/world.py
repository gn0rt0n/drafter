"""World domain MCP tools.

All 33 world tools are registered via the register(mcp) function pattern.
This module is standalone — it does not modify server.py; wiring happens in
the server module.

IMPORTANT: Never use the print function in this module. All logging goes to
stderr via the logging module — using print corrupts the stdio protocol.
"""

import json
import logging

from mcp.server.fastmcp import FastMCP

from novel.mcp.db import get_connection
from novel.models.world import (
    Act,
    Artifact,
    Book,
    Culture,
    Era,
    Faction,
    FactionPoliticalState,
    Location,
    ObjectState,
)
from novel.models.shared import NotFoundResponse, ValidationFailure

logger = logging.getLogger(__name__)


def register(mcp: FastMCP) -> None:
    """Register all 33 world domain tools with the given FastMCP instance.

    Tools are defined as local async functions and decorated with @mcp.tool().
    The FastMCP instance is always the one passed in — never imported globally.

    Args:
        mcp: The FastMCP server instance to register tools against.
    """

    # ------------------------------------------------------------------
    # get_book
    # ------------------------------------------------------------------

    @mcp.tool()
    async def get_book(book_id: int) -> Book | NotFoundResponse:
        """Look up a single book by ID, returning all fields.

        Args:
            book_id: Primary key of the book to retrieve.

        Returns:
            Book with all fields populated, or NotFoundResponse if the
            book does not exist.
        """
        async with get_connection() as conn:
            row = await conn.execute_fetchall(
                "SELECT * FROM books WHERE id = ?", (book_id,)
            )
            if not row:
                logger.debug("Book %d not found", book_id)
                return NotFoundResponse(not_found_message=f"Book {book_id} not found")
            return Book(**dict(row[0]))

    # ------------------------------------------------------------------
    # list_books
    # ------------------------------------------------------------------

    @mcp.tool()
    async def list_books() -> list[Book]:
        """Return all books ordered by series_order then id.

        Returns:
            List of Book objects ordered by series_order (nulls last), then id.
            Returns an empty list if no books exist.
        """
        async with get_connection() as conn:
            rows = await conn.execute_fetchall(
                "SELECT * FROM books ORDER BY series_order, id"
            )
            return [Book(**dict(row)) for row in rows]

    # ------------------------------------------------------------------
    # upsert_book
    # ------------------------------------------------------------------

    @mcp.tool()
    async def upsert_book(
        book_id: int | None,
        title: str,
        series_order: int | None = None,
        word_count_target: int | None = None,
        actual_word_count: int = 0,
        status: str = "planning",
        notes: str | None = None,
        canon_status: str = "draft",
    ) -> Book | ValidationFailure:
        """Create or update a book.

        When book_id is None, a new book is inserted and the AUTOINCREMENT
        primary key is assigned. When book_id is provided, the existing row
        is updated via ON CONFLICT(id) DO UPDATE.

        Args:
            book_id: Existing book ID to update, or None to create.
            title: Book title (required).
            series_order: Position in the series (optional).
            word_count_target: Target word count for the book (optional).
            actual_word_count: Actual word count written so far (default: 0).
            status: Drafting status — e.g. "planning", "drafting", "complete" (default: "planning").
            notes: Free-form notes (optional).
            canon_status: Canon status — e.g. "draft", "canon" (default: "draft").

        Returns:
            The created or updated Book, or ValidationFailure on DB error.
        """
        async with get_connection() as conn:
            try:
                if book_id is None:
                    cursor = await conn.execute(
                        """INSERT INTO books (
                            title, series_order, word_count_target, actual_word_count,
                            status, notes, canon_status, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))""",
                        (title, series_order, word_count_target, actual_word_count,
                         status, notes, canon_status),
                    )
                    new_id = cursor.lastrowid
                    await conn.commit()
                    row = await conn.execute_fetchall(
                        "SELECT * FROM books WHERE id = ?", (new_id,)
                    )
                else:
                    await conn.execute(
                        """INSERT INTO books (
                            id, title, series_order, word_count_target, actual_word_count,
                            status, notes, canon_status, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                        ON CONFLICT(id) DO UPDATE SET
                            title=excluded.title,
                            series_order=excluded.series_order,
                            word_count_target=excluded.word_count_target,
                            actual_word_count=excluded.actual_word_count,
                            status=excluded.status,
                            notes=excluded.notes,
                            canon_status=excluded.canon_status,
                            updated_at=datetime('now')""",
                        (book_id, title, series_order, word_count_target, actual_word_count,
                         status, notes, canon_status),
                    )
                    await conn.commit()
                    row = await conn.execute_fetchall(
                        "SELECT * FROM books WHERE id = ?", (book_id,)
                    )
            except Exception as exc:
                logger.error("upsert_book failed: %s", exc)
                return ValidationFailure(is_valid=False, errors=[str(exc)])

            return Book(**dict(row[0]))

    # ------------------------------------------------------------------
    # delete_book
    # ------------------------------------------------------------------

    @mcp.tool()
    async def delete_book(book_id: int) -> NotFoundResponse | ValidationFailure | dict:
        """Delete a book by ID, refusing if referenced records exist.

        FK-safe: books are referenced by acts (book_id NOT NULL), chapters
        (book_id NOT NULL), and story_structure / seven_point_structure
        (book_id NOT NULL). If any FK constraint is violated, returns
        ValidationFailure with the error rather than raising.

        Args:
            book_id: Primary key of the book to delete.

        Returns:
            {"deleted": True, "id": book_id} on success, NotFoundResponse
            if the book does not exist, or ValidationFailure if FK constraints
            prevent deletion.
        """
        async with get_connection() as conn:
            row = await conn.execute_fetchall(
                "SELECT id FROM books WHERE id = ?", (book_id,)
            )
            if not row:
                return NotFoundResponse(not_found_message=f"Book {book_id} not found")
            try:
                await conn.execute("DELETE FROM books WHERE id = ?", (book_id,))
                await conn.commit()
                return {"deleted": True, "id": book_id}
            except Exception as exc:
                logger.error("delete_book failed: %s", exc)
                return ValidationFailure(is_valid=False, errors=[str(exc)])

    # ------------------------------------------------------------------
    # get_era
    # ------------------------------------------------------------------

    @mcp.tool()
    async def get_era(era_id: int) -> Era | NotFoundResponse:
        """Look up a single era by ID, returning all fields.

        Args:
            era_id: Primary key of the era to retrieve.

        Returns:
            Era with all fields populated, or NotFoundResponse if the era
            does not exist.
        """
        async with get_connection() as conn:
            row = await conn.execute_fetchall(
                "SELECT * FROM eras WHERE id = ?", (era_id,)
            )
            if not row:
                logger.debug("Era %d not found", era_id)
                return NotFoundResponse(not_found_message=f"Era {era_id} not found")
            return Era(**dict(row[0]))

    # ------------------------------------------------------------------
    # list_eras
    # ------------------------------------------------------------------

    @mcp.tool()
    async def list_eras() -> list[Era]:
        """Return all eras ordered by sequence_order then name.

        Returns:
            List of Era objects ordered by sequence_order (nulls last), then name.
            Returns an empty list if no eras exist.
        """
        async with get_connection() as conn:
            rows = await conn.execute_fetchall(
                "SELECT * FROM eras ORDER BY sequence_order, name"
            )
            return [Era(**dict(row)) for row in rows]

    # ------------------------------------------------------------------
    # upsert_era
    # ------------------------------------------------------------------

    @mcp.tool()
    async def upsert_era(
        era_id: int | None,
        name: str,
        sequence_order: int | None = None,
        date_start: str | None = None,
        date_end: str | None = None,
        summary: str | None = None,
        certainty_level: str = "established",
        notes: str | None = None,
        canon_status: str = "draft",
    ) -> Era | ValidationFailure:
        """Create or update an era.

        When era_id is None, a new era is inserted and the AUTOINCREMENT
        primary key is assigned. When era_id is provided, the existing row
        is updated via ON CONFLICT(id) DO UPDATE.

        Args:
            era_id: Existing era ID to update, or None to create.
            name: Era name (required).
            sequence_order: Chronological order position (optional).
            date_start: Start date as text string (optional).
            date_end: End date as text string (optional).
            summary: Brief summary of the era (optional).
            certainty_level: How established this era is — e.g. "established", "speculative" (default: "established").
            notes: Free-form notes (optional).
            canon_status: Canon status — e.g. "draft", "canon" (default: "draft").

        Returns:
            The created or updated Era, or ValidationFailure on DB error.
        """
        async with get_connection() as conn:
            try:
                if era_id is None:
                    cursor = await conn.execute(
                        """INSERT INTO eras (
                            name, sequence_order, date_start, date_end,
                            summary, certainty_level, notes, canon_status, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))""",
                        (name, sequence_order, date_start, date_end,
                         summary, certainty_level, notes, canon_status),
                    )
                    new_id = cursor.lastrowid
                    await conn.commit()
                    row = await conn.execute_fetchall(
                        "SELECT * FROM eras WHERE id = ?", (new_id,)
                    )
                else:
                    await conn.execute(
                        """INSERT INTO eras (
                            id, name, sequence_order, date_start, date_end,
                            summary, certainty_level, notes, canon_status, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                        ON CONFLICT(id) DO UPDATE SET
                            name=excluded.name,
                            sequence_order=excluded.sequence_order,
                            date_start=excluded.date_start,
                            date_end=excluded.date_end,
                            summary=excluded.summary,
                            certainty_level=excluded.certainty_level,
                            notes=excluded.notes,
                            canon_status=excluded.canon_status,
                            updated_at=datetime('now')""",
                        (era_id, name, sequence_order, date_start, date_end,
                         summary, certainty_level, notes, canon_status),
                    )
                    await conn.commit()
                    row = await conn.execute_fetchall(
                        "SELECT * FROM eras WHERE id = ?", (era_id,)
                    )
            except Exception as exc:
                logger.error("upsert_era failed: %s", exc)
                return ValidationFailure(is_valid=False, errors=[str(exc)])

            return Era(**dict(row[0]))

    # ------------------------------------------------------------------
    # delete_era
    # ------------------------------------------------------------------

    @mcp.tool()
    async def delete_era(era_id: int) -> NotFoundResponse | ValidationFailure | dict:
        """Delete an era by ID, refusing if referenced records exist.

        FK-safe: eras are referenced by artifacts (origin_era_id FK) and
        by characters (home_era_id FK). If any FK constraint is violated,
        returns ValidationFailure with the error rather than raising.

        Args:
            era_id: Primary key of the era to delete.

        Returns:
            {"deleted": True, "id": era_id} on success, NotFoundResponse
            if the era does not exist, or ValidationFailure if FK constraints
            prevent deletion.
        """
        async with get_connection() as conn:
            row = await conn.execute_fetchall(
                "SELECT id FROM eras WHERE id = ?", (era_id,)
            )
            if not row:
                return NotFoundResponse(not_found_message=f"Era {era_id} not found")
            try:
                await conn.execute("DELETE FROM eras WHERE id = ?", (era_id,))
                await conn.commit()
                return {"deleted": True, "id": era_id}
            except Exception as exc:
                logger.error("delete_era failed: %s", exc)
                return ValidationFailure(is_valid=False, errors=[str(exc)])

    # ------------------------------------------------------------------
    # get_location
    # ------------------------------------------------------------------

    @mcp.tool()
    async def get_location(location_id: int) -> Location | NotFoundResponse:
        """Look up a single location by ID, returning all fields.

        The sensory_profile field is returned as a parsed dict (the
        field_validator on Location handles JSON string coercion automatically).

        Args:
            location_id: Primary key of the location to retrieve.

        Returns:
            Location with all fields populated (sensory_profile as dict), or
            NotFoundResponse if the location does not exist.
        """
        async with get_connection() as conn:
            row = await conn.execute_fetchall(
                "SELECT * FROM locations WHERE id = ?", (location_id,)
            )
            if not row:
                logger.debug("Location %d not found", location_id)
                return NotFoundResponse(not_found_message=f"Location {location_id} not found")
            return Location(**dict(row[0]))

    # ------------------------------------------------------------------
    # get_faction
    # ------------------------------------------------------------------

    @mcp.tool()
    async def get_faction(faction_id: int) -> Faction | NotFoundResponse:
        """Look up a single faction by ID, returning the full faction profile.

        Args:
            faction_id: Primary key of the faction to retrieve.

        Returns:
            Faction with all fields populated, or NotFoundResponse if the
            faction does not exist.
        """
        async with get_connection() as conn:
            row = await conn.execute_fetchall(
                "SELECT * FROM factions WHERE id = ?", (faction_id,)
            )
            if not row:
                logger.debug("Faction %d not found", faction_id)
                return NotFoundResponse(not_found_message=f"Faction {faction_id} not found")
            return Faction(**dict(row[0]))

    # ------------------------------------------------------------------
    # get_faction_political_state
    # ------------------------------------------------------------------

    @mcp.tool()
    async def get_faction_political_state(
        faction_id: int,
        chapter_id: int | None = None,
    ) -> FactionPoliticalState | NotFoundResponse:
        """Return the political state for a faction, optionally at a specific chapter.

        When chapter_id is None, returns the most recent state (highest
        chapter_id) for that faction. When chapter_id is provided, returns
        the state recorded at that exact chapter.

        Args:
            faction_id: ID of the faction whose political state to retrieve.
            chapter_id: If provided, returns the state for that specific chapter.
                        If None, returns the most recent recorded state.

        Returns:
            FactionPoliticalState with all fields, or NotFoundResponse if no
            political state record exists for the given faction (and chapter).
        """
        async with get_connection() as conn:
            if chapter_id is not None:
                row = await conn.execute_fetchall(
                    "SELECT * FROM faction_political_states "
                    "WHERE faction_id = ? AND chapter_id = ?",
                    (faction_id, chapter_id),
                )
            else:
                row = await conn.execute_fetchall(
                    "SELECT * FROM faction_political_states "
                    "WHERE faction_id = ? ORDER BY chapter_id DESC LIMIT 1",
                    (faction_id,),
                )
            if not row:
                logger.debug(
                    "No political state found for faction %d chapter %s",
                    faction_id, chapter_id,
                )
                return NotFoundResponse(
                    not_found_message=f"No political state found for faction {faction_id}"
                )
            return FactionPoliticalState(**dict(row[0]))

    # ------------------------------------------------------------------
    # get_culture
    # ------------------------------------------------------------------

    @mcp.tool()
    async def get_culture(culture_id: int) -> Culture | NotFoundResponse:
        """Look up a single culture record by ID.

        Args:
            culture_id: Primary key of the culture to retrieve.

        Returns:
            Culture with all fields populated, or NotFoundResponse if the
            culture does not exist.
        """
        async with get_connection() as conn:
            row = await conn.execute_fetchall(
                "SELECT * FROM cultures WHERE id = ?", (culture_id,)
            )
            if not row:
                logger.debug("Culture %d not found", culture_id)
                return NotFoundResponse(not_found_message=f"Culture {culture_id} not found")
            return Culture(**dict(row[0]))

    # ------------------------------------------------------------------
    # upsert_location
    # ------------------------------------------------------------------

    @mcp.tool()
    async def upsert_location(
        location_id: int | None,
        name: str,
        location_type: str | None = None,
        parent_location_id: int | None = None,
        culture_id: int | None = None,
        controlling_faction_id: int | None = None,
        description: str | None = None,
        sensory_profile: dict | None = None,
        strategic_value: str | None = None,
        accessibility: str | None = None,
        notable_features: str | None = None,
        notes: str | None = None,
    ) -> Location | ValidationFailure:
        """Create or update a location.

        The sensory_profile dict is serialised to a JSON string for storage
        and automatically parsed back to a dict on return.

        When location_id is None, a new location is inserted and the
        AUTOINCREMENT primary key is assigned. When location_id is provided,
        the existing row is updated via ON CONFLICT(id) DO UPDATE.

        Args:
            location_id: Existing location ID to update, or None to create.
            name: Location name (required).
            location_type: Category — e.g. "city", "wilderness", "building" (optional).
            parent_location_id: FK to parent location (optional).
            culture_id: FK to cultures table (optional).
            controlling_faction_id: FK to factions table (optional).
            description: Narrative description of the location (optional).
            sensory_profile: Dict of sensory details — sight, sound, smell, etc. (optional).
            strategic_value: Strategic importance notes (optional).
            accessibility: How accessible the location is (optional).
            notable_features: Distinctive features of the location (optional).
            notes: Free-form notes (optional).

        Returns:
            The created or updated Location (sensory_profile as dict), or
            ValidationFailure on DB error.
        """
        async with get_connection() as conn:
            try:
                if location_id is None:
                    # Build model object to use to_db_dict() for sensory_profile serialisation
                    loc = Location(
                        name=name,
                        location_type=location_type,
                        parent_location_id=parent_location_id,
                        culture_id=culture_id,
                        controlling_faction_id=controlling_faction_id,
                        description=description,
                        sensory_profile=sensory_profile,
                        strategic_value=strategic_value,
                        accessibility=accessibility,
                        notable_features=notable_features,
                        notes=notes,
                    )
                    db_dict = loc.to_db_dict()
                    cursor = await conn.execute(
                        """INSERT INTO locations (
                            name, location_type, parent_location_id, culture_id,
                            controlling_faction_id, description, sensory_profile,
                            strategic_value, accessibility, notable_features,
                            notes, updated_at
                        ) VALUES (
                            ?, ?, ?, ?,
                            ?, ?, ?,
                            ?, ?, ?,
                            ?, datetime('now')
                        )""",
                        (
                            db_dict["name"], db_dict["location_type"],
                            db_dict["parent_location_id"], db_dict["culture_id"],
                            db_dict["controlling_faction_id"], db_dict["description"],
                            db_dict["sensory_profile"],
                            db_dict["strategic_value"], db_dict["accessibility"],
                            db_dict["notable_features"], db_dict["notes"],
                        ),
                    )
                    new_id = cursor.lastrowid
                    await conn.commit()
                    row = await conn.execute_fetchall(
                        "SELECT * FROM locations WHERE id = ?", (new_id,)
                    )
                else:
                    # UPSERT — update existing row via ON CONFLICT(id) DO UPDATE
                    sensory_profile_json = json.dumps(sensory_profile) if sensory_profile is not None else None
                    await conn.execute(
                        """INSERT INTO locations (
                            id, name, location_type, parent_location_id, culture_id,
                            controlling_faction_id, description, sensory_profile,
                            strategic_value, accessibility, notable_features,
                            notes, updated_at
                        ) VALUES (
                            ?, ?, ?, ?, ?,
                            ?, ?, ?,
                            ?, ?, ?,
                            ?, datetime('now')
                        )
                        ON CONFLICT(id) DO UPDATE SET
                            name=excluded.name,
                            location_type=excluded.location_type,
                            parent_location_id=excluded.parent_location_id,
                            culture_id=excluded.culture_id,
                            controlling_faction_id=excluded.controlling_faction_id,
                            description=excluded.description,
                            sensory_profile=excluded.sensory_profile,
                            strategic_value=excluded.strategic_value,
                            accessibility=excluded.accessibility,
                            notable_features=excluded.notable_features,
                            notes=excluded.notes,
                            updated_at=datetime('now')
                        """,
                        (
                            location_id,
                            name, location_type, parent_location_id, culture_id,
                            controlling_faction_id, description, sensory_profile_json,
                            strategic_value, accessibility, notable_features,
                            notes,
                        ),
                    )
                    await conn.commit()
                    row = await conn.execute_fetchall(
                        "SELECT * FROM locations WHERE id = ?", (location_id,)
                    )
            except Exception as exc:
                logger.error("upsert_location failed: %s", exc)
                return ValidationFailure(is_valid=False, errors=[str(exc)])

            return Location(**dict(row[0]))

    # ------------------------------------------------------------------
    # upsert_faction
    # ------------------------------------------------------------------

    @mcp.tool()
    async def upsert_faction(
        faction_id: int | None,
        name: str,
        faction_type: str | None = None,
        leader_character_id: int | None = None,
        headquarters: str | None = None,
        size_estimate: str | None = None,
        goals: str | None = None,
        resources: str | None = None,
        weaknesses: str | None = None,
        alliances: str | None = None,
        conflicts: str | None = None,
        notes: str | None = None,
    ) -> Faction | ValidationFailure:
        """Create or update a faction.

        Does NOT write to faction_political_states — that is a separate
        time-stamped log table managed independently.

        When faction_id is None, uses ON CONFLICT(name) DO UPDATE so that
        re-creating a faction by name merges rather than duplicates. When
        faction_id is provided, uses ON CONFLICT(id) DO UPDATE.

        Args:
            faction_id: Existing faction ID to update, or None to create/merge by name.
            name: Faction name — UNIQUE constraint in the database (required).
            faction_type: Category of faction — e.g. "political", "military" (optional).
            leader_character_id: FK to characters table for faction leader (optional).
            headquarters: Description or location of HQ (optional).
            size_estimate: Estimated membership size (optional).
            goals: Faction goals and objectives (optional).
            resources: Available resources (optional).
            weaknesses: Known weaknesses (optional).
            alliances: Current alliance descriptions (optional).
            conflicts: Current conflict descriptions (optional).
            notes: Free-form notes (optional).

        Returns:
            The created or updated Faction, or ValidationFailure on DB error.
        """
        async with get_connection() as conn:
            try:
                if faction_id is None:
                    # No id — conflict target is UNIQUE(name); always SELECT back by name
                    cursor = await conn.execute(
                        """INSERT INTO factions (
                            name, faction_type, leader_character_id, headquarters,
                            size_estimate, goals, resources, weaknesses,
                            alliances, conflicts, notes, updated_at
                        ) VALUES (
                            ?, ?, ?, ?,
                            ?, ?, ?, ?,
                            ?, ?, ?, datetime('now')
                        )
                        ON CONFLICT(name) DO UPDATE SET
                            faction_type=excluded.faction_type,
                            leader_character_id=excluded.leader_character_id,
                            headquarters=excluded.headquarters,
                            size_estimate=excluded.size_estimate,
                            goals=excluded.goals,
                            resources=excluded.resources,
                            weaknesses=excluded.weaknesses,
                            alliances=excluded.alliances,
                            conflicts=excluded.conflicts,
                            notes=excluded.notes,
                            updated_at=datetime('now')
                        """,
                        (
                            name, faction_type, leader_character_id, headquarters,
                            size_estimate, goals, resources, weaknesses,
                            alliances, conflicts, notes,
                        ),
                    )
                    await conn.commit()
                    # lastrowid is 0 on conflict — always re-query by name
                    row = await conn.execute_fetchall(
                        "SELECT * FROM factions WHERE name = ?", (name,)
                    )
                else:
                    # Provided id — conflict target is id
                    await conn.execute(
                        """INSERT INTO factions (
                            id, name, faction_type, leader_character_id, headquarters,
                            size_estimate, goals, resources, weaknesses,
                            alliances, conflicts, notes, updated_at
                        ) VALUES (
                            ?, ?, ?, ?, ?,
                            ?, ?, ?, ?,
                            ?, ?, ?, datetime('now')
                        )
                        ON CONFLICT(id) DO UPDATE SET
                            name=excluded.name,
                            faction_type=excluded.faction_type,
                            leader_character_id=excluded.leader_character_id,
                            headquarters=excluded.headquarters,
                            size_estimate=excluded.size_estimate,
                            goals=excluded.goals,
                            resources=excluded.resources,
                            weaknesses=excluded.weaknesses,
                            alliances=excluded.alliances,
                            conflicts=excluded.conflicts,
                            notes=excluded.notes,
                            updated_at=datetime('now')
                        """,
                        (
                            faction_id,
                            name, faction_type, leader_character_id, headquarters,
                            size_estimate, goals, resources, weaknesses,
                            alliances, conflicts, notes,
                        ),
                    )
                    await conn.commit()
                    row = await conn.execute_fetchall(
                        "SELECT * FROM factions WHERE id = ?", (faction_id,)
                    )
            except Exception as exc:
                logger.error("upsert_faction failed: %s", exc)
                return ValidationFailure(is_valid=False, errors=[str(exc)])

            return Faction(**dict(row[0]))

    # ------------------------------------------------------------------
    # delete_location
    # ------------------------------------------------------------------

    @mcp.tool()
    async def delete_location(location_id: int) -> NotFoundResponse | ValidationFailure | dict:
        """Delete a location by ID, refusing if referenced records exist.

        FK-safe: factions and characters may reference locations via
        controlling_faction_id and other optional FK columns. If any FK
        constraint is violated, returns ValidationFailure with the error
        rather than raising.

        Args:
            location_id: Primary key of the location to delete.

        Returns:
            {"deleted": True, "id": location_id} on success, NotFoundResponse
            if the location does not exist, or ValidationFailure if FK
            constraints prevent deletion.
        """
        async with get_connection() as conn:
            row = await conn.execute_fetchall(
                "SELECT id FROM locations WHERE id = ?", (location_id,)
            )
            if not row:
                return NotFoundResponse(not_found_message=f"Location {location_id} not found")
            try:
                await conn.execute("DELETE FROM locations WHERE id = ?", (location_id,))
                await conn.commit()
                return {"deleted": True, "id": location_id}
            except Exception as exc:
                logger.error("delete_location failed: %s", exc)
                return ValidationFailure(is_valid=False, errors=[str(exc)])

    # ------------------------------------------------------------------
    # delete_faction
    # ------------------------------------------------------------------

    @mcp.tool()
    async def delete_faction(faction_id: int) -> NotFoundResponse | ValidationFailure | dict:
        """Delete a faction by ID, refusing if referenced records exist.

        FK-safe: factions are referenced by faction_political_states
        (faction_id FK) and by characters (faction_id FK, nullable). If
        either FK constraint is violated, returns ValidationFailure with the
        error rather than raising.

        Args:
            faction_id: Primary key of the faction to delete.

        Returns:
            {"deleted": True, "id": faction_id} on success, NotFoundResponse
            if the faction does not exist, or ValidationFailure if FK
            constraints prevent deletion.
        """
        async with get_connection() as conn:
            row = await conn.execute_fetchall(
                "SELECT id FROM factions WHERE id = ?", (faction_id,)
            )
            if not row:
                return NotFoundResponse(not_found_message=f"Faction {faction_id} not found")
            try:
                await conn.execute("DELETE FROM factions WHERE id = ?", (faction_id,))
                await conn.commit()
                return {"deleted": True, "id": faction_id}
            except Exception as exc:
                logger.error("delete_faction failed: %s", exc)
                return ValidationFailure(is_valid=False, errors=[str(exc)])

    # ------------------------------------------------------------------
    # upsert_culture
    # ------------------------------------------------------------------

    @mcp.tool()
    async def upsert_culture(
        culture_id: int | None,
        name: str,
        region: str | None = None,
        language_family: str | None = None,
        naming_conventions: str | None = None,
        social_structure: str | None = None,
        values_beliefs: str | None = None,
        taboos: str | None = None,
        aesthetic_style: str | None = None,
        notes: str | None = None,
        canon_status: str = "draft",
        source_file: str | None = None,
    ) -> Culture | ValidationFailure:
        """Create or update a culture.

        When culture_id is None, uses ON CONFLICT(name) DO UPDATE so that
        re-creating a culture by name merges rather than duplicates. When
        culture_id is provided, uses ON CONFLICT(id) DO UPDATE.

        Args:
            culture_id: Existing culture ID to update, or None to create/merge by name.
            name: Culture name — UNIQUE constraint in the database (required).
            region: Geographic region of the culture (optional).
            language_family: Language family or linguistic grouping (optional).
            naming_conventions: Naming patterns and conventions (optional).
            social_structure: Description of social hierarchy and structure (optional).
            values_beliefs: Core values and belief systems (optional).
            taboos: Cultural taboos and prohibitions (optional).
            aesthetic_style: Artistic and aesthetic preferences (optional).
            notes: Free-form notes (optional).
            canon_status: Canon status — e.g. "draft", "approved" (default: "draft").
            source_file: Source seed file if applicable (optional).

        Returns:
            The created or updated Culture, or ValidationFailure on DB error.
        """
        async with get_connection() as conn:
            try:
                if culture_id is None:
                    # No id — conflict target is UNIQUE(name); always SELECT back by name
                    await conn.execute(
                        """INSERT INTO cultures (
                            name, region, language_family, naming_conventions,
                            social_structure, values_beliefs, taboos, aesthetic_style,
                            notes, canon_status, source_file, updated_at
                        ) VALUES (
                            ?, ?, ?, ?,
                            ?, ?, ?, ?,
                            ?, ?, ?, datetime('now')
                        )
                        ON CONFLICT(name) DO UPDATE SET
                            region=excluded.region,
                            language_family=excluded.language_family,
                            naming_conventions=excluded.naming_conventions,
                            social_structure=excluded.social_structure,
                            values_beliefs=excluded.values_beliefs,
                            taboos=excluded.taboos,
                            aesthetic_style=excluded.aesthetic_style,
                            notes=excluded.notes,
                            canon_status=excluded.canon_status,
                            source_file=excluded.source_file,
                            updated_at=datetime('now')
                        """,
                        (
                            name, region, language_family, naming_conventions,
                            social_structure, values_beliefs, taboos, aesthetic_style,
                            notes, canon_status, source_file,
                        ),
                    )
                    await conn.commit()
                    row = await conn.execute_fetchall(
                        "SELECT * FROM cultures WHERE name = ?", (name,)
                    )
                else:
                    # Provided id — conflict target is id
                    await conn.execute(
                        """INSERT INTO cultures (
                            id, name, region, language_family, naming_conventions,
                            social_structure, values_beliefs, taboos, aesthetic_style,
                            notes, canon_status, source_file, updated_at
                        ) VALUES (
                            ?, ?, ?, ?, ?,
                            ?, ?, ?, ?,
                            ?, ?, ?, datetime('now')
                        )
                        ON CONFLICT(id) DO UPDATE SET
                            name=excluded.name,
                            region=excluded.region,
                            language_family=excluded.language_family,
                            naming_conventions=excluded.naming_conventions,
                            social_structure=excluded.social_structure,
                            values_beliefs=excluded.values_beliefs,
                            taboos=excluded.taboos,
                            aesthetic_style=excluded.aesthetic_style,
                            notes=excluded.notes,
                            canon_status=excluded.canon_status,
                            source_file=excluded.source_file,
                            updated_at=datetime('now')
                        """,
                        (
                            culture_id,
                            name, region, language_family, naming_conventions,
                            social_structure, values_beliefs, taboos, aesthetic_style,
                            notes, canon_status, source_file,
                        ),
                    )
                    await conn.commit()
                    row = await conn.execute_fetchall(
                        "SELECT * FROM cultures WHERE id = ?", (culture_id,)
                    )
            except Exception as exc:
                logger.error("upsert_culture failed: %s", exc)
                return ValidationFailure(is_valid=False, errors=[str(exc)])

            return Culture(**dict(row[0]))

    # ------------------------------------------------------------------
    # list_cultures
    # ------------------------------------------------------------------

    @mcp.tool()
    async def list_cultures() -> list[Culture]:
        """Return all cultures ordered by name.

        Returns:
            List of Culture objects ordered alphabetically by name.
            Returns an empty list if no cultures exist.
        """
        async with get_connection() as conn:
            rows = await conn.execute_fetchall(
                "SELECT * FROM cultures ORDER BY name"
            )
            return [Culture(**dict(row)) for row in rows]

    # ------------------------------------------------------------------
    # delete_culture
    # ------------------------------------------------------------------

    @mcp.tool()
    async def delete_culture(culture_id: int) -> NotFoundResponse | ValidationFailure | dict:
        """Delete a culture by ID, refusing if referenced records exist.

        FK-safe: cultures are referenced by locations (culture_id FK) and by
        the name_registry (culture_id FK). If any FK constraint is violated,
        returns ValidationFailure with the error rather than raising.

        Args:
            culture_id: Primary key of the culture to delete.

        Returns:
            {"deleted": True, "id": culture_id} on success, NotFoundResponse
            if the culture does not exist, or ValidationFailure if FK
            constraints prevent deletion.
        """
        async with get_connection() as conn:
            row = await conn.execute_fetchall(
                "SELECT id FROM cultures WHERE id = ?", (culture_id,)
            )
            if not row:
                return NotFoundResponse(not_found_message=f"Culture {culture_id} not found")
            try:
                await conn.execute("DELETE FROM cultures WHERE id = ?", (culture_id,))
                await conn.commit()
                return {"deleted": True, "id": culture_id}
            except Exception as exc:
                logger.error("delete_culture failed: %s", exc)
                return ValidationFailure(is_valid=False, errors=[str(exc)])

    # ------------------------------------------------------------------
    # log_faction_political_state
    # ------------------------------------------------------------------

    @mcp.tool()
    async def log_faction_political_state(
        faction_id: int,
        chapter_id: int,
        power_level: int = 5,
        alliances: str | None = None,
        conflicts: str | None = None,
        internal_state: str | None = None,
        noted_by_character_id: int | None = None,
        notes: str | None = None,
    ) -> FactionPoliticalState | NotFoundResponse | ValidationFailure:
        """Record a political state snapshot for a faction at a specific chapter.

        The faction_political_states table has a UNIQUE(faction_id, chapter_id)
        constraint — only one political state per faction per chapter.

        Args:
            faction_id: ID of the faction whose political state to record (required).
            chapter_id: Chapter at which this state is recorded (required).
            power_level: Power level 1-10 (default: 5).
            alliances: Current alliances description (optional).
            conflicts: Current conflicts description (optional).
            internal_state: Internal faction state description (optional).
            noted_by_character_id: FK to characters — who noted this state (optional).
            notes: Free-form notes (optional).

        Returns:
            The newly created FactionPoliticalState, NotFoundResponse if the
            faction does not exist, or ValidationFailure on DB error.
        """
        async with get_connection() as conn:
            fac = await conn.execute_fetchall(
                "SELECT id FROM factions WHERE id = ?", (faction_id,)
            )
            if not fac:
                return NotFoundResponse(
                    not_found_message=f"Faction {faction_id} not found"
                )
            try:
                cursor = await conn.execute(
                    """INSERT INTO faction_political_states (
                        faction_id, chapter_id, power_level, alliances,
                        conflicts, internal_state, noted_by_character_id, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        faction_id, chapter_id, power_level, alliances,
                        conflicts, internal_state, noted_by_character_id, notes,
                    ),
                )
                new_id = cursor.lastrowid
                await conn.commit()
                row = await conn.execute_fetchall(
                    "SELECT * FROM faction_political_states WHERE id = ?", (new_id,)
                )
                return FactionPoliticalState(**dict(row[0]))
            except Exception as exc:
                logger.error("log_faction_political_state failed: %s", exc)
                return ValidationFailure(is_valid=False, errors=[str(exc)])

    # ------------------------------------------------------------------
    # get_current_faction_political_state
    # ------------------------------------------------------------------

    @mcp.tool()
    async def get_current_faction_political_state(
        faction_id: int,
    ) -> FactionPoliticalState | NotFoundResponse:
        """Return the most recent political state for a faction.

        Selects the row with the highest id for the given faction, which
        corresponds to the most recently logged political state entry.

        Args:
            faction_id: ID of the faction whose most recent political state to retrieve.

        Returns:
            The most recent FactionPoliticalState for the faction, or
            NotFoundResponse if no political state records exist for it.
        """
        async with get_connection() as conn:
            rows = await conn.execute_fetchall(
                "SELECT * FROM faction_political_states "
                "WHERE faction_id = ? ORDER BY id DESC LIMIT 1",
                (faction_id,),
            )
            if not rows:
                return NotFoundResponse(
                    not_found_message=f"No political state found for faction {faction_id}"
                )
            return FactionPoliticalState(**dict(rows[0]))

    # ------------------------------------------------------------------
    # delete_faction_political_state
    # ------------------------------------------------------------------

    @mcp.tool()
    async def delete_faction_political_state(
        political_state_id: int,
    ) -> NotFoundResponse | dict:
        """Delete a faction political state entry by ID.

        Log-style delete: faction_political_states has no FK children, so
        no try/except for FK violations is needed.

        Args:
            political_state_id: Primary key of the political state entry to delete.

        Returns:
            {"deleted": True, "id": political_state_id} on success, or
            NotFoundResponse if the entry does not exist.
        """
        async with get_connection() as conn:
            row = await conn.execute_fetchall(
                "SELECT id FROM faction_political_states WHERE id = ?",
                (political_state_id,),
            )
            if not row:
                return NotFoundResponse(
                    not_found_message=f"Faction political state {political_state_id} not found"
                )
            await conn.execute(
                "DELETE FROM faction_political_states WHERE id = ?",
                (political_state_id,),
            )
            await conn.commit()
            return {"deleted": True, "id": political_state_id}

    # ------------------------------------------------------------------
    # get_act
    # ------------------------------------------------------------------

    @mcp.tool()
    async def get_act(act_id: int) -> Act | NotFoundResponse:
        """Look up a single act by ID, returning all fields.

        Args:
            act_id: Primary key of the act to retrieve.

        Returns:
            Act with all fields populated, or NotFoundResponse if the act
            does not exist.
        """
        async with get_connection() as conn:
            row = await conn.execute_fetchall(
                "SELECT * FROM acts WHERE id = ?", (act_id,)
            )
            if not row:
                logger.debug("Act %d not found", act_id)
                return NotFoundResponse(not_found_message=f"Act {act_id} not found")
            return Act(**dict(row[0]))

    # ------------------------------------------------------------------
    # list_acts
    # ------------------------------------------------------------------

    @mcp.tool()
    async def list_acts(book_id: int) -> list[Act]:
        """Return all acts for a given book, ordered by act_number.

        Args:
            book_id: ID of the book whose acts to list.

        Returns:
            List of Act objects ordered by act_number. Returns an empty list
            if the book has no acts (or the book does not exist).
        """
        async with get_connection() as conn:
            rows = await conn.execute_fetchall(
                "SELECT * FROM acts WHERE book_id = ? ORDER BY act_number",
                (book_id,),
            )
            return [Act(**dict(row)) for row in rows]

    # ------------------------------------------------------------------
    # upsert_act
    # ------------------------------------------------------------------

    @mcp.tool()
    async def upsert_act(
        act_id: int | None,
        book_id: int,
        act_number: int,
        name: str | None = None,
        purpose: str | None = None,
        word_count_target: int | None = None,
        start_chapter_id: int | None = None,
        end_chapter_id: int | None = None,
        structural_notes: str | None = None,
        canon_status: str = "draft",
    ) -> Act | NotFoundResponse | ValidationFailure:
        """Create or update an act.

        Pre-checks that book_id exists before writing. The start_chapter_id
        and end_chapter_id are nullable FKs to chapters — pass None freely;
        they are NOT pre-checked (intentional design to allow acts to be
        created before chapters exist).

        The acts table has a UNIQUE(book_id, act_number) constraint. Upserting
        with an existing (book_id, act_number) pair will update the existing row.

        When act_id is None, a new act is inserted via AUTOINCREMENT. When
        act_id is provided, the existing row is updated via ON CONFLICT(id) DO UPDATE.

        Args:
            act_id: Existing act ID to update, or None to create.
            book_id: ID of the book this act belongs to (required).
            act_number: Act number within the book (required). UNIQUE per book.
            name: Act name or title (optional).
            purpose: Narrative purpose of the act (optional).
            word_count_target: Target word count for this act (optional).
            start_chapter_id: FK to chapters — first chapter of the act (optional).
            end_chapter_id: FK to chapters — last chapter of the act (optional).
            structural_notes: Notes on act structure (optional).
            canon_status: Canon status — e.g. "draft", "canon" (default: "draft").

        Returns:
            The created or updated Act, NotFoundResponse if book_id does not
            exist, or ValidationFailure on DB error.
        """
        async with get_connection() as conn:
            book_row = await conn.execute_fetchall(
                "SELECT id FROM books WHERE id = ?", (book_id,)
            )
            if not book_row:
                return NotFoundResponse(not_found_message=f"Book {book_id} not found")
            try:
                if act_id is None:
                    cursor = await conn.execute(
                        """INSERT INTO acts (
                            book_id, act_number, name, purpose, word_count_target,
                            start_chapter_id, end_chapter_id, structural_notes,
                            canon_status, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))""",
                        (book_id, act_number, name, purpose, word_count_target,
                         start_chapter_id, end_chapter_id, structural_notes, canon_status),
                    )
                    new_id = cursor.lastrowid
                    await conn.commit()
                    row = await conn.execute_fetchall(
                        "SELECT * FROM acts WHERE id = ?", (new_id,)
                    )
                else:
                    await conn.execute(
                        """INSERT INTO acts (
                            id, book_id, act_number, name, purpose, word_count_target,
                            start_chapter_id, end_chapter_id, structural_notes,
                            canon_status, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                        ON CONFLICT(id) DO UPDATE SET
                            book_id=excluded.book_id,
                            act_number=excluded.act_number,
                            name=excluded.name,
                            purpose=excluded.purpose,
                            word_count_target=excluded.word_count_target,
                            start_chapter_id=excluded.start_chapter_id,
                            end_chapter_id=excluded.end_chapter_id,
                            structural_notes=excluded.structural_notes,
                            canon_status=excluded.canon_status,
                            updated_at=datetime('now')""",
                        (act_id, book_id, act_number, name, purpose, word_count_target,
                         start_chapter_id, end_chapter_id, structural_notes, canon_status),
                    )
                    await conn.commit()
                    row = await conn.execute_fetchall(
                        "SELECT * FROM acts WHERE id = ?", (act_id,)
                    )
            except Exception as exc:
                logger.error("upsert_act failed: %s", exc)
                return ValidationFailure(is_valid=False, errors=[str(exc)])

            return Act(**dict(row[0]))

    # ------------------------------------------------------------------
    # delete_act
    # ------------------------------------------------------------------

    @mcp.tool()
    async def delete_act(act_id: int) -> NotFoundResponse | ValidationFailure | dict:
        """Delete an act by ID.

        FK-safe pattern used for consistency, even though acts have no known
        FK children. If any FK constraint is violated, returns ValidationFailure
        with the error rather than raising.

        Args:
            act_id: Primary key of the act to delete.

        Returns:
            {"deleted": True, "id": act_id} on success, NotFoundResponse
            if the act does not exist, or ValidationFailure if FK constraints
            prevent deletion.
        """
        async with get_connection() as conn:
            row = await conn.execute_fetchall(
                "SELECT id FROM acts WHERE id = ?", (act_id,)
            )
            if not row:
                return NotFoundResponse(not_found_message=f"Act {act_id} not found")
            try:
                await conn.execute("DELETE FROM acts WHERE id = ?", (act_id,))
                await conn.commit()
                return {"deleted": True, "id": act_id}
            except Exception as exc:
                logger.error("delete_act failed: %s", exc)
                return ValidationFailure(is_valid=False, errors=[str(exc)])

    # ------------------------------------------------------------------
    # get_artifact
    # ------------------------------------------------------------------

    @mcp.tool()
    async def get_artifact(artifact_id: int) -> Artifact | NotFoundResponse:
        """Look up a single artifact by ID, returning all fields.

        Args:
            artifact_id: Primary key of the artifact to retrieve.

        Returns:
            Artifact with all fields populated, or NotFoundResponse if the
            artifact does not exist.
        """
        async with get_connection() as conn:
            row = await conn.execute_fetchall(
                "SELECT * FROM artifacts WHERE id = ?", (artifact_id,)
            )
            if not row:
                logger.debug("Artifact %d not found", artifact_id)
                return NotFoundResponse(not_found_message=f"Artifact {artifact_id} not found")
            return Artifact(**dict(row[0]))

    # ------------------------------------------------------------------
    # list_artifacts
    # ------------------------------------------------------------------

    @mcp.tool()
    async def list_artifacts() -> list[Artifact]:
        """Return all artifacts ordered by name.

        Returns:
            List of Artifact objects ordered alphabetically by name.
            Returns an empty list if no artifacts exist.
        """
        async with get_connection() as conn:
            rows = await conn.execute_fetchall(
                "SELECT * FROM artifacts ORDER BY name"
            )
            return [Artifact(**dict(row)) for row in rows]

    # ------------------------------------------------------------------
    # upsert_artifact
    # ------------------------------------------------------------------

    @mcp.tool()
    async def upsert_artifact(
        artifact_id: int | None,
        name: str,
        artifact_type: str | None = None,
        current_owner_id: int | None = None,
        current_location_id: int | None = None,
        origin_era_id: int | None = None,
        description: str | None = None,
        significance: str | None = None,
        magical_properties: str | None = None,
        history: str | None = None,
        notes: str | None = None,
        canon_status: str = "draft",
        source_file: str | None = None,
    ) -> Artifact | ValidationFailure:
        """Create or update an artifact.

        When artifact_id is None, a new artifact is inserted and the
        AUTOINCREMENT primary key is assigned. When artifact_id is provided,
        the existing row is updated via ON CONFLICT(id) DO UPDATE.

        Args:
            artifact_id: Existing artifact ID to update, or None to create.
            name: Artifact name (required).
            artifact_type: Category — e.g. "weapon", "relic", "document" (optional).
            current_owner_id: FK to characters — current owner (optional).
            current_location_id: FK to locations — current location (optional).
            origin_era_id: FK to eras — era of origin (optional).
            description: Narrative description of the artifact (optional).
            significance: Story significance of the artifact (optional).
            magical_properties: Magical or special properties (optional).
            history: Historical background of the artifact (optional).
            notes: Free-form notes (optional).
            canon_status: Canon status — e.g. "draft", "canon" (default: "draft").
            source_file: Source seed file if applicable (optional).

        Returns:
            The created or updated Artifact, or ValidationFailure on DB error.
        """
        async with get_connection() as conn:
            try:
                if artifact_id is None:
                    cursor = await conn.execute(
                        """INSERT INTO artifacts (
                            name, artifact_type, current_owner_id, current_location_id,
                            origin_era_id, description, significance, magical_properties,
                            history, notes, canon_status, source_file, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))""",
                        (
                            name, artifact_type, current_owner_id, current_location_id,
                            origin_era_id, description, significance, magical_properties,
                            history, notes, canon_status, source_file,
                        ),
                    )
                    new_id = cursor.lastrowid
                    await conn.commit()
                    row = await conn.execute_fetchall(
                        "SELECT * FROM artifacts WHERE id = ?", (new_id,)
                    )
                else:
                    await conn.execute(
                        """INSERT INTO artifacts (
                            id, name, artifact_type, current_owner_id, current_location_id,
                            origin_era_id, description, significance, magical_properties,
                            history, notes, canon_status, source_file, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                        ON CONFLICT(id) DO UPDATE SET
                            name=excluded.name,
                            artifact_type=excluded.artifact_type,
                            current_owner_id=excluded.current_owner_id,
                            current_location_id=excluded.current_location_id,
                            origin_era_id=excluded.origin_era_id,
                            description=excluded.description,
                            significance=excluded.significance,
                            magical_properties=excluded.magical_properties,
                            history=excluded.history,
                            notes=excluded.notes,
                            canon_status=excluded.canon_status,
                            source_file=excluded.source_file,
                            updated_at=datetime('now')""",
                        (
                            artifact_id,
                            name, artifact_type, current_owner_id, current_location_id,
                            origin_era_id, description, significance, magical_properties,
                            history, notes, canon_status, source_file,
                        ),
                    )
                    await conn.commit()
                    row = await conn.execute_fetchall(
                        "SELECT * FROM artifacts WHERE id = ?", (artifact_id,)
                    )
            except Exception as exc:
                logger.error("upsert_artifact failed: %s", exc)
                return ValidationFailure(is_valid=False, errors=[str(exc)])

            return Artifact(**dict(row[0]))

    # ------------------------------------------------------------------
    # delete_artifact
    # ------------------------------------------------------------------

    @mcp.tool()
    async def delete_artifact(artifact_id: int) -> NotFoundResponse | ValidationFailure | dict:
        """Delete an artifact by ID, refusing if referenced records exist.

        FK-safe: artifacts are referenced by object_states (artifact_id NOT
        NULL FK) and by event_artifacts (artifact_id FK — junction table for
        events). If any FK constraint is violated, returns ValidationFailure
        with the error rather than raising.

        Args:
            artifact_id: Primary key of the artifact to delete.

        Returns:
            {"deleted": True, "id": artifact_id} on success, NotFoundResponse
            if the artifact does not exist, or ValidationFailure if FK
            constraints prevent deletion.
        """
        async with get_connection() as conn:
            row = await conn.execute_fetchall(
                "SELECT id FROM artifacts WHERE id = ?", (artifact_id,)
            )
            if not row:
                return NotFoundResponse(not_found_message=f"Artifact {artifact_id} not found")
            try:
                await conn.execute("DELETE FROM artifacts WHERE id = ?", (artifact_id,))
                await conn.commit()
                return {"deleted": True, "id": artifact_id}
            except Exception as exc:
                logger.error("delete_artifact failed: %s", exc)
                return ValidationFailure(is_valid=False, errors=[str(exc)])

    # ------------------------------------------------------------------
    # get_object_states
    # ------------------------------------------------------------------

    @mcp.tool()
    async def get_object_states(artifact_id: int) -> list[ObjectState]:
        """Return all state records for an artifact, ordered by chapter_id.

        Args:
            artifact_id: ID of the artifact whose state history to retrieve.

        Returns:
            List of ObjectState objects ordered by chapter_id. Returns an
            empty list if no states have been recorded for the artifact.
        """
        async with get_connection() as conn:
            rows = await conn.execute_fetchall(
                "SELECT * FROM object_states WHERE artifact_id = ? ORDER BY chapter_id",
                (artifact_id,),
            )
            return [ObjectState(**dict(row)) for row in rows]

    # ------------------------------------------------------------------
    # log_object_state
    # ------------------------------------------------------------------

    @mcp.tool()
    async def log_object_state(
        artifact_id: int,
        chapter_id: int,
        condition: str = "intact",
        owner_id: int | None = None,
        location_id: int | None = None,
        notes: str | None = None,
    ) -> ObjectState | NotFoundResponse | ValidationFailure:
        """Record the state of an artifact at a specific chapter.

        Follows the log_* pattern: pre-checks artifact_id and chapter_id FKs
        before inserting. The object_states table has a UNIQUE(artifact_id,
        chapter_id) constraint — only one state record per artifact per chapter.

        Args:
            artifact_id: ID of the artifact whose state to record (required).
            chapter_id: Chapter at which this state is recorded (required).
            condition: State of the artifact — e.g. "intact", "damaged", "destroyed"
                       (default: "intact").
            owner_id: FK to characters — current owner at this chapter (optional).
            location_id: FK to locations — current location at this chapter (optional).
            notes: Free-form notes about the object state (optional).

        Returns:
            The newly created ObjectState, NotFoundResponse if artifact_id or
            chapter_id do not exist, or ValidationFailure on DB error.
        """
        async with get_connection() as conn:
            artifact_row = await conn.execute_fetchall(
                "SELECT id FROM artifacts WHERE id = ?", (artifact_id,)
            )
            if not artifact_row:
                return NotFoundResponse(
                    not_found_message=f"Artifact {artifact_id} not found"
                )
            chapter_row = await conn.execute_fetchall(
                "SELECT id FROM chapters WHERE id = ?", (chapter_id,)
            )
            if not chapter_row:
                return NotFoundResponse(
                    not_found_message=f"Chapter {chapter_id} not found"
                )
            try:
                cursor = await conn.execute(
                    """INSERT INTO object_states (
                        artifact_id, chapter_id, owner_id, location_id, condition, notes
                    ) VALUES (?, ?, ?, ?, ?, ?)""",
                    (artifact_id, chapter_id, owner_id, location_id, condition, notes),
                )
                new_id = cursor.lastrowid
                await conn.commit()
                row = await conn.execute_fetchall(
                    "SELECT * FROM object_states WHERE id = ?", (new_id,)
                )
                return ObjectState(**dict(row[0]))
            except Exception as exc:
                logger.error("log_object_state failed: %s", exc)
                return ValidationFailure(is_valid=False, errors=[str(exc)])

    # ------------------------------------------------------------------
    # delete_object_state
    # ------------------------------------------------------------------

    @mcp.tool()
    async def delete_object_state(object_state_id: int) -> NotFoundResponse | dict:
        """Delete an object state entry by ID.

        Log-style delete: object_states is a leaf table with no FK children,
        so no try/except for FK violations is needed.

        Args:
            object_state_id: Primary key of the object state entry to delete.

        Returns:
            {"deleted": True, "id": object_state_id} on success, or
            NotFoundResponse if the entry does not exist.
        """
        async with get_connection() as conn:
            row = await conn.execute_fetchall(
                "SELECT id FROM object_states WHERE id = ?", (object_state_id,)
            )
            if not row:
                return NotFoundResponse(
                    not_found_message=f"Object state {object_state_id} not found"
                )
            await conn.execute(
                "DELETE FROM object_states WHERE id = ?", (object_state_id,)
            )
            await conn.commit()
            return {"deleted": True, "id": object_state_id}
