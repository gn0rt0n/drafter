# Phase 8: Canon, Knowledge & Foreshadowing - Research

**Researched:** 2026-03-07
**Domain:** Python MCP tools — literary tracking (canon, reader state, foreshadowing)
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- Three separate tool files following established domain separation pattern: `src/novel/tools/canon.py`, `src/novel/tools/knowledge.py`, `src/novel/tools/foreshadowing.py`
- Models already exist in `src/novel/models/canon.py` — all 12 model classes ready to use
- `StoryDecision` model is missing from `src/novel/models/canon.py` — must be added in 08-01 before canon tools are written. Schema from migration 021 decisions_log table: `id, decision_type, description, rationale, alternatives (TEXT nullable), session_id (FK nullable), chapter_id (FK nullable), created_at`
- `get_reader_state(chapter_id)` queries `WHERE chapter_id <= X` — returns cumulative reader knowledge UP TO that chapter, not AT that exact chapter; returns list of `ReaderInformationState` records ordered by chapter_id ASC
- `log_foreshadowing` implements upsert behavior (two-branch: None-id INSERT + lastrowid; provided-id ON CONFLICT(id) DO UPDATE) — not append-only
- `log_motif_occurrence` (FORE-08) IS append-only — motif occurrences are historical events, not updateable records
- `get_dramatic_irony_inventory` returns only unresolved entries (`resolved = FALSE`) by default; accepts optional `include_resolved: bool = False` parameter; optional `chapter_id` filter
- `get_continuity_issues` returns only open issues (`is_resolved = FALSE`) by default; optional `severity: str | None = None` filter; optional `include_resolved: bool = False` parameter
- `resolve_continuity_issue(id, resolution_note)` UPDATE sets `is_resolved=True, resolution_note=now, updated_at=now`; returns updated `ContinuityIssue` or `NotFoundResponse`
- `get_canon_facts(domain)` — required `domain` parameter; returns all `CanonFact` rows for that domain ordered by created_at
- `log_canon_fact` — append-only INSERT; `CanonFact` with parent_fact_id support for building fact hierarchies
- `log_decision` — append-only INSERT into decisions_log; returns `StoryDecision`
- `get_decisions(decision_type=None, chapter_id=None)` — optional filters; returns list of `StoryDecision` ordered by created_at DESC
- `get_reader_reveals(chapter_id=None)` — optional chapter_id filter; returns all `ReaderReveal` records
- `upsert_reader_state` — two-branch: None-id INSERT + lastrowid; provided-id ON CONFLICT(id) DO UPDATE on `reader_information_states`
- `get_foreshadowing(status=None, chapter_id=None)` — optional `status` filter (planted/paid_off); optional `chapter_id` filters on `plant_chapter_id`; returns list of `ForeshadowingEntry`
- `get_prophecies()` — returns all `ProphecyEntry` records; no required filter
- `get_motifs()` — returns all `MotifEntry` records
- `get_motif_occurrences(motif_id=None, chapter_id=None)` — optional filters by motif or chapter; returns list of `MotifOccurrence`
- `get_thematic_mirrors()` — returns all `ThematicMirror` records
- `get_opposition_pairs()` — returns all `OppositionPair` records
- Plan split: 08-01 (canon domain), 08-02 (knowledge domain), 08-03 (foreshadowing domain + server.py wiring + all tests)

### Claude's Discretion

