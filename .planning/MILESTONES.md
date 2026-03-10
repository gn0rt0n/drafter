# Milestones

## v1.1 Tech Debt & API Completeness (Shipped: 2026-03-10)

**Phases completed:** 3 phases (13–15), 26 plans
**Git range:** docs(13) → docs(phase-15) (2026-03-09, 1 day)
**Stats:** 136 files changed, 16,841 Python LOC

**Key accomplishments:**
1. Cleared tech debt: fixed stale gate count strings (33/34→36) in gate.py and cli.py, corrected `novel db seed` CLI help text, fixed 4 README doc bugs, added pydantic as direct dependency
2. Fixed gate audit/certify count inconsistency — both now operate on 36-item set
3. Added 128 new MCP tools (delete, write, junction) across all 14 domains — achieving full CRUD coverage for all 71 schema tables (231 total tools)
4. Split `docs/mcp-tools.md` (231-tool monolith) into 18 per-domain tool reference files under `docs/tools/`
5. Split `docs/schema.md` into 18 per-domain schema files under `docs/schema/` with read-only justifications
6. Created `docs/README.md` as master navigation index; deleted both monoliths

---

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

