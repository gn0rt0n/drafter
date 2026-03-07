# Pitfalls Research

**Domain:** Python MCP Server + SQLite tooling for large-scale novel management
**Researched:** 2026-03-07
**Confidence:** HIGH (verified across MCP SDK docs, SQLite official docs, community reports, and production MCP server patterns)

## Critical Pitfalls

### Pitfall 1: 80 Tools Flooding Claude's Context Window

**What goes wrong:**
With ~80 MCP tools registered on a single server, every tool definition (name, description, parameter schema) is injected into the LLM's context window on every request. At ~600-800 tokens per tool, that is 48,000-64,000 tokens consumed before the conversation even starts. This crowds out actual project context (file contents, conversation history), degrades tool selection accuracy, and increases latency. Empirically, Opus 4 tool selection accuracy drops from 74% to 49% as tool count grows without mitigation.

**Why it happens:**
The PRD defines 14 domains with ~80 tools as a flat namespace on a single MCP server. Developers build all tools into one `server.py` registration block, treating MCP like a REST API where more endpoints are always fine. But MCP tools are not endpoints -- they are injected into the prompt, meaning each one has a marginal cost to every interaction.

**How to avoid:**
1. Write keyword-rich, specific tool descriptions so Claude Code's Tool Search (auto-enabled when tools exceed 10% of context) can match accurately. Tool Search reduced context bloat by 46.9% (51K to 8.5K tokens) in production measurements.
2. Use clear, non-overlapping tool names. Avoid near-synonyms like `get_character` and `list_characters` having ambiguous descriptions. The name itself is a search signal.
3. Group tools into well-named domains in the server instruction field. Server instructions help Claude decide *when* to search for tools from your server.
4. Test tool selection accuracy with representative queries during Phase B. If Claude consistently picks the wrong tool among similar options (e.g., `get_arc` vs `get_arc_health` vs `log_arc_health`), tighten names and descriptions.
5. Do NOT split into multiple MCP servers unless Tool Search proves insufficient. Multiple servers multiply startup overhead and connection management complexity. One server with good descriptions is better than three servers with vague ones.

**Warning signs:**
- Claude picks a wrong but similarly-named tool (e.g., calls `get_character` when it should call `get_character_state`)
- Claude apologizes for "not having access" to a tool that is registered
- Response latency noticeably increases as tools are added
- Tool descriptions are generic ("Get character data") rather than specific ("Retrieve the full character sheet including voice profile, physical description, and arc summary for a single character by ID or name")

**Phase to address:**
Phase B (MCP Server). Tool descriptions must be written with search-matching in mind from the start, not retrofitted. Validate tool selection accuracy before moving to Phase C.

---

### Pitfall 2: SQLite "Database is Locked" Under MCP Async Concurrency

**What goes wrong:**
The MCP server runs async (via FastMCP/asyncio). If the database connection strategy is wrong -- sharing a single `sqlite3` connection across coroutines, opening connections without WAL mode, or holding transactions open too long -- concurrent tool calls will hit `sqlite3.OperationalError: database is locked`. This is especially likely when Claude calls multiple tools in parallel (which it does regularly for independent queries).

**Why it happens:**
SQLite uses file-level locking, not row-level. Python's `sqlite3` module connections are not thread-safe by default. Developers either: (a) create one connection at server startup and share it (locks on any concurrent write), (b) forget to enable WAL mode (which allows concurrent reads during writes), or (c) use `sqlite3` directly in async code, blocking the event loop while waiting for locks.

**How to avoid:**
1. Use `aiosqlite` for all database access in the MCP server. It runs SQLite operations in a dedicated thread, preventing event loop blocking.
2. Enable WAL mode on database creation: `PRAGMA journal_mode=WAL`. WAL is a property of the database file itself, not per-connection -- set it once during migration and it persists.
3. Use a connection-per-request pattern with context managers: open connection, execute, close. Do not hold connections open across tool calls.
4. Keep transactions as short as possible. Perform validation and data preparation before entering the transaction, then execute the minimal SQL within it.
5. Set a reasonable timeout (10-30 seconds) on connections as a safety net: `aiosqlite.connect(db_path, timeout=30)`.
6. For the CLI (`novel` command), use standard synchronous `sqlite3` -- `aiosqlite` is only needed in the async MCP server context.

