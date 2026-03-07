---
phase: 03-mcp-server-core-characters-relationships
verified: 2026-03-07T14:20:00Z
status: passed
score: 16/16 must-haves verified
re_verification: false
---

# Phase 3: MCP Server Core — Characters & Relationships Verification Report

**Phase Goal:** A working MCP server callable from Claude Code with the error contract enforced and two tightly coupled domains (characters and relationships) fully operational
**Verified:** 2026-03-07T14:20:00Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| #  | Truth                                                                                            | Status     | Evidence                                                                                                    |
|----|--------------------------------------------------------------------------------------------------|------------|-------------------------------------------------------------------------------------------------------------|
| 1  | `uv run novel-mcp` starts without error                                                          | VERIFIED   | Server emits `Starting novel-mcp server` log line and listens on stdio transport                            |
| 2  | 14 tools are registered on the MCP server (8 character + 6 relationship)                         | VERIFIED   | `mcp._tool_manager._tools` contains exactly 14 keys — confirmed by Python import check                     |
| 3  | `get_character` returns a Character dict for valid ID; `not_found_message` for invalid           | VERIFIED   | test_get_character_found (id=1 → Aeryn Vael) and test_get_character_not_found (id=9999) both pass          |
| 4  | `list_characters` returns all 5 seeded characters                                                | VERIFIED   | test_list_characters: len >= 5 and "Aeryn Vael" in names passes                                            |
| 5  | `upsert_character` creates when character_id=None, updates when non-None                         | VERIFIED   | test_upsert_character_create (new id assigned) and test_upsert_character_update (name changed) both pass   |
| 6  | Character state tools (injuries, knowledge, beliefs, location) return lists or NotFoundResponse  | VERIFIED   | 6 tests pass covering all 4 state tools including chapter-scoped queries and not-found cases                |
| 7  | `log_character_knowledge` inserts and returns the created row with id                            | VERIFIED   | test_log_character_knowledge: id in data and character_id == 1 pass                                        |
| 8  | `get_relationship` returns same row for A→B and B→A orderings                                   | VERIFIED   | test_get_relationship_reversed_order: data_forward["id"] == data_reversed["id"] passes                     |
| 9  | `list_relationships` returns all 3 seeded relationships for Aeryn                                | VERIFIED   | test_list_relationships: len >= 3 passes                                                                    |
| 10 | `upsert_relationship` canonicalizes (min, max) before INSERT                                     | VERIFIED   | Canonical `a, b = min(...), max(...)` present at line 160 of relationships.py; test_upsert_relationship_create passes |
| 11 | Perception profile tools create/retrieve directional profiles                                    | VERIFIED   | test_get_perception_profile_not_found and test_upsert_perception_profile both pass                         |
| 12 | `log_relationship_change` verifies relationship exists then inserts event row                    | VERIFIED   | test_log_relationship_change: id in data and relationship_id == 1 pass                                     |
| 13 | Error contract: not-found returns have `not_found_message`, result.isError is False              | VERIFIED   | All 5 not-found tests assert `not result.isError` and `"not_found_message" in data`                        |
| 14 | No `print()` calls in MCP server or tools source code                                           | VERIFIED   | grep matches only appear in docstring/comment text, not as executable calls                                 |
| 15 | `GateViolation` model with `requires_action` field exists (ERRC-03 Phase 3 scope)               | VERIFIED   | `src/novel/models/shared.py` defines `class GateViolation(BaseModel): requires_action: str`                |
| 16 | Full test suite passes with no regressions from prior phases                                     | VERIFIED   | 92 tests pass (21 Phase 3 + 71 prior), 0 failures                                                          |

**Score:** 16/16 truths verified

### Required Artifacts

