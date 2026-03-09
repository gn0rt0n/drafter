---
phase: 14-mcp-api-completeness
plan: "10"
subsystem: api
tags: [mcp, sqlite, upsert, magic, voice, names, fastmcp, pydantic]

# Dependency graph
requires:
  - phase: 14-mcp-api-completeness
    provides: delete tools for magic_use_log and name_registry_entry (Plan 04 baseline)
provides:
  - upsert_magic_element: two-branch upsert for magic_system_elements
  - list_magic_elements: full listing of magic system elements ordered by name
  - upsert_practitioner_ability: two-branch upsert with character and element FK pre-checks
  - delete_magic_element: FK-safe delete for magic_system_elements
  - delete_practitioner_ability: FK-safe delete for practitioner_abilities
  - upsert_supernatural_voice_guideline: gate-gated two-branch upsert for supernatural_voice_guidelines
  - delete_supernatural_voice_guideline: gate-gated FK-safe delete for supernatural_voice_guidelines
  - upsert_name_registry_entry: gate-free two-branch upsert for name_registry
affects: [phase-15-docs, novel-plugin]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - two-branch upsert (id=None INSERT, id=N ON CONFLICT DO UPDATE) applied to magic, voice, names domains
    - FK pre-check pattern (verify character and element existence before upsert) for practitioner_abilities
    - gate-gated upsert tools in voice.py consistent with existing gate pattern in that module

key-files:
  created: []
  modified:
    - src/novel/tools/magic.py
    - src/novel/tools/voice.py
    - src/novel/tools/names.py

key-decisions:
  - "magic_system_elements columns confirmed from migration 011: name, element_type, rules, limitations, costs, exceptions, introduced_chapter_id, notes, canon_status — no description column (plan example used wrong column name)"
  - "practitioner_abilities unique key is UNIQUE(character_id, magic_element_id) — upsert uses id-based ON CONFLICT(id) branch to avoid compound conflict issues"
  - "supernatural_voice_guidelines has UNIQUE(element_name) — upsert branch uses ON CONFLICT(id) for update (id-based, not name-based) to allow element_name edits"
  - "upsert_name_registry_entry is gate-free consistent with all other names.py tools"
  - "Voice upsert/delete tools are gate-gated consistent with all existing voice.py tools"

patterns-established:
  - "Two-branch upsert: id=None triggers plain INSERT with lastrowid; id=N triggers INSERT ... ON CONFLICT(id) DO UPDATE"
  - "FK pre-check before upsert: query FK tables first, return NotFoundResponse before attempting write"

requirements-completed: [MCP-01, MCP-02]

# Metrics
duration: 15min
completed: 2026-03-09
---

# Phase 14 Plan 10: Write Tools for Magic, Voice, and Names Summary

**8 upsert/delete tools added across magic.py, voice.py, and names.py completing CRUD for four previously read-only world-building tables**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-03-09T19:52:00Z
- **Completed:** 2026-03-09T20:07:00Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Completed magic.py with upsert_magic_element, list_magic_elements, upsert_practitioner_ability, delete_magic_element, delete_practitioner_ability (5 tools)
- Completed voice.py with gate-gated upsert_supernatural_voice_guideline and delete_supernatural_voice_guideline (2 tools)
- Completed names.py with gate-free upsert_name_registry_entry (1 tool)
- All 3 modules import cleanly; all tools follow established patterns for their domain (gated/non-gated)

## Task Commits

Each task was committed atomically:

1. **Task 1: Add upsert and delete tools to magic.py** - `375da4a` (feat)
2. **Task 2: Add write tools to voice.py and names.py** - `dc061b2` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified
- `src/novel/tools/magic.py` - Added upsert_magic_element, list_magic_elements, upsert_practitioner_ability, delete_magic_element, delete_practitioner_ability
- `src/novel/tools/voice.py` - Added upsert_supernatural_voice_guideline, delete_supernatural_voice_guideline (both gate-gated)
- `src/novel/tools/names.py` - Added upsert_name_registry_entry (gate-free)

## Decisions Made
- magic_system_elements columns confirmed from migration 011 — the plan example used `description` but the real table has `rules, limitations, costs, exceptions` instead; implemented with correct columns
- practitioner_abilities has UNIQUE(character_id, magic_element_id) — upsert uses id-based ON CONFLICT(id) to allow modifying either FK column
- supernatural_voice_guidelines UNIQUE(element_name) — upsert uses ON CONFLICT(id) so element_name can be edited
- Voice tools are gate-gated (consistent with all other voice.py tools); names tools are gate-free (consistent with all other names.py tools)

## Deviations from Plan

None - plan executed exactly as written. The plan example showed `description` as a column in `upsert_magic_element` but noted to check actual columns — actual columns (rules, limitations, costs, exceptions) were used as confirmed from migration 011.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All four tables (magic_system_elements, practitioner_abilities, supernatural_voice_guidelines, name_registry) now have full CRUD via MCP tools
- Phase 14 MCP API completeness work is complete
- Ready for Phase 15 documentation phase

---
*Phase: 14-mcp-api-completeness*
*Completed: 2026-03-09*
