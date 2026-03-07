---
phase: 04-chapters-scenes-world
plan: 01
subsystem: api
tags: [mcp, fastmcp, pydantic, sqlite, chapters, aiosqlite]

# Dependency graph
requires:
  - phase: 03-mcp-server-core-characters-relationships
    provides: register(mcp) pattern, get_connection async context manager, NotFoundResponse/ValidationFailure contracts
provides:
  - Chapter domain MCP tools (5 tools: get_chapter, get_chapter_plan, get_chapter_obligations, list_chapters, upsert_chapter)
  - ChapterPlan Pydantic model (writing-focused subset of Chapter)
affects:
  - 04-02-scenes (same domain, same pattern)
  - 04-03-world (same domain, same pattern)
  - future phases that need chapter context

# Tech tracking
tech-stack:
  added: []
  patterns:
    - register(mcp) tool module pattern (continued from Phase 03)
    - Two-branch upsert (None id = INSERT, provided id = ON CONFLICT DO UPDATE)
    - NotFoundResponse for missing records, ValidationFailure for DB errors
    - No print() — all logging to stderr

key-files:
  created:
    - src/novel/tools/chapters.py
  modified:
    - src/novel/models/chapters.py

key-decisions:
  - "ChapterPlan is a projection model (not a DB table) — defined in models/chapters.py alongside Chapter for semantic grouping"
  - "get_chapter_obligations verifies chapter existence before querying obligations table — consistent with relationships pattern"
  - "list_chapters filters by book_id — must not return chapters from all books"

patterns-established:
  - "ChapterPlan projection pattern: SELECT * FROM chapters, then manually pick 8 fields into dedicated model"

requirements-completed: [CHAP-01, CHAP-02, CHAP-03, CHAP-06, CHAP-07]

# Metrics
duration: 1min
completed: 2026-03-07
---

# Phase 4 Plan 01: Chapters Tool Module Summary

**Chapter domain MCP tools with ChapterPlan projection model — 5 tools covering full retrieval, writing-plan subset, structural obligations, list, and upsert**

## Performance

- **Duration:** 1 min
- **Started:** 2026-03-07T21:35:33Z
- **Completed:** 2026-03-07T21:36:59Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Added ChapterPlan Pydantic model to chapters.py — 8-field writing-guidance projection of Chapter
- Created src/novel/tools/chapters.py with register(mcp) function containing all 5 chapter tools
- All tools follow established error contract: NotFoundResponse for missing records, ValidationFailure for DB errors
- upsert_chapter uses two-branch pattern matching characters tool pattern (None id vs provided id)

## Task Commits

Each task was committed atomically:

1. **Task 1: Add ChapterPlan model to chapters.py** - `ad2c25a` (feat)
2. **Task 2: Implement chapters tool module (5 tools)** - `053ec19` (feat)

**Plan metadata:** (docs commit below)

## Files Created/Modified
- `src/novel/models/chapters.py` - Added ChapterPlan model with 8 writing-guidance fields
- `src/novel/tools/chapters.py` - 5 chapter MCP tools: get_chapter, get_chapter_plan, get_chapter_obligations, list_chapters, upsert_chapter

## Decisions Made
- ChapterPlan is placed in models/chapters.py (not in the tools module) — semantic grouping with Chapter and ChapterStructuralObligation, matching the established pattern from Phase 02
- get_chapter_obligations first verifies the chapter exists (SELECT id FROM chapters WHERE id = ?) before querying the obligations table, returning NotFoundResponse on miss — consistent with get_character_injuries/beliefs/knowledge pattern
- list_chapters strictly filters by book_id to prevent returning chapters across all books

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Chapter tools fully wired and ready for server registration (04-03 wiring plan)
- Pattern established for scenes (04-02) and world (04-03) tool modules
- All 5 chapter requirements satisfied: CHAP-01, CHAP-02, CHAP-03, CHAP-06, CHAP-07

---
*Phase: 04-chapters-scenes-world*
*Completed: 2026-03-07*
