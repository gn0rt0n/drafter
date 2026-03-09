# Phase 7: Session & Timeline - Research

**Researched:** 2026-03-07
**Domain:** FastMCP tool authoring, aiosqlite, SQLite aggregate queries, session lifecycle patterns
**Confidence:** HIGH

## Summary

Phase 7 adds 18 MCP tools split across two new modules: `novel/tools/session.py` (10 tools: session lifecycle, agent run logging, metrics, POV balance, open questions) and `novel/tools/timeline.py` (8 tools: POV positions, events, travel segments, travel validation). All 18 tools are prose-phase tools that must call `check_gate()` at the top before any DB logic. The phase concludes with server.py wiring and a comprehensive in-memory test file.

All models are already defined in `novel.models.sessions` and `novel.models.timeline`. The only new model is `TravelValidationResult`, added to `timeline.py`. All established patterns from Phases 3-6 apply directly: `register(mcp)` pattern, `get_connection()` async context manager, `check_gate(conn)` call, append-only vs upsert branches, `cursor.lastrowid` for new rows, and per-test MCP session entry via `_call_tool`.

The session lifecycle presents one nuance: the seeded `session_logs` row has `closed_at IS NULL`, making it an open session. `start_session` will auto-close it and create a new row. Tests that expect a briefing must first have a closed session in the DB — the test for the briefing flow should therefore close the existing session first or use a separate fixture state.

**Primary recommendation:** Copy the arcs.py/gate.py module structure exactly. The only Phase 7-specific challenge is the `start_session` auto-close logic (two-step: close any open session, then insert new session + return briefing from the just-closed session). The travel validation is pure Python logic on top of a simple row fetch — no SQL complexity.

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Session lifecycle behavior**
- `start_session` checks for any unclosed session (`WHERE closed_at IS NULL`); if found, auto-closes it with `notes = "auto-closed by new session start"` before creating the new session row. Prevents orphaned sessions.
- Briefing content returned by `start_session`: the most recent closed session's `summary` + `carried_forward` list (from `session_logs WHERE closed_at IS NOT NULL ORDER BY started_at DESC LIMIT 1`). If no prior session exists, return the new session with a null briefing.
- `close_session` auto-populates `carried_forward` by querying `open_questions WHERE answered_at IS NULL` — serialized as JSON into `carried_forward` field. Accepts explicit `summary` and `word_count_delta` and `chapters_touched` from caller. Returns the closed `SessionLog`.
- `get_last_session` returns most recent row from `session_logs ORDER BY started_at DESC LIMIT 1` — `NotFoundResponse` if table is empty.

**Agent run logging**
- `log_agent_run` is append-only INSERT (no ON CONFLICT) — audit trail, not upsertable. Takes `session_id` (optional), `agent_name`, `tool_name`, `input_summary`, `output_summary`, `duration_ms`, `success`, `error_message`. Returns inserted `AgentRunLog`.

**Project metrics — live computation**
- `get_project_metrics` computes LIVE from DB: `SUM(chapters.word_count)` for word_count, `COUNT` from chapters/scenes/characters/session_logs tables. Does NOT read from `project_metrics_snapshots`. Always accurate; no stale data risk.
- Returns a `ProjectMetricsSnapshot` model (reusing existing model) populated from live queries.
- `log_project_snapshot` is a manual INSERT into `project_metrics_snapshots` — caller explicitly chooses when to snapshot. No auto-triggering.

**POV balance**
- `get_pov_balance` computes live: for each distinct `pov_character_id` in chapters, return chapter count and `SUM(word_count)`. Covers all chapters regardless of status.
- Returns a list of `PovBalanceSnapshot` records (reusing existing model) populated from aggregate query.

**Open questions**
- `get_open_questions` returns all rows `WHERE answered_at IS NULL` by default; accepts optional `domain` filter. Ordered by `created_at ASC`.
- `log_open_question` is append-only INSERT — returns inserted `OpenQuestion`.
- `answer_open_question` UPDATE sets `answer` and `answered_at = now` on the row; returns updated `OpenQuestion` or `NotFoundResponse`.

**Travel validation — completeness + advisory**
- `validate_travel_realism` takes a `travel_segment_id` (or `character_id` to get all segments for a character). Fetches the segment(s) from `travel_segments`, then checks:
  1. `elapsed_days` must be non-null and > 0
  2. `travel_method` must be non-null
  3. Advisory: if `travel_method = 'walking'` and `elapsed_days < 1`, flag as suspicious
  4. Advisory: if `from_location_id` or `to_location_id` is null, flag as incomplete
- No distance oracle. Returns `TravelValidationResult`: `{ is_realistic: bool, issues: list[str], segment: TravelSegment | None }`.
- `TravelValidationResult` defined in `models/timeline.py`.

**Timeline CRUD tools**
- `get_pov_positions(chapter_id)` — list of all `PovChronologicalPosition` rows for that chapter.
- `get_pov_position(character_id, chapter_id)` — single row or `NotFoundResponse`.
- `get_event(event_id)` — single `Event` or `NotFoundResponse`.
- `list_events(chapter_id=None, start_chapter=None, end_chapter=None)` — accepts chapter range filter; returns list.
- `get_travel_segments(character_id)` — list of all segments for a character; empty list if none.
- `upsert_event` — None-id branch: INSERT + lastrowid; provided-id branch: ON CONFLICT(id) DO UPDATE.
- `upsert_pov_position` — ON CONFLICT(character_id, chapter_id) DO UPDATE (natural unique key).