**Warning signs:**
- Intermittent `OperationalError: database is locked` errors, especially when Claude calls 2-3 tools at once
- Tool calls that succeed individually but fail when batched
- Writes succeeding only when no reads are in flight

**Phase to address:**
Phase A (Python Foundation) for WAL mode enablement. Phase B (MCP Server) for `aiosqlite` connection management. The `db.py` module in `mcp/novel_server/` must enforce these patterns from the first tool implementation.

---

### Pitfall 3: Pydantic Models Drifting from SQLite Schema

**What goes wrong:**
The system has three sources of truth for data shape: (1) the 21 SQL migration files defining the SQLite schema, (2) the Pydantic models in `models.py` defining MCP tool input/output types, and (3) the actual tool implementation SQL queries. When a migration adds a column, renames a field, or changes a type, the Pydantic models and queries silently fall out of sync. Tools then return incomplete data (missing new columns), crash on renamed columns, or accept parameters that don't match the actual schema.

**Why it happens:**
There is no automated check binding Pydantic models to the SQL schema. A developer updates migration 002 to add `emotional_state` to the characters table, writes the SQL query in the tool to SELECT it, but forgets to add it to the `CharacterResponse` Pydantic model. Or vice versa: the Pydantic model is updated but the query still uses `SELECT *` from a cached mental model of the table. With 21 migration files and ~80 tools, the surface area for drift is enormous.

**How to avoid:**
1. Establish a strict convention: every schema change requires a checklist of (a) migration SQL, (b) Pydantic model update, (c) tool query update, (d) seed data update.
2. Never use `SELECT *` in tool queries. Explicitly name every column. This way, new columns don't silently appear in results and missing columns cause immediate SQL errors rather than silent omissions.
3. Write a schema validation test that compares Pydantic model fields against the actual SQLite table columns (via `PRAGMA table_info(table_name)`). Run this test after every migration. This is cheap to build and catches 90% of drift.
4. Group the Pydantic models by domain matching the tool files: `models/characters.py`, `models/chapters.py`, etc. This makes it harder to forget which model corresponds to which table.
5. Consider a code generation step that produces Pydantic model stubs from the SQLite schema. Even a partial automation reduces manual synchronization burden.

**Warning signs:**
- MCP tools return `null` for fields that the database definitely has values for
- Pydantic validation errors on tool output (field missing or wrong type)
- Newly added columns never appearing in MCP tool responses despite being populated in the database
- `SELECT *` appearing anywhere in tool implementation code

**Phase to address:**
Phase A (Python Foundation) for establishing conventions and building the schema validation test. Phase B (MCP Server) for enforcing explicit column naming in every query. This pitfall compounds over time -- catching it early is orders of magnitude cheaper than catching it after 80 tools are built.

---

### Pitfall 4: PRAGMA foreign_keys Not Enabled -- Silent Data Corruption

**What goes wrong:**
SQLite disables foreign key enforcement by default. Unless every connection explicitly runs `PRAGMA foreign_keys = ON`, INSERT and UPDATE operations can create orphaned records -- characters referencing nonexistent books, scenes referencing nonexistent chapters, relationships referencing deleted characters. The 21-migration schema defines extensive foreign key relationships, but they are entirely decorative without this PRAGMA. The database silently accepts invalid data.

**Why it happens:**
This is a well-documented SQLite gotcha: foreign key constraints exist in the schema DDL for documentation purposes but are not enforced unless explicitly enabled per-connection. Python's `sqlite3.connect()` does not enable them by default. Developers coming from PostgreSQL or MySQL assume FK constraints are always active.

