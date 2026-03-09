---
phase: 09-names-voice-publishing
plan: "02"
subsystem: api
tags: [mcp, sqlite, aiosqlite, pydantic, voice, gate-system]

# Dependency graph
requires:
  - phase: 06-gate-system
    provides: check_gate() helper used by all 5 voice tools
  - phase: 02-pydantic-models-seed-data
    provides: VoiceProfile, VoiceDriftLog, SupernaturalVoiceGuideline models
provides:
  - 5 gated MCP voice tools in src/novel/tools/voice.py
  - get_voice_profile (character-scoped profile retrieval)
  - upsert_voice_profile (two-branch upsert on character_id UNIQUE)
  - get_supernatural_voice_guidelines (all guidelines list)
  - log_voice_drift (append-only drift event logging)
  - get_voice_drift_log (character drift history, desc order)
affects: [09-03-publishing, server-wiring]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - register(mcp) pattern with local async functions + @mcp.tool() decorators
    - Two-branch upsert on UNIQUE column (character_id) not PK for voice_profiles
    - Append-only INSERT for log_voice_drift (discrete audit trail events)
    - Empty list return for missing collections (not NotFoundResponse)
    - Gate-first pattern: check_gate(conn) before any DB logic in all 5 tools

key-files:
  created:
    - src/novel/tools/voice.py
  modified: []

key-decisions:
  - "upsert_voice_profile ON CONFLICT targets character_id (UNIQUE column) not id — character_id is the business key for voice profiles"
  - "log_voice_drift is append-only with no ON CONFLICT — each drift event is a discrete, immutable log entry"
  - "get_voice_drift_log returns empty list for character with no drift — no drift is valid state, not NotFoundResponse"
  - "get_supernatural_voice_guidelines returns empty list when table empty — consistent with all get_* collection tools"

patterns-established:
  - "Voice profile upsert targets UNIQUE business key (character_id), not PK — applicable to any domain with one-per-character semantics"

requirements-completed: [VOIC-01, VOIC-02, VOIC-03, VOIC-04, VOIC-05]

# Metrics
duration: 1min
completed: 2026-03-08
---

# Phase 9 Plan 02: Voice Domain Summary

**5 gated voice MCP tools (get/upsert voice profiles, supernatural guidelines, log/retrieve drift) with ON CONFLICT(character_id) upsert and append-only drift logging**

## Performance

- **Duration:** 1 min
- **Started:** 2026-03-08T02:40:04Z
- **Completed:** 2026-03-08T02:41:23Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments

- Implemented `src/novel/tools/voice.py` with 5 gated MCP tools registered via `register(mcp)` pattern
- All 5 tools call `check_gate(conn)` before any database logic — voice is a prose-phase domain
- `upsert_voice_profile` uses two-branch upsert: None-id INSERT + lastrowid; provided-id ON CONFLICT(character_id) DO UPDATE (character_id is the UNIQUE column, not id)
- `log_voice_drift` is append-only INSERT — each drift event is a discrete immutable audit entry
- `get_voice_drift_log` returns empty list for character with no drift (valid state, not error)

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement voice.py with 5 gated tools** - `7dadae5` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified

- `src/novel/tools/voice.py` - 5 gated voice domain MCP tools: get_voice_profile, upsert_voice_profile, get_supernatural_voice_guidelines, log_voice_drift, get_voice_drift_log

## Decisions Made

- **character_id UNIQUE upsert target:** `upsert_voice_profile` ON CONFLICT targets `character_id` (the UNIQUE constraint column), not `id`. The provided `profile_id` is used as the `id` value in the INSERT, but the conflict clause fires on `character_id` — consistent with the schema design where one character has exactly one voice profile.
- **Append-only drift log:** `log_voice_drift` uses plain INSERT with no ON CONFLICT. Voice drift events are discrete historical observations; each call creates an independent record in the audit trail.
- **Empty list semantics:** Both `get_voice_drift_log` and `get_supernatural_voice_guidelines` return empty lists for missing/empty data. Only single-record lookups (`get_voice_profile`) return `NotFoundResponse`.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `src/novel/tools/voice.py` complete with all 5 tools
- Ready for 09-03 (publishing domain + server.py wiring + in-memory tests for all 14 Phase 9 tools)
- Server.py wiring (`voice.register(mcp)`) deferred to 09-03 per plan split

---
*Phase: 09-names-voice-publishing*
*Completed: 2026-03-08*
