"""Novel CLI — root Typer application.

Entry point (pyproject.toml):
    novel = "novel.cli:app"

Subcommand groups:
    novel db ...      — database management (migrate, seed, reset, status)

Additional groups added in later phases:
    novel session ... — session management (Phase 7 / Phase 10)
    novel gate ...    — architecture gate (Phase 6)
    novel query ...   — query commands (Phase 10)
    novel export ...  — export commands (Phase 10)
    novel name ...    — name registry (Phase 10)
"""

import typer

from novel.db import cli as db_cli  # noqa: F401 — registers db subcommands

app = typer.Typer(
    name="novel",
    help="Novel writing toolkit — CLI for database management, sessions, and queries.",
    no_args_is_help=True,
)

# Register the db subcommand group
app.add_typer(db_cli.app, name="db")


if __name__ == "__main__":
    app()