**How to avoid:**
1. Create a single connection factory function used by both the MCP server and the CLI. This function must always execute `PRAGMA foreign_keys = ON` immediately after opening the connection, before any other operation.
2. In the migration runner, enable foreign keys and run `PRAGMA foreign_key_check` after all migrations complete. This validates existing data against FK constraints.
3. Add a startup assertion in the MCP server that verifies `PRAGMA foreign_keys` returns `1` before accepting any tool calls.
4. During migrations that alter tables, be aware that `PRAGMA foreign_keys = ON/OFF` has no effect inside a transaction. Run PRAGMA settings outside transaction blocks.

**Warning signs:**
- Seed data imports succeed even with deliberately invalid foreign key references (test this!)
- `PRAGMA foreign_keys` returns `0` when queried on an active connection
- Orphaned records appearing in query results (characters without books, scenes without chapters)

**Phase to address:**
Phase A (Python Foundation). The connection factory function in `novel/db/` must enforce this from day one. The migration runner must validate FK integrity after applying migrations.

---

### Pitfall 5: Migration Ordering and Foreign Key Dependency Chains

**What goes wrong:**
The 21 migration files have implicit dependencies through foreign keys (e.g., `002_characters.sql` references `books` from `001_core_entities.sql`; `009_timeline.sql` references both characters and chapters). If migrations are executed out of order, or if a migration's DDL references a table from a higher-numbered migration, the build fails. More subtly, if migration files are later edited to add cross-references to tables defined in earlier migrations, those references work -- but adding references to later-defined tables silently breaks on a clean rebuild even though they work in development (where the table already exists from a previous run).

**Why it happens:**
The migration runner executes files in numeric order, which works on initial build. But during development, developers run individual migrations against an existing database (where all tables already exist). A migration that works against a populated database may fail against an empty database because it references a table that has not been created yet.

**How to avoid:**
1. The migration runner must always test against a clean, empty database. Add a CI/test step that drops and rebuilds from scratch to verify ordering.
2. Document the dependency graph: which migration files reference which other migration's tables. Include this as a comment header in each migration file.
3. When adding new foreign key constraints in later migrations, reference only tables from earlier-numbered migrations. If a constraint requires a table from a later migration, restructure the migration numbering.
4. The rebuild-from-scratch test must be part of Phase A acceptance criteria, not deferred. Running `novel db migrate` on a fresh database is the gold standard for migration correctness.

**Warning signs:**
- `novel db migrate` succeeds on development database but fails on a fresh file
- Error messages about "no such table" during migration
- Developers manually running individual migration files instead of the full sequence

**Phase to address:**
Phase A (Python Foundation). The migration runner must include a clean-rebuild test from the start. Every Phase A milestone should include a fresh rebuild verification.

---

### Pitfall 6: Gate System Bypassable Through Direct Tool Calls

**What goes wrong:**
The architecture gate (33-item checklist) is supposed to block prose-phase operations until certification. But the gate enforcement is specified only in agent/skill markdown files ("check gate status before operating"). If a user calls `upsert_chapter` with prose content directly through the MCP tool -- bypassing the prose-writer skill -- the gate check never fires. The gate becomes advisory rather than enforced. Similarly, if gate checking is implemented in the MCP tool layer but a single tool lacks the check, that tool becomes a backdoor.

**Why it happens:**
The PRD specifies gate enforcement at the skill/agent layer (markdown instructions telling Claude to check the gate). But MCP tools are callable directly by any Claude Code session regardless of which skill is active. If enforcement lives only in prompt instructions, it is suggestions rather than constraints. Additionally, with ~80 tools, it is easy to miss adding gate checks to all prose-relevant tools.

**How to avoid:**
1. Implement gate enforcement at the MCP tool level, not just the skill/agent level. Prose-modifying tools (`upsert_chapter` with prose content, scene writing tools) should check gate status in their Python implementation and return `{"requires_action": "Gate certification required. Run gate audit first."}` when the gate is not passed.
2. Define a clear list of which tools are "gate-gated." Not all tools need gate checks -- `upsert_character` during architecture phase should work fine. Only tools that write prose content need enforcement.
3. Create a `@requires_gate` decorator that wraps the gate check logic. Apply it to all prose-phase tools. This is more reliable than remembering to add the check to each tool individually.
4. Test the gate enforcement by attempting to call prose tools without gate certification and verifying the `requires_action` response.

