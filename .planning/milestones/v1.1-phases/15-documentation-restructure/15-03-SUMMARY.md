---
phase: 15-documentation-restructure
plan: "03"
subsystem: documentation
tags: [docs, mcp-tools, per-domain, markdown, reference]

# Dependency graph
requires:
  - phase: 15-documentation-restructure
    provides: docs/mcp-tools.md monolith (231 tools) and docs/tools/ directory from 15-01

provides:
  - 18 per-domain tool reference files under docs/tools/ (231 tools total)
  - Navigable documentation split by domain with back-links to index
  - Mixed-gate annotations for timeline and publishing domains

affects:
  - agent-skill docs that reference tool documentation
  - docs/README.md index (needs links updated to per-domain files)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Per-domain tool docs: one .md per domain, back-link to README, level-2 ## headers for tools"
    - "Index table per file listing tool name, gate status, and description"
    - "Gate status line in file header summarizes domain-level gate policy"

key-files:
  created:
    - docs/tools/arcs.md
    - docs/tools/canon.md
    - docs/tools/chapters.md
    - docs/tools/characters.md
    - docs/tools/foreshadowing.md
    - docs/tools/gate.md
    - docs/tools/knowledge.md
    - docs/tools/magic.md
    - docs/tools/names.md
    - docs/tools/plot.md
    - docs/tools/publishing.md
    - docs/tools/relationships.md
    - docs/tools/scenes.md
    - docs/tools/session.md
    - docs/tools/structure.md
    - docs/tools/timeline.md
    - docs/tools/voice.md
    - docs/tools/world.md
  modified: []

key-decisions:
  - "Tool headers use level-2 (## `tool_name`) not level-4 as in monolith — matches plan template and enables grep-based counting"
  - "Timeline domain described as mixed-gate with explicit per-tool gate status: 8 pre-Phase-14 CRUD tools gated, 10 junction/delete tools gate-free"
  - "Publishing domain described as mixed-gate: 5 publishing_assets/submission tools gated, 8 delete/documentation/research tools gate-free"
  - "World domain includes eras, books, acts, artifacts, object_states tools added in Phase 14 (33 tools total)"

patterns-established:
  - "Per-domain file structure: back-link → H1 title → description → gate status line → tool count → Index table → divider → tool entries"
  - "Gate status line options: 'All tools in this domain are gate-free', 'All tools in this domain require gate certification', 'Mixed — see individual tool entries'"

requirements-completed:
  - DOCS-01

# Metrics
duration: ~45min
completed: 2026-03-09
---

# Phase 15 Plan 03: Per-Domain Tool Documentation Split Summary

**Monolithic docs/mcp-tools.md (231 tools, ~5500 lines) split into 18 navigable per-domain files under docs/tools/ with Index tables, gate status headers, and back-links**

## Performance

- **Duration:** ~45 min
- **Started:** 2026-03-09T00:00:00Z
- **Completed:** 2026-03-09T00:45:00Z
- **Tasks:** 2
- **Files modified:** 18 created

## Accomplishments

- Created 18 per-domain tool reference files covering all 231 MCP tools
- Each file has back-link to docs/README.md, correct tool count, Index table, and per-tool entries with level-2 headers
- Correctly annotated mixed-gate domains (timeline: 8 gated + 10 free; publishing: 5 gated + 8 free)
- Total count verified: 231 tools across 18 files (exact match to monolith)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create 9 smaller domain files** - `d1a18be` (feat)
2. **Task 2: Create 9 larger/mixed domain files** - `65cc8fd` (feat)

**Plan metadata:** (pending — final commit below)

## Files Created/Modified

- `docs/tools/arcs.md` — 15 tools, gate-free
- `docs/tools/canon.md` — 10 tools, all gated
- `docs/tools/chapters.md` — 8 tools, gate-free
- `docs/tools/characters.md` — 19 tools, gate-free
- `docs/tools/foreshadowing.md` — 18 tools, all gated
- `docs/tools/gate.md` — 6 tools, gate-free
- `docs/tools/knowledge.md` — 12 tools, all gated
- `docs/tools/magic.md` — 14 tools, gate-free
- `docs/tools/names.md` — 6 tools, gate-free
- `docs/tools/plot.md` — 7 tools, gate-free
- `docs/tools/publishing.md` — 13 tools, mixed gate (5 gated, 8 free)
- `docs/tools/relationships.md` — 9 tools, gate-free
- `docs/tools/scenes.md` — 12 tools, gate-free
- `docs/tools/session.md` — 16 tools, all gated
- `docs/tools/structure.md` — 6 tools, gate-free
- `docs/tools/timeline.md` — 18 tools, mixed gate (8 gated, 10 free)
- `docs/tools/voice.md` — 9 tools, all gated
- `docs/tools/world.md` — 33 tools, gate-free

## Decisions Made

- Tool entries use level-2 `## \`tool_name\`` headers (not level-4 from the monolith) to match the plan template and support grep-based counting
- Timeline domain gate status annotated as mixed: the 8 pre-Phase-14 timeline CRUD tools (`get_pov_positions`, `get_pov_position`, `get_event`, `list_events`, `get_travel_segments`, `validate_travel_realism`, `upsert_event`, `upsert_pov_position`) are gated; the 10 Phase-14 junction/delete tools are gate-free
- Publishing domain gate status annotated as mixed: the 5 original publishing_assets/submission tools remain gated; the 8 delete/documentation/research tools added in Phase 14 are gate-free
- World domain expanded description to cover eras, books, acts, artifacts, object_states (all gate-free, Phase 14 additions)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- All 18 per-domain tool files ready for use by agent skill docs and README.md index linking
- docs/README.md will need its tool domain links updated to point to docs/tools/*.md files (Phase 15-04 task)
- The monolith docs/mcp-tools.md is now superseded by the per-domain files but has not been removed

---
*Phase: 15-documentation-restructure*
*Completed: 2026-03-09*

## Self-Check: PASSED

- All 18 docs/tools/*.md files confirmed on disk
- Task 1 commit d1a18be confirmed in git log
- Task 2 commit 65cc8fd confirmed in git log
- Total tool count: 231 across 18 files (verified via grep)
