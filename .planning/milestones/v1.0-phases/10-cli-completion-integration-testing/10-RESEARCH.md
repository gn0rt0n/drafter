# Phase 10: CLI Completion & Integration Testing - Research

**Researched:** 2026-03-08
**Domain:** Typer CLI subcommands, MCP tool testing, SQLite sync queries, pytest parametrize
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Session CLI (`novel session`)**
- `novel session start` — read-only display: fetch last session log and print a formatted briefing to stdout. Output includes: session date, summary, carried-forward items, and open questions. Does not create a new session record.
- `novel session close` — interactive: use `typer.prompt("Session summary")` to collect a freeform summary from the user at the terminal. Also accept `--summary TEXT` CLI arg for scripting/piping (skips the prompt). Calls the same DB logic as `close_session` MCP tool (via sync `get_connection()`, not `mcp.db`).
- Output format: clean `typer.echo()` lines — no tables, just labeled fields. Consistent with how gate CLI displays status.

**Query CLI (`novel query`)**
- `novel query pov-balance` — display POV distribution by character name with chapter count and word-count estimate. Tabular output: character | chapters | word count.
- `novel query arc-health` — display arc progression for all POV characters. Output: character | arc | last logged health | last chapter.
- `novel query thread-gaps` — display subplots overdue for a touchpoint. Output: subplot name | last touchpoint chapter | chapters overdue.
- All query commands are read-only. Exit code 0 on success even if no rows (show "No data." message). All use sync `get_connection()`.

**Export CLI (`novel export`)**
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

**Name CLI (`novel name`)**
- `novel name check [name]` — check for conflicts. Display: "No conflict." or list of conflicts with character names.
- `novel name register [name]` — register with prompted context. Prompt for: character role (optional), faction (optional), notes (optional). Accept all as `--role`, `--faction`, `--notes` args to skip prompts.
- `novel name suggest [faction-or-region]` — display a list of suggested names. Plain list output, one per line.
- All three delegate to the same SQL logic as names MCP tools — no re-implementation, just CLI wrappers.

**TEST-03: Error contract completeness**
- All 14 per-domain test files already exist. TEST-03 means: audit each for the three error contract cases and add tests where missing:
  1. **Not-found** — tool called with unknown ID returns `null` with `not_found_message`
  2. **Validation failure** — tool called with invalid data returns response with `is_valid: false` and `errors` list
  3. **Gate violation** — gated tool called without certification returns response with `requires_action: true`
- Priority targets: canon, knowledge, foreshadowing, voice, publishing (built last, likely thinnest error coverage).
- Not a new consolidated test file — add missing cases to each existing `test_*.py` file. Keep one test file per domain.

**TEST-04: Tool selection accuracy**
- Pytest file `tests/test_tool_selection.py` — two test suites:
  1. **Structural checks** (automated): verify ~80 tools registered in the MCP server, no duplicate tool names, all have descriptions ≥ 50 characters. Fails if tool count drops below 75 or above 90.
  2. **Disambiguation fixture** (semi-automated): parametrized test with 20–30 `(query_phrase, expected_tool_name)` pairs. For each pair, check that `expected_tool_name` is a registered tool and its description contains at least one keyword from the query phrase. This is a structural check — not calling Claude — but it documents intended query→tool routing so regressions are visible.
- No Claude API calls in tests.