**Warning signs:**
- Prose content appearing in the database before gate certification
- Gate status queries showing "not passed" while chapters already contain prose
- No `requires_action` responses appearing in tool call logs during development

**Phase to address:**
Phase B (MCP Server) for tool-level enforcement. Phase H (Architecture Gate) for integration testing. The `@requires_gate` decorator should be built alongside the gate tools in Phase B, even if the actual gate checklist items are not populated until Phase H.

---

### Pitfall 7: stdout Corruption of MCP Protocol Messages

**What goes wrong:**
MCP stdio transport uses stdout exclusively for protocol messages (JSON-RPC). Any stray `print()` statement, logging misconfiguration, or library that writes to stdout corrupts the protocol stream. The MCP client receives malformed JSON, and tools silently fail or return garbage. This is especially insidious because it works fine during development (where you might test via HTTP transport or direct function calls) and only breaks in production (stdio transport via `uv run`).

**Why it happens:**
Python's default logging handler writes to stderr (correct), but developers add `print()` for debugging and forget to remove them. Third-party libraries may also write to stdout. The `sqlite3` module's verbose error messages go to stderr (safe), but if you use `traceback.print_exc()` without specifying the file parameter, it defaults to stderr (safe) -- but `print()` defaults to stdout (dangerous).

**How to avoid:**
1. Configure logging to stderr explicitly in the MCP server entry point. Never rely on defaults.
2. Ban `print()` from all MCP server code. Use a linter rule or pre-commit hook to flag `print(` in `mcp/` directory files.
3. Test the MCP server in stdio mode early -- do not rely solely on development testing with direct function calls or HTTP transport.
4. Redirect stdout to stderr as a safety net at server startup: `sys.stdout = sys.stderr` after the MCP framework has set up its protocol handler (though this is a last resort -- better to not write to stdout at all).

**Warning signs:**
- MCP tools work when called directly but fail when invoked through Claude Code
- JSON parsing errors in the MCP client logs
- Tools returning empty or garbled responses intermittently
- Debug output appearing in Claude Code's tool response display

**Phase to address:**
Phase B (MCP Server). Establish the logging configuration and `print()` ban from the first tool implementation. Add stdio-mode integration testing to Phase B acceptance criteria.

---

### Pitfall 8: UV Package Configuration Missing Build System

**What goes wrong:**
The plugin's `.mcp.json` invokes the server via `uv run --project /path/to/novel-tools novel-mcp`. This requires: (a) `novel-mcp` defined as a `[project.scripts]` entry point in `pyproject.toml`, and (b) `[build-system]` defined so UV treats the project as an installable package. If either is missing, `uv run novel-mcp` fails with a confusing error about the command not being found. The `novel` CLI has the same requirement for its entry point.

**Why it happens:**
UV projects initialized with `uv init` may not include `[build-system]` by default, and without it, UV does not install the project itself into the virtual environment -- meaning entry points defined in `[project.scripts]` are never created. Developers who test with `uv run python -m novel_server.server` during development bypass entry point resolution entirely, so they never discover the misconfiguration until deployment.

**How to avoid:**
1. Include `[build-system]` in `pyproject.toml` from day one:
   ```toml
   [build-system]
   requires = ["hatchling"]
   build-backend = "hatchling.build"
   ```
2. Define both entry points early:
   ```toml
   [project.scripts]
   novel = "novel.cli:main"
   novel-mcp = "mcp.novel_server.server:main"
   ```
3. Test entry point invocation (`uv run novel-mcp`, `uv run novel`) immediately after setting up `pyproject.toml`, not after building the full server.
4. Match the `.mcp.json` invocation exactly to the entry point name. If `.mcp.json` says `novel-mcp`, the `[project.scripts]` key must be `novel-mcp`, not `novel_mcp` or `mcp-server`.

