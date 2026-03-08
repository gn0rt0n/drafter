# Requirements: Drafter

**Defined:** 2026-03-07
**Core Value:** Claude Code can query and update all story data through typed MCP tool calls — no raw SQL, no markdown parsing — enabling consistent AI collaboration at novel scale.

## v1 Requirements

### Project Setup

- [x] **SETUP-01**: `pyproject.toml` configures two entry points — `novel` (CLI) and `novel-mcp` (MCP server) — both invocable via `uv run` with no global installs
- [x] **SETUP-02**: All 21 SQL migration files exist and define the complete narrative schema (books, characters, world, plot, timeline, gate, publishing, session, etc.)
- [x] **SETUP-03**: `novel db migrate` runs all migrations in order, with clean-rebuild support (drop + recreate), completing in under 5 seconds
- [x] **SETUP-04**: Database connection factory enables WAL mode and `PRAGMA foreign_keys=ON` on every connection (both sync sqlite3 and async aiosqlite)

### Seed Data

- [x] **SEED-01**: Minimal seed profile provides enough data to exercise every MCP domain (1 book, 2-3 characters, 1 chapter, 2 scenes, 1 session, representative entries in each domain)
- [x] **SEED-02**: Gate-ready seed profile satisfies all 33 architecture gate checklist items so gate certification can be tested with seed data
- [x] **SEED-03**: `novel db seed [profile]` CLI command loads a named seed profile into the database

### Error Contract (Cross-Cutting)

- [x] **ERRC-01**: Every MCP tool returns `null` with a `not_found_message` field when a record is not found — never raises an exception
- [x] **ERRC-02**: Every MCP tool returns a record with `is_valid: false` and `errors: []` on validation failure — never raises an exception
- [x] **ERRC-03**: Prose-phase tools return a `requires_action` field describing what gate action must happen first when gate is not certified
- [x] **ERRC-04**: No `print()` exists in MCP server code — all logging goes to stderr via the `logging` module

### MCP — Characters Domain

- [x] **CHAR-01**: Claude can retrieve a character's full profile by ID (`get_character`)
- [x] **CHAR-02**: Claude can retrieve a character's state (location, injuries, beliefs, knowledge) at a given chapter (`get_character_state`)
- [x] **CHAR-03**: Claude can list all characters in the book (`list_characters`)
- [x] **CHAR-04**: Claude can create or update a character record (`upsert_character`)
- [x] **CHAR-05**: Claude can log what a character learns at a specific chapter (`log_character_knowledge`)
- [x] **CHAR-06**: Claude can retrieve a character's injury history (`get_character_injuries`)
- [x] **CHAR-07**: Claude can retrieve a character's current beliefs (`get_character_beliefs`)

### MCP — Relationships Domain

- [x] **REL-01**: Claude can retrieve the relationship between two characters (`get_relationship`)
- [x] **REL-02**: Claude can retrieve how one character perceives another (`get_perception_profile`)
- [x] **REL-03**: Claude can list all relationships for a character (`list_relationships`)
- [x] **REL-04**: Claude can create or update a character relationship (`upsert_relationship`)
- [x] **REL-05**: Claude can create or update a perception profile (`upsert_perception_profile`)
- [x] **REL-06**: Claude can log a change event in a character relationship (`log_relationship_change`)

### MCP — Chapters & Scenes Domain

- [x] **CHAP-01**: Claude can retrieve a chapter with its plan and metadata (`get_chapter`)
- [x] **CHAP-02**: Claude can retrieve a chapter's writing plan (`get_chapter_plan`)
- [x] **CHAP-03**: Claude can retrieve a chapter's structural obligations (`get_chapter_obligations`)
- [x] **CHAP-04**: Claude can retrieve a scene with full details (`get_scene`)
- [x] **CHAP-05**: Claude can retrieve character goals for a scene (`get_scene_character_goals`)
- [x] **CHAP-06**: Claude can list all chapters in the book (`list_chapters`)
- [x] **CHAP-07**: Claude can create or update a chapter record (`upsert_chapter`)
- [x] **CHAP-08**: Claude can create or update a scene record (`upsert_scene`)
- [x] **CHAP-09**: Claude can create or update a character goal for a scene (`upsert_scene_goal`)

