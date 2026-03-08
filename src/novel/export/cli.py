"""Export CLI subcommands: chapter, all.

Regenerates chapter markdown files from database records.
Uses sync sqlite3 via novel.db.connection.get_connection() — never novel.mcp.db.

Commands:
    novel export chapter [n]  — regenerate markdown for a single chapter (CLEX-01)
    novel export all          — regenerate all chapter markdown files (CLEX-02)

Note on schema: chapters table uses time_marker (TEXT) and elapsed_days_from_start (INTEGER)
rather than start_day/end_day. Scenes have no title column — heading uses scene_number.
Location is resolved via the first scene's location_id JOIN to locations.name.
"""
from pathlib import Path

import typer

from novel.db.connection import get_connection

app = typer.Typer(help="Export commands (regenerate chapter markdown files)")


def _build_chapter_markdown(
    chapter_row: "sqlite3.Row",  # type: ignore[name-defined]  # noqa: F821
    scenes: list,
    location_name: str | None,
) -> str:
    """Build chapter markdown string from chapter row and scene rows.

    Args:
        chapter_row: sqlite3.Row with chapter fields plus pov_character_name
        scenes: list of sqlite3.Row scene records ordered by scene_number
        location_name: resolved location name from the first scene's location (or None)

    Returns:
        Markdown string using the chapter format.
    """
    n = chapter_row["chapter_number"]
    title = chapter_row["title"] or "Untitled"
    pov = chapter_row["pov_character_name"] or "(unknown)"
    time_marker = chapter_row["time_marker"] or "—"
    location = location_name or "(unknown)"

    lines = [
        f"# Chapter {n}: {title}",
        "",
        f"**POV**: {pov}",
        f"**Timeline**: {time_marker}",
        f"**Location**: {location}",
        "",
    ]

    if scenes:
        for scene in scenes:
            scene_heading = f"Scene {scene['scene_number']}"
            scene_summary = scene["summary"] or "(no summary)"
            lines.append(f"## {scene_heading}")
            lines.append("")
            lines.append(scene_summary)
            lines.append("")
            lines.append("---")
            lines.append("")
    else:
        lines.append("*(No scenes recorded)*")
        lines.append("")

    return "\n".join(lines)


def _resolve_location(conn: "sqlite3.Connection", chapter_id: int) -> str | None:  # type: ignore[name-defined]  # noqa: F821
    """Return the location name for the first scene of a chapter, or None."""
    row = conn.execute(
        """SELECT l.name
           FROM scenes s
           LEFT JOIN locations l ON l.id = s.location_id
           WHERE s.chapter_id = ?
           ORDER BY s.scene_number
           LIMIT 1""",
        (chapter_id,),
    ).fetchone()
    if row:
        return row["name"]
    return None


def _write_chapter(
    conn: "sqlite3.Connection",  # type: ignore[name-defined]  # noqa: F821
    chapter_row: "sqlite3.Row",  # type: ignore[name-defined]  # noqa: F821
    output_dir: Path,
) -> Path:
    """Write a single chapter markdown file.

    Args:
        conn: Open sync sqlite3 connection.
        chapter_row: sqlite3.Row with chapter fields plus pov_character_name.
        output_dir: Directory to write the file into.

    Returns:
        Path of the written file.
    """
    n = chapter_row["chapter_number"]
    scenes = conn.execute(
        "SELECT * FROM scenes WHERE chapter_id = ? ORDER BY scene_number",
        (chapter_row["id"],),
    ).fetchall()

    location_name = _resolve_location(conn, chapter_row["id"])
    content = _build_chapter_markdown(chapter_row, scenes, location_name)

    out_path = output_dir / f"chapter_{n:03d}.md"
    out_path.write_text(content, encoding="utf-8")
    return out_path


@app.command()
def chapter(
    n: int = typer.Argument(..., help="Chapter number to export"),
    output_dir: str = typer.Option("./chapters", "--output-dir", help="Output directory"),
) -> None:
    """Export a single chapter to a markdown file (CLEX-01)."""
    try:
        out_dir = Path(output_dir)
        out_dir.mkdir(exist_ok=True, parents=True)

        with get_connection() as conn:
            chapter_row = conn.execute(
                """SELECT ch.*, c.name AS pov_character_name
                   FROM chapters ch
                   LEFT JOIN characters c ON c.id = ch.pov_character_id
                   WHERE ch.chapter_number = ?""",
                (n,),
            ).fetchone()

            if chapter_row is None:
                typer.echo(f"Chapter {n} not found.")
                return

            out_path = _write_chapter(conn, chapter_row, out_dir)

        typer.echo(f"Written: {out_path}")

    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)


@app.command(name="all")
def export_all(
    output_dir: str = typer.Option("./chapters", "--output-dir", help="Output directory"),
) -> None:
    """Export all chapters to markdown files (CLEX-02)."""
    try:
        out_dir = Path(output_dir)
        out_dir.mkdir(exist_ok=True, parents=True)

        with get_connection() as conn:
            chapters = conn.execute(
                """SELECT ch.*, c.name AS pov_character_name
                   FROM chapters ch
                   LEFT JOIN characters c ON c.id = ch.pov_character_id
                   ORDER BY ch.chapter_number""",
            ).fetchall()

            if not chapters:
                typer.echo("No chapters found.")
                return

            for chapter_row in chapters:
                out_path = _write_chapter(conn, chapter_row, out_dir)
                typer.echo(f"Written: {out_path}")

    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)