**Warning signs:**
- `uv run novel-mcp` returns "command not found" or "No module named..."
- Server works when run directly (`python -m mcp.novel_server.server`) but not through UV entry point
- `uv sync` does not list the project itself in installed packages

**Phase to address:**
Phase A (Python Foundation). The `pyproject.toml` with build system, entry points, and dependencies should be the first thing validated -- before writing any migration SQL.

---

## Technical Debt Patterns

Shortcuts that seem reasonable but create long-term problems.

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| `SELECT *` in tool queries | Faster to write, automatically includes new columns | Schema drift invisible; Pydantic models get extra unvalidated fields; column ordering assumptions break | Never -- always name columns explicitly |
| Single connection shared across all tool calls | Simpler connection management code | "Database is locked" under concurrency; blocks event loop | Never for async MCP server; acceptable for synchronous CLI |
| Gate enforcement only in skill markdown files | Faster to implement; no Python code needed for gate | Gate is advisory, not enforced; bypassed by direct tool calls | Only acceptable as initial stub in Phase B, must be replaced with tool-level enforcement before Phase H |
| Hardcoded `NOVEL_DB_PATH` during development | Skip environment variable plumbing | Breaks on any machine besides the developer's; fails in CI | Only in earliest Phase A prototyping, must use env var within the first week |
| Skipping the clean-rebuild migration test | Saves time during rapid schema iteration | Migrations that work on dirty DB but fail on clean rebuild; discovered only when someone else tries to set up | Never -- always rebuild from scratch as a test after any migration change |
| Flat Pydantic model file (`models.py`) for all 80 tools | One file to find everything | 3000+ line file; merge conflicts; hard to find related models | Only in earliest prototyping; split into per-domain model files by end of Phase B |

## Integration Gotchas

Common mistakes when connecting components of this system.

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| `.mcp.json` -> UV entry point | Using `--directory` flag (deprecated in some UV versions) instead of `--project` | Use `uv run --project /path/to/novel-tools novel-mcp` as shown in the PRD |
| MCP server -> SQLite | Opening connections at import time or module scope | Open connections inside each tool function using an async context manager |
| CLI -> MCP server | Sharing database module code but using async in CLI | CLI uses synchronous `sqlite3`; MCP server uses `aiosqlite`. Share SQL query strings, not connection code |
| Pydantic -> MCP tool schema | Assuming Optional fields will show as optional in tool schema | Explicitly set `Field(default=None)` and test that the generated schema matches expectations |
| Seed data -> Migration schema | Seed SQL written against an older schema version | Seed data script must run migrations first, then insert seed data. Never hardcode column lists in seed inserts -- validate against current schema |
| Plugin `.mcp.json` -> `NOVEL_DB_PATH` | Committing machine-specific paths to the plugin repo | Use placeholder values in the repo; document that actual paths are set per-machine in the novel project's `.claude/settings.json` |

## Performance Traps

Patterns that work at small scale but fail as the database grows.

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Unindexed foreign key columns | Queries joining characters to chapters slow down | Add indexes on all FK columns in migration files; SQLite does not auto-index FKs | 500+ chapters/scenes (likely with 55 chapters x 5+ scenes each) |
| Full-table scans in validation queries | `run_gate_audit` takes 10+ seconds | The 33 gate queries must use indexed columns; add `EXPLAIN QUERY PLAN` checks | When all 33 queries run sequentially against populated tables |
| Loading all records in list tools | `list_characters` returns every character with every field | Add pagination parameters (`limit`, `offset`) to all list tools; return summary fields by default, full records only in `get_` tools | 100+ characters (likely in a 250K-word fantasy novel) |
| N+1 queries in composite tools | `get_chapter_plan` calls `get_scene` for each scene individually | Use JOINs for tools that return nested data; single query for chapter + scenes + obligations | 55 chapters x 5+ scenes = 275+ individual queries |
| Not using WAL mode | Concurrent reads block behind writes | Enable WAL at database creation time | Any time Claude calls 2+ tools simultaneously |

