"""Session domain MCP tools.

All 16 session tools are registered via the register(mcp) function pattern.
This module is standalone — it does not modify server.py; wiring happens in
the server module.

IMPORTANT: Never use the print function in this module. All logging goes to
stderr via the logging module — using print corrupts the stdio protocol.
"""

import json
import logging

from mcp.server.fastmcp import FastMCP

from novel.mcp.db import get_connection
from novel.mcp.gate import check_gate
from novel.models.sessions import (
    AgentRunLog,
    OpenQuestion,
    ProjectMetricsSnapshot,
    PovBalanceSnapshot,
    SessionLog,
    SessionStartResult,
)
from novel.models.shared import GateViolation, NotFoundResponse, ValidationFailure

logger = logging.getLogger(__name__)


def register(mcp: FastMCP) -> None:
    """Register all 16 session domain tools with the given FastMCP instance.

    Tools are defined as local async functions and decorated with @mcp.tool().
    The FastMCP instance is always the one passed in — never imported globally.

    All tools are prose-phase tools — each calls check_gate(conn) at the top
    before any DB logic and returns GateViolation if the gate is not certified.

    Args:
        mcp: The FastMCP server instance to register tools against.
    """

    # ------------------------------------------------------------------
    # start_session (SESS-01)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def start_session() -> SessionStartResult | GateViolation:
        """Start a new writing session and return briefing from the prior session.

        If an open session already exists, it is auto-closed before the new
        session is created.

        The briefing field in the response contains the most recent closed
        session's data (summary + carried_forward) so Claude can read it
        directly from the MCP tool response body — not via stderr.

        Returns:
            SessionStartResult with the new session and optional prior-session
            briefing, or GateViolation if the architecture gate is not
            certified.
        """
        async with get_connection() as conn:
            violation = await check_gate(conn)
            if violation:
                return violation

            # 1. Auto-close any open session
            open_rows = await conn.execute_fetchall(
                "SELECT * FROM session_logs WHERE closed_at IS NULL "
                "ORDER BY started_at DESC LIMIT 1",
                [],
            )
            if open_rows:
                open_id = open_rows[0]["id"]
                await conn.execute(
                    "UPDATE session_logs SET closed_at = datetime('now'), "
                    "notes = 'auto-closed by new session start' WHERE id = ?",
                    (open_id,),
                )
                await conn.commit()

            # 2. Get briefing from the most recent closed session
            prior_rows = await conn.execute_fetchall(
                "SELECT * FROM session_logs WHERE closed_at IS NOT NULL "
                "ORDER BY started_at DESC LIMIT 1",
                [],
            )
            prior_session_row = prior_rows[0] if prior_rows else None

            # 3. INSERT new session
            cursor = await conn.execute(
                "INSERT INTO session_logs DEFAULT VALUES",
                [],
            )
            new_id = cursor.lastrowid
            await conn.commit()

            # 4. SELECT back new row
            new_rows = await conn.execute_fetchall(
                "SELECT * FROM session_logs WHERE id = ?",
                (new_id,),
            )
            new_session = SessionLog(**dict(new_rows[0]))

            # 5. Build briefing if prior session exists
            briefing = SessionLog(**dict(prior_session_row)) if prior_session_row else None

            # 6. Return wrapper — briefing travels in the tool response body
            return SessionStartResult(session=new_session, briefing=briefing)

    # ------------------------------------------------------------------
    # close_session (SESS-02)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def close_session(
        session_id: int,
        summary: str | None = None,
        word_count_delta: int = 0,
        chapters_touched: list[int] | None = None,
    ) -> SessionLog | NotFoundResponse | GateViolation:
        """Close an open session and record its summary and metadata.

        Automatically populates carried_forward from all unanswered open
        questions at the time of closing.

        Args:
            session_id: Primary key of the open session to close.
            summary: Optional summary of work done this session.
            word_count_delta: Net word count change this session (default: 0).
            chapters_touched: List of chapter IDs worked on this session.

        Returns:
            Updated SessionLog row, NotFoundResponse if the session is not
            found or already closed, or GateViolation if gate is not certified.
        """
        async with get_connection() as conn:
            violation = await check_gate(conn)
            if violation:
                return violation

            # 1. Verify session exists and is open
            session_rows = await conn.execute_fetchall(
                "SELECT * FROM session_logs WHERE id = ? AND closed_at IS NULL",
                (session_id,),
            )
            if not session_rows:
                return NotFoundResponse(
                    not_found_message=f"Open session {session_id} not found"
                )

            # 2. Auto-populate carried_forward from unanswered open questions
            question_rows = await conn.execute_fetchall(
                "SELECT question FROM open_questions WHERE answered_at IS NULL "
                "ORDER BY created_at ASC",
                [],
            )
            carried = [r["question"] for r in question_rows]

            # 3. UPDATE session
            await conn.execute(
                "UPDATE session_logs SET "
                "closed_at = datetime('now'), "
                "summary = COALESCE(?, summary), "
                "word_count_delta = ?, "
                "chapters_touched = ?, "
                "carried_forward = ? "
                "WHERE id = ?",
                (
                    summary,
                    word_count_delta,
                    json.dumps(chapters_touched) if chapters_touched is not None else None,
                    json.dumps(carried),
                    session_id,
                ),
            )
            await conn.commit()

            # 4. SELECT back updated row
            updated = await conn.execute_fetchall(
                "SELECT * FROM session_logs WHERE id = ?",
                (session_id,),
            )
            return SessionLog(**dict(updated[0]))

    # ------------------------------------------------------------------
    # get_last_session (SESS-03)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def get_last_session() -> SessionLog | NotFoundResponse | GateViolation:
        """Retrieve the most recent session log entry.

        Returns:
            The most recently started SessionLog, NotFoundResponse if no
            sessions exist, or GateViolation if gate is not certified.
        """
        async with get_connection() as conn:
            violation = await check_gate(conn)
            if violation:
                return violation

            rows = await conn.execute_fetchall(
                "SELECT * FROM session_logs ORDER BY started_at DESC LIMIT 1",
                [],
            )
            if not rows:
                return NotFoundResponse(not_found_message="No session logs found")
            return SessionLog(**dict(rows[0]))

    # ------------------------------------------------------------------
    # log_agent_run (SESS-04)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def log_agent_run(
        agent_name: str,
        tool_name: str,
        input_summary: str | None = None,
        output_summary: str | None = None,
        duration_ms: int | None = None,
        success: bool = True,
        session_id: int | None = None,
        error_message: str | None = None,
    ) -> AgentRunLog | GateViolation:
        """Append an agent run entry to the audit trail.

        Append-only INSERT — no ON CONFLICT since agent_run_log is a pure
        audit trail. Multiple entries per session are expected and valid.

        Args:
            agent_name: Name of the agent that ran (required).
            tool_name: Name of the tool the agent called (required).
            input_summary: Brief description of the tool input (optional).
            output_summary: Brief description of the tool output (optional).
            duration_ms: Duration of the run in milliseconds (optional).
            success: Whether the run succeeded (default: True).
            session_id: FK to session_logs — which session this run belongs
                        to (optional).
            error_message: Error description if success is False (optional).

        Returns:
            The newly created AgentRunLog row, or GateViolation if gate is
            not certified.
        """
        async with get_connection() as conn:
            violation = await check_gate(conn)
            if violation:
                return violation

            cursor = await conn.execute(
                "INSERT INTO agent_run_log "
                "(session_id, agent_name, tool_name, input_summary, output_summary, "
                "duration_ms, success, error_message) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    session_id,
                    agent_name,
                    tool_name,
                    input_summary,
                    output_summary,
                    duration_ms,
                    success,
                    error_message,
                ),
            )
            new_id = cursor.lastrowid
            await conn.commit()

            rows = await conn.execute_fetchall(
                "SELECT * FROM agent_run_log WHERE id = ?",
                (new_id,),
            )
            return AgentRunLog(**dict(rows[0]))

    # ------------------------------------------------------------------
    # get_project_metrics (SESS-05)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def get_project_metrics() -> ProjectMetricsSnapshot | GateViolation:
        """Retrieve live-computed project metrics (not stored snapshots).

        Aggregates current counts directly from the database tables:
        word_count from chapters, plus counts of chapters, scenes,
        characters, and session_logs.

        Returns:
            ProjectMetricsSnapshot with live aggregate values (id and
            snapshot_at will be None for live results), or GateViolation
            if gate is not certified.
        """
        async with get_connection() as conn:
            violation = await check_gate(conn)
            if violation:
                return violation

            wc_rows = await conn.execute_fetchall(
                "SELECT COALESCE(SUM(actual_word_count), 0) AS word_count FROM chapters",
                [],
            )
            ch_rows = await conn.execute_fetchall(
                "SELECT COUNT(*) AS cnt FROM chapters",
                [],
            )
            sc_rows = await conn.execute_fetchall(
                "SELECT COUNT(*) AS cnt FROM scenes",
                [],
            )
            char_rows = await conn.execute_fetchall(
                "SELECT COUNT(*) AS cnt FROM characters",
                [],
            )
            sess_rows = await conn.execute_fetchall(
                "SELECT COUNT(*) AS cnt FROM session_logs",
                [],
            )

            return ProjectMetricsSnapshot(
                word_count=wc_rows[0]["word_count"],
                chapter_count=ch_rows[0]["cnt"],
                scene_count=sc_rows[0]["cnt"],
                character_count=char_rows[0]["cnt"],
                session_count=sess_rows[0]["cnt"],
            )

    # ------------------------------------------------------------------
    # log_project_snapshot (SESS-06)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def log_project_snapshot(
        notes: str | None = None,
    ) -> ProjectMetricsSnapshot | GateViolation:
        """Persist a project metrics snapshot to the database.

        Runs the same live aggregate queries as get_project_metrics, then
        inserts a permanent snapshot row for historical tracking.

        Args:
            notes: Optional notes to store with the snapshot.

        Returns:
            The newly created ProjectMetricsSnapshot row (with id and
            snapshot_at populated), or GateViolation if gate is not
            certified.
        """
        async with get_connection() as conn:
            violation = await check_gate(conn)
            if violation:
                return violation

            # Run same live aggregates as get_project_metrics
            wc_rows = await conn.execute_fetchall(
                "SELECT COALESCE(SUM(actual_word_count), 0) AS word_count FROM chapters",
                [],
            )
            ch_rows = await conn.execute_fetchall(
                "SELECT COUNT(*) AS cnt FROM chapters",
                [],
            )
            sc_rows = await conn.execute_fetchall(
                "SELECT COUNT(*) AS cnt FROM scenes",
                [],
            )
            char_rows = await conn.execute_fetchall(
                "SELECT COUNT(*) AS cnt FROM characters",
                [],
            )
            sess_rows = await conn.execute_fetchall(
                "SELECT COUNT(*) AS cnt FROM session_logs",
                [],
            )

            word_count = wc_rows[0]["word_count"]
            chapter_count = ch_rows[0]["cnt"]
            scene_count = sc_rows[0]["cnt"]
            character_count = char_rows[0]["cnt"]
            session_count = sess_rows[0]["cnt"]

            cursor = await conn.execute(
                "INSERT INTO project_metrics_snapshots "
                "(word_count, chapter_count, scene_count, character_count, "
                "session_count, notes) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (word_count, chapter_count, scene_count, character_count, session_count, notes),
            )
            new_id = cursor.lastrowid
            await conn.commit()

            rows = await conn.execute_fetchall(
                "SELECT * FROM project_metrics_snapshots WHERE id = ?",
                (new_id,),
            )
            return ProjectMetricsSnapshot(**dict(rows[0]))

    # ------------------------------------------------------------------
    # get_pov_balance (SESS-07)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def get_pov_balance() -> list[PovBalanceSnapshot] | GateViolation:
        """Retrieve live-computed POV balance across all chapters.

        Groups chapters by pov_character_id and aggregates chapter count
        and total word count for each POV character. Only chapters with a
        non-NULL pov_character_id are included.

        Returns:
            List of PovBalanceSnapshot records ordered by chapter_count
            DESC (may be empty if no chapters have POV characters assigned),
            or GateViolation if gate is not certified.
        """
        async with get_connection() as conn:
            violation = await check_gate(conn)
            if violation:
                return violation

            rows = await conn.execute_fetchall(
                """SELECT pov_character_id AS character_id,
                          COUNT(*) AS chapter_count,
                          COALESCE(SUM(actual_word_count), 0) AS word_count
                   FROM chapters
                   WHERE pov_character_id IS NOT NULL
                   GROUP BY pov_character_id
                   ORDER BY chapter_count DESC""",
                [],
            )
            return [
                PovBalanceSnapshot(
                    character_id=r["character_id"],
                    chapter_count=r["chapter_count"],
                    word_count=r["word_count"],
                )
                for r in rows
            ]

    # ------------------------------------------------------------------
    # get_open_questions (SESS-08)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def get_open_questions(
        domain: str | None = None,
    ) -> list[OpenQuestion] | GateViolation:
        """Retrieve all unanswered open questions, optionally filtered by domain.

        Only returns questions where answered_at IS NULL (unanswered).
        Results are ordered by created_at ASC (oldest first).

        Args:
            domain: Optional domain filter (e.g. 'plot', 'character', 'world').
                    If None, all unanswered questions across all domains are
                    returned.

        Returns:
            List of OpenQuestion records (may be empty), or GateViolation if
            gate is not certified.
        """
        async with get_connection() as conn:
            violation = await check_gate(conn)
            if violation:
                return violation

            sql = "SELECT * FROM open_questions WHERE answered_at IS NULL"
            params: list = []
            if domain is not None:
                sql += " AND domain = ?"
                params.append(domain)
            sql += " ORDER BY created_at ASC"

            rows = await conn.execute_fetchall(sql, params)
            return [OpenQuestion(**dict(r)) for r in rows]

    # ------------------------------------------------------------------
    # log_open_question (SESS-09)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def log_open_question(
        question: str,
        domain: str | None = None,
        session_id: int | None = None,
        priority: str | None = None,
        notes: str | None = None,
    ) -> OpenQuestion | GateViolation:
        """Append a new open question to the log (append-only, no upsert).

        Open questions are always appended — duplicate questions are allowed
        since context and priority may differ between occurrences.

        Args:
            question: The question text (required).
            domain: Optional domain classification (e.g. 'plot', 'character').
            session_id: FK to session_logs — which session raised this question.
            priority: Optional priority level (e.g. 'high', 'normal', 'low').
            notes: Optional freeform notes about the question.

        Returns:
            The newly created OpenQuestion row, or GateViolation if gate is
            not certified.
        """
        # Apply SQL DEFAULT values for NOT NULL columns when caller passes None
        effective_domain = domain if domain is not None else "general"
        effective_priority = priority if priority is not None else "normal"

        async with get_connection() as conn:
            violation = await check_gate(conn)
            if violation:
                return violation

            cursor = await conn.execute(
                "INSERT INTO open_questions "
                "(question, domain, session_id, priority, notes) "
                "VALUES (?, ?, ?, ?, ?)",
                (question, effective_domain, session_id, effective_priority, notes),
            )
            new_id = cursor.lastrowid
            await conn.commit()

            rows = await conn.execute_fetchall(
                "SELECT * FROM open_questions WHERE id = ?",
                (new_id,),
            )
            return OpenQuestion(**dict(rows[0]))

    # ------------------------------------------------------------------
    # answer_open_question (SESS-10)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def answer_open_question(
        question_id: int,
        answer: str,
    ) -> OpenQuestion | NotFoundResponse | GateViolation:
        """Mark an open question as answered with a recorded answer and timestamp.

        Updates the answer and sets answered_at to the current UTC time.
        If the question does not exist, returns NotFoundResponse.

        Args:
            question_id: Primary key of the open_questions row to answer.
            answer: The answer text to record (required).

        Returns:
            The updated OpenQuestion row with answered_at populated,
            NotFoundResponse if the question_id does not exist, or
            GateViolation if gate is not certified.
        """
        async with get_connection() as conn:
            violation = await check_gate(conn)
            if violation:
                return violation

            await conn.execute(
                "UPDATE open_questions SET answer = ?, answered_at = datetime('now') "
                "WHERE id = ?",
                (answer, question_id),
            )
            await conn.commit()

            rows = await conn.execute_fetchall(
                "SELECT * FROM open_questions WHERE id = ?",
                (question_id,),
            )
            if not rows:
                return NotFoundResponse(
                    not_found_message=f"Open question {question_id} not found"
                )
            return OpenQuestion(**dict(rows[0]))

    # ------------------------------------------------------------------
    # delete_session_log (SESS-11)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def delete_session_log(
        session_log_id: int,
    ) -> GateViolation | NotFoundResponse | ValidationFailure | dict:
        """Delete a session log entry by ID.

        Gate-gated: deleting session records is a prose-phase operation that
        requires gate certification. session_logs may be referenced by
        agent_run_log (via session_id FK); FK violations are caught and
        returned as ValidationFailure.

        Args:
            session_log_id: Primary key of the session_logs row to delete.

        Returns:
            Dict with deleted=True and id on success. NotFoundResponse if the
            session log does not exist. GateViolation if the gate is not
            certified. ValidationFailure if a FK constraint prevents deletion
            (e.g. linked agent_run_log entries exist).
        """
        async with get_connection() as conn:
            violation = await check_gate(conn)
            if violation:
                return violation

            rows = await conn.execute_fetchall(
                "SELECT id FROM session_logs WHERE id = ?",
                (session_log_id,),
            )
            if not rows:
                return NotFoundResponse(
                    not_found_message=f"Session log {session_log_id} not found"
                )

            try:
                await conn.execute(
                    "DELETE FROM session_logs WHERE id = ?", (session_log_id,)
                )
                await conn.commit()
                return {"deleted": True, "id": session_log_id}
            except Exception as exc:
                logger.error("delete_session_log failed: %s", exc)
                return ValidationFailure(is_valid=False, errors=[str(exc)])

    # ------------------------------------------------------------------
    # delete_agent_run_log (SESS-12)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def delete_agent_run_log(
        agent_run_log_id: int,
    ) -> GateViolation | NotFoundResponse | dict:
        """Delete an agent run log entry by ID.

        Gate-gated: removing audit trail entries is a prose-phase operation
        that requires gate certification. agent_run_log is an append-only
        audit log with no FK children — deletion uses the log-style pattern
        (no try/except needed for FK safety).

        Args:
            agent_run_log_id: Primary key of the agent_run_log row to delete.

        Returns:
            Dict with deleted=True and id on success. NotFoundResponse if the
            agent run log entry does not exist. GateViolation if the gate is
            not certified.
        """
        async with get_connection() as conn:
            violation = await check_gate(conn)
            if violation:
                return violation

            rows = await conn.execute_fetchall(
                "SELECT id FROM agent_run_log WHERE id = ?",
                (agent_run_log_id,),
            )
            if not rows:
                return NotFoundResponse(
                    not_found_message=f"Agent run log entry {agent_run_log_id} not found"
                )

            await conn.execute(
                "DELETE FROM agent_run_log WHERE id = ?", (agent_run_log_id,)
            )
            await conn.commit()
            return {"deleted": True, "id": agent_run_log_id}

    # ------------------------------------------------------------------
    # delete_open_question (SESS-13)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def delete_open_question(
        open_question_id: int,
    ) -> GateViolation | NotFoundResponse | dict:
        """Delete an open question by ID.

        Gate-gated: removing open questions is a prose-phase operation that
        requires gate certification. open_questions is an append-only log
        with no FK children — deletion uses the log-style pattern
        (no try/except needed for FK safety).

        Args:
            open_question_id: Primary key of the open_questions row to delete.

        Returns:
            Dict with deleted=True and id on success. NotFoundResponse if the
            open question does not exist. GateViolation if the gate is not
            certified.
        """
        async with get_connection() as conn:
            violation = await check_gate(conn)
            if violation:
                return violation

            rows = await conn.execute_fetchall(
                "SELECT id FROM open_questions WHERE id = ?",
                (open_question_id,),
            )
            if not rows:
                return NotFoundResponse(
                    not_found_message=f"Open question {open_question_id} not found"
                )

            await conn.execute(
                "DELETE FROM open_questions WHERE id = ?", (open_question_id,)
            )
            await conn.commit()
            return {"deleted": True, "id": open_question_id}

    # ------------------------------------------------------------------
    # delete_project_snapshot (SESS-14)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def delete_project_snapshot(
        snapshot_id: int,
    ) -> GateViolation | NotFoundResponse | dict:
        """Delete a project metrics snapshot by ID.

        Gate-gated: removing project snapshots is a prose-phase operation
        that requires gate certification. project_metrics_snapshots is a
        log-style table with no FK children — deletion uses the log-style
        pattern (no try/except needed for FK safety).

        Args:
            snapshot_id: Primary key of the project_metrics_snapshots row
                         to delete.

        Returns:
            Dict with deleted=True and id on success. NotFoundResponse if the
            snapshot does not exist. GateViolation if the gate is not certified.
        """
        async with get_connection() as conn:
            violation = await check_gate(conn)
            if violation:
                return violation

            rows = await conn.execute_fetchall(
                "SELECT id FROM project_metrics_snapshots WHERE id = ?",
                (snapshot_id,),
            )
            if not rows:
                return NotFoundResponse(
                    not_found_message=f"Project snapshot {snapshot_id} not found"
                )

            await conn.execute(
                "DELETE FROM project_metrics_snapshots WHERE id = ?", (snapshot_id,)
            )
            await conn.commit()
            return {"deleted": True, "id": snapshot_id}

    # ------------------------------------------------------------------
    # log_pov_balance_snapshot (SESS-15)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def log_pov_balance_snapshot(
        chapter_id: int | None = None,
        character_id: int | None = None,
        chapter_count: int = 0,
        word_count: int = 0,
    ) -> PovBalanceSnapshot | GateViolation | NotFoundResponse | ValidationFailure:
        """Append a POV balance snapshot entry to the log.

        Gate-gated: POV tracking is a prose-phase operation.

        Append-only INSERT — pov_balance_snapshots has no UNIQUE constraint
        beyond the primary key, so each call always inserts a new row.
        The snapshot_at timestamp is automatically set to the current time.

        Pre-checks that chapter_id exists in chapters if provided.

        Args:
            chapter_id: FK to chapters — the chapter context for this
                        snapshot (optional).
            character_id: FK to characters — the character whose POV balance
                          is being recorded (optional).
            chapter_count: Number of chapters from the character's POV
                           (default: 0).
            word_count: Total word count for this POV character (default: 0).

        Returns:
            The newly created PovBalanceSnapshot row.
            GateViolation if gate is not certified.
            NotFoundResponse if chapter_id does not exist.
            ValidationFailure on database error.
        """
        async with get_connection() as conn:
            violation = await check_gate(conn)
            if violation:
                return violation

            if chapter_id is not None:
                chapter = await conn.execute_fetchall(
                    "SELECT id FROM chapters WHERE id = ?", (chapter_id,)
                )
                if not chapter:
                    return NotFoundResponse(
                        not_found_message=f"Chapter {chapter_id} not found"
                    )

            try:
                cursor = await conn.execute(
                    "INSERT INTO pov_balance_snapshots "
                    "(chapter_id, character_id, chapter_count, word_count) "
                    "VALUES (?, ?, ?, ?)",
                    (chapter_id, character_id, chapter_count, word_count),
                )
                new_id = cursor.lastrowid
                await conn.commit()
                row = await conn.execute_fetchall(
                    "SELECT * FROM pov_balance_snapshots WHERE id = ?", (new_id,)
                )
                return PovBalanceSnapshot(**dict(row[0]))
            except Exception as exc:
                logger.error("log_pov_balance_snapshot failed: %s", exc)
                return ValidationFailure(is_valid=False, errors=[str(exc)])

    # ------------------------------------------------------------------
    # delete_pov_balance_snapshot (SESS-16)
    # ------------------------------------------------------------------

    @mcp.tool()
    async def delete_pov_balance_snapshot(
        snapshot_id: int,
    ) -> GateViolation | NotFoundResponse | dict:
        """Delete a POV balance snapshot entry by ID.

        Gate-gated: removing POV balance records is a prose-phase operation
        that requires gate certification. pov_balance_snapshots is a log-style
        table with no FK children — deletion uses the log-style pattern
        (no try/except needed for FK safety).

        Args:
            snapshot_id: Primary key of the pov_balance_snapshots row to
                         delete.

        Returns:
            {"deleted": True, "id": snapshot_id} on success.
            GateViolation if gate is not certified.
            NotFoundResponse if the snapshot does not exist.
        """
        async with get_connection() as conn:
            violation = await check_gate(conn)
            if violation:
                return violation

            rows = await conn.execute_fetchall(
                "SELECT id FROM pov_balance_snapshots WHERE id = ?", (snapshot_id,)
            )
            if not rows:
                return NotFoundResponse(
                    not_found_message=f"POV balance snapshot {snapshot_id} not found"
                )

            await conn.execute(
                "DELETE FROM pov_balance_snapshots WHERE id = ?", (snapshot_id,)
            )
            await conn.commit()
            return {"deleted": True, "id": snapshot_id}
