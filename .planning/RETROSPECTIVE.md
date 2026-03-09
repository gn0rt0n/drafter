# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

---

## Milestone: v1.0 — MVP

**Shipped:** 2026-03-09
**Phases:** 12 | **Plans:** 41
**Timeline:** 2 days (2026-03-07 → 2026-03-09)

### What Was Built

- Installable `drafter` Python package: UV-managed, Hatchling build, `novel` CLI + `novel-mcp` stdio server
- 22 SQLite migrations (71 tables, 16 domains) with WAL + FK pragmas enforced on every connection
- 68+ Pydantic models covering all domains; "Age of Embers" seed profile covering all 71 tables
- 103 MCP tools across 18 domains — full character/relationship/world/plot/arc/session/canon/gate/publishing stack
- Architecture gate: 36 SQL-verifiable items enforced at MCP tool level via `check_gate()`
- 7-point structure tracking (Phase 11 insertion) — story-level and per-POV-character arc with 2 new gate items
- Complete reference docs: `docs/schema.md`, `docs/mcp-tools.md`, `docs/README.md`

### What Worked

- **Layered build order**: DB → Pydantic models → MCP tools → gate → remaining domains → docs. Zero rework due to dependency order violations.
- **Migration-as-ground-truth pattern**: Every plan that tried to use plan-prose field names got corrected automatically; using `PRAGMA table_info` and migration SQL as authority eliminated schema drift.
- **register(mcp) pattern**: Consistent function signature across all 18 tool modules made server wiring trivial. Each module is independently testable.
- **Seed profiles** (minimal + gate-ready): Fast test cycles without touching real manuscript. Gate-ready seed was essential for verifying gate enforcement.
- **Decimal phases**: Inserting Phase 11 (7-point structure) and Phase 12 (docs) as numbered extensions rather than scope creep additions was clean.
- **Audit-before-archive**: Running `/gsd:audit-milestone` before completion surfaced tech debt explicitly, giving a clear known-gaps list rather than leaving it implicit.

### What Was Inefficient

- **Count string drift**: "33 items" / "34 items" / "36 items" confusion in gate.py, cli.py, and REQUIREMENTS.md — happened because implementation added items and prose wasn't updated atomically. Left as tech debt.
- **Plan prose vs migration SQL mismatches**: Occurred in Phases 2, 4, 6, 10 — plan descriptions had wrong column names. Auto-fixed each time but added friction. Could be mitigated by running `PRAGMA table_info` in research phase.
- **SUMMARY.md one_liner field**: Not populated in any phase summary — the `gsd-tools summary-extract` CLI returned None for all 41 files. Lost automatic accomplishment extraction for MILESTONES.md; had to write accomplishments manually.
- **ROADMAP.md progress table stale**: Phase 2 and Phase 5 showed wrong counts at audit time. Progress table is too easy to forget to update.

### Patterns Established

- `register(mcp: FastMCP) -> None` — all tool modules use this signature; never expose FastMCP instance directly
- `check_gate()` in `novel.mcp` (not `novel.tools`) — prevents circular import
- SELECT-back after UPDATE (not relying on UPDATE to error on missing row) — established in Phase 8, reinforced in Phase 9
- Append-only for audit log tables (`canon_facts`, `continuity_issues`, `drama_irony`, `motif_occurrences`) — no ON CONFLICT
- Two-branch upsert pattern: `None id → INSERT+lastrowid`, `provided id → ON CONFLICT(id) DO UPDATE`
- `cursor.lastrowid` for INSERT id retrieval in aiosqlite (not `Connection.lastrowid`)
- Gate-violation tests must use function-scoped uncertified DB — not session-scoped certified autouse fixture

### Key Lessons

1. **Migration SQL is always ground truth.** Any plan prose, REQUIREMENTS.md entry, or docstring that names a column is suspect. Verify against `PRAGMA table_info` or the migration file.
2. **Gate item count needs a single canonical source.** A constant `GATE_ITEM_COUNT = 36` exported from gate.py would have prevented all the stale-string drift.
3. **Populate SUMMARY.md one_liner frontmatter field.** The automated accomplishment extraction is useless without it. Add to execute-phase workflow as a required post-step.
4. **Phase insertions (decimal phases) work cleanly** — Phase 11 and 12 extended v1.0 scope without disruption. The naming convention is solid.
5. **Audit before milestone completion is essential.** The `tech_debt` audit status gave a precise debt register rather than leaving gaps implicit.

### Cost Observations

- Model mix: Quality profile (Opus for research/plan agents, Sonnet for execution)
- Sessions: Multiple across 2 days
- Notable: 12 phases / 41 plans in 2 days is high velocity; parallel plan execution within phases contributed significantly

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Phases | Plans | Key Change |
|-----------|--------|-------|------------|
| v1.0 | 12 | 41 | Initial build — established all patterns |

### Cumulative Quality

| Milestone | LOC | Domains | Tools | Gate Items |
|-----------|-----|---------|-------|-----------|
| v1.0 | ~448k | 18 | 103 | 36 |