## UX Pitfalls

Common user experience mistakes in MCP tool design for Claude Code.

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Tool returns raw SQL error messages | User sees `sqlite3.IntegrityError: UNIQUE constraint failed: characters.name` with no context | Catch SQL errors; return structured error with `is_valid: false` and human-readable `errors: ["A character named 'Kael' already exists (id: 42). Use upsert_character with the existing ID to update."]` |
| Not-found returns empty object `{}` | User cannot distinguish "no data" from "data with all null fields" | Return `null` with `not_found_message: "No character found with name 'Kael'. Did you mean 'Kaelan'?"` per the error contract |
| Tool names ambiguous to Claude | Claude calls `get_arc` when user asked about arc health | Use specific names: `get_arc_definition` vs `get_arc_health_log`. Include "when to use" in descriptions |
| Validation errors lack specificity | User told "invalid data" without knowing which field | Return per-field errors: `errors: [{"field": "pov_character_id", "error": "Character ID 99 does not exist"}]` |
| Gate rejection with no guidance | User told "gate not passed" with no path forward | Return `requires_action: "Architecture gate not certified. 7 of 33 checklist items failing. Run get_gate_checklist to see specific gaps."` with the failing count and next step |

## "Looks Done But Isn't" Checklist

Things that appear complete but are missing critical pieces.

- [ ] **Migration runner:** Often missing clean-rebuild test -- verify `novel db migrate` works on a brand new empty `.sqlite` file
- [ ] **Foreign keys:** Often missing `PRAGMA foreign_keys = ON` -- verify by inserting a record with an invalid FK reference and confirming it is rejected
- [ ] **WAL mode:** Often missing from database initialization -- verify with `PRAGMA journal_mode` returning `wal`
- [ ] **Tool error contract:** Often missing structured errors -- verify each tool returns `null` (not-found), `is_valid: false` (validation), and `requires_action` (gate) per the PRD contract instead of raising exceptions
- [ ] **Entry points:** Often missing `[build-system]` in `pyproject.toml` -- verify `uv run novel-mcp` works, not just `python -m mcp.novel_server.server`
- [ ] **Gate enforcement in tools:** Often only in agent markdown, not tool code -- verify by calling a prose tool directly via MCP without gate certification and confirming `requires_action` response
- [ ] **Seed data coverage:** Often covers happy path only -- verify seed data includes: orphaned records (for FK testing), edge cases (empty names, very long text), and sufficient volume to test pagination
- [ ] **Logging configuration:** Often uses `print()` or default logging -- verify no output appears on stdout when running in stdio mode
- [ ] **Tool descriptions:** Often generic -- verify each description is specific enough for Claude to distinguish it from similar tools without reading parameters

## Recovery Strategies

When pitfalls occur despite prevention, how to recover.

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Schema/Pydantic drift | MEDIUM | Run `PRAGMA table_info` for all tables, diff against Pydantic models, update models, re-test affected tools. Cost scales with number of drifted models. |
| Database locked errors | LOW | Enable WAL mode (one-time PRAGMA), switch to aiosqlite, use connection-per-request pattern. No data loss involved. |
| Missing FK enforcement | HIGH | Enable PRAGMA, run `PRAGMA foreign_key_check` to find violations, write data cleanup migration to fix orphaned records. If orphaned records are extensive, may require manual review of which records to keep/delete/re-link. |
| Gate bypass in production | MEDIUM | Add `@requires_gate` decorator to prose tools, audit existing prose content in DB for records created before gate certification, flag for review. |
| Migration ordering failure | MEDIUM | Renumber migration files to fix dependency order, re-test clean rebuild. If data exists, export and re-import after fixing migration order. |
| stdout protocol corruption | LOW | Remove print statements, configure logging to stderr, add lint rule. No data loss; only affects MCP communication. |
| UV entry point misconfiguration | LOW | Add `[build-system]` and `[project.scripts]` to `pyproject.toml`, run `uv sync`. Fix in minutes once diagnosed. |
| Tool selection confusion (too many similar tools) | MEDIUM | Rewrite tool names and descriptions for clarity, potentially merge tools with overlapping functionality, re-test tool selection accuracy. May require updating agent/skill markdown that references old tool names. |