**Plan split (3 plans)**
- **07-01**: Core session tools — `start_session`, `close_session`, `get_last_session`, `log_agent_run`, `get_project_metrics`, `log_project_snapshot`, `get_pov_balance` (7 tools)
- **07-02**: Open questions + timeline reads — `get_open_questions`, `log_open_question`, `answer_open_question`, `get_pov_positions`, `get_pov_position`, `get_event`, `list_events`, `get_travel_segments` (8 tools)
- **07-03**: Timeline writes + validation + server wiring + all tests — `validate_travel_realism`, `upsert_event`, `upsert_pov_position` (3 tools) + `TravelValidationResult` model + `session.register(mcp)` / `timeline.register(mcp)` in server.py + in-memory FastMCP client tests for all 18 tools

### Claude's Discretion
- Exact SQL for all queries (joins, aggregates, CTEs)
- `TravelValidationResult` field order and exact validation logic
- conftest.py extension for session/timeline seed data
- Fixture scope for test DB (consistent with prior phases: per-test MCP session)
- Whether `list_events` uses a single query with nullable filters or branched queries

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| SESS-01 | Claude can start a new writing session with a briefing from the last session's log (`start_session`) | Two-step: auto-close open session, INSERT new session, SELECT most recent closed for briefing |
| SESS-02 | Claude can close the current session, logging a summary and carrying open items forward (`close_session`) | UPDATE session row, query open_questions for carried_forward JSON, return closed SessionLog |
| SESS-03 | Claude can retrieve the most recent session log (`get_last_session`) | SELECT ORDER BY started_at DESC LIMIT 1, NotFoundResponse if empty |
| SESS-04 | Claude can log an agent run record (`log_agent_run`) | Append-only INSERT, no ON CONFLICT, return AgentRunLog via lastrowid |
| SESS-05 | Claude can retrieve project-level metrics (`get_project_metrics`) | Live aggregate: SUM(chapters.word_count), COUNT of chapters/scenes/characters/sessions |
| SESS-06 | Claude can log a project metrics snapshot (`log_project_snapshot`) | Manual INSERT into project_metrics_snapshots, return new row |
| SESS-07 | Claude can retrieve POV balance (`get_pov_balance`) | Live GROUP BY pov_character_id, COUNT + SUM(word_count) |
| SESS-08 | Claude can retrieve open questions (`get_open_questions`) | SELECT WHERE answered_at IS NULL, optional domain filter |
| SESS-09 | Claude can log a new open question (`log_open_question`) | Append-only INSERT, return OpenQuestion |
| SESS-10 | Claude can mark an open question as answered (`answer_open_question`) | UPDATE answer + answered_at=now, NotFoundResponse if missing |
| TIME-01 | Claude can retrieve all POV character positions at a given chapter (`get_pov_positions`) | SELECT WHERE chapter_id=?, list result |
| TIME-02 | Claude can retrieve a specific POV character's chronological position (`get_pov_position`) | SELECT WHERE character_id=? AND chapter_id=?, NotFoundResponse |
| TIME-03 | Claude can retrieve a timeline event by ID (`get_event`) | SELECT WHERE id=?, NotFoundResponse |
| TIME-04 | Claude can list events within a chapter range or time range (`list_events`) | Nullable filter query on chapter_id or chapter range |
| TIME-05 | Claude can retrieve travel segments for a character (`get_travel_segments`) | SELECT WHERE character_id=?, return list (empty if none) |
| TIME-06 | Claude can validate whether travel is realistic (`validate_travel_realism`) | Fetch segment(s), apply Python logic, return TravelValidationResult |
| TIME-07 | Claude can create or update a timeline event (`upsert_event`) | Two-branch: None-id INSERT+lastrowid, provided-id ON CONFLICT(id) DO UPDATE |
| TIME-08 | Claude can create or update a POV chronological position (`upsert_pov_position`) | ON CONFLICT(character_id, chapter_id) DO UPDATE |
</phase_requirements>

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `mcp.server.fastmcp` | bundled with `mcp>=1.26.0,<2.0.0` | FastMCP server, tool registration | Established in Phase 3; standalone fastmcp diverged |
| `aiosqlite` | project pinned | Async SQLite for all MCP tool DB access | WAL mode + async tool handlers require it |
| `pydantic` | `>=2.11` | Model validation, JSON serialization | Established Phase 2 — all models use BaseModel |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `sqlite3` (stdlib) | stdlib | Test fixture DB setup only | Seed/migrate in test conftest — sync operations |
| `logging` | stdlib | All output in MCP server code | Never use print() — corrupts stdio protocol |
| `json` (stdlib) | stdlib | Encode/decode JSON TEXT fields | `carried_forward` and `chapters_touched` in SessionLog |
| `datetime` (stdlib) | stdlib | Timestamps for answered_at, now() | `datetime.now(timezone.utc).isoformat()` |

### No New Dependencies
Phase 7 requires zero new packages. All tools use existing stack.

**Existing imports for Phase 7 tools:**
```python
import logging
import json
from datetime import datetime, timezone
from mcp.server.fastmcp import FastMCP
from novel.mcp.db import get_connection
from novel.mcp.gate import check_gate
from novel.models.sessions import (
    SessionLog, AgentRunLog, ProjectMetricsSnapshot, PovBalanceSnapshot, OpenQuestion
)
from novel.models.timeline import (
    Event, TravelSegment, PovChronologicalPosition, TravelValidationResult
)
from novel.models.shared import NotFoundResponse, ValidationFailure, GateViolation
```

