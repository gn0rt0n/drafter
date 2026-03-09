"""Database management CLI subcommands.

Commands:
    novel db migrate  — apply pending migrations (SETUP-03 / CLDB-01)
    novel db seed     — load a named seed profile (CLDB-02)
    novel db reset    — drop all tables and rebuild (CLDB-03)
    novel db status   — show migration version and table/row counts (CLDB-04)

Requirements implemented: SETUP-03, CLDB-01, CLDB-02, CLDB-03, CLDB-04
"""

import sqlite3
import time

import typer

from novel.db.connection import get_connection
from novel.db.migrations import apply_migrations, drop_all_tables
from novel.db.seed import load_seed_profile

app = typer.Typer(help="Database management commands")


@app.command()
def migrate() -> None:
    """Apply all pending SQL migrations to the database.

    Reads schema_migrations table to determine which migrations have already
    been applied, then applies any remaining migrations in order.
    Completes in under 5 seconds for all 21 migrations on a fresh database.
    """
    start = time.monotonic()
    try:
        with get_connection() as conn:
            newly_applied = apply_migrations(conn)
    except Exception as e:
        typer.echo(f"Error running migrations: {e}", err=True)
        raise typer.Exit(code=1)

    elapsed = time.monotonic() - start

    if not newly_applied:
        typer.echo("Database is already up to date.")
    else:
        for name in newly_applied:
            typer.echo(f"  Applied: {name}")
        typer.echo(f"Applied {len(newly_applied)} migration(s) in {elapsed:.2f}s.")


@app.command()
def seed(
    profile: str = typer.Argument("minimal", help="Seed profile name (e.g. minimal, gate_ready)"),
) -> None:
    """Load a named seed profile into the database.

    Phase 1 stub — no seed profiles are defined yet. Phase 2 implements
    the 'minimal' and 'gate_ready' profiles.
    """
    try:
        with get_connection() as conn:
            load_seed_profile(conn, profile)
    except ValueError as e:
        # Phase 1: load_seed_profile always raises ValueError
        typer.echo(str(e))
        raise typer.Exit(code=0)  # Not an error — expected in Phase 1
    except Exception as e:
        typer.echo(f"Error loading seed profile '{profile}': {e}", err=True)
        raise typer.Exit(code=1)


@app.command()
def reset(
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
) -> None:
    """Drop all tables and rebuild the database from migrations.

    WARNING: Destroys all data. Use --yes to skip the confirmation prompt.
    If the database file does not exist yet, runs migrate directly.
    """
    if not yes:
        confirmed = typer.confirm("This will drop all tables and all data. Continue?", default=False)
        if not confirmed:
            typer.echo("Aborted.")
            raise typer.Exit(code=0)

    try:
        with get_connection() as conn:
            drop_all_tables(conn)
            typer.echo("All tables dropped.")
            newly_applied = apply_migrations(conn)
    except Exception as e:
        typer.echo(f"Error during reset: {e}", err=True)
        raise typer.Exit(code=1)

    for name in newly_applied:
        typer.echo(f"  Applied: {name}")
    typer.echo(f"Reset complete. Applied {len(newly_applied)} migration(s).")


@app.command()
def status() -> None:
    """Show current migration version, table count, and key table row counts.

    Displays:
      - Last applied migration version (0 if no migrations run)
      - Total user table count
      - Row counts for: books, chapters, characters, scenes
    """
    try:
        with get_connection() as conn:
            version = _get_migration_version(conn)
            table_count = _get_table_count(conn)
            row_counts = _get_key_row_counts(conn)
    except Exception as e:
        typer.echo(f"Error reading database status: {e}", err=True)
        raise typer.Exit(code=1)

    typer.echo(f"Migration version : {version}")
    typer.echo(f"Total tables      : {table_count}")
    typer.echo(f"Row counts        :")
    for table, count in row_counts.items():
        typer.echo(f"  {table:<20} {count}")


def _get_migration_version(conn: sqlite3.Connection) -> int:
    """Return the highest applied migration version number, or 0 if none."""
    try:
        row = conn.execute("SELECT MAX(version) FROM schema_migrations").fetchone()
        return row[0] if row and row[0] is not None else 0
    except sqlite3.OperationalError:
        return 0  # schema_migrations table does not exist yet


def _get_table_count(conn: sqlite3.Connection) -> int:
    """Return the count of user-created tables (excludes sqlite_ internal tables)."""
    return conn.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    ).fetchone()[0]


def _get_key_row_counts(conn: sqlite3.Connection) -> dict[str, int]:
    """Return row counts for the four key monitoring tables."""
    counts: dict[str, int] = {}
    for table in ("books", "chapters", "characters", "scenes"):
        try:
            counts[table] = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        except sqlite3.OperationalError:
            counts[table] = 0  # table does not exist yet
    return counts
