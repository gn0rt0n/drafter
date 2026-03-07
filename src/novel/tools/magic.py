"""Magic domain MCP tools.

All 4 magic tools are registered via the register(mcp) function pattern.
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
)
from novel.models.shared import NotFoundResponse, ValidationFailure

logger = logging.getLogger(__name__)


def register(mcp: FastMCP) -> None:
    """Register all 4 magic domain tools with the given FastMCP instance.

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