## Architecture Patterns

### Recommended File Structure
```
src/novel/
├── tools/
│   ├── session.py       # NEW: 10 session domain tools
│   └── timeline.py      # NEW: 8 timeline domain tools
├── models/
│   └── timeline.py      # EXTEND: add TravelValidationResult class
└── mcp/
    └── server.py        # EXTEND: import + register session, timeline

tests/
├── test_session.py      # NEW: in-memory tests for all 10 session tools
└── test_timeline.py     # NEW: in-memory tests for all 8 timeline tools
```

### Pattern 1: Prose-Phase Tool Module Structure

Every Phase 7 tool module follows this exact structure:

```python
"""[Domain] domain MCP tools.
...
IMPORTANT: Never use the print function in this module. All logging goes to
stderr via the logging module — using print corrupts the stdio protocol.
"""
import logging
from datetime import datetime, timezone

from mcp.server.fastmcp import FastMCP

from novel.mcp.db import get_connection
from novel.mcp.gate import check_gate
from novel.models.[domain] import [ModelClasses]
from novel.models.shared import NotFoundResponse, ValidationFailure, GateViolation

logger = logging.getLogger(__name__)


def register(mcp: FastMCP) -> None:
    """Register all N [domain] tools with the given FastMCP instance."""

    @mcp.tool()
    async def tool_name(arg1: type, arg2: type | None = None) -> ReturnType | GateViolation:
        """Docstring describing tool behavior.

        Args:
            arg1: description
            arg2: description (optional)

        Returns:
            ReturnType on success, GateViolation if gate not certified.
        """
        async with get_connection() as conn:
            violation = await check_gate(conn)
            if violation:
                return violation
            # ... tool logic
```

**Source:** Established pattern from `novel/mcp/gate.py` documentation and prior phase conventions.

### Pattern 2: start_session Two-Step Logic

The most complex tool in Phase 7. The logic sequence:

```python
@mcp.tool()
async def start_session() -> SessionLog | GateViolation:
    async with get_connection() as conn:
        violation = await check_gate(conn)
        if violation:
            return violation

        # Step 1: Find any open session (closed_at IS NULL)
        open_rows = await conn.execute_fetchall(
            "SELECT * FROM session_logs WHERE closed_at IS NULL ORDER BY started_at DESC LIMIT 1"
        )
        if open_rows:
            # Auto-close it
            await conn.execute(
                "UPDATE session_logs SET closed_at = datetime('now'), "
                "notes = 'auto-closed by new session start' WHERE id = ?",
                (open_rows[0]["id"],)
            )
            await conn.commit()

        # Step 2: Get briefing from the most recent closed session
        closed_rows = await conn.execute_fetchall(
            "SELECT * FROM session_logs WHERE closed_at IS NOT NULL "
            "ORDER BY started_at DESC LIMIT 1"
        )
        prior_session = SessionLog(**dict(closed_rows[0])) if closed_rows else None

        # Step 3: Insert new session
        cursor = await conn.execute("INSERT INTO session_logs DEFAULT VALUES")
        new_id = cursor.lastrowid
        await conn.commit()

        # Step 4: Return new session with briefing context
        new_rows = await conn.execute_fetchall(
            "SELECT * FROM session_logs WHERE id = ?", (new_id,)
        )
        new_session = SessionLog(**dict(new_rows[0]))
        # Attach briefing fields from prior_session
        # (return as dict or extend SessionLog model with optional briefing fields)
        ...
```

**Key insight on briefing return:** The CONTEXT.md says "return the new session with a null briefing" if no prior session exists. The tool must return something that includes both the new `SessionLog` AND the briefing context. Options at Claude's discretion: return a dict, or define a thin `SessionBriefing` wrapper model. A plain dict is simplest given the tooling.

### Pattern 3: close_session with Auto-Populated carried_forward

```python
@mcp.tool()
async def close_session(
    session_id: int,
    summary: str | None = None,
    word_count_delta: int = 0,
    chapters_touched: list[int] | None = None,
) -> SessionLog | NotFoundResponse | GateViolation:
    async with get_connection() as conn:
        violation = await check_gate(conn)
        if violation:
            return violation

        # Verify session exists and is open
        rows = await conn.execute_fetchall(
            "SELECT * FROM session_logs WHERE id = ? AND closed_at IS NULL", (session_id,)
        )
        if not rows:
            return NotFoundResponse(not_found_message=f"Open session {session_id} not found")

        # Auto-populate carried_forward from unanswered open questions
        oq_rows = await conn.execute_fetchall(
            "SELECT question FROM open_questions WHERE answered_at IS NULL ORDER BY created_at ASC"
        )
        carried = [r["question"] for r in oq_rows]

        import json
        await conn.execute(
            """UPDATE session_logs SET
                   closed_at = datetime('now'),
                   summary = COALESCE(?, summary),
                   word_count_delta = ?,
                   chapters_touched = ?,
                   carried_forward = ?
               WHERE id = ?""",
            (summary, word_count_delta,
             json.dumps(chapters_touched) if chapters_touched else None,
             json.dumps(carried),
             session_id)
        )
        await conn.commit()
        updated = await conn.execute_fetchall(
            "SELECT * FROM session_logs WHERE id = ?", (session_id,)
        )
        return SessionLog(**dict(updated[0]))
```

