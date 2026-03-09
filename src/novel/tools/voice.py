"""Voice domain MCP tools.

All 9 voice tools are registered via the register(mcp) function pattern.
All tools call check_gate(conn) before any database logic — voice tools
are prose-phase operations requiring gate certification.

IMPORTANT: Never use the print function in this module. All logging goes to
stderr via the logging module — using print corrupts the stdio protocol.
"""
import logging

from mcp.server.fastmcp import FastMCP

from novel.mcp.db import get_connection
from novel.mcp.gate import check_gate
from novel.models.shared import GateViolation, NotFoundResponse, ValidationFailure
from novel.models.voice import SupernaturalVoiceGuideline, VoiceDriftLog, VoiceProfile

logger = logging.getLogger(__name__)


def register(mcp: FastMCP) -> None:
    """Register all 9 voice domain tools with the given FastMCP instance.

    Tools are defined as local async functions and decorated with @mcp.tool().
    The FastMCP instance is always the one passed in — never imported globally.

    All tools call check_gate(conn) at the top before any DB logic and return
    GateViolation if the gate is not certified. Voice tools are prose-phase
    operations that require gate certification.

    Args:
        mcp: The FastMCP server instance to register tools against.
    """

    # ------------------------------------------------------------------
    # get_voice_profile (VOIC-01)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def get_voice_profile(
        character_id: int,
    ) -> VoiceProfile | NotFoundResponse | GateViolation:
        """Retrieve the voice profile for a character.

        Args:
            character_id: ID of the character whose voice profile to fetch.

        Returns:
            VoiceProfile if found. NotFoundResponse if no profile exists for
            the character. GateViolation if the gate is not certified.
        """
        async with get_connection() as conn:
            gate = await check_gate(conn)
            if gate is not None:
                return gate

            async with conn.execute(
                "SELECT * FROM voice_profiles WHERE character_id = ?",
                (character_id,),
            ) as cursor:
                row = await cursor.fetchone()

            if row is None:
                return NotFoundResponse(
                    not_found_message=f"No voice profile for character {character_id}"
                )

            return VoiceProfile(**dict(row))

    # ------------------------------------------------------------------
    # upsert_voice_profile (VOIC-02)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def upsert_voice_profile(
        character_id: int,
        profile_id: int | None = None,
        sentence_length: str | None = None,
        vocabulary_level: str | None = None,
        speech_patterns: str | None = None,
        verbal_tics: str | None = None,
        avoids: str | None = None,
        internal_voice_notes: str | None = None,
        dialogue_sample: str | None = None,
        notes: str | None = None,
        canon_status: str = "draft",
    ) -> VoiceProfile | GateViolation:
        """Create or update a voice profile for a character.

        Two-branch upsert on character_id (UNIQUE column in voice_profiles):
        - None profile_id: plain INSERT creates a new profile row.
        - Provided profile_id: INSERT ... ON CONFLICT(character_id) DO UPDATE
          updates the existing profile (character_id is the UNIQUE constraint).

        After either branch, the row is SELECT-ed back by id and returned.

        Args:
            character_id: ID of the character (UNIQUE — one profile per character).
            profile_id: Existing profile ID for update branch (optional).
            sentence_length: Typical sentence length style (optional).
            vocabulary_level: Vocabulary complexity level (optional).
            speech_patterns: Notable speech patterns (optional).
            verbal_tics: Repeated verbal tics or mannerisms (optional).
            avoids: Words or constructions the character avoids (optional).
            internal_voice_notes: Notes on internal monologue voice (optional).
            dialogue_sample: Sample dialogue illustrating the voice (optional).
            notes: Additional notes (optional).
            canon_status: Canon status of the profile (default "draft").

        Returns:
            The created or updated VoiceProfile record.
            GateViolation if the gate is not certified.
        """
        async with get_connection() as conn:
            gate = await check_gate(conn)
            if gate is not None:
                return gate

            if profile_id is None:
                # None-id branch: plain INSERT
                cursor = await conn.execute(
                    """
                    INSERT INTO voice_profiles
                        (character_id, sentence_length, vocabulary_level,
                         speech_patterns, verbal_tics, avoids,
                         internal_voice_notes, dialogue_sample, notes,
                         canon_status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        character_id,
                        sentence_length,
                        vocabulary_level,
                        speech_patterns,
                        verbal_tics,
                        avoids,
                        internal_voice_notes,
                        dialogue_sample,
                        notes,
                        canon_status,
                    ),
                )
                new_id = cursor.lastrowid
            else:
                # Provided-id branch: INSERT ... ON CONFLICT(character_id) DO UPDATE
                await conn.execute(
                    """
                    INSERT INTO voice_profiles
                        (id, character_id, sentence_length, vocabulary_level,
                         speech_patterns, verbal_tics, avoids,
                         internal_voice_notes, dialogue_sample, notes,
                         canon_status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(character_id) DO UPDATE SET
                        sentence_length=excluded.sentence_length,
                        vocabulary_level=excluded.vocabulary_level,
                        speech_patterns=excluded.speech_patterns,
                        verbal_tics=excluded.verbal_tics,
                        avoids=excluded.avoids,
                        internal_voice_notes=excluded.internal_voice_notes,
                        dialogue_sample=excluded.dialogue_sample,
                        notes=excluded.notes,
                        canon_status=excluded.canon_status,
                        updated_at=datetime('now')
                    """,
                    (
                        profile_id,
                        character_id,
                        sentence_length,
                        vocabulary_level,
                        speech_patterns,
                        verbal_tics,
                        avoids,
                        internal_voice_notes,
                        dialogue_sample,
                        notes,
                        canon_status,
                    ),
                )
                new_id = profile_id

            await conn.commit()

            async with conn.execute(
                "SELECT * FROM voice_profiles WHERE id = ?", (new_id,)
            ) as cur:
                row = await cur.fetchone()

            return VoiceProfile(**dict(row))

    # ------------------------------------------------------------------
    # get_supernatural_voice_guidelines (VOIC-03)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def get_supernatural_voice_guidelines() -> (
        list[SupernaturalVoiceGuideline] | GateViolation
    ):
        """Retrieve all supernatural voice guidelines ordered by element name.

        Returns:
            List of SupernaturalVoiceGuideline records ordered by element_name ASC
            (may be empty). GateViolation if the gate is not certified.
        """
        async with get_connection() as conn:
            gate = await check_gate(conn)
            if gate is not None:
                return gate

            async with conn.execute(
                "SELECT * FROM supernatural_voice_guidelines ORDER BY element_name ASC"
            ) as cursor:
                rows = await cursor.fetchall()

            return [SupernaturalVoiceGuideline(**dict(row)) for row in rows]

    # ------------------------------------------------------------------
    # log_voice_drift (VOIC-04)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def log_voice_drift(
        character_id: int,
        description: str,
        drift_type: str = "vocabulary",
        severity: str = "minor",
        chapter_id: int | None = None,
        scene_id: int | None = None,
    ) -> VoiceDriftLog | GateViolation:
        """Log a voice drift event for a character (append-only).

        Append-only INSERT — each call creates a distinct drift log entry.
        Voice drift events are discrete historical observations; they are not
        upserted. Use get_voice_drift_log to retrieve the full drift history.

        Args:
            character_id: ID of the character exhibiting voice drift.
            description: Description of the drift observed.
            drift_type: Category of drift (default "vocabulary").
            severity: Severity of the drift (default "minor").
            chapter_id: Chapter where drift was observed (optional).
            scene_id: Scene where drift was observed (optional).

        Returns:
            The newly created VoiceDriftLog record.
            GateViolation if the gate is not certified.
        """
        async with get_connection() as conn:
            gate = await check_gate(conn)
            if gate is not None:
                return gate

            cursor = await conn.execute(
                """
                INSERT INTO voice_drift_log
                    (character_id, chapter_id, scene_id,
                     drift_type, description, severity)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (character_id, chapter_id, scene_id, drift_type, description, severity),
            )
            new_id = cursor.lastrowid
            await conn.commit()

            async with conn.execute(
                "SELECT * FROM voice_drift_log WHERE id = ?", (new_id,)
            ) as cur:
                row = await cur.fetchone()

            return VoiceDriftLog(**dict(row))

    # ------------------------------------------------------------------
    # get_voice_drift_log (VOIC-05)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def get_voice_drift_log(
        character_id: int,
    ) -> list[VoiceDriftLog] | GateViolation:
        """Retrieve voice drift log entries for a character.

        Returns all drift log entries for the given character ordered by
        created_at DESC (most recent first). An empty list is valid — a
        character with no drift is in good shape, not an error state.

        Args:
            character_id: ID of the character whose drift log to fetch.

        Returns:
            List of VoiceDriftLog records ordered by created_at DESC
            (may be empty). GateViolation if the gate is not certified.
        """
        async with get_connection() as conn:
            gate = await check_gate(conn)
            if gate is not None:
                return gate

            async with conn.execute(
                """
                SELECT * FROM voice_drift_log
                WHERE character_id = ?
                ORDER BY created_at DESC
                """,
                (character_id,),
            ) as cursor:
                rows = await cursor.fetchall()

            return [VoiceDriftLog(**dict(row)) for row in rows]

    # ------------------------------------------------------------------
    # delete_voice_profile (VOIC-06)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def delete_voice_profile(
        voice_profile_id: int,
    ) -> GateViolation | NotFoundResponse | ValidationFailure | dict:
        """Delete a voice profile by ID.

        Gate-gated: deleting a voice profile is a prose-phase operation
        that requires gate certification. voice_profiles may be referenced
        by voice_drift_log entries (via character_id linkage); FK violations
        are caught and returned as ValidationFailure.

        Args:
            voice_profile_id: Primary key of the voice_profiles row to delete.

        Returns:
            Dict with deleted=True and id on success. NotFoundResponse if the
            voice profile does not exist. GateViolation if the gate is not
            certified. ValidationFailure if a FK constraint prevents deletion.
        """
        async with get_connection() as conn:
            gate = await check_gate(conn)
            if gate is not None:
                return gate

            async with conn.execute(
                "SELECT id FROM voice_profiles WHERE id = ?", (voice_profile_id,)
            ) as cursor:
                row = await cursor.fetchone()

            if row is None:
                return NotFoundResponse(
                    not_found_message=f"Voice profile {voice_profile_id} not found"
                )

            try:
                await conn.execute(
                    "DELETE FROM voice_profiles WHERE id = ?", (voice_profile_id,)
                )
                await conn.commit()
                return {"deleted": True, "id": voice_profile_id}
            except Exception as exc:
                logger.error("delete_voice_profile failed: %s", exc)
                return ValidationFailure(is_valid=False, errors=[str(exc)])

    # ------------------------------------------------------------------
    # delete_voice_drift (VOIC-07)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def delete_voice_drift(
        voice_drift_id: int,
    ) -> GateViolation | NotFoundResponse | dict:
        """Delete a voice drift log entry by ID.

        Gate-gated: removing drift log entries is a prose-phase operation
        that requires gate certification. voice_drift_log is an append-only
        log with no FK children — deletion uses the log-style pattern
        (no try/except needed for FK safety).

        Args:
            voice_drift_id: Primary key of the voice_drift_log row to delete.

        Returns:
            Dict with deleted=True and id on success. NotFoundResponse if the
            drift log entry does not exist. GateViolation if the gate is not
            certified.
        """
        async with get_connection() as conn:
            gate = await check_gate(conn)
            if gate is not None:
                return gate

            async with conn.execute(
                "SELECT id FROM voice_drift_log WHERE id = ?", (voice_drift_id,)
            ) as cursor:
                row = await cursor.fetchone()

            if row is None:
                return NotFoundResponse(
                    not_found_message=f"Voice drift log entry {voice_drift_id} not found"
                )

            await conn.execute(
                "DELETE FROM voice_drift_log WHERE id = ?", (voice_drift_id,)
            )
            await conn.commit()
            return {"deleted": True, "id": voice_drift_id}

    # ------------------------------------------------------------------
    # upsert_supernatural_voice_guideline
    # ------------------------------------------------------------------

    @mcp.tool()
    async def upsert_supernatural_voice_guideline(
        guideline_id: int | None,
        element_name: str,
        writing_rules: str,
        element_type: str = "creature",
        avoid: str | None = None,
        example_phrases: str | None = None,
        notes: str | None = None,
    ) -> GateViolation | SupernaturalVoiceGuideline | ValidationFailure:
        """Create or update a supernatural voice guideline.

        Gate-gated: supernatural voice guidelines are prose-phase data
        requiring gate certification.

        Two-branch upsert on guideline_id:
        - guideline_id=None: INSERT creates a new supernatural_voice_guidelines row.
        - guideline_id=N: INSERT ... ON CONFLICT(id) DO UPDATE updates the
          existing row.

        After either branch, the row is SELECT-ed back by id and returned.

        Args:
            guideline_id: Existing guideline ID for update branch (None to create).
            element_name: Name of the supernatural element (UNIQUE in table).
            writing_rules: Writing rules for this element's voice (required).
            element_type: Category of element, e.g. 'creature', 'spirit'
                          (default 'creature').
            avoid: Words, phrases, or patterns to avoid (optional).
            example_phrases: Example phrases that capture the voice (optional).
            notes: Additional notes (optional).

        Returns:
            The created or updated SupernaturalVoiceGuideline record.
            GateViolation if the gate is not certified.
            ValidationFailure on DB error.
        """
        async with get_connection() as conn:
            gate = await check_gate(conn)
            if gate is not None:
                return gate

            try:
                if guideline_id is None:
                    cursor = await conn.execute(
                        """INSERT INTO supernatural_voice_guidelines
                            (element_name, element_type, writing_rules,
                             avoid, example_phrases, notes)
                           VALUES (?, ?, ?, ?, ?, ?)""",
                        (
                            element_name,
                            element_type,
                            writing_rules,
                            avoid,
                            example_phrases,
                            notes,
                        ),
                    )
                    new_id = cursor.lastrowid
                    await conn.commit()
                    async with conn.execute(
                        "SELECT * FROM supernatural_voice_guidelines WHERE id = ?",
                        (new_id,),
                    ) as cur:
                        row = await cur.fetchone()
                else:
                    await conn.execute(
                        """INSERT INTO supernatural_voice_guidelines
                            (id, element_name, element_type, writing_rules,
                             avoid, example_phrases, notes)
                           VALUES (?, ?, ?, ?, ?, ?, ?)
                           ON CONFLICT(id) DO UPDATE SET
                               element_name=excluded.element_name,
                               element_type=excluded.element_type,
                               writing_rules=excluded.writing_rules,
                               avoid=excluded.avoid,
                               example_phrases=excluded.example_phrases,
                               notes=excluded.notes,
                               updated_at=datetime('now')""",
                        (
                            guideline_id,
                            element_name,
                            element_type,
                            writing_rules,
                            avoid,
                            example_phrases,
                            notes,
                        ),
                    )
                    await conn.commit()
                    async with conn.execute(
                        "SELECT * FROM supernatural_voice_guidelines WHERE id = ?",
                        (guideline_id,),
                    ) as cur:
                        row = await cur.fetchone()
                return SupernaturalVoiceGuideline(**dict(row))
            except Exception as exc:
                logger.error("upsert_supernatural_voice_guideline failed: %s", exc)
                return ValidationFailure(is_valid=False, errors=[str(exc)])

    # ------------------------------------------------------------------
    # delete_supernatural_voice_guideline
    # ------------------------------------------------------------------

    @mcp.tool()
    async def delete_supernatural_voice_guideline(
        guideline_id: int,
    ) -> GateViolation | NotFoundResponse | ValidationFailure | dict:
        """Delete a supernatural voice guideline by ID.

        Gate-gated: deleting supernatural voice guidelines is a prose-phase
        operation requiring gate certification. FK-safe: if any FK constraint
        is violated, returns ValidationFailure rather than raising.

        Args:
            guideline_id: Primary key of the supernatural_voice_guidelines row to delete.

        Returns:
            {"deleted": True, "id": guideline_id} on success.
            GateViolation if the gate is not certified.
            NotFoundResponse if the guideline does not exist.
            ValidationFailure if FK constraints prevent deletion.
        """
        async with get_connection() as conn:
            gate = await check_gate(conn)
            if gate is not None:
                return gate

            async with conn.execute(
                "SELECT id FROM supernatural_voice_guidelines WHERE id = ?",
                (guideline_id,),
            ) as cursor:
                row = await cursor.fetchone()

            if row is None:
                return NotFoundResponse(
                    not_found_message=f"Supernatural voice guideline {guideline_id} not found"
                )

            try:
                await conn.execute(
                    "DELETE FROM supernatural_voice_guidelines WHERE id = ?",
                    (guideline_id,),
                )
                await conn.commit()
                return {"deleted": True, "id": guideline_id}
            except Exception as exc:
                logger.error("delete_supernatural_voice_guideline failed: %s", exc)
                return ValidationFailure(is_valid=False, errors=[str(exc)])
