# Phase 5: Plot & Arcs - Research

**Researched:** 2026-03-07
**Domain:** Python MCP tools — SQLite plot/arc domain (migrations 016, 017)
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Tool module split**
- 2 modules: `tools/plot.py` and `tools/arcs.py` — matches model file organization (`models/plot.py`, `models/arcs.py`)
- `tools/plot.py`: `get_plot_thread`, `list_plot_threads`, `upsert_plot_thread`
- `tools/arcs.py`: `get_arc`, `get_arc_health`, `get_chekovs_guns`, `upsert_chekov`, `get_subplot_touchpoint_gaps`, `log_arc_health`
- `server.py` gets 2 more `register(mcp)` calls: `from novel.tools import plot, arcs`

**`get_arc` — dual-mode lookup (PLOT-04)**
- Signature: `get_arc(arc_id: int | None = None, character_id: int | None = None)`
- If `arc_id` provided: return single `CharacterArc` or `NotFoundResponse`
- If `character_id` provided: return list of all `CharacterArc` rows for that character (empty list if none)
- If both provided: `arc_id` takes precedence
- If neither provided: `ValidationFailure` — at least one required
- This covers both direct lookup and character-based discovery without adding a separate list tool

**`get_arc_health` — full history (PLOT-05)**
- Signature: `get_arc_health(character_id: int, arc_id: int | None = None)`
- Returns full `arc_health_log` history ordered by chapter_id ascending — not just the latest entry
- If `arc_id` provided: filter to that arc only; else return health for all arcs of that character
- Returns empty list (not `NotFoundResponse`) when no health logs exist yet — log is optional

**`get_subplot_touchpoint_gaps` — configurable threshold (PLOT-06)**
- Signature: `get_subplot_touchpoint_gaps(threshold_chapters: int = 5)`
- Finds plot threads where `thread_type = 'subplot'` AND `status = 'active'` AND the most recent `subplot_touchpoint_log` entry is more than `threshold_chapters` chapters ago (by chapter_id ordering)
- Also includes active subplots with zero touchpoints logged (never touched since opened)
- Returns list of `{plot_thread_id, name, last_touchpoint_chapter_id, chapters_since_touchpoint}` — structured enough for Claude to act on
- Default 5 chapters is a sensible novel pacing cadence; caller can tighten or loosen

**`get_chekovs_guns` — status filter + unresolved flag (PLOT-03)**
- Signature: `get_chekovs_guns(status: str | None = None, unresolved_only: bool = False)`
- `status` filter: matches `chekovs_gun_registry.status` column (planted/fired/misfired) — `None` returns all
- `unresolved_only=True`: returns only entries where `status = 'planted'` AND `payoff_chapter_id IS NULL`
- `unresolved_only` takes precedence over `status` when both are provided
- Returns list of `ChekhovGun` models

**`list_plot_threads` — optional filters (PLOT-02)**
- Signature: `list_plot_threads(thread_type: str | None = None, status: str | None = None)`
- Filters on `plot_threads.thread_type` (main/subplot/backstory) and/or `status` (active/closed/dormant)
- Both optional — no args returns all threads

### Claude's Discretion
- All SQL query patterns and join strategies
- `upsert_plot_thread` and `upsert_chekov` conflict resolution (INSERT OR REPLACE vs ON CONFLICT UPDATE)
- Whether `upsert_plot_thread` touches `chapter_plot_threads` junction table or just `plot_threads` (recommend: just plot_threads — junction management is implicit via chapter tools)
- Test fixture scope (session vs function)
- Plan file split across the 2 plan slots

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| PLOT-01 | Claude can retrieve a plot thread by ID (`get_plot_thread`) | Simple SELECT by PK from `plot_threads`; return `PlotThread` or `NotFoundResponse` |
| PLOT-02 | Claude can list all plot threads in the book (`list_plot_threads`) | SELECT with optional WHERE on `thread_type` and/or `status`; return `list[PlotThread]` |
| PLOT-03 | Claude can retrieve Chekhov's gun registry entries (`get_chekovs_guns`) | SELECT from `chekovs_gun_registry` with dual filter mode; return `list[ChekhovGun]` |
| PLOT-04 | Claude can retrieve a character arc (`get_arc`) | Dual-mode: by `arc_id` (single) or `character_id` (list); covers `character_arcs` table |
| PLOT-05 | Claude can retrieve arc health status for a character (`get_arc_health`) | JOIN `arc_health_log` to `character_arcs` on `arc_id`, filter by `character_id`; return full history ordered by `chapter_id` ASC |
| PLOT-06 | Claude can retrieve subplots overdue for a touchpoint (`get_subplot_touchpoint_gaps`) | Aggregate query: LEFT JOIN `subplot_touchpoint_log`, GROUP BY `plot_thread_id`, compare MAX(chapter_id) to threshold |
| PLOT-07 | Claude can create or update a plot thread (`upsert_plot_thread`) | INSERT / ON CONFLICT(id) DO UPDATE on `plot_threads`; does NOT touch junction tables |
| PLOT-08 | Claude can create or update a Chekhov's gun entry (`upsert_chekov`) | INSERT / ON CONFLICT(id) DO UPDATE on `chekovs_gun_registry` |
| PLOT-09 | Claude can log arc health for a character at a chapter (`log_arc_health`) | Append-only INSERT into `arc_health_log`; no ON CONFLICT clause — same pattern as `log_magic_use` |
</phase_requirements>

