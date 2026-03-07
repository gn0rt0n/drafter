"""Novel MCP server — entry point for the novel-mcp command.

Phase 1: Server scaffold only. MCP tools are registered in Phase 3+.

IMPORTANT: No print() statements here or anywhere in this module tree.
All logging goes to stderr via the logging module. print() corrupts
the stdio protocol.

Entry point (pyproject.toml):
    novel-mcp = "novel.mcp.server:run"
"""

import logging
import sys

from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)

# FastMCP instance — tools registered in Phase 3+ via @mcp.tool() decorators
mcp = FastMCP("novel-mcp")


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
