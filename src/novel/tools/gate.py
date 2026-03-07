"""Gate domain MCP tools — Architecture gate enforcement.

All 5 gate tools are registered via the register(mcp) function pattern.
This module is standalone — it does not modify server.py; wiring happens in
the server module (06-02).

IMPORTANT: Never use the print function in this module. All logging goes to
stderr via the logging module — using print corrupts the stdio protocol.

The 34 SQL evidence queries in GATE_QUERIES are the core intellectual content
of this module. Every query is relational ("all existing X must have Y"), not
hard-coded counts, making the gate valid for any novel size.
"""

import logging
from datetime import datetime, timezone

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel

from novel.mcp.db import get_connection
from novel.models.gate import ArchitectureGate, GateChecklistItem
from novel.models.shared import NotFoundResponse, ValidationFailure

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# GateAuditReport — returned by run_gate_audit
# ---------------------------------------------------------------------------


class GateAuditReport(BaseModel):
    """Summary result of executing all gate evidence queries."""

    gate_id: int
    total_items: int
    passing_count: int
    failing_count: int
    items: list[GateChecklistItem]
    audited_at: str


# ---------------------------------------------------------------------------
# GATE_ITEM_META — human-readable metadata for each checklist item
# ---------------------------------------------------------------------------

GATE_ITEM_META: dict[str, dict[str, str]] = {
    # population
    "pop_characters": {
        "category": "population",
        "description": "All characters have a motivation defined",
    },
    "pop_factions": {
        "category": "population",
        "description": "All factions have goals defined",
    },
    "pop_locations": {
        "category": "population",
        "description": "All locations have a description defined",
    },
    "pop_cultures": {
        "category": "population",
        "description": "At least one culture exists",
    },
    # structure
    "struct_acts_bounded": {
        "category": "structure",
        "description": "All acts have start_chapter_id and end_chapter_id defined",
    },
    "struct_chapters_summary": {
        "category": "structure",
        "description": "All chapters have a summary defined",
    },
    "struct_chapters_structural_fn": {
        "category": "structure",
        "description": "All chapters have a structural_function defined",
    },
    "struct_chapters_hooks": {
        "category": "structure",
        "description": "All chapters have opening_hook_note and closing_hook_note defined",
    },
    "struct_chapters_pov": {
        "category": "structure",
        "description": "All chapters have a pov_character_id defined",
    },
    "struct_chapter_obligations": {
        "category": "structure",
        "description": "All chapters have at least one chapter_structural_obligations entry",
    },
    # scenes
    "scene_summary": {
        "category": "scenes",
        "description": "All scenes have a summary defined",
    },
    "scene_dramatic_question": {
        "category": "scenes",
        "description": "All scenes have a dramatic_question defined",
    },
    "scene_goals": {
        "category": "scenes",
        "description": "All scenes have at least one scene_character_goals entry",
    },
    "scene_action_summary": {
        "category": "scenes",
        "description": "All action scenes have a summary defined",
    },
    # plot
    "plot_main_stakes": {
        "category": "plot",
        "description": "All main plot threads have stakes defined",
    },
    "plot_threads_summary": {
        "category": "plot",
        "description": "All plot threads have a summary defined",
    },
    "plot_chapter_coverage": {
        "category": "plot",
        "description": "All chapters are linked to at least one plot thread",
    },
    "arcs_pov": {
        "category": "plot",
        "description": "All POV characters have a character arc defined",
    },
    "arcs_lie_truth": {
        "category": "plot",
        "description": "All character arcs have lie_believed and truth_to_learn defined",
    },
    "chekovs_planted": {
        "category": "plot",
        "description": "At least one Chekhov's gun is planted",
    },
    # relationships
    "rel_pov_pairs": {
        "category": "relationships",
        "description": "All POV character pairs have a character_relationship entry",
    },
    "rel_perception": {
        "category": "relationships",
        "description": "All POV characters have at least one perception_profile entry",
    },
    # world
    "world_magic_rules": {
        "category": "world",
        "description": "All magic system elements have rules and limitations defined",
    },
    "world_faction_political": {
        "category": "world",
        "description": "All factions have at least one faction_political_states entry",
    },
    "world_supernatural_voice": {
        "category": "world",
        "description": "Supernatural voice guidelines exist when supernatural elements exist",
    },
    # pacing
    "pacing_tension": {
        "category": "pacing",
        "description": "All chapters have at least one tension_measurements entry",
    },
    "pacing_beats": {
        "category": "pacing",
        "description": "All chapters have at least one pacing_beats entry",
    },
    # voice
    "voice_pov": {
        "category": "voice",
        "description": "All POV characters have a voice_profile defined",
    },
    # names
    "names_characters": {
        "category": "names",
        "description": "All characters have a name_registry entry",
    },
    "names_locations": {
        "category": "names",
        "description": "All locations have a name_registry entry",
    },
    # canon
    "canon_domains": {
        "category": "canon",
        "description": "Canon facts exist in at least 3 distinct domains",
    },
    "foreshadowing_planted": {
        "category": "canon",
        "description": "At least one foreshadowing entry is planted",
    },
    "prophecy_text": {
        "category": "canon",
        "description": "All active prophecies have text defined",
    },
    "motif_registered": {
        "category": "canon",
        "description": "At least one motif is registered",
    },
}


