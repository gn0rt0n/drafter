"""Magic domain MCP tools.

All 14 magic tools are registered via the register(mcp) function pattern.
This module is standalone — it does not modify server.py; wiring happens in
the server module.

IMPORTANT: Never use the print function in this module. All logging goes to
stderr via the logging module — using print corrupts the stdio protocol.
"""

import logging

from mcp.server.fastmcp import FastMCP

from novel.mcp.db import get_connection
from novel.models.magic import (
    MagicComplianceResult,
    MagicSystemElement,
    MagicUseLog,
    PractitionerAbility,
    SupernaturalElement,
)
from novel.models.shared import NotFoundResponse, ValidationFailure

logger = logging.getLogger(__name__)


def register(mcp: FastMCP) -> None:
    """Register all 14 magic domain tools with the given FastMCP instance.

    Tools are defined as local async functions and decorated with @mcp.tool().
    The FastMCP instance is always the one passed in — never imported globally.

    Args:
        mcp: The FastMCP server instance to register tools against.
    """

    # ------------------------------------------------------------------
    # get_magic_element (WRLD-05)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def get_magic_element(
        magic_element_id: int,
    ) -> MagicSystemElement | NotFoundResponse:
        """Look up a single magic system element by ID, returning all fields.

        Returns the full element record including rules, limitations, costs,
        exceptions, and notes.

        Args:
            magic_element_id: Primary key of the magic element to retrieve.

        Returns:
            MagicSystemElement with all fields populated, or NotFoundResponse
            if the element does not exist.
        """
        async with get_connection() as conn:
            rows = await conn.execute_fetchall(
                "SELECT * FROM magic_system_elements WHERE id = ?",
                (magic_element_id,),
            )
            if not rows:
                logger.debug("Magic element %d not found", magic_element_id)
                return NotFoundResponse(
                    not_found_message=f"Magic element {magic_element_id} not found"
                )
            return MagicSystemElement(**dict(rows[0]))

    # ------------------------------------------------------------------
    # get_practitioner_abilities (WRLD-06)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def get_practitioner_abilities(
        character_id: int,
    ) -> list[PractitionerAbility] | NotFoundResponse:
        """Return all registered magic abilities for a character.

        First verifies the character exists, then returns all practitioner
        ability rows ordered by ID. An empty list is a valid response for
        characters that exist but have no registered abilities.

        Args:
            character_id: Primary key of the character whose abilities to retrieve.

        Returns:
            List of PractitionerAbility records (may be empty), or
            NotFoundResponse if the character does not exist.
        """
        async with get_connection() as conn:
            char_rows = await conn.execute_fetchall(
                "SELECT id FROM characters WHERE id = ?",
                (character_id,),
            )
            if not char_rows:
                logger.debug("Character %d not found", character_id)
                return NotFoundResponse(
                    not_found_message=f"Character {character_id} not found"
                )
            rows = await conn.execute_fetchall(
                "SELECT * FROM practitioner_abilities WHERE character_id = ? ORDER BY id",
                (character_id,),
            )
            return [PractitionerAbility(**dict(row)) for row in rows]

    # ------------------------------------------------------------------
    # log_magic_use (WRLD-07)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def log_magic_use(
        chapter_id: int,
        character_id: int,
        action_description: str,
        magic_element_id: int | None = None,
        scene_id: int | None = None,
        cost_paid: str | None = None,
        compliance_status: str = "compliant",
        notes: str | None = None,
    ) -> MagicUseLog | NotFoundResponse | ValidationFailure:
        """Append a magic use event to the immutable magic use log.

        This is an append-only operation — magic_use_log has no UNIQUE
        constraint, so each call always inserts a new row. The chapter must
        exist before logging a magic use against it.

        Args:
            chapter_id: FK to chapters table — chapter where magic was used (required).
            character_id: FK to characters table — character who performed magic (required).
            action_description: Free-text description of the magic action (required).
            magic_element_id: FK to magic_system_elements table (optional).
            scene_id: FK to scenes table (optional).
            cost_paid: Description of the cost the character paid (optional).
            compliance_status: Compliance status — "compliant", "non_compliant", or
                               "unchecked" (default: "compliant").
            notes: Free-form notes about this magic use event (optional).

        Returns:
            The newly created MagicUseLog row, NotFoundResponse if chapter does
            not exist, or ValidationFailure on DB error.
        """
        async with get_connection() as conn:
            try:
                chapter_rows = await conn.execute_fetchall(
                    "SELECT id FROM chapters WHERE id = ?",
                    (chapter_id,),
                )
                if not chapter_rows:
                    logger.debug("Chapter %d not found for log_magic_use", chapter_id)
                    return NotFoundResponse(
                        not_found_message=f"Chapter {chapter_id} not found"
                    )
                cursor = await conn.execute(
                    """INSERT INTO magic_use_log
                        (chapter_id, scene_id, character_id, magic_element_id,
                         action_description, cost_paid, compliance_status, notes, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))""",
                    (
                        chapter_id,
                        scene_id,
                        character_id,
                        magic_element_id,
                        action_description,
                        cost_paid,
                        compliance_status,
                        notes,
                    ),
                )
                new_id = cursor.lastrowid
                await conn.commit()
                row = await conn.execute_fetchall(
                    "SELECT * FROM magic_use_log WHERE id = ?",
                    (new_id,),
                )
                return MagicUseLog(**dict(row[0]))
            except Exception as exc:
                logger.error("log_magic_use failed: %s", exc)
                return ValidationFailure(is_valid=False, errors=[str(exc)])

    # ------------------------------------------------------------------
    # check_magic_compliance (WRLD-08)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def check_magic_compliance(
        character_id: int,
        magic_element_id: int,
        action_description: str,
    ) -> MagicComplianceResult | NotFoundResponse:
        """Check whether a character's proposed magic action complies with system rules.

        READ-ONLY tool — does not write to magic_use_log. Use log_magic_use
        separately to record the event after compliance is verified.

        Logic:
        1. Retrieve the magic element — return NotFoundResponse if missing.
        2. Check practitioner_abilities for character + element pair.
        3. Build violations list (currently: ability registration check only).
        4. compliant = no violations AND character has ability.

        Args:
            character_id: ID of the character performing the magic action.
            magic_element_id: ID of the magic element being invoked.
            action_description: Free-text description of the proposed action
                                 (for context; not used in compliance logic).

        Returns:
            MagicComplianceResult with compliant flag, violations, applicable
            rules, and character_has_ability status; or NotFoundResponse if the
            magic element does not exist.
        """
        async with get_connection() as conn:
            element_rows = await conn.execute_fetchall(
                "SELECT * FROM magic_system_elements WHERE id = ?",
                (magic_element_id,),
            )
            if not element_rows:
                logger.debug("Magic element %d not found for compliance check", magic_element_id)
                return NotFoundResponse(
                    not_found_message=f"Magic element {magic_element_id} not found"
                )
            element = dict(element_rows[0])

            ability_rows = await conn.execute_fetchall(
                "SELECT * FROM practitioner_abilities "
                "WHERE character_id = ? AND magic_element_id = ?",
                (character_id, magic_element_id),
            )
            character_has_ability: bool = bool(ability_rows)

            applicable_rules: list[str] = [
                v
                for v in [
                    element.get("rules"),
                    element.get("limitations"),
                    element.get("costs"),
                ]
                if v
            ]

            violations: list[str] = []
            if not character_has_ability:
                violations.append(
                    f"Character {character_id} has no registered ability for element {magic_element_id}"
                )

            compliant: bool = len(violations) == 0 and character_has_ability

            return MagicComplianceResult(
                compliant=compliant,
                violations=violations,
                applicable_rules=applicable_rules,
                character_has_ability=character_has_ability,
            )

    # ------------------------------------------------------------------
    # upsert_magic_element
    # ------------------------------------------------------------------

    @mcp.tool()
    async def upsert_magic_element(
        element_id: int | None,
        name: str,
        element_type: str,
        rules: str | None = None,
        limitations: str | None = None,
        costs: str | None = None,
        exceptions: str | None = None,
        introduced_chapter_id: int | None = None,
        notes: str | None = None,
        canon_status: str = "draft",
    ) -> MagicSystemElement | ValidationFailure:
        """Create or update a magic system element.

        Two-branch upsert on element_id:
        - element_id=None: INSERT creates a new magic_system_elements row.
        - element_id=N: INSERT ... ON CONFLICT(id) DO UPDATE updates the
          existing row.

        After either branch, the row is SELECT-ed back by id and returned.
        Not gate-gated: magic elements are worldbuilding data that must be
        writable before gate certification.

        Args:
            element_id: Existing element ID for update branch (None to create).
            name: Name of the magic element (required).
            element_type: Category of element, e.g. 'ability', 'spell', 'rule'
                          (required, default 'ability').
            rules: Rules governing this element (optional).
            limitations: Limitations of this element (optional).
            costs: Costs associated with using this element (optional).
            exceptions: Known exceptions to the rules (optional).
            introduced_chapter_id: FK to chapters table — chapter where element
                                    first appears (optional).
            notes: Additional notes (optional).
            canon_status: Canon status of the element (default 'draft').

        Returns:
            The created or updated MagicSystemElement record.
            ValidationFailure on DB error.
        """
        async with get_connection() as conn:
            try:
                if element_id is None:
                    cursor = await conn.execute(
                        """INSERT INTO magic_system_elements
                            (name, element_type, rules, limitations, costs,
                             exceptions, introduced_chapter_id, notes, canon_status)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            name,
                            element_type,
                            rules,
                            limitations,
                            costs,
                            exceptions,
                            introduced_chapter_id,
                            notes,
                            canon_status,
                        ),
                    )
                    new_id = cursor.lastrowid
                    await conn.commit()
                    row = await conn.execute_fetchall(
                        "SELECT * FROM magic_system_elements WHERE id = ?", (new_id,)
                    )
                else:
                    await conn.execute(
                        """INSERT INTO magic_system_elements
                            (id, name, element_type, rules, limitations, costs,
                             exceptions, introduced_chapter_id, notes, canon_status)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                           ON CONFLICT(id) DO UPDATE SET
                               name=excluded.name,
                               element_type=excluded.element_type,
                               rules=excluded.rules,
                               limitations=excluded.limitations,
                               costs=excluded.costs,
                               exceptions=excluded.exceptions,
                               introduced_chapter_id=excluded.introduced_chapter_id,
                               notes=excluded.notes,
                               canon_status=excluded.canon_status,
                               updated_at=datetime('now')""",
                        (
                            element_id,
                            name,
                            element_type,
                            rules,
                            limitations,
                            costs,
                            exceptions,
                            introduced_chapter_id,
                            notes,
                            canon_status,
                        ),
                    )
                    await conn.commit()
                    row = await conn.execute_fetchall(
                        "SELECT * FROM magic_system_elements WHERE id = ?", (element_id,)
                    )
                return MagicSystemElement(**dict(row[0]))
            except Exception as exc:
                logger.error("upsert_magic_element failed: %s", exc)
                return ValidationFailure(is_valid=False, errors=[str(exc)])

    # ------------------------------------------------------------------
    # list_magic_elements
    # ------------------------------------------------------------------

    @mcp.tool()
    async def list_magic_elements() -> list[MagicSystemElement]:
        """Return all magic system elements ordered by name.

        Returns every row from magic_system_elements ordered alphabetically
        by name ASC. An empty list is valid when no elements have been
        created yet.

        Returns:
            List of MagicSystemElement records ordered by name ASC
            (may be empty).
        """
        async with get_connection() as conn:
            rows = await conn.execute_fetchall(
                "SELECT * FROM magic_system_elements ORDER BY name ASC"
            )
            return [MagicSystemElement(**dict(row)) for row in rows]

    # ------------------------------------------------------------------
    # upsert_practitioner_ability
    # ------------------------------------------------------------------

    @mcp.tool()
    async def upsert_practitioner_ability(
        ability_id: int | None,
        character_id: int,
        magic_element_id: int,
        proficiency_level: int = 1,
        acquired_chapter_id: int | None = None,
        notes: str | None = None,
    ) -> PractitionerAbility | NotFoundResponse | ValidationFailure:
        """Create or update a practitioner ability for a character.

        Two-branch upsert on ability_id. Pre-checks that both character_id and
        magic_element_id exist before attempting the upsert.

        The practitioner_abilities table has a UNIQUE(character_id,
        magic_element_id) constraint — use the update branch (ability_id=N)
        when modifying an existing character/element pair to avoid conflicts.

        Not gate-gated: practitioner abilities are worldbuilding data.

        Args:
            ability_id: Existing ability ID for update branch (None to create).
            character_id: FK to characters table — character who has the ability.
            magic_element_id: FK to magic_system_elements table — element the
                              character can use.
            proficiency_level: Proficiency level 1–10 (default 1).
            acquired_chapter_id: FK to chapters — chapter where ability was
                                  acquired (optional).
            notes: Additional notes (optional).

        Returns:
            The created or updated PractitionerAbility record.
            NotFoundResponse if character or magic element does not exist.
            ValidationFailure on DB error (e.g. UNIQUE conflict).
        """
        async with get_connection() as conn:
            # Pre-check character exists
            char_rows = await conn.execute_fetchall(
                "SELECT id FROM characters WHERE id = ?", (character_id,)
            )
            if not char_rows:
                logger.debug(
                    "Character %d not found for upsert_practitioner_ability", character_id
                )
                return NotFoundResponse(
                    not_found_message=f"Character {character_id} not found"
                )
            # Pre-check magic element exists
            elem_rows = await conn.execute_fetchall(
                "SELECT id FROM magic_system_elements WHERE id = ?", (magic_element_id,)
            )
            if not elem_rows:
                logger.debug(
                    "Magic element %d not found for upsert_practitioner_ability",
                    magic_element_id,
                )
                return NotFoundResponse(
                    not_found_message=f"Magic element {magic_element_id} not found"
                )
            try:
                if ability_id is None:
                    cursor = await conn.execute(
                        """INSERT INTO practitioner_abilities
                            (character_id, magic_element_id, proficiency_level,
                             acquired_chapter_id, notes)
                           VALUES (?, ?, ?, ?, ?)""",
                        (
                            character_id,
                            magic_element_id,
                            proficiency_level,
                            acquired_chapter_id,
                            notes,
                        ),
                    )
                    new_id = cursor.lastrowid
                    await conn.commit()
                    row = await conn.execute_fetchall(
                        "SELECT * FROM practitioner_abilities WHERE id = ?", (new_id,)
                    )
                else:
                    await conn.execute(
                        """INSERT INTO practitioner_abilities
                            (id, character_id, magic_element_id, proficiency_level,
                             acquired_chapter_id, notes)
                           VALUES (?, ?, ?, ?, ?, ?)
                           ON CONFLICT(id) DO UPDATE SET
                               character_id=excluded.character_id,
                               magic_element_id=excluded.magic_element_id,
                               proficiency_level=excluded.proficiency_level,
                               acquired_chapter_id=excluded.acquired_chapter_id,
                               notes=excluded.notes,
                               updated_at=datetime('now')""",
                        (
                            ability_id,
                            character_id,
                            magic_element_id,
                            proficiency_level,
                            acquired_chapter_id,
                            notes,
                        ),
                    )
                    await conn.commit()
                    row = await conn.execute_fetchall(
                        "SELECT * FROM practitioner_abilities WHERE id = ?", (ability_id,)
                    )
                return PractitionerAbility(**dict(row[0]))
            except Exception as exc:
                logger.error("upsert_practitioner_ability failed: %s", exc)
                return ValidationFailure(is_valid=False, errors=[str(exc)])

    # ------------------------------------------------------------------
    # delete_magic_element
    # ------------------------------------------------------------------

    @mcp.tool()
    async def delete_magic_element(
        magic_element_id: int,
    ) -> NotFoundResponse | ValidationFailure | dict:
        """Delete a magic system element by ID.

        FK-safe: magic_system_elements is referenced by practitioner_abilities
        (via magic_element_id) and magic_use_log. If any FK constraint is
        violated, returns ValidationFailure rather than raising.

        Not gate-gated: consistent with phase 14 no-gate pattern for deletes.

        Args:
            magic_element_id: Primary key of the magic_system_elements row to delete.

        Returns:
            {"deleted": True, "id": magic_element_id} on success.
            NotFoundResponse if the element does not exist.
            ValidationFailure if FK constraints prevent deletion.
        """
        async with get_connection() as conn:
            row = await conn.execute_fetchall(
                "SELECT id FROM magic_system_elements WHERE id = ?",
                (magic_element_id,),
            )
            if not row:
                return NotFoundResponse(
                    not_found_message=f"Magic element {magic_element_id} not found"
                )
            try:
                await conn.execute(
                    "DELETE FROM magic_system_elements WHERE id = ?",
                    (magic_element_id,),
                )
                await conn.commit()
                return {"deleted": True, "id": magic_element_id}
            except Exception as exc:
                logger.error("delete_magic_element failed: %s", exc)
                return ValidationFailure(is_valid=False, errors=[str(exc)])

    # ------------------------------------------------------------------
    # delete_practitioner_ability
    # ------------------------------------------------------------------

    @mcp.tool()
    async def delete_practitioner_ability(
        ability_id: int,
    ) -> NotFoundResponse | ValidationFailure | dict:
        """Delete a practitioner ability by ID.

        FK-safe pattern used for safety: if an unexpected FK constraint is
        violated, returns ValidationFailure rather than raising.

        Not gate-gated: consistent with phase 14 no-gate pattern for deletes.

        Args:
            ability_id: Primary key of the practitioner_abilities row to delete.

        Returns:
            {"deleted": True, "id": ability_id} on success.
            NotFoundResponse if the ability does not exist.
            ValidationFailure if FK constraints prevent deletion.
        """
        async with get_connection() as conn:
            row = await conn.execute_fetchall(
                "SELECT id FROM practitioner_abilities WHERE id = ?", (ability_id,)
            )
            if not row:
                return NotFoundResponse(
                    not_found_message=f"Practitioner ability {ability_id} not found"
                )
            try:
                await conn.execute(
                    "DELETE FROM practitioner_abilities WHERE id = ?", (ability_id,)
                )
                await conn.commit()
                return {"deleted": True, "id": ability_id}
            except Exception as exc:
                logger.error("delete_practitioner_ability failed: %s", exc)
                return ValidationFailure(is_valid=False, errors=[str(exc)])

    # ------------------------------------------------------------------
    # delete_magic_use_log
    # ------------------------------------------------------------------

    @mcp.tool()
    async def delete_magic_use_log(magic_use_log_id: int) -> NotFoundResponse | dict:
        """Delete a magic use log entry by ID.

        Log-table delete (simpler pattern): magic_use_log is an append-only
        log with no FK children, so no try/except is needed. Returns
        NotFoundResponse if the entry does not exist.

        Args:
            magic_use_log_id: Primary key of the magic use log entry to delete.

        Returns:
            {"deleted": True, "id": magic_use_log_id} on success, or
            NotFoundResponse if the entry does not exist.
        """
        async with get_connection() as conn:
            row = await conn.execute_fetchall(
                "SELECT id FROM magic_use_log WHERE id = ?", (magic_use_log_id,)
            )
            if not row:
                return NotFoundResponse(
                    not_found_message=f"Magic use log entry {magic_use_log_id} not found"
                )
            await conn.execute("DELETE FROM magic_use_log WHERE id = ?", (magic_use_log_id,))
            await conn.commit()
            return {"deleted": True, "id": magic_use_log_id}

    # ------------------------------------------------------------------
    # get_supernatural_element
    # ------------------------------------------------------------------

    @mcp.tool()
    async def get_supernatural_element(
        element_id: int,
    ) -> SupernaturalElement | NotFoundResponse:
        """Look up a single supernatural element by ID, returning all fields.

        Returns the full element record including description, rules,
        voice_guidelines, and notes.

        Args:
            element_id: Primary key of the supernatural element to retrieve.

        Returns:
            SupernaturalElement with all fields populated, or NotFoundResponse
            if the element does not exist.
        """
        async with get_connection() as conn:
            rows = await conn.execute_fetchall(
                "SELECT * FROM supernatural_elements WHERE id = ?",
                (element_id,),
            )
            if not rows:
                logger.debug("Supernatural element %d not found", element_id)
                return NotFoundResponse(
                    not_found_message=f"Supernatural element {element_id} not found"
                )
            return SupernaturalElement(**dict(rows[0]))

    # ------------------------------------------------------------------
    # list_supernatural_elements
    # ------------------------------------------------------------------

    @mcp.tool()
    async def list_supernatural_elements() -> list[SupernaturalElement]:
        """Return all supernatural elements ordered by name.

        Returns every row from supernatural_elements ordered alphabetically
        by name ASC. An empty list is valid when no elements have been
        created yet.

        Not gate-gated: supernatural elements are worldbuilding data that must
        be writable before gate certification.

        Returns:
            List of SupernaturalElement records ordered by name ASC
            (may be empty).
        """
        async with get_connection() as conn:
            rows = await conn.execute_fetchall(
                "SELECT * FROM supernatural_elements ORDER BY name ASC"
            )
            return [SupernaturalElement(**dict(row)) for row in rows]

    # ------------------------------------------------------------------
    # upsert_supernatural_element
    # ------------------------------------------------------------------

    @mcp.tool()
    async def upsert_supernatural_element(
        element_id: int | None,
        name: str,
        element_type: str,
        description: str | None = None,
        rules: str | None = None,
        voice_guidelines: str | None = None,
        introduced_chapter_id: int | None = None,
        notes: str | None = None,
        canon_status: str = "draft",
    ) -> SupernaturalElement | ValidationFailure:
        """Create or update a supernatural element.

        Two-branch upsert on element_id:
        - element_id=None: INSERT creates a new supernatural_elements row.
        - element_id=N: INSERT ... ON CONFLICT(id) DO UPDATE updates the
          existing row.

        After either branch, the row is SELECT-ed back by id and returned.
        Not gate-gated: supernatural elements are worldbuilding data that must
        be writable before gate certification.

        Args:
            element_id: Existing element ID for update branch (None to create).
            name: Name of the supernatural element (required).
            element_type: Category of element, e.g. 'creature', 'curse',
                          'blessing', 'entity' (required).
            description: Description of the supernatural element (optional).
            rules: Rules governing this element (optional).
            voice_guidelines: Voice/writing guidelines for this element (optional).
            introduced_chapter_id: FK to chapters table — chapter where element
                                    first appears (optional).
            notes: Additional notes (optional).
            canon_status: Canon status of the element (default 'draft').

        Returns:
            The created or updated SupernaturalElement record.
            ValidationFailure on DB error.
        """
        async with get_connection() as conn:
            try:
                if element_id is None:
                    cursor = await conn.execute(
                        """INSERT INTO supernatural_elements
                            (name, element_type, description, rules, voice_guidelines,
                             introduced_chapter_id, notes, canon_status)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            name,
                            element_type,
                            description,
                            rules,
                            voice_guidelines,
                            introduced_chapter_id,
                            notes,
                            canon_status,
                        ),
                    )
                    new_id = cursor.lastrowid
                    await conn.commit()
                    row = await conn.execute_fetchall(
                        "SELECT * FROM supernatural_elements WHERE id = ?", (new_id,)
                    )
                else:
                    await conn.execute(
                        """INSERT INTO supernatural_elements
                            (id, name, element_type, description, rules, voice_guidelines,
                             introduced_chapter_id, notes, canon_status)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                           ON CONFLICT(id) DO UPDATE SET
                               name=excluded.name,
                               element_type=excluded.element_type,
                               description=excluded.description,
                               rules=excluded.rules,
                               voice_guidelines=excluded.voice_guidelines,
                               introduced_chapter_id=excluded.introduced_chapter_id,
                               notes=excluded.notes,
                               canon_status=excluded.canon_status,
                               updated_at=datetime('now')""",
                        (
                            element_id,
                            name,
                            element_type,
                            description,
                            rules,
                            voice_guidelines,
                            introduced_chapter_id,
                            notes,
                            canon_status,
                        ),
                    )
                    await conn.commit()
                    row = await conn.execute_fetchall(
                        "SELECT * FROM supernatural_elements WHERE id = ?", (element_id,)
                    )
                return SupernaturalElement(**dict(row[0]))
            except Exception as exc:
                logger.error("upsert_supernatural_element failed: %s", exc)
                return ValidationFailure(is_valid=False, errors=[str(exc)])

    # ------------------------------------------------------------------
    # delete_supernatural_element
    # ------------------------------------------------------------------

    @mcp.tool()
    async def delete_supernatural_element(
        element_id: int,
    ) -> NotFoundResponse | ValidationFailure | dict:
        """Delete a supernatural element by ID.

        FK-safe: uses try/except pattern to catch any unexpected FK constraint
        violations and return ValidationFailure rather than raising. The
        supernatural_elements table has no direct FK children in the current
        schema (supernatural_voice_guidelines references by element_name text,
        not by FK), but the safe pattern is used for robustness.

        Not gate-gated: consistent with phase 14 no-gate pattern for deletes.

        Args:
            element_id: Primary key of the supernatural_elements row to delete.

        Returns:
            {"deleted": True, "id": element_id} on success.
            NotFoundResponse if the element does not exist.
            ValidationFailure if FK constraints prevent deletion.
        """
        async with get_connection() as conn:
            row = await conn.execute_fetchall(
                "SELECT id FROM supernatural_elements WHERE id = ?",
                (element_id,),
            )
            if not row:
                return NotFoundResponse(
                    not_found_message=f"Supernatural element {element_id} not found"
                )
            try:
                await conn.execute(
                    "DELETE FROM supernatural_elements WHERE id = ?",
                    (element_id,),
                )
                await conn.commit()
                return {"deleted": True, "id": element_id}
            except Exception as exc:
                logger.error("delete_supernatural_element failed: %s", exc)
                return ValidationFailure(is_valid=False, errors=[str(exc)])