- Exact SQL for all queries
- conftest.py extension for canon/knowledge/foreshadowing seed data
- Fixture scope and test helpers
- Whether get_prophecies/get_motifs accept optional filters beyond what's listed
- `get_decisions` ordering and pagination approach

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| CANO-01 | Claude can retrieve canon facts for a named domain (`get_canon_facts`) | SQL: `SELECT * FROM canon_facts WHERE domain = ? ORDER BY created_at` |
| CANO-02 | Claude can log a new canon fact (`log_canon_fact`) | Append-only INSERT; parent_fact_id nullable for hierarchies |
| CANO-03 | Claude can log a story decision (`log_decision`) | Append-only INSERT into decisions_log; requires new `StoryDecision` model |
| CANO-04 | Claude can retrieve the decisions log (`get_decisions`) | SQL with optional decision_type + chapter_id filters, ORDER BY created_at DESC |
| CANO-05 | Claude can log a continuity issue with severity (`log_continuity_issue`) | Append-only INSERT into continuity_issues |
| CANO-06 | Claude can retrieve open continuity issues filtered by severity (`get_continuity_issues`) | SQL: `WHERE is_resolved = FALSE` + optional severity filter |
| CANO-07 | Claude can mark a continuity issue as resolved (`resolve_continuity_issue`) | UPDATE is_resolved=1, updated_at; returns NotFoundResponse if missing |
| KNOW-01 | Claude can retrieve reader information state at a chapter (`get_reader_state`) | SQL: `WHERE chapter_id <= ?` (cumulative) ORDER BY chapter_id ASC |
| KNOW-02 | Claude can retrieve dramatic irony inventory (`get_dramatic_irony_inventory`) | SQL: `WHERE resolved = FALSE` by default; optional include_resolved + chapter_id |
| KNOW-03 | Claude can retrieve planned and actual reveals (`get_reader_reveals`) | SQL: optional chapter_id filter; returns list of ReaderReveal |
| KNOW-04 | Claude can create or update reader information state (`upsert_reader_state`) | Two-branch upsert; table has UNIQUE(chapter_id, domain) — use ON CONFLICT |
| KNOW-05 | Claude can log a dramatic irony entry (`log_dramatic_irony`) | Append-only INSERT into dramatic_irony_inventory |
| FORE-01 | Claude can retrieve foreshadowing entries (`get_foreshadowing`) | SQL: optional status + plant_chapter_id filters |
| FORE-02 | Claude can retrieve prophecy registry entries (`get_prophecies`) | `SELECT * FROM prophecy_registry` — no required filter |
| FORE-03 | Claude can retrieve the motif registry (`get_motifs`) | `SELECT * FROM motif_registry` — no required filter |
| FORE-04 | Claude can retrieve motif occurrences (`get_motif_occurrences`) | Optional motif_id and chapter_id filters |
| FORE-05 | Claude can retrieve thematic mirror pairs (`get_thematic_mirrors`) | `SELECT * FROM thematic_mirrors` — no required filter |
| FORE-06 | Claude can retrieve opposition pairs (`get_opposition_pairs`) | `SELECT * FROM opposition_pairs` — no required filter |
| FORE-07 | Claude can log a foreshadowing entry (`log_foreshadowing`) | Two-branch upsert — allows payoff_chapter_id to be filled later |
| FORE-08 | Claude can log a motif occurrence (`log_motif_occurrence`) | Append-only INSERT — historical events, not updateable |
</phase_requirements>

---

## Summary

Phase 8 adds 20 MCP tools across three literary tracking domains: Canon (7 tools), Knowledge/Reader State (5 tools), and Foreshadowing/Literary Devices (8 tools). The implementation is a pure extension of the established Phase 3–7 tool patterns. No new libraries, no new DB schema, no new server infrastructure patterns are needed — the entire phase reuses `get_connection()`, `check_gate()`, the `register(mcp)` function pattern, and the existing error contract.

The most structurally important pre-condition is adding the missing `StoryDecision` model to `src/novel/models/canon.py` in 08-01 before canon tools are written. All other models are confirmed present in the file (verified by direct read). The schema for all 12+ tables in this phase is confirmed in `021_literary_publishing.sql`. The `gate_ready` seed already populates all Phase 8 tables, making test setup straightforward — use the same session-scoped `certified_gate` autouse fixture pattern from Phase 7.

One schema subtlety matters: `reader_information_states` has a `UNIQUE(chapter_id, domain)` constraint, making `upsert_reader_state` the only Knowledge tool that uses ON CONFLICT — specifically `ON CONFLICT(chapter_id, domain) DO UPDATE` (not by id). `log_foreshadowing` uses the two-branch upsert on `id` (not a unique constraint pair). All other write tools in this phase are append-only INSERTs.

**Primary recommendation:** Implement 08-01 → 08-02 → 08-03 in strict sequence. Add `StoryDecision` model first in 08-01 before touching any tool file. Wire all three modules into server.py and write all tests in the final plan.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `mcp.server.fastmcp` | bundled with `mcp>=1.26.0` | MCP server, `@mcp.tool()` decorator, FastMCP instance | Project-mandated — not standalone fastmcp PyPI |
| `aiosqlite` | `>=0.17.0` | Async SQLite — all tool DB access via `get_connection()` | Established Phase 3+ pattern |
| `pydantic` | `>=2.11` | Model classes for all return types | All domain models are Pydantic v2 BaseModel |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `novel.mcp.db.get_connection` | internal | Async context manager — WAL + FK pragmas | Every tool handler |
| `novel.mcp.gate.check_gate` | internal | Gate enforcement — must be first call in every tool | Every tool handler |
| `novel.models.shared` | internal | `NotFoundResponse`, `GateViolation`, `ValidationFailure` | Error contract |
| `novel.models.canon` | internal | All 12 domain models + `StoryDecision` (to be added) | Import at top of each tool file |