# ---------------------------------------------------------------------------
# GATE_QUERIES — 34 SQL evidence queries (zero missing_count = passing)
# ---------------------------------------------------------------------------

GATE_QUERIES: dict[str, str] = {
    "pop_characters": (
        "SELECT COUNT(*) AS missing_count FROM characters WHERE motivation IS NULL"
    ),
    "pop_factions": (
        "SELECT COUNT(*) AS missing_count FROM factions WHERE goals IS NULL"
    ),
    "pop_locations": (
        "SELECT COUNT(*) AS missing_count FROM locations WHERE description IS NULL"
    ),
    "pop_cultures": (
        "SELECT CASE WHEN COUNT(*) = 0 THEN 1 ELSE 0 END AS missing_count FROM cultures"
    ),
    "struct_acts_bounded": (
        "SELECT COUNT(*) AS missing_count FROM acts"
        " WHERE start_chapter_id IS NULL OR end_chapter_id IS NULL"
    ),
    "struct_chapters_summary": (
        "SELECT COUNT(*) AS missing_count FROM chapters WHERE summary IS NULL"
    ),
    "struct_chapters_structural_fn": (
        "SELECT COUNT(*) AS missing_count FROM chapters"
        " WHERE structural_function IS NULL"
    ),
    "struct_chapters_hooks": (
        "SELECT COUNT(*) AS missing_count FROM chapters"
        " WHERE opening_hook_note IS NULL OR closing_hook_note IS NULL"
    ),
    "struct_chapters_pov": (
        "SELECT COUNT(*) AS missing_count FROM chapters WHERE pov_character_id IS NULL"
    ),
    "struct_chapter_obligations": (
        "SELECT COUNT(*) AS missing_count FROM chapters c"
        " WHERE NOT EXISTS ("
        "SELECT 1 FROM chapter_structural_obligations o WHERE o.chapter_id = c.id)"
    ),
    "scene_summary": (
        "SELECT COUNT(*) AS missing_count FROM scenes WHERE summary IS NULL"
    ),
    "scene_dramatic_question": (
        "SELECT COUNT(*) AS missing_count FROM scenes WHERE dramatic_question IS NULL"
    ),
    "scene_goals": (
        "SELECT COUNT(*) AS missing_count FROM scenes s"
        " WHERE NOT EXISTS ("
        "SELECT 1 FROM scene_character_goals g WHERE g.scene_id = s.id)"
    ),
    "scene_action_summary": (
        "SELECT COUNT(*) AS missing_count FROM scenes"
        " WHERE scene_type = 'action' AND summary IS NULL"
    ),
    "plot_main_stakes": (
        "SELECT COUNT(*) AS missing_count FROM plot_threads"
        " WHERE thread_type = 'main' AND stakes IS NULL"
    ),
    "plot_threads_summary": (
        "SELECT COUNT(*) AS missing_count FROM plot_threads WHERE summary IS NULL"
    ),
    "plot_chapter_coverage": (
        "SELECT COUNT(*) AS missing_count FROM chapters c"
        " WHERE NOT EXISTS ("
        "SELECT 1 FROM chapter_plot_threads cpt WHERE cpt.chapter_id = c.id)"
    ),
    "arcs_pov": (
        "SELECT COUNT(DISTINCT c.pov_character_id) AS missing_count"
        " FROM chapters c"
        " WHERE c.pov_character_id IS NOT NULL"
        " AND NOT EXISTS ("
        "SELECT 1 FROM character_arcs a WHERE a.character_id = c.pov_character_id)"
    ),
    "arcs_lie_truth": (
        "SELECT COUNT(*) AS missing_count FROM character_arcs"
        " WHERE lie_believed IS NULL OR truth_to_learn IS NULL"
    ),
    "chekovs_planted": (
        "SELECT CASE WHEN COUNT(*) = 0 THEN 1 ELSE 0 END AS missing_count"
        " FROM chekovs_gun_registry WHERE status = 'planted'"
    ),
    "rel_pov_pairs": """SELECT COUNT(*) AS missing_count FROM (
        SELECT DISTINCT
            MIN(c1.pov_character_id, c2.pov_character_id) AS char_a,
            MAX(c1.pov_character_id, c2.pov_character_id) AS char_b
        FROM chapters c1
        JOIN chapters c2
            ON c2.pov_character_id != c1.pov_character_id
        WHERE c1.pov_character_id IS NOT NULL
          AND c2.pov_character_id IS NOT NULL
    ) pairs WHERE NOT EXISTS (
        SELECT 1 FROM character_relationships r
        WHERE (r.character_a_id = pairs.char_a AND r.character_b_id = pairs.char_b)
           OR (r.character_a_id = pairs.char_b AND r.character_b_id = pairs.char_a)
    )""",
    "rel_perception": """SELECT COUNT(DISTINCT pov_char) AS missing_count FROM (
        SELECT DISTINCT pov_character_id AS pov_char
        FROM chapters WHERE pov_character_id IS NOT NULL
    ) pov WHERE NOT EXISTS (
        SELECT 1 FROM perception_profiles pp WHERE pp.observer_id = pov.pov_char
    )""",
    "world_magic_rules": (
        "SELECT COUNT(*) AS missing_count FROM magic_system_elements"
        " WHERE rules IS NULL OR limitations IS NULL"
    ),
    "world_faction_political": (
        "SELECT COUNT(*) AS missing_count FROM factions f"
        " WHERE NOT EXISTS ("
        "SELECT 1 FROM faction_political_states fps WHERE fps.faction_id = f.id)"
    ),
    "world_supernatural_voice": (
        "SELECT CASE"
        " WHEN (SELECT COUNT(*) FROM supernatural_elements) > 0"
        "  AND (SELECT COUNT(*) FROM supernatural_voice_guidelines) = 0"
        " THEN 1 ELSE 0 END AS missing_count"
    ),
    "pacing_tension": (
        "SELECT COUNT(*) AS missing_count FROM chapters c"
        " WHERE NOT EXISTS ("
        "SELECT 1 FROM tension_measurements tm WHERE tm.chapter_id = c.id)"
    ),
    "pacing_beats": (
        "SELECT COUNT(*) AS missing_count FROM chapters c"
        " WHERE NOT EXISTS ("
        "SELECT 1 FROM pacing_beats pb WHERE pb.chapter_id = c.id)"
    ),
    "voice_pov": (
        "SELECT COUNT(DISTINCT pov_character_id) AS missing_count FROM chapters"
        " WHERE pov_character_id IS NOT NULL"
        " AND NOT EXISTS ("
        "SELECT 1 FROM voice_profiles vp"
        " WHERE vp.character_id = chapters.pov_character_id)"
    ),
    "names_characters": (
        "SELECT COUNT(*) AS missing_count FROM characters ch"
        " WHERE NOT EXISTS ("
        "SELECT 1 FROM name_registry nr WHERE nr.name = ch.name)"
    ),
    "names_locations": (
        "SELECT COUNT(*) AS missing_count FROM locations loc"
        " WHERE NOT EXISTS ("
        "SELECT 1 FROM name_registry nr WHERE nr.name = loc.name)"
    ),
    "canon_domains": (
        "SELECT CASE WHEN COUNT(DISTINCT domain) < 3"
        " THEN (3 - COUNT(DISTINCT domain)) ELSE 0 END AS missing_count"
        " FROM canon_facts"
    ),
    "foreshadowing_planted": (
        "SELECT CASE WHEN COUNT(*) = 0 THEN 1 ELSE 0 END AS missing_count"
        " FROM foreshadowing_registry WHERE status = 'planted'"
    ),
    "prophecy_text": (
        "SELECT COUNT(*) AS missing_count FROM prophecy_registry"
        " WHERE status = 'active' AND text IS NULL"
    ),
    "motif_registered": (
        "SELECT CASE WHEN COUNT(*) = 0 THEN 1 ELSE 0 END AS missing_count"
        " FROM motif_registry"
    ),
}