---

## Summary

Phase 5 is a domain-tool extension following the exact patterns established in Phases 3 and 4. It introduces 9 tools across 2 new modules (`tools/plot.py`, `tools/arcs.py`) that surface data from migrations 016 and 017. All Pydantic models are already written and all seed data for the test assertions is already inserted by `load_seed_profile(conn, "minimal")` — no schema work is required.

The implementation complexity is concentrated in three places. First, `get_arc` requires branching logic: single-record return when `arc_id` is given, list return when `character_id` is given, and `ValidationFailure` when neither is provided. Second, `get_subplot_touchpoint_gaps` requires a non-trivial aggregate SQL query joining `plot_threads` to `subplot_touchpoint_log` with a LEFT JOIN to capture zero-touchpoint subplots. Third, the upsert tools must use `ON CONFLICT(id) DO UPDATE` (not `INSERT OR REPLACE`) because both `plot_threads` and `chekovs_gun_registry` have FK children in junction tables — replacing the row would break those FK references.

**Primary recommendation:** Build `tools/plot.py` first (3 simpler tools), then `tools/arcs.py` (6 tools including the more complex `get_arc` and `get_subplot_touchpoint_gaps`). Wire both into `server.py` last. Write tests (`test_plot.py`, `test_arcs.py`) alongside the tools, using the session-scoped DB fixture + per-test MCP session pattern established in Phases 3–4.

---

## Standard Stack

### Core (all already installed — no new dependencies)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `mcp.server.fastmcp` | bundled with `mcp>=1.26.0,<2.0.0` | FastMCP instance, `@mcp.tool()` decorator | Project decision; standalone `fastmcp` PyPI package has diverged |
| `aiosqlite` | project requirement | Async SQLite connection in MCP tools | Already used by every existing tool module |
| `pydantic` | `>=2.11` | `PlotThread`, `CharacterArc`, `ChekhovGun`, etc. | All domain models already defined in `models/plot.py` and `models/arcs.py` |
| `pytest` + `pytest-asyncio` | dev deps | Async tool tests | Same pattern used by Phases 3–4 tests |

**Installation:** No new packages needed. All dependencies are already in `pyproject.toml`.

---

## Architecture Patterns

### Established Project Structure (extend, do not change)

```
src/novel/
├── tools/
│   ├── plot.py          # NEW — PLOT-01, PLOT-02, PLOT-07
│   ├── arcs.py          # NEW — PLOT-03, PLOT-04, PLOT-05, PLOT-06, PLOT-08, PLOT-09
│   ├── chapters.py      # existing
│   └── ...
├── models/
│   ├── plot.py          # exists — PlotThread, ChapterPlotThread, ChapterCharacterArc
│   ├── arcs.py          # exists — CharacterArc, ArcHealthLog, ChekhovGun, SubplotTouchpoint
│   └── shared.py        # exists — NotFoundResponse, ValidationFailure
└── mcp/
    └── server.py        # update: add plot + arcs register() calls

tests/
├── test_plot.py         # NEW
├── test_arcs.py         # NEW
└── conftest.py          # existing — no changes needed
```

### Pattern 1: Tool Module Structure

Every tool module follows the identical shape. No deviation in Phase 5.

```python
# Source: established pattern from tools/world.py, tools/magic.py
"""Plot domain MCP tools."""

import logging
from mcp.server.fastmcp import FastMCP
from novel.mcp.db import get_connection
from novel.models.plot import PlotThread
from novel.models.shared import NotFoundResponse, ValidationFailure

logger = logging.getLogger(__name__)


def register(mcp: FastMCP) -> None:
    """Register all 3 plot domain tools with the given FastMCP instance."""

    @mcp.tool()
    async def get_plot_thread(plot_thread_id: int) -> PlotThread | NotFoundResponse:
        """..."""
        async with get_connection() as conn:
            rows = await conn.execute_fetchall(
                "SELECT * FROM plot_threads WHERE id = ?", (plot_thread_id,)
            )
            if not rows:
                return NotFoundResponse(not_found_message=f"Plot thread {plot_thread_id} not found")
            return PlotThread(**dict(rows[0]))
```