### Alternatives Considered

None — stack is fully locked by project decisions from Phases 3–7.

**Installation:** No new packages required. All dependencies already present.

---

## Architecture Patterns

### Recommended Project Structure

```
src/novel/
├── models/
│   └── canon.py          # ADD StoryDecision model here (08-01)
├── tools/
│   ├── canon.py          # NEW — 7 tools (08-01)
│   ├── knowledge.py      # NEW — 5 tools (08-02)
│   └── foreshadowing.py  # NEW — 8 tools (08-03)
└── mcp/
    └── server.py         # ADD 3 import+register lines (08-03)

tests/
├── test_canon.py         # NEW — canon tool tests (08-03)
├── test_knowledge.py     # NEW — knowledge tool tests (08-03)
└── test_foreshadowing.py # NEW — foreshadowing tool tests (08-03)
```

### Pattern 1: Register Function with Local Tool Definitions

Every tool module follows this exact structure — no variation:

```python
# Source: established pattern from src/novel/tools/session.py, timeline.py
import logging
from mcp.server.fastmcp import FastMCP
from novel.mcp.db import get_connection
from novel.mcp.gate import check_gate
from novel.models.canon import CanonFact, ContinuityIssue, StoryDecision
from novel.models.shared import GateViolation, NotFoundResponse

logger = logging.getLogger(__name__)


def register(mcp: FastMCP) -> None:
    """Register all N canon domain tools with the given FastMCP instance."""

    @mcp.tool()
    async def get_canon_facts(domain: str) -> list[CanonFact] | GateViolation:
        """..."""
        async with get_connection() as conn:
            violation = await check_gate(conn)
            if violation:
                return violation
            rows = await conn.execute_fetchall(
                "SELECT * FROM canon_facts WHERE domain = ? ORDER BY created_at",
                (domain,),
            )
            return [CanonFact(**dict(r)) for r in rows]
```

### Pattern 2: Append-Only INSERT

Used for log/audit tools where rows are never updated. Returns the newly created row via `cursor.lastrowid`:

```python
# Source: established pattern from src/novel/tools/session.py (log_agent_run)
@mcp.tool()
async def log_canon_fact(
    fact: str,
    domain: str = "general",
    source_chapter_id: int | None = None,
    source_event_id: int | None = None,
    parent_fact_id: int | None = None,
    certainty_level: str = "established",
    canon_status: str = "approved",
    notes: str | None = None,
) -> CanonFact | GateViolation:
    async with get_connection() as conn:
        violation = await check_gate(conn)
        if violation:
            return violation
        cursor = await conn.execute(
            "INSERT INTO canon_facts "
            "(domain, fact, source_chapter_id, source_event_id, parent_fact_id, "
            "certainty_level, canon_status, notes) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (domain, fact, source_chapter_id, source_event_id, parent_fact_id,
             certainty_level, canon_status, notes),
        )
        new_id = cursor.lastrowid
        await conn.commit()
        rows = await conn.execute_fetchall(
            "SELECT * FROM canon_facts WHERE id = ?", (new_id,)
        )
        return CanonFact(**dict(rows[0]))
```

### Pattern 3: Two-Branch Upsert

Used for `log_foreshadowing` (id-based), `upsert_reader_state` (unique constraint-based). Two variants:

**Id-based upsert** (foreshadowing_registry has no UNIQUE beyond PK):

