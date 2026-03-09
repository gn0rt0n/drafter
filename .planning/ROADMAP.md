# Roadmap: Drafter

## Overview

Drafter delivers a complete Python MCP server with ~80 tools across 14 domains, a SQLite narrative database, and a UV-managed CLI for AI-assisted novel writing at scale. The build follows a strictly layered order: database schema and project scaffolding first, then Pydantic models and seed data, then MCP server with domain tools built in dependency order (characters before relationships, chapters before plot threads), then the gate enforcement system, then remaining domains in natural clusters, and finally CLI completion. Each phase delivers a coherent, testable capability.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Project Foundation & Database** - pyproject.toml, migrations, connection factory, and database CLI commands (completed 2026-03-07)
- [ ] **Phase 2: Pydantic Models & Seed Data** - Domain models, error contract types, minimal seed profile, and schema validation tests
- [x] **Phase 3: MCP Server Core, Characters & Relationships** - FastMCP server setup, error contract enforcement, and first two domain tool modules (completed 2026-03-07)
- [x] **Phase 4: Chapters, Scenes & World** - Chapter/scene structure tools and world-building domain tools (completed 2026-03-07)
- [x] **Phase 5: Plot & Arcs** - Plot threads, character arcs, Chekhov's guns, and subplot tracking tools (completed 2026-03-07)
- [x] **Phase 6: Gate System** - Architecture gate with 33 SQL checks, gate enforcement helper, gate-ready seed, and gate CLI commands (completed 2026-03-07)
- [x] **Phase 7: Session & Timeline** - Session management, project metrics, timeline events, and travel validation tools (completed 2026-03-08)
- [x] **Phase 8: Canon, Knowledge & Foreshadowing** - Continuity tracking, reader state, dramatic irony, foreshadowing, and literary device tools (completed 2026-03-08)
- [x] **Phase 9: Names, Voice & Publishing** - Name registry, voice profiles, and publishing asset tools (completed 2026-03-08)
- [x] **Phase 10: CLI Completion & Integration Testing** - Remaining CLI subcommands (session, query, export, name) and full-scale tool selection validation (completed 2026-03-08)

## Phase Details

### Phase 1: Project Foundation & Database
**Goal**: A working Python project with both entry points verified, all 21 SQL migrations executing cleanly, and full database lifecycle management from the CLI
**Depends on**: Nothing (first phase)
**Requirements**: SETUP-01, SETUP-02, SETUP-03, SETUP-04, CLDB-01, CLDB-02, CLDB-03, CLDB-04
**Success Criteria** (what must be TRUE):
  1. `uv run novel --help` and `uv run novel-mcp --help` both produce output without errors
  2. `novel db migrate` creates a SQLite database with all tables from 21 migrations in under 5 seconds
  3. `novel db reset` drops and rebuilds the database cleanly, and `novel db status` displays migration version and table/row counts
  4. Every database connection (sync and async) enforces WAL mode and `PRAGMA foreign_keys=ON` -- verified by inserting an invalid FK reference and confirming rejection
**Plans**: 3 plans

Plans:
- [ ] 01-01-PLAN.md — Project scaffold + entry points + connection factory
- [ ] 01-02-PLAN.md — 21 SQL migration files (complete narrative schema)
- [ ] 01-03-PLAN.md — Migration runner + CLI db commands + end-to-end verification

### Phase 2: Pydantic Models & Seed Data
**Goal**: Typed input/output models exist for every domain, seed data enables tool testing without real manuscript content, and automated tests catch schema drift
**Depends on**: Phase 1
**Requirements**: SEED-01, SEED-03, TEST-01, TEST-02
**Success Criteria** (what must be TRUE):
  1. Pydantic models exist for all 14 domains plus shared error types (NotFoundResponse, ValidationFailure, GateViolation) and every model field matches its corresponding SQL column from `PRAGMA table_info`
  2. `novel db seed minimal` loads a seed profile that populates every domain table with representative data (1 book, 2-3 characters, 1 chapter, 2 scenes, entries in each domain table)
  3. Schema validation test passes -- comparing every Pydantic model field against the SQL schema -- and clean-rebuild test confirms all FK constraints hold after migrate + seed