### Pattern 2: Optional Filter List Query

Used by `list_plot_threads` and `get_chekovs_guns`. Build WHERE clause dynamically.

```python
# Source: established pattern — same approach used in list_characters
@mcp.tool()
async def list_plot_threads(
    thread_type: str | None = None,
    status: str | None = None,
) -> list[PlotThread]:
    async with get_connection() as conn:
        clauses, params = [], []
        if thread_type is not None:
            clauses.append("thread_type = ?")
            params.append(thread_type)
        if status is not None:
            clauses.append("status = ?")
            params.append(status)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        rows = await conn.execute_fetchall(
            f"SELECT * FROM plot_threads {where} ORDER BY id", params
        )
        return [PlotThread(**dict(r)) for r in rows]
```

### Pattern 3: `get_chekovs_guns` Dual-Mode Filter

`unresolved_only` takes precedence over `status` when both are provided.

```python
@mcp.tool()
async def get_chekovs_guns(
    status: str | None = None,
    unresolved_only: bool = False,
) -> list[ChekhovGun]:
    async with get_connection() as conn:
        if unresolved_only:
            rows = await conn.execute_fetchall(
                "SELECT * FROM chekovs_gun_registry "
                "WHERE status = 'planted' AND payoff_chapter_id IS NULL ORDER BY id",
                [],
            )
        elif status is not None:
            rows = await conn.execute_fetchall(
                "SELECT * FROM chekovs_gun_registry WHERE status = ? ORDER BY id",
                (status,),
            )
        else:
            rows = await conn.execute_fetchall(
                "SELECT * FROM chekovs_gun_registry ORDER BY id", []
            )
        return [ChekhovGun(**dict(r)) for r in rows]
```

### Pattern 4: `get_arc` Dual-Mode Lookup

Returns a single model or a list depending on which parameter is given. `ValidationFailure` when neither.

```python
@mcp.tool()
async def get_arc(
    arc_id: int | None = None,
    character_id: int | None = None,
) -> CharacterArc | list[CharacterArc] | NotFoundResponse | ValidationFailure:
    if arc_id is None and character_id is None:
        return ValidationFailure(
            is_valid=False,
            errors=["At least one of arc_id or character_id must be provided"]
        )
    async with get_connection() as conn:
        if arc_id is not None:
            rows = await conn.execute_fetchall(
                "SELECT * FROM character_arcs WHERE id = ?", (arc_id,)
            )
            if not rows:
                return NotFoundResponse(not_found_message=f"Arc {arc_id} not found")
            return CharacterArc(**dict(rows[0]))
        else:
            rows = await conn.execute_fetchall(
                "SELECT * FROM character_arcs WHERE character_id = ? ORDER BY id",
                (character_id,),
            )
            return [CharacterArc(**dict(r)) for r in rows]
```

### Pattern 5: `get_arc_health` — JOIN Query for Character Filter

`arc_health_log` only has `arc_id`, not `character_id` directly. Join to `character_arcs` to filter by character.

```python
@mcp.tool()
async def get_arc_health(
    character_id: int,
    arc_id: int | None = None,
) -> list[ArcHealthLog]:
    async with get_connection() as conn:
        if arc_id is not None:
            rows = await conn.execute_fetchall(
                """SELECT ahl.*
                   FROM arc_health_log ahl
                   JOIN character_arcs ca ON ca.id = ahl.arc_id
                   WHERE ca.character_id = ? AND ahl.arc_id = ?
                   ORDER BY ahl.chapter_id ASC""",
                (character_id, arc_id),
            )
        else:
            rows = await conn.execute_fetchall(
                """SELECT ahl.*
                   FROM arc_health_log ahl
                   JOIN character_arcs ca ON ca.id = ahl.arc_id
                   WHERE ca.character_id = ?
                   ORDER BY ahl.chapter_id ASC""",
                (character_id,),
            )
        return [ArcHealthLog(**dict(r)) for r in rows]
```

### Pattern 6: `get_subplot_touchpoint_gaps` — Aggregate Query

The most complex SQL in Phase 5. LEFT JOIN captures subplots with zero touchpoints.

