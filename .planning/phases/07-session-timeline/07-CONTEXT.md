# Phase 7: Session & Timeline - Context

**Gathered:** 2026-03-07
**Status:** Ready for planning

<domain>
## Phase Boundary

Session management (10 MCP tools: start/close sessions, agent run logging, project metrics, POV balance, open questions) and timeline management (8 MCP tools: POV positions, events, travel validation), plus server.py wiring for both modules. All 18 tools are prose-phase tools and call `check_gate()` at the top. No CLI subcommands in this phase — session and query CLI are Phase 10.

</domain>

<decisions>
## Implementation Decisions

### Session lifecycle behavior
- `start_session` checks for any unclosed session (WHERE `closed_at IS NULL`); if found, auto-closes it with `notes = "auto-closed by new session start"` before creating the new session row. Prevents orphaned sessions.
- Briefing content returned by `start_session`: the most recent closed session's `summary` + `carried_forward` list (from `session_logs` WHERE `closed_at IS NOT NULL` ORDER BY `started_at DESC LIMIT 1`). If no prior session exists, return the new session with a null briefing.
- `close_session` auto-populates `carried_forward` by querying `open_questions WHERE answered_at IS NULL` — serialized as JSON into `carried_forward` field. Accepts explicit `summary` and `word_count_delta` and `chapters_touched` from caller. Returns the closed `SessionLog`.
- `get_last_session` returns most recent row from `session_logs` ORDER BY `started_at DESC LIMIT 1` — `NotFoundResponse` if table is empty.

### Agent run logging
- `log_agent_run` is append-only INSERT (no ON CONFLICT) — audit trail, not upsertable. Takes `session_id` (optional), `agent_name`, `tool_name`, `input_summary`, `output_summary`, `duration_ms`, `success`, `error_message`. Returns inserted `AgentRunLog`.

### Project metrics — live computation
- `get_project_metrics` computes LIVE from DB: `SUM(chapters.word_count)` for word_count, `COUNT` from chapters/scenes/characters/session_logs tables. Does NOT read from `project_metrics_snapshots`. Always accurate; no stale data risk.
- Returns a `ProjectMetricsSnapshot` model (reusing existing model) populated from live queries.
- `log_project_snapshot` is a manual INSERT into `project_metrics_snapshots` — caller explicitly chooses when to snapshot (e.g., at session close). No auto-triggering.

### POV balance
- `get_pov_balance` computes live: for each distinct `pov_character_id` in chapters, return chapter count and SUM(word_count). Covers all chapters regardless of status.
- Returns a list of `PovBalanceSnapshot` records (reusing existing model) populated from aggregate query.

### Open questions
- `get_open_questions` returns all rows WHERE `answered_at IS NULL` by default; accepts optional `domain` filter. Ordered by `created_at ASC`.
- `log_open_question` is append-only INSERT — returns inserted `OpenQuestion`.
- `answer_open_question` UPDATE sets `answer` and `answered_at = now` on the row; returns updated `OpenQuestion` or `NotFoundResponse`.

### Travel validation — completeness + advisory
- `validate_travel_realism` takes a `travel_segment_id` (or `character_id` to get all segments for a character). Fetches the segment(s) from `travel_segments`, then checks:
  1. `elapsed_days` must be non-null and > 0
  2. `travel_method` must be non-null
  3. Advisory: if `travel_method = 'walking'` and `elapsed_days < 1`, flag as suspicious
  4. Advisory: if `from_location_id` or `to_location_id` is null, flag as incomplete
- No distance oracle (no reference table exists) — validates completeness and obvious inconsistencies.
- Returns a new `TravelValidationResult` model: `{ is_realistic: bool, issues: list[str], segment: TravelSegment | None }`.
- `TravelValidationResult` defined in `models/timeline.py` alongside existing timeline models.

### Timeline CRUD tools
- `get_pov_positions(chapter_id)` — returns list of all `PovChronologicalPosition` rows for that chapter.
- `get_pov_position(character_id, chapter_id)` — single row or `NotFoundResponse`.
- `get_event(event_id)` — single `Event` or `NotFoundResponse`.
- `list_events(chapter_id=None, start_chapter=None, end_chapter=None)` — accepts chapter range filter; returns list.
- `get_travel_segments(character_id)` — list of all segments for a character; empty list if none.
- `upsert_event` — None-id branch: INSERT + lastrowid; provided-id branch: ON CONFLICT(id) DO UPDATE.
- `upsert_pov_position` — ON CONFLICT(character_id, chapter_id) DO UPDATE (natural unique key).