## Pitfall-to-Phase Mapping

How roadmap phases should address these pitfalls.

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| 80 tools flooding context | Phase B (MCP Server) | Measure tool description token count; test tool selection accuracy on 10 representative queries |
| SQLite database locked | Phase A (Foundation) + Phase B (Server) | Run 5 concurrent tool calls against the same database; zero lock errors |
| Pydantic model drift | Phase A (Foundation) + Phase B (Server) | Schema validation test passes after every migration change |
| PRAGMA foreign_keys not enabled | Phase A (Foundation) | Insert record with invalid FK reference; confirm rejection |
| Migration ordering failure | Phase A (Foundation) | `novel db migrate` succeeds on empty database; clean-rebuild test in CI |
| Gate system bypassable | Phase B (Server) + Phase H (Gate) | Call prose tool directly without certification; confirm `requires_action` |
| stdout protocol corruption | Phase B (Server) | MCP server produces zero stdout output when run in stdio mode (except protocol messages) |
| UV package misconfiguration | Phase A (Foundation) | `uv run novel-mcp` and `uv run novel` both resolve to correct entry points |
| Seed data insufficient coverage | Phase A (Foundation) | Seed data includes FK violation test cases, empty strings, pagination-requiring volume |
| N+1 queries in composite tools | Phase B (Server) | `EXPLAIN QUERY PLAN` shows JOINs not nested selects for composite tools |
| Ambiguous tool descriptions | Phase B (Server) | Claude selects correct tool for 10 representative natural-language queries |

## Sources

- [Implementing MCP: Tips, Tricks and Pitfalls (NearForm)](https://nearform.com/digital-community/implementing-model-context-protocol-mcp-tips-tricks-and-pitfalls/)
- [MCP Python SDK (GitHub)](https://github.com/modelcontextprotocol/python-sdk)
- [Claude Code MCP Tool Search: Save 95% Context](https://claudefa.st/blog/tools/mcp-extensions/mcp-tool-search)
- [Model Context Protocol and the "too many tools" problem](https://demiliani.com/2025/09/04/model-context-protocol-and-the-too-many-tools-problem/)
- [Claude Code Just Cut MCP Context Bloat by 46.9%](https://medium.com/@joe.njenga/claude-code-just-cut-mcp-context-bloat-by-46-9-51k-tokens-down-to-8-5k-with-new-tool-search-ddf9e905f734)
- [SQLite Foreign Key Support (Official)](https://sqlite.org/foreignkeys.html)
- [Multi-threaded SQLite without OperationalErrors (Charles Leifer)](https://charlesleifer.com/blog/multi-threaded-sqlite-without-the-operationalerrors/)
- [How to prevent the "SQLite database is locked" error (Abilian)](https://lab.abilian.com/Tech/Databases%20&%20Persistence/sqlite/How%20to%20prevent%20the%20%22SQLite%20database%20is%20locked%22%20error/)
- [SQLite Write-Ahead Logging (Official)](https://sqlite.org/wal.html)
- [aiosqlite (PyPI)](https://pypi.org/project/aiosqlite/)
- [UV Build Failures Documentation](https://docs.astral.sh/uv/reference/troubleshooting/build-failures/)
- [UV Project Configuration](https://docs.astral.sh/uv/concepts/projects/config/)
- [Optimising MCP Server Context Usage in Claude Code (Scott Spence)](https://scottspence.com/posts/optimising-mcp-server-context-usage-in-claude-code)
- [Python sqlite3 PRAGMA foreign_keys Issue (CPython tracker)](https://github.com/python/cpython/issues/57206)
- [Connect Claude Code to tools via MCP (Official Docs)](https://code.claude.com/docs/en/mcp)

---
*Pitfalls research for: Python MCP Server + SQLite novel management tooling*
*Researched: 2026-03-07*
