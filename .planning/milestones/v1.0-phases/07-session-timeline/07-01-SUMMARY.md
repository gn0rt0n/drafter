---
phase: 07-session-timeline
plan: "01"
subsystem: session
tags: [mcp, fastmcp, aiosqlite, pydantic, session-management, audit-trail, metrics]

# Dependency graph
requires:
  - phase: 06-gate-system
    provides: check_gate() helper in novel.mcp.gate, GateViolation model
  - phase: 03-mcp-server-core-characters-relationships
    provides: register(mcp) pattern, get_connection() context manager, novel.mcp.db
  - phase: 02-pydantic-models-seed-data
    provides: SessionLog, AgentRunLog, ProjectMetricsSnapshot, PovBalanceSnapshot, OpenQuestion models in novel.models.sessions

provides:
  - SessionStartResult wrapper model (session + briefing fields) in novel.models.sessions
  - 7 session domain MCP tools via novel.tools.session.register(mcp)
  - start_session: auto-closes open session, returns new session + prior briefing in MCP response body
  - close_session: auto-populates carried_forward from unanswered open_questions
  - get_last_session: retrieves most recent session_logs row
  - log_agent_run: append-only audit trail INSERT to agent_run_log
  - get_project_metrics: live aggregate (word_count + 4 table counts, no snapshot write)
  - log_project_snapshot: persists live metrics to project_metrics_snapshots
  - get_pov_balance: live GROUP BY pov_character_id with chapter/word counts

affects:
  - 07-session-timeline (remaining timeline tools will register alongside these)
  - 10-cli-completion-integration-testing (integration tests will call these tools end-to-end)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - prose-phase tool gate enforcement: check_gate(conn) called at top of every tool before DB logic
    - briefing-in-response: start_session returns SessionStartResult wrapper so prior session summary travels in tool response body, not stderr
    - append-only audit: log_agent_run uses plain INSERT with no ON CONFLICT — audit logs are never upserted
    - live aggregate vs snapshot: get_project_metrics computes live; log_project_snapshot persists a point-in-time copy
    - auto-close pattern: start_session auto-closes any open session before creating new one

key-files:
  created:
    - src/novel/tools/session.py
  modified:
    - src/novel/models/sessions.py

key-decisions:
  - "SessionStartResult carries briefing in the MCP tool response body so Claude can read prior session context as an MCP caller — never logged to stderr"
  - "start_session auto-closes open sessions before inserting new one to prevent multiple open sessions"
  - "close_session auto-populates carried_forward from all unanswered open_questions at close time"
  - "get_project_metrics is a live aggregate — does NOT read from project_metrics_snapshots table (locked decision from plan)"

patterns-established:
  - "Prose-phase gate check: every tool starts with violation = await check_gate(conn); if violation: return violation"
  - "SessionStartResult wrapper pattern: briefing travels in tool response body for MCP caller access"

requirements-completed:
  - SESS-01
  - SESS-02
  - SESS-03
  - SESS-04
  - SESS-05
  - SESS-06
  - SESS-07

# Metrics
duration: 2min
completed: 2026-03-08
---

# Phase 7 Plan 01: Session Domain MCP Tools Summary

**7 session MCP tools + SessionStartResult wrapper enabling Claude to manage writing sessions, log agent runs, and retrieve live project metrics and POV balance via typed tool responses**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-08T01:30:56Z
- **Completed:** 2026-03-08T01:32:28Z
- **Tasks:** 1
- **Files modified:** 2

## Accomplishments

- Added `SessionStartResult` Pydantic wrapper model to `novel.models.sessions` with `session: SessionLog` and `briefing: SessionLog | None` fields
- Created `src/novel/tools/session.py` with `register(mcp: FastMCP) -> None` exposing all 7 session tools
- `start_session` returns prior session briefing inside the MCP tool response body (not stderr), giving Claude session context as an MCP caller
- `close_session` auto-populates `carried_forward` from all unanswered `open_questions` at session close time
- `get_project_metrics` and `get_pov_balance` provide live aggregates without persisting snapshots

## Task Commits

Each task was committed atomically:

1. **Task 1: Add SessionStartResult model and create src/novel/tools/session.py with 7 session tools** - `f85dc16` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified

- `src/novel/models/sessions.py` - Appended `SessionStartResult(session: SessionLog, briefing: SessionLog | None)` at end of file
- `src/novel/tools/session.py` - New file: `register(mcp)` with 7 tools: start_session, close_session, get_last_session, log_agent_run, get_project_metrics, log_project_snapshot, get_pov_balance

## Decisions Made

- `SessionStartResult` carries briefing in the MCP tool response body — prior session summary travels to Claude as an MCP caller, not via stderr (which would be invisible to the caller)
- `start_session` auto-closes open sessions before inserting new one, preventing multiple concurrent open sessions
- `close_session` reads all unanswered `open_questions` at close time and stores as `carried_forward` JSON — ensures questions are never silently dropped between sessions
- `get_project_metrics` is live-only (no write to snapshots table) — locked decision per plan; `log_project_snapshot` is the explicit snapshot tool
- `OpenQuestion` imported in session.py even though not returned by any tool (used indirectly via SQL query pattern)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- All 7 session tools registered and verified clean import
- `SessionStartResult` available for use by server.py wiring (Phase 7 next plans)
- Gate enforcement pattern consistent with Phase 6 — all prose-phase tools call `check_gate(conn)` at top
- Ready for Phase 7 timeline tools (Plan 02)

## Self-Check: PASSED

- FOUND: src/novel/models/sessions.py
- FOUND: src/novel/tools/session.py
- FOUND: .planning/phases/07-session-timeline/07-01-SUMMARY.md
- FOUND commit: f85dc16

---
*Phase: 07-session-timeline*
*Completed: 2026-03-08*