**Plans**: 4 plans

Plans:
- [ ] 02-01-PLAN.md — Foundation models: shared error types + world + characters + relationships (Wave 1)
- [ ] 02-02-PLAN.md — Narrative models: chapters + scenes + plot + arcs + voice (Wave 1, parallel)
- [ ] 02-03-PLAN.md — Remaining models: sessions + timeline + canon + gate + publishing + magic + pacing; minimal seed data (Wave 1, parallel)
- [ ] 02-04-PLAN.md — __init__.py re-exports + schema validation tests + clean-rebuild tests (Wave 2)

### Phase 3: MCP Server Core, Characters & Relationships
**Goal**: A working MCP server callable from Claude Code with the error contract enforced and two tightly coupled domains (characters and relationships) fully operational
**Depends on**: Phase 2
**Requirements**: ERRC-01, ERRC-02, ERRC-03, ERRC-04, CHAR-01, CHAR-02, CHAR-03, CHAR-04, CHAR-05, CHAR-06, CHAR-07, REL-01, REL-02, REL-03, REL-04, REL-05, REL-06
**Success Criteria** (what must be TRUE):
  1. `uv run novel-mcp` starts the MCP server via stdio transport and Claude Code can discover and call tools
  2. Claude can retrieve, list, create, and update character records, including state-at-chapter, injuries, beliefs, and knowledge logging
  3. Claude can retrieve, list, create, and update relationships and perception profiles, including relationship change logging
  4. Every tool returns `null` with `not_found_message` for missing records, `is_valid: false` with `errors` for validation failures, and no `print()` statements exist in server code
  5. In-memory FastMCP client tests verify callable interface for all character and relationship tools
**Plans**: 3 plans

Plans:
- [ ] 03-01-PLAN.md — Character domain tools: 7 tools in tools/characters.py via register(mcp) (Wave 1)
- [ ] 03-02-PLAN.md — Relationship domain tools: 6 tools in tools/relationships.py via register(mcp) (Wave 1, parallel)
- [ ] 03-03-PLAN.md — Server wiring + pytest-asyncio + conftest + MCP client tests for all 13 tools (Wave 2)

### Phase 4: Chapters, Scenes & World
**Goal**: Claude can manage the full chapter/scene structure and world-building data (locations, factions, cultures, magic system) through MCP tools
**Depends on**: Phase 3
**Requirements**: CHAP-01, CHAP-02, CHAP-03, CHAP-04, CHAP-05, CHAP-06, CHAP-07, CHAP-08, CHAP-09, WRLD-01, WRLD-02, WRLD-03, WRLD-04, WRLD-05, WRLD-06, WRLD-07, WRLD-08, WRLD-09, WRLD-10
**Success Criteria** (what must be TRUE):
  1. Claude can retrieve chapters with plans, obligations, and metadata, and list all chapters in a book
  2. Claude can retrieve scenes with full details and character goals, and create/update chapters, scenes, and scene goals
  3. Claude can retrieve locations with sensory profiles, factions with political state, cultures, and magic system elements
  4. Claude can check magic compliance, log magic use events, retrieve practitioner abilities, and create/update locations and factions
  5. All new tools follow the established error contract and pass in-memory FastMCP client tests
**Plans**: 5 plans

Plans:
- [ ] 04-01-PLAN.md — Chapter tools: ChapterPlan model + 5 tools in tools/chapters.py (Wave 1)
- [ ] 04-02-PLAN.md — Scene tools: 4 tools in tools/scenes.py with JSON serialization (Wave 1, parallel)
- [ ] 04-03-PLAN.md — World tools: 6 tools in tools/world.py for locations, factions, political state, cultures (Wave 1, parallel)
- [ ] 04-04-PLAN.md — Magic tools: MagicComplianceResult model + 4 tools in tools/magic.py incl. check_magic_compliance (Wave 1, parallel)
- [ ] 04-05-PLAN.md — Server wiring + MCP client tests for all 19 new tools (Wave 2)