```python
@mcp.tool()
async def get_subplot_touchpoint_gaps(
    threshold_chapters: int = 5,
) -> list[dict]:
    async with get_connection() as conn:
        # Subquery finds the current max chapter_id in the DB to compute 'chapters since'
        max_row = await conn.execute_fetchall(
            "SELECT MAX(id) AS max_id FROM chapters", []
        )
        max_chapter_id = max_row[0]["max_id"] or 0

        rows = await conn.execute_fetchall(
            """SELECT
                   pt.id AS plot_thread_id,
                   pt.name,
                   MAX(stl.chapter_id) AS last_touchpoint_chapter_id,
                   CASE
                       WHEN MAX(stl.chapter_id) IS NULL THEN NULL
                       ELSE (? - MAX(stl.chapter_id))
                   END AS chapters_since_touchpoint
               FROM plot_threads pt
               LEFT JOIN subplot_touchpoint_log stl ON stl.plot_thread_id = pt.id
               WHERE pt.thread_type = 'subplot'
                 AND pt.status = 'active'
               GROUP BY pt.id, pt.name
               HAVING MAX(stl.chapter_id) IS NULL
                   OR (? - MAX(stl.chapter_id)) > ?
               ORDER BY chapters_since_touchpoint DESC NULLS LAST""",
            (max_chapter_id, max_chapter_id, threshold_chapters),
        )
        return [dict(r) for r in rows]
```

**Note on seed data:** The minimal seed inserts only `thread_type = 'main'` plot threads, so `get_subplot_touchpoint_gaps` will return an empty list against the seed DB. Tests should INSERT a subplot thread directly to exercise the gap detection logic.

### Pattern 7: Upsert — ON CONFLICT(id) DO UPDATE

Use for both `upsert_plot_thread` and `upsert_chekov`. Never `INSERT OR REPLACE` on tables with FK children — it would delete and re-insert the parent row, cascading deletions or FK violations.

```python
@mcp.tool()
async def upsert_plot_thread(
    plot_thread_id: int | None,
    name: str,
    thread_type: str | None = None,
    status: str | None = None,
    opened_chapter_id: int | None = None,
    closed_chapter_id: int | None = None,
    parent_thread_id: int | None = None,
    summary: str | None = None,
    resolution: str | None = None,
    stakes: str | None = None,
    notes: str | None = None,
) -> PlotThread | ValidationFailure:
    async with get_connection() as conn:
        try:
            if plot_thread_id is None:
                cursor = await conn.execute(
                    """INSERT INTO plot_threads
                           (name, thread_type, status, opened_chapter_id, closed_chapter_id,
                            parent_thread_id, summary, resolution, stakes, notes, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))""",
                    (name, thread_type or "main", status or "active",
                     opened_chapter_id, closed_chapter_id, parent_thread_id,
                     summary, resolution, stakes, notes),
                )
                new_id = cursor.lastrowid
                await conn.commit()
                row = await conn.execute_fetchall(
                    "SELECT * FROM plot_threads WHERE id = ?", (new_id,)
                )
            else:
                await conn.execute(
                    """INSERT INTO plot_threads
                           (id, name, thread_type, status, opened_chapter_id, closed_chapter_id,
                            parent_thread_id, summary, resolution, stakes, notes, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                       ON CONFLICT(id) DO UPDATE SET
                           name=excluded.name,
                           thread_type=excluded.thread_type,
                           status=excluded.status,
                           opened_chapter_id=excluded.opened_chapter_id,
                           closed_chapter_id=excluded.closed_chapter_id,
                           parent_thread_id=excluded.parent_thread_id,
                           summary=excluded.summary,
                           resolution=excluded.resolution,
                           stakes=excluded.stakes,
                           notes=excluded.notes,
                           updated_at=datetime('now')""",
                    (plot_thread_id, name, thread_type or "main", status or "active",
                     opened_chapter_id, closed_chapter_id, parent_thread_id,
                     summary, resolution, stakes, notes),
                )
                await conn.commit()
                row = await conn.execute_fetchall(
                    "SELECT * FROM plot_threads WHERE id = ?", (plot_thread_id,)
                )
        except Exception as exc:
            logger.error("upsert_plot_thread failed: %s", exc)
            return ValidationFailure(is_valid=False, errors=[str(exc)])
        return PlotThread(**dict(row[0]))
```

### Pattern 8: Append-Only Log Insert

`log_arc_health` is append-only — same pattern as `log_magic_use`. No ON CONFLICT clause.

