"""Sync SQLite connection factory for CLI commands.

Every connection enforces WAL journal mode and foreign key constraints.
Use as a context manager:

    from novel.db.connection import get_connection
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM books").fetchall()
"""

import os
import sqlite3
from contextlib import contextmanager
from typing import Generator


def _get_db_path() -> str:
    """Return the database file path from env var or development fallback."""
    return os.environ.get("NOVEL_DB_PATH", "./novel.db")


@contextmanager
def get_connection() -> Generator[sqlite3.Connection, None, None]:
    """Open a sync SQLite connection with WAL mode and FK enforcement.

    Yields:
        sqlite3.Connection with row_factory set to sqlite3.Row (dict-like access).

    Always sets:
        PRAGMA journal_mode=WAL  — for concurrent read/write access
        PRAGMA foreign_keys=ON   — connection-level, not persistent; must be set every time
    """
    conn = sqlite3.connect(_get_db_path())
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.row_factory = sqlite3.Row
        yield conn
    finally:
        conn.close()
