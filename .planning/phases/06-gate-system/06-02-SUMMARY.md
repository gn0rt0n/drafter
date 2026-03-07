---
phase: 06-gate-system
plan: "02"
subsystem: database
tags: [gate, mcp, seed, sqlite, aiosqlite, fastmcp]

# Dependency graph
requires:
  - phase: 06-gate-system/06-01
    provides: GATE_ITEM_META dict with 34 item_key/category/description entries, gate tools register() function
  - phase: 02-pydantic-models-seed-data
    provides: GateViolation model in novel.models.shared, _load_minimal seed function
  - phase: 03-mcp-server-core-characters-relationships
    provides: FastMCP server instance and register() pattern
provides:
  - check_gate(conn) async helper in novel.mcp.gate — returns GateViolation when uncertified, None when certified
  - gate_ready seed profile in novel.db.seed — satisfies all 34 gate checks without FK violations
  - gate tools (5 total) registered in MCP server alongside all prior domain tools
affects:
  - 07-session-timeline
  - 08-canon-knowledge-foreshadowing
  - 09-names-voice-publishing
  - 10-cli-completion-integration-testing

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "check_gate(conn) placed in novel.mcp (not novel.tools) to prevent circular imports — Phase 7+ tools import from here"
    - "gate_ready seed calls _load_minimal() then extends with supplementary rows needed for all gate SQL checks"
    - "INSERT OR IGNORE used consistently for tables with UNIQUE constraints; plain INSERT for tables without"

key-files:
  created:
    - src/novel/mcp/gate.py
  modified:
    - src/novel/db/seed.py
    - src/novel/mcp/server.py

key-decisions:
  - "check_gate() placed in novel.mcp not novel.tools — prevents circular import since Phase 7+ tools will import from novel.mcp.gate"
  - "gate_ready seed references GATE_ITEM_META from novel.tools.gate at runtime (import inside function) — avoids duplication while still satisfying the cross-package import constraint"
  - "gate_ready seed correctly targets 34 GATE_ITEM_META items (not 33 as plan prose stated — confirmed by 06-01 implementation)"
  - "scene_character_goals schema uses goal/obstacle/outcome columns (not motivation) — plan's sample code corrected to match actual schema"
  - "voice_profiles schema has no narrative_style column — replaced with sentence_length to match actual migration schema"
  - "name_registry schema has no language_family column — plan's INSERT corrected to use actual columns (name, entity_type)"

patterns-established:
  - "check_gate(conn) pattern: receive already-open connection, query architecture_gate WHERE id=1, return GateViolation or None"
  - "Prose-phase tools (Phase 7+) import check_gate from novel.mcp.gate and call at top of each handler"

requirements-completed:
  - GATE-06
  - SEED-02

# Metrics
duration: 10min
completed: 2026-03-07
---

# Phase 06 Plan 02: Gate Wiring — check_gate(), gate_ready seed, server registration Summary

**async check_gate() helper in novel.mcp.gate, gate_ready seed profile satisfying all 34 gate SQL checks, and gate tools wired into the MCP server as the 47th–51st registered tools**

## Performance

- **Duration:** ~10 min
- **Started:** 2026-03-07T22:50:00Z
- **Completed:** 2026-03-07T22:55:00Z
- **Tasks:** 2
- **Files modified:** 3 (1 created, 2 modified)

## Accomplishments

- Created `src/novel/mcp/gate.py` with `check_gate(conn)` async helper — the cross-cutting enforcement primitive that Phase 7+ tools will call at the top of every handler
- Added `gate_ready` seed profile to `seed.py` that extends `_load_minimal()` with all data needed to satisfy all 34 gate checklist SQL queries, including voice profiles, character relationships, perception profiles, chapter hook notes, structural obligations, scene goals, pacing beats, tension measurements, canon domains, and name registry entries
- Wired `gate.register(mcp)` into `server.py` — all 5 gate tools (`get_gate_status`, `get_gate_checklist`, `run_gate_audit`, `update_checklist_item`, `certify_gate`) now appear in the MCP server tool list (47 total tools)

## Task Commits

1. **Task 1: Create novel/mcp/gate.py — check_gate() helper** - `634c449` (feat)
2. **Task 2: Extend seed.py with gate_ready profile + wire gate into server.py** - `6999a75` (feat)

**Plan metadata:** (final docs commit follows)