### MCP — Plot & Arcs Domain

- [x] **PLOT-01**: Claude can retrieve a plot thread by ID (`get_plot_thread`)
- [x] **PLOT-02**: Claude can list all plot threads in the book (`list_plot_threads`)
- [x] **PLOT-03**: Claude can retrieve Chekhov's gun registry entries (`get_chekovs_guns`)
- [x] **PLOT-04**: Claude can retrieve a character arc (`get_arc`)
- [x] **PLOT-05**: Claude can retrieve arc health status for a character (`get_arc_health`)
- [x] **PLOT-06**: Claude can retrieve subplots that are overdue for a touchpoint (`get_subplot_touchpoint_gaps`)
- [x] **PLOT-07**: Claude can create or update a plot thread (`upsert_plot_thread`)
- [x] **PLOT-08**: Claude can create or update a Chekhov's gun entry (`upsert_chekov`)
- [x] **PLOT-09**: Claude can log arc health for a character at a chapter (`log_arc_health`)

### MCP — World Domain

- [x] **WRLD-01**: Claude can retrieve a location with its sensory profile (`get_location`)
- [x] **WRLD-02**: Claude can retrieve a faction's profile (`get_faction`)
- [x] **WRLD-03**: Claude can retrieve a faction's current political state (`get_faction_political_state`)
- [x] **WRLD-04**: Claude can retrieve a culture record (`get_culture`)
- [x] **WRLD-05**: Claude can retrieve a magic system element with its rules and limitations (`get_magic_element`)
- [x] **WRLD-06**: Claude can retrieve a character's practitioner abilities (`get_practitioner_abilities`)
- [x] **WRLD-07**: Claude can log a magic use event (`log_magic_use`)
- [x] **WRLD-08**: Claude can check whether a proposed magic action is compliant with system rules (`check_magic_compliance`)
- [x] **WRLD-09**: Claude can create or update a location record (`upsert_location`)
- [x] **WRLD-10**: Claude can create or update a faction record (`upsert_faction`)

### MCP — Gate & Architecture Domain

- [x] **GATE-01**: Claude can retrieve the current gate status (certified/not-certified, blocking item count) (`get_gate_status`)
- [x] **GATE-02**: Claude can run a full gate audit that evaluates all 33 SQL checklist queries and returns a gap report (`run_gate_audit`)
- [x] **GATE-03**: Claude can retrieve the gate checklist with per-item pass/fail status and missing record counts (`get_gate_checklist`)
- [x] **GATE-04**: Claude can manually update a checklist item's status (`update_checklist_item`)
- [x] **GATE-05**: Claude can certify the gate when all 33 items pass, writing a certification record (`certify_gate`)
- [x] **GATE-06**: A shared `check_gate()` helper function is called at the top of every prose-phase tool; returns a `GateViolation` object (not an exception) if gate is not certified

### MCP — Session & Project Domain

- [x] **SESS-01**: Claude can start a new writing session with a briefing from the last session's log (`start_session`)
- [x] **SESS-02**: Claude can close the current session, logging a summary and carrying open items forward (`close_session`)
- [x] **SESS-03**: Claude can retrieve the most recent session log (`get_last_session`)
- [x] **SESS-04**: Claude can log an agent run record (`log_agent_run`)
- [x] **SESS-05**: Claude can retrieve project-level metrics (word count, chapter count, session count) (`get_project_metrics`)
- [x] **SESS-06**: Claude can log a project metrics snapshot (`log_project_snapshot`)
- [x] **SESS-07**: Claude can retrieve POV balance across chapters (chapter count and word count per POV character) (`get_pov_balance`)
- [x] **SESS-08**: Claude can retrieve open questions (`get_open_questions`)
- [x] **SESS-09**: Claude can log a new open question (`log_open_question`)
- [x] **SESS-10**: Claude can mark an open question as answered (`answer_open_question`)