### Pattern 4: get_project_metrics Live Aggregate

```python
@mcp.tool()
async def get_project_metrics() -> ProjectMetricsSnapshot | GateViolation:
    async with get_connection() as conn:
        violation = await check_gate(conn)
        if violation:
            return violation

        wc_row = await conn.execute_fetchall(
            "SELECT COALESCE(SUM(word_count), 0) AS word_count FROM chapters"
        )
        ch_row = await conn.execute_fetchall("SELECT COUNT(*) AS cnt FROM chapters")
        sc_row = await conn.execute_fetchall("SELECT COUNT(*) AS cnt FROM scenes")
        char_row = await conn.execute_fetchall("SELECT COUNT(*) AS cnt FROM characters")
        sess_row = await conn.execute_fetchall("SELECT COUNT(*) AS cnt FROM session_logs")

        return ProjectMetricsSnapshot(
            word_count=wc_row[0]["word_count"],
            chapter_count=ch_row[0]["cnt"],
            scene_count=sc_row[0]["cnt"],
            character_count=char_row[0]["cnt"],
            session_count=sess_row[0]["cnt"],
        )
```

### Pattern 5: get_pov_balance Live Aggregate

```python
@mcp.tool()
async def get_pov_balance() -> list[PovBalanceSnapshot] | GateViolation:
    async with get_connection() as conn:
        violation = await check_gate(conn)
        if violation:
            return violation

        rows = await conn.execute_fetchall(
            """SELECT pov_character_id AS character_id,
                      COUNT(*) AS chapter_count,
                      COALESCE(SUM(word_count), 0) AS word_count
               FROM chapters
               WHERE pov_character_id IS NOT NULL
               GROUP BY pov_character_id
               ORDER BY chapter_count DESC"""
        )
        return [
            PovBalanceSnapshot(character_id=r["character_id"],
                               chapter_count=r["chapter_count"],
                               word_count=r["word_count"])
            for r in rows
        ]
```

**Note:** `PovBalanceSnapshot` has `id`, `snapshot_at`, `chapter_id`, `character_id`, `chapter_count`, `word_count` fields. When constructing from a live query (not from the `pov_balance_snapshots` table), `id` and `snapshot_at` will be None — that is correct and expected behavior per the locked decision.

### Pattern 6: TravelValidationResult Model and validate_travel_realism

New model to add to `models/timeline.py`:

```python
class TravelValidationResult(BaseModel):
    """Result of validating a travel segment's realism."""

    is_realistic: bool
    issues: list[str]
    segment: TravelSegment | None = None
```

Tool logic (purely Python after DB fetch):

```python
@mcp.tool()
async def validate_travel_realism(
    travel_segment_id: int | None = None,
    character_id: int | None = None,
) -> TravelValidationResult | list[TravelValidationResult] | ValidationFailure | GateViolation:
    async with get_connection() as conn:
        violation = await check_gate(conn)
        if violation:
            return violation

        if travel_segment_id is not None:
            rows = await conn.execute_fetchall(
                "SELECT * FROM travel_segments WHERE id = ?", (travel_segment_id,)
            )
        elif character_id is not None:
            rows = await conn.execute_fetchall(
                "SELECT * FROM travel_segments WHERE character_id = ? ORDER BY id",
                (character_id,)
            )
        else:
            return ValidationFailure(
                is_valid=False,
                errors=["Either travel_segment_id or character_id must be provided"]
            )

    results = []
    for row in rows:
        seg = TravelSegment(**dict(row))
        issues: list[str] = []

        if seg.elapsed_days is None or seg.elapsed_days <= 0:
            issues.append("elapsed_days must be non-null and > 0")
        if seg.travel_method is None:
            issues.append("travel_method must be non-null")
        if seg.travel_method == "walking" and seg.elapsed_days is not None and seg.elapsed_days < 1:
            issues.append("suspicious: walking travel with elapsed_days < 1")
        if seg.from_location_id is None or seg.to_location_id is None:
            issues.append("incomplete: from_location_id or to_location_id is null")

        results.append(TravelValidationResult(
            is_realistic=len(issues) == 0,
            issues=issues,
            segment=seg,
        ))

    # Single-segment path: return single result
    if travel_segment_id is not None:
        return results[0] if results else TravelValidationResult(
            is_realistic=False,
            issues=["travel_segment_id not found"],
            segment=None,
        )
    return results
```

### Pattern 7: upsert_pov_position with Natural Unique Key

```python
@mcp.tool()
async def upsert_pov_position(
    character_id: int,
    chapter_id: int,
    in_story_date: str | None = None,
    day_number: int | None = None,
    location_id: int | None = None,
    notes: str | None = None,
) -> PovChronologicalPosition | ValidationFailure | GateViolation:
    async with get_connection() as conn:
        violation = await check_gate(conn)
        if violation:
            return violation
        try:
            await conn.execute(
                """INSERT INTO pov_chronological_position
                       (character_id, chapter_id, in_story_date, day_number,
                        location_id, notes, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
                   ON CONFLICT(character_id, chapter_id) DO UPDATE SET
                       in_story_date = excluded.in_story_date,
                       day_number = excluded.day_number,
                       location_id = excluded.location_id,
                       notes = excluded.notes,
                       updated_at = datetime('now')""",
                (character_id, chapter_id, in_story_date, day_number, location_id, notes)
            )
            await conn.commit()
            rows = await conn.execute_fetchall(
                "SELECT * FROM pov_chronological_position "
                "WHERE character_id = ? AND chapter_id = ?",
                (character_id, chapter_id)
            )
            return PovChronologicalPosition(**dict(rows[0]))
        except Exception as exc:
            logger.error("upsert_pov_position failed: %s", exc)
            return ValidationFailure(is_valid=False, errors=[str(exc)])
```

