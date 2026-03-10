---
phase: 13-tech-debt-clearance
plan: "01"
subsystem: gate-cli / db-cli / planning-docs
tags: [tech-debt, gate, cli, docstrings, help-text]
dependency_graph:
  requires: []
  provides: [corrected-gate-count-strings, corrected-seed-help-text]
  affects: [gate-cli, db-cli]
tech_stack:
  added: []
  patterns: [string-literal-replacement-only]
key_files:
  created: []
  modified:
    - src/novel/gate/cli.py
    - src/novel/db/cli.py
decisions:
  - "REQUIREMENTS.md was already clean — no stale 33/34 gate count references present; Task 3 required zero edits"
  - "Only human-visible docstring/help strings updated; runtime logic (total = len(GATE_QUERIES)) was already correct and dynamic"
metrics:
  duration_minutes: 2
  completed_date: "2026-03-09"
  tasks_completed: 3
  tasks_total: 3
  files_changed: 2
---

# Phase 13 Plan 01: Fix Stale Gate Count Strings Summary

Corrected three stale "34-item" docstrings to "36-item" in gate/cli.py and two "gate-ready" (hyphen) help text occurrences to "gate_ready" (underscore) in db/cli.py; REQUIREMENTS.md was already clean.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Fix stale 34-item strings in gate/cli.py | 8daab06 | src/novel/gate/cli.py |
| 2 | Fix gate-ready hyphen typo in db/cli.py | 08b9c72 | src/novel/db/cli.py |
| 3 | Verify REQUIREMENTS.md has no stale gate count strings | n/a (no changes needed) | .planning/REQUIREMENTS.md |

## Verification Results

All five plan verification checks passed:

- `grep -n "34" src/novel/gate/cli.py` → PASS (no stale 34 found)
- `grep -n "gate-ready" src/novel/db/cli.py` → PASS (no hyphen form found)
- `uv run python -c "from novel.gate.cli import app"` → gate/cli import OK
- `uv run python -c "from novel.db.cli import app"` → db/cli import OK
- REQUIREMENTS.md python regex scan → PASS (no stale gate count references)

## Changes Made

### src/novel/gate/cli.py — 3 string replacements

| Location | Before | After |
|----------|--------|-------|
| Line 7 (module docstring) | `run full 34-item audit` | `run full 36-item audit` |
| Line 20 (check() docstring) | `"""Run full 34-item gate audit...` | `"""Run full 36-item gate audit...` |
| Line 110 (certify() docstring) | `all 34 checklist items pass` | `all 36 checklist items pass` |

Runtime logic (`total = len(GATE_QUERIES)`) was already correct and dynamic — not touched.

### src/novel/db/cli.py — 2 string replacements

| Location | Before | After |
|----------|--------|-------|
| Line 52 (Argument help text) | `(e.g. minimal, gate-ready)` | `(e.g. minimal, gate_ready)` |
| Line 57 (docstring) | `'gate-ready' profiles` | `'gate_ready' profiles` |

### .planning/REQUIREMENTS.md — no changes

Pre-inspected during planning and confirmed clean on execution. DEBT-01 already reads "Gate count displays '36 items' in all output". Zero edits required.

## Deviations from Plan

None — plan executed exactly as written.

## Self-Check: PASSED

- [x] src/novel/gate/cli.py — FOUND
- [x] src/novel/db/cli.py — FOUND
- [x] Commit 8daab06 — FOUND
- [x] Commit 08b9c72 — FOUND
