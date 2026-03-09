"""Relationship domain MCP tools.

All 6 relationship tools are registered via the register(mcp) function pattern.
This module is standalone — it does not modify server.py; wiring happens in
the server module (Plan 03).

Key complexity: relationship symmetry. The character_relationships table has
UNIQUE(character_a_id, character_b_id) with order-sensitive storage.
- get_relationship queries both orderings to find a row regardless of call order.
- upsert_relationship canonicalizes the pair so min(a, b) is always character_a_id,
  preventing duplicate rows for the same dyad.

IMPORTANT: Never use the print function in this module. All logging goes to
stderr via the logging module — using print corrupts the stdio protocol.
"""

import logging

from mcp.server.fastmcp import FastMCP

from novel.mcp.db import get_connection
from novel.models.relationships import (
    CharacterRelationship,
    PerceptionProfile,
    RelationshipChangeEvent,
)
from novel.models.shared import NotFoundResponse, ValidationFailure

logger = logging.getLogger(__name__)


def register(mcp: FastMCP) -> None:
    """Register all 9 relationship domain tools with the given FastMCP instance.

    Tools are defined as local async functions and decorated with @mcp.tool().
    The FastMCP instance is always the one passed in — never imported globally.

    Args:
        mcp: The FastMCP server instance to register tools against.
    """

    # ------------------------------------------------------------------
    # get_relationship
    # ------------------------------------------------------------------

    @mcp.tool()
    async def get_relationship(
        character_a_id: int,
        character_b_id: int,
    ) -> CharacterRelationship | NotFoundResponse:
        """Look up the relationship between two characters in either direction.

        The character_relationships table stores pairs in canonical order
        (min_id as character_a_id). This tool queries both orderings so the
        caller does not need to know the canonical order.

        Args:
            character_a_id: First character ID in the pair.
            character_b_id: Second character ID in the pair.

        Returns:
            CharacterRelationship if a row exists between the two characters,
            NotFoundResponse if no relationship record exists for this pair.
        """
        async with get_connection() as conn:
            rows = await conn.execute_fetchall(
                """SELECT * FROM character_relationships
                   WHERE (character_a_id = ? AND character_b_id = ?)
                      OR (character_a_id = ? AND character_b_id = ?)
                   LIMIT 1""",
                (character_a_id, character_b_id, character_b_id, character_a_id),
            )
            if not rows:
                logger.debug(
                    "No relationship between characters %d and %d",
                    character_a_id,
                    character_b_id,
                )
                return NotFoundResponse(
                    not_found_message=(
                        f"No relationship between characters "
                        f"{character_a_id} and {character_b_id}"
                    )
                )
            return CharacterRelationship(**dict(rows[0]))

    # ------------------------------------------------------------------
    # list_relationships
    # ------------------------------------------------------------------

    @mcp.tool()
    async def list_relationships(
        character_id: int,
    ) -> list[CharacterRelationship]:
        """Return all relationships where the given character appears as either party.

        Queries both character_a_id and character_b_id columns so the result
        includes relationships regardless of canonical storage order.

        Args:
            character_id: ID of the character whose relationships to retrieve.

        Returns:
            List of CharacterRelationship records ordered by updated_at descending.
            Returns an empty list (not NotFoundResponse) if the character has
            no relationships.
        """
        async with get_connection() as conn:
            rows = await conn.execute_fetchall(
                """SELECT * FROM character_relationships
                   WHERE character_a_id = ? OR character_b_id = ?
                   ORDER BY updated_at DESC""",
                (character_id, character_id),
            )
            return [CharacterRelationship(**dict(row)) for row in rows]

    # ------------------------------------------------------------------
    # upsert_relationship
    # ------------------------------------------------------------------

    @mcp.tool()
    async def upsert_relationship(
        character_a_id: int,
        character_b_id: int,
        relationship_type: str = "acquaintance",
        bond_strength: int = 0,
        trust_level: int = 0,
        current_status: str = "neutral",
        history_summary: str | None = None,
        first_meeting_chapter_id: int | None = None,
        notes: str | None = None,
        canon_status: str = "draft",
    ) -> CharacterRelationship | ValidationFailure:
        """Create or update the relationship between two characters.

        The pair is canonicalized before storage: min(a, b) is always stored
        as character_a_id to ensure exactly one row per dyad regardless of
        call argument order.

        When a row already exists (conflict on UNIQUE(character_a_id, character_b_id)),
        all mutable fields are updated in place.

        Args:
            character_a_id: First character ID (will be canonicalized).
            character_b_id: Second character ID (will be canonicalized).
            relationship_type: Type label — e.g. "ally", "rival", "enemy".
            bond_strength: Numeric bond intensity (positive = strong bond).
            trust_level: Numeric trust score (positive = high trust).
            current_status: Relationship status — e.g. "neutral", "active", "hostile".
            history_summary: Free-text summary of relationship history (optional).
            first_meeting_chapter_id: FK to chapters where they first met (optional).
            notes: Free-form notes (optional).
            canon_status: Approval status — "draft" or "approved".

        Returns:
            The created or updated CharacterRelationship, or ValidationFailure on
            DB error.
        """
        # Canonicalize: always store lower ID as character_a_id
        a, b = min(character_a_id, character_b_id), max(character_a_id, character_b_id)

        async with get_connection() as conn:
            try:
                await conn.execute(
                    """INSERT INTO character_relationships (
                        character_a_id, character_b_id, relationship_type,
                        bond_strength, trust_level, current_status,
                        history_summary, first_meeting_chapter_id, notes,
                        canon_status, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                    ON CONFLICT(character_a_id, character_b_id) DO UPDATE SET
                        relationship_type=excluded.relationship_type,
                        bond_strength=excluded.bond_strength,
                        trust_level=excluded.trust_level,
                        current_status=excluded.current_status,
                        history_summary=excluded.history_summary,
                        first_meeting_chapter_id=excluded.first_meeting_chapter_id,
                        notes=excluded.notes,
                        canon_status=excluded.canon_status,
                        updated_at=datetime('now')""",
                    (
                        a, b, relationship_type,
                        bond_strength, trust_level, current_status,
                        history_summary, first_meeting_chapter_id, notes,
                        canon_status,
                    ),
                )
                await conn.commit()
                rows = await conn.execute_fetchall(
                    "SELECT * FROM character_relationships WHERE character_a_id = ? AND character_b_id = ?",
                    (a, b),
                )
                return CharacterRelationship(**dict(rows[0]))
            except Exception as exc:
                logger.error("upsert_relationship failed: %s", exc)
                return ValidationFailure(is_valid=False, errors=[str(exc)])

    # ------------------------------------------------------------------
    # get_perception_profile
    # ------------------------------------------------------------------

    @mcp.tool()
    async def get_perception_profile(
        observer_id: int,
        subject_id: int,
    ) -> PerceptionProfile | NotFoundResponse:
        """Return the perception profile one character holds of another.

        Perception profiles are directional: observer → subject is stored as a
        separate row from subject → observer.

        Args:
            observer_id: ID of the character whose perception is recorded.
            subject_id: ID of the character being perceived.

        Returns:
            PerceptionProfile if a row exists for this (observer, subject) pair,
            NotFoundResponse if no profile has been recorded.
        """
        async with get_connection() as conn:
            rows = await conn.execute_fetchall(
                "SELECT * FROM perception_profiles WHERE observer_id = ? AND subject_id = ?",
                (observer_id, subject_id),
            )
            if not rows:
                logger.debug(
                    "No perception profile for observer=%d subject=%d",
                    observer_id,
                    subject_id,
                )
                return NotFoundResponse(
                    not_found_message=(
                        f"No perception profile for observer={observer_id} subject={subject_id}"
                    )
                )
            return PerceptionProfile(**dict(rows[0]))

    # ------------------------------------------------------------------
    # upsert_perception_profile
    # ------------------------------------------------------------------

    @mcp.tool()
    async def upsert_perception_profile(
        observer_id: int,
        subject_id: int,
        chapter_id: int | None = None,
        perceived_traits: str | None = None,
        trust_level: int = 0,
        emotional_valence: str = "neutral",
        misperceptions: str | None = None,
        notes: str | None = None,
    ) -> PerceptionProfile | ValidationFailure:
        """Create or update the perception profile for an (observer, subject) pair.

        Uses ON CONFLICT(observer_id, subject_id) DO UPDATE so calling this
        a second time for the same pair updates rather than duplicates.

        Args:
            observer_id: ID of the observing character.
            subject_id: ID of the subject character being perceived.
            chapter_id: Chapter at which this perception snapshot applies (optional).
            perceived_traits: Free-text description of perceived personality traits (optional).
            trust_level: Observer's trust rating of the subject.
            emotional_valence: Observer's emotional orientation — e.g. "neutral", "trusting", "wary".
            misperceptions: Known misperceptions the observer holds (optional).
            notes: Free-form notes (optional).

        Returns:
            The created or updated PerceptionProfile, or ValidationFailure on
            DB error.
        """
        async with get_connection() as conn:
            try:
                await conn.execute(
                    """INSERT INTO perception_profiles (
                        observer_id, subject_id, chapter_id, perceived_traits,
                        trust_level, emotional_valence, misperceptions, notes, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                    ON CONFLICT(observer_id, subject_id) DO UPDATE SET
                        chapter_id=excluded.chapter_id,
                        perceived_traits=excluded.perceived_traits,
                        trust_level=excluded.trust_level,
                        emotional_valence=excluded.emotional_valence,
                        misperceptions=excluded.misperceptions,
                        notes=excluded.notes,
                        updated_at=datetime('now')""",
                    (
                        observer_id, subject_id, chapter_id, perceived_traits,
                        trust_level, emotional_valence, misperceptions, notes,
                    ),
                )
                await conn.commit()
                rows = await conn.execute_fetchall(
                    "SELECT * FROM perception_profiles WHERE observer_id = ? AND subject_id = ?",
                    (observer_id, subject_id),
                )
                return PerceptionProfile(**dict(rows[0]))
            except Exception as exc:
                logger.error("upsert_perception_profile failed: %s", exc)
                return ValidationFailure(is_valid=False, errors=[str(exc)])

    # ------------------------------------------------------------------
    # log_relationship_change
    # ------------------------------------------------------------------

    @mcp.tool()
    async def log_relationship_change(
        relationship_id: int,
        chapter_id: int | None = None,
        event_id: int | None = None,
        change_type: str = "shift",
        description: str = "",
        bond_delta: int = 0,
        trust_delta: int = 0,
    ) -> RelationshipChangeEvent | NotFoundResponse | ValidationFailure:
        """Record a change event for an existing relationship.

        First verifies the relationship exists. If it does, inserts a
        relationship_change_events row and returns the newly created record.

        Args:
            relationship_id: FK to character_relationships.id — must exist.
            chapter_id: Chapter at which this change occurred (optional).
            event_id: FK to story events table (optional).
            change_type: Nature of the change — e.g. "shift", "breakthrough", "rupture".
            description: Human-readable description of what changed.
            bond_delta: Change in bond strength (positive = stronger bond).
            trust_delta: Change in trust level (positive = more trust).

        Returns:
            The newly created RelationshipChangeEvent with its assigned id, or
            NotFoundResponse if relationship_id does not exist, or
            ValidationFailure on DB error.
        """
        async with get_connection() as conn:
            exists = await conn.execute_fetchall(
                "SELECT id FROM character_relationships WHERE id = ?",
                (relationship_id,),
            )
            if not exists:
                logger.debug("Relationship %d not found for change event", relationship_id)
                return NotFoundResponse(
                    not_found_message=f"Relationship {relationship_id} not found"
                )

            try:
                cursor = await conn.execute(
                    """INSERT INTO relationship_change_events (
                        relationship_id, chapter_id, event_id, change_type,
                        description, bond_delta, trust_delta, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))""",
                    (
                        relationship_id, chapter_id, event_id, change_type,
                        description, bond_delta, trust_delta,
                    ),
                )
                await conn.commit()
                new_id = cursor.lastrowid
                rows = await conn.execute_fetchall(
                    "SELECT * FROM relationship_change_events WHERE id = ?",
                    (new_id,),
                )
                return RelationshipChangeEvent(**dict(rows[0]))
            except Exception as exc:
                logger.error("log_relationship_change failed: %s", exc)
                return ValidationFailure(is_valid=False, errors=[str(exc)])

    # ------------------------------------------------------------------
    # delete_relationship
    # ------------------------------------------------------------------

    @mcp.tool()
    async def delete_relationship(
        relationship_id: int,
    ) -> NotFoundResponse | ValidationFailure | dict:
        """Delete a character relationship by ID.

        Idempotent: returns NotFoundResponse if the relationship does not exist.
        Refuses with ValidationFailure if dependent records (e.g.
        relationship_change_events) reference this relationship.

        Args:
            relationship_id: Primary key of the character_relationships row.

        Returns:
            {"deleted": True, "id": relationship_id} on success.
            NotFoundResponse if not found.
            ValidationFailure if FK constraint blocks deletion.
        """
        async with get_connection() as conn:
            row = await conn.execute_fetchall(
                "SELECT id FROM character_relationships WHERE id = ?",
                (relationship_id,),
            )
            if not row:
                return NotFoundResponse(
                    not_found_message=f"Relationship {relationship_id} not found"
                )
            try:
                await conn.execute(
                    "DELETE FROM character_relationships WHERE id = ?",
                    (relationship_id,),
                )
                await conn.commit()
                return {"deleted": True, "id": relationship_id}
            except Exception as exc:
                logger.error("delete_relationship failed: %s", exc)
                return ValidationFailure(is_valid=False, errors=[str(exc)])

    # ------------------------------------------------------------------
    # delete_relationship_change
    # ------------------------------------------------------------------

    @mcp.tool()
    async def delete_relationship_change(
        relationship_change_event_id: int,
    ) -> NotFoundResponse | dict:
        """Delete a relationship change event by ID.

        Idempotent: returns NotFoundResponse if the record does not exist.
        relationship_change_events is a log table with no FK children, so no
        FK constraint check is needed.

        Args:
            relationship_change_event_id: Primary key of the
                relationship_change_events row.

        Returns:
            {"deleted": True, "id": relationship_change_event_id} on success.
            NotFoundResponse if not found.
        """
        async with get_connection() as conn:
            row = await conn.execute_fetchall(
                "SELECT id FROM relationship_change_events WHERE id = ?",
                (relationship_change_event_id,),
            )
            if not row:
                return NotFoundResponse(
                    not_found_message=(
                        f"Relationship change event {relationship_change_event_id} not found"
                    )
                )
            await conn.execute(
                "DELETE FROM relationship_change_events WHERE id = ?",
                (relationship_change_event_id,),
            )
            await conn.commit()
            return {"deleted": True, "id": relationship_change_event_id}

    # ------------------------------------------------------------------
    # delete_perception_profile
    # ------------------------------------------------------------------

    @mcp.tool()
    async def delete_perception_profile(
        perception_profile_id: int,
    ) -> NotFoundResponse | ValidationFailure | dict:
        """Delete a perception profile by ID.

        Idempotent: returns NotFoundResponse if the record does not exist.
        Uses FK-safe pattern (ValidationFailure on exception) for consistency
        with the safety-first delete approach, even if no known FK children.

        Args:
            perception_profile_id: Primary key of the perception_profiles row.

        Returns:
            {"deleted": True, "id": perception_profile_id} on success.
            NotFoundResponse if not found.
            ValidationFailure if FK constraint blocks deletion.
        """
        async with get_connection() as conn:
            row = await conn.execute_fetchall(
                "SELECT id FROM perception_profiles WHERE id = ?",
                (perception_profile_id,),
            )
            if not row:
                return NotFoundResponse(
                    not_found_message=f"Perception profile {perception_profile_id} not found"
                )
            try:
                await conn.execute(
                    "DELETE FROM perception_profiles WHERE id = ?",
                    (perception_profile_id,),
                )
                await conn.commit()
                return {"deleted": True, "id": perception_profile_id}
            except Exception as exc:
                logger.error("delete_perception_profile failed: %s", exc)
                return ValidationFailure(is_valid=False, errors=[str(exc)])
