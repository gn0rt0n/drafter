"""Async SQLite connection factory for MCP tool handlers.

Every connection enforces WAL journal mode and foreign key constraints.
Use as an async context manager:

    from novel.mcp.db import get_connection
    async with get_connection() as conn:
        rows = await conn.execute_fetchall("SELECT * FROM books")

IMPORTANT: Never use print() in MCP server code. All output goes through
the logging module to stderr — print() corrupts the stdio protocol.
"""

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import aiosqlite


def _get_db_path() -> str:
    """Return the database file path from env var or development fallback."""
    return os.environ.get("NOVEL_DB_PATH", "./novel.db")


@asynccontextmanager
async def get_connection() -> AsyncGenerator[aiosqlite.Connection, None]:
    """Open an async SQLite connection with WAL mode and FK enforcement.

    Yields:
        aiosqlite.Connection with row_factory set to aiosqlite.Row (dict-like access).

    Always sets:
        PRAGMA journal_mode=WAL  — for concurrent read/write access
        PRAGMA foreign_keys=ON   — connection-level, not persistent; must be set every time
    """
    async with aiosqlite.connect(_get_db_path()) as conn:
        await conn.execute("PRAGMA journal_mode=WAL")
        await conn.execute("PRAGMA foreign_keys=ON")
        conn.row_factory = aiosqlite.Row
        yield conn