### Pattern 8: list_events Nullable Filter

```python
@mcp.tool()
async def list_events(
    chapter_id: int | None = None,
    start_chapter: int | None = None,
    end_chapter: int | None = None,
) -> list[Event] | GateViolation:
    async with get_connection() as conn:
        violation = await check_gate(conn)
        if violation:
            return violation

        if chapter_id is not None:
            rows = await conn.execute_fetchall(
                "SELECT * FROM events WHERE chapter_id = ? ORDER BY id",
                (chapter_id,)
            )
        elif start_chapter is not None or end_chapter is not None:
            rows = await conn.execute_fetchall(
                "SELECT * FROM events WHERE "
                "(? IS NULL OR chapter_id >= ?) AND (? IS NULL OR chapter_id <= ?) "
                "ORDER BY chapter_id, id",
                (start_chapter, start_chapter, end_chapter, end_chapter)
            )
        else:
            rows = await conn.execute_fetchall("SELECT * FROM events ORDER BY id")

        return [Event(**dict(r)) for r in rows]
```

### Pattern 9: Server Wiring (Plan 07-03)

```python
# server.py additions (Phase 7)
from novel.tools import session, timeline

# After Phase 6 gate registration:
session.register(mcp)
timeline.register(mcp)
```

### Pattern 10: Test File Structure (Plan 07-03)

Tests use `gate_ready` seed (not `minimal`) because prose-phase tools call `check_gate()` and return `GateViolation` when gate is not certified.

```python
"""In-memory MCP client tests for session domain tools.

Uses gate_ready seed — session tools call check_gate() and require a certified gate.
After loading gate_ready seed, run_gate_audit() must be called to certify,
OR the test DB must have is_certified=1 set directly.

FastMCP serialization:
  - Single object: json.loads(result.content[0].text)
  - list[T]: [json.loads(c.text) for c in result.content]
"""
import json
import os
import sqlite3

import pytest
from mcp.shared.memory import create_connected_server_and_client_session

from novel.db.migrations import apply_migrations
from novel.db.seed import load_seed_profile
from novel.mcp.server import mcp


@pytest.fixture(scope="session")
def test_db_path(tmp_path_factory):
    db_file = tmp_path_factory.mktemp("session_db") / "test_session.db"
    conn = sqlite3.connect(str(db_file))
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA journal_mode=WAL")
    apply_migrations(conn)
    load_seed_profile(conn, "gate_ready")
    conn.commit()
    conn.close()
    return str(db_file)


async def _call_tool(db_path: str, tool_name: str, args: dict):
    os.environ["NOVEL_DB_PATH"] = db_path
    async with create_connected_server_and_client_session(mcp) as session:
        return await session.call_tool(tool_name, args)
```

**Gate certification for prose-phase tests:** The `gate_ready` seed does NOT set `is_certified=1`. Tests must run `certify_gate` (after `run_gate_audit`) before calling prose-phase tools, OR set the gate certified directly via raw SQL in the fixture. The cleanest approach (from Phase 6 test pattern) is to use the MCP tools themselves: call `run_gate_audit`, update `min_characters`, then `certify_gate` as a module-level setup step.

### Anti-Patterns to Avoid

- **Using `print()` anywhere in tools/session.py or tools/timeline.py:** corrupts stdio protocol; use `logger.debug/info/error` instead.
- **Reading from `project_metrics_snapshots` in `get_project_metrics`:** The locked decision is live computation. Do not read from the snapshot table.
- **Setting `closed_at` to a Python datetime string vs SQLite's `datetime('now')`:** Use `datetime('now')` in SQL to keep timestamps in UTC SQLite format consistent with all other timestamps in the DB.
- **Calling `check_gate()` after DB reads:** Always call check_gate as the FIRST thing inside the `async with get_connection()` block, before any other SQL. Return immediately if violated.
- **Using INSERT OR REPLACE for upsert_pov_position:** The `pov_chronological_position` table has UNIQUE(character_id, chapter_id) constraint; use ON CONFLICT DO UPDATE to avoid deleting and reinserting (which would reset `created_at`).
- **Entering MCP session in a pytest fixture:** anyio cancel scope is incompatible with pytest-asyncio fixture lifecycle. Always enter inside `_call_tool` per-test helper.
- **Using `minimal` seed for prose-phase tool tests:** Prose-phase tools call `check_gate()`. The `gate_ready` seed must be used, and the gate must be certified before tool calls succeed.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| JSON encode/decode for list fields | Custom serializer | `json.dumps()` / `json.loads()` + Pydantic field_validator | Already implemented in `SessionLog.to_db_dict()` and validators |
| Gate enforcement | Custom auth/state check | `check_gate(conn)` from `novel.mcp.gate` | Shared, tested, single point of change |
| DB connection setup | Custom connection factory | `get_connection()` from `novel.mcp.db` | WAL + FK pragmas always applied |
| Model-to-dict for INSERT | Manual dict building | `model.model_dump()` or `model.to_db_dict()` for JSON-field models | Pydantic handles field mapping |
| Travel distance lookup | Custom distance table/oracle | Advisory-only logic on `elapsed_days` | No reference data exists; completeness + obvious inconsistency is the scope |