### Claude's Discretion
- Exact column widths and padding for tabular query output
- Whether `novel query` commands display a header row (e.g., "POV Balance:") or go straight to data
- Exact wording of empty state messages
- How to handle DB connection errors in the new CLI commands (follow the gate CLI pattern: print error to stderr, exit code 1)
- Implementation order of plans within the phase

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| CLSG-01 | `novel session start` displays a briefing from the last session log | Session briefing SQL is in `tools/session.py:get_last_session`; sync rewrite uses `get_connection()` pattern from gate CLI |
| CLSG-02 | `novel session close` prompts for summary and writes session log | `tools/session.py:close_session` SQL logic to mirror; `typer.prompt()` pattern in `db/cli.py:seed` |
| CLSG-06 | `novel query pov-balance` displays POV distribution by chapter and word count | SQL in `tools/session.py:get_pov_balance`; JOIN with characters for name lookup |
| CLSG-07 | `novel query arc-health` displays arc progression for all POV characters | SQL in `tools/arcs.py:get_arc_health` with JOIN to `character_arcs` and `characters` |
| CLSG-08 | `novel query thread-gaps` displays subplots overdue for a touchpoint | SQL in `tools/arcs.py:get_subplot_touchpoint_gaps`; complex HAVING clause already proven |
| CLEX-01 | `novel export chapter [n]` regenerates markdown for a single chapter | JOIN chapters+scenes; `pathlib.Path.mkdir(exist_ok=True)`; formatted f-string template |
| CLEX-02 | `novel export all` regenerates all chapter files | Iterate `SELECT * FROM chapters ORDER BY chapter_number` then write each |
| CLNM-01 | `novel name check [name]` checks for conflicts | Sync mirror of `tools/names.py:check_name` SQL |
| CLNM-02 | `novel name register [name]` registers a name with context | Sync mirror of `tools/names.py:register_name`; `typer.prompt()` for optional fields |
| CLNM-03 | `novel name suggest [faction/region]` generates name suggestions | Sync mirror of `tools/names.py:generate_name_suggestions` |
| TEST-03 | Error contract completeness across all 99 MCP tools | Gap analysis complete — canon/knowledge/foreshadowing/session have no not-found or gate-violation tests; no domain has is_valid:false tests except arcs, gate, names |
| TEST-04 | Tool selection accuracy check at 99-tool scale | FastMCP exposes `mcp._tool_manager.tools` dict; structural checks + parametrized disambiguation |
</phase_requirements>

## Summary

Phase 10 is the final delivery phase. All MCP tools are already built (Phases 3–9). This phase adds four CLI subcommand groups (`session`, `query`, `export`, `name`) and completes integration test coverage (error contract audit + tool selection structural check). No new MCP tools, no schema changes.

The work divides cleanly into two streams: CLI implementation (4 new subcommand modules following the gate CLI pattern) and test completion (error contract gap filling + `tests/test_tool_selection.py`). Both streams can be parallelized across plans.

The most nuanced part is the query CLI: `pov-balance` requires a JOIN to the `characters` table to display names instead of IDs (the MCP tool only returns `character_id`). The export CLI requires `pathlib` for directory creation and formatted markdown output. The TEST-03 gap analysis confirms that no domain currently tests gate violations (`requires_action: true`) as a positive test, and many late-phase domains are missing not-found and validation-failure tests.

**Primary recommendation:** Structure 3 plans — Wave 1 parallelizes CLI modules (session+query in one plan, export+name in another), Wave 2 completes TEST-03 gap fills + TEST-04 in a single plan.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| typer | 0.24.x | CLI subcommand groups | Already used in gate CLI and db CLI — established pattern |
| sqlite3 (stdlib) | stdlib | Sync DB access for CLI | Already used throughout CLI layer; never `aiosqlite` in CLI |
| pathlib (stdlib) | stdlib | Directory creation for export | `Path.mkdir(exist_ok=True, parents=True)` — one-liner |
| pytest | latest | Error contract tests + tool selection | Already installed; pytest-asyncio for MCP tests |
| pytest-asyncio / anyio | latest | Async MCP tests | Already configured; `@pytest.mark.anyio` pattern established |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| json (stdlib) | stdlib | Parse FastMCP TextContent in tests | `json.loads(result.content[0].text)` — established pattern |
| mcp.shared.memory | bundled | In-memory MCP sessions for tests | `create_connected_server_and_client_session(mcp)` |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| pathlib.Path | os.makedirs | pathlib is more Pythonic; already standard in Python 3.12+ |
| typer.prompt() | click.prompt() | Typer wraps click; use typer directly to avoid abstraction leakage |

**Installation:** No new dependencies. All libraries already installed.

## Architecture Patterns

### Recommended Project Structure
```
src/novel/
├── session/
│   ├── __init__.py
│   └── cli.py          # novel session start / close
├── query/
│   ├── __init__.py
│   └── cli.py          # novel query pov-balance / arc-health / thread-gaps
├── export/
│   ├── __init__.py
│   └── cli.py          # novel export chapter [n] / all
├── name/
│   ├── __init__.py
│   └── cli.py          # novel name check / register / suggest
tests/
└── test_tool_selection.py  # NEW — TEST-04
```