```python
# Source: established pattern from src/novel/tools/timeline.py (upsert_event)
@mcp.tool()
async def log_foreshadowing(
    description: str,
    plant_chapter_id: int,
    foreshadowing_id: int | None = None,
    plant_scene_id: int | None = None,
    payoff_chapter_id: int | None = None,
    payoff_scene_id: int | None = None,
    foreshadowing_type: str = "direct",
    status: str = "planted",
    notes: str | None = None,
) -> ForeshadowingEntry | GateViolation:
    async with get_connection() as conn:
        violation = await check_gate(conn)
        if violation:
            return violation
        if foreshadowing_id is None:
            cursor = await conn.execute(
                "INSERT INTO foreshadowing_registry "
                "(description, plant_chapter_id, plant_scene_id, payoff_chapter_id, "
                "payoff_scene_id, foreshadowing_type, status, notes) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (description, plant_chapter_id, plant_scene_id, payoff_chapter_id,
                 payoff_scene_id, foreshadowing_type, status, notes),
            )
            new_id = cursor.lastrowid
            await conn.commit()
        else:
            await conn.execute(
                "INSERT INTO foreshadowing_registry "
                "(id, description, plant_chapter_id, plant_scene_id, payoff_chapter_id, "
                "payoff_scene_id, foreshadowing_type, status, notes) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) "
                "ON CONFLICT(id) DO UPDATE SET "
                "description=excluded.description, plant_chapter_id=excluded.plant_chapter_id, "
                "plant_scene_id=excluded.plant_scene_id, payoff_chapter_id=excluded.payoff_chapter_id, "
                "payoff_scene_id=excluded.payoff_scene_id, foreshadowing_type=excluded.foreshadowing_type, "
                "status=excluded.status, notes=excluded.notes, updated_at=datetime('now')",
                (foreshadowing_id, description, plant_chapter_id, plant_scene_id,
                 payoff_chapter_id, payoff_scene_id, foreshadowing_type, status, notes),
            )
            new_id = foreshadowing_id
            await conn.commit()
        rows = await conn.execute_fetchall(
            "SELECT * FROM foreshadowing_registry WHERE id = ?", (new_id,)
        )
        return ForeshadowingEntry(**dict(rows[0]))
```

**UNIQUE-constraint upsert** (`reader_information_states` has UNIQUE(chapter_id, domain)):

```python
# Source: established pattern from src/novel/tools/timeline.py (upsert_pov_position)
@mcp.tool()
async def upsert_reader_state(
    chapter_id: int,
    domain: str,
    information: str,
    reader_state_id: int | None = None,
    revealed_how: str | None = None,
    notes: str | None = None,
) -> ReaderInformationState | GateViolation:
    async with get_connection() as conn:
        violation = await check_gate(conn)
        if violation:
            return violation
        if reader_state_id is None:
            cursor = await conn.execute(
                "INSERT INTO reader_information_states "
                "(chapter_id, domain, information, revealed_how, notes) "
                "VALUES (?, ?, ?, ?, ?) "
                "ON CONFLICT(chapter_id, domain) DO UPDATE SET "
                "information=excluded.information, revealed_how=excluded.revealed_how, "
                "notes=excluded.notes",
                (chapter_id, domain, information, revealed_how, notes),
            )
            # After ON CONFLICT DO UPDATE, lastrowid is the existing row's id
            new_id = cursor.lastrowid
            await conn.commit()
        else:
            await conn.execute(
                "INSERT INTO reader_information_states "
                "(id, chapter_id, domain, information, revealed_how, notes) "
                "VALUES (?, ?, ?, ?, ?, ?) "
                "ON CONFLICT(id) DO UPDATE SET "
                "information=excluded.information, revealed_how=excluded.revealed_how, "
                "notes=excluded.notes",
                (reader_state_id, chapter_id, domain, information, revealed_how, notes),
            )
            new_id = reader_state_id
            await conn.commit()
        rows = await conn.execute_fetchall(
            "SELECT * FROM reader_information_states WHERE id = ?", (new_id,)
        )
        return ReaderInformationState(**dict(rows[0]))
```

### Pattern 4: Filtered List Query

Dynamically build WHERE clause from optional parameters — established pattern from `list_events`:

```python
# Source: established pattern from src/novel/tools/timeline.py (list_events)
@mcp.tool()
async def get_continuity_issues(
    severity: str | None = None,
    include_resolved: bool = False,
) -> list[ContinuityIssue] | GateViolation:
    async with get_connection() as conn:
        violation = await check_gate(conn)
        if violation:
            return violation
        conditions: list[str] = []
        params: list = []
        if not include_resolved:
            conditions.append("is_resolved = FALSE")
        if severity is not None:
            conditions.append("severity = ?")
            params.append(severity)
        sql = "SELECT * FROM continuity_issues"
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY created_at ASC"
        rows = await conn.execute_fetchall(sql, params)
        return [ContinuityIssue(**dict(r)) for r in rows]
```

### Pattern 5: UPDATE with NotFoundResponse

For resolve-style tools that must confirm the row exists:

```python
# Source: established pattern from src/novel/tools/session.py (answer_open_question)
@mcp.tool()
async def resolve_continuity_issue(
    issue_id: int,
    resolution_note: str,
) -> ContinuityIssue | NotFoundResponse | GateViolation:
    async with get_connection() as conn:
        violation = await check_gate(conn)
        if violation:
            return violation
        await conn.execute(
            "UPDATE continuity_issues SET "
            "is_resolved = 1, resolution_note = ?, updated_at = datetime('now') "
            "WHERE id = ?",
            (resolution_note, issue_id),
        )
        await conn.commit()
        rows = await conn.execute_fetchall(
            "SELECT * FROM continuity_issues WHERE id = ?", (issue_id,)
        )
        if not rows:
            return NotFoundResponse(
                not_found_message=f"Continuity issue {issue_id} not found"
            )
        return ContinuityIssue(**dict(rows[0]))
```