### Phase 5: Plot & Arcs
**Goal**: Claude can manage plot threads, character arcs, Chekhov's gun tracking, and subplot gap detection through MCP tools
**Depends on**: Phase 4
**Requirements**: PLOT-01, PLOT-02, PLOT-03, PLOT-04, PLOT-05, PLOT-06, PLOT-07, PLOT-08, PLOT-09
**Success Criteria** (what must be TRUE):
  1. Claude can retrieve and list plot threads, and create/update plot thread records
  2. Claude can retrieve character arcs and arc health status, and log arc health at a chapter
  3. Claude can retrieve and create/update Chekhov's gun registry entries, and retrieve subplots overdue for touchpoints
**Plans**: 3 plans

Plans:
- [ ] 05-01-PLAN.md — Plot thread tools: 3 tools in tools/plot.py (get_plot_thread, list_plot_threads, upsert_plot_thread) (Wave 1)
- [ ] 05-02-PLAN.md — Arc tools: 6 tools in tools/arcs.py (get_arc, get_arc_health, get_chekovs_guns, upsert_chekov, get_subplot_touchpoint_gaps, log_arc_health) (Wave 1, parallel)
- [ ] 05-03-PLAN.md — Server wiring + MCP client tests for all 9 new tools (Wave 2)

### Phase 6: Gate System
**Goal**: The architecture gate correctly blocks prose-phase operations when the 33-item checklist is incomplete, with full audit, certification, and CLI access
**Depends on**: Phase 5
**Requirements**: GATE-01, GATE-02, GATE-03, GATE-04, GATE-05, GATE-06, SEED-02, CLSG-03, CLSG-04, CLSG-05
**Success Criteria** (what must be TRUE):
  1. `get_gate_status` returns certified/not-certified with blocking item count, and `get_gate_checklist` shows per-item pass/fail with missing record counts
  2. `run_gate_audit` executes all 33 SQL evidence queries and returns a structured gap report
  3. `certify_gate` writes a certification record when all 33 items pass, and refuses when any item fails
  4. The shared `check_gate()` helper is called at the top of every prose-phase tool and returns a `GateViolation` object (not exception) when gate is not certified
  5. `novel gate check`, `novel gate status`, and `novel gate certify` CLI commands work, and the gate-ready seed profile satisfies all 33 checklist items
**Plans**: 3 plans

Plans:
- [ ] 06-01-PLAN.md — 5 MCP gate tools + GateAuditReport model + 33 SQL evidence queries in tools/gate.py (Wave 1)
- [ ] 06-02-PLAN.md — check_gate() helper in mcp/gate.py + gate_ready seed profile + server.py wiring (Wave 2)
- [ ] 06-03-PLAN.md — CLI gate commands (check/status/certify) + MCP tests for all 5 gate tools (Wave 3)

### Phase 7: Session & Timeline
**Goal**: Claude can manage writing sessions with briefings and summaries, track project metrics, and validate timeline consistency including travel realism
**Depends on**: Phase 6
**Requirements**: SESS-01, SESS-02, SESS-03, SESS-04, SESS-05, SESS-06, SESS-07, SESS-08, SESS-09, SESS-10, TIME-01, TIME-02, TIME-03, TIME-04, TIME-05, TIME-06, TIME-07, TIME-08
**Success Criteria** (what must be TRUE):
  1. Claude can start a session with a briefing from the last session, close a session with summary and carried-forward items, and retrieve the most recent session log
  2. Claude can log agent runs, retrieve and log project metrics snapshots, retrieve POV balance, and manage open questions (log, retrieve, answer)
  3. Claude can retrieve POV positions at a chapter, list timeline events by chapter/time range, and create/update events and POV positions
  4. Claude can retrieve travel segments and validate whether travel between locations is realistic given elapsed in-story time
**Plans**: 3 plans

Plans:
- [ ] 07-01-PLAN.md — Core session tools: 7 tools in tools/session.py (start_session, close_session, get_last_session, log_agent_run, get_project_metrics, log_project_snapshot, get_pov_balance) (Wave 1)
- [ ] 07-02-PLAN.md — Open questions + timeline reads: 3 question tools added to session.py + 5 tools in tools/timeline.py (Wave 2)
- [ ] 07-03-PLAN.md — Timeline writes + validation + server.py wiring + MCP tests for all 18 tools (Wave 3)

