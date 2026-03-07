"""Seed profile loader — stub for Phase 1. Implemented in Phase 2."""

import sqlite3


def load_seed_profile(conn: sqlite3.Connection, profile: str) -> None:
    """Load a named seed profile into the database.

    Phase 1 stub — no profiles defined yet. Phase 2 implements this.

    Args:
        conn: Open sync SQLite connection.
        profile: Seed profile name (e.g., "minimal", "gate-ready").

    Raises:
        ValueError: Always in Phase 1 — no profiles defined.
    """
    raise ValueError(f"No seed profiles defined yet. Profile '{profile}' not available until Phase 2.")