### Pattern 6: Cumulative State Query (get_reader_state)

This is the only tool in Phase 8 with a range-based semantics — `<=` not `=`:

```python
@mcp.tool()
async def get_reader_state(
    chapter_id: int,
) -> list[ReaderInformationState] | GateViolation:
    async with get_connection() as conn:
        violation = await check_gate(conn)
        if violation:
            return violation
        rows = await conn.execute_fetchall(
            "SELECT * FROM reader_information_states "
            "WHERE chapter_id <= ? ORDER BY chapter_id ASC",
            (chapter_id,),
        )
        return [ReaderInformationState(**dict(r)) for r in rows]
```

### Pattern 7: StoryDecision Model (to be added in 08-01)

The `decisions_log` table schema from migration 021:

```python
# Add to src/novel/models/canon.py — migration 021 ground truth
class StoryDecision(BaseModel):
    """Represents a row in the decisions_log table (migration 021)."""

    id: int | None = None
    decision_type: str = "plot"
    description: str
    rationale: str | None = None
    alternatives: str | None = None
    session_id: int | None = None
    chapter_id: int | None = None
    created_at: str | None = None
```

### Pattern 8: Test File Structure

All tests go in a single wave in 08-03. Each test file uses the gate_ready seed + session-scoped certified_gate autouse fixture:

```python
# Source: established pattern from tests/test_session.py, test_timeline.py
import json
import os
import sqlite3
import pytest
from mcp.shared.memory import create_connected_server_and_client_session
from novel.db.migrations import apply_migrations
from novel.db.seed import load_seed_profile
from novel.mcp.server import mcp


@pytest.fixture(scope="session")
def test_db_path(tmp_path_factory):
    db_file = tmp_path_factory.mktemp("canon_db") / "test_canon.db"
    conn = sqlite3.connect(str(db_file))
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA journal_mode=WAL")
    apply_migrations(conn)
    load_seed_profile(conn, "gate_ready")
    conn.commit()
    conn.close()
    return str(db_file)


@pytest.fixture(scope="session", autouse=True)
def certified_gate(test_db_path):
    conn = sqlite3.connect(test_db_path)
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("UPDATE gate_checklist_items SET is_passing=1, missing_count=0")
    cur = conn.execute("SELECT COUNT(*) FROM architecture_gate")
    count = cur.fetchone()[0]
    if count == 0:
        conn.execute(
            "INSERT INTO architecture_gate (is_certified, certified_by, certified_at) "
            "VALUES (1, 'test-suite', datetime('now'))"
        )
    else:
        conn.execute(
            "UPDATE architecture_gate SET is_certified=1, certified_by='test-suite', "
            "certified_at=datetime('now') WHERE id=1"
        )
    conn.commit()
    conn.close()


async def _call_tool(db_path: str, tool_name: str, args: dict):
    os.environ["NOVEL_DB_PATH"] = db_path
    async with create_connected_server_and_client_session(mcp) as session:
        return await session.call_tool(tool_name, args)
```

### Anti-Patterns to Avoid

- **print() anywhere in tool files:** Corrupts stdio MCP protocol — use `logging.getLogger(__name__)` only
- **Skipping check_gate():** Every tool must call `check_gate(conn)` as its first DB action — even read-only tools
- **Using INSERT OR REPLACE instead of ON CONFLICT DO UPDATE:** INSERT OR REPLACE deletes then reinserts, breaking FK children — always use ON CONFLICT for tables with FK children
- **Querying reader_state with `=` instead of `<=`:** The cumulative semantics are a locked decision; `WHERE chapter_id = X` would break the reader knowledge model
- **Using standalone fastmcp PyPI package:** Only bundled `mcp.server.fastmcp` — packages have diverged
- **Entering MCP session in fixtures:** anyio cancel scope incompatible with pytest fixture lifecycle; always enter session per-test inside `_call_tool` helper

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Async SQLite access | Custom connection pool | `novel.mcp.db.get_connection()` | WAL + FK pragmas already enforced |
| Gate enforcement | Inline gate SQL | `novel.mcp.gate.check_gate(conn)` | Centralized, tested, consistent error |
| Error types | Custom dicts/exceptions | `NotFoundResponse`, `GateViolation` | MCP contract — planner and verifier check for these fields |
| Test DB setup | Custom migration runner | `apply_migrations()` + `load_seed_profile()` | These are the tested, production paths |
| MCP in-memory test client | Custom test harness | `create_connected_server_and_client_session(mcp)` | Tests the real FastMCP serialization path |
| JSON serialization | `json.dumps()` in tools | aiosqlite.Row + `dict(row)` → `Model(**dict(row))` | Models handle serialization; no JSON columns in Phase 8 tables |

