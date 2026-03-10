# Phase 13: Tech Debt Clearance - Context

**Gathered:** 2026-03-09
**Status:** Ready for planning

<domain>
## Phase Boundary

Fix all 8 known v1.0 defects: stale gate count strings, CLI help text typo, 4 bugs in docs/README.md, and missing pydantic direct dependency. No new features, no refactoring beyond the listed defects.

</domain>

<decisions>
## Implementation Decisions

### pydantic dependency (DEBT-07)
- Add `pydantic>=2.11` as a direct dependency in pyproject.toml
- Rationale: matches the version currently pulled transitively via mcp>=1.26.0; explicit declaration makes the v2 requirement visible and prevents silent breakage if mcp's transitive dependency changes

### Gate count fix scope (DEBT-01, DEBT-08)
- Fix stale "34" strings in `src/novel/gate/cli.py` (×4 occurrences: help text lines and docstrings for `check` and `certify` commands) → "36"
- REQUIREMENTS.md is also in scope: update the description text that still references "33"/"34" stale counts
- The MCP tool `certify_gate` in `src/novel/tools/gate.py` already uses `_GATE_ITEM_COUNT = len(GATE_QUERIES)` (correct at 36) — no change needed there

### README migration description (DEBT-03)
- The current claim "applied automatically on `uv run novel-mcp`" is false — the MCP server does NOT auto-apply migrations
- Fix: replace with accurate description that migrations require explicit `novel db migrate` invocation; the MCP server requires a pre-initialized database

### README export command name (DEBT-04)
- README says `novel export` subcommand is `regenerate` — actual subcommands are `chapter` and `export-all` (from export/cli.py)
- Fix: update to reflect actual command names

### README gate table names (DEBT-06)
- README says gate state is stored in `gate_certifications` and `gate_checklist_log` — these tables do not exist
- Actual tables: `architecture_gate` (gate record) and `gate_checklist_items` (checklist rows)
- Fix: replace both wrong names with correct names

### README GateViolation type name (DEBT-05)
- Research the exact wrong reference during planning — from code scout, the Python type is `GateViolation` and the README describes the shape as `requires_action: true`. Planner should identify the specific wrong name and correct it.

### CLI help text typo (DEBT-02)
- `src/novel/db/cli.py` line 52 says "gate-ready" (hyphen) in help text; actual dict key is "gate_ready" (underscore)
- Fix both occurrences (line 52 and line 57)

### Claude's Discretion
- Whether to add regression tests for stale string detection (acceptable either way for a bug-fix phase)
- Exact wording of corrected README migration description (accurate and concise)
- Whether to update any comments in gate.py that reference old counts (fix if found, skip if none)

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- No new code to write — all fixes are string replacements and a pyproject.toml edit

### Established Patterns
- pyproject.toml uses `>=major.minor.patch` style for all existing deps (typer, aiosqlite, mcp) — match this pattern for pydantic
- Gate count is dynamic in MCP tools (`_GATE_ITEM_COUNT = len(GATE_QUERIES)`) — CLI has hardcoded strings that need updating

### Integration Points
- `src/novel/gate/cli.py` — gate check and certify CLI commands (stale strings)
- `src/novel/db/cli.py` — seed command help text (help text typo)
- `docs/README.md` — 4 factual bugs in migration description, export command, GateViolation type, table names
- `pyproject.toml` — direct dependency declarations

### Confirmed Bug Locations
| Bug | File | Lines | Fix |
|-----|------|-------|-----|
| DEBT-01 "34-item" | src/novel/gate/cli.py | 7, 9, 20, 110 | → "36-item" / "36 checklist items" |
| DEBT-01 REQUIREMENTS.md | .planning/REQUIREMENTS.md | description text | remove stale "33"/"34" references |
| DEBT-02 gate-ready | src/novel/db/cli.py | 52, 57 | → gate_ready (underscore) |
| DEBT-03 auto-apply | docs/README.md | ~41 | → accurate migration description |
| DEBT-04 export cmd | docs/README.md | ~73 | regenerate → chapter / export-all |
| DEBT-05 type name | docs/README.md | TBD | researcher to identify exact wrong name |
| DEBT-06 table names | docs/README.md | ~122 | gate_certifications → architecture_gate, gate_checklist_log → gate_checklist_items |
| DEBT-07 pydantic | pyproject.toml | dependencies | add pydantic>=2.11 |
| DEBT-08 certify str | src/novel/gate/cli.py | 110 | → "36 checklist items" (covered by DEBT-01 fix) |

</code_context>

<specifics>
## Specific Ideas

- All decisions deferred to Claude's discretion — user requested best long-term project management approach
- pydantic>=2.11 chosen to match current transitive constraint without over-constraining future mcp upgrades

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 13-tech-debt-clearance*
*Context gathered: 2026-03-09*
