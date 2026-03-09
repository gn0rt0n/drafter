---
phase: 12-schema-and-mcp-system-documentation
plan: "02"
subsystem: documentation
tags: [schema, sqlite, mermaid, reference-docs]
dependency_graph:
  requires: []
  provides: [docs/schema.md]
  affects: []
tech_stack:
  added: []
  patterns: [domain-organized schema documentation, Mermaid ER diagrams per domain, cross-domain FK prose notes]
key_files:
  created:
    - docs/schema.md
  modified: []
decisions:
  - "Field names derived from migration SQL files — not from project-research/database-schema.md (known to have drifted)"
  - "16 domain sections match CONTEXT.md grouping — semantic organization preferred over migration number order"
  - "Cross-domain FKs documented as prose notes below each Mermaid diagram rather than diagram edges"
  - "thematic_mirrors polymorphic FKs documented as plain INTEGER with no SQL FK constraint (by design)"
  - "Gate-free domains (characters, world, chapters, etc.) have no gate flag — flag only appears where check_gate() is called"
  - "name_registry/names domain explicitly documented as gate-free by design (worldbuilding phase tools)"
metrics:
  duration: "26 minutes"
  completed: "2026-03-09T16:24:50Z"
  tasks_completed: 1
  files_created: 1
---

# Phase 12 Plan 02: Schema Documentation Summary

Complete SQLite schema reference with all 71 tables across 22 migrations organized into 16 semantic domains, each with a Mermaid ER diagram, per-table field documentation, FK relationships, lifecycle notes, and gate flags.

## What Was Built

`docs/schema.md` — 2670-line implementation-accurate schema reference.

**Structure:**
- File header with status note pointing to migration SQL as source of truth
- System Integration section: domain dependency flowchart (Mermaid) + cross-domain FK summary table
- 16 domain sections in dependency order (Foundation → Structure → World → Characters → Chapters & Scenes → Relationships → Timeline & Events → Plot & Arcs → Gate & Metrics → Session → Canon & Continuity → Knowledge & Reader → Foreshadowing & Literary → Voice & Names → Publishing → Utility)

**Per domain section:**
- 1-2 sentence overview
- Mermaid ER diagram (tables and FKs within the domain only)
- Cross-domain FK prose note below diagram
- Gate flag where applicable (⚠️ Gate-enforced writes)

**Per table entry:**
- Purpose statement
- Field table: name, type, description (FK fields note exact target)
- Constraints (UNIQUE, notable constraints)
- Populated by (which MCP tools write to it, or "Not writable via MCP")
- Gate flag where the domain calls check_gate()

## Verification Results

| Check | Result |
|-------|--------|
| File exists | PASS |
| Line count ≥ 800 | PASS — 2670 lines |
| erDiagram count == 16 | PASS — 16 |
| open_questions has `question` field (not `question_text`) | PASS |
| arc_seven_point_beats UNIQUE(arc_id, beat_type) noted | PASS |
| Gate flag in Session, Timeline, Canon, Knowledge, Foreshadowing, Voice, Publishing | PASS |
| All 71 table names present | PASS |
| Spot-check tables (submission_tracker, thematic_mirrors, pov_chronological_position) | PASS |

## Deviations from Plan

None — plan executed exactly as written. All source material was read from migration SQL files before writing any documentation content.

## Self-Check

**Files created:**
- `docs/schema.md` — FOUND

**Commits:**
- `ceb50d4` — FOUND (feat(12-02): create docs/schema.md — complete SQLite schema reference)

## Self-Check: PASSED
