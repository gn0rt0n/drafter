---
phase: 07-session-timeline
plan: "02"
subsystem: api
tags: [mcp, sqlite, aiosqlite, fastmcp, pydantic, session, timeline]

# Dependency graph
requires:
  - phase: 07-01
    provides: "7 session tools, session.py register() pattern, check_gate() wiring"
  - phase: 06-gate-system
    provides: "check_gate() helper in novel.mcp.gate"
  - phase: 02-pydantic-models-seed-data
    provides: "OpenQuestion, Event, TravelSegment, PovChronologicalPosition models"
provides:
  - "get_open_questions: retrieve unanswered questions with optional domain filter"
  - "log_open_question: append-only INSERT for new open questions"
  - "answer_open_question: UPDATE answered_at + return updated row"
  - "get_pov_positions: all POV positions at a given chapter"
  - "get_pov_position: single character/chapter POV lookup"
  - "get_event: retrieve timeline event by primary key"
  - "list_events: list events filtered by chapter or chapter range"
  - "get_travel_segments: all travel segments for a character (empty list, not NotFoundResponse)"
  - "src/novel/tools/timeline.py module with 5 read tools"
affects:
  - "08-canon-knowledge-foreshadowing"
  - "10-cli-completion-integration-testing"

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Dynamic WHERE clause construction: conditions list + params list, joined before ORDER BY"
    - "get_travel_segments returns empty list (not NotFoundResponse) — character may legitimately have no travel"
    - "OpenQuestion import added to session.py from novel.models.sessions"

key-files:
  created:
    - src/novel/tools/timeline.py
  modified:
    - src/novel/tools/session.py

key-decisions:
  - "get_travel_segments returns empty list not NotFoundResponse — a character with no travel is valid state, locked in CONTEXT.md"
  - "list_events chapter_id takes priority over start_chapter/end_chapter range when both provided"
  - "get_open_questions filters on answered_at IS NULL — answered questions are excluded from retrieval"

patterns-established:
  - "Dynamic WHERE clause: build conditions[] and params[], join with AND, skip WHERE if conditions empty"
  - "timeline.py follows identical module structure as session.py: module docstring with print warning, logging.getLogger, register(mcp) with local async defs"

requirements-completed:
  - SESS-08
  - SESS-09
  - SESS-10
  - TIME-01
  - TIME-02
  - TIME-03
  - TIME-04
  - TIME-05

# Metrics
duration: 5min
completed: 2026-03-08
---

# Phase 7 Plan 02: Session Timeline (Open Questions + Timeline Reads) Summary

**3 open question tools added to session.py and 5 timeline read tools created in new timeline.py, completing session domain and starting timeline domain with gate-checked aiosqlite reads**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-08T01:35:00Z
- **Completed:** 2026-03-08T01:40:00Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Extended session.py to 10 tools total: get_open_questions (domain-filtered), log_open_question (append-only INSERT), answer_open_question (UPDATE + NotFoundResponse guard)
- Created src/novel/tools/timeline.py with register(mcp) pattern and 5 read tools covering POV positions, events, and travel segments
- All 8 new tools call check_gate() before DB logic and return GateViolation if not certified
- Full plan verification: all 15 tools (10 session + 5 timeline) import and register cleanly

## Task Commits

Each task was committed atomically:

1. **Task 1: Extend session.py with 3 open question tools** - `e8cbe2d` (feat)
2. **Task 2: Create src/novel/tools/timeline.py with 5 timeline read tools** - `41ec8e8` (feat)

**Plan metadata:** (docs commit to follow)

## Files Created/Modified
- `src/novel/tools/session.py` - Added OpenQuestion import + 3 open question tools (get_open_questions, log_open_question, answer_open_question); now 10 tools total
- `src/novel/tools/timeline.py` - New file: 5 timeline read tools (get_pov_positions, get_pov_position, get_event, list_events, get_travel_segments)

## Decisions Made
- `get_travel_segments` returns empty list not NotFoundResponse — locked decision from CONTEXT.md; a character with no travel is a valid (not error) state
- `list_events` prioritises exact `chapter_id` over range filters when both are provided — unambiguous semantics for callers
- `get_open_questions` uses `answered_at IS NULL` filter — only unanswered questions are surfaced to Claude

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Session domain complete: 10 tools covering session lifecycle, metrics, POV balance, open question management
- Timeline read tools ready: 5 tools for POV positions, events, and travel segments
- Phase 08 (canon, knowledge, foreshadowing) can build on the gate-checked tool pattern established here
- timeline.py needs write tools in a future plan (upsert_event, upsert_pov_position, log_travel_segment) — those are scoped to Phase 07-03 or beyond

---
*Phase: 07-session-timeline*
*Completed: 2026-03-08*

## Self-Check: PASSED

- FOUND: src/novel/tools/session.py
- FOUND: src/novel/tools/timeline.py
- FOUND commit e8cbe2d (feat(07-02): extend session.py with 3 open question tools)
- FOUND commit 41ec8e8 (feat(07-02): create timeline.py with 5 timeline read tools)
