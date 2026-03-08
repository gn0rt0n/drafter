"""Name CLI subcommands: check, register, suggest.

CLI wrappers around the same SQL logic used by the names MCP tools.
Uses sync sqlite3 via novel.db.connection.get_connection() — never novel.mcp.db.

Commands:
    novel name check [name]           — check for name conflicts (CLNM-01)
    novel name register [name]        — register a name with context (CLNM-02)
    novel name suggest [faction]      — generate culturally consistent name suggestions (CLNM-03)

Schema note: name_registry has columns: id, name, entity_type, culture_id,
linguistic_notes, introduced_chapter_id, notes, created_at.
No character_id, character_role, or faction column exists.
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
                "SELECT name, entity_type, culture_id FROM name_registry WHERE LOWER(name) = LOWER(?)",
                (name,),
            ).fetchall()

        if not rows:
            typer.echo("No conflict.")
        else:
            for row in rows:
                typer.echo(f"Conflict: {row['name']} (entity_type: {row['entity_type']})")

    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)


@app.command()
def register(
    name: str = typer.Argument(..., help="Name to register"),
    entity_type: str | None = typer.Option(None, "--entity-type", help="Entity type (e.g. character, place)"),
    culture: str | None = typer.Option(None, "--culture", help="Culture name to associate"),
    notes: str | None = typer.Option(None, "--notes", help="Additional notes"),
) -> None:
    """Register a name in the name_registry with optional context (CLNM-02)."""
    try:
        if entity_type is None:
            entity_type = (
                typer.prompt("Entity type (character/place/etc, Enter for 'character')", default="character")
                or "character"
            )
        if culture is None:
            culture = typer.prompt("Culture name (optional, Enter to skip)", default="") or None
        if notes is None:
            notes = typer.prompt("Notes (optional, Enter to skip)", default="") or None

        # Resolve culture name to culture_id if provided
        culture_id: int | None = None
        if culture:
            with get_connection() as conn:
                culture_row = conn.execute(
                    "SELECT id FROM cultures WHERE LOWER(name) = LOWER(?)",
                    (culture,),
                ).fetchone()
                if culture_row:
                    culture_id = culture_row["id"]
                else:
                    typer.echo(f"Warning: culture '{culture}' not found — registering without culture_id.")

        with get_connection() as conn:
            try:
                conn.execute(
                    "INSERT INTO name_registry (name, entity_type, culture_id, notes) VALUES (?, ?, ?, ?)",
                    (name, entity_type or "character", culture_id, notes),
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
                # Try resolving via factions table (factions have culture_id)
                faction_row = conn.execute(
                    "SELECT culture_id FROM factions WHERE LOWER(name) = LOWER(?)",
                    (faction_or_region,),
                ).fetchone()
                if faction_row:
                    culture_id = faction_row["culture_id"]

            if culture_id is None:
                typer.echo(f"No culture found for '{faction_or_region}'.")
                return

            # Query name_registry for names associated with this culture
            rows = conn.execute(
                "SELECT name FROM name_registry WHERE culture_id = ? LIMIT 20",
                (culture_id,),
            ).fetchall()

        if not rows:
            typer.echo(
                "No names found for that culture/faction. Add names via 'novel name register'."
            )
        else:
            for row in rows:
                typer.echo(row["name"])

    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)
