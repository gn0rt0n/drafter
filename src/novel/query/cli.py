"""Query CLI subcommands: pov-balance, arc-health, thread-gaps.

Read-only commands that display narrative data from the database.
Uses sync sqlite3 via novel.db.connection.get_connection() — never novel.mcp.db.

Commands:
    novel query pov-balance   — POV balance table by character (CLSG-06)
    novel query arc-health    — arc progression table for all characters (CLSG-07)
    novel query thread-gaps   — subplots overdue for a touchpoint (CLSG-08)
"""

import typer

from novel.db.connection import get_connection

app = typer.Typer(help="Narrative query commands")


@app.command("pov-balance")
def pov_balance() -> None:
    """Display POV balance: character name, chapter count, and word count (CLSG-06)."""
    try:
        with get_connection() as conn:
            rows = conn.execute(
                """SELECT c.name AS character_name,
                          COUNT(ch.id) AS chapter_count,
                          COALESCE(SUM(ch.actual_word_count), 0) AS word_count
                   FROM chapters ch
                   JOIN characters c ON c.id = ch.pov_character_id
                   WHERE ch.pov_character_id IS NOT NULL
                   GROUP BY ch.pov_character_id
                   ORDER BY chapter_count DESC"""
            ).fetchall()

        if not rows:
            typer.echo("No data.")
            return

        typer.echo(f"{'CHARACTER':<30} {'CHAPTERS':>9} {'WORDS':>10}")
        typer.echo(f"  {'-'*28} {'-'*9} {'-'*10}")
        for row in rows:
            typer.echo(
                f"  {row['character_name']:<28} {row['chapter_count']:>9} {row['word_count']:>10}"
            )

    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)


@app.command("arc-health")
def arc_health() -> None:
    """Display arc progression for all characters with arcs (CLSG-07)."""
    try:
        with get_connection() as conn:
            rows = conn.execute(
                """SELECT ch.name AS character_name,
                          ca.arc_type,
                          ah.health_status AS last_health,
                          ah.chapter_id AS last_chapter
                   FROM character_arcs ca
                   JOIN characters ch ON ch.id = ca.character_id
                   LEFT JOIN arc_health_log ah ON ah.arc_id = ca.id
                     AND ah.id = (
                         SELECT id FROM arc_health_log
                         WHERE arc_id = ca.id
                         ORDER BY chapter_id DESC, id DESC
                         LIMIT 1
                     )
                   ORDER BY ch.name"""
            ).fetchall()

        if not rows:
            typer.echo("No data.")
            return

        typer.echo(
            f"{'CHARACTER':<28} {'ARC TYPE':<18} {'LAST HEALTH':<16} {'LAST CHAPTER':>12}"
        )
        typer.echo(f"  {'-'*26} {'-'*18} {'-'*14} {'-'*12}")
        for row in rows:
            last_health = row["last_health"] or "(none)"
            last_chapter = str(row["last_chapter"]) if row["last_chapter"] is not None else "(none)"
            typer.echo(
                f"  {row['character_name']:<26} {row['arc_type']:<18} "
                f"{last_health:<14} {last_chapter:>12}"
            )

    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)


@app.command("thread-gaps")
def thread_gaps(
    threshold: int = typer.Option(
        3, "--threshold", help="Chapters without touchpoint before subplot is overdue"
    ),
) -> None:
    """Display subplots overdue for a touchpoint (CLSG-08)."""
    try:
        with get_connection() as conn:
            max_row = conn.execute(
                "SELECT MAX(id) AS max_id FROM chapters"
            ).fetchone()
            max_chapter_id = max_row["max_id"] or 0

            rows = conn.execute(
                """SELECT
                       pt.id AS plot_thread_id,
                       pt.name,
                       MAX(stl.chapter_id) AS last_touchpoint_chapter_id,
                       CASE
                           WHEN MAX(stl.chapter_id) IS NULL THEN NULL
                           ELSE (? - MAX(stl.chapter_id))
                       END AS chapters_since_touchpoint
                   FROM plot_threads pt
                   LEFT JOIN subplot_touchpoint_log stl ON stl.plot_thread_id = pt.id
                   WHERE pt.thread_type = 'subplot'
                     AND pt.status = 'active'
                   GROUP BY pt.id, pt.name
                   HAVING MAX(stl.chapter_id) IS NULL
                       OR (? - MAX(stl.chapter_id)) > ?
                   ORDER BY chapters_since_touchpoint DESC""",
                (max_chapter_id, max_chapter_id, threshold),
            ).fetchall()

        if not rows:
            typer.echo("No subplot gaps detected.")
            return

        typer.echo(f"{'SUBPLOT':<35} {'LAST CHAPTER':>12} {'CHAPTERS OVERDUE':>16}")
        typer.echo(f"  {'-'*33} {'-'*12} {'-'*16}")
        for row in rows:
            last_ch = str(row["last_touchpoint_chapter_id"]) if row["last_touchpoint_chapter_id"] is not None else "(never)"
            overdue = str(row["chapters_since_touchpoint"]) if row["chapters_since_touchpoint"] is not None else "(unknown)"
            typer.echo(
                f"  {row['name']:<33} {last_ch:>12} {overdue:>16}"
            )

    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)
