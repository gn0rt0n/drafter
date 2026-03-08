"""TEST-04: Tool selection accuracy check.

Structural checks: verify tool count, uniqueness, and description length.
Disambiguation fixture: parametrized tests that each expected_tool_name is
registered and its description contains at least one keyword from the query phrase.

No Claude API calls — this is a static/structural check only.

Actual tool count (confirmed in research): 99 tools across 17 domains.
TEST-04 bounds: 90 <= count <= 110.

_get_tools() access path: mcp._tool_manager._tools (FastMCP internal dict).
Each value is a mcp.server.fastmcp.tools.base.Tool with a .description attribute.
"""

import asyncio

import pytest
from mcp.shared.memory import create_connected_server_and_client_session

from novel.mcp.server import mcp


# ---------------------------------------------------------------------------
# Tool registry access helper
# ---------------------------------------------------------------------------


def _get_tools() -> dict:
    """Access registered tools from FastMCP instance.

    Tries mcp._tool_manager._tools first (FastMCP internal dict, fast).
    Falls back to asyncio list_tools() if the internal attribute is not available
    in a future FastMCP version.
    """
    if hasattr(mcp, "_tool_manager"):
        tm = mcp._tool_manager
        # FastMCP >= 2.x stores tools in _tools dict
        if hasattr(tm, "_tools") and tm._tools:
            return tm._tools
        # FastMCP < 2.x may use .tools directly
        if hasattr(tm, "tools") and tm.tools:
            return tm.tools

    # Fallback: use asyncio to call list_tools via MCP session
    async def _list():
        async with create_connected_server_and_client_session(mcp) as session:
            result = await session.list_tools()
            return {t.name: t for t in result.tools}

    return asyncio.run(_list())


# ---------------------------------------------------------------------------
# Structural tests (sync — no pytest.mark.anyio needed)
# ---------------------------------------------------------------------------


def test_tool_count_in_range():
    """Verify tool count is between 90 and 110.

    Catches accidental module drops (tool < 90) or duplications (> 110).
    Actual count confirmed by research: 99 tools across 17 domains.
    """
    tools = _get_tools()
    count = len(tools)
    assert 90 <= count <= 110, (
        f"Expected 90-110 registered tools, got {count}. "
        "Check that all domain modules are imported in server.py."
    )


def test_no_duplicate_tool_names():
    """All tool names must be unique across all domain modules."""
    tools = _get_tools()
    names = list(tools.keys())
    duplicates = [n for n in set(names) if names.count(n) > 1]
    assert len(names) == len(set(names)), (
        f"Duplicate tool names found: {duplicates}"
    )


def test_all_tools_have_descriptions():
    """Every tool must have a description of at least 50 characters.

    Short descriptions reduce tool selection accuracy for the AI agent.
    """
    tools = _get_tools()
    short = []
    for name, tool in tools.items():
        desc = getattr(tool, "description", None) or ""
        if len(desc) < 50:
            short.append((name, len(desc)))
    assert not short, (
        f"Tools with short descriptions (<50 chars): {short}"
    )


# ---------------------------------------------------------------------------
# Disambiguation pairs: >= 25 pairs covering all 17 domains
# ---------------------------------------------------------------------------

DISAMBIGUATION_PAIRS = [
    # characters (3 pairs)
    ("get a character full profile", "get_character"),
    ("what does this character know at this chapter", "log_character_knowledge"),
    ("list all characters in the book", "list_characters"),
    # relationships (2 pairs)
    ("get relationship between two characters", "get_relationship"),
    ("how does one character perceive another", "get_perception_profile"),
    # chapters (2 pairs)
    ("get chapter plan and metadata", "get_chapter"),
    ("list all chapters in the book", "list_chapters"),
    # scenes (2 pairs)
    ("get scene with full details", "get_scene"),
    ("get character goals for a scene", "get_scene_character_goals"),
    # world (2 pairs)
    ("get faction profile and political state", "get_faction"),
    ("get location with sensory profile", "get_location"),
    # magic (1 pair)
    ("check if a magic action is compliant with system rules", "check_magic_compliance"),
    # plot (2 pairs)
    ("list all plot threads", "list_plot_threads"),
    ("get chekhov gun registry entries", "get_chekovs_guns"),
    # arcs (2 pairs)
    ("get character arc health status", "get_arc_health"),
    ("get subplots overdue for a touchpoint", "get_subplot_touchpoint_gaps"),
    # gate (2 pairs)
    ("run gate audit and get gap report", "run_gate_audit"),
    ("certify the architecture gate", "certify_gate"),
    # session (2 pairs)
    ("start a writing session with briefing", "start_session"),
    ("close current session with summary", "close_session"),
    # timeline (2 pairs)
    ("list timeline events by chapter range", "list_events"),
    ("validate travel realism between locations", "validate_travel_realism"),
    # canon (2 pairs)
    ("log a new canon fact", "log_canon_fact"),
    ("resolve a continuity issue", "resolve_continuity_issue"),
    # knowledge (2 pairs)
    ("get reader information state at chapter", "get_reader_state"),
    ("get dramatic irony inventory", "get_dramatic_irony_inventory"),
    # foreshadowing (2 pairs)
    ("get foreshadowing entries with plant and payoff chapters", "get_foreshadowing"),
    ("log a motif occurrence", "log_motif_occurrence"),
    # names (1 pair)
    ("check for name conflicts in the name registry", "check_name"),
    # voice (2 pairs)
    ("get character voice profile", "get_voice_profile"),
    ("log a voice drift instance", "log_voice_drift"),
    # publishing (2 pairs)
    ("log a new submission to a publisher", "log_submission"),
    ("get publishing assets like query letters", "get_publishing_assets"),
]


@pytest.mark.parametrize("query_phrase,expected_tool", DISAMBIGUATION_PAIRS)
def test_tool_disambiguation(query_phrase: str, expected_tool: str):
    """Each expected_tool is registered and its description contains keywords from the query.

    This validates that the tool name chosen for a given writing task is:
    1. Actually registered in the MCP server (no typos, no missing imports)
    2. Has a description that shares vocabulary with the task description

    These are static checks — no Claude API calls are made.
    """
    tools = _get_tools()
    assert expected_tool in tools, (
        f"Tool '{expected_tool}' is not registered in the MCP server. "
        "Check that the domain module is imported in server.py."
    )
    tool = tools[expected_tool]
    description = getattr(tool, "description", None) or ""
    # Extract meaningful keywords (words > 3 chars, lowercase)
    keywords = [w.lower() for w in query_phrase.split() if len(w) > 3]
    assert any(kw in description.lower() for kw in keywords), (
        f"Tool '{expected_tool}' description does not contain any keywords from query.\n"
        f"Query: '{query_phrase}'\n"
        f"Keywords checked: {keywords}\n"
        f"Description (first 200 chars): '{description[:200]}'"
    )