| Artifact                         | Expected                                                              | Status     | Details                                                    |
|----------------------------------|-----------------------------------------------------------------------|------------|------------------------------------------------------------|
| `src/novel/tools/characters.py`  | 8 character tools via register(mcp), min 140 lines                   | VERIFIED   | 434 lines, 8 async defs inside register(), exports register |
| `src/novel/tools/relationships.py` | 6 relationship tools via register(mcp), min 90 lines               | VERIFIED   | 366 lines, 6 async defs inside register(), exports register |
| `src/novel/mcp/server.py`        | FastMCP instance with characters and relationships registered         | VERIFIED   | contains `characters.register(mcp)` and `relationships.register(mcp)` |
| `tests/conftest.py`              | Session-scoped temp DB fixture and mcp_session fixture               | VERIFIED   | Both fixtures present; imports create_connected_server_and_client_session |
| `tests/test_characters.py`       | In-memory MCP tests for all 8 character tools, min 70 lines         | VERIFIED   | 227 lines, 13 test functions covering all 8 tools          |
| `tests/test_relationships.py`    | In-memory MCP tests for all 6 relationship tools, min 50 lines      | VERIFIED   | 189 lines, 8 test functions covering all 6 tools           |

### Key Link Verification

| From                                | To                                    | Via                                    | Status   | Details                                                      |
|-------------------------------------|---------------------------------------|----------------------------------------|----------|--------------------------------------------------------------|
| `src/novel/mcp/server.py`           | `src/novel/tools/characters.py`       | `characters.register(mcp)`            | WIRED    | Line 26 of server.py; confirmed by 14-tool count             |
| `src/novel/mcp/server.py`           | `src/novel/tools/relationships.py`    | `relationships.register(mcp)`         | WIRED    | Line 27 of server.py; confirmed by 14-tool count             |
| `src/novel/tools/characters.py`     | `novel.mcp.db.get_connection`         | `async with get_connection() as conn`  | WIRED    | 8 occurrences of `get_connection()` in characters.py         |
| `src/novel/tools/characters.py`     | `novel.models.characters`             | `Character(**dict(row))`              | WIRED    | All 5 character models imported and used                     |
| `src/novel/tools/characters.py`     | `novel.models.shared`                 | `return NotFoundResponse(...)`        | WIRED    | NotFoundResponse and ValidationFailure imported and returned  |
| `src/novel/tools/relationships.py`  | `novel.mcp.db.get_connection`         | `async with get_connection() as conn`  | WIRED    | 6 occurrences of `get_connection()` in relationships.py      |
| `src/novel/tools/relationships.py`  | `novel.models.relationships`          | `CharacterRelationship(**dict(row))`  | WIRED    | All 3 relationship models imported and used                  |
| `src/novel/tools/relationships.py`  | `novel.models.shared`                 | `return NotFoundResponse(...)`        | WIRED    | NotFoundResponse and ValidationFailure imported and returned  |
| `tests/conftest.py`                 | `novel.mcp.server.mcp`               | `create_connected_server_and_client_session(mcp)` | WIRED | mcp imported and passed to session factory |
| `tests/conftest.py`                 | `NOVEL_DB_PATH` env var              | `monkeypatch.setenv('NOVEL_DB_PATH', test_db_path)` | WIRED | Line 42 of conftest.py |
| `tests/test_characters.py`          | `create_connected_server_and_client_session` | `_call_tool()` helper     | WIRED    | Per-test context manager entry avoids anyio teardown issues  |
| `tests/test_relationships.py`       | `create_connected_server_and_client_session` | `_call_tool()` helper     | WIRED    | Per-test context manager entry avoids anyio teardown issues  |

### Requirements Coverage

