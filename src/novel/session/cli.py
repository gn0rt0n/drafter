"""Session CLI subcommands: start, close.

Uses sync sqlite3 via novel.db.connection.get_connection() — never novel.mcp.db.

Commands:
    novel session start  — display briefing from last session log (CLSG-01)
    novel session close  — prompt for summary and write session log (CLSG-02)
"""
import json

import typer

from novel.db.connection import get_connection

app = typer.Typer(help="Session management commands")


@app.command()
def start() -> None:
    """Display a briefing from the last session log."""
    try:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM session_logs ORDER BY started_at DESC LIMIT 1"
            ).fetchone()

            if row is None:
                typer.echo("No session logs found.")
                return

            typer.echo(f"Session date    : {row['started_at']}")
            typer.echo(f"Summary         : {row['summary'] or '(none)'}")
            typer.echo(f"Carried forward : {row['carried_forward'] or '(none)'}")

            # Fetch unanswered open questions
            questions = conn.execute(
                "SELECT question FROM open_questions "
                "WHERE answered_at IS NULL ORDER BY created_at ASC"
            ).fetchall()

            if questions:
                typer.echo("\nOpen questions:")
                for q in questions:
                    typer.echo(f"  - {q['question']}")

    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)


@app.command()
def close(
    summary: str | None = typer.Option(
        None, "--summary", help="Session summary (skips prompt)"
    ),
) -> None:
    """Prompt for a summary and close the current open session."""
    try:
        if summary is None:
            summary = typer.prompt("Session summary")

        with get_connection() as conn:
            # Find the most recent open session
            row = conn.execute(
                "SELECT id FROM session_logs "
                "WHERE closed_at IS NULL ORDER BY started_at DESC LIMIT 1"
            ).fetchone()

            if row is None:
                typer.echo("No open session to close.")
                return

            session_id = row["id"]

            # Fetch unanswered open questions for carried_forward
            questions = conn.execute(
                "SELECT question FROM open_questions "
                "WHERE answered_at IS NULL ORDER BY created_at ASC"
            ).fetchall()
            carried_forward = json.dumps([q["question"] for q in questions])

            # Close the session
            conn.execute(
                "UPDATE session_logs "
                "SET closed_at = datetime('now'), summary = ?, carried_forward = ? "
                "WHERE id = ?",
                (summary, carried_forward, session_id),
            )
            conn.commit()

        typer.echo(f"Session {session_id} closed.")

    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)
