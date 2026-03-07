"""Novel MCP server — entry point for the novel-mcp command.

Phase 4: Character, relationship, chapter, scene, world, and magic tools registered.

IMPORTANT: No print() statements here or anywhere in this module tree.
All logging goes to stderr via the logging module. print() corrupts
the stdio protocol.

Entry point (pyproject.toml):
    novel-mcp = "novel.mcp.server:run"
"""

import logging
import sys

from mcp.server.fastmcp import FastMCP

from novel.tools import characters, relationships, chapters, scenes, world, magic

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