```python
@mcp.tool()
async def log_arc_health(
    arc_id: int,
    chapter_id: int,
    health_status: str = "on-track",
    notes: str | None = None,
) -> ArcHealthLog | ValidationFailure:
    async with get_connection() as conn:
        try:
            cursor = await conn.execute(
                "INSERT INTO arc_health_log (arc_id, chapter_id, health_status, notes) "
                "VALUES (?, ?, ?, ?)",
                (arc_id, chapter_id, health_status, notes),
            )
            new_id = cursor.lastrowid
            await conn.commit()
            row = await conn.execute_fetchall(
                "SELECT * FROM arc_health_log WHERE id = ?", (new_id,)
            )
            return ArcHealthLog(**dict(row[0]))
        except Exception as exc:
            logger.error("log_arc_health failed: %s", exc)
            return ValidationFailure(is_valid=False, errors=[str(exc)])
```

### Pattern 9: Test File Structure

Each test file manages its own session-scoped DB fixture (not the shared `conftest.py` fixture) to avoid cross-file collision. MCP session entered per-test, not per-fixture (anyio cancel scope constraint).

```python
# Source: established pattern from tests/test_magic.py

@pytest.fixture(scope="session")
def test_db_path(tmp_path_factory):
    db_file = tmp_path_factory.mktemp("plot_db") / "test_plot.db"
    conn = sqlite3.connect(str(db_file))
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA journal_mode=WAL")
    apply_migrations(conn)
    load_seed_profile(conn, "minimal")
    conn.commit()
    conn.close()
    return str(db_file)


async def _call_tool(db_path: str, tool_name: str, args: dict):
    os.environ["NOVEL_DB_PATH"] = db_path
    async with create_connected_server_and_client_session(mcp) as session:
        return await session.call_tool(tool_name, args)
```

### Pattern 10: server.py Wiring

Add exactly 2 lines to the import and 2 lines for registration in `server.py`:

```python
# Add to import line (extend existing)
from novel.tools import characters, relationships, chapters, scenes, world, magic, plot, arcs

# Add after existing Phase 4 register() calls
# Register domain tools — Phase 5
plot.register(mcp)
arcs.register(mcp)
```

And update the module docstring to say "Phase 5" in the registered tools list.

### Anti-Patterns to Avoid

- **INSERT OR REPLACE on tables with FK children:** `plot_threads` has `chapter_plot_threads` as a FK child. INSERT OR REPLACE deletes then re-inserts the parent, which cascades or causes FK violations. Use `ON CONFLICT(id) DO UPDATE` instead.
- **print() statements:** Any `print()` in tool modules corrupts the stdio MCP protocol. Use `logger.debug()` / `logger.error()` only.
- **Raising exceptions:** Tools never raise. Wrap DB operations in `try/except` and return `ValidationFailure(is_valid=False, errors=[str(exc)])`.
- **Global mcp import in tools:** Tools receive `mcp` as a parameter to `register()`. Never import `mcp` from `server.py` in a tool module — circular import.
- **conn.commit() on read-only tools:** `get_*` and `list_*` tools are read-only. No `commit()` call — same pattern as `check_magic_compliance`.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Async SQLite connection | Custom connection pool | `novel.mcp.db.get_connection()` | Already sets WAL + FK pragmas; used by all existing tools |
| Error union types | Custom exception hierarchy | `NotFoundResponse`, `ValidationFailure` from `models/shared.py` | Error contract already established in Phase 3; all tools return these |
| Pydantic models | New dataclasses | `PlotThread`, `CharacterArc`, `ArcHealthLog`, `ChekhovGun`, `SubplotTouchpoint` | All defined in `models/plot.py` and `models/arcs.py` — Phase 2 work |
| Test DB setup | New migration runner | `apply_migrations()` + `load_seed_profile(conn, "minimal")` | Seed already populates plot_threads, character_arcs, arc_health_log, chekovs_gun_registry, subplot_touchpoint_log |
| FastMCP in-memory client | Custom test harness | `create_connected_server_and_client_session(mcp)` | Standard MCP SDK pattern; used in all Phase 3–4 tests |

**Key insight:** Phase 5 has zero infrastructure work. The entire phase is tool logic + SQL queries + tests. All models, DB infrastructure, and test patterns are inherited from earlier phases.

---

## Common Pitfalls

### Pitfall 1: `get_arc` Return Type Complexity

**What goes wrong:** FastMCP serializes `list[T]` as N separate `TextContent` blocks, while a single model becomes 1 block. `get_arc` returns either a single `CharacterArc` OR a `list[CharacterArc]` depending on which parameter is given. Tests must handle both shapes.

**Why it happens:** The dual-mode design means the tool's return type is a union of a single model and a list — unusual for MCP tools.