### MCP — Timeline Domain

- [x] **TIME-01**: Claude can retrieve all POV character positions at a given chapter (`get_pov_positions`)
- [x] **TIME-02**: Claude can retrieve a specific POV character's chronological position (`get_pov_position`)
- [x] **TIME-03**: Claude can retrieve a timeline event by ID (`get_event`)
- [x] **TIME-04**: Claude can list events within a chapter range or time range (`list_events`)
- [x] **TIME-05**: Claude can retrieve travel segments for a character (`get_travel_segments`)
- [x] **TIME-06**: Claude can validate whether travel between two locations is realistic given elapsed in-story time (`validate_travel_realism`)
- [x] **TIME-07**: Claude can create or update a timeline event (`upsert_event`)
- [x] **TIME-08**: Claude can create or update a POV chronological position (`upsert_pov_position`)

### MCP — Canon & Continuity Domain

- [x] **CANO-01**: Claude can retrieve canon facts for a named domain (magic, politics, geography, etc.) (`get_canon_facts`)
- [x] **CANO-02**: Claude can log a new canon fact (`log_canon_fact`)
- [x] **CANO-03**: Claude can log a story decision (`log_decision`)
- [x] **CANO-04**: Claude can retrieve the decisions log (`get_decisions`)
- [x] **CANO-05**: Claude can log a continuity issue with severity (`log_continuity_issue`)
- [x] **CANO-06**: Claude can retrieve open continuity issues filtered by severity (`get_continuity_issues`)
- [x] **CANO-07**: Claude can mark a continuity issue as resolved (`resolve_continuity_issue`)

### MCP — Knowledge & Reader State Domain