### Phase 8: Canon, Knowledge & Foreshadowing
**Goal**: Claude can track canon facts, story decisions, continuity issues, reader information state, dramatic irony, foreshadowing, prophecies, motifs, and thematic structures
**Depends on**: Phase 7
**Requirements**: CANO-01, CANO-02, CANO-03, CANO-04, CANO-05, CANO-06, CANO-07, KNOW-01, KNOW-02, KNOW-03, KNOW-04, KNOW-05, FORE-01, FORE-02, FORE-03, FORE-04, FORE-05, FORE-06, FORE-07, FORE-08
**Success Criteria** (what must be TRUE):
  1. Claude can retrieve canon facts by domain, log new facts, log and retrieve story decisions, and log/retrieve/resolve continuity issues filtered by severity
  2. Claude can retrieve reader information state at a chapter, the dramatic irony inventory, and planned/actual reader reveals, and can update reader state and log dramatic irony entries
  3. Claude can retrieve foreshadowing entries with plant/payoff chapters, prophecy registry entries, and motif registry with occurrences
  4. Claude can retrieve thematic mirrors, opposition pairs, and log foreshadowing entries and motif occurrences
**Plans**: 3 plans

Plans:
- [ ] 08-01-PLAN.md — StoryDecision model + 7 canon tools (get_canon_facts, log_canon_fact, log_decision, get_decisions, log_continuity_issue, get_continuity_issues, resolve_continuity_issue) (Wave 1)
- [ ] 08-02-PLAN.md — 5 knowledge tools (get_reader_state, get_dramatic_irony_inventory, get_reader_reveals, upsert_reader_state, log_dramatic_irony) (Wave 1, parallel)
- [ ] 08-03-PLAN.md — 8 foreshadowing tools + server.py wiring for all 3 modules + in-memory FastMCP tests for all 20 tools (Wave 2)

### Phase 9: Names, Voice & Publishing
**Goal**: Claude can manage the name registry with conflict detection and cultural suggestions, voice profiles with drift tracking, and publishing assets with submission tracking
**Depends on**: Phase 8
**Requirements**: NAME-01, NAME-02, NAME-03, NAME-04, VOIC-01, VOIC-02, VOIC-03, VOIC-04, VOIC-05, PUBL-01, PUBL-02, PUBL-03, PUBL-04, PUBL-05
**Success Criteria** (what must be TRUE):
  1. Claude can check name conflicts, register names with cultural context, retrieve the full registry, and get culturally consistent name suggestions for a faction/region
  2. Claude can retrieve and create/update voice profiles, retrieve supernatural voice guidelines, and log/retrieve voice drift instances
  3. Claude can retrieve and create/update publishing assets, retrieve submission tracker entries, log new submissions, and update submission status
**Plans**: 3 plans

Plans:
- [ ] 09-01-PLAN.md — Names domain: 4 gate-free tools in tools/names.py (check_name, register_name, get_name_registry, generate_name_suggestions) (Wave 1)
- [ ] 09-02-PLAN.md — Voice domain: 5 gated tools in tools/voice.py (get_voice_profile, upsert_voice_profile, get_supernatural_voice_guidelines, log_voice_drift, get_voice_drift_log) (Wave 1, parallel)
- [ ] 09-03-PLAN.md — Publishing domain: 5 gated tools in tools/publishing.py + server.py wiring + MCP tests for all 14 tools (Wave 2)

