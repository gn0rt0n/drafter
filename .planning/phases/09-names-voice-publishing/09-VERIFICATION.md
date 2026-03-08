---
phase: 09-names-voice-publishing
verified: 2026-03-08T02:53:22Z
status: passed
score: 16/16 must-haves verified
re_verification: false
---

# Phase 9: Names, Voice & Publishing Verification Report

**Phase Goal:** Claude can manage the name registry with conflict detection and cultural suggestions, voice profiles with drift tracking, and publishing assets with submission tracking
**Verified:** 2026-03-08T02:53:22Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | check_name returns NameRegistryEntry (safe-to-use indicator) when name exists, NotFoundResponse when not | VERIFIED | `LOWER(name) = LOWER(?)` match logic confirmed; "safe to use" in NotFoundResponse message; 3 tests pass |
| 2 | register_name inserts into name_registry and returns NameRegistryEntry, or ValidationFailure on duplicate | VERIFIED | `try/except aiosqlite.IntegrityError` confirmed; lastrowid SELECT-back confirmed; test_register_name_duplicate passes |
| 3 | get_name_registry returns all NameRegistryEntry records, optionally filtered by entity_type and/or culture_id, ordered by name ASC | VERIFIED | Conditional WHERE clause with combined filters; `ORDER BY name ASC` confirmed; 3 filter tests pass |
| 4 | generate_name_suggestions returns NameSuggestionsResult with existing_names list and linguistic_context from cultures | VERIFIED | Two separate SELECTs (name_registry + cultures.naming_conventions); NameSuggestionsResult inline model confirmed; 2 tests pass |
| 5 | No check_gate() call exists anywhere in names.py — gate-free by locked design decision | VERIFIED | `await check_gate` count = 0 in names.py; gate references only appear in comments/docstrings |
| 6 | get_voice_profile returns VoiceProfile for a character or NotFoundResponse if none exists | VERIFIED | `SELECT * FROM voice_profiles WHERE character_id = ?`; both branches confirmed; 2 tests pass |
| 7 | upsert_voice_profile creates or updates a voice profile using ON CONFLICT(character_id) DO UPDATE | VERIFIED | Two-branch upsert with `ON CONFLICT(character_id) DO UPDATE` confirmed; character_id is UNIQUE column; 2 tests pass |
| 8 | get_supernatural_voice_guidelines returns all SupernaturalVoiceGuideline rows | VERIFIED | `SELECT * FROM supernatural_voice_guidelines ORDER BY element_name ASC`; 1 test passes |
| 9 | log_voice_drift appends a new VoiceDriftLog row and returns it | VERIFIED | Append-only INSERT with lastrowid + SELECT-back; 1 test passes |
| 10 | get_voice_drift_log returns all VoiceDriftLog rows for a character ordered by created_at DESC | VERIFIED | `ORDER BY created_at DESC`; empty-list semantics for no-drift case confirmed; 2 tests pass |
| 11 | All 5 voice tools call check_gate(conn) and return GateViolation when gate is not certified | VERIFIED | `await check_gate` count = 5 in voice.py (exactly one per tool); certified_gate fixture confirms gate path works |
| 12 | get_publishing_assets returns a list of PublishingAsset, optionally filtered by asset_type | VERIFIED | Conditional WHERE for asset_type; `ORDER BY created_at DESC`; 2 tests pass |
| 13 | upsert_publishing_asset creates or updates via two-branch upsert on id PK | VERIFIED | `ON CONFLICT(id) DO UPDATE` confirmed (PK target — publishing_assets has no named UNIQUE beyond PK); 2 tests pass |
| 14 | get_submissions returns a list of SubmissionEntry, optionally filtered by status | VERIFIED | Conditional WHERE for status; `ORDER BY submitted_at DESC`; 2 tests pass |
| 15 | log_submission appends a new submission and returns the inserted SubmissionEntry | VERIFIED | Append-only INSERT with lastrowid + SELECT-back; 1 test passes |
| 16 | update_submission partially updates a submission and returns updated SubmissionEntry, or NotFoundResponse if id not found | VERIFIED | Dynamic SET clause; SELECT-back after UPDATE for missing-row detection; 2 tests pass (found + not_found) |

**Score:** 16/16 truths verified

