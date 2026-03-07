"""Database management CLI subcommands.

Commands:
    novel db migrate  — apply pending migrations (SETUP-03 / CLDB-01)
    novel db seed     — load a seed profile (CLDB-02)
    novel db reset    — drop and rebuild (CLDB-03)
    novel db status   — show migration version and table counts (CLDB-04)

Full implementations added in Plan 03 (01-03-PLAN.md).
"""

import typer

app = typer.Typer(help="Database management commands")


@app.command()
def migrate() -> None:
    """Apply all pending SQL migrations to the database."""
    typer.echo("(stub) migrate — implemented in Plan 03")


@app.command()
def seed(
    profile: str = typer.Argument("minimal", help="Seed profile name (e.g. minimal, gate-ready)"),
) -> None:
    """Load a named seed profile into the database."""
    typer.echo("No seed profiles defined yet.")


@app.command()
def reset(
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
) -> None:
    """Drop all tables and rebuild the database from migrations."""
    typer.echo("(stub) reset — implemented in Plan 03")


@app.command()
def status() -> None:
    """Show migration version, table count, and key table row counts."""
    typer.echo("(stub) status — implemented in Plan 03")
