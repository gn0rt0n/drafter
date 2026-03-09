"""Foreshadowing domain MCP tools.

All 8 foreshadowing tools are registered via the register(mcp) function pattern.
This module is standalone — it does not modify server.py; wiring happens in
the server module.

IMPORTANT: Never use the print function in this module. All logging goes to
stderr via the logging module — using print corrupts the stdio protocol.
"""

import logging

from mcp.server.fastmcp import FastMCP

from novel.mcp.db import get_connection
from novel.mcp.gate import check_gate
from novel.models.canon import (
    ForeshadowingEntry,
    MotifEntry,
    MotifOccurrence,
    OppositionPair,
    ProphecyEntry,
    ThematicMirror,
)
from novel.models.shared import GateViolation, NotFoundResponse, ValidationFailure

logger = logging.getLogger(__name__)


def register(mcp: FastMCP) -> None:
    """Register all 18 foreshadowing domain tools with the given FastMCP instance.

    Tools are defined as local async functions and decorated with @mcp.tool().
    The FastMCP instance is always the one passed in — never imported globally.

    All tools call check_gate(conn) at the top before any DB logic and return
    GateViolation if the gate is not certified.

    Args:
        mcp: The FastMCP server instance to register tools against.
    """

    # ------------------------------------------------------------------
    # get_foreshadowing (FORE-01)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def get_foreshadowing(
        status: str | None = None,
        chapter_id: int | None = None,
    ) -> list[ForeshadowingEntry] | GateViolation:
        """Retrieve foreshadowing entries with optional status and chapter filters.

        Args:
            status: Filter by foreshadowing status (e.g. "planted", "paid_off").
            chapter_id: Filter by plant_chapter_id (optional).

        Returns:
            List of ForeshadowingEntry records ordered by plant_chapter_id ASC
            (may be empty). GateViolation if the gate is not certified.
        """
        async with get_connection() as conn:
            gate = await check_gate(conn)
            if gate is not None:
                return gate

            conditions: list[str] = []
            params: list[object] = []

            if status is not None:
                conditions.append("status = ?")
                params.append(status)
            if chapter_id is not None:
                conditions.append("plant_chapter_id = ?")
                params.append(chapter_id)

            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
            sql = f"SELECT * FROM foreshadowing_registry {where_clause} ORDER BY plant_chapter_id ASC"

            async with conn.execute(sql, params) as cursor:
                rows = await cursor.fetchall()

            return [ForeshadowingEntry(**dict(row)) for row in rows]

    # ------------------------------------------------------------------
    # get_prophecies (FORE-02)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def get_prophecies() -> list[ProphecyEntry] | GateViolation:
        """Retrieve all prophecy registry entries ordered by creation date.

        Returns:
            List of ProphecyEntry records ordered by created_at ASC
            (may be empty). GateViolation if the gate is not certified.
        """
        async with get_connection() as conn:
            gate = await check_gate(conn)
            if gate is not None:
                return gate

            async with conn.execute(
                "SELECT * FROM prophecy_registry ORDER BY created_at ASC"
            ) as cursor:
                rows = await cursor.fetchall()

            return [ProphecyEntry(**dict(row)) for row in rows]

    # ------------------------------------------------------------------
    # get_motifs (FORE-03)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def get_motifs() -> list[MotifEntry] | GateViolation:
        """Retrieve all motif registry entries ordered by creation date.

        Returns:
            List of MotifEntry records ordered by created_at ASC
            (may be empty). GateViolation if the gate is not certified.
        """
        async with get_connection() as conn:
            gate = await check_gate(conn)
            if gate is not None:
                return gate

            async with conn.execute(
                "SELECT * FROM motif_registry ORDER BY created_at ASC"
            ) as cursor:
                rows = await cursor.fetchall()

            return [MotifEntry(**dict(row)) for row in rows]

    # ------------------------------------------------------------------
    # get_motif_occurrences (FORE-04)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def get_motif_occurrences(
        motif_id: int | None = None,
        chapter_id: int | None = None,
    ) -> list[MotifOccurrence] | GateViolation:
        """Retrieve motif occurrences filtered by motif or chapter.

        Args:
            motif_id: Filter by motif (optional).
            chapter_id: Filter by chapter (optional).

        Returns:
            List of MotifOccurrence records ordered by created_at ASC
            (may be empty). GateViolation if the gate is not certified.
        """
        async with get_connection() as conn:
            gate = await check_gate(conn)
            if gate is not None:
                return gate

            conditions: list[str] = []
            params: list[object] = []

            if motif_id is not None:
                conditions.append("motif_id = ?")
                params.append(motif_id)
            if chapter_id is not None:
                conditions.append("chapter_id = ?")
                params.append(chapter_id)

            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
            sql = f"SELECT * FROM motif_occurrences {where_clause} ORDER BY created_at ASC"

            async with conn.execute(sql, params) as cursor:
                rows = await cursor.fetchall()

            return [MotifOccurrence(**dict(row)) for row in rows]

    # ------------------------------------------------------------------
    # get_thematic_mirrors (FORE-05)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def get_thematic_mirrors() -> list[ThematicMirror] | GateViolation:
        """Retrieve all thematic mirror pairs ordered by creation date.

        Returns:
            List of ThematicMirror records ordered by created_at ASC
            (may be empty). GateViolation if the gate is not certified.
        """
        async with get_connection() as conn:
            gate = await check_gate(conn)
            if gate is not None:
                return gate

            async with conn.execute(
                "SELECT * FROM thematic_mirrors ORDER BY created_at ASC"
            ) as cursor:
                rows = await cursor.fetchall()

            return [ThematicMirror(**dict(row)) for row in rows]

    # ------------------------------------------------------------------
    # get_opposition_pairs (FORE-06)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def get_opposition_pairs() -> list[OppositionPair] | GateViolation:
        """Retrieve all opposition pairs ordered by creation date.

        Returns:
            List of OppositionPair records ordered by created_at ASC
            (may be empty). GateViolation if the gate is not certified.
        """
        async with get_connection() as conn:
            gate = await check_gate(conn)
            if gate is not None:
                return gate

            async with conn.execute(
                "SELECT * FROM opposition_pairs ORDER BY created_at ASC"
            ) as cursor:
                rows = await cursor.fetchall()

            return [OppositionPair(**dict(row)) for row in rows]

    # ------------------------------------------------------------------
    # log_foreshadowing (FORE-07)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def log_foreshadowing(
        description: str,
        plant_chapter_id: int,
        foreshadowing_id: int | None = None,
        plant_scene_id: int | None = None,
        payoff_chapter_id: int | None = None,
        payoff_scene_id: int | None = None,
        foreshadowing_type: str = "direct",
        status: str = "planted",
        notes: str | None = None,
    ) -> ForeshadowingEntry | GateViolation:
        """Log or update a foreshadowing entry (upsert — allows payoff to be filled later).

        Two-branch upsert:
        - None foreshadowing_id: plain INSERT creates a new foreshadowing entry.
        - Provided foreshadowing_id: INSERT ... ON CONFLICT(id) DO UPDATE updates
          the existing entry (e.g. filling in payoff_chapter_id when the plant pays off).

        After either branch, the row is SELECT-ed back by id and returned.

        Args:
            description: Description of the foreshadowing plant or callback.
            plant_chapter_id: Chapter where the foreshadowing is planted.
            foreshadowing_id: If provided, upsert the existing entry by primary key.
            plant_scene_id: Scene where the foreshadowing is planted (optional).
            payoff_chapter_id: Chapter where the foreshadowing pays off (optional).
            payoff_scene_id: Scene where the foreshadowing pays off (optional).
            foreshadowing_type: Type of foreshadowing (default "direct").
            status: Current status (default "planted"; use "paid_off" when resolved).
            notes: Additional notes (optional).

        Returns:
            The created or updated ForeshadowingEntry record.
            GateViolation if the gate is not certified.
        """
        async with get_connection() as conn:
            gate = await check_gate(conn)
            if gate is not None:
                return gate

            if foreshadowing_id is None:
                # None-id branch: plain INSERT
                cursor = await conn.execute(
                    """
                    INSERT INTO foreshadowing_registry
                        (description, plant_chapter_id, plant_scene_id,
                         payoff_chapter_id, payoff_scene_id,
                         foreshadowing_type, status, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        description,
                        plant_chapter_id,
                        plant_scene_id,
                        payoff_chapter_id,
                        payoff_scene_id,
                        foreshadowing_type,
                        status,
                        notes,
                    ),
                )
                new_id = cursor.lastrowid
            else:
                # Provided-id branch: INSERT with ON CONFLICT(id) DO UPDATE
                await conn.execute(
                    """
                    INSERT INTO foreshadowing_registry
                        (id, description, plant_chapter_id, plant_scene_id,
                         payoff_chapter_id, payoff_scene_id,
                         foreshadowing_type, status, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        description=excluded.description,
                        plant_chapter_id=excluded.plant_chapter_id,
                        plant_scene_id=excluded.plant_scene_id,
                        payoff_chapter_id=excluded.payoff_chapter_id,
                        payoff_scene_id=excluded.payoff_scene_id,
                        foreshadowing_type=excluded.foreshadowing_type,
                        status=excluded.status,
                        notes=excluded.notes,
                        updated_at=datetime('now')
                    """,
                    (
                        foreshadowing_id,
                        description,
                        plant_chapter_id,
                        plant_scene_id,
                        payoff_chapter_id,
                        payoff_scene_id,
                        foreshadowing_type,
                        status,
                        notes,
                    ),
                )
                new_id = foreshadowing_id

            await conn.commit()

            async with conn.execute(
                "SELECT * FROM foreshadowing_registry WHERE id = ?", (new_id,)
            ) as cur:
                row = await cur.fetchone()

            return ForeshadowingEntry(**dict(row))

    # ------------------------------------------------------------------
    # log_motif_occurrence (FORE-08)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def log_motif_occurrence(
        motif_id: int,
        chapter_id: int,
        scene_id: int | None = None,
        description: str | None = None,
        occurrence_type: str = "direct",
        notes: str | None = None,
    ) -> MotifOccurrence | GateViolation:
        """Log a new motif occurrence (append-only).

        Append-only INSERT — each call creates a distinct occurrence record.
        Historical events are not upserted; each appearance of a motif is a
        discrete, immutable record in the audit trail.

        Args:
            motif_id: FK to the motif in motif_registry.
            chapter_id: Chapter where the motif appears.
            scene_id: Scene where the motif appears (optional).
            description: Description of how the motif manifests (optional).
            occurrence_type: Type of occurrence (default "direct").
            notes: Additional notes (optional).

        Returns:
            The newly created MotifOccurrence record.
            GateViolation if the gate is not certified.
        """
        async with get_connection() as conn:
            gate = await check_gate(conn)
            if gate is not None:
                return gate

            cursor = await conn.execute(
                """
                INSERT INTO motif_occurrences
                    (motif_id, chapter_id, scene_id, description,
                     occurrence_type, notes)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (motif_id, chapter_id, scene_id, description, occurrence_type, notes),
            )
            new_id = cursor.lastrowid
            await conn.commit()

            async with conn.execute(
                "SELECT * FROM motif_occurrences WHERE id = ?", (new_id,)
            ) as cur:
                row = await cur.fetchone()

            return MotifOccurrence(**dict(row))

    # ------------------------------------------------------------------
    # delete_foreshadowing (FORE-09)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def delete_foreshadowing(
        foreshadowing_id: int,
    ) -> GateViolation | NotFoundResponse | dict:
        """Delete a foreshadowing entry by ID.

        Requires gate certification. Idempotent: returns NotFoundResponse if
        absent. foreshadowing_registry is an append-only log with no FK
        children — no IntegrityError expected.

        Args:
            foreshadowing_id: Primary key of the foreshadowing entry to delete.

        Returns:
            {"deleted": True, "id": N} on success.
            GateViolation if the gate is not certified.
            NotFoundResponse if the foreshadowing entry does not exist.
        """
        async with get_connection() as conn:
            gate = await check_gate(conn)
            if gate is not None:
                return gate

            rows = await conn.execute_fetchall(
                "SELECT id FROM foreshadowing_registry WHERE id = ?",
                (foreshadowing_id,),
            )
            if not rows:
                return NotFoundResponse(
                    not_found_message=f"Foreshadowing entry {foreshadowing_id} not found"
                )

            await conn.execute(
                "DELETE FROM foreshadowing_registry WHERE id = ?", (foreshadowing_id,)
            )
            await conn.commit()
            return {"deleted": True, "id": foreshadowing_id}

    # ------------------------------------------------------------------
    # delete_motif_occurrence (FORE-10)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def delete_motif_occurrence(
        motif_occurrence_id: int,
    ) -> GateViolation | NotFoundResponse | dict:
        """Delete a motif occurrence by ID.

        Requires gate certification. Idempotent: returns NotFoundResponse if
        absent. motif_occurrences is a log table with no FK children — no
        IntegrityError expected.

        Args:
            motif_occurrence_id: Primary key of the motif occurrence to delete.

        Returns:
            {"deleted": True, "id": N} on success.
            GateViolation if the gate is not certified.
            NotFoundResponse if the motif occurrence does not exist.
        """
        async with get_connection() as conn:
            gate = await check_gate(conn)
            if gate is not None:
                return gate

            rows = await conn.execute_fetchall(
                "SELECT id FROM motif_occurrences WHERE id = ?",
                (motif_occurrence_id,),
            )
            if not rows:
                return NotFoundResponse(
                    not_found_message=f"Motif occurrence {motif_occurrence_id} not found"
                )

            await conn.execute(
                "DELETE FROM motif_occurrences WHERE id = ?", (motif_occurrence_id,)
            )
            await conn.commit()
            return {"deleted": True, "id": motif_occurrence_id}

    # ------------------------------------------------------------------
    # upsert_motif (FORE-11)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def upsert_motif(
        name: str,
        description: str,
        motif_id: int | None = None,
        motif_type: str = "symbol",
        thematic_role: str | None = None,
        first_appearance_chapter_id: int | None = None,
        notes: str | None = None,
    ) -> GateViolation | MotifEntry | ValidationFailure:
        """Create or update a motif in the motif_registry table.

        Two-branch upsert:
        - None motif_id: plain INSERT creates a new motif.
        - Provided motif_id: INSERT ... ON CONFLICT(id) DO UPDATE sets all
          editable fields on the existing row.

        After either branch, the row is SELECT-ed back by id and returned.

        Args:
            name: Unique name for the motif (required).
            description: Description of the motif (required).
            motif_id: If provided, upsert the existing motif by primary key.
            motif_type: Type of motif (default "symbol").
            thematic_role: Thematic role the motif plays (optional).
            first_appearance_chapter_id: Chapter of first appearance (optional).
            notes: Additional notes (optional).

        Returns:
            The created or updated MotifEntry record.
            GateViolation if the gate is not certified.
            ValidationFailure on database error.
        """
        async with get_connection() as conn:
            gate = await check_gate(conn)
            if gate is not None:
                return gate
            try:
                if motif_id is None:
                    cursor = await conn.execute(
                        """
                        INSERT INTO motif_registry
                            (name, motif_type, description, thematic_role,
                             first_appearance_chapter_id, notes)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            name,
                            motif_type,
                            description,
                            thematic_role,
                            first_appearance_chapter_id,
                            notes,
                        ),
                    )
                    new_id = cursor.lastrowid
                else:
                    await conn.execute(
                        """
                        INSERT INTO motif_registry
                            (id, name, motif_type, description, thematic_role,
                             first_appearance_chapter_id, notes)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(id) DO UPDATE SET
                            name=excluded.name,
                            motif_type=excluded.motif_type,
                            description=excluded.description,
                            thematic_role=excluded.thematic_role,
                            first_appearance_chapter_id=excluded.first_appearance_chapter_id,
                            notes=excluded.notes,
                            updated_at=datetime('now')
                        """,
                        (
                            motif_id,
                            name,
                            motif_type,
                            description,
                            thematic_role,
                            first_appearance_chapter_id,
                            notes,
                        ),
                    )
                    new_id = motif_id
                await conn.commit()
                async with conn.execute(
                    "SELECT * FROM motif_registry WHERE id = ?", (new_id,)
                ) as cur:
                    row = await cur.fetchone()
                return MotifEntry(**dict(row))
            except Exception as exc:
                logger.error("upsert_motif failed: %s", exc)
                return ValidationFailure(is_valid=False, errors=[str(exc)])

    # ------------------------------------------------------------------
    # delete_motif (FORE-12)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def delete_motif(
        motif_id: int,
    ) -> GateViolation | NotFoundResponse | ValidationFailure | dict:
        """Delete a motif from motif_registry by ID.

        Requires gate certification. Idempotent: returns NotFoundResponse if
        absent. motif_registry is referenced by motif_occurrences (motif_id FK)
        — FK-safe: returns ValidationFailure if FK children exist.

        Args:
            motif_id: Primary key of the motif to delete.

        Returns:
            {"deleted": True, "id": N} on success.
            GateViolation if the gate is not certified.
            NotFoundResponse if the motif does not exist.
            ValidationFailure if FK children (motif_occurrences) prevent deletion.
        """
        async with get_connection() as conn:
            gate = await check_gate(conn)
            if gate is not None:
                return gate
            rows = await conn.execute_fetchall(
                "SELECT id FROM motif_registry WHERE id = ?", (motif_id,)
            )
            if not rows:
                return NotFoundResponse(
                    not_found_message=f"Motif {motif_id} not found"
                )
            try:
                await conn.execute(
                    "DELETE FROM motif_registry WHERE id = ?", (motif_id,)
                )
                await conn.commit()
                return {"deleted": True, "id": motif_id}
            except Exception as exc:
                logger.error("delete_motif failed: %s", exc)
                return ValidationFailure(is_valid=False, errors=[str(exc)])

    # ------------------------------------------------------------------
    # upsert_prophecy (FORE-13)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def upsert_prophecy(
        name: str,
        text: str,
        prophecy_id: int | None = None,
        subject_character_id: int | None = None,
        source_character_id: int | None = None,
        uttered_chapter_id: int | None = None,
        fulfilled_chapter_id: int | None = None,
        status: str = "active",
        interpretation: str | None = None,
        notes: str | None = None,
        canon_status: str = "draft",
    ) -> GateViolation | ProphecyEntry | ValidationFailure:
        """Create or update a prophecy in the prophecy_registry table.

        Two-branch upsert:
        - None prophecy_id: plain INSERT creates a new prophecy.
        - Provided prophecy_id: INSERT ... ON CONFLICT(id) DO UPDATE sets all
          editable fields on the existing row.

        After either branch, the row is SELECT-ed back by id and returned.

        Args:
            name: Name of the prophecy (required).
            text: Full text of the prophecy (required).
            prophecy_id: If provided, upsert the existing prophecy by primary key.
            subject_character_id: Character the prophecy is about (optional FK).
            source_character_id: Character who uttered the prophecy (optional FK).
            uttered_chapter_id: Chapter where prophecy was uttered (optional FK).
            fulfilled_chapter_id: Chapter where prophecy was fulfilled (optional FK).
            status: Current status (default "active").
            interpretation: Interpretation notes (optional).
            notes: Additional notes (optional).
            canon_status: Canon status (default "draft").

        Returns:
            The created or updated ProphecyEntry record.
            GateViolation if the gate is not certified.
            ValidationFailure on database error.
        """
        async with get_connection() as conn:
            gate = await check_gate(conn)
            if gate is not None:
                return gate
            try:
                if prophecy_id is None:
                    cursor = await conn.execute(
                        """
                        INSERT INTO prophecy_registry
                            (name, text, subject_character_id, source_character_id,
                             uttered_chapter_id, fulfilled_chapter_id, status,
                             interpretation, notes, canon_status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            name,
                            text,
                            subject_character_id,
                            source_character_id,
                            uttered_chapter_id,
                            fulfilled_chapter_id,
                            status,
                            interpretation,
                            notes,
                            canon_status,
                        ),
                    )
                    new_id = cursor.lastrowid
                else:
                    await conn.execute(
                        """
                        INSERT INTO prophecy_registry
                            (id, name, text, subject_character_id, source_character_id,
                             uttered_chapter_id, fulfilled_chapter_id, status,
                             interpretation, notes, canon_status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(id) DO UPDATE SET
                            name=excluded.name,
                            text=excluded.text,
                            subject_character_id=excluded.subject_character_id,
                            source_character_id=excluded.source_character_id,
                            uttered_chapter_id=excluded.uttered_chapter_id,
                            fulfilled_chapter_id=excluded.fulfilled_chapter_id,
                            status=excluded.status,
                            interpretation=excluded.interpretation,
                            notes=excluded.notes,
                            canon_status=excluded.canon_status,
                            updated_at=datetime('now')
                        """,
                        (
                            prophecy_id,
                            name,
                            text,
                            subject_character_id,
                            source_character_id,
                            uttered_chapter_id,
                            fulfilled_chapter_id,
                            status,
                            interpretation,
                            notes,
                            canon_status,
                        ),
                    )
                    new_id = prophecy_id
                await conn.commit()
                async with conn.execute(
                    "SELECT * FROM prophecy_registry WHERE id = ?", (new_id,)
                ) as cur:
                    row = await cur.fetchone()
                return ProphecyEntry(**dict(row))
            except Exception as exc:
                logger.error("upsert_prophecy failed: %s", exc)
                return ValidationFailure(is_valid=False, errors=[str(exc)])

    # ------------------------------------------------------------------
    # delete_prophecy (FORE-14)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def delete_prophecy(
        prophecy_id: int,
    ) -> GateViolation | NotFoundResponse | ValidationFailure | dict:
        """Delete a prophecy from prophecy_registry by ID.

        Requires gate certification. Idempotent: returns NotFoundResponse if
        absent. FK-safe: returns ValidationFailure if FK constraints prevent
        deletion.

        Args:
            prophecy_id: Primary key of the prophecy to delete.

        Returns:
            {"deleted": True, "id": N} on success.
            GateViolation if the gate is not certified.
            NotFoundResponse if the prophecy does not exist.
            ValidationFailure on database error.
        """
        async with get_connection() as conn:
            gate = await check_gate(conn)
            if gate is not None:
                return gate
            rows = await conn.execute_fetchall(
                "SELECT id FROM prophecy_registry WHERE id = ?", (prophecy_id,)
            )
            if not rows:
                return NotFoundResponse(
                    not_found_message=f"Prophecy {prophecy_id} not found"
                )
            try:
                await conn.execute(
                    "DELETE FROM prophecy_registry WHERE id = ?", (prophecy_id,)
                )
                await conn.commit()
                return {"deleted": True, "id": prophecy_id}
            except Exception as exc:
                logger.error("delete_prophecy failed: %s", exc)
                return ValidationFailure(is_valid=False, errors=[str(exc)])
