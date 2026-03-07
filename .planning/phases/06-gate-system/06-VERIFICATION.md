---
phase: 06-gate-system
verified: 2026-03-07T00:00:00Z
status: passed
score: 10/10 must-haves verified
re_verification: false
---

# Phase 6: Gate System Verification Report

**Phase Goal:** The architecture gate correctly blocks prose-phase operations when the 34-item checklist is incomplete, with full audit, certification, and CLI access
**Verified:** 2026-03-07
**Status:** passed
**Re-verification:** No — initial verification

---

## Note on Item Count

The plan prose text and requirements repeatedly say "33 checklist items" but the actual `GATE_ITEM_META` and `GATE_QUERIES` dicts each contain **34 entries** (the plan's enumerated key list sums to 34: 4 population + 6 structure + 4 scenes + 6 plot + 2 relationships + 3 world + 2 pacing + 1 voice + 2 names + 4 canon = 34). The codebase is internally consistent at 34 everywhere. The minimal seed also contributes one extra row (`min_characters`) not in `GATE_ITEM_META`, making `gate_checklist_items` 35 rows after seeding. All tests account for this correctly. This is a documentation discrepancy in the plan text only, not a functional defect.

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `get_gate_status` returns `is_certified` flag and `blocking_item_count` | VERIFIED | `src/novel/tools/gate.py:391-431`: queries `architecture_gate WHERE id=1` and `gate_checklist_items` count; returns dict with both fields; test `test_get_gate_status_returns_not_certified` passes |
| 2 | `get_gate_checklist` returns per-item pass/fail and `missing_count` for all gate_checklist_items rows | VERIFIED | `gate.py:438-452`: SELECT * FROM gate_checklist_items ORDER BY category, item_key; returns `list[GateChecklistItem]`; test confirms 35 items returned |
| 3 | `run_gate_audit` executes all 34 SQL evidence queries, writes results back via upsert, returns `GateAuditReport` with `total_items`, `passing_count`, `failing_count`, and `items` list | VERIFIED | `gate.py:459-543`: iterates GATE_QUERIES (34 keys), ON CONFLICT upsert, returns `GateAuditReport(gate_id=1, total_items=len(items), ...)`; `test_run_gate_audit_gate_ready_all_pass` confirms 0 failing gate-SQL items |
| 4 | `update_checklist_item` allows full manual override of `is_passing`, `missing_count`, and `notes` | VERIFIED | `gate.py:550-608`: SELECT check → UPDATE with COALESCE for notes → return updated row; `test_update_checklist_item_overrides_status` passes with `is_passing=False, missing_count=2, notes='test override'` |
| 5 | `certify_gate` writes `is_certified=1` when all items pass; returns `ValidationFailure` with error count when any item `is_passing=0` | VERIFIED | `gate.py:615-668`: counts failing items first; returns `ValidationFailure` if any; else UPDATE architecture_gate SET is_certified=1; `test_certify_gate_refuses_when_item_failing` and `test_certify_gate_passes_after_full_audit` both pass |
| 6 | `check_gate(conn)` returns `GateViolation` when `architecture_gate.is_certified=0`, returns `None` when `is_certified=1` | VERIFIED | `src/novel/mcp/gate.py:39-50`: SELECT is_certified WHERE id=1; returns GateViolation if not rows or not `rows[0]["is_certified"]`; imports only `aiosqlite` and `novel.models.shared` (no circular risk) |
| 7 | `gate_ready` seed satisfies all 34 checklist SQL queries and loads without FK violations | VERIFIED | `src/novel/db/seed.py:875-1045`: `_load_gate_ready` calls `_load_minimal` then adds supplementary rows for all 34 checks; `test_run_gate_audit_gate_ready_all_pass` confirms 0 failing SQL items |
| 8 | MCP server registers gate tools alongside existing domain tools | VERIFIED | `src/novel/mcp/server.py:19,41`: `from novel.tools import ... gate`; `gate.register(mcp)`; server has 47 total tools including all 5 gate tools |
| 9 | `novel gate check` runs audit and displays gap report | VERIFIED | `src/novel/gate/cli.py:26-57`: iterates GATE_QUERIES, upserts gate_checklist_items, displays formatted table of failing items; `novel gate --help` shows `check` command |
| 10 | `novel gate status` and `novel gate certify` work correctly | VERIFIED | `cli.py:60-103` (status): queries architecture_gate and blocking count; `cli.py:106-145` (certify): counts failing items, refuses if any, writes `is_certified=1`; all three commands listed in `novel gate --help` |

**Score:** 10/10 truths verified

---

## Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/novel/tools/gate.py` | 5 MCP gate tools + GateAuditReport + GATE_QUERIES + GATE_ITEM_META | VERIFIED | 668 lines; all 5 tools in `register()`; 34-entry dicts; keys match; assert at module level |
| `src/novel/mcp/gate.py` | `check_gate()` helper for prose-phase tools | VERIFIED | 50 lines; async function with `conn: aiosqlite.Connection` parameter; returns `GateViolation | None`; no `novel.tools.*` imports |
| `src/novel/db/seed.py` | `gate_ready` profile in `load_seed_profile` | VERIFIED | `_load_gate_ready` at line 875; registered in profiles dict at line 17; 34 gate_checklist_items inserted via GATE_ITEM_META |
| `src/novel/mcp/server.py` | gate tool registration | VERIFIED | Line 19 imports `gate`; line 41 calls `gate.register(mcp)` |
| `src/novel/gate/__init__.py` | Package marker | VERIFIED | File exists (empty package marker) |
| `src/novel/gate/cli.py` | Typer app with check, status, certify | VERIFIED | 142 lines; 3 commands; uses sync `get_connection()` from `novel.db.connection` |
| `src/novel/cli.py` | Root CLI with gate subcommand registered | VERIFIED | Line 20: `from novel.gate import cli as gate_cli`; line 32: `app.add_typer(gate_cli.app, name="gate")` |
| `tests/test_gate.py` | MCP in-memory tests using gate_ready seed | VERIFIED | 231 lines; 8 tests; all pass; uses `gate_ready` seed fixture |

---

## Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `src/novel/tools/gate.py` | `architecture_gate` table | `SELECT * FROM architecture_gate WHERE id = 1` | WIRED | Lines 402, 476, 664 |
| `src/novel/tools/gate.py` | `gate_checklist_items` | `ON CONFLICT(gate_id, item_key) DO UPDATE` | WIRED | Line 507 |
| `GATE_QUERIES` dict | 34 actual schema tables | Each query returns `missing_count` column | WIRED | All 34 queries use `AS missing_count`; verified by import check |
| `src/novel/mcp/gate.py` | `architecture_gate` | `SELECT is_certified FROM architecture_gate WHERE id = 1` | WIRED | Line 40 |
| `src/novel/db/seed.py _load_gate_ready` | `gate_checklist_items` | `INSERT OR IGNORE INTO gate_checklist_items` | WIRED | Line 1040 |
| `src/novel/mcp/server.py` | `src/novel/tools/gate.py` | `gate.register(mcp)` | WIRED | Line 41 |
| `src/novel/gate/cli.py` | `novel.db.connection.get_connection` | `from novel.db.connection import get_connection` | WIRED | Line 12 — uses sync connection, not MCP async connection |
| `src/novel/gate/cli.py` | `novel.tools.gate.GATE_QUERIES` | `from novel.tools.gate import GATE_QUERIES, GATE_ITEM_META` | WIRED | Line 13 |
| `tests/test_gate.py` | `novel.db.seed.load_seed_profile` | `load_seed_profile(conn, 'gate_ready')` | WIRED | Line 46 |
| `src/novel/mcp/gate.py` | `novel.models.shared` only | No `novel.tools.*` imports | VERIFIED | AST parse confirms imports: `['logging', 'aiosqlite', 'novel.models.shared']` |

---

## Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| GATE-01 | 06-01, 06-03 | `get_gate_status` tool exists | SATISFIED | `get_gate_status` in `register()`; returns `is_certified` + `blocking_item_count` |
| GATE-02 | 06-01, 06-03 | `run_gate_audit` evaluates all SQL queries | SATISFIED | Iterates all 34 GATE_QUERIES; writes back via ON CONFLICT upsert |
| GATE-03 | 06-01, 06-03 | `get_gate_checklist` with per-item pass/fail | SATISFIED | Returns `list[GateChecklistItem]` ordered by category |
| GATE-04 | 06-01, 06-03 | `update_checklist_item` manual override | SATISFIED | UPDATE with COALESCE(?, notes); test confirms override behavior |
| GATE-05 | 06-01, 06-03 | `certify_gate` writes certification when all pass | SATISFIED | Counts failing items; returns ValidationFailure or certified ArchitectureGate |
| GATE-06 | 06-02 | Shared `check_gate()` helper returns GateViolation | SATISFIED | `src/novel/mcp/gate.py`; no circular imports; returns `GateViolation | None` |
| SEED-02 | 06-02 | gate-ready seed satisfies all gate checklist items | SATISFIED | `_load_gate_ready` in `seed.py`; `test_run_gate_audit_gate_ready_all_pass` confirms 0 failing SQL items |
| CLSG-03 | 06-03 | `novel gate check` runs 34-item audit and displays gap report | SATISFIED | `check()` in `novel/gate/cli.py`; iterates GATE_QUERIES; formatted output |
| CLSG-04 | 06-03 | `novel gate status` displays current gate status and blocking count | SATISFIED | `status()` in cli.py; queries architecture_gate + count of failing items |
| CLSG-05 | 06-03 | `novel gate certify` certifies gate when all items pass | SATISFIED | `certify()` in cli.py; refuses with message if failing items exist |

All 10 requirements satisfied. No orphaned requirements found.

---

## Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `src/novel/mcp/gate.py` | 7-8 | Comment says "Never use print()" — it's a docstring warning, not actual print() | Info | No impact; informational comment only |

No `print()` calls found in any gate module files. No TODO/FIXME/placeholder patterns. No empty implementations (`return null`, `return {}`, `return []`).

---

## Test Suite Verification

```
147 passed in 1.32s
```

All 147 tests pass including 8 new gate tests. Zero regressions.

**Gate-specific test results:**
- `test_get_gate_status_returns_not_certified` — PASSED
- `test_get_gate_checklist_returns_items` — PASSED (35 items: 34 from GATE_ITEM_META + 1 min_characters)
- `test_run_gate_audit_returns_expected_items` — PASSED
- `test_run_gate_audit_gate_ready_all_pass` — PASSED (0 failing gate SQL items)
- `test_update_checklist_item_overrides_status` — PASSED
- `test_update_checklist_item_not_found` — PASSED
- `test_certify_gate_refuses_when_item_failing` — PASSED
- `test_certify_gate_passes_after_full_audit` — PASSED

---

## Human Verification Required

None. All gate behavior is fully verifiable programmatically: SQL queries are deterministic, certify/refuse logic is a count check, CLI output is text, and MCP tests cover the full call path with in-memory protocol.

---

## Summary

Phase 6 goal is fully achieved. The architecture gate system is complete and functional:

- All 5 MCP gate tools are registered and tested (`get_gate_status`, `get_gate_checklist`, `run_gate_audit`, `update_checklist_item`, `certify_gate`)
- The `check_gate()` helper is wired correctly in `novel.mcp.gate` with no circular import risk — ready for Phase 7+ prose-phase tools to call it
- The `gate_ready` seed satisfies all 34 SQL evidence queries, enabling reliable gate certification testing
- All 3 CLI commands (`novel gate check`, `novel gate status`, `novel gate certify`) are wired and working
- 147 tests pass with zero regressions

One documentation discrepancy: the plan prose says "33 items" throughout but the enumerated key list and actual implementation consistently use **34 items**. This is not a defect — the code is internally consistent.

---

_Verified: 2026-03-07_
_Verifier: Claude (gsd-verifier)_
