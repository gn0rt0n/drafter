---
phase: 14-mcp-api-completeness
plan: "02"
subsystem: mcp-tools
tags: [delete, chapters, scenes, structure, fk-safe, tdd]
dependency_graph:
  requires: [14-01]
  provides: [delete_chapter, delete_scene, delete_scene_goal, delete_story_structure, delete_arc_beat]
  affects: [src/novel/tools/chapters.py, src/novel/tools/scenes.py, src/novel/tools/structure.py]
tech_stack:
  added: []
  patterns: [fk-safe-delete, log-delete]
key_files:
  modified:
    - src/novel/tools/chapters.py
    - src/novel/tools/scenes.py
    - src/novel/tools/structure.py
    - tests/test_chapters.py
    - tests/test_scenes.py
    - tests/test_structure.py
decisions:
  - "FK-safe pattern (try/except ValidationFailure) used for delete_chapter, delete_scene, delete_story_structure — parent tables with known FK children"
  - "Log-delete pattern (no ValidationFailure) used for delete_scene_goal and delete_arc_beat — confirmed leaf tables with no FK children"
  - "No gate checks on any delete tools in these modules — chapters, scenes, structure are gate-free"
metrics:
  duration: "4m 19s"
  completed_date: "2026-03-09"
  tasks_completed: 3
  files_modified: 6
---

# Phase 14 Plan 02: Delete Tools for Chapters, Scenes, and Structure Summary

One-liner: FK-safe delete_chapter, delete_scene, and delete_story_structure plus leaf-table log-deletes for delete_scene_goal and delete_arc_beat — 5 new tools across 3 document-backbone modules.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Add delete_chapter to chapters.py | 0a343f7 | src/novel/tools/chapters.py, tests/test_chapters.py |
| 2 | Add delete_scene and delete_scene_goal to scenes.py | bb38392 | src/novel/tools/scenes.py, tests/test_scenes.py |
| 3 | Add delete_story_structure and delete_arc_beat to structure.py | 46a0fde | src/novel/tools/structure.py, tests/test_structure.py |

## What Was Built

5 delete tools added across 3 modules forming the narrative document backbone:

**chapters.py — delete_chapter (FK-safe):**
- Pre-existence check returns `NotFoundResponse` when chapter absent
- `try/except` catches FK violations and returns `ValidationFailure(errors=[str(exc)])`
- chapters table is heavily referenced (scenes, acts, character state tables, pacing_beats, junction tables)

**scenes.py — delete_scene (FK-safe) + delete_scene_goal (log-delete):**
- `delete_scene`: FK-safe pattern; scene_character_goals references scenes via scene_id
- `delete_scene_goal`: simpler log-delete; scene_character_goals has no FK children

**structure.py — delete_story_structure (FK-safe) + delete_arc_beat (log-delete):**
- `delete_story_structure`: FK-safe pattern; story_structure referenced via book_id FK
- `delete_arc_beat`: simpler log-delete; arc_seven_point_beats is a confirmed leaf table

All tools:
- Return `NotFoundResponse` for absent records (idempotent)
- Use `logging` to stderr (never `print()`)
- Have no gate checks (these modules are gate-free)
- Are properly annotated with union return types

## Test Coverage

10 new TDD tests added (2 per tool):
- `test_delete_chapter_not_found`, `test_delete_chapter_success`
- `test_delete_scene_not_found`, `test_delete_scene_success`
- `test_delete_scene_goal_not_found`, `test_delete_scene_goal_success`
- `test_delete_story_structure_not_found`, `test_delete_story_structure_success`
- `test_delete_arc_beat_not_found`, `test_delete_arc_beat_success`

All 31 tests in test_chapters.py, test_scenes.py, test_structure.py pass.

## Verification

```
grep -c "async def delete_" src/novel/tools/{chapters,scenes,structure}.py
# chapters.py:1  scenes.py:2  structure.py:2
```

All 3 modules import cleanly via `uv run python -c "from novel.tools.X import register"`.

## Deviations from Plan

None — plan executed exactly as written.

## Self-Check: PASSED

- src/novel/tools/chapters.py: FOUND — modified, imports OK
- src/novel/tools/scenes.py: FOUND — modified, imports OK
- src/novel/tools/structure.py: FOUND — modified, imports OK
- Commit 0a343f7: FOUND
- Commit bb38392: FOUND
- Commit 46a0fde: FOUND