**How to avoid:** In tests, check `result.content` length before deciding whether to parse as a list or a single object. When `character_id` path is taken, always use `[json.loads(c.text) for c in result.content]`. When `arc_id` path is taken, use `json.loads(result.content[0].text)`.

**Warning signs:** Test assertion `data["id"]` fails on list result — means test used wrong parsing for the list branch.

### Pitfall 2: `get_subplot_touchpoint_gaps` Returns Empty List Against Seed DB

**What goes wrong:** The minimal seed only inserts a `thread_type = 'main'` plot thread. The gap query filters `WHERE thread_type = 'subplot'`, so it always returns empty against unmodified seed data.

**Why it happens:** Seed data prioritizes coverage of all domain tables, not testing every query variant. Subplot gaps are a specialized query.

**How to avoid:** Test for `get_subplot_touchpoint_gaps` must INSERT a subplot thread directly via raw SQL in the test setup, OR use a function-scoped fixture that adds test-only rows. The session-scoped DB is reused across tests — INSERT a subplot thread that persists for the session, or use a separate function-scoped connection for isolation.

**Warning signs:** Test passes vacuously because it only checks `isinstance(result, list)` without verifying the gap detection logic actually fired.

### Pitfall 3: `upsert_plot_thread` Omits Defaults for thread_type / status

**What goes wrong:** `plot_threads` schema has `NOT NULL DEFAULT 'main'` for `thread_type` and `NOT NULL DEFAULT 'active'` for `status`. If the upsert passes `None` for these, the SQLite INSERT gets a NULL into a NOT NULL column → IntegrityError.

**Why it happens:** Tool parameters are `str | None` for flexibility, but the DB column is NOT NULL.

**How to avoid:** Apply fallback defaults in the upsert: `thread_type or "main"`, `status or "active"`. The `PlotThread` model already carries these defaults — the tool should mirror them.

**Warning signs:** `upsert_plot_thread` with minimal args raises `NOT NULL constraint failed: plot_threads.thread_type`.

### Pitfall 4: `chekovs_gun_registry` Has No UNIQUE Constraint Beyond PK

**What goes wrong:** Unlike `factions` (UNIQUE name), `chekovs_gun_registry` has no UNIQUE constraint on `name`. The None-id branch of `upsert_chekov` cannot use `ON CONFLICT(name)` — `lastrowid` is the only way to recover the new row id.

**Why it happens:** Chekhov's guns can legitimately share names (e.g., "The Scratch Marks" could appear twice if the user re-registers).

**How to avoid:** For None-id branch: plain INSERT, use `cursor.lastrowid` to fetch the new row. For provided-id branch: `ON CONFLICT(id) DO UPDATE`. This is the same two-branch pattern as `upsert_location`.

**Warning signs:** `upsert_chekov` None-id branch tries `ON CONFLICT(name)` → SQLite error "no such conflict target".

### Pitfall 5: `arc_health_log` Has No UNIQUE Constraint — log_arc_health Is Truly Append-Only

**What goes wrong:** `arc_health_log` allows multiple entries for the same `(arc_id, chapter_id)` pair. Calling `log_arc_health` twice with the same args inserts two rows — this is correct behavior (health can be re-evaluated), but tests that call it multiple times will accumulate rows.

**Why it happens:** It mirrors `magic_use_log` — an audit trail, not an upsertable record.

**How to avoid:** Tests for `log_arc_health` should count rows before and after, not assert a specific total count. Use `assert new_id is not None` and verify returned model fields.

### Pitfall 6: anyio Cancel Scope — MCP Session Per Test, Not Per Fixture

**What goes wrong:** If `mcp_session` is a pytest-asyncio fixture that yields a session, anyio's cancel scope teardown errors occur.

**Why it happens:** anyio cancel scopes must be entered and exited in the same coroutine. Fixtures and test functions run in different coroutines under pytest-asyncio.

**How to avoid:** Enter and exit `create_connected_server_and_client_session(mcp)` inside each test function via the `_call_tool()` helper. This is already established pattern in Phases 3–4; do not deviate.

---

## Code Examples

### Seed Data Available for Tests

The minimal seed already populates all Phase 5 tables with these IDs (insertion order guarantees these values given autoincrement from a clean DB):

| Table | Key Rows | Notes |
|-------|----------|-------|
| `plot_threads` | id=1, `name="The Hidden Vault"`, `thread_type="main"`, `status="active"` | Seeded in Phase 9 of `_load_minimal` |
| `character_arcs` | id=1, `character_id=1` (Aeryn), `arc_type="transformation"` | Same phase |
| `arc_health_log` | id=1, `arc_id=1`, `chapter_id=1`, `health_status="on-track"` | Same phase |
| `chekovs_gun_registry` | id=1, `name="The Scratch Marks"`, `status="planted"`, `payoff_chapter_id=NULL` | Same phase |
| `subplot_touchpoint_log` | id=1, `plot_thread_id=1`, `chapter_id=2` | Same phase — but thread_type is "main", not "subplot" |