**Key insight:** All infrastructure (connection, gate, models, error contract) is built. Phase 7 is purely tool authoring on top of the existing stack.

## Common Pitfalls

### Pitfall 1: start_session Briefing Race Condition
**What goes wrong:** Inserting the new session before closing the old one — the old session is in an open state when you query for "most recent closed" and returns nothing, so briefing is null when it shouldn't be.
**Why it happens:** Wrong operation order.
**How to avoid:** Sequence strictly: (1) find open session, (2) close it, (3) query closed sessions for briefing, (4) insert new session. Commit after step 2 before querying in step 3.
**Warning signs:** Test for "briefing from prior session" shows null briefing when a prior closed session should exist.

### Pitfall 2: PovBalanceSnapshot Populated Without id/snapshot_at
**What goes wrong:** Pydantic validation error because the model expects `id` and `snapshot_at` fields (defined in the model with defaults of `None` and `None`).
**Why it happens:** `get_pov_balance` constructs the model from a live GROUP BY query, not from the `pov_balance_snapshots` table rows. Both `id` and `snapshot_at` default to `None`.
**How to avoid:** Check `PovBalanceSnapshot` definition — `id: int | None = None` and `snapshot_at: str | None = None` — both already nullable, no action needed. Just construct the model without those fields.
**Warning signs:** Pydantic `ValidationError` on `PovBalanceSnapshot` construction.

### Pitfall 3: Gate Not Certified When Testing Prose-Phase Tools
**What goes wrong:** Test calls `start_session` and receives `{"requires_action": "..."}` instead of a `SessionLog` — every prose-phase tool returns GateViolation when gate uncertified.
**Why it happens:** `gate_ready` seed sets `is_certified=0`. Tests use `minimal` seed (which also has `is_certified=0`).
**How to avoid:** Use `gate_ready` seed AND certify the gate in test setup (call `run_gate_audit` + `certify_gate` via MCP tools in a session-scoped setup step, or set `is_certified=1` directly via raw SQL in fixture).
**Warning signs:** All prose-phase tool tests return dicts with `requires_action` key.

### Pitfall 4: open_questions answered_at IS NULL vs IS NOT NULL Filter
**What goes wrong:** `get_open_questions` returns all questions (including answered ones) or `close_session` includes already-answered questions in `carried_forward`.
**Why it happens:** Missing `WHERE answered_at IS NULL` filter.
**How to avoid:** Both `get_open_questions` (default) and `close_session` carried_forward query must include `WHERE answered_at IS NULL`.
**Warning signs:** `close_session` returns answered questions in `carried_forward` list.

### Pitfall 5: travel_segments Seed Row Has NULL elapsed_days
**What goes wrong:** `validate_travel_realism` test on the seeded travel segment finds `elapsed_days IS NULL` → `is_realistic=False` when test might expect `True`.
**Why it happens:** The minimal seed inserts a travel segment with only `travel_method='foot'`, no `elapsed_days`.
**How to avoid:** Insert fresh test data in the test (raw SQL before calling the tool), or use a travel_segment_id that corresponds to a row with all fields populated.
**Warning signs:** `test_validate_travel_realism` fails with unexpected `is_realistic=False`.

### Pitfall 6: list_events Nullable Filter SQL
**What goes wrong:** `(? IS NULL OR chapter_id >= ?)` requires binding the same parameter twice. Passing `(start_chapter, start_chapter, end_chapter, end_chapter)` correctly doubles the params.
**Why it happens:** SQLite doesn't support named params via aiosqlite's `execute_fetchall` in the same way — positional params must be repeated.
**How to avoid:** Double the params tuple for nullable WHERE clauses, or use branched queries (one branch per filter combination). The branched approach is simpler to reason about.
**Warning signs:** `sqlite3.ProgrammingError: Binding N has no value` on list_events calls.

### Pitfall 7: Seeded session_logs Row is OPEN (closed_at IS NULL)
**What goes wrong:** Tests for `get_last_session` get an open session back, but tests for `start_session` auto-close logic are confused because there's already an open session from seed.
**Why it happens:** The minimal/gate_ready seed inserts a session_log without setting `closed_at`, so it defaults to NULL.
**How to avoid:** Tests for `start_session` should expect the auto-close behavior to trigger. Tests for `close_session` can use the existing open session (id=1). Tests for briefing flow need to first close the seeded session, then start a new one to see the briefing populated.
**Warning signs:** `close_session` test fails with "NotFoundResponse" if the test is calling with wrong session_id.

## Code Examples

### check_gate Import and Usage (established pattern)
```python
# Source: src/novel/mcp/gate.py (check_gate helper) + CONTEXT.md code_context
from novel.mcp.gate import check_gate

async with get_connection() as conn:
    violation = await check_gate(conn)
    if violation:
        return violation
    # ... proceed with tool logic
```