Each new CLI module follows the exact structure of `src/novel/gate/cli.py`.

### Pattern 1: Typer Subcommand Group (gate CLI is canonical)

**What:** Each domain gets a `typer.Typer()` app registered on the root CLI via `app.add_typer()`.
**When to use:** All four new CLI groups follow this.
**Example:**
```python
# src/novel/session/cli.py (adapted from src/novel/gate/cli.py)
import typer
from novel.db.connection import get_connection

app = typer.Typer(help="Session management commands")

@app.command()
def start() -> None:
    """Display briefing from the most recent session log."""
    try:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM session_logs "
                "ORDER BY started_at DESC LIMIT 1"
            ).fetchone()
        if not row:
            typer.echo("No session logs found.")
            return
        typer.echo(f"Last session  : {row['started_at']}")
        typer.echo(f"Summary       : {row['summary'] or '(none)'}")
        # ... carried_forward, open questions
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)
```

### Pattern 2: CLI Registration in cli.py

**What:** Root `src/novel/cli.py` gains four `app.add_typer()` calls.
**Example:**
```python
# src/novel/cli.py additions
from novel.session import cli as session_cli
from novel.query import cli as query_cli
from novel.export import cli as export_cli
from novel.name import cli as name_cli

app.add_typer(session_cli.app, name="session")
app.add_typer(query_cli.app, name="query")
app.add_typer(export_cli.app, name="export")
app.add_typer(name_cli.app, name="name")
```

### Pattern 3: Sync SQL Reuse for CLI

**What:** CLI commands mirror MCP tool SQL logic using sync `sqlite3` via `get_connection()`. Never import `novel.mcp.db` (that is async).
**When to use:** All CLI commands. The SQL is already proven in MCP tools.
**Critical difference for pov-balance:** MCP tool returns `character_id`; CLI needs character name. Add a JOIN:
```python
# In query/cli.py — pov_balance command
rows = conn.execute("""
    SELECT
        c.name AS character_name,
        COUNT(ch.id) AS chapter_count,
        COALESCE(SUM(ch.actual_word_count), 0) AS word_count
    FROM chapters ch
    JOIN characters c ON c.id = ch.pov_character_id
    WHERE ch.pov_character_id IS NOT NULL
    GROUP BY ch.pov_character_id
    ORDER BY chapter_count DESC
""").fetchall()
```

### Pattern 4: Export Markdown Generation

**What:** Read chapters + scenes; write one .md file per chapter.
**When to use:** CLEX-01 and CLEX-02.
```python
# In export/cli.py
import json
from pathlib import Path

def _write_chapter(conn, chapter_row, output_dir: Path) -> Path:
    chapter_num = chapter_row["chapter_number"]
    out_path = output_dir / f"chapter_{chapter_num:03d}.md"

    scenes = conn.execute(
        "SELECT * FROM scenes WHERE chapter_id = ? ORDER BY scene_number",
        (chapter_row["id"],)
    ).fetchall()

    lines = [
        f"# Chapter {chapter_num}: {chapter_row['title'] or 'Untitled'}",
        "",
        f"**POV**: {chapter_row['pov_character_name'] or '(unknown)'}",
        # ... etc
    ]
    # ... write scenes or placeholder
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path
```

Note: `chapters` table does not store `pov_character_name` directly — need to JOIN `characters` on `pov_character_id`. Use a JOIN query rather than separate lookup.

### Pattern 5: TEST-04 Tool Selection Structural Check

**What:** Use FastMCP's internal tool registry to verify count, uniqueness, and description length. Use `@pytest.mark.parametrize` for disambiguation pairs.
**How to access tool registry:**
```python
# tests/test_tool_selection.py
import pytest
from novel.mcp.server import mcp

def _get_tools() -> dict:
    """Access registered tools from FastMCP instance."""
    # FastMCP stores tools in _tool_manager
    return mcp._tool_manager.tools  # dict[str, Tool]
```

