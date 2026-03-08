"""Name CLI subcommands: check, register, suggest.

CLI wrappers around the same SQL logic used by the names MCP tools.
Uses sync sqlite3 via novel.db.connection.get_connection() — never novel.mcp.db.

Commands:
    novel name check [name]           — check for name conflicts (CLNM-01)
    novel name register [name]        — register a name with context (CLNM-02)
    novel name suggest [faction]      — generate culturally consistent name suggestions (CLNM-03)
"""
import sqlite3

import typer

from novel.db.connection import get_connection

app = typer.Typer(help="Name registry commands")


@app.command()
def check(name: str = typer.Argument(..., help="Name to check for conflicts")) -> None:
    """Check name_registry for conflicts with the given name (CLNM-01)."""
    try:
        with get_connection() as conn:
            rows = conn.execute(
                """SELECT nr.name, c.name AS character_name
                   FROM name_registry nr
                   LEFT JOIN characters c ON c.id = nr.character_id
                   WHERE LOWER(nr.name) = LOWER(?)""",
                (name,),
            ).fetchall()

        if not rows:
            typer.echo("No conflict.")
        else:
            for row in rows:
                char_name = row["character_name"] or "unassigned"
                typer.echo(f"Conflict: {row['name']} (character: {char_name})")

    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)


@app.command()
def register(
    name: str = typer.Argument(..., help="Name to register"),
    role: str | None = typer.Option(None, "--role", help="Character role"),
    faction: str | None = typer.Option(None, "--faction", help="Faction or region"),
    notes: str | None = typer.Option(None, "--notes", help="Additional notes"),
) -> None:
    """Register a name in the name_registry with optional context (CLNM-02)."""
    try:
        if role is None:
            role = typer.prompt("Character role (optional, Enter to skip)", default="") or None
        if faction is None:
            faction = typer.prompt("Faction/region (optional, Enter to skip)", default="") or None
        if notes is None:
            notes = typer.prompt("Notes (optional, Enter to skip)", default="") or None

        with get_connection() as conn:
            try:
                conn.execute(
                    "INSERT INTO name_registry (name, character_role, faction, notes) VALUES (?, ?, ?, ?)",
                    (name, role, faction, notes),
                )
                conn.commit()
            except sqlite3.IntegrityError:
                typer.echo(f"Name '{name}' already registered.")
                return

        typer.echo(f"Name '{name}' registered.")

    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)


@app.command()
def suggest(
    faction_or_region: str = typer.Argument(..., help="Faction or region name"),
) -> None:
    """Show existing names for a faction/region from the name registry (CLNM-03)."""
    try:
        with get_connection() as conn:
            # Look up culture by name first
            culture_row = conn.execute(
                "SELECT id FROM cultures WHERE LOWER(name) = LOWER(?)",
                (faction_or_region,),
            ).fetchone()

            culture_id = culture_row["id"] if culture_row else None

            if culture_id is None:
                # Try resolving via factions table
                faction_row = conn.execute(
                    "SELECT culture_id FROM factions WHERE LOWER(name) = LOWER(?)",
                    (faction_or_region,),
                ).fetchone()
                if faction_row:
                    culture_id = faction_row["culture_id"]

            if culture_id is None:
                typer.echo(f"No culture found for '{faction_or_region}'.")
                return

            # Query name_registry for names associated with this faction/region string
            rows = conn.execute(
                "SELECT name FROM name_registry WHERE LOWER(faction) = LOWER(?) LIMIT 20",
                (faction_or_region,),
            ).fetchall()

        if not rows:
            typer.echo(
                f"No names found for that culture/faction. Add names via 'novel name register'."
            )
        else:
            for row in rows:
                typer.echo(row["name"])

    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)
