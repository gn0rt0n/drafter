---
phase: 07-session-timeline
plan: "03"
subsystem: session-timeline
tags: [mcp, session, timeline, travel-validation, tests]
dependency_graph:
  requires:
    - 07-01  # session tools implementation
    - 07-02  # timeline read tools
  provides:
    - TravelValidationResult model
    - timeline write and validation tools (8 total)
    - session and timeline modules wired into server.py
    - in-memory MCP tests for all 18 Phase 7 tools
  affects:
    - src/novel/mcp/server.py
    - src/novel/tools/session.py
tech_stack:
  added: []
  patterns:
    - "Python-level DEFAULT substitution for NOT NULL SQLite columns when tool args are None"
    - "Session-scoped autouse fixture using synchronous sqlite3 to certify gate before async tests"
    - "Two-branch upsert with ON CONFLICT for timeline events"
    - "ON CONFLICT(character_id, chapter_id) DO UPDATE for POV position natural unique key"
key_files:
  created:
    - tests/test_session.py
    - tests/test_timeline.py
  modified:
    - src/novel/models/timeline.py
    - src/novel/tools/timeline.py
    - src/novel/mcp/server.py
    - src/novel/tools/session.py
decisions:
  - "[07-03]: TravelValidationResult uses segment: TravelSegment | None — single-segment validations include the segment; character-level aggregation sets segment=None"
  - "[07-03]: upsert_event applies Python-level defaults (event_type='plot', canon_status='draft') before INSERT to avoid NOT NULL constraint failures when caller passes None"
  - "[07-03]: log_open_question applies Python-level defaults (domain='general', priority='normal') before INSERT — same NOT NULL pattern"
  - "[07-03]: Gate certification uses session-scoped autouse synchronous sqlite3 fixture — avoids anyio cancel scope lifecycle issues with async session fixtures"
  - "[07-03]: close_session carried_forward field is already-parsed list in FastMCP JSON response — test must handle both str and list forms"
  - "[07-03]: chapters table uses actual_word_count not word_count — session.py get_project_metrics and log_project_snapshot bugs fixed"
metrics:
  duration: 7 minutes
  completed: 2026-03-08
  tasks_completed: 2
  files_modified: 6
---

# Phase 7 Plan 03: Timeline Write Tools, Server Wiring, and Full MCP Tests Summary

One-liner: TravelValidationResult model added, 3 timeline write tools completed, all 18 Phase 7 tools wired into server.py, and 24 in-memory MCP tests covering both session and timeline domains pass green.

## What Was Built

### Task 1: TravelValidationResult + 3 Timeline Tools + Server Wiring

**src/novel/models/timeline.py** — Added `TravelValidationResult(BaseModel)` after `PovChronologicalPosition`. Fields: `is_realistic: bool`, `issues: list[str]`, `segment: TravelSegment | None`.

**src/novel/tools/timeline.py** — Extended from 5 read tools to 8 total:
- `validate_travel_realism(travel_segment_id, character_id)` — validates elapsed_days, travel_method, walking advisory, and location endpoint completeness. Returns single-segment results with segment attached; character-level results aggregate all issues with `segment=None`.
- `upsert_event(name, ...)` — two-branch INSERT+lastrowid vs ON CONFLICT(id) DO UPDATE. Python-level defaults applied for `event_type='plot'` and `canon_status='draft'` to satisfy NOT NULL columns.
- `upsert_pov_position(character_id, chapter_id, ...)` — `ON CONFLICT(character_id, chapter_id) DO UPDATE` on natural unique key.

**src/novel/mcp/server.py** — Imports `session, timeline` modules and calls `session.register(mcp)` and `timeline.register(mcp)` after `gate.register(mcp)`. Total tool count: 65.

### Task 2: In-Memory MCP Tests

**tests/test_session.py** — 10 tests for all session tools. Session-scoped autouse `certified_gate` fixture uses synchronous sqlite3 to certify `architecture_gate` directly before any test runs. Tests cover: `start_session` (SessionStartResult structure), `close_session` (carried_forward as list), `get_last_session`, `log_agent_run`, `get_project_metrics`, `log_project_snapshot`, `get_pov_balance`, `log_open_question`, `get_open_questions`, `answer_open_question`.

