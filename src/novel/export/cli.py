"""Export CLI subcommands: chapter, all.

Regenerates chapter markdown files from database records.
Uses sync sqlite3 via novel.db.connection.get_connection() — never novel.mcp.db.

Commands:
    novel export chapter [n]  — regenerate markdown for a single chapter (CLEX-01)
    novel export all          — regenerate all chapter markdown files (CLEX-02)
"""
from pathlib import Path

import typer

from novel.db.connection import get_connection

app = typer.Typer(help="Export commands (regenerate chapter markdown files)")


def _build_chapter_markdown(chapter_row: "sqlite3.Row", scenes: list) -> str:  # type: ignore[name-defined]  # noqa: F821
    """Build chapter markdown string from chapter row and scene rows.

    Args:
        chapter_row: sqlite3.Row with chapter fields plus pov_character_name
        scenes: list of sqlite3.Row scene records ordered by scene_number

    Returns:
        Markdown string using the LOCKED format.
    """
    n = chapter_row["chapter_number"]
    title = chapter_row["title"] or "Untitled"
    pov = chapter_row["pov_character_name"] or "(unknown)"
    start_day = chapter_row["start_day"] if chapter_row["start_day"] is not None else "?"
    end_day = chapter_row["end_day"] if chapter_row["end_day"] is not None else "?"
    location = chapter_row["primary_location"] or "(unknown)"

    lines = [
        f"# Chapter {n}: {title}",
        "",
        f"**POV**: {pov}",
        f"**Timeline**: Day {start_day} — Day {end_day}",
        f"**Location**: {location}",
        "",
    ]

    if scenes:
        for scene in scenes:
            scene_title = scene["title"] or f"Scene {scene['scene_number']}"
            scene_summary = scene["summary"] or "(no summary)"
            lines.append(f"## {scene_title}")
            lines.append("")
            lines.append(scene_summary)
            lines.append("")
            lines.append("---")
            lines.append("")
    else:
        lines.append("*(No scenes recorded)*")
        lines.append("")

    return "\n".join(lines)


def _write_chapter(conn: "sqlite3.Connection", chapter_row: "sqlite3.Row", output_dir: Path) -> Path:  # type: ignore[name-defined]  # noqa: F821
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

    content = _build_chapter_markdown(chapter_row, scenes)

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
