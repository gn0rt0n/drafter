"""World domain MCP tools.

All 6 world tools are registered via the register(mcp) function pattern.
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
    Culture,
    Faction,
    FactionPoliticalState,
    Location,
)
from novel.models.shared import NotFoundResponse, ValidationFailure

logger = logging.getLogger(__name__)


def register(mcp: FastMCP) -> None:
    """Register all 6 world domain tools with the given FastMCP instance.

    Tools are defined as local async functions and decorated with @mcp.tool().
    The FastMCP instance is always the one passed in — never imported globally.

    Args:
        mcp: The FastMCP server instance to register tools against.
    """

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