**Key insight:** Phase 8 tables have NO JSON TEXT columns (unlike scenes with `narrative_functions`). All inserts use plain Python values — no `to_db_dict()` calls needed.

---

## Common Pitfalls

### Pitfall 1: Missing StoryDecision Model Causes Import Failure

**What goes wrong:** `canon.py` tools try to return `StoryDecision` but the class doesn't exist yet — `ImportError` at startup
**Why it happens:** `decisions_log` table exists in migration 021 but the model was never added to `models/canon.py`
**How to avoid:** 08-01 must add `StoryDecision` to `models/canon.py` BEFORE writing any tool code. The model is fully derivable from migration SQL (fields: id, decision_type, description, rationale, alternatives, session_id, chapter_id, created_at).
**Warning signs:** Import errors when server starts; mypy type errors if type-checking is run

### Pitfall 2: reader_information_states UNIQUE Constraint Collision

**What goes wrong:** `upsert_reader_state` with `reader_state_id=None` branch uses INSERT + lastrowid — but if a row already exists for (chapter_id, domain), the UNIQUE constraint fires before ON CONFLICT can handle it
**Why it happens:** The None-id branch must include `ON CONFLICT(chapter_id, domain) DO UPDATE` — not a plain INSERT. After ON CONFLICT DO UPDATE fires, `cursor.lastrowid` returns the existing row's id (this is correct SQLite behavior).
**How to avoid:** Both branches of `upsert_reader_state` must use ON CONFLICT — the None-id branch uses `ON CONFLICT(chapter_id, domain)`, the id-branch uses `ON CONFLICT(id)`.
**Warning signs:** IntegrityError on second call with same chapter_id + domain

### Pitfall 3: log_foreshadowing updated_at Column Missing

**What goes wrong:** The ON CONFLICT DO UPDATE branch for `log_foreshadowing` omits `updated_at=datetime('now')` — row appears updated but timestamp stays at INSERT time
**Why it happens:** Easy to copy-paste from other upserts and forget the timestamp update
**How to avoid:** Always include `updated_at=datetime('now')` in every ON CONFLICT DO UPDATE SET clause for tables with updated_at columns (foreshadowing_registry, continuity_issues, canon_facts)
**Warning signs:** Updated rows show stale updated_at timestamps in tests

### Pitfall 4: get_reader_state Using = Instead of <=

**What goes wrong:** `WHERE chapter_id = X` returns only state ADDED at chapter X, not cumulative state through X — breaks the tool's purpose
**Why it happens:** The cumulative semantics (locked decision) are easy to misread as "get state for chapter X"
**How to avoid:** SQL must be `WHERE chapter_id <= ?` — not `WHERE chapter_id = ?`
**Warning signs:** Tests pass for chapter 1 but return empty for chapter 3 when data was inserted at chapters 1 and 2

### Pitfall 5: Test File tmpdir Collision

**What goes wrong:** Three test files (test_canon.py, test_knowledge.py, test_foreshadowing.py) all use session-scoped `test_db_path` fixture — if they share the same tmp directory they may write to the same DB file
**Why it happens:** Each file must use a DIFFERENT `tmp_path_factory.mktemp()` name (e.g., "canon_db", "knowledge_db", "foreshadowing_db")
**How to avoid:** Use distinct mktemp names in each test file. The session.py and timeline.py tests use "session_db" and "timeline_db" respectively — follow that pattern.
**Warning signs:** Tests in one file see data written by another file; ordering-dependent failures

### Pitfall 6: FastMCP List Serialization

**What goes wrong:** Test asserts `json.loads(result.content[0].text)` on a list-returning tool but FastMCP serializes `list[T]` as N separate TextContent blocks
**Why it happens:** Single-object tools use `result.content[0]`; list tools require `[json.loads(c.text) for c in result.content]`. Empty lists produce zero TextContent blocks.
**How to avoid:** Know which tools return single objects vs lists (see table below). For empty lists, `result.content` is empty — `[json.loads(c.text) for c in result.content]` safely returns `[]`.
**Warning signs:** `IndexError: list index out of range` on `result.content[0]` when tool returns empty list