## Files Created/Modified

- `src/novel/mcp/gate.py` — New module: async `check_gate(conn)` that queries `architecture_gate WHERE id=1`, returns `GateViolation` when uncertified, `None` when certified. Imports only from `aiosqlite` and `novel.models.shared` — no circular import risk.
- `src/novel/db/seed.py` — Added `_load_gate_ready()` function and registered it in `load_seed_profile()` profiles dict. Function extends minimal seed with supplementary rows for all 34 gate checks.
- `src/novel/mcp/server.py` — Added `gate` to imports from `novel.tools`, added `gate.register(mcp)` call under Phase 6 comment, updated module docstring.

## Decisions Made

- **check_gate() module placement:** Placed in `novel.mcp` (not `novel.tools`) to prevent circular imports — Phase 7+ tools in `novel.tools` will import from `novel.mcp.gate`, and `novel.mcp.gate` must not import from `novel.tools.*`.
- **GATE_ITEM_META import inside _load_gate_ready:** The import from `novel.tools.gate` is placed inside the function body to avoid a module-level circular import. This is valid since seed.py is only run via CLI, not imported by MCP tools.
- **34 items, not 33:** The plan prose said "33 checklist items" but `GATE_ITEM_META` has 34 entries (confirmed by 06-01 implementation). The gate_ready seed correctly inserts all 34. The total row count in `gate_checklist_items` after seeding is 35 (34 from GATE_ITEM_META + 1 `min_characters` row from minimal seed that is outside GATE_ITEM_META).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed voice_profiles INSERT to use actual schema columns**
- **Found during:** Task 2 (gate_ready seed implementation)
- **Issue:** Plan's sample code used `(character_id, speech_patterns, narrative_style, canon_status)` — but `voice_profiles` has no `narrative_style` column; actual columns are `sentence_length`, `vocabulary_level`, `speech_patterns`, `verbal_tics`, etc.
- **Fix:** Changed INSERT to `(character_id, speech_patterns, sentence_length, canon_status)` to match actual migration schema
- **Files modified:** `src/novel/db/seed.py`
- **Verification:** FK check passes, no column-not-found errors
- **Committed in:** `6999a75` (Task 2 commit)

**2. [Rule 1 - Bug] Fixed name_registry INSERT to use actual schema columns**
- **Found during:** Task 2 (gate_ready seed implementation)
- **Issue:** Plan's sample code used `(name, entity_type, language_family, canon_status)` — but `name_registry` has no `language_family` column; the actual column is `linguistic_notes` and `canon_status` is not required.
- **Fix:** Changed INSERT to `(name, entity_type)` — minimal required columns with correct UNIQUE constraint on `name`
- **Files modified:** `src/novel/db/seed.py`
- **Verification:** FK check passes, name_registry entries inserted correctly
- **Committed in:** `6999a75` (Task 2 commit)

**3. [Rule 1 - Bug] Fixed scene_character_goals INSERT to use actual schema columns**
- **Found during:** Task 2 (gate_ready seed implementation)
- **Issue:** Plan's sample code used `(scene_id, character_id, goal, motivation)` — but `scene_character_goals` has no `motivation` column; actual columns are `goal`, `obstacle`, `outcome`.
- **Fix:** Changed INSERT to `(scene_id, character_id, goal)` — minimal required columns
- **Files modified:** `src/novel/db/seed.py`
- **Verification:** FK check passes, scene goals inserted correctly
- **Committed in:** `6999a75` (Task 2 commit)

---

**Total deviations:** 3 auto-fixed (all Rule 1 — schema column name mismatches between plan sample code and actual migrations)
**Impact on plan:** All fixes were necessary for correctness. The plan's sample code used incorrect column names for three tables; actual schema was ground truth (consistent with prior phase decisions).

## Issues Encountered

None beyond the schema column mismatches documented above. All resolved inline without requiring additional investigation.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `check_gate(conn)` is ready for Phase 7 (Session & Timeline) tools to import and use
- `gate_ready` seed profile is ready for Phase 7+ integration tests that need a fully gate-satisfying database state
- All 5 gate tools are live in the MCP server for Claude Code use
- Phase 6 (Gate System) is complete: 33 SQL queries (06-01) + 3 wiring files (06-02)

---
*Phase: 06-gate-system*
*Completed: 2026-03-07*