### SessionLog JSON field handling (established pattern from models/sessions.py)
```python
# Source: src/novel/models/sessions.py
# SessionLog has to_db_dict() for JSON field encoding:
session = SessionLog(
    carried_forward=["item 1", "item 2"],
    chapters_touched=[1, 2, 3],
)
db_dict = session.to_db_dict()
# db_dict["carried_forward"] == '["item 1", "item 2"]'  (JSON string)
# db_dict["chapters_touched"] == '[1, 2, 3]'            (JSON string)

# Reading back: field_validators auto-parse JSON string → list
row = {"carried_forward": '["item 1"]', "chapters_touched": "[1]", ...}
session = SessionLog(**row)
# session.carried_forward == ["item 1"]  (list)
```

### Append-only INSERT returning new row
```python
# Source: established in Phase 3 (characters), Phase 5 (arc_health_log)
cursor = await conn.execute(
    "INSERT INTO agent_run_log (session_id, agent_name, ...) VALUES (?, ?, ...)",
    (session_id, agent_name, ...)
)
new_id = cursor.lastrowid
await conn.commit()
row = await conn.execute_fetchall(
    "SELECT * FROM agent_run_log WHERE id = ?", (new_id,)
)
return AgentRunLog(**dict(row[0]))
```

### FastMCP list[T] serialization in tests
```python
# Source: test_gate.py, test_arcs.py — established Phase 3, 6 pattern
# list[T] serializes as N TextContent blocks (one per item)
result = await _call_tool(db_path, "get_open_questions", {})
questions = [json.loads(c.text) for c in result.content]

# Single object serializes as 1 TextContent block
result = await _call_tool(db_path, "get_last_session", {})
session_data = json.loads(result.content[0].text)
```

### ON CONFLICT DO UPDATE (upsert pattern for tables with FK children)
```python
# Source: Phase 3 decision log, Phase 4 decisions
await conn.execute(
    """INSERT INTO events (id, name, event_type, ...)
           VALUES (?, ?, ?, ...)
           ON CONFLICT(id) DO UPDATE SET
               name=excluded.name,
               event_type=excluded.event_type,
               ...
               updated_at=datetime('now')""",
    (event_id, name, event_type, ...)
)
```

## Schema Reference (Confirmed from Migrations)

### session_logs (migration 019)
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK AUTOINCREMENT | |
| started_at | TEXT NOT NULL DEFAULT datetime('now') | |
| closed_at | TEXT | NULL = open session |
| summary | TEXT | |
| carried_forward | TEXT | JSON array of strings |
| word_count_delta | INTEGER NOT NULL DEFAULT 0 | |
| chapters_touched | TEXT | JSON array of ints |
| notes | TEXT | |

### agent_run_log (migration 019)
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK AUTOINCREMENT | |
| session_id | INTEGER REFERENCES session_logs(id) | nullable |
| agent_name | TEXT NOT NULL | |
| tool_name | TEXT | nullable |
| input_summary | TEXT | nullable |
| output_summary | TEXT | nullable |
| duration_ms | INTEGER | nullable |
| success | INTEGER NOT NULL DEFAULT 1 | coerce to bool via field_validator |
| error_message | TEXT | nullable |
| ran_at | TEXT NOT NULL DEFAULT datetime('now') | |

### project_metrics_snapshots (migration 020)
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK AUTOINCREMENT | |
| snapshot_at | TEXT NOT NULL DEFAULT datetime('now') | |
| word_count | INTEGER NOT NULL DEFAULT 0 | |
| chapter_count | INTEGER NOT NULL DEFAULT 0 | |
| scene_count | INTEGER NOT NULL DEFAULT 0 | |
| character_count | INTEGER NOT NULL DEFAULT 0 | |
| session_count | INTEGER NOT NULL DEFAULT 0 | |
| notes | TEXT | |

### open_questions (migration 021)
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK AUTOINCREMENT | |
| question | TEXT NOT NULL | |
| domain | TEXT NOT NULL DEFAULT 'general' | |
| session_id | INTEGER REFERENCES session_logs(id) | nullable |
| answer | TEXT | nullable; NULL = open |
| answered_at | TEXT | nullable; NULL = open |
| priority | TEXT NOT NULL DEFAULT 'normal' | |
| notes | TEXT | |
| created_at | TEXT NOT NULL DEFAULT datetime('now') | |

### events (migration 015)
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK AUTOINCREMENT | |
| name | TEXT NOT NULL | |
| event_type | TEXT NOT NULL DEFAULT 'plot' | |
| chapter_id | INTEGER REFERENCES chapters(id) | nullable |
| location_id | INTEGER REFERENCES locations(id) | nullable |
| in_story_date | TEXT | nullable |
| duration | TEXT | nullable |
| summary | TEXT | nullable |
| significance | TEXT | nullable |
| notes | TEXT | nullable |
| canon_status | TEXT NOT NULL DEFAULT 'draft' | |
| created_at | TEXT NOT NULL DEFAULT datetime('now') | |
| updated_at | TEXT NOT NULL DEFAULT datetime('now') | |

### travel_segments (migration 015)
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK AUTOINCREMENT | |
| character_id | INTEGER NOT NULL REFERENCES characters(id) | |
| from_location_id | INTEGER REFERENCES locations(id) | nullable |
| to_location_id | INTEGER REFERENCES locations(id) | nullable |
| start_chapter_id | INTEGER REFERENCES chapters(id) | nullable |
| end_chapter_id | INTEGER REFERENCES chapters(id) | nullable |
| start_event_id | INTEGER REFERENCES events(id) | nullable |
| elapsed_days | INTEGER | nullable — key validation field |
| travel_method | TEXT | nullable — key validation field |
| notes | TEXT | nullable |
| created_at | TEXT NOT NULL DEFAULT datetime('now') | |