**Chapter IDs:** chapters 1, 2, 3 exist (IDs 1, 2, 3). Character IDs: 1 (Aeryn), 2 (Solvann), 3 (Ithrel), 4 (Mira), 5 (Calder).

### Multi-Result Parsing in Tests

```python
# Single result (get_plot_thread, get_arc with arc_id)
data = json.loads(result.content[0].text)
assert data["name"] == "The Hidden Vault"

# List result (list_plot_threads, get_arc with character_id, get_chekovs_guns)
items = [json.loads(c.text) for c in result.content]
assert len(items) >= 1

# NotFoundResponse
data = json.loads(result.content[0].text)
assert "not_found_message" in data

# ValidationFailure
data = json.loads(result.content[0].text)
assert data["is_valid"] is False
assert len(data["errors"]) > 0
```

### `get_subplot_touchpoint_gaps` Test Setup

Since seed data has no subplot threads, the test must insert one:

```python
# In test setup or function-scoped fixture
conn = sqlite3.connect(test_db_path)
conn.execute("PRAGMA foreign_keys=ON")
# Insert a subplot thread — use chapter 1 (far enough back to trigger gap at threshold=2)
conn.execute(
    "INSERT INTO plot_threads (name, thread_type, status, opened_chapter_id, canon_status) "
    "VALUES ('The Rival Subplot', 'subplot', 'active', 1, 'draft')"
)
conn.commit()
conn.close()
# Now call get_subplot_touchpoint_gaps(threshold_chapters=1) — this subplot has zero touchpoints
```

---

## Schema Reference

### `plot_threads` (migration 016)

| Column | Type | Constraint | Default |
|--------|------|-----------|---------|
| id | INTEGER | PK AUTOINCREMENT | - |
| name | TEXT | NOT NULL | - |
| thread_type | TEXT | NOT NULL | 'main' |
| status | TEXT | NOT NULL | 'active' |
| opened_chapter_id | INTEGER | REFERENCES chapters(id) | NULL |
| closed_chapter_id | INTEGER | REFERENCES chapters(id) | NULL |
| parent_thread_id | INTEGER | REFERENCES plot_threads(id) | NULL |
| summary | TEXT | | NULL |
| resolution | TEXT | | NULL |
| stakes | TEXT | | NULL |
| notes | TEXT | | NULL |
| canon_status | TEXT | NOT NULL | 'draft' |
| created_at | TEXT | NOT NULL | datetime('now') |
| updated_at | TEXT | NOT NULL | datetime('now') |

**FK Children:** `chapter_plot_threads.plot_thread_id`, `subplot_touchpoint_log.plot_thread_id`
**UNIQUE constraints:** None (PK only)

### `character_arcs` (migration 017)

| Column | Type | Constraint | Default |
|--------|------|-----------|---------|
| id | INTEGER | PK AUTOINCREMENT | - |
| character_id | INTEGER | NOT NULL REFERENCES characters(id) | - |
| arc_type | TEXT | NOT NULL | 'growth' |
| starting_state | TEXT | | NULL |
| desired_state | TEXT | | NULL |
| wound | TEXT | | NULL |
| lie_believed | TEXT | | NULL |
| truth_to_learn | TEXT | | NULL |
| opened_chapter_id | INTEGER | REFERENCES chapters(id) | NULL |
| closed_chapter_id | INTEGER | REFERENCES chapters(id) | NULL |
| notes | TEXT | | NULL |
| canon_status | TEXT | NOT NULL | 'draft' |
| created_at | TEXT | NOT NULL | datetime('now') |
| updated_at | TEXT | NOT NULL | datetime('now') |

**FK Children:** `arc_health_log.arc_id`, `chapter_character_arcs.arc_id`

### `arc_health_log` (migration 017)

| Column | Type | Constraint | Default |
|--------|------|-----------|---------|
| id | INTEGER | PK AUTOINCREMENT | - |
| arc_id | INTEGER | NOT NULL REFERENCES character_arcs(id) | - |
| chapter_id | INTEGER | NOT NULL REFERENCES chapters(id) | - |
| health_status | TEXT | NOT NULL | 'on-track' |
| notes | TEXT | | NULL |
| created_at | TEXT | NOT NULL | datetime('now') |

**UNIQUE constraints:** None — append-only log