- [x] **KNOW-01**: Claude can retrieve reader information state at a chapter (what readers know at that point) (`get_reader_state`)
- [x] **KNOW-02**: Claude can retrieve the dramatic irony inventory (what readers know that characters don't) (`get_dramatic_irony_inventory`)
- [x] **KNOW-03**: Claude can retrieve planned and actual reveals for readers (`get_reader_reveals`)
- [x] **KNOW-04**: Claude can create or update reader information state (`upsert_reader_state`)
- [x] **KNOW-05**: Claude can log a dramatic irony entry (`log_dramatic_irony`)

### MCP — Foreshadowing & Literary Domain

- [x] **FORE-01**: Claude can retrieve foreshadowing entries with plant and payoff chapters (`get_foreshadowing`)
- [x] **FORE-02**: Claude can retrieve prophecy registry entries (`get_prophecies`)
- [x] **FORE-03**: Claude can retrieve the motif registry (`get_motifs`)
- [x] **FORE-04**: Claude can retrieve motif occurrences in chapters or scenes (`get_motif_occurrences`)
- [x] **FORE-05**: Claude can retrieve thematic mirror pairs (`get_thematic_mirrors`)
- [x] **FORE-06**: Claude can retrieve opposition pairs (`get_opposition_pairs`)
- [x] **FORE-07**: Claude can log a foreshadowing entry (`log_foreshadowing`)
- [x] **FORE-08**: Claude can log a motif occurrence (`log_motif_occurrence`)

### MCP — Names Domain

- [x] **NAME-01**: Claude can check whether a proposed name conflicts with existing names in the registry (`check_name`)
- [x] **NAME-02**: Claude can register a name in the registry with its cultural/linguistic context (`register_name`)
- [x] **NAME-03**: Claude can retrieve the full name registry (`get_name_registry`)
- [x] **NAME-04**: Claude can get name suggestions following the cultural and linguistic rules of a given faction or region (`generate_name_suggestions`)

### MCP — Voice & Style Domain

- [x] **VOIC-01**: Claude can retrieve a character's voice profile (`get_voice_profile`)
- [x] **VOIC-02**: Claude can retrieve supernatural voice guidelines for writing supernatural elements (`get_supernatural_voice_guidelines`)
- [x] **VOIC-03**: Claude can log a voice drift instance for a character (`log_voice_drift`)
- [x] **VOIC-04**: Claude can retrieve the voice drift log for a character (`get_voice_drift_log`)
- [x] **VOIC-05**: Claude can create or update a voice profile (`upsert_voice_profile`)

### MCP — Publishing Domain

- [x] **PUBL-01**: Claude can retrieve publishing assets (query letters, synopses, pitches) (`get_publishing_assets`)
- [x] **PUBL-02**: Claude can create or update a publishing asset (`upsert_publishing_asset`)
- [x] **PUBL-03**: Claude can retrieve submission tracker entries (`get_submissions`)
- [x] **PUBL-04**: Claude can log a new submission (`log_submission`)
- [x] **PUBL-05**: Claude can update a submission's status (`update_submission`)

### CLI — Database Commands

- [x] **CLDB-01**: `novel db migrate` builds a clean database from all 21 migrations in under 5 seconds
- [x] **CLDB-02**: `novel db seed [profile]` loads a named seed profile (minimal or gate-ready)
- [x] **CLDB-03**: `novel db reset` drops and rebuilds the database (migrate + optional seed)
- [x] **CLDB-04**: `novel db status` displays migration version, table count, and row counts for key tables

### CLI — Session, Gate & Query Commands

- [x] **CLSG-01**: `novel session start` displays a briefing from the last session log
- [x] **CLSG-02**: `novel session close` prompts for session summary and writes a session log
- [x] **CLSG-03**: `novel gate check` runs the full 33-item gate audit and displays a gap report
- [x] **CLSG-04**: `novel gate status` displays current gate status and blocking item count
- [x] **CLSG-05**: `novel gate certify` certifies the gate when all items pass
- [x] **CLSG-06**: `novel query pov-balance` displays POV distribution by chapter and word count
- [x] **CLSG-07**: `novel query arc-health` displays arc progression for all POV characters
- [x] **CLSG-08**: `novel query thread-gaps` displays subplots overdue for a touchpoint

### CLI — Export Commands

- [x] **CLEX-01**: `novel export chapter [n]` regenerates the markdown file for a single chapter from database records
- [x] **CLEX-02**: `novel export all` regenerates all story content markdown files from the database

### CLI — Name Commands

- [x] **CLNM-01**: `novel name check [name]` checks for conflicts in the name registry
- [x] **CLNM-02**: `novel name register [name]` registers a name with its context
- [x] **CLNM-03**: `novel name suggest [faction/region]` generates culturally consistent name suggestions

### Testing

- [x] **TEST-01**: Schema validation test compares Pydantic model fields against `PRAGMA table_info` for every domain — fails if models drift from migrations
- [x] **TEST-02**: Clean-rebuild test runs `novel db migrate` from scratch, validates all FK constraints with `PRAGMA foreign_key_check`, and confirms all seed data inserts cleanly with `PRAGMA foreign_keys=ON`
- [ ] **TEST-03**: In-memory MCP tool tests use the FastMCP in-memory client to call every tool, verifying callable interface and error contract compliance (not-found returns null, validation returns is_valid:false, gate violation returns requires_action)
- [ ] **TEST-04**: Tool selection accuracy check validates that representative natural-language queries trigger the correct tools at 80-tool scale (Claude Code Tool Search validation)

## v2 Requirements

### Performance & Optimization

- **OPTM-01**: Gate status caching — avoid re-running 33 SQL queries on every tool call
- **OPTM-02**: Dynamic toolset loading — expose domain subsets based on current task context to reduce context window impact

### Import

- **IMPT-01**: `novel import world` parses existing location/faction/culture markdown into database records
- **IMPT-02**: `novel import characters` parses existing character markdown into database records
- **IMPT-03**: `novel import chapters` parses existing chapter markdown into database records
- **IMPT-04**: `novel import all` runs all import scripts in dependency order

### CLI Polish

- **CLIP-01**: Rich colored CLI output for all commands
- **CLIP-02**: `--dry-run` flag on all destructive CLI commands

## Out of Scope

| Feature | Reason |
|---------|--------|
| Real novel manuscript content | Seed files only during development — real manuscript stays untouched |
| `novel-plugin/` (Claude Code plugin) | Separate repo; built after this engine is stable |
| Web UI or REST API layer | CLI + MCP only; single-user tool |
| SQLAlchemy or any ORM | Adds complexity without benefit for a single-file SQLite database |
| Multiple database support | SQLite only; single-file design is a constraint, not a gap |
| Standalone `fastmcp` PyPI package | SDK built-in (`mcp.server.fastmcp`) only; packages have diverged |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| SETUP-01 | Phase 1: Project Foundation & Database | Complete |
| SETUP-02 | Phase 1: Project Foundation & Database | Complete |
| SETUP-03 | Phase 1: Project Foundation & Database | Complete |
| SETUP-04 | Phase 1: Project Foundation & Database | Complete |
| CLDB-01 | Phase 1: Project Foundation & Database | Complete |
| CLDB-02 | Phase 1: Project Foundation & Database | Complete |
| CLDB-03 | Phase 1: Project Foundation & Database | Complete |
| CLDB-04 | Phase 1: Project Foundation & Database | Complete |
| SEED-01 | Phase 2: Pydantic Models & Seed Data | Complete |
| SEED-03 | Phase 2: Pydantic Models & Seed Data | Complete |
| TEST-01 | Phase 2: Pydantic Models & Seed Data | Complete |
| TEST-02 | Phase 2: Pydantic Models & Seed Data | Complete |
| ERRC-01 | Phase 3: MCP Server Core, Characters & Relationships | Complete |
| ERRC-02 | Phase 3: MCP Server Core, Characters & Relationships | Complete |
| ERRC-03 | Phase 3: MCP Server Core, Characters & Relationships | Complete |
| ERRC-04 | Phase 3: MCP Server Core, Characters & Relationships | Complete |
| CHAR-01 | Phase 3: MCP Server Core, Characters & Relationships | Complete |
| CHAR-02 | Phase 3: MCP Server Core, Characters & Relationships | Complete |
| CHAR-03 | Phase 3: MCP Server Core, Characters & Relationships | Complete |
| CHAR-04 | Phase 3: MCP Server Core, Characters & Relationships | Complete |
| CHAR-05 | Phase 3: MCP Server Core, Characters & Relationships | Complete |
| CHAR-06 | Phase 3: MCP Server Core, Characters & Relationships | Complete |
| CHAR-07 | Phase 3: MCP Server Core, Characters & Relationships | Complete |
| REL-01 | Phase 3: MCP Server Core, Characters & Relationships | Complete |
| REL-02 | Phase 3: MCP Server Core, Characters & Relationships | Complete |
| REL-03 | Phase 3: MCP Server Core, Characters & Relationships | Complete |
| REL-04 | Phase 3: MCP Server Core, Characters & Relationships | Complete |
| REL-05 | Phase 3: MCP Server Core, Characters & Relationships | Complete |
| REL-06 | Phase 3: MCP Server Core, Characters & Relationships | Complete |
| CHAP-01 | Phase 4: Chapters, Scenes & World | Complete |
| CHAP-02 | Phase 4: Chapters, Scenes & World | Complete |
| CHAP-03 | Phase 4: Chapters, Scenes & World | Complete |
| CHAP-04 | Phase 4: Chapters, Scenes & World | Complete |
| CHAP-05 | Phase 4: Chapters, Scenes & World | Complete |
| CHAP-06 | Phase 4: Chapters, Scenes & World | Complete |
| CHAP-07 | Phase 4: Chapters, Scenes & World | Complete |
| CHAP-08 | Phase 4: Chapters, Scenes & World | Complete |
| CHAP-09 | Phase 4: Chapters, Scenes & World | Complete |
| WRLD-01 | Phase 4: Chapters, Scenes & World | Complete |
| WRLD-02 | Phase 4: Chapters, Scenes & World | Complete |
| WRLD-03 | Phase 4: Chapters, Scenes & World | Complete |
| WRLD-04 | Phase 4: Chapters, Scenes & World | Complete |
| WRLD-05 | Phase 4: Chapters, Scenes & World | Complete |
| WRLD-06 | Phase 4: Chapters, Scenes & World | Complete |
| WRLD-07 | Phase 4: Chapters, Scenes & World | Complete |
| WRLD-08 | Phase 4: Chapters, Scenes & World | Complete |
| WRLD-09 | Phase 4: Chapters, Scenes & World | Complete |
| WRLD-10 | Phase 4: Chapters, Scenes & World | Complete |
| PLOT-01 | Phase 5: Plot & Arcs | Complete |
| PLOT-02 | Phase 5: Plot & Arcs | Complete |
| PLOT-03 | Phase 5: Plot & Arcs | Complete |
| PLOT-04 | Phase 5: Plot & Arcs | Complete |
| PLOT-05 | Phase 5: Plot & Arcs | Complete |
| PLOT-06 | Phase 5: Plot & Arcs | Complete |
| PLOT-07 | Phase 5: Plot & Arcs | Complete |
| PLOT-08 | Phase 5: Plot & Arcs | Complete |
| PLOT-09 | Phase 5: Plot & Arcs | Complete |
| GATE-01 | Phase 6: Gate System | Complete |
| GATE-02 | Phase 6: Gate System | Complete |
| GATE-03 | Phase 6: Gate System | Complete |
| GATE-04 | Phase 6: Gate System | Complete |
| GATE-05 | Phase 6: Gate System | Complete |
| GATE-06 | Phase 6: Gate System | Complete |
| SEED-02 | Phase 6: Gate System | Complete |
| CLSG-03 | Phase 6: Gate System | Complete |
| CLSG-04 | Phase 6: Gate System | Complete |
| CLSG-05 | Phase 6: Gate System | Complete |
| SESS-01 | Phase 7: Session & Timeline | Complete |
| SESS-02 | Phase 7: Session & Timeline | Complete |
| SESS-03 | Phase 7: Session & Timeline | Complete |
| SESS-04 | Phase 7: Session & Timeline | Complete |
| SESS-05 | Phase 7: Session & Timeline | Complete |
| SESS-06 | Phase 7: Session & Timeline | Complete |
| SESS-07 | Phase 7: Session & Timeline | Complete |
| SESS-08 | Phase 7: Session & Timeline | Complete |
| SESS-09 | Phase 7: Session & Timeline | Complete |
| SESS-10 | Phase 7: Session & Timeline | Complete |
| TIME-01 | Phase 7: Session & Timeline | Complete |
| TIME-02 | Phase 7: Session & Timeline | Complete |
| TIME-03 | Phase 7: Session & Timeline | Complete |
| TIME-04 | Phase 7: Session & Timeline | Complete |
| TIME-05 | Phase 7: Session & Timeline | Complete |
| TIME-06 | Phase 7: Session & Timeline | Complete |
| TIME-07 | Phase 7: Session & Timeline | Complete |
| TIME-08 | Phase 7: Session & Timeline | Complete |
| CANO-01 | Phase 8: Canon, Knowledge & Foreshadowing | Complete |
| CANO-02 | Phase 8: Canon, Knowledge & Foreshadowing | Complete |
| CANO-03 | Phase 8: Canon, Knowledge & Foreshadowing | Complete |
| CANO-04 | Phase 8: Canon, Knowledge & Foreshadowing | Complete |
| CANO-05 | Phase 8: Canon, Knowledge & Foreshadowing | Complete |
| CANO-06 | Phase 8: Canon, Knowledge & Foreshadowing | Complete |
| CANO-07 | Phase 8: Canon, Knowledge & Foreshadowing | Complete |
| KNOW-01 | Phase 8: Canon, Knowledge & Foreshadowing | Complete |
| KNOW-02 | Phase 8: Canon, Knowledge & Foreshadowing | Complete |
| KNOW-03 | Phase 8: Canon, Knowledge & Foreshadowing | Complete |
| KNOW-04 | Phase 8: Canon, Knowledge & Foreshadowing | Complete |
| KNOW-05 | Phase 8: Canon, Knowledge & Foreshadowing | Complete |
| FORE-01 | Phase 8: Canon, Knowledge & Foreshadowing | Complete |
| FORE-02 | Phase 8: Canon, Knowledge & Foreshadowing | Complete |
| FORE-03 | Phase 8: Canon, Knowledge & Foreshadowing | Complete |
| FORE-04 | Phase 8: Canon, Knowledge & Foreshadowing | Complete |
| FORE-05 | Phase 8: Canon, Knowledge & Foreshadowing | Complete |
| FORE-06 | Phase 8: Canon, Knowledge & Foreshadowing | Complete |
| FORE-07 | Phase 8: Canon, Knowledge & Foreshadowing | Complete |
| FORE-08 | Phase 8: Canon, Knowledge & Foreshadowing | Complete |
| NAME-01 | Phase 9: Names, Voice & Publishing | Complete |
| NAME-02 | Phase 9: Names, Voice & Publishing | Complete |
| NAME-03 | Phase 9: Names, Voice & Publishing | Complete |
| NAME-04 | Phase 9: Names, Voice & Publishing | Complete |
| VOIC-01 | Phase 9: Names, Voice & Publishing | Complete |
| VOIC-02 | Phase 9: Names, Voice & Publishing | Complete |
| VOIC-03 | Phase 9: Names, Voice & Publishing | Complete |
| VOIC-04 | Phase 9: Names, Voice & Publishing | Complete |
| VOIC-05 | Phase 9: Names, Voice & Publishing | Complete |
| PUBL-01 | Phase 9: Names, Voice & Publishing | Complete |
| PUBL-02 | Phase 9: Names, Voice & Publishing | Complete |
| PUBL-03 | Phase 9: Names, Voice & Publishing | Complete |
| PUBL-04 | Phase 9: Names, Voice & Publishing | Complete |
| PUBL-05 | Phase 9: Names, Voice & Publishing | Complete |
| CLSG-01 | Phase 10: CLI Completion & Integration Testing | Complete |
| CLSG-02 | Phase 10: CLI Completion & Integration Testing | Complete |
| CLSG-06 | Phase 10: CLI Completion & Integration Testing | Complete |
| CLSG-07 | Phase 10: CLI Completion & Integration Testing | Complete |
| CLSG-08 | Phase 10: CLI Completion & Integration Testing | Complete |
| CLEX-01 | Phase 10: CLI Completion & Integration Testing | Complete |
| CLEX-02 | Phase 10: CLI Completion & Integration Testing | Complete |
| CLNM-01 | Phase 10: CLI Completion & Integration Testing | Complete |
| CLNM-02 | Phase 10: CLI Completion & Integration Testing | Complete |
| CLNM-03 | Phase 10: CLI Completion & Integration Testing | Complete |
| TEST-03 | Phase 10: CLI Completion & Integration Testing | Pending |
| TEST-04 | Phase 10: CLI Completion & Integration Testing | Pending |

**Coverage:**
- v1 requirements: 131 total
- Mapped to phases: 131
- Unmapped: 0

---
*Requirements defined: 2026-03-07*
*Last updated: 2026-03-07 after roadmap creation*
