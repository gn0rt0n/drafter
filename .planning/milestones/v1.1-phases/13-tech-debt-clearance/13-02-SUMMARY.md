---
phase: 13-tech-debt-clearance
plan: "02"
subsystem: docs
tags: [readme, documentation, pyproject, pydantic, dependencies]

# Dependency graph
requires: []
provides:
  - "docs/README.md corrected: accurate migration description, export subcommands, error contract, gate table names"
  - "pyproject.toml: pydantic>=2.11 declared as direct dependency"
affects: [15-docs-overhaul]

# Tech tracking
tech-stack:
  added: []
  patterns: []

key-files:
  created: []
  modified:
    - docs/README.md
    - pyproject.toml

key-decisions:
  - "DEBT-04: export subcommand confirmed as 'chapter' and 'all' (not 'export-all') — source-verified from src/novel/export/cli.py"
  - "DEBT-07: pydantic pinned at >=2.11 with no patch version, matching >=major.minor style used by typer and aiosqlite"

patterns-established: []

requirements-completed:
  - DEBT-03
  - DEBT-04
  - DEBT-05
  - DEBT-06
  - DEBT-07

# Metrics
duration: 2min
completed: 2026-03-09
---

# Phase 13 Plan 02: Documentation Corrections & Pydantic Direct Dependency Summary

**Four factual README bugs corrected (migrations, export subcommands, GateViolation type, gate table names) and pydantic>=2.11 declared as explicit direct dependency**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-03-09T17:44:21Z
- **Completed:** 2026-03-09T17:46:30Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Corrected false auto-apply migration claim in README (DEBT-03)
- Fixed export subcommand from non-existent `regenerate` to actual `chapter`, `all` (DEBT-04)
- Fixed GateViolation error contract table row from `requires_action: true` (bool + separate message) to `requires_action: str` (DEBT-05)
- Fixed gate table names from `gate_certifications`/`gate_checklist_log` to `architecture_gate`/`gate_checklist_items` (DEBT-06)
- Added `pydantic>=2.11` as declared direct dependency in pyproject.toml (DEBT-07)

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix four factual bugs in docs/README.md** - `cb33dcf` (fix)
2. **Task 2: Add pydantic as a declared direct dependency** - `8dbcbe1` (chore)

**Plan metadata:** (to be added after final commit)

## Files Created/Modified

- `docs/README.md` — four factual corrections to migration description, CLI export subcommands, error contract table, and gate table names
- `pyproject.toml` — added `"pydantic>=2.11"` to dependencies list

## Decisions Made

- Export subcommand name confirmed as `all` (not `export-all`) via source verification of `src/novel/export/cli.py` line 149: `@app.command(name="all")`. The CONTEXT.md text was stale.
- Pydantic pinned with `>=2.11` (no patch suffix) to match the `>=major.minor` style used by typer and aiosqlite, avoiding over-constraining future mcp upgrades.

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- docs/README.md is now accurate for system-admin readers
- pyproject.toml explicitly declares the pydantic v2 requirement
- Phase 15 docs overhaul can now update README as a clean baseline

---
*Phase: 13-tech-debt-clearance*
*Completed: 2026-03-09*

## Self-Check: PASSED

- docs/README.md: FOUND
- pyproject.toml: FOUND
- 13-02-SUMMARY.md: FOUND
- commit cb33dcf: FOUND
- commit 8dbcbe1: FOUND