**Structural test:**
```python
def test_tool_count_in_range():
    tools = _get_tools()
    count = len(tools)
    assert 75 <= count <= 90, f"Expected 75-90 tools, got {count}"

def test_no_duplicate_tool_names():
    tools = _get_tools()
    names = list(tools.keys())
    assert len(names) == len(set(names))

def test_all_tools_have_descriptions():
    tools = _get_tools()
    for name, tool in tools.items():
        desc = tool.description or ""
        assert len(desc) >= 50, f"Tool '{name}' description too short: {len(desc)} chars"
```

**Disambiguation parametrize:**
```python
DISAMBIGUATION_PAIRS = [
    ("what does this character know", "log_character_knowledge"),
    ("get relationship between two characters", "get_relationship"),
    # ... 25+ pairs total (one per domain minimum)
]

@pytest.mark.parametrize("query_phrase,expected_tool", DISAMBIGUATION_PAIRS)
def test_tool_disambiguation(query_phrase, expected_tool):
    tools = _get_tools()
    assert expected_tool in tools, f"Tool '{expected_tool}' not registered"
    description = tools[expected_tool].description or ""
    keywords = [w.lower() for w in query_phrase.split() if len(w) > 3]
    assert any(kw in description.lower() for kw in keywords), (
        f"Tool '{expected_tool}' description does not contain keywords from query"
    )
```

### Anti-Patterns to Avoid
- **Importing `novel.mcp.db` in CLI code:** That is async aiosqlite; CLI uses sync `sqlite3` via `novel.db.connection.get_connection()`.
- **Using `print()` anywhere in `src/novel/`:** Corrupts MCP stdio protocol. CLI uses `typer.echo()`, not `print()`.
- **Catching `typer.Exit` before re-raising in except clauses:** Always re-raise `typer.Exit` — see gate CLI `except typer.Exit: raise` pattern.
- **Calling `novel.tools.*` functions directly from CLI:** Those are async MCP tool handlers. Mirror the SQL; do not call the async functions from sync CLI context.
- **Accessing `mcp._tool_manager` without testing it exists:** FastMCP internals may vary. If this access fails, fall back to `list(mcp.list_tools())` or similar.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Sync DB connection management | Custom sqlite3 wrapper | `novel.db.connection.get_connection()` | Already handles WAL + FK pragma; PRAGMA must be set on every connection |
| Output directory creation | Manual `os.makedirs` calls | `pathlib.Path.mkdir(exist_ok=True, parents=True)` | One-liner, handles nested paths |
| FastMCP tool registry access | Manual tool enumeration | `mcp._tool_manager.tools` dict | FastMCP maintains this internally |
| MCP in-memory test sessions | Custom test server | `create_connected_server_and_client_session(mcp)` | Established pattern; handles lifecycle |
| Gate violation test setup | Custom auth bypass | Sync sqlite3 UPDATE on `architecture_gate` | Same pattern used in 8 existing test files |

**Key insight:** All SQL for CLI commands already exists in MCP tool modules. The CLI work is translation: async aiosqlite → sync sqlite3, MCP response object → `typer.echo()` lines.

## Common Pitfalls

### Pitfall 1: pov-balance returns character_id, not name
**What goes wrong:** CLI copies MCP SQL which returns `character_id`; display shows integers instead of character names.
**Why it happens:** MCP tool is designed for machine consumption (Claude resolves IDs); CLI is for human display.
**How to avoid:** Add `JOIN characters c ON c.id = ch.pov_character_id` to the query and select `c.name AS character_name`.
**Warning signs:** Output shows `POV character: 3` instead of `POV character: Aeryn Vael`.

### Pitfall 2: session close prompt vs --summary flag conflict
**What goes wrong:** When both `--summary TEXT` and the interactive prompt are active, the user gets prompted even when they passed `--summary`.
**Why it happens:** Typer calls `typer.prompt()` unconditionally if coded naively.
**How to avoid:** `summary` must be an `Optional[str]` argument with `default=None`. Only call `typer.prompt()` when `summary is None`.
```python
@app.command()
def close(summary: str | None = typer.Option(None, "--summary")):
    if summary is None:
        summary = typer.prompt("Session summary")
    # proceed with summary
```

