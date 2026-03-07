"""Shared test fixtures for MCP tool tests.

Strategy: session-scoped temp SQLite file (not :memory:) because each
get_connection() call opens a fresh connection. A shared file persists
data across connections within the test session.
"""
import json
import sqlite3

import pytest
import pytest_asyncio
from mcp.shared.memory import create_connected_server_and_client_session

from novel.db.migrations import apply_migrations
from novel.db.seed import load_seed_profile
from novel.mcp.server import mcp


@pytest.fixture(scope="session")
def test_db_path(tmp_path_factory):
    """Create a temp SQLite file with all migrations + minimal seed.

    Session-scoped: created once, reused for all tests in the session.
    """
    db_file = tmp_path_factory.mktemp("db") / "test_mcp.db"
    conn = sqlite3.connect(str(db_file))
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA journal_mode=WAL")
    apply_migrations(conn)
    load_seed_profile(conn, "minimal")
    conn.commit()
    conn.close()
    return str(db_file)


@pytest_asyncio.fixture
async def mcp_session(test_db_path, monkeypatch):
    """Yield a ClientSession connected to the novel MCP server.

    Monkeypatches NOVEL_DB_PATH so get_connection() routes to the test DB.
    """
    monkeypatch.setenv("NOVEL_DB_PATH", test_db_path)
    async with create_connected_server_and_client_session(mcp) as session:
        yield session
