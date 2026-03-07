"""Shared gate enforcement helper for prose-phase MCP tools.

Placed in novel.mcp (not novel.tools) to avoid circular imports with novel.tools.gate.
Phase 7+ tools (session, timeline, canon, knowledge, foreshadowing, names, voice,
publishing) import check_gate from here and call it at the top of each tool handler.

IMPORTANT: Never use print() in this module. All logging goes to stderr via the
logging module — print() corrupts the stdio protocol.
"""
import logging

import aiosqlite

from novel.models.shared import GateViolation

logger = logging.getLogger(__name__)


async def check_gate(conn: aiosqlite.Connection) -> GateViolation | None:
    """Check whether the architecture gate is certified.

    Call at the top of every prose-phase tool (Phase 7+). If gate is not
    certified, return the GateViolation to the caller immediately.

    Usage in prose-phase tools:
        async with get_connection() as conn:
            violation = await check_gate(conn)
            if violation:
                return violation
            # ... rest of tool logic

    Args:
        conn: An already-open aiosqlite.Connection (from get_connection()).

    Returns:
        GateViolation if gate is not certified (caller must return it).
        None if gate is certified (tool may proceed normally).
    """
    rows = await conn.execute_fetchall(
        "SELECT is_certified FROM architecture_gate WHERE id = 1"
    )
    if not rows or not rows[0]["is_certified"]:
        logger.debug("Gate not certified — returning GateViolation")
        return GateViolation(
            requires_action=(
                "Architecture gate is not certified. Run `novel gate check` to see "
                "what is missing, then `novel gate certify` when all 34 items pass."
            )
        )
    return None