**Phase 8 serialization map:**

| Tool | Returns | Test pattern |
|------|---------|-------------|
| get_canon_facts | list[CanonFact] | `[json.loads(c.text) for c in result.content]` |
| log_canon_fact | CanonFact | `json.loads(result.content[0].text)` |
| log_decision | StoryDecision | `json.loads(result.content[0].text)` |
| get_decisions | list[StoryDecision] | `[json.loads(c.text) for c in result.content]` |
| log_continuity_issue | ContinuityIssue | `json.loads(result.content[0].text)` |
| get_continuity_issues | list[ContinuityIssue] | `[json.loads(c.text) for c in result.content]` |
| resolve_continuity_issue | ContinuityIssue \| NotFoundResponse | `json.loads(result.content[0].text)` |
| get_reader_state | list[ReaderInformationState] | `[json.loads(c.text) for c in result.content]` |
| get_dramatic_irony_inventory | list[DramaticIronyEntry] | `[json.loads(c.text) for c in result.content]` |
| get_reader_reveals | list[ReaderReveal] | `[json.loads(c.text) for c in result.content]` |
| upsert_reader_state | ReaderInformationState | `json.loads(result.content[0].text)` |
| log_dramatic_irony | DramaticIronyEntry | `json.loads(result.content[0].text)` |
| get_foreshadowing | list[ForeshadowingEntry] | `[json.loads(c.text) for c in result.content]` |
| get_prophecies | list[ProphecyEntry] | `[json.loads(c.text) for c in result.content]` |
| get_motifs | list[MotifEntry] | `[json.loads(c.text) for c in result.content]` |
| get_motif_occurrences | list[MotifOccurrence] | `[json.loads(c.text) for c in result.content]` |
| get_thematic_mirrors | list[ThematicMirror] | `[json.loads(c.text) for c in result.content]` |
| get_opposition_pairs | list[OppositionPair] | `[json.loads(c.text) for c in result.content]` |
| log_foreshadowing | ForeshadowingEntry | `json.loads(result.content[0].text)` |
| log_motif_occurrence | MotifOccurrence | `json.loads(result.content[0].text)` |

---

## Code Examples

### Server Wiring (08-03 final step)

```python
# Source: src/novel/mcp/server.py — add after Phase 7 section
from novel.tools import canon, knowledge, foreshadowing

# Register domain tools — Phase 8
canon.register(mcp)
knowledge.register(mcp)
foreshadowing.register(mcp)
```

### get_reader_state (Cumulative Query — KNOW-01)

```python
# Source: CONTEXT.md locked decision
@mcp.tool()
async def get_reader_state(
    chapter_id: int,
) -> list[ReaderInformationState] | GateViolation:
    """Retrieve cumulative reader information state up to (and including) a chapter.

    Returns all reader_information_states rows where chapter_id <= the given
    chapter_id — a complete snapshot of what readers know at any story point.
    Ordered by chapter_id ASC.

    Args:
        chapter_id: Return all reader state entries up to and including this chapter.

    Returns:
        List of ReaderInformationState records (may be empty), or GateViolation
        if gate is not certified.
    """
    async with get_connection() as conn:
        violation = await check_gate(conn)
        if violation:
            return violation
        rows = await conn.execute_fetchall(
            "SELECT * FROM reader_information_states "
            "WHERE chapter_id <= ? ORDER BY chapter_id ASC",
            (chapter_id,),
        )
        return [ReaderInformationState(**dict(r)) for r in rows]
```

### get_dramatic_irony_inventory (Unresolved by Default — KNOW-02)

```python
# Source: CONTEXT.md locked decision
@mcp.tool()
async def get_dramatic_irony_inventory(
    include_resolved: bool = False,
    chapter_id: int | None = None,
) -> list[DramaticIronyEntry] | GateViolation:
    """Retrieve dramatic irony entries (unresolved only by default).

    Args:
        include_resolved: If True, include resolved entries (default False).
        chapter_id: Optional filter to scope entries created at a specific chapter.

    Returns:
        List of DramaticIronyEntry records (may be empty), or GateViolation
        if gate is not certified.
    """
    async with get_connection() as conn:
        violation = await check_gate(conn)
        if violation:
            return violation
        conditions: list[str] = []
        params: list = []
        if not include_resolved:
            conditions.append("resolved = FALSE")
        if chapter_id is not None:
            conditions.append("chapter_id = ?")
            params.append(chapter_id)
        sql = "SELECT * FROM dramatic_irony_inventory"
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY created_at ASC"
        rows = await conn.execute_fetchall(sql, params)
        return [DramaticIronyEntry(**dict(r)) for r in rows]
```

