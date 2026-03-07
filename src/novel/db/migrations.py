"""Migration runner for the novel database.

Discovers .sql files bundled inside src/novel/migrations/, compares against
the schema_migrations tracking table, and applies unapplied migrations in order.

Usage:
    from novel.db.connection import get_connection
    from novel.db.migrations import apply_migrations, drop_all_tables

    with get_connection() as conn:
        applied = apply_migrations(conn)
"""

import sqlite3
from datetime import datetime, timezone
from importlib.resources import files
from typing import NamedTuple


class Migration(NamedTuple):
    version: int
    name: str
    sql: str


def discover_migrations() -> list[Migration]:
    """Discover and return all bundled .sql migration files, sorted by version.

    Reads from src/novel/migrations/ via importlib.resources (works in editable
    installs and built wheels). Files must follow the NNN_name.sql naming convention.

    Returns:
        List of Migration tuples sorted by version number ascending.
    """
    migration_dir = files("novel").joinpath("migrations")
    results: list[Migration] = []
    for resource in migration_dir.iterdir():
        name = resource.name
        if name.endswith(".sql"):
            try:
                version = int(name.split("_")[0])
            except (ValueError, IndexError):
                continue  # skip non-conforming files
            sql_text = resource.read_text(encoding="utf-8")
            results.append(Migration(version=version, name=name, sql=sql_text))
    return sorted(results, key=lambda m: m.version)


def _ensure_tracking_table(conn: sqlite3.Connection) -> None:
    """Create schema_migrations table if it does not exist."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version    INTEGER PRIMARY KEY,
            name       TEXT    NOT NULL,
            applied_at TEXT    NOT NULL
        )
        """
    )
    conn.commit()


def get_applied_versions(conn: sqlite3.Connection) -> set[int]:
    """Return the set of migration version numbers already applied."""
    _ensure_tracking_table(conn)
    rows = conn.execute("SELECT version FROM schema_migrations").fetchall()
    return {row[0] for row in rows}


def apply_migrations(conn: sqlite3.Connection) -> list[str]:
    """Apply all unapplied migrations in version order.

    Uses conn.executescript() for each migration file, which handles
    multi-statement SQL files and auto-commits before execution.
    After each migration, records it in schema_migrations.

    Args:
        conn: Open sync SQLite connection (from get_connection()).

    Returns:
        List of applied migration filenames (empty if already up to date).
    """
    applied = get_applied_versions(conn)
    migrations = discover_migrations()
    newly_applied: list[str] = []

    for migration in migrations:
        if migration.version not in applied:
            # executescript() commits any pending transaction before running.
            # Do NOT wrap in an explicit BEGIN — executescript handles it.
            conn.executescript(migration.sql)
            applied_at = datetime.now(timezone.utc).isoformat()
            conn.execute(
                "INSERT INTO schema_migrations (version, name, applied_at) VALUES (?, ?, ?)",
                (migration.version, migration.name, applied_at),
            )
            conn.commit()
            newly_applied.append(migration.name)

    return newly_applied


def drop_all_tables(conn: sqlite3.Connection) -> None:
    """Drop all user-created tables for a clean reset.

    Temporarily disables FK enforcement to allow dropping in any order.
    Re-enables FK enforcement after all tables are dropped.

    Args:
        conn: Open sync SQLite connection.
    """
    conn.execute("PRAGMA foreign_keys=OFF")
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    ).fetchall()
    for row in tables:
        conn.execute(f'DROP TABLE IF EXISTS "{row[0]}"')
    conn.commit()
    conn.execute("PRAGMA foreign_keys=ON")
