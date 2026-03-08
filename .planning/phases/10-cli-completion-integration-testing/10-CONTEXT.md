# Phase 10: CLI Completion & Integration Testing - Context

**Gathered:** 2026-03-08
**Status:** Ready for planning

<domain>
## Phase Boundary

Add the four remaining CLI subcommand groups (`session`, `query`, `export`, `name`) to the `novel` CLI, and complete full integration test coverage — error-contract compliance across all 80 MCP tools plus a structural tool-selection accuracy check. No new MCP tools, no schema changes, no new domains.

</domain>

<decisions>
## Implementation Decisions

### Session CLI (`novel session`)
- `novel session start` — read-only display: fetch last session log and print a formatted briefing to stdout. Output includes: session date, summary, carried-forward items, and open questions. Does not create a new session record.
- `novel session close` — interactive: use `typer.prompt("Session summary")` to collect a freeform summary from the user at the terminal. Also accept `--summary TEXT` CLI arg for scripting/piping (skips the prompt). Calls the same DB logic as `close_session` MCP tool (via sync `get_connection()`, not `mcp.db`).
- Output format: clean `typer.echo()` lines — no tables, just labeled fields. Consistent with how gate CLI displays status.

### Query CLI (`novel query`)
- `novel query pov-balance` — display POV distribution by character name with chapter count and word-count estimate. Tabular output: character | chapters | word count.
- `novel query arc-health` — display arc progression for all POV characters. Output: character | arc | last logged health | last chapter.
- `novel query thread-gaps` — display subplots overdue for a touchpoint. Output: subplot name | last touchpoint chapter | chapters overdue.
- All query commands are read-only. Exit code 0 on success even if no rows (show "No data." message). All use sync `get_connection()`.

### Export CLI (`novel export`)
- Output destination: `./chapters/` directory by default. `--output-dir PATH` option to override.
- Create output directory if it does not exist.
- `novel export chapter [n]` — write `chapter_{n:03d}.md` to the output dir. Print confirmation: `Written: ./chapters/chapter_003.md`.
- `novel export all` — iterate all chapters, write one file per chapter, print each as written.
- Markdown structure per chapter:
  ```
  # Chapter {n}: {title}

  **POV**: {pov_character_name}
  **Timeline**: Day {start_day} — Day {end_day}
  **Location**: {primary_location}

  ## {scene_title}

  {scene_summary}

  ---
  ```
- Fields sourced from `chapters` + `scenes` tables via sync query. For chapters with no scenes, write just the chapter header and a `*(No scenes recorded)*` placeholder.

### Name CLI (`novel name`)
- `novel name check [name]` — check for conflicts. Display: "No conflict." or list of conflicts with character names.
- `novel name register [name]` — register with prompted context. Prompt for: character role (optional), faction (optional), notes (optional). Accept all as `--role`, `--faction`, `--notes` args to skip prompts.
- `novel name suggest [faction-or-region]` — display a list of suggested names. Plain list output, one per line.
- All three delegate to the same SQL logic as names MCP tools — no re-implementation, just CLI wrappers.

### TEST-03: Error contract completeness
- All 14 per-domain test files already exist. TEST-03 means: audit each for the three error contract cases and add tests where missing:
  1. **Not-found** — tool called with unknown ID returns `null` with `not_found_message`
  2. **Validation failure** — tool called with invalid data returns response with `is_valid: false` and `errors` list
  3. **Gate violation** — gated tool called without certification returns response with `requires_action: true`
- Priority targets: canon, knowledge, foreshadowing, voice, publishing (built last, likely thinnest error coverage).
- Not a new consolidated test file — add missing cases to each existing `test_*.py` file. Keep one test file per domain.

### TEST-04: Tool selection accuracy
- Pytest file `tests/test_tool_selection.py` — two test suites:
  1. **Structural checks** (automated): verify ~80 tools registered in the MCP server, no duplicate tool names, all have descriptions ≥ 50 characters. Fails if tool count drops below 75 or above 90 (catches accidental omissions/duplications).
  2. **Disambiguation fixture** (semi-automated): parametrized test with 20–30 `(query_phrase, expected_tool_name)` pairs. For each pair, check that `expected_tool_name` is a registered tool and its description contains at least one keyword from the query phrase. This is a structural check — not calling Claude — but it documents intended query→tool routing so regressions are visible.
- No Claude API calls in tests. Tool selection accuracy at actual Claude Code runtime is a manual verification step, not automated.

### Claude's Discretion
- Exact column widths and padding for tabular query output
- Whether `novel query` commands display a header row (e.g., "POV Balance:") or go straight to data
- Exact wording of empty state messages
- How to handle DB connection errors in the new CLI commands (follow the gate CLI pattern: print error to stderr, exit code 1)
- Implementation order of plans within the phase

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `novel.db.connection.get_connection()` — sync context manager, all new CLI commands use this (never `novel.mcp.db`)
- `novel.gate.cli` — existing pattern for a Typer subcommand group with try/except → `typer.Exit(code=1)` error handling
- `novel.db.cli` — existing pattern for db commands, including `novel db seed` with `typer.prompt()` usage
- `novel.tools.session` — contains `start_session`, `close_session`, `get_last_session`, `get_pov_balance` — SQL logic can be extracted or mirrored for CLI
- `novel.tools.arcs` — contains `get_arc_health` logic, usable for `novel query arc-health`
- `novel.tools.arcs.get_subplot_touchpoint_gaps` — usable for `novel query thread-gaps`
- `novel.tools.names` — 4 tools: check_name, register_name, get_name_registry, generate_name_suggestions — CLI wrappers around same SQL
- `tests/conftest.py` — session-scoped `test_db_path` fixture + `mcp_session` async fixture, reusable for TEST-03 additions
- `tests/test_names.py` — canonical test pattern for the in-memory MCP client approach

### Established Patterns
- CLI subcommand groups: `typer.Typer()` app registered on root `app` via `app.add_typer(..., name="...")`
- CLI error handling: `try/except Exception as e: typer.echo(f"Error: {e}", err=True); raise typer.Exit(code=1)`
- MCP test pattern: `create_connected_server_and_client_session(mcp)` per test (not fixture-scoped due to anyio cancel scope)
- FastMCP serialization: single object = `json.loads(result.content[0].text)`, list = `[json.loads(c.text) for c in result.content]`, empty list = empty content

### Integration Points
- `src/novel/cli.py` — add `app.add_typer(session_cli.app, name="session")` etc. for all 4 new groups
- New CLI modules go in `src/novel/session/cli.py`, `src/novel/query/cli.py`, `src/novel/export/cli.py`, `src/novel/name/cli.py` — following the `novel/gate/cli.py` pattern

</code_context>

<specifics>
## Specific Ideas

- No specific user requirements — all decisions are Claude's discretion. Follow existing patterns (gate CLI, db CLI) for consistency.
- TEST-04 disambiguation fixture should cover at least one query per domain (14 domains × 1–2 queries = ~25 pairs minimum).

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 10-cli-completion-integration-testing*
*Context gathered: 2026-03-08*