### Pitfall 3: Export requires JOIN for character name in chapter header
**What goes wrong:** `chapters.pov_character_id` is an FK integer; exporting `{pov_character_id}` shows a number.
**Why it happens:** Same as pitfall 1 — table stores ID, not name.
**How to avoid:** JOIN chapters to characters in the export query:
```sql
SELECT ch.*, c.name AS pov_character_name
FROM chapters ch
LEFT JOIN characters c ON c.id = ch.pov_character_id
WHERE ch.chapter_number = ?
```
**Warning signs:** Chapter header reads `**POV**: 1` instead of `**POV**: Aeryn Vael`.

### Pitfall 4: FastMCP tool registry access API
**What goes wrong:** `mcp._tool_manager.tools` is a private attribute and could break if FastMCP internals change.
**Why it happens:** FastMCP does not expose a stable public API for listing registered tools in the test context.
**How to avoid:** Test the access pattern with a quick `hasattr(mcp._tool_manager, 'tools')` guard. If it fails, use `asyncio.run(mcp.list_tools())` or equivalent. Current project uses `mcp>=1.26.0,<2.0.0` — pin before changing.
**Warning signs:** `AttributeError: 'ToolManager' object has no attribute 'tools'` during test collection.

### Pitfall 5: TEST-03 gate violation tests require uncertified DB
**What goes wrong:** All late-phase test files use `certified_gate` autouse fixture — adding a gate violation test to the same file would always fail because the gate is already certified.
**Why it happens:** The fixture certifies once per session; no test in the same file can run with an uncertified gate.
**How to avoid:** Gate violation tests need their own uncertified DB. Options:
  1. Add a separate function-scoped fixture within the same test file that creates a fresh uncertified DB and calls one gated tool.
  2. Accept that gate violation coverage can be tested via `test_gate.py` or a shared fixture.
  The CONTEXT.md decision says "add missing cases to each existing `test_*.py` file" — use option 1: a fresh function-scoped DB that skips gate certification.
**Warning signs:** Gate violation test always returns the actual result instead of GateViolation.

### Pitfall 6: name suggest CLI takes faction-or-region but MCP tool takes culture_id
**What goes wrong:** CLI expects a string (faction name or region), but `generate_name_suggestions` takes `culture_id: int`.
**Why it happens:** MCP is typed for Claude's consumption; CLI is for human convenience.
**How to avoid:** CLI must look up `culture_id` from faction/culture name first:
```python
# In name/cli.py — suggest command
row = conn.execute(
    "SELECT id FROM cultures WHERE LOWER(name) = LOWER(?)",
    (faction_or_region,)
).fetchone()
if not row:
    typer.echo(f"No culture found for '{faction_or_region}'.")
    return
culture_id = row["id"]
```
**Warning signs:** `novel name suggest Kaelthari` fails with FK error or always returns empty.

### Pitfall 7: anyio cancel scope in MCP tests
**What goes wrong:** Opening an MCP session in a pytest fixture (not inside the test coroutine) causes `RuntimeError: cancel scope` teardown failure.
**Why it happens:** anyio cancel scopes must be entered and exited in the same task context.
**How to avoid:** All MCP tests use the established `_call_tool(db_path, tool_name, args)` helper that opens and closes the session inside the same async coroutine (not in a fixture). This pattern is proven across 14 existing test files.

## Code Examples

Verified patterns from actual project code:

### Gate CLI Error Pattern (canonical — gate/cli.py)
```python
# Source: src/novel/gate/cli.py
try:
    with get_connection() as conn:
        # ... sync sqlite3 work ...
except typer.Exit:
    raise
except Exception as e:
    typer.echo(f"Error: {e}", err=True)
    raise typer.Exit(code=1)
```

### Tabular Output (gate CLI style)
```python
# Source: src/novel/gate/cli.py
typer.echo(f"  {'ITEM':<40} {'MISSING':>8}")
typer.echo(f"  {'-'*40} {'-'*8}")
for key, count in failing_items:
    typer.echo(f"  {key:<40} {count:>8}")
```
Apply same pattern for query commands with appropriate column widths.

### typer.prompt with CLI flag override (db CLI pattern)
```python
# Source: src/novel/db/cli.py — reset command uses typer.confirm(); session close uses typer.prompt()
if not yes:
    confirmed = typer.confirm("This will drop all tables...", default=False)
```
Adapt for `novel session close`: `if summary is None: summary = typer.prompt("Session summary")`

