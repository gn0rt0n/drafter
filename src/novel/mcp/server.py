"""Novel MCP server — entry point for the novel-mcp command.

Phase 6: Character, relationship, chapter, scene, world, magic, plot, arc,
and gate tools registered.
Phase 7: Session and timeline tools registered.
Phase 8: Canon, knowledge, and foreshadowing tools registered.

IMPORTANT: No print() statements here or anywhere in this module tree.
All logging goes to stderr via the logging module. print() corrupts
the stdio protocol.

Entry point (pyproject.toml):
    novel-mcp = "novel.mcp.server:run"
"""

import logging
import sys

from mcp.server.fastmcp import FastMCP

from novel.tools import characters, relationships, chapters, scenes, world, magic, plot, arcs, gate, session, timeline, canon, knowledge, foreshadowing

logger = logging.getLogger(__name__)

# FastMCP instance — tools registered via register() calls below
mcp = FastMCP("novel-mcp")

# Register domain tools — Phase 3
characters.register(mcp)
relationships.register(mcp)

# Register domain tools — Phase 4
chapters.register(mcp)
scenes.register(mcp)
world.register(mcp)
magic.register(mcp)

# Register domain tools — Phase 5
plot.register(mcp)
arcs.register(mcp)

# Register domain tools — Phase 6
gate.register(mcp)

# Register domain tools — Phase 7
session.register(mcp)
timeline.register(mcp)

# Register domain tools — Phase 8
canon.register(mcp)
knowledge.register(mcp)
foreshadowing.register(mcp)


def run() -> None:
    """Start the MCP server on stdio transport.

    This function is the pyproject.toml entry point for novel-mcp.
    It must be a function (not the FastMCP instance) so we can configure
    logging and transport before the server loop starts.
    """
    logging.basicConfig(
        level=logging.INFO,
        stream=sys.stderr,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )
    logger.info("Starting novel-mcp server")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    run()
