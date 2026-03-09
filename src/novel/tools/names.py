"""Names domain MCP tools.

All 6 name tools are registered via the register(mcp) function pattern.
This module is gate-free: name tools must work during worldbuilding (before
gate certification). Do NOT add check_gate() to this module.

IMPORTANT: Never use the print function in this module. All logging goes to
stderr via the logging module — using print corrupts the stdio protocol.
"""
import logging

import aiosqlite
from pydantic import BaseModel

from mcp.server.fastmcp import FastMCP

from novel.mcp.db import get_connection
from novel.models.magic import NameRegistryEntry
from novel.models.shared import NotFoundResponse, ValidationFailure

logger = logging.getLogger(__name__)


class NameSuggestionsResult(BaseModel):
    """Result for generate_name_suggestions — combines registry rows and cultural context."""

    existing_names: list[NameRegistryEntry]
    linguistic_context: str | None
    culture_id: int


def register(mcp: FastMCP) -> None:
    """Register all 6 name domain tools with the given FastMCP instance.

    Tools are defined as local async functions and decorated with @mcp.tool().
    The FastMCP instance is always the one passed in — never imported globally.

    These tools are gate-free: name conflict checking and registration are
    worldbuilding operations that must work before the gate is certified.
    Do NOT add check_gate() calls to any tool in this module.

    Args:
        mcp: The FastMCP server instance to register tools against.
    """

    # ------------------------------------------------------------------
    # check_name (NAME-01)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def check_name(name: str) -> NameRegistryEntry | NotFoundResponse:
        """Check if a name is already registered (case-insensitive exact match).

        Use this before register_name to avoid UNIQUE constraint conflicts.
        Returns the existing NameRegistryEntry if the name is taken, or a
        NotFoundResponse indicating the name is safe to use.

        Args:
            name: The name to look up (case-insensitive exact match).

        Returns:
            NameRegistryEntry if the name exists in the registry.
            NotFoundResponse with 'safe to use' message if not found.
        """
        async with get_connection() as conn:
            async with conn.execute(
                "SELECT * FROM name_registry WHERE LOWER(name) = LOWER(?)",
                (name,),
            ) as cursor:
                row = await cursor.fetchone()

            if row is not None:
                return NameRegistryEntry(**dict(row))

            return NotFoundResponse(
                not_found_message=f"Name '{name}' is not in the registry — safe to use"
            )

    # ------------------------------------------------------------------
    # register_name (NAME-02)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def register_name(
        name: str,
        entity_type: str = "character",
        culture_id: int | None = None,
        linguistic_notes: str | None = None,
        introduced_chapter_id: int | None = None,
        notes: str | None = None,
    ) -> NameRegistryEntry | ValidationFailure:
        """Register a new name in the name registry.

        Inserts a new row into name_registry. Returns the created NameRegistryEntry
        on success. Returns ValidationFailure if the name already exists (the
        name_registry.name column has a UNIQUE constraint).

        Use check_name first to verify the name is available before registering.

        Args:
            name: The name to register (must be unique in the registry).
            entity_type: Category of entity (default 'character').
            culture_id: FK to cultures table (optional).
            linguistic_notes: Notes on name etymology or pronunciation (optional).
            introduced_chapter_id: FK to chapters table where name first appears (optional).
            notes: Additional notes (optional).

        Returns:
            NameRegistryEntry with id set on success.
            ValidationFailure with is_valid=False if the name already exists.
        """
        async with get_connection() as conn:
            try:
                cursor = await conn.execute(
                    """
                    INSERT INTO name_registry
                        (name, entity_type, culture_id, linguistic_notes,
                         introduced_chapter_id, notes)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        name,
                        entity_type,
                        culture_id,
                        linguistic_notes,
                        introduced_chapter_id,
                        notes,
                    ),
                )
            except aiosqlite.IntegrityError:
                return ValidationFailure(
                    is_valid=False,
                    errors=[
                        f"Name '{name}' already exists in the registry. "
                        "Use check_name to verify before registering."
                    ],
                )

            new_id = cursor.lastrowid
            await conn.commit()

            async with conn.execute(
                "SELECT * FROM name_registry WHERE id = ?", (new_id,)
            ) as cur:
                row = await cur.fetchone()

            return NameRegistryEntry(**dict(row))

    # ------------------------------------------------------------------
    # get_name_registry (NAME-03)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def get_name_registry(
        entity_type: str | None = None,
        culture_id: int | None = None,
    ) -> list[NameRegistryEntry]:
        """Retrieve all name registry entries, with optional filters.

        Returns every NameRegistryEntry ordered alphabetically by name ASC.
        Both filters are optional and can be combined.

        Args:
            entity_type: Filter by entity category (e.g. 'character', 'location').
            culture_id: Filter by culture FK.

        Returns:
            List of NameRegistryEntry records ordered by name ASC (may be empty).
        """
        async with get_connection() as conn:
            conditions: list[str] = []
            params: list[object] = []

            if entity_type is not None:
                conditions.append("entity_type = ?")
                params.append(entity_type)
            if culture_id is not None:
                conditions.append("culture_id = ?")
                params.append(culture_id)

            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
            sql = f"SELECT * FROM name_registry {where_clause} ORDER BY name ASC"

            async with conn.execute(sql, params) as cursor:
                rows = await cursor.fetchall()

            return [NameRegistryEntry(**dict(row)) for row in rows]

    # ------------------------------------------------------------------
    # generate_name_suggestions (NAME-04)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def generate_name_suggestions(culture_id: int) -> NameSuggestionsResult:
        """Retrieve name data for a culture to support consistent name generation.

        Returns existing names registered for the given culture plus the culture's
        naming conventions (linguistic context). Claude uses this data to generate
        new names that fit established cultural patterns.

        Two separate SELECT queries are used:
        1. name_registry WHERE culture_id = ? — existing names for the culture
        2. cultures.naming_conventions WHERE id = ? — linguistic context

        If no names are registered for the culture, existing_names is [].
        If the culture does not exist, linguistic_context is None.
        Neither case is an error.

        Args:
            culture_id: FK to cultures table — the culture to fetch data for.

        Returns:
            NameSuggestionsResult with existing_names list, linguistic_context string
            (or None), and the queried culture_id.
        """
        async with get_connection() as conn:
            # Query 1: existing name registry entries for this culture
            async with conn.execute(
                "SELECT * FROM name_registry WHERE culture_id = ? ORDER BY name ASC",
                (culture_id,),
            ) as cursor:
                name_rows = await cursor.fetchall()

            # Query 2: culture's naming conventions for linguistic context
            async with conn.execute(
                "SELECT naming_conventions FROM cultures WHERE id = ?",
                (culture_id,),
            ) as cursor:
                culture_row = await cursor.fetchone()

            existing_names = [NameRegistryEntry(**dict(r)) for r in name_rows]
            linguistic_context = (
                culture_row["naming_conventions"] if culture_row is not None else None
            )

            return NameSuggestionsResult(
                existing_names=existing_names,
                linguistic_context=linguistic_context,
                culture_id=culture_id,
            )

    # ------------------------------------------------------------------
    # upsert_name_registry_entry
    # ------------------------------------------------------------------

    @mcp.tool()
    async def upsert_name_registry_entry(
        entry_id: int | None,
        name: str,
        entity_type: str = "character",
        culture_id: int | None = None,
        linguistic_notes: str | None = None,
        introduced_chapter_id: int | None = None,
        notes: str | None = None,
    ) -> NameRegistryEntry | ValidationFailure:
        """Create or update a name registry entry.

        Two-branch upsert on entry_id:
        - entry_id=None: INSERT creates a new name_registry row.
        - entry_id=N: INSERT ... ON CONFLICT(id) DO UPDATE updates the
          existing row.

        After either branch, the row is SELECT-ed back by id and returned.
        Not gate-gated: name registry is worldbuilding data that must be
        writable before gate certification.

        Note: name_registry has a UNIQUE(name) constraint. If creating with
        entry_id=None and the name already exists, returns ValidationFailure.
        Use check_name first to verify name availability.

        Args:
            entry_id: Existing entry ID for update branch (None to create).
            name: The name to register (must be unique in the registry).
            entity_type: Category of entity (default 'character').
            culture_id: FK to cultures table (optional).
            linguistic_notes: Notes on name etymology or pronunciation (optional).
            introduced_chapter_id: FK to chapters table where name first appears
                                   (optional).
            notes: Additional notes (optional).

        Returns:
            The created or updated NameRegistryEntry record.
            ValidationFailure on DB error (e.g. UNIQUE constraint violation).
        """
        async with get_connection() as conn:
            try:
                if entry_id is None:
                    cursor = await conn.execute(
                        """INSERT INTO name_registry
                            (name, entity_type, culture_id, linguistic_notes,
                             introduced_chapter_id, notes)
                           VALUES (?, ?, ?, ?, ?, ?)""",
                        (
                            name,
                            entity_type,
                            culture_id,
                            linguistic_notes,
                            introduced_chapter_id,
                            notes,
                        ),
                    )
                    new_id = cursor.lastrowid
                    await conn.commit()
                    async with conn.execute(
                        "SELECT * FROM name_registry WHERE id = ?", (new_id,)
                    ) as cur:
                        row = await cur.fetchone()
                else:
                    await conn.execute(
                        """INSERT INTO name_registry
                            (id, name, entity_type, culture_id, linguistic_notes,
                             introduced_chapter_id, notes)
                           VALUES (?, ?, ?, ?, ?, ?, ?)
                           ON CONFLICT(id) DO UPDATE SET
                               name=excluded.name,
                               entity_type=excluded.entity_type,
                               culture_id=excluded.culture_id,
                               linguistic_notes=excluded.linguistic_notes,
                               introduced_chapter_id=excluded.introduced_chapter_id,
                               notes=excluded.notes""",
                        (
                            entry_id,
                            name,
                            entity_type,
                            culture_id,
                            linguistic_notes,
                            introduced_chapter_id,
                            notes,
                        ),
                    )
                    await conn.commit()
                    async with conn.execute(
                        "SELECT * FROM name_registry WHERE id = ?", (entry_id,)
                    ) as cur:
                        row = await cur.fetchone()
                return NameRegistryEntry(**dict(row))
            except Exception as exc:
                logger.error("upsert_name_registry_entry failed: %s", exc)
                return ValidationFailure(is_valid=False, errors=[str(exc)])

    # ------------------------------------------------------------------
    # delete_name_registry_entry
    # ------------------------------------------------------------------

    @mcp.tool()
    async def delete_name_registry_entry(
        name_registry_id: int,
    ) -> NotFoundResponse | ValidationFailure | dict:
        """Delete a name registry entry by its integer primary key.

        FK-safe: name_registry entries may be referenced by other tables
        (e.g. characters via introduced_chapter_id FK path). If any FK
        constraint is violated, returns ValidationFailure with the error
        rather than raising.

        Note: The parameter uses the integer primary key (id), not the name
        string, to allow unambiguous deletion.

        Args:
            name_registry_id: Primary key (id) of the name registry entry to delete.

        Returns:
            {"deleted": True, "id": name_registry_id} on success, NotFoundResponse
            if the entry does not exist, or ValidationFailure if FK constraints
            prevent deletion.
        """
        async with get_connection() as conn:
            row = await conn.execute_fetchall(
                "SELECT id FROM name_registry WHERE id = ?", (name_registry_id,)
            )
            if not row:
                return NotFoundResponse(
                    not_found_message=f"Name registry entry {name_registry_id} not found"
                )
            try:
                await conn.execute(
                    "DELETE FROM name_registry WHERE id = ?", (name_registry_id,)
                )
                await conn.commit()
                return {"deleted": True, "id": name_registry_id}
            except Exception as exc:
                logger.error("delete_name_registry_entry failed: %s", exc)
                return ValidationFailure(is_valid=False, errors=[str(exc)])