### MCP Test Helper Pattern (test_names.py — canonical)
```python
# Source: tests/test_names.py
async def _call_tool(db_path: str, tool_name: str, args: dict):
    os.environ["NOVEL_DB_PATH"] = db_path
    async with create_connected_server_and_client_session(mcp) as session:
        return await session.call_tool(tool_name, args)
```

### Gate Certification Fixture (canon/timeline/session test pattern)
```python
# Source: tests/test_canon.py
@pytest.fixture(scope="session", autouse=True)
def certified_gate(test_db_path):
    conn = sqlite3.connect(test_db_path)
    conn.execute("UPDATE gate_checklist_items SET is_passing=1, missing_count=0")
    conn.execute("UPDATE architecture_gate SET is_certified=1, certified_by='test-suite', "
                 "certified_at=datetime('now') WHERE id=1")
    conn.commit()
    conn.close()
```

### Gate Violation Test (function-scoped uncertified DB)
```python
# Pattern for TEST-03 gate violation additions in any gated domain test file
@pytest.fixture
def uncertified_db_path(tmp_path):
    """Create a fresh uncertified DB for gate violation tests."""
    db_file = tmp_path / "uncertified.db"
    conn = sqlite3.connect(str(db_file))
    conn.execute("PRAGMA foreign_keys=ON")
    apply_migrations(conn)
    load_seed_profile(conn, "minimal")
    conn.commit()
    conn.close()
    return str(db_file)

@pytest.mark.anyio
async def test_gated_tool_returns_gate_violation_when_uncertified(uncertified_db_path):
    result = await _call_tool(uncertified_db_path, "get_last_session", {})
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "requires_action" in data
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Monolithic CLI | Typer subcommand groups via `add_typer()` | Phase 1 (established) | Clean separation — each domain gets its own `cli.py` |
| MCP-only tooling | CLI wrappers for human-facing commands | Phase 10 (this phase) | Humans can use `novel` commands; Claude uses MCP tools |
| No tool count validation | Structural TEST-04 | Phase 10 (this phase) | Regression protection if a domain module is accidentally dropped |

**Deprecated/outdated:**
- None relevant to this phase.

## Open Questions

1. **FastMCP tool registry access in test_tool_selection.py**
   - What we know: `mcp._tool_manager.tools` is the internal dict used by FastMCP to store registered tools. Tests for existing tools use `session.call_tool()` not direct registry access.
   - What's unclear: Whether `_tool_manager.tools` is stable across `mcp>=1.26.0` or if there's a public API.
   - Recommendation: Try `mcp._tool_manager.tools` first. If it raises AttributeError, use `asyncio.run(mcp.list_tools())` or inspect via `mcp.list_tools()` in an async test. The tool count can also be verified by calling `list_tools` via the in-memory session.

2. **`novel name suggest` — string vs. culture_id**
   - What we know: The CLI takes a faction-or-region string (human-friendly), but `generate_name_suggestions` takes `culture_id: int`. The `cultures` table has a `name` column.
   - What's unclear: Whether the minimal/gate-ready seed always has a culture with a predictable name (it does: "Kaelthari", id=1).
   - Recommendation: Do a `SELECT id FROM cultures WHERE LOWER(name) = LOWER(?)` lookup. If no match, show "No culture found" and exit 0 (not an error — user may have mistyped). Optionally also try `factions.name` as a fallback.

3. **`novel session close` — finding the open session ID**
   - What we know: `close_session` MCP tool takes `session_id: int`. CLI users don't know the session ID.
   - What's unclear: How does the CLI resolve which session to close?
   - Recommendation: CLI should always close the most recent open session: `SELECT id FROM session_logs WHERE closed_at IS NULL ORDER BY started_at DESC LIMIT 1`. If none found, print "No open session to close." and exit 0.

## Sources

### Primary (HIGH confidence)
- Direct codebase inspection — `src/novel/gate/cli.py`, `src/novel/db/cli.py`, `src/novel/cli.py` (canonical CLI patterns)
- Direct codebase inspection — `src/novel/tools/session.py`, `src/novel/tools/arcs.py`, `src/novel/tools/names.py` (SQL to mirror)
- Direct codebase inspection — `tests/test_names.py`, `tests/conftest.py`, `tests/test_canon.py` (test patterns)
- Direct codebase inspection — `src/novel/mcp/server.py` (confirmed 17 tool modules, 99 actual `@mcp.tool()` decorators)
- Tool count verification: `grep -c "^    @mcp.tool()" src/novel/tools/*.py` — indentation-filtered to exclude docstring mentions

### Secondary (MEDIUM confidence)
- Typer documentation — `typer.prompt()`, `typer.Option()`, `typer.Argument()`, `typer.Typer()`, `add_typer()` patterns consistent with project usage
- pytest parametrize pattern — `@pytest.mark.parametrize` for disambiguation fixture in TEST-04

### Tertiary (LOW confidence)
- FastMCP `_tool_manager.tools` internal API — unverified in docs; inferred from common FastMCP usage patterns. Needs validation during implementation.

## Tool Count Clarification

Actual tool count (verified via `grep -c "^    @mcp.tool()" src/novel/tools/*.py`, indentation-filtered to exclude docstring mentions):
```
arcs.py:          6
canon.py:         7
chapters.py:      5
characters.py:    8
foreshadowing.py: 8
gate.py:          5
knowledge.py:     5
magic.py:         4
names.py:         4
plot.py:          3
publishing.py:    5
relationships.py: 6
scenes.py:        4
session.py:       10
timeline.py:      8
voice.py:         5
world.py:         6
```
**Total: 99 registered tools** (not ~80 as stated in CONTEXT.md).

**Impact on TEST-04:** The CONTEXT.md specifies a guard of `75 <= count <= 90`. The actual count of 99 falls outside this range. The planner must adjust the structural test bounds to `90 <= count <= 110` or determine the actual count at test runtime using `asyncio.run(mcp.list_tools())`. The guard should protect against accidental module drops (lower bound) and accidental duplications (upper bound), not assert an exact count.

**Recommended TEST-04 bounds:** `90 <= count <= 110` based on actual verified count of 99.

## Error Contract Gap Analysis (TEST-03)

Current state by domain (from code audit):

| Domain | Not-Found Tests | Validation Failure Tests | Gate Violation Tests |
|--------|----------------|--------------------------|----------------------|
| characters | 3 | 0 | 0 |
| relationships | 2 | 0 | 0 |
| chapters | 2 | 0 | 0 |
| scenes | 2 | 0 | 0 |
| world | 2 | 0 | 0 |
| magic | 1 | 0 | 0 |
| plot | 1 | 0 | 0 |
| arcs | 1 | 1 | 0 |
| gate | 1 | 1 | 0 (gate domain itself, different concept) |
| session | 0 | 0 | 0 |
| timeline | 4 | 0 | 0 |
| canon | 0 | 0 | 0 |
| knowledge | 0 | 0 | 0 |
| foreshadowing | 0 | 0 | 0 |
| voice | 2 | 0 | 0 |
| publishing | 2 | 0 | 0 |
| names | 1 | 1 | n/a (gate-free) |

**Gaps by error contract type:**
- **Not-found**: canon, knowledge, foreshadowing, session have zero not-found tests
- **Validation failure**: almost all domains have zero validation-failure tests (only arcs, gate, names have any)
- **Gate violation**: zero tests across ALL gated domains — no domain tests the `requires_action: true` path

**Priority for TEST-03 additions (per CONTEXT.md):**
1. canon, knowledge, foreshadowing, voice, publishing — add not-found + gate violation tests
2. session — add not-found tests (e.g., `close_session` with unknown ID, `get_last_session` when DB empty)
3. Validation failure — add to domains that have tools returning `is_valid: false` (characters: `upsert_character` with bad data; world: `check_magic_compliance` could be tested with invalid params)
4. Gate violation — add one test per gated domain using function-scoped uncertified DB

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — direct codebase inspection, all libraries already installed
- Architecture: HIGH — pattern directly extracted from `gate/cli.py` which is the canonical model
- Pitfalls: HIGH — derived from actual test failures documented in STATE.md + code inspection
- Error contract gaps: HIGH — direct grep analysis of test files

**Research date:** 2026-03-08
**Valid until:** 2026-04-08 (stable — no dependency changes expected)
