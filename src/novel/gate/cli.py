"""Gate CLI subcommands: check, status, certify.

Uses sync sqlite3 via novel.db.connection.get_connection() — same as db CLI.
Never uses novel.mcp.db (that is async, for MCP tools only).

Commands:
    novel gate check    — run full 34-item audit and display gap report (CLSG-03)
    novel gate status   — display current gate status and blocking count (CLSG-04)
    novel gate certify  — certify gate when all items pass (CLSG-05)
"""
import typer
from novel.db.connection import get_connection
from novel.tools.gate import GATE_QUERIES, GATE_ITEM_META

app = typer.Typer(help="Architecture gate commands")


@app.command()
def check() -> None:
    """Run full 34-item gate audit and display gap report."""
    try:
        with get_connection() as conn:
            from datetime import datetime, timezone
            audited_at = datetime.now(timezone.utc).isoformat()
            failing_items: list[tuple[str, int]] = []

            for item_key, query in GATE_QUERIES.items():
                row = conn.execute(query).fetchone()
                missing = row[0] if row else 0
                is_passing = 1 if missing == 0 else 0
                meta = GATE_ITEM_META[item_key]

                conn.execute(
                    """INSERT INTO gate_checklist_items
                           (gate_id, item_key, category, description,
                            is_passing, missing_count, last_checked_at)
                       VALUES (1, ?, ?, ?, ?, ?, ?)
                       ON CONFLICT(gate_id, item_key) DO UPDATE SET
                           is_passing=excluded.is_passing,
                           missing_count=excluded.missing_count,
                           last_checked_at=excluded.last_checked_at""",
                    (item_key, meta["category"], meta["description"],
                     is_passing, missing, audited_at),
                )

                if not is_passing:
                    failing_items.append((item_key, missing))

            conn.commit()

        total = len(GATE_QUERIES)
        if not failing_items:
            typer.echo(f"Gate OPEN — all {total} items pass.")
            typer.echo("Run 'novel gate certify' to write the certification record.")
        else:
            typer.echo(f"Gate BLOCKED — {len(failing_items)} item(s) failing:\n")
            typer.echo(f"  {'ITEM':<40} {'MISSING':>8}")
            typer.echo(f"  {'-'*40} {'-'*8}")
            for key, count in failing_items:
                typer.echo(f"  {'FAIL  ' + key:<40} {count:>8}")
            typer.echo(f"\n{total - len(failing_items)}/{total} items passing.")

    except Exception as e:
        typer.echo(f"Error running gate check: {e}", err=True)
        raise typer.Exit(code=1)


@app.command()
def status() -> None:
    """Display current gate certification status and blocking item count."""
    try:
        with get_connection() as conn:
            gate_row = conn.execute(
                "SELECT is_certified, certified_at, certified_by "
                "FROM architecture_gate WHERE id = 1"
            ).fetchone()

            if not gate_row:
                typer.echo("Gate record not found. Run 'novel db migrate' and 'novel db seed minimal'.")
                raise typer.Exit(code=1)

            blocking = conn.execute(
                "SELECT COUNT(*) FROM gate_checklist_items "
                "WHERE gate_id = 1 AND is_passing = 0"
            ).fetchone()[0]

        certified = bool(gate_row[0])
        certified_at = gate_row[1] or "—"
        certified_by = gate_row[2] or "—"

        typer.echo(f"Gate status       : {'CERTIFIED' if certified else 'NOT CERTIFIED'}")
        typer.echo(f"Blocking items    : {blocking}")
        if certified:
            typer.echo(f"Certified at      : {certified_at}")
            typer.echo(f"Certified by      : {certified_by}")
        else:
            typer.echo("Run 'novel gate check' to see what is missing.")

    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"Error reading gate status: {e}", err=True)
        raise typer.Exit(code=1)


@app.command()
def certify(
    certified_by: str = typer.Option("cli-user", "--by", help="Who is certifying the gate"),
) -> None:
    """Certify the architecture gate if all 34 checklist items pass."""
    try:
        with get_connection() as conn:
            failing = conn.execute(
                "SELECT COUNT(*) FROM gate_checklist_items "
                "WHERE gate_id = 1 AND is_passing = 0"
            ).fetchone()[0]

            if failing > 0:
                typer.echo(
                    f"Gate NOT certified — {failing} item(s) still failing.\n"
                    "Run 'novel gate check' to identify and resolve gaps."
                )
                raise typer.Exit(code=1)

            conn.execute(
                """UPDATE architecture_gate
                   SET is_certified = 1,
                       certified_at = datetime('now'),
                       certified_by = ?,
                       updated_at = datetime('now')
                   WHERE id = 1""",
                (certified_by,),
            )
            conn.commit()

        typer.echo(f"Gate CERTIFIED by '{certified_by}'. Prose-phase tools are now unlocked.")

    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"Error certifying gate: {e}", err=True)
        raise typer.Exit(code=1)
