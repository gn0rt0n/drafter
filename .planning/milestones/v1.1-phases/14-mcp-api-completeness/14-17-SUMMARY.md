---
phase: 14-mcp-api-completeness
plan: "17"
subsystem: api
tags: [mcp, publishing, sqlite, pydantic, aiosqlite, crud]

# Dependency graph
requires:
  - phase: 14-06
    provides: delete_publishing_asset and delete_submission tools in publishing.py

provides:
  - get_documentation_tasks: optional status filter, returns list[DocumentationTask]
  - upsert_documentation_task: two-branch upsert on id PK with all schema fields
  - delete_documentation_task: FK-safe delete with NotFoundResponse
  - get_research_notes: optional relevance filter (LIKE match), returns list[ResearchNote]
  - upsert_research_note: two-branch upsert on id PK (topic + content required)
  - delete_research_note: FK-safe delete with NotFoundResponse

affects: [14-mcp-api-completeness, 15-docs]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Two-branch upsert on id PK for entity tables (not append-only logs)"
    - "FK-safe delete pattern (try/except ValidationFailure) for consistency"
    - "Gate-free tools for dev-internal tables (documentation_tasks, research_notes)"

key-files:
  created: []
  modified:
    - src/novel/tools/publishing.py
    - tests/test_publishing.py

key-decisions:
  - "ResearchNote uses topic (not title) and relevance (not tags) — real schema from migration 021 used; plan interface was simplified"
  - "get_research_notes filters by relevance using LIKE '%value%' for partial match support"
  - "DocumentationTask has due_chapter_id FK and completed_at fields included in upsert — real schema used over simplified plan interface"
  - "documentation_tasks and research_notes are not gate-gated (dev-internal tables) — consistent with plan spec"

patterns-established:
  - "Dev-internal publishing tables (documentation_tasks, research_notes) use gate-free tools — only publishing_assets and submission_tracker are gate-gated"

requirements-completed:
  - MCP-01
  - MCP-02

# Metrics
duration: 4min
completed: 2026-03-09
---

# Phase 14 Plan 17: Documentation Tasks and Research Notes CRUD Summary

**Full CRUD for documentation_tasks and research_notes in publishing.py using two-branch upsert and FK-safe delete patterns, with real schema fields (topic/relevance) corrected from plan interface**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-09T20:22:08Z
- **Completed:** 2026-03-09T20:26:00Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Added get_documentation_tasks, upsert_documentation_task, delete_documentation_task (3 tools)
- Added get_research_notes, upsert_research_note, delete_research_note (3 tools)
- TDD: wrote failing tests first for all 6 tools, then implemented GREEN
- All 22 publishing tests pass; publishing.py now has 13 total tools

## Task Commits

Each task was committed atomically (TDD: test then feat):

1. **Task 1 RED: Failing documentation_tasks tests** - `157bc97` (test)
2. **Task 1 GREEN: documentation_tasks CRUD implementation** - `24b9313` (feat)
3. **Task 2 RED: Failing research_notes tests** - `b6c8743` (test)
4. **Task 2 GREEN: research_notes CRUD implementation** - `2cbfe3b` (feat)

**Plan metadata:** (docs commit — see below)

_Note: TDD tasks have two commits each (test RED → feat GREEN)_

## Files Created/Modified
- `src/novel/tools/publishing.py` - Added 6 new CRUD tools for documentation_tasks and research_notes; added DocumentationTask and ResearchNote imports; updated docstring to 13 tools
- `tests/test_publishing.py` - Added 12 new tests (6 per domain); full suite now 22 tests, all passing

## Decisions Made
- ResearchNote real schema uses `topic` (not `title`) and `relevance` (not `tags`) — confirmed from migration 021 and Pydantic model; plan interface was simplified/incorrect
- DocumentationTask real schema includes `due_chapter_id` (FK to chapters) and `completed_at` — all fields included in upsert for completeness
- get_research_notes uses LIKE `%value%` for relevance filter — supports partial matching, consistent with other LIKE-based filters in the codebase
- documentation_tasks and research_notes tools are not gate-gated — consistent with plan spec (dev-internal tables)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Corrected ResearchNote schema fields from plan interface**
- **Found during:** Task 2 (read src/novel/models/publishing.py before implementing)
- **Issue:** Plan interface specified `title` and `tags` parameters; real schema uses `topic` and `relevance` respectively
- **Fix:** Used real schema field names in tool signatures, SQL, and tests
- **Files modified:** src/novel/tools/publishing.py, tests/test_publishing.py
- **Verification:** All 22 publishing tests pass
- **Committed in:** 2cbfe3b (Task 2 GREEN commit)

**2. [Rule 1 - Bug] Corrected DocumentationTask schema fields from plan interface**
- **Found during:** Task 1 (read migration 021 and Pydantic model to confirm schema)
- **Issue:** Plan interface omitted `due_chapter_id` and `completed_at` from upsert; real schema has these fields
- **Fix:** Included all real schema fields in upsert_documentation_task signature and SQL
- **Files modified:** src/novel/tools/publishing.py, tests/test_publishing.py
- **Verification:** All documentation_tasks tests pass with full field round-trip
- **Committed in:** 24b9313 (Task 1 GREEN commit)

---

**Total deviations:** 2 auto-fixed (both Rule 1 - schema field corrections from plan interface to real schema)
**Impact on plan:** Both fixes necessary for correctness — tools using wrong field names would have caused SQL errors at runtime. No scope creep.

## Issues Encountered
None beyond the schema field corrections documented above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- publishing.py now has full CRUD coverage for all 4 publishing-domain tables: publishing_assets, submission_tracker, documentation_tasks, research_notes
- Phase 14 MCP API completeness work can continue with remaining domain gaps
- All 22 publishing tests pass cleanly

## Self-Check: PASSED

- FOUND: src/novel/tools/publishing.py
- FOUND: tests/test_publishing.py
- FOUND: .planning/phases/14-mcp-api-completeness/14-17-SUMMARY.md
- FOUND: commit 157bc97 (test RED: documentation_tasks)
- FOUND: commit 24b9313 (feat GREEN: documentation_tasks)
- FOUND: commit b6c8743 (test RED: research_notes)
- FOUND: commit 2cbfe3b (feat GREEN: research_notes)
- 22/22 publishing tests passing

---
*Phase: 14-mcp-api-completeness*
*Completed: 2026-03-09*