Additional truths verified from 09-03 must_haves:

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| A | All 5 publishing tools call check_gate(conn) and return GateViolation when gate is not certified | VERIFIED | `await check_gate` count = 5 in publishing.py (exactly one per tool) |
| B | server.py registers names, voice, and publishing modules — all 14 Phase 9 tools callable via MCP | VERIFIED | `names.register(mcp)`, `voice.register(mcp)`, `publishing.register(mcp)` all present in server.py Phase 9 block |
| C | In-memory FastMCP tests cover all 14 tools across test_names.py, test_voice.py, test_publishing.py | VERIFIED | 27 tests total: 10 names + 8 voice + 9 publishing — all 27 pass |

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/novel/tools/names.py` | 4 gate-free name domain MCP tools via register(mcp) | VERIFIED | 241 lines; 4 @mcp.tool() decorators; register(mcp) function; NameSuggestionsResult inline model; no check_gate calls |
| `src/novel/tools/voice.py` | 5 gated voice domain MCP tools via register(mcp) | VERIFIED | 310 lines; 6 @mcp.tool() lines (5 actual tools + 1 in docstring); register(mcp) function; 5 await check_gate calls |
| `src/novel/tools/publishing.py` | 5 gated publishing domain MCP tools via register(mcp) | VERIFIED | 312 lines; 6 @mcp.tool() lines (5 actual tools + 1 in docstring); register(mcp) function; 5 await check_gate calls |
| `src/novel/mcp/server.py` | server wiring for all Phase 9 tool modules | VERIFIED | names/voice/publishing imported and registered in Phase 9 block; docstring updated to "Phase 9: Names, voice, and publishing tools registered." |
| `tests/test_names.py` | in-memory FastMCP tests for all 4 name tools | VERIFIED | 10 tests; no certified_gate fixture; minimal seed; all 10 pass |
| `tests/test_voice.py` | in-memory FastMCP tests for all 5 voice tools | VERIFIED | 8 tests; certified_gate autouse fixture; gate_ready seed; all 8 pass |
| `tests/test_publishing.py` | in-memory FastMCP tests for all 5 publishing tools | VERIFIED | 9 tests; certified_gate autouse fixture; gate_ready seed; all 9 pass |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `names.py` tools | name_registry table | `get_connection()` aiosqlite context manager | WIRED | `async with get_connection() as conn` in all 4 tools confirmed |
| `generate_name_suggestions` | cultures.naming_conventions | `SELECT naming_conventions FROM cultures WHERE id = ?` | WIRED | Second SELECT query confirmed at line 225–229 of names.py |
| `voice.py` tools | `novel.mcp.gate.check_gate` | `gate = await check_gate(conn)` at top of every tool | WIRED | 5 `await check_gate` calls confirmed; `from novel.mcp.gate import check_gate` import confirmed |
| `upsert_voice_profile` | voice_profiles | `ON CONFLICT(character_id) DO UPDATE` | WIRED | Character_id is UNIQUE column; conflict clause confirmed at lines 155–165 of voice.py |
| `update_submission` | submission_tracker | `SELECT * FROM submission_tracker WHERE id = ?` after UPDATE | WIRED | SELECT-back at lines 300–304 of publishing.py confirmed; NotFoundResponse on `row is None` |
| `upsert_publishing_asset` | publishing_assets | `ON CONFLICT(id) DO UPDATE` | WIRED | PK conflict target confirmed at lines 132–139 of publishing.py |
| `server.py` | names/voice/publishing modules | `names.register(mcp)`, `voice.register(mcp)`, `publishing.register(mcp)` | WIRED | All three calls present in server.py lines 56–58 |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| NAME-01 | 09-01 | Claude can check whether a proposed name conflicts with existing names (`check_name`) | SATISFIED | `check_name` tool implemented; case-insensitive LOWER() match; 3 tests pass |
| NAME-02 | 09-01 | Claude can register a name with its cultural/linguistic context (`register_name`) | SATISFIED | `register_name` tool implemented; IntegrityError catch for UNIQUE; 2 tests pass |
| NAME-03 | 09-01 | Claude can retrieve the full name registry (`get_name_registry`) | SATISFIED | `get_name_registry` with optional filters; ordered by name ASC; 3 tests pass |
| NAME-04 | 09-01 | Claude can get name suggestions following cultural/linguistic rules (`generate_name_suggestions`) | SATISFIED | `generate_name_suggestions` with two-pass SELECTs; NameSuggestionsResult; 2 tests pass |
| VOIC-01 | 09-02 | Claude can retrieve a character's voice profile (`get_voice_profile`) | SATISFIED | `get_voice_profile` gated tool; NotFoundResponse for missing profile; 2 tests pass |
| VOIC-02 | 09-02 | Claude can retrieve supernatural voice guidelines (`get_supernatural_voice_guidelines`) | SATISFIED | `get_supernatural_voice_guidelines` gated tool; returns list; 1 test passes |
| VOIC-03 | 09-02 | Claude can log a voice drift instance (`log_voice_drift`) | SATISFIED | `log_voice_drift` append-only gated tool; SELECT-back; 1 test passes |
| VOIC-04 | 09-02 | Claude can retrieve the voice drift log for a character (`get_voice_drift_log`) | SATISFIED | `get_voice_drift_log` gated tool; empty list for no-drift; 2 tests pass |
| VOIC-05 | 09-02 | Claude can create or update a voice profile (`upsert_voice_profile`) | SATISFIED | `upsert_voice_profile` gated; two-branch ON CONFLICT(character_id); 2 tests pass |
| PUBL-01 | 09-03 | Claude can retrieve publishing assets (`get_publishing_assets`) | SATISFIED | `get_publishing_assets` gated; asset_type filter; 2 tests pass |
| PUBL-02 | 09-03 | Claude can create or update a publishing asset (`upsert_publishing_asset`) | SATISFIED | `upsert_publishing_asset` gated; two-branch ON CONFLICT(id); 2 tests pass |
| PUBL-03 | 09-03 | Claude can retrieve submission tracker entries (`get_submissions`) | SATISFIED | `get_submissions` gated; status filter; 2 tests pass |
| PUBL-04 | 09-03 | Claude can log a new submission (`log_submission`) | SATISFIED | `log_submission` append-only gated tool; SELECT-back; 1 test passes |
| PUBL-05 | 09-03 | Claude can update a submission's status (`update_submission`) | SATISFIED | `update_submission` gated; dynamic SET; SELECT-back for NotFoundResponse; 2 tests pass |

All 14 requirement IDs declared across plans are satisfied. No orphaned requirements detected for Phase 9 in REQUIREMENTS.md.

### Anti-Patterns Found

None detected.

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| — | — | No print() statements | — | Clean |
| — | — | No TODO/FIXME/placeholder | — | Clean |
| — | — | No stub returns (null/empty/static) | — | Clean |
| — | — | No empty handlers | — | Clean |

Specific checks performed:
- `print(` in names.py, voice.py, publishing.py: 0 matches
- `TODO|FIXME|PLACEHOLDER|placeholder|coming soon` in all 3 files: 0 matches
- `await check_gate` absent from names.py (correctly gate-free): confirmed
- `await check_gate` count in voice.py: 5 (one per tool)
- `await check_gate` count in publishing.py: 5 (one per tool)

### Human Verification Required

None. All 14 tools are DB-level MCP tools with no visual/UI behavior. The full MCP protocol path is tested via in-memory FastMCP sessions. All 27 Phase 9 tests pass. The full 219-test suite passes with no regressions.

### Gaps Summary

No gaps. All must-haves from all three PLANs are verified.

---

## Test Run Evidence

```
============================= test session starts ==============================
platform darwin -- Python 3.13.12, pytest-9.0.2
collected 27 items

tests/test_names.py::test_check_name_found[asyncio] PASSED
tests/test_names.py::test_check_name_case_insensitive[asyncio] PASSED
tests/test_names.py::test_check_name_not_found[asyncio] PASSED
tests/test_names.py::test_register_name_success[asyncio] PASSED
tests/test_names.py::test_register_name_duplicate_returns_validation_failure[asyncio] PASSED
tests/test_names.py::test_get_name_registry_returns_all[asyncio] PASSED
tests/test_names.py::test_get_name_registry_filter_entity_type[asyncio] PASSED
tests/test_names.py::test_get_name_registry_filter_culture_id[asyncio] PASSED
tests/test_names.py::test_generate_name_suggestions_known_culture[asyncio] PASSED
tests/test_names.py::test_generate_name_suggestions_unknown_culture[asyncio] PASSED
tests/test_voice.py::test_get_voice_profile_found[asyncio] PASSED
tests/test_voice.py::test_get_voice_profile_not_found[asyncio] PASSED
tests/test_voice.py::test_upsert_voice_profile_create[asyncio] PASSED
tests/test_voice.py::test_upsert_voice_profile_update[asyncio] PASSED
tests/test_voice.py::test_get_supernatural_voice_guidelines[asyncio] PASSED
tests/test_voice.py::test_log_voice_drift[asyncio] PASSED
tests/test_voice.py::test_get_voice_drift_log[asyncio] PASSED
tests/test_voice.py::test_get_voice_drift_log_empty[asyncio] PASSED
tests/test_publishing.py::test_get_publishing_assets_all[asyncio] PASSED
tests/test_publishing.py::test_get_publishing_assets_filtered[asyncio] PASSED
tests/test_publishing.py::test_upsert_publishing_asset_create[asyncio] PASSED
tests/test_publishing.py::test_upsert_publishing_asset_update[asyncio] PASSED
tests/test_publishing.py::test_get_submissions_all[asyncio] PASSED
tests/test_publishing.py::test_get_submissions_filtered[asyncio] PASSED
tests/test_publishing.py::test_log_submission[asyncio] PASSED
tests/test_publishing.py::test_update_submission_found[asyncio] PASSED
tests/test_publishing.py::test_update_submission_not_found[asyncio] PASSED

============================== 27 passed in 0.45s ==============================

Full suite: 219 passed in 2.86s (no regressions)
```

---

_Verified: 2026-03-08T02:53:22Z_
_Verifier: Claude (gsd-verifier)_
