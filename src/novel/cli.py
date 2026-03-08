"""Novel CLI — root Typer application.

Entry point (pyproject.toml):
    novel = "novel.cli:app"

Subcommand groups:
    novel db ...      — database management (migrate, seed, reset, status)
    novel gate ...    — architecture gate (check, status, certify)
    novel export ...  — export commands (regenerate chapter markdown files)
    novel name ...    — name registry commands (check, register, suggest)
"""

import typer

from novel.db import cli as db_cli  # noqa: F401 — registers db subcommands
from novel.gate import cli as gate_cli  # noqa: F401 — registers gate subcommands
from novel.export import cli as export_cli  # noqa: F401 — registers export subcommands
from novel.name import cli as name_cli  # noqa: F401 — registers name subcommands

app = typer.Typer(
    name="novel",
    help="Novel writing toolkit — CLI for database management, sessions, queries, export, and names.",
    no_args_is_help=True,
)

# Register the db subcommand group
app.add_typer(db_cli.app, name="db")

# Register the gate subcommand group (Phase 6)
app.add_typer(gate_cli.app, name="gate")

# Register the export subcommand group (Phase 10)
app.add_typer(export_cli.app, name="export")

# Register the name subcommand group (Phase 10)
app.add_typer(name_cli.app, name="name")


if __name__ == "__main__":
    app()
