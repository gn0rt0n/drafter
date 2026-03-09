# Roadmap: Drafter

## Milestones

- ✅ **v1.0 MVP** — Phases 1–12 (shipped 2026-03-09)
- 🚧 **v1.1 Tech Debt & API Completeness** — Phases 13–15 (in progress)

## Phases

<details>
<summary>✅ v1.0 MVP (Phases 1–12) — SHIPPED 2026-03-09</summary>

- [x] Phase 1: Project Foundation & Database (3/3 plans) — completed 2026-03-07
- [x] Phase 2: Pydantic Models & Seed Data (4/4 plans) — completed 2026-03-07
- [x] Phase 3: MCP Server Core, Characters & Relationships (3/3 plans) — completed 2026-03-07
- [x] Phase 4: Chapters, Scenes & World (5/5 plans) — completed 2026-03-07
- [x] Phase 5: Plot & Arcs (3/3 plans) — completed 2026-03-07
- [x] Phase 6: Gate System (3/3 plans) — completed 2026-03-07
- [x] Phase 7: Session & Timeline (3/3 plans) — completed 2026-03-08
- [x] Phase 8: Canon, Knowledge & Foreshadowing (3/3 plans) — completed 2026-03-08
- [x] Phase 9: Names, Voice & Publishing (3/3 plans) — completed 2026-03-08
- [x] Phase 10: CLI Completion & Integration Testing (3/3 plans) — completed 2026-03-08
- [x] Phase 11: 7-Point Structure Extension (4/4 plans) — completed 2026-03-09
- [x] Phase 12: Schema & MCP System Documentation (4/4 plans) — completed 2026-03-09

See archive: `.planning/milestones/v1.0-ROADMAP.md`

</details>

### 🚧 v1.1 Tech Debt & API Completeness (In Progress)

**Milestone Goal:** Clear all v1.0 tech debt, fill MCP write-tool gaps, and restructure monolithic docs into per-domain files.

- [ ] **Phase 13: Tech Debt Clearance** - Fix stale gate count strings, CLI help text bug, README doc bugs, and missing pydantic dependency
- [ ] **Phase 14: MCP API Completeness** - Audit all schema tables, implement missing write tools, enforce error contract
- [ ] **Phase 15: Documentation Restructure** - Update and split mcp-tools.md and schema.md into per-domain files, create master index

## Phase Details

### Phase 13: Tech Debt Clearance
**Goal**: All v1.0 known defects are corrected — gate counts are consistent everywhere, CLI help text is accurate, README documentation matches reality, and pydantic is a declared dependency
**Depends on**: Nothing (first phase of v1.1; v1.0 complete)
**Requirements**: DEBT-01, DEBT-02, DEBT-03, DEBT-04, DEBT-05, DEBT-06, DEBT-07, DEBT-08
**Success Criteria** (what must be TRUE):
  1. `novel gate run` and `novel gate certify` output shows "36 items" — no stale "33" or "34" strings appear anywhere in gate.py or cli.py
  2. `novel db seed --help` lists the seed profile as `gate_ready` (underscore), matching the actual dict key used in the seed command
  3. `docs/README.md` accurately describes migrations (no auto-apply claim), correct export command name, correct GateViolation type name, and correct table names
  4. `uv add pydantic` or inspecting `pyproject.toml` confirms pydantic is a declared direct dependency (not only transitive)
  5. `run_gate_audit` and `certify_gate` both operate on the same 36-item set — no off-by-one inconsistency between audit count and certify count
**Plans**: TBD

### Phase 14: MCP API Completeness
**Goal**: Every schema table is either covered by at least one MCP write tool, or has an explicit documented justification for being read-only — no silent gaps in the API surface
**Depends on**: Phase 13
**Requirements**: MCP-01, MCP-02
**Success Criteria** (what must be TRUE):
  1. A full audit of all 71 schema tables against existing MCP tools produces a documented list: tables with write tools, and tables explicitly marked read-only with justification
  2. Every table that was writable-but-unimplemented now has at least one working MCP write tool callable from Claude Code
  3. Every new write tool returns the established error contract: `null` for not-found, `is_valid: false` for validation failures, `requires_action` for gate violations
**Plans**: TBD

### Phase 15: Documentation Restructure
**Goal**: The monolithic mcp-tools.md and schema.md are split into per-domain files that reflect the current implementation (including new tools from Phase 14), with a master index linking all domain files
**Depends on**: Phase 13, Phase 14
**Requirements**: DOCS-01, DOCS-02, DOCS-03
**Success Criteria** (what must be TRUE):
  1. `docs/mcp-tools.md` no longer exists as a monolith — it is replaced by per-domain files (e.g., `docs/tools/characters.md`, `docs/tools/gate.md`) that include all tools from Phase 14
  2. `docs/schema.md` no longer exists as a monolith — it is replaced by per-domain files (e.g., `docs/schema/characters.md`) that include read-only justifications from Phase 14
  3. A master index file (`docs/README.md` or `docs/index.md`) links to every per-domain tool file and every per-domain schema file so the full documentation surface is navigable from one location
**Plans**: TBD

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Project Foundation & Database | v1.0 | 3/3 | Complete | 2026-03-07 |
| 2. Pydantic Models & Seed Data | v1.0 | 4/4 | Complete | 2026-03-07 |
| 3. MCP Server Core, Characters & Relationships | v1.0 | 3/3 | Complete | 2026-03-07 |
| 4. Chapters, Scenes & World | v1.0 | 5/5 | Complete | 2026-03-07 |
| 5. Plot & Arcs | v1.0 | 3/3 | Complete | 2026-03-07 |
| 6. Gate System | v1.0 | 3/3 | Complete | 2026-03-07 |
| 7. Session & Timeline | v1.0 | 3/3 | Complete | 2026-03-08 |
| 8. Canon, Knowledge & Foreshadowing | v1.0 | 3/3 | Complete | 2026-03-08 |
| 9. Names, Voice & Publishing | v1.0 | 3/3 | Complete | 2026-03-08 |
| 10. CLI Completion & Integration Testing | v1.0 | 3/3 | Complete | 2026-03-08 |
| 11. 7-Point Structure Extension | v1.0 | 4/4 | Complete | 2026-03-09 |
| 12. Schema & MCP System Documentation | v1.0 | 4/4 | Complete | 2026-03-09 |
| 13. Tech Debt Clearance | v1.1 | 0/TBD | Not started | - |
| 14. MCP API Completeness | v1.1 | 0/TBD | Not started | - |
| 15. Documentation Restructure | v1.1 | 0/TBD | Not started | - |