**tests/test_timeline.py** — 14 tests for all timeline tools. Same autouse certification pattern. Tests cover: `upsert_event` (create + update), `get_event` (found + not_found), `list_events` (all + filtered by chapter_id), `upsert_pov_position` (create + ON CONFLICT update), `get_pov_positions`, `get_pov_position` (found + not_found), `get_travel_segments`, `validate_travel_realism` (no_args + segment_not_found).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed word_count column reference in session.py**
- **Found during:** Task 2 (test_get_project_metrics failure)
- **Issue:** `src/novel/tools/session.py` queried `SUM(word_count)` from chapters but the actual column is `actual_word_count` (verified in migration 008). Both `get_project_metrics` and `log_project_snapshot` had this bug, plus `get_pov_balance` used the same wrong column name.
- **Fix:** Changed `SUM(word_count)` to `SUM(actual_word_count)` in all three locations in session.py
- **Files modified:** `src/novel/tools/session.py`
- **Commit:** c01ce97

**2. [Rule 2 - Missing] Python-level NOT NULL defaults for upsert_event**
- **Found during:** Task 2 (test_upsert_event_create failure: `NOT NULL constraint failed: events.canon_status`)
- **Issue:** `upsert_event` passed `None` for `event_type` and `canon_status` directly to SQLite INSERT, overriding the DEFAULT clause. SQLite DEFAULTs only apply when the column is omitted, not when NULL is explicitly passed.
- **Fix:** Apply Python-level defaults before the connection block: `effective_event_type = event_type if event_type is not None else "plot"` and `effective_canon_status = canon_status if canon_status is not None else "draft"`.
- **Files modified:** `src/novel/tools/timeline.py`
- **Commit:** c01ce97

**3. [Rule 2 - Missing] Python-level NOT NULL defaults for log_open_question**
- **Found during:** Task 2 (test_log_open_question failure: `NOT NULL constraint failed: open_questions.priority`)
- **Issue:** Same pattern — `domain` and `priority` in `open_questions` are NOT NULL with DEFAULTs, but passing `None` from Python inserts NULL.
- **Fix:** Apply Python-level defaults: `effective_domain = domain if domain is not None else "general"` and `effective_priority = priority if priority is not None else "normal"`.
- **Files modified:** `src/novel/tools/session.py`
- **Commit:** c01ce97

**4. [Rule 1 - Bug] Test carried_forward handling for already-parsed list**
- **Found during:** Task 2 (test_close_session failure: `TypeError: the JSON object must be str, bytes or bytearray, not list`)
- **Issue:** `close_session` returns `SessionLog` with `carried_forward` stored as a JSON string in SQLite. FastMCP/Pydantic deserializes it as a Python list in the MCP JSON response. Test incorrectly assumed `json.loads()` was needed.
- **Fix:** Test now handles both cases — if `carried_forward` is already a list, use it directly; if it's a string, parse it; if None, use `[]`.
- **Files modified:** `tests/test_session.py`
- **Commit:** c01ce97

**5. [Rule 1 - Bug] Gate certification required before each test session**
- **Found during:** Task 2 (multiple GateViolation responses when gate not certified)
- **Issue:** Original plan called `_certify_gate` inside individual tests using async MCP calls, but tests running in isolation or out of order would fail. Additionally, calling async gate tools adds significant overhead per test.
- **Fix:** Replaced per-test `_certify_gate` calls with a session-scoped autouse fixture that uses synchronous sqlite3 to directly update `architecture_gate.is_certified=1` and `gate_checklist_items.is_passing=1` in the DB before any test in the file runs.
- **Files modified:** `tests/test_session.py`, `tests/test_timeline.py`
- **Commit:** c01ce97

## Self-Check: PASSED

All files exist on disk. All commits verified in git log.

| Item | Status |
|------|--------|
| src/novel/models/timeline.py (TravelValidationResult) | FOUND |
| src/novel/tools/timeline.py (8 tools) | FOUND |
| src/novel/mcp/server.py (session+timeline registered) | FOUND |
| tests/test_session.py (11 test functions) | FOUND |
| tests/test_timeline.py (15 test functions) | FOUND |
| src/novel/tools/session.py (actual_word_count fix) | FOUND |
| Commit 355bfd6 (Task 1) | FOUND |
| Commit c01ce97 (Task 2) | FOUND |
| Full suite 171/171 green | PASSED |