| Requirement | Source Plan | Description                                                                              | Status    | Evidence                                                                                     |
|-------------|-------------|------------------------------------------------------------------------------------------|-----------|----------------------------------------------------------------------------------------------|
| ERRC-01     | 03-01, 03-03 | Every MCP tool returns `not_found_message` when record not found — never raises         | SATISFIED | NotFoundResponse returned in all 8 char tools and 6 rel tools; 5 not-found tests pass        |
| ERRC-02     | 03-01, 03-03 | Every MCP tool returns `is_valid: false` + `errors` on validation failure — never raises | SATISFIED | ValidationFailure returned in upsert_character, upsert_relationship, log_* tools with try/except |
| ERRC-03     | 03-03        | Prose-phase tools return `requires_action` when gate not certified                       | SATISFIED | GateViolation model defined in shared.py with `requires_action: str`; Phase 3 research explicitly notes this is the Phase 3 scope for ERRC-03 (enforcement in Phase 6) |
| ERRC-04     | 03-01, 03-03 | No `print()` in MCP server code — all logging via logging module                        | SATISFIED | grep of src/novel/mcp/ and src/novel/tools/ finds only docstring mentions, no executable print() calls |
| CHAR-01     | 03-01, 03-03 | Claude can retrieve a character's full profile by ID (`get_character`)                   | SATISFIED | get_character implemented; test_get_character_found passes                                    |
| CHAR-02     | 03-01, 03-03 | Claude can retrieve a character's state at a given chapter (`get_character_state`)       | SATISFIED | Satisfied by 4 separate state tools: get_character_injuries, get_character_knowledge, get_character_beliefs, get_character_location (per plan design) |
| CHAR-03     | 03-01, 03-03 | Claude can list all characters (`list_characters`)                                       | SATISFIED | list_characters implemented; test_list_characters passes (len >= 5)                          |
| CHAR-04     | 03-01, 03-03 | Claude can create or update a character record (`upsert_character`)                      | SATISFIED | upsert_character with ON CONFLICT; test_upsert_character_create and _update pass             |
| CHAR-05     | 03-01, 03-03 | Claude can log what a character learns at a chapter (`log_character_knowledge`)          | SATISFIED | log_character_knowledge implemented; test_log_character_knowledge passes                      |
| CHAR-06     | 03-01, 03-03 | Claude can retrieve a character's injury history (`get_character_injuries`)              | SATISFIED | get_character_injuries with optional chapter scoping; 2 tests pass                           |
| CHAR-07     | 03-01, 03-03 | Claude can retrieve a character's current beliefs (`get_character_beliefs`)              | SATISFIED | get_character_beliefs implemented; test_get_character_beliefs_returns_list passes            |
| REL-01      | 03-02, 03-03 | Claude can retrieve the relationship between two characters (`get_relationship`)         | SATISFIED | get_relationship queries both orderings; 3 tests pass including reversed order               |
| REL-02      | 03-02, 03-03 | Claude can retrieve how one character perceives another (`get_perception_profile`)       | SATISFIED | get_perception_profile implemented; test_get_perception_profile_not_found passes            |
| REL-03      | 03-02, 03-03 | Claude can list all relationships for a character (`list_relationships`)                 | SATISFIED | list_relationships with OR clause; test_list_relationships passes (len >= 3)                 |
| REL-04      | 03-02, 03-03 | Claude can create or update a character relationship (`upsert_relationship`)             | SATISFIED | upsert_relationship with min/max canonicalization; test_upsert_relationship_create passes    |
| REL-05      | 03-02, 03-03 | Claude can create or update a perception profile (`upsert_perception_profile`)           | SATISFIED | upsert_perception_profile with ON CONFLICT; test_upsert_perception_profile passes            |
| REL-06      | 03-02, 03-03 | Claude can log a change event in a character relationship (`log_relationship_change`)    | SATISFIED | log_relationship_change with existence check; test_log_relationship_change passes            |

**All 16 phase requirements SATISFIED. No orphaned requirements.**

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `src/novel/mcp/db.py` | 10-11 | Text "print(" in docstring comment | Info | False positive — not an executable call; documents the prohibition |
| `src/novel/mcp/server.py` | 5-6 | Text "print(" in docstring comment | Info | False positive — not an executable call; documents the prohibition |

No blocker or warning anti-patterns found. Stub detection found no placeholder returns, empty handlers, or unconnected state.

### Human Verification Required

**1. Claude Code MCP Integration**

**Test:** Add the `novel-mcp` server to Claude Code's MCP configuration and issue a natural-language query like "What are Aeryn Vael's relationships?"
**Expected:** Claude Code selects the correct tools (`list_relationships`, `get_character`) without ambiguity
**Why human:** MCP tool selection accuracy and Claude Code's MCP configuration wiring cannot be verified from source alone

**2. stdio Protocol Integrity**

**Test:** Run `novel-mcp` as a real MCP server subprocess and verify no non-JSON output reaches stdout
**Expected:** Only valid MCP JSON-RPC messages on stdout; all log lines on stderr
**Why human:** The in-memory test transport bypasses stdio; the actual subprocess stdio behavior requires a live client connection to verify

## Gaps Summary

No gaps. All must-haves verified, all 16 requirements satisfied, all 21 tests pass, all 14 tools registered and wired. Human verification items above are informational — they do not block phase completion.

---

_Verified: 2026-03-07T14:20:00Z_
_Verifier: Claude (gsd-verifier)_