# Sanity check: both dicts must have identical key sets
assert set(GATE_QUERIES) == set(GATE_ITEM_META), (
    f"GATE_QUERIES / GATE_ITEM_META key mismatch: "
    f"only in QUERIES: {set(GATE_QUERIES) - set(GATE_ITEM_META)}, "
    f"only in META: {set(GATE_ITEM_META) - set(GATE_QUERIES)}"
)

_GATE_ITEM_COUNT = len(GATE_QUERIES)  # 34 items — store once for tool use


# ---------------------------------------------------------------------------
# register — attach all 5 gate tools to the FastMCP instance
# ---------------------------------------------------------------------------


def register(mcp: FastMCP) -> None:
    """Register all 5 gate tools with the given FastMCP instance.

    Tools are defined as local async functions and decorated with @mcp.tool().
    The FastMCP instance is always the one passed in — never imported globally.

    Args:
        mcp: The FastMCP server instance to register tools against.
    """

    # ------------------------------------------------------------------
    # get_gate_status
    # ------------------------------------------------------------------

    @mcp.tool()
    async def get_gate_status() -> dict | NotFoundResponse:
        """Return the current certification status of the architecture gate.

        Queries architecture_gate id=1 and counts any failing checklist items.

        Returns:
            Dict with gate_id, is_certified, certified_at, certified_by, and
            blocking_item_count, or NotFoundResponse if the gate row is missing.
        """
        async with get_connection() as conn:
            gate_rows = await conn.execute_fetchall(
                "SELECT * FROM architecture_gate WHERE id = 1"
            )
            if not gate_rows:
                logger.warning("architecture_gate id=1 not found")
                return NotFoundResponse(
                    not_found_message=(
                        "Gate record not found (id=1). "
                        "Run 'novel db migrate' and 'novel db seed minimal'."
                    )
                )
            gate = ArchitectureGate(**dict(gate_rows[0]))

            count_rows = await conn.execute_fetchall(
                "SELECT COUNT(*) AS cnt FROM gate_checklist_items"
                " WHERE gate_id = 1 AND is_passing = 0"
            )
            blocking_count = count_rows[0]["cnt"] if count_rows else 0

        logger.debug(
            "get_gate_status: is_certified=%s, blocking_item_count=%d",
            gate.is_certified,
            blocking_count,
        )
        return {
            "gate_id": gate.id,
            "is_certified": gate.is_certified,
            "certified_at": gate.certified_at,
            "certified_by": gate.certified_by,
            "blocking_item_count": blocking_count,
        }

    # ------------------------------------------------------------------
    # get_gate_checklist
    # ------------------------------------------------------------------

    @mcp.tool()
    async def get_gate_checklist() -> list[GateChecklistItem]:
        """Return all checklist items for the architecture gate ordered by category.

        Returns:
            List of GateChecklistItem records ordered by category then item_key.
            Returns an empty list if no checklist items have been populated yet
            (run run_gate_audit to populate them).
        """
        async with get_connection() as conn:
            rows = await conn.execute_fetchall(
                "SELECT * FROM gate_checklist_items"
                " WHERE gate_id = 1 ORDER BY category, item_key"
            )
        logger.debug("get_gate_checklist: returning %d items", len(rows))
        return [GateChecklistItem(**dict(r)) for r in rows]

    # ------------------------------------------------------------------
    # run_gate_audit
    # ------------------------------------------------------------------

    @mcp.tool()
    async def run_gate_audit() -> GateAuditReport | NotFoundResponse:
        """Execute all gate evidence queries and update gate_checklist_items.

        Runs each SQL query in GATE_QUERIES, writes the results back to the
        gate_checklist_items table via upsert, and returns a GateAuditReport
        with per-item pass/fail details.

        This does NOT certify the gate — call certify_gate() separately after
        all items are passing.

        Returns:
            GateAuditReport with total_items, passing_count, failing_count, and
            full items list, or NotFoundResponse if architecture_gate id=1 is
            missing.
        """
        async with get_connection() as conn:
            gate_rows = await conn.execute_fetchall(
                "SELECT * FROM architecture_gate WHERE id = 1"
            )
            if not gate_rows:
                logger.warning("run_gate_audit: architecture_gate id=1 not found")
                return NotFoundResponse(
                    not_found_message=(
                        "Gate record not found (id=1). "
                        "Run 'novel db migrate' and 'novel db seed minimal'."
                    )
                )

            audited_at = datetime.now(timezone.utc).isoformat()

            for item_key, query in GATE_QUERIES.items():
                try:
                    result = await conn.execute_fetchall(query)
                    missing = result[0]["missing_count"] if result else 0
                except Exception as exc:
                    logger.error(
                        "run_gate_audit: query for '%s' failed: %s", item_key, exc
                    )
                    missing = -1  # mark as unknown / errored

                is_passing = 1 if missing == 0 else 0
                meta = GATE_ITEM_META[item_key]

                await conn.execute(
                    """INSERT INTO gate_checklist_items
                           (gate_id, item_key, category, description,
                            is_passing, missing_count, last_checked_at)
                       VALUES (1, ?, ?, ?, ?, ?, datetime('now'))
                       ON CONFLICT(gate_id, item_key) DO UPDATE SET
                           category = excluded.category,
                           description = excluded.description,
                           is_passing = excluded.is_passing,
                           missing_count = excluded.missing_count,
                           last_checked_at = excluded.last_checked_at""",
                    (
                        item_key,
                        meta["category"],
                        meta["description"],
                        is_passing,
                        max(missing, 0),  # never store -1 in the DB
                    ),
                )

            await conn.commit()

            updated_rows = await conn.execute_fetchall(
                "SELECT * FROM gate_checklist_items"
                " WHERE gate_id = 1 ORDER BY category, item_key"
            )

        items = [GateChecklistItem(**dict(r)) for r in updated_rows]
        passing_count = sum(1 for item in items if item.is_passing)
        failing_count = len(items) - passing_count

        logger.info(
            "run_gate_audit complete: %d/%d passing", passing_count, len(items)
        )
        return GateAuditReport(
            gate_id=1,
            total_items=len(items),
            passing_count=passing_count,
            failing_count=failing_count,
            items=items,
            audited_at=audited_at,
        )

    # ------------------------------------------------------------------
    # update_checklist_item
    # ------------------------------------------------------------------

    @mcp.tool()
    async def update_checklist_item(
        item_key: str,
        is_passing: bool,
        missing_count: int = 0,
        notes: str | None = None,
    ) -> GateChecklistItem | NotFoundResponse:
        """Manually override a gate checklist item's pass/fail state.

        Allows human judgment to override the SQL evidence result for cases
        where narrative completeness cannot be captured by a query.

        Args:
            item_key: The unique key of the checklist item (e.g. "pop_characters").
            is_passing: Whether this item should be considered passing.
            missing_count: Number of missing items (0 when is_passing=True).
            notes: Optional free-form notes explaining the manual override.

        Returns:
            The updated GateChecklistItem, or NotFoundResponse if the item key
            does not exist (run run_gate_audit first to populate items).
        """
        async with get_connection() as conn:
            existing = await conn.execute_fetchall(
                "SELECT * FROM gate_checklist_items"
                " WHERE gate_id = 1 AND item_key = ?",
                (item_key,),
            )
            if not existing:
                logger.warning(
                    "update_checklist_item: item_key '%s' not found", item_key
                )
                return NotFoundResponse(
                    not_found_message=(
                        f"Checklist item '{item_key}' not found. "
                        "Run run_gate_audit first."
                    )
                )

            await conn.execute(
                """UPDATE gate_checklist_items
                   SET is_passing = ?,
                       missing_count = ?,
                       notes = COALESCE(?, notes),
                       last_checked_at = datetime('now')
                   WHERE gate_id = 1 AND item_key = ?""",
                (1 if is_passing else 0, missing_count, notes, item_key),
            )
            await conn.commit()

            updated = await conn.execute_fetchall(
                "SELECT * FROM gate_checklist_items"
                " WHERE gate_id = 1 AND item_key = ?",
                (item_key,),
            )

        logger.debug(
            "update_checklist_item: '%s' is_passing=%s", item_key, is_passing
        )
        return GateChecklistItem(**dict(updated[0]))

    # ------------------------------------------------------------------
    # certify_gate
    # ------------------------------------------------------------------

    @mcp.tool()
    async def certify_gate(
        certified_by: str | None = None,
    ) -> ArchitectureGate | ValidationFailure:
        """Certify the architecture gate if all checklist items are passing.

        Reads the current state of gate_checklist_items — does NOT re-run the
        audit. Call run_gate_audit first (or update_checklist_item for manual
        overrides), then call certify_gate to lock the gate as certified.

        Args:
            certified_by: Optional name/identifier of who is certifying the gate.
                          Defaults to "system" when not provided.

        Returns:
            The updated ArchitectureGate record with is_certified=True, or a
            ValidationFailure listing how many items are still failing.
        """
        async with get_connection() as conn:
            failing_rows = await conn.execute_fetchall(
                "SELECT COUNT(*) AS cnt FROM gate_checklist_items"
                " WHERE gate_id = 1 AND is_passing = 0"
            )
            failing = failing_rows[0]["cnt"] if failing_rows else 0

            if failing > 0:
                logger.warning(
                    "certify_gate: %d item(s) still failing", failing
                )
                return ValidationFailure(
                    is_valid=False,
                    errors=[
                        f"{failing} checklist item(s) not passing. "
                        "Run run_gate_audit first, then resolve all gaps."
                    ],
                )

            certifier = certified_by or "system"
            await conn.execute(
                """UPDATE architecture_gate
                   SET is_certified = 1,
                       certified_at = datetime('now'),
                       certified_by = ?,
                       updated_at = datetime('now')
                   WHERE id = 1""",
                (certifier,),
            )
            await conn.commit()

            gate_rows = await conn.execute_fetchall(
                "SELECT * FROM architecture_gate WHERE id = 1"
            )

        logger.info("certify_gate: gate certified by '%s'", certifier)
        return ArchitectureGate(**dict(gate_rows[0]))