### Plan split (3 plans)
- **07-01**: Core session tools — `start_session`, `close_session`, `get_last_session`, `log_agent_run`, `get_project_metrics`, `log_project_snapshot`, `get_pov_balance` (7 tools)
- **07-02**: Open questions + timeline reads — `get_open_questions`, `log_open_question`, `answer_open_question`, `get_pov_positions`, `get_pov_position`, `get_event`, `list_events`, `get_travel_segments` (8 tools)
- **07-03**: Timeline writes + validation + server wiring + all tests — `validate_travel_realism`, `upsert_event`, `upsert_pov_position` (3 tools) + `TravelValidationResult` model + `session.register(mcp)` / `timeline.register(mcp)` in server.py + in-memory FastMCP client tests for all 18 tools

### Claude's Discretion
- Exact SQL for all queries (joins, aggregates, CTEs)
- `TravelValidationResult` field order and exact validation logic
- conftest.py extension for session/timeline seed data
- Fixture scope for test DB (consistent with prior phases: per-test MCP session)
- Whether `list_events` uses a single query with nullable filters or branched queries

</decisions>

<specifics>
## Specific Ideas

No specific requirements — user delegated all implementation decisions to Claude. Follow established patterns from Phases 3–6.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `novel.models.sessions`: `SessionLog`, `AgentRunLog`, `ProjectMetricsSnapshot`, `PovBalanceSnapshot`, `OpenQuestion` — all defined, ready to use
- `novel.models.timeline`: `Event`, `TravelSegment`, `PovChronologicalPosition`, `EventParticipant`, `EventArtifact` — all defined; add `TravelValidationResult` here in Plan 01
- `novel.mcp.gate.check_gate(conn)` — import and call at top of every tool; returns `GateViolation | None`
- `novel.mcp.db.get_connection()` — async context manager; WAL + FK pragmas already set
- `novel.models.shared`: `NotFoundResponse`, `ValidationFailure`, `GateViolation` — error contract types
- `novel.db.seed.load_seed_profile("minimal")` — loads test data; conftest.py uses this for in-memory tests

### Established Patterns
- `register(mcp: FastMCP) -> None` with local async functions decorated with `@mcp.tool()`
- `check_gate()` first, before any DB read logic — return violation immediately if not None
- Error contract: `NotFoundResponse` for missing, `ValidationFailure` for bad input
- No `print()` — `logging.getLogger(__name__)` only
- Upsert pattern: None-id → INSERT + `cursor.lastrowid`; provided-id → ON CONFLICT(id) DO UPDATE
- Append-only pattern (no ON CONFLICT): agent run log, magic use log, arc health log
- JSON fields (like `carried_forward`, `chapters_touched` in SessionLog) use `to_db_dict()` for storage
- FastMCP serializes `list[T]` as N TextContent blocks — tests use `[json.loads(c.text) for c in result.content]`
- MCP session entered per-test (not per-fixture) — anyio cancel scope teardown incompatible with pytest-asyncio fixture lifecycle

### Integration Points
- `server.py`: add `from novel.tools import session, timeline; session.register(mcp); timeline.register(mcp)` in Plan 03
- Create `src/novel/tools/session.py` and `src/novel/tools/timeline.py` (new files, no existing module)
- `src/novel/models/timeline.py`: add `TravelValidationResult` model alongside existing timeline models
- `tests/`: add `test_session.py` and `test_timeline.py` in Plan 03

### Schema Notes (migrations 015, 019, 020, 021)
- `session_logs`: id, started_at, closed_at, summary, carried_forward (JSON TEXT), word_count_delta, chapters_touched (JSON TEXT), notes
- `agent_run_log`: id, session_id, agent_name, tool_name, input_summary, output_summary, duration_ms, success, error_message, ran_at
- `project_metrics_snapshots`: id, snapshot_at, word_count, chapter_count, scene_count, character_count, session_count, notes
- `pov_balance_snapshots`: id, snapshot_at, chapter_id, character_id, chapter_count, word_count
- `open_questions`: id, question, domain, session_id, answer, answered_at, priority, notes, created_at
- `events`: id, name, event_type, chapter_id, location_id, in_story_date, duration, summary, significance, notes, canon_status, created_at, updated_at
- `travel_segments`: id, character_id, from_location_id, to_location_id, start_chapter_id, end_chapter_id, start_event_id, elapsed_days, travel_method, notes, created_at
- `pov_chronological_position`: id, character_id, chapter_id, in_story_date, day_number, location_id, notes, created_at, updated_at (UNIQUE on character_id, chapter_id)

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 07-session-timeline*
*Context gathered: 2026-03-07*