### Phase 10: CLI Completion & Integration Testing
**Goal**: All remaining CLI subcommands work, and tool selection accuracy is validated at full 99-tool scale
**Depends on**: Phase 9
**Requirements**: CLSG-01, CLSG-02, CLSG-06, CLSG-07, CLSG-08, CLEX-01, CLEX-02, CLNM-01, CLNM-02, CLNM-03, TEST-03, TEST-04
**Success Criteria** (what must be TRUE):
  1. `novel session start` displays a briefing and `novel session close` writes a session log
  2. `novel query pov-balance`, `novel query arc-health`, and `novel query thread-gaps` display correct data from the database
  3. `novel export chapter [n]` regenerates a single chapter markdown and `novel export all` regenerates all chapter files from database records
  4. `novel name check`, `novel name register`, and `novel name suggest` work from the CLI
  5. In-memory MCP tool tests cover every tool with error contract compliance, and tool selection accuracy check confirms representative queries trigger correct tools at 99-tool scale
**Plans**: 3 plans

Plans:
- [ ] 10-01-PLAN.md — Session + Query CLI: novel session start/close + novel query pov-balance/arc-health/thread-gaps (Wave 1)
- [ ] 10-02-PLAN.md — Export + Name CLI: novel export chapter/all + novel name check/register/suggest (Wave 1, parallel)
- [ ] 10-03-PLAN.md — Integration tests: TEST-03 error contract gap fills + TEST-04 test_tool_selection.py (Wave 2)

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5 -> 6 -> 7 -> 8 -> 9 -> 10 -> 11 -> 12

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Project Foundation & Database | 3/3 | Complete   | 2026-03-07 |
| 2. Pydantic Models & Seed Data | 2/4 | In Progress|  |
| 3. MCP Server Core, Characters & Relationships | 3/3 | Complete    | 2026-03-07 |
| 4. Chapters, Scenes & World | 5/5 | Complete   | 2026-03-07 |
| 5. Plot & Arcs | 2/3 | Complete    | 2026-03-07 |
| 6. Gate System | 3/3 | Complete    | 2026-03-07 |
| 7. Session & Timeline | 3/3 | Complete    | 2026-03-08 |
| 8. Canon, Knowledge & Foreshadowing | 3/3 | Complete   | 2026-03-08 |
| 9. Names, Voice & Publishing | 3/3 | Complete    | 2026-03-08 |
| 10. CLI Completion & Integration Testing | 3/3 | Complete    | 2026-03-08 |
| 11. 7-Point Structure & Gate Extension | 4/4 | Complete    | 2026-03-09 |
| 12. Schema and MCP System Documentation | 2/3 | In Progress|  |

### Phase 11: Update schema, CLI, MCP, and planning docs to support 7-point structure and 3-act/7-point integration

**Goal:** Add 7-point structure tracking at story level and per-POV-character arc, extend the gate to enforce complete beat coverage, and update all related planning docs
**Requirements**: STRUCT-01, STRUCT-02, STRUCT-03, STRUCT-04, STRUCT-05, STRUCT-06, STRUCT-07
**Depends on:** Phase 10
**Plans:** 4/4 plans complete

Plans:
- [ ] 11-01-PLAN.md — Migration 022 + Pydantic models (StoryStructure, ArcSevenPointBeat) + models/__init__.py (Wave 1)
- [ ] 11-02-PLAN.md — Gate extension (36 items) + gate_ready seed rows for new tables (Wave 1, parallel)
- [ ] 11-03-PLAN.md — tools/structure.py (4 tools) + server.py wiring + test updates + database-schema.md (Wave 2)

### Phase 12: Schema and MCP System Documentation

**Goal:** Create implementation-accurate reference documentation for the complete system: docs/schema.md (71 tables, 16 domains, Mermaid ER diagrams), docs/mcp-tools.md (103 tools, 18 domains, full tool cards), and docs/README.md (architecture overview and navigation entry point)
**Requirements**: TBD (documentation phase — no formal requirement IDs)
**Depends on:** Phase 11
**Plans:** 2/3 plans executed

Plans:
- [ ] 12-01-PLAN.md — docs/README.md (architecture overview) + pointer note in project-research/database-schema.md (Wave 1)
- [ ] 12-02-PLAN.md — docs/schema.md: 71 tables, 16 domains, Mermaid ER diagrams, derived from migration SQL (Wave 1, parallel)
- [ ] 12-03-PLAN.md — docs/mcp-tools.md: 103 tools, 18 domains, full tool cards, derived from Python tool modules (Wave 1, parallel)
