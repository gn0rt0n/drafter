# Milestones

## v1.0 MVP (Shipped: 2026-03-09)

**Phases completed:** 12 phases, 41 plans
**Git range:** Phase 1 → Phase 12 (2026-03-07 → 2026-03-09, 2 days)
**Stats:** 394 files changed, ~448k Python LOC

**Key accomplishments:**
1. Python MCP server scaffolded — installable `drafter` package with `novel` CLI and `novel-mcp` stdio server, UV-managed with Hatchling build
2. 69-table SQLite schema — 22 migration files covering all 14 narrative domains; WAL + FK pragmas enforced on every connection
3. 103 MCP tools across 18 domains — characters, relationships, chapters, scenes, world, plot, arcs, sessions, timeline, canon, knowledge, foreshadowing, names, voice, publishing, structure, gate, magic
4. Gate system with 36 SQL checks — `check_gate()` enforced at tool level; `novel gate run` and `novel gate certify` CLI commands; gate-ready seed profile
5. 7-point structure extension (Phase 11) — story-level and per-POV-character arc tracking integrated into gate with 2 new gate items
6. Complete reference documentation (Phase 12) — `docs/schema.md` (71 tables, 16 domains), `docs/mcp-tools.md` (103 tools), `docs/README.md` (architecture overview)

**Known Tech Debt:**
- `novel db seed gate-ready` CLI help text uses hyphen but dict key uses underscore — correct invocation: `novel db seed gate_ready`
- Stale "33 items" / "34 items" strings in gate.py, cli.py, REQUIREMENTS.md — actual count is 36
- Gate semantic inconsistency: `run_gate_audit` reports 36 items; `certify_gate` checks 37 rows (min_characters row intentional per STATE.md)
- docs/README.md has 4 doc bugs (migration claim, export command, GateViolation type, table names)

---