### `chekovs_gun_registry` (migration 017)

| Column | Type | Constraint | Default |
|--------|------|-----------|---------|
| id | INTEGER | PK AUTOINCREMENT | - |
| name | TEXT | NOT NULL | - |
| description | TEXT | NOT NULL | - |
| planted_chapter_id | INTEGER | REFERENCES chapters(id) | NULL |
| planted_scene_id | INTEGER | REFERENCES scenes(id) | NULL |
| payoff_chapter_id | INTEGER | REFERENCES chapters(id) | NULL |
| payoff_scene_id | INTEGER | REFERENCES scenes(id) | NULL |
| status | TEXT | NOT NULL | 'planted' |
| notes | TEXT | | NULL |
| canon_status | TEXT | NOT NULL | 'draft' |
| created_at | TEXT | NOT NULL | datetime('now') |
| updated_at | TEXT | NOT NULL | datetime('now') |

**UNIQUE constraints:** None beyond PK

### `subplot_touchpoint_log` (migration 017)

| Column | Type | Constraint | Default |
|--------|------|-----------|---------|
| id | INTEGER | PK AUTOINCREMENT | - |
| plot_thread_id | INTEGER | NOT NULL REFERENCES plot_threads(id) | - |
| chapter_id | INTEGER | NOT NULL REFERENCES chapters(id) | - |
| touchpoint_type | TEXT | NOT NULL | 'advance' |
| notes | TEXT | | NULL |
| created_at | TEXT | NOT NULL | datetime('now') |

**UNIQUE constraints:** None — append-only log

---

## Open Questions

1. **`get_subplot_touchpoint_gaps` chapter gap calculation**
   - What we know: The query compares `MAX(stl.chapter_id)` to the current maximum chapter id. Chapter IDs are autoincrement integers (1, 2, 3...) in the seed DB, so the gap is computed by chapter ID delta, not chapter number.
   - What's unclear: Whether `MAX(chapters.id)` is the right comparator, or whether the caller intends "chapters written since touchpoint" relative to the most recently written chapter. The CONTEXT.md says "most recent `subplot_touchpoint_log` entry is more than `threshold_chapters` chapters ago (by chapter_id ordering)" — this confirms chapter_id ordering is correct.
   - Recommendation: Use `SELECT MAX(id) FROM chapters` as the current position. This is consistent with chapter_id-ordered logic throughout the project.

2. **`upsert_plot_thread` — pass-through of canon_status**
   - What we know: The tool signature in CONTEXT.md does not explicitly list `canon_status` as a parameter.
   - What's unclear: Should `canon_status` be a parameter so Claude can set it, or default to "draft" always?
   - Recommendation: Include `canon_status: str | None = None` and default to "draft" in the INSERT if None. Matches `upsert_location` and `upsert_faction` patterns where all non-mandatory columns are optional params.

---

## Sources

### Primary (HIGH confidence)

- Codebase: `src/novel/migrations/016_plot_threads.sql` — exact column names and constraints for plot_threads, chapter_plot_threads, chapter_structural_obligations
- Codebase: `src/novel/migrations/017_arcs_chekhov.sql` — exact column names and constraints for character_arcs, arc_health_log, chekovs_gun_registry, subplot_touchpoint_log
- Codebase: `src/novel/models/plot.py` — PlotThread, ChapterPlotThread, ChapterCharacterArc model fields confirmed
- Codebase: `src/novel/models/arcs.py` — CharacterArc, ArcHealthLog, ChekhovGun, SubplotTouchpoint model fields confirmed
- Codebase: `src/novel/tools/world.py` — upsert pattern (ON CONFLICT(id) DO UPDATE, two-branch none-id / provided-id)
- Codebase: `src/novel/tools/magic.py` — append-only log pattern, read-only tool pattern
- Codebase: `tests/test_magic.py` — per-test MCP session pattern, result.content parsing
- Codebase: `src/novel/db/seed.py` — exact seed data rows for all Phase 5 tables including IDs

### Secondary (MEDIUM confidence)

- `.planning/phases/05-plot-arcs/05-CONTEXT.md` — user decisions on tool signatures, behaviors, and module structure

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all dependencies already installed and verified in codebase
- Architecture: HIGH — all patterns verified directly from existing Phase 3–4 code
- Pitfalls: HIGH — derived from existing STATE.md decisions, actual schema constraints, and direct code inspection
- SQL queries: MEDIUM — designed from schema inspection; `get_subplot_touchpoint_gaps` aggregate query is new and should be integration-tested carefully

**Research date:** 2026-03-07
**Valid until:** Stable — no external dependencies; only changes if migrations are altered