### Seed Data Available for Tests

The `gate_ready` seed (confirmed by reading `src/novel/db/seed.py`) already inserts into ALL Phase 8 tables:

| Table | Seed data present |
|-------|-------------------|
| `canon_facts` | 1 row (domain="world") |
| `continuity_issues` | 1 row (severity="minor", unresolved) |
| `decisions_log` | 1 row (decision_type="plot") |
| `foreshadowing_registry` | 1 row (status="planted") |
| `prophecy_registry` | 1 row (status="active") |
| `motif_registry` | 1 row (name="Dying Embers") |
| `motif_occurrences` | 1 row (linked to motif above) |
| `thematic_mirrors` | 1 row (Aeryn vs Solvann) |
| `opposition_pairs` | 1 row (Order vs Truth) |
| `reader_information_states` | 1 row (chapter_id=1, domain="world") |
| `reader_reveals` | 1 row (chapter_id=2) |
| `dramatic_irony_inventory` | 1 row (chapter_id=1, unresolved) |

Tests can read existing seed data OR create new rows — both approaches work.

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Standalone `fastmcp` PyPI package | Bundled `mcp.server.fastmcp` | Phase 3 decision | Packages diverged; never use PyPI fastmcp |
| Session-level async fixture for MCP | Per-test `_call_tool` helper with async with | Phase 3 discovery | anyio cancel scope incompatible with pytest fixture lifecycle |
| INSERT OR REPLACE | ON CONFLICT DO UPDATE | Phase 3 (relationships) | INSERT OR REPLACE deletes+reinserts, breaking FK children |
| Global `print()` for debugging | `logging.getLogger(__name__)` to stderr | Phase 1 decision | print() corrupts stdio MCP protocol |

---

## Open Questions

1. **`upsert_reader_state` — None-id branch ON CONFLICT behavior for lastrowid**
   - What we know: SQLite `cursor.lastrowid` returns the rowid of the row that was inserted OR the existing row's rowid after ON CONFLICT DO UPDATE (confirmed as correct SQLite behavior in Phase 4 upsert_faction)
   - What's unclear: Whether aiosqlite exposes this consistently for ON CONFLICT DO UPDATE (Phase 4 verified it for ON CONFLICT(name) on factions)
   - Recommendation: Use cursor.lastrowid after ON CONFLICT DO UPDATE — then SELECT back by id. If lastrowid is 0 (shouldn't happen but defensive), SELECT by (chapter_id, domain) as fallback.

2. **`get_decisions` — pagination not specified**
   - What we know: CONTEXT.md says ORDER BY created_at DESC; no LIMIT specified
   - What's unclear: Very large decisions logs could be slow to return all at once
   - Recommendation: Return all rows (no pagination) — consistent with every other list tool in this project. Claude's discretion.

---

## Sources

### Primary (HIGH confidence)

- `src/novel/migrations/021_literary_publishing.sql` — definitive schema for all 12 Phase 8 tables (read directly)
- `src/novel/models/canon.py` — confirmed 12 existing models, confirmed StoryDecision is missing (read directly)
- `src/novel/tools/session.py` — definitive patterns for append-only INSERT, UPDATE with NotFoundResponse, filtered list queries (read directly)
- `src/novel/tools/timeline.py` — definitive patterns for two-branch upsert (id-based and unique-constraint-based), list serialization (read directly)
- `src/novel/db/seed.py` — confirmed gate_ready seed populates all Phase 8 tables (read directly)
- `tests/test_session.py`, `tests/test_timeline.py` — definitive test file structure, certified_gate fixture, _call_tool helper, FastMCP serialization patterns (read directly)
- `.planning/phases/08-canon-knowledge-foreshadowing/08-CONTEXT.md` — locked decisions for all 20 tools (read directly)

### Secondary (MEDIUM confidence)

None required — all findings verified from first-party source code.

### Tertiary (LOW confidence)

None.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — same stack as Phases 3–7, confirmed from source code
- Architecture: HIGH — all patterns exist in production code and tests, verified by direct file read
- Schema: HIGH — read directly from migration 021 SQL file
- Seed data: HIGH — read directly from seed.py, all 12 tables confirmed populated in gate_ready profile
- Pitfalls: HIGH — identified from Phase 3–7 decisions log in STATE.md and actual code inspection

**Research date:** 2026-03-07
**Valid until:** 2026-06-07 (stable — all findings from internal source files, not external libraries)