### pov_chronological_position (migration 015)
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK AUTOINCREMENT | |
| character_id | INTEGER NOT NULL REFERENCES characters(id) | |
| chapter_id | INTEGER NOT NULL REFERENCES chapters(id) | |
| in_story_date | TEXT | nullable |
| day_number | INTEGER | nullable |
| location_id | INTEGER REFERENCES locations(id) | nullable |
| notes | TEXT | nullable |
| created_at | TEXT NOT NULL DEFAULT datetime('now') | |
| updated_at | TEXT NOT NULL DEFAULT datetime('now') | |
| UNIQUE | (character_id, chapter_id) | natural key for upsert |

## Seed Data Reference for Tests

The `gate_ready` seed provides:
- **session_logs**: 1 row (id=1), `closed_at IS NULL` (open session), word_count_delta=1800
- **agent_run_log**: 1 row (id=1), session_id=1, agent_name="ContextAgent"
- **project_metrics_snapshots**: 1 row (word_count=1800, chapter_count=3, scene_count=6, character_count=5, session_count=1)
- **open_questions**: 1 row (id=1), domain="plot", priority="high", answered_at IS NULL
- **events**: 1 row (id=1), name="The Final Ember Watch", chapter_id=1
- **pov_chronological_position**: 1 row, character_id=1 (Aeryn), chapter_id=1
- **travel_segments**: 1 row, character_id=1, travel_method="foot", elapsed_days IS NULL (incomplete — good test case for validation failure)
- **architecture_gate**: id=1, is_certified=0 — must be certified before prose-phase tools work

Test constants derived from seed (to put in test file headers):
```
SESSION_ID = 1         # open session from seed
OPEN_QUESTION_ID = 1   # unanswered question, domain="plot"
EVENT_ID = 1           # "The Final Ember Watch", chapter_id=1
CHARACTER_ID = 1       # Aeryn Vael (protagonist)
CHAPTER_ID = 1         # first chapter
TRAVEL_SEGMENT_ID = 1  # elapsed_days=NULL → validation fails
NOT_FOUND_ID = 9999
```

## Open Questions

1. **start_session return type for briefing**
   - What we know: Must return new SessionLog + optional briefing context from prior session
   - What's unclear: Whether to add briefing fields to SessionLog, use a dict, or define a new model
   - Recommendation: Return a dict with `session: {...}` and `briefing: {...} | None` — matches what Claude actually needs to use from the tool and avoids extending the Pydantic model with non-persisted fields

2. **close_session session_id parameter**
   - What we know: The tool needs to know which session to close
   - What's unclear: Whether `session_id` should default to "the open session" (auto-detect) or require explicit ID
   - Recommendation: Accept explicit `session_id` for clarity. If the caller doesn't know the ID, they can call `get_last_session` first. This keeps the tool simple and predictable.

3. **validate_travel_realism when character_id returns empty list**
   - What we know: `get_travel_segments` returns empty list for no segments
   - What's unclear: What `validate_travel_realism(character_id=X)` should return when no segments exist
   - Recommendation: Return empty list `[]` (consistent with how list tools handle no results)

## Sources

### Primary (HIGH confidence)
- Direct code inspection of `src/novel/mcp/gate.py` — tool module structure, check_gate pattern
- Direct code inspection of `src/novel/mcp/gate.py` (check_gate helper) — exact check_gate API
- Direct code inspection of `src/novel/models/sessions.py` — all session model fields and validators
- Direct code inspection of `src/novel/models/timeline.py` — all timeline model fields
- Direct code inspection of `src/novel/models/shared.py` — error contract types
- Direct code inspection of `src/novel/migrations/015_events_timeline.sql` — exact schema
- Direct code inspection of `src/novel/migrations/019_sessions.sql` — exact schema
- Direct code inspection of `src/novel/migrations/020_gate_metrics.sql` — exact schema
- Direct code inspection of `src/novel/migrations/021_literary_publishing.sql` lines 261-271 — open_questions schema
- Direct code inspection of `src/novel/db/seed.py` lines 380-592 — seed data for timeline, sessions, questions
- Direct code inspection of `tests/test_gate.py` — gate_ready seed test pattern
- Direct code inspection of `tests/test_arcs.py` — per-test MCP session via _call_tool, list[T] deserialization
- Direct code inspection of `tests/conftest.py` — shared fixture structure
- Direct code inspection of `.planning/config.json` — nyquist_validation=false confirmed
- `.planning/phases/07-session-timeline/07-CONTEXT.md` — all locked decisions

### Secondary (MEDIUM confidence)
- `src/novel/mcp/server.py` — confirmed server.py wiring pattern for new module registration
- `src/novel/tools/arcs.py` — confirmed append-only vs upsert patterns, local function tool structure

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — direct code inspection of all relevant modules
- Architecture patterns: HIGH — code examples derived from existing working implementations
- Pitfalls: HIGH — derived from STATE.md accumulated decisions and direct schema inspection
- Test patterns: HIGH — direct inspection of test_gate.py and test_arcs.py

**Research date:** 2026-03-07
**Valid until:** 2026-04-07 (stable project, no upstream library churn expected)
