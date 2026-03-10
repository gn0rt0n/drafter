---
phase: 14-mcp-api-completeness
plan: "08"
subsystem: mcp-tools
tags: [mcp, arcs, chapters, session, timeline, write-tools, upsert]
dependency_graph:
  requires: ["14-03"]
  provides: [upsert_arc, log_subplot_touchpoint, delete_subplot_touchpoint, upsert_chapter_obligation, delete_chapter_obligation, log_pov_balance_snapshot, delete_pov_balance_snapshot, log_travel_segment]
  affects: [arcs.py, chapters.py, session.py, timeline.py]
tech_stack:
  added: []
  patterns: [two-branch-upsert, log-style-delete, gate-gated-write]
key_files:
  created: []
  modified:
    - src/novel/tools/arcs.py
    - src/novel/tools/chapters.py
    - src/novel/tools/session.py
    - src/novel/tools/timeline.py
decisions:
  - "log_travel_segment is NOT gate-gated per plan spec — return type is TravelSegment | NotFoundResponse | ValidationFailure (no GateViolation), matching the plan's explicit requirement"
  - "pov_balance_snapshots table has chapter_count + word_count fields (not pov_percentage) — used real schema from migration 020 and PovBalanceSnapshot model as truth"
  - "character_structural_obligations uses is_met (bool) + description (NOT NULL), not status field — used real schema from migration 016"
  - "upsert_arc: character_id field not arc_name (CharacterArc model has no arc_name field) — used real model fields: arc_type, starting_state, desired_state, wound, lie_believed, truth_to_learn, opened_chapter_id, closed_chapter_id"
metrics:
  duration_seconds: 242
  completed_date: "2026-03-09"
  tasks_completed: 2
  files_modified: 4
---

# Phase 14 Plan 08: Missing Write Tools (Arcs, Chapters, Session, Timeline) Summary

**One-liner:** Added 8 write tools completing CRUD for character_arcs, subplot_touchpoint_log, chapter_structural_obligations, pov_balance_snapshots, and travel_segments using two-branch upsert and log-style patterns.

## What Was Built

### Task 1: arcs.py — 3 new tools

**upsert_arc** — Two-branch upsert for `character_arcs`. Pre-checks `character_id` exists. Parameters: `character_id`, `arc_type`, `arc_id` (opt), `starting_state`, `desired_state`, `wound`, `lie_believed`, `truth_to_learn`, `opened_chapter_id`, `closed_chapter_id`, `notes`, `canon_status`. Not gate-gated. Returns `CharacterArc | NotFoundResponse | ValidationFailure`.

**log_subplot_touchpoint** — Append-only INSERT into `subplot_touchpoint_log`. Pre-checks both `plot_thread_id` (in `plot_threads`) and `chapter_id` (in `chapters`). Returns `SubplotTouchpoint | NotFoundResponse | ValidationFailure`.

**delete_subplot_touchpoint** — Log-style delete (no try/except). Returns `NotFoundResponse | dict`.

Also: added `SubplotTouchpoint` to import from `novel.models.arcs`. Updated tool count docstrings from 9 to 12.

### Task 2: Three files — 5 new tools

**chapters.py — upsert_chapter_obligation** — Two-branch upsert for `chapter_structural_obligations`. Pre-checks `chapter_id`. Parameters: `chapter_id`, `obligation_type`, `description` (NOT NULL), `obligation_id` (opt), `is_met` (bool), `notes`. Not gate-gated. Returns `ChapterStructuralObligation | NotFoundResponse | ValidationFailure`.

**chapters.py — delete_chapter_obligation** — Log-style delete. Returns `NotFoundResponse | dict`.

**session.py — log_pov_balance_snapshot** — Gate-gated. Append-only INSERT into `pov_balance_snapshots`. Pre-checks optional `chapter_id`. Parameters: `chapter_id` (opt), `character_id` (opt), `chapter_count`, `word_count`. Returns `PovBalanceSnapshot | GateViolation | NotFoundResponse | ValidationFailure`.

**session.py — delete_pov_balance_snapshot** — Gate-gated. Log-style delete. Returns `GateViolation | NotFoundResponse | dict`.

**timeline.py — log_travel_segment** — NOT gate-gated (per plan spec). Pre-checks `character_id` and optional `start_chapter_id`. Columns: `character_id`, `from_location_id`, `to_location_id`, `start_chapter_id`, `end_chapter_id`, `start_event_id`, `elapsed_days`, `travel_method`, `notes`. Returns `TravelSegment | NotFoundResponse | ValidationFailure`.

## Decisions Made

1. **log_travel_segment is NOT gate-gated** — Plan explicitly states this, and the return type confirming no GateViolation. Followed plan over the general pattern in timeline.py where other write tools are gated.

2. **Used real schema fields, not plan interface sketch** — The plan `<interfaces>` section showed simplified/incorrect fields. Used actual Pydantic models and SQL migration files as truth:
   - `PovBalanceSnapshot` has `chapter_count` + `word_count`, not `pov_percentage`
   - `CharacterArc` has `arc_type`, `starting_state`, `desired_state` etc., not `arc_name`
   - `ChapterStructuralObligation` has `is_met` (bool) + `description` (NOT NULL), not `status`

3. **delete_chapter_obligation uses log-style delete** — `chapter_structural_obligations` has no FK children, so no try/except needed.

## Deviations from Plan

None — plan executed exactly as written with one schema correction (Rule 1 auto-fix: used actual DB columns instead of sketch-level interface definitions in plan context).

## Verification

```
All 4 modules import OK
upsert_arc at arcs.py:497
log_subplot_touchpoint at arcs.py:632
upsert_chapter_obligation at chapters.py:328
log_pov_balance_snapshot at session.py:756
log_travel_segment at timeline.py:496
```

## Self-Check: PASSED

- All 4 source files exist and import cleanly
- SUMMARY.md created
- Commit d7f2234: feat(14-08) arcs.py — FOUND
- Commit 805a29d: feat(14-08) chapters/session/timeline — FOUND
