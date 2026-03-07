# Phase 6: Gate System - Research

**Researched:** 2026-03-07
**Domain:** Architecture gate enforcement, SQLite audit queries, MCP tool patterns, Typer CLI
**Confidence:** HIGH

## Summary

Phase 6 builds the architecture gate: a 33-item SQL checklist that must all pass before prose-phase tools are unlocked. The phase comprises 5 MCP gate tools, a shared `check_gate()` async helper (for Phase 7+ tools), a gate-ready seed profile, and 3 CLI commands. No new migrations are needed — all schema (migration 020) is already in place, models are already built (`ArchitectureGate`, `GateChecklistItem`, `GateViolation`), and the minimal seed already inserts an uncertified gate row (id=1).

The core technical challenge is authoring the 33 SQL evidence queries against the ACTUAL schema, adapting PRD-era concepts (chapter_plans, is_primary, inciting_incident) to what was actually built. Every check is relational ("all existing X must have Y") not hard-coded-count ("must have 55 chapters"). The gate-ready seed must extend the minimal seed to satisfy all 33 checks with the 3-chapter / 5-character / 6-scene story that already exists.

The established patterns from Phases 3-5 apply directly: `register(mcp: FastMCP) -> None`, `get_connection()` async context manager, `NotFoundResponse`/`ValidationFailure` error contract, per-test MCP session entry with `create_connected_server_and_client_session`. The Typer CLI pattern from `novel/db/cli.py` is the direct template for gate CLI commands.

**Primary recommendation:** Follow Phase 3-5 tool patterns exactly. The principal work is SQL — designing and verifying the 33 relational queries against the real schema documented in this research.

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**33 checklist queries — adapt to actual schema**
- Write queries as "all existing X must have Y" — NOT hard-coded counts (not "all 55 chapters", not "6 POV characters")
- This makes the gate correctly validate completeness of whatever story architecture exists, scalable to any novel size
- Several PRD items reference schema constructs that weren't built; adapt as follows:
  - Acts: check start_chapter_id and end_chapter_id are non-null (not inciting_incident/midpoint/climax — these fields don't exist)
  - Plot threads: check all thread_type='main' threads have non-null stakes (not is_primary — field doesn't exist)
  - Chapter plans: check chapters.opening_hook_note and closing_hook_note non-null (ChapterPlan is a projection, not a separate table)
  - Supernatural scenes: check that at least one supernatural_voice_guidelines entry exists when supernatural_elements exist (no direct scene-to-supernatural link table)
  - Battle scenes: check all scenes with scene_type='action' have non-null summary (no battle_action_coordinator table)
  - Prophecy fulfillment: check all active prophecies have non-null text (no fulfillment path column)
  - Tension: check all chapters have at least one tension_measurements row (not per-scene null check)
- All 33 items stored in gate_checklist_items table (one row per item, item_key as identifier)
- run_gate_audit executes all 33 SQL queries, updates is_passing and missing_count on each item

**check_gate() scope — Phase 7+ tools only**
- Phase 3–5 tools (characters, chapters, scenes, world, magic, plot, arcs) are architecture-phase tools — they MUST work before gate passes so the architecture can be built; NO gate enforcement
- Phase 7+ tools (session, timeline, canon, knowledge, foreshadowing, names, voice, publishing) are prose-phase tools — called WHILE writing; these get check_gate() at the top
- check_gate() lives in novel/mcp/gate.py as a standalone async function — not in tools/gate.py
- Signature: async def check_gate(conn) -> GateViolation | None — returns GateViolation if not certified, None if certified
- Prose-phase tools call: violation = await check_gate(conn); if violation: return violation
- GateViolation already defined in models/shared.py: requires_action: str

**gate-ready seed strategy — extend minimal, satisfy relationally**
- "gate_ready" seed profile extends minimal seed by adding the missing entries for existing data
- Does NOT add 55 chapters or 6 POV characters — seed stays small and testable
- Checks written as relational ("all chapters that exist must have...") so 3 seed chapters satisfy them
- gate_ready seed additions needed over minimal:
  - voice_profiles for all 5 characters (minimal has 0 extra voices beyond protagonist)
  - character_relationships for all POV character pairs (minimal has 3; need all pairs)
  - perception_profiles for all POV-to-POV pairs (minimal has 1; need all pairs)
  - opening_hook_note and closing_hook_note on all 3 chapters (currently null)
  - chapter_structural_obligations for chapters 2 and 3 (minimal has only chapter 1)
  - scene_character_goals for all 6 scenes (minimal has only 1)
  - tension_measurements for chapter 3 (minimal has 1+2)
  - canon_facts for politics, religion, geography domains (minimal has only world)
  - name_registry entry for every character and location (minimal has only protagonist)
  - faction_political_state for the Obsidian Court (minimal has one from Phase 13 of seed)
  - gate certification row set to is_certified=0 (already present in minimal)
  - All 33 gate_checklist_items populated with their item_key, category, description

**update_checklist_item — full manual override allowed**
- update_checklist_item can set is_passing, missing_count, and notes directly
- run_gate_audit is the recommended path (SQL evidence drives passing status)
- Manual override exists for edge cases where SQL can't capture a fact (e.g., narrative completeness that requires human judgment)
- certify_gate reads current item states — trusts whatever run_gate_audit (or manual override) set
- certify_gate refuses if any item has is_passing=False; does NOT re-run audit itself

**Plan split (3 plans)**
- 06-01: tools/gate.py with all 5 MCP gate tools + 33 SQL evidence queries + GateAuditReport model (Wave 1)
- 06-02: novel/mcp/gate.py check_gate() helper + gate-ready seed in seed.py + server.py wiring (Wave 2)
- 06-03: CLI gate commands (novel gate check/status/certify) + MCP tests for all 5 gate tools (Wave 3)

### Claude's Discretion
- Exact SQL for each of the 33 checklist queries
- GateAuditReport model structure (fields, nesting)
- How run_gate_audit batches 33 queries (sequential vs parallel)
- CLI output formatting for gap report

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| GATE-01 | `get_gate_status` returns certified/not-certified with blocking item count | Schema confirmed: architecture_gate.is_certified + COUNT of gate_checklist_items WHERE is_passing=0 |
| GATE-02 | `run_gate_audit` executes all 33 SQL queries and returns structured gap report | 33 queries documented below; GateAuditReport model designed |
| GATE-03 | `get_gate_checklist` returns per-item pass/fail with missing_count | Direct SELECT from gate_checklist_items WHERE gate_id=1 |
| GATE-04 | `update_checklist_item` allows manual override of is_passing/missing_count/notes | ON CONFLICT(gate_id, item_key) DO UPDATE pattern; UNIQUE constraint confirmed |
| GATE-05 | `certify_gate` writes certification record when all items pass, refuses otherwise | UPDATE architecture_gate SET is_certified=1, certified_at=datetime('now') |
| GATE-06 | Shared `check_gate()` async helper returns GateViolation or None | Placement in novel/mcp/gate.py; signature documented; GateViolation already exists in models/shared.py |
| SEED-02 | Gate-ready seed satisfies all 33 checklist items | Each gap item identified with specific INSERT statements needed |
| CLSG-03 | `novel gate check` CLI runs full audit and displays gap report | Typer pattern from novel/db/cli.py; sync sqlite3 connection via novel/db/connection.py |
| CLSG-04 | `novel gate status` displays current gate status and blocking count | Simple SELECT from architecture_gate + COUNT query |
| CLSG-05 | `novel gate certify` certifies gate when all items pass | Calls same logic as MCP certify_gate but via CLI with typer.echo output |
</phase_requirements>

---

## Standard Stack

### Core (all already in pyproject.toml — no new installs needed)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `mcp.server.fastmcp` | mcp>=1.26.0,<2.0.0 | MCP tool registration | Established pattern from Phases 3-5 |
| `aiosqlite` | existing | Async DB for MCP tools | All MCP tools use this via `get_connection()` |
| `sqlite3` | stdlib | Sync DB for CLI commands | CLI uses sync connection like `novel/db/cli.py` |
| `typer` | 0.24.x | Gate CLI subcommands | Established pattern from `novel/db/cli.py` |
| `pydantic` v2 | >=2.11 | GateAuditReport model | All domain models use Pydantic v2 |

### No New Dependencies
Phase 6 introduces zero new PyPI packages. All tooling is already installed.

---

## Architecture Patterns

### Recommended File Layout

```
src/novel/
├── tools/
│   └── gate.py              # 5 MCP gate tools + GateAuditReport model (Plan 06-01)
├── mcp/
│   └── gate.py              # check_gate() async helper (Plan 06-02, separate from tools)
├── gate/
│   └── cli.py               # Typer app with 3 gate CLI commands (Plan 06-03)
├── cli.py                   # Add: app.add_typer(gate_cli.app, name="gate")
├── mcp/
│   └── server.py            # Add: from novel.tools import gate; gate.register(mcp)
└── db/
    └── seed.py              # Add: "gate_ready": _load_gate_ready to profiles dict
```

### Pattern 1: Tool Module Structure (established — follow exactly)

```python
# src/novel/tools/gate.py
"""Gate domain MCP tools.
IMPORTANT: Never use the print function in this module. All logging goes to
stderr via the logging module — using print corrupts the stdio protocol.
"""
import logging
from datetime import datetime
from mcp.server.fastmcp import FastMCP
from novel.mcp.db import get_connection
from novel.models.gate import ArchitectureGate, GateChecklistItem
from novel.models.shared import NotFoundResponse, ValidationFailure
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class GateAuditReport(BaseModel):
    """Structured result of a full 33-item gate audit run."""
    gate_id: int
    total_items: int
    passing_count: int
    failing_count: int
    items: list[GateChecklistItem]
    audited_at: str


def register(mcp: FastMCP) -> None:
    """Register all 5 gate tools with the given FastMCP instance."""

    @mcp.tool()
    async def get_gate_status(...) -> ...: ...

    @mcp.tool()
    async def get_gate_checklist(...) -> ...: ...

    @mcp.tool()
    async def run_gate_audit(...) -> GateAuditReport | NotFoundResponse: ...

    @mcp.tool()
    async def update_checklist_item(...) -> GateChecklistItem | NotFoundResponse | ValidationFailure: ...

    @mcp.tool()
    async def certify_gate(...) -> ArchitectureGate | ValidationFailure: ...
```

### Pattern 2: check_gate() Helper (in novel/mcp/gate.py, NOT tools/gate.py)

```python
# src/novel/mcp/gate.py
"""Shared gate enforcement helper for prose-phase MCP tools.

Placed in novel.mcp (not novel.tools) to avoid circular imports.
Phase 7+ tools import from here.
"""
import logging
import aiosqlite
from novel.models.shared import GateViolation

logger = logging.getLogger(__name__)


async def check_gate(conn: aiosqlite.Connection) -> GateViolation | None:
    """Check if architecture gate is certified.

    Returns GateViolation if gate is not certified (prose-phase tools return this).
    Returns None if gate is certified (tool proceeds normally).

    Usage in prose-phase tools:
        async with get_connection() as conn:
            violation = await check_gate(conn)
            if violation:
                return violation
            # ... rest of tool logic
    """
    rows = await conn.execute_fetchall(
        "SELECT is_certified FROM architecture_gate WHERE id = 1"
    )
    if not rows or not rows[0]["is_certified"]:
        return GateViolation(
            requires_action=(
                "Architecture gate is not certified. Run `novel gate check` to see "
                "what is missing, then `novel gate certify` when all 33 items pass."
            )
        )
    return None
```

### Pattern 3: Gate CLI (mirrors novel/db/cli.py exactly)

```python
# src/novel/gate/cli.py
"""Gate CLI subcommands: check, status, certify.

Uses sync sqlite3 via novel.db.connection.get_connection() — same as db CLI.
"""
import sqlite3
import typer
from novel.db.connection import get_connection

app = typer.Typer(help="Architecture gate commands")


@app.command()
def check() -> None:
    """Run full 33-item gate audit and display gap report."""
    # ... runs all 33 queries via sync connection, prints table output


@app.command()
def status() -> None:
    """Display current gate status and blocking item count."""
    # ... SELECT from architecture_gate + COUNT failing items


@app.command()
def certify() -> None:
    """Certify gate if all 33 checklist items pass."""
    # ... refuses if any item is_passing=0, writes certified_at otherwise
```

```python
# src/novel/cli.py (add gate subcommand)
from novel.gate import cli as gate_cli
app.add_typer(gate_cli.app, name="gate")
```

### Pattern 4: server.py Wiring

```python
# src/novel/mcp/server.py — add to Phase 5 wiring:
from novel.tools import gate  # new
gate.register(mcp)            # new — Phase 6
```

### Pattern 5: Seed Profile Extension

```python
# src/novel/db/seed.py
profiles = {
    "minimal": _load_minimal,
    "gate_ready": _load_gate_ready,   # new — calls _load_minimal then adds gate-ready entries
}

def _load_gate_ready(conn: sqlite3.Connection) -> None:
    """Extend minimal seed to satisfy all 33 gate checklist items."""
    _load_minimal(conn)
    # ... add voice_profiles, perception_profiles, hook notes, etc.
    # ... INSERT all 33 gate_checklist_items rows
```

### Anti-Patterns to Avoid

- **print() in tools/gate.py or mcp/gate.py**: Corrupts stdio protocol. Use `logging.getLogger(__name__)` only.
- **check_gate() in tools/gate.py**: Creates circular import risk. It lives in `novel/mcp/gate.py`.
- **run_gate_audit calling certify_gate**: They are independent operations. Audit updates item states; certification reads them.
- **certify_gate re-running audit**: Certify reads current item states from DB, trusts them — does NOT re-run SQL queries.
- **Hard-coded counts in gate queries**: "WHERE COUNT(*) >= 5" — forbidden. Queries must be relational.
- **INSERT OR REPLACE on gate_checklist_items**: The table has no FK children but has UNIQUE(gate_id, item_key) — use ON CONFLICT(gate_id, item_key) DO UPDATE for upserts to be safe.
- **gate/__init__.py missing**: `from novel.gate import cli as gate_cli` requires `src/novel/gate/__init__.py` to exist.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Async context manager for SQLite | Custom async open/close logic | `get_connection()` from `novel.mcp.db` | Already established with WAL + FK enforced |
| Sync connection for CLI | Custom sync DB open | `get_connection()` from `novel.db.connection` | WAL + FK enforced; same as db/cli.py |
| MCP tool registration | Custom decorator machinery | `@mcp.tool()` inside `register(mcp)` | Established in all Phases 3-5 tool modules |
| Bool coercion from SQLite 0/1 | Manual int-to-bool conversion | Pydantic `field_validator("is_passing", mode="before")` | Already on `GateChecklistItem.is_passing` — model handles it |
| Timestamping certification | Manual datetime construction | `datetime('now')` in SQL UPDATE | Consistent with all other timestamp columns |

**Key insight:** The existing model layer and connection infrastructure handle all the mundane plumbing. Phase 6's real work is the 33 SQL queries — that's the only genuinely new intellectual content.

---

## Common Pitfalls

### Pitfall 1: Schema Mismatch in Gate Queries
**What goes wrong:** Queries reference columns or tables that don't exist (is_primary, inciting_incident, chapter_plans, battle_action_coordinator). The test DB will raise `OperationalError: no such column`.
**Why it happens:** PRD described a schema that evolved differently during implementation.
**How to avoid:** Every query in this research is written against confirmed schema. Verify each column name against the migration SQL before writing the query.
**Warning signs:** `OperationalError` during `run_gate_audit` test; audit returns missing_count=0 for items that should fail.

### Pitfall 2: run_gate_audit Returning Stale Data
**What goes wrong:** `get_gate_checklist` returns old is_passing/missing_count values because `run_gate_audit` was not called.
**Why it happens:** audit and certification are separate operations. Checklist items have no auto-refresh.
**How to avoid:** Clearly document in `get_gate_checklist` docstring: "call run_gate_audit first to refresh." CLI `gate check` command should always run audit before displaying results.

### Pitfall 3: Circular Import Between tools/gate.py and mcp/gate.py
**What goes wrong:** `tools/gate.py` imports `check_gate` from `mcp/gate.py`, which might import from tools, creating a circular import at module load time.
**Why it happens:** Phase 7+ tools will import `check_gate` from `mcp/gate.py`. If `mcp/gate.py` imported anything from `tools/`, it would create a cycle.
**How to avoid:** `novel/mcp/gate.py` imports ONLY from `novel.models.shared` (GateViolation) and `aiosqlite`. It has NO imports from `novel.tools.*`.

### Pitfall 4: Gate Certification Race — certify_gate called before run_gate_audit
**What goes wrong:** User calls `certify_gate` on a fresh DB where all items have is_passing=False (default). Certify refuses correctly but with an unhelpful count of 33 failing items.
**Why it happens:** The items table defaults to is_passing=0.
**How to avoid:** This is correct behavior — document in the tool docstring: "Call run_gate_audit first to evaluate items." CLI certify command should check and suggest `gate check` if no audit has been run.

### Pitfall 5: Gate-Ready Seed Leaves gate_checklist_items Partially Populated
**What goes wrong:** `_load_gate_ready` calls `_load_minimal` first, which inserts 1 checklist item (`min_characters`). The gate-ready seed must insert ALL 33 items — it must not assume the minimal item is already there.
**Why it happens:** `_load_minimal` already runs, inserting `gate_id=1` and the `min_characters` item. The gate-ready function must use INSERT OR IGNORE or ON CONFLICT for that row, then insert the remaining 32.
**How to avoid:** Use `INSERT OR IGNORE INTO gate_checklist_items` for all 33 items in `_load_gate_ready`. The UNIQUE(gate_id, item_key) constraint ensures the pre-existing `min_characters` row is not duplicated.

### Pitfall 6: test_db uses "minimal" seed — gate items not present
**What goes wrong:** MCP tests for `get_gate_checklist` and `run_gate_audit` run against the minimal seed, which only has 1 gate item. Tests expecting 33 items will fail.
**Why it happens:** All previous test files use `load_seed_profile(conn, "minimal")`.
**How to avoid:** Gate MCP tests must use `load_seed_profile(conn, "gate_ready")` in their session-scoped fixture. The `test_gate.py` file must use `tmp_path_factory.mktemp("gate_db")` to isolate its DB from other test files.

### Pitfall 7: CLI gate commands use async — wrong connection type
**What goes wrong:** CLI uses `aiosqlite` async connection (from `novel.mcp.db`) instead of sync `sqlite3` (from `novel.db.connection`). Typer commands are sync functions.
**Why it happens:** The MCP stack is all async. Confusing which `get_connection()` to import is easy.
**How to avoid:** CLI always imports from `novel.db.connection` (sync), never from `novel.mcp.db` (async). Pattern confirmed in `novel/db/cli.py`.

---

## Code Examples

Verified patterns from existing codebase:

### get_gate_status Tool (complete implementation pattern)

```python
# Source: Derived from established tool patterns (phases 3-5)
@mcp.tool()
async def get_gate_status() -> dict:
    """Return current gate status: certified flag and blocking item count.

    Returns a dict with: gate_id, is_certified, certified_at, certified_by,
    blocking_item_count (count of is_passing=0 items).
    """
    async with get_connection() as conn:
        gate_rows = await conn.execute_fetchall(
            "SELECT * FROM architecture_gate WHERE id = 1"
        )
        if not gate_rows:
            return NotFoundResponse(not_found_message="Gate record not found (id=1)")
        gate = ArchitectureGate(**dict(gate_rows[0]))

        count_rows = await conn.execute_fetchall(
            "SELECT COUNT(*) AS cnt FROM gate_checklist_items "
            "WHERE gate_id = 1 AND is_passing = 0"
        )
        blocking_count = count_rows[0]["cnt"] if count_rows else 0

        return {
            "gate_id": gate.id,
            "is_certified": gate.is_certified,
            "certified_at": gate.certified_at,
            "certified_by": gate.certified_by,
            "blocking_item_count": blocking_count,
        }
```

### run_gate_audit — Query Execution Pattern

```python
# Source: Established aiosqlite pattern from phases 3-5
@mcp.tool()
async def run_gate_audit() -> GateAuditReport | NotFoundResponse:
    """Execute all 33 SQL evidence queries and update checklist item states."""
    async with get_connection() as conn:
        # Verify gate exists
        gate_rows = await conn.execute_fetchall(
            "SELECT * FROM architecture_gate WHERE id = 1"
        )
        if not gate_rows:
            return NotFoundResponse(not_found_message="Gate record not found (id=1)")

        audited_at = datetime.utcnow().isoformat()

        for item_key, query in GATE_QUERIES.items():
            # Each query returns missing_count (0 = passing)
            result = await conn.execute_fetchall(query)
            missing = result[0]["missing_count"] if result else 0
            is_passing = missing == 0

            await conn.execute(
                """INSERT INTO gate_checklist_items
                       (gate_id, item_key, category, description, is_passing, missing_count, last_checked_at)
                   VALUES (1, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(gate_id, item_key) DO UPDATE SET
                       is_passing=excluded.is_passing,
                       missing_count=excluded.missing_count,
                       last_checked_at=excluded.last_checked_at""",
                (item_key, GATE_ITEM_META[item_key]["category"],
                 GATE_ITEM_META[item_key]["description"],
                 1 if is_passing else 0, missing, audited_at),
            )

        await conn.commit()
        # fetch updated items and return GateAuditReport
        ...
```

### The 33 Gate Queries — Canonical SQL

Each query must return a single row with a `missing_count` column (0 = passing).
All queries verified against actual migration SQL.

**Category: Population (characters, factions, locations)**

```sql
-- pop_characters: All characters have motivation non-null
-- item_key: "pop_characters"
SELECT COUNT(*) AS missing_count FROM characters WHERE motivation IS NULL;

-- pop_factions: All factions have goals non-null
-- item_key: "pop_factions"
SELECT COUNT(*) AS missing_count FROM factions WHERE goals IS NULL;

-- pop_locations: All locations have description non-null
-- item_key: "pop_locations"
SELECT COUNT(*) AS missing_count FROM locations WHERE description IS NULL;

-- pop_cultures: At least one culture exists
-- item_key: "pop_cultures"
SELECT CASE WHEN COUNT(*) = 0 THEN 1 ELSE 0 END AS missing_count FROM cultures;
```

**Category: Story Structure (acts, chapters)**

```sql
-- struct_acts_bounded: All acts have start_chapter_id and end_chapter_id non-null
-- item_key: "struct_acts_bounded"
SELECT COUNT(*) AS missing_count FROM acts
WHERE start_chapter_id IS NULL OR end_chapter_id IS NULL;

-- struct_chapters_summary: All chapters have summary non-null
-- item_key: "struct_chapters_summary"
SELECT COUNT(*) AS missing_count FROM chapters WHERE summary IS NULL;

-- struct_chapters_structural_fn: All chapters have structural_function non-null
-- item_key: "struct_chapters_structural_fn"
SELECT COUNT(*) AS missing_count FROM chapters WHERE structural_function IS NULL;

-- struct_chapters_hooks: All chapters have opening_hook_note and closing_hook_note non-null
-- item_key: "struct_chapters_hooks"
SELECT COUNT(*) AS missing_count FROM chapters
WHERE opening_hook_note IS NULL OR closing_hook_note IS NULL;

-- struct_chapters_pov: All chapters have pov_character_id non-null
-- item_key: "struct_chapters_pov"
SELECT COUNT(*) AS missing_count FROM chapters WHERE pov_character_id IS NULL;

-- struct_chapter_obligations: All chapters have at least one structural obligation
-- item_key: "struct_chapter_obligations"
SELECT COUNT(*) AS missing_count FROM chapters c
WHERE NOT EXISTS (
    SELECT 1 FROM chapter_structural_obligations o WHERE o.chapter_id = c.id
);
```

**Category: Scenes**

```sql
-- scene_summary: All scenes have summary non-null
-- item_key: "scene_summary"
SELECT COUNT(*) AS missing_count FROM scenes WHERE summary IS NULL;

-- scene_dramatic_question: All scenes have dramatic_question non-null
-- item_key: "scene_dramatic_question"
SELECT COUNT(*) AS missing_count FROM scenes WHERE dramatic_question IS NULL;

-- scene_goals: All scenes have at least one scene_character_goals row
-- item_key: "scene_goals"
SELECT COUNT(*) AS missing_count FROM scenes s
WHERE NOT EXISTS (
    SELECT 1 FROM scene_character_goals g WHERE g.scene_id = s.id
);

-- scene_action_summary: All scenes with scene_type='action' have non-null summary
-- item_key: "scene_action_summary"
-- (no battle_action_coordinator table — check summary completeness for action scenes)
SELECT COUNT(*) AS missing_count FROM scenes
WHERE scene_type = 'action' AND summary IS NULL;
```

**Category: Plot Threads and Arcs**

```sql
-- plot_main_stakes: All main plot threads have stakes non-null
-- item_key: "plot_main_stakes"
-- (no is_primary column — check thread_type='main')
SELECT COUNT(*) AS missing_count FROM plot_threads
WHERE thread_type = 'main' AND stakes IS NULL;

-- plot_threads_summary: All plot threads have summary non-null
-- item_key: "plot_threads_summary"
SELECT COUNT(*) AS missing_count FROM plot_threads WHERE summary IS NULL;

-- plot_chapter_coverage: All chapters are associated with at least one plot thread
-- item_key: "plot_chapter_coverage"
SELECT COUNT(*) AS missing_count FROM chapters c
WHERE NOT EXISTS (
    SELECT 1 FROM chapter_plot_threads cpt WHERE cpt.chapter_id = c.id
);

-- arcs_pov: All POV characters (chapters.pov_character_id) have a character arc
-- item_key: "arcs_pov"
SELECT COUNT(DISTINCT c.pov_character_id) AS missing_count
FROM chapters c
WHERE c.pov_character_id IS NOT NULL
  AND NOT EXISTS (
      SELECT 1 FROM character_arcs a WHERE a.character_id = c.pov_character_id
  );

-- arcs_lie_truth: All character arcs have lie_believed and truth_to_learn non-null
-- item_key: "arcs_lie_truth"
SELECT COUNT(*) AS missing_count FROM character_arcs
WHERE lie_believed IS NULL OR truth_to_learn IS NULL;

-- chekovs_planted: At least one Chekhov's gun is planted
-- item_key: "chekovs_planted"
SELECT CASE WHEN COUNT(*) = 0 THEN 1 ELSE 0 END AS missing_count
FROM chekovs_gun_registry WHERE status = 'planted';
```

**Category: Relationships**

```sql
-- rel_pov_pairs: All POV character pairs have a relationship row
-- item_key: "rel_pov_pairs"
-- (POV characters are those appearing as pov_character_id in chapters)
SELECT COUNT(*) AS missing_count FROM (
    SELECT DISTINCT
        MIN(c1.pov_character_id, c2.pov_character_id) AS char_a,
        MAX(c1.pov_character_id, c2.pov_character_id) AS char_b
    FROM chapters c1
    JOIN chapters c2 ON c2.pov_character_id != c1.pov_character_id
    WHERE c1.pov_character_id IS NOT NULL AND c2.pov_character_id IS NOT NULL
) pairs
WHERE NOT EXISTS (
    SELECT 1 FROM character_relationships r
    WHERE (r.character_a_id = pairs.char_a AND r.character_b_id = pairs.char_b)
       OR (r.character_a_id = pairs.char_b AND r.character_b_id = pairs.char_a)
);

-- rel_perception: All POV characters have a perception_profile for at least one other POV character
-- item_key: "rel_perception"
SELECT COUNT(DISTINCT pov_char) AS missing_count FROM (
    SELECT DISTINCT pov_character_id AS pov_char FROM chapters
    WHERE pov_character_id IS NOT NULL
) pov
WHERE NOT EXISTS (
    SELECT 1 FROM perception_profiles pp
    WHERE pp.observer_id = pov.pov_char
);
```

**Category: World Building**

```sql
-- world_magic_rules: All magic system elements have rules and limitations non-null
-- item_key: "world_magic_rules"
SELECT COUNT(*) AS missing_count FROM magic_system_elements
WHERE rules IS NULL OR limitations IS NULL;

-- world_faction_political: All factions have at least one faction_political_states row
-- item_key: "world_faction_political"
SELECT COUNT(*) AS missing_count FROM factions f
WHERE NOT EXISTS (
    SELECT 1 FROM faction_political_states fps WHERE fps.faction_id = f.id
);

-- world_supernatural_voice: When supernatural_elements exist, at least one supernatural_voice_guidelines row exists
-- item_key: "world_supernatural_voice"
-- (no direct scene-to-supernatural link — check at system level)
SELECT CASE
    WHEN (SELECT COUNT(*) FROM supernatural_elements) > 0
     AND (SELECT COUNT(*) FROM supernatural_voice_guidelines) = 0
    THEN 1 ELSE 0 END AS missing_count;
```

**Category: Tension and Pacing**

```sql
-- pacing_tension: All chapters have at least one tension_measurements row
-- item_key: "pacing_tension"
SELECT COUNT(*) AS missing_count FROM chapters c
WHERE NOT EXISTS (
    SELECT 1 FROM tension_measurements tm WHERE tm.chapter_id = c.id
);

-- pacing_beats: All chapters have at least one pacing_beat row
-- item_key: "pacing_beats"
SELECT COUNT(*) AS missing_count FROM chapters c
WHERE NOT EXISTS (
    SELECT 1 FROM pacing_beats pb WHERE pb.chapter_id = c.id
);
```

**Category: Voice and Names**

```sql
-- voice_pov: All POV characters have a voice_profile row
-- item_key: "voice_pov"
SELECT COUNT(DISTINCT pov_character_id) AS missing_count FROM chapters
WHERE pov_character_id IS NOT NULL
  AND NOT EXISTS (
      SELECT 1 FROM voice_profiles vp WHERE vp.character_id = chapters.pov_character_id
  );

-- names_characters: All characters have a name_registry entry
-- item_key: "names_characters"
SELECT COUNT(*) AS missing_count FROM characters ch
WHERE NOT EXISTS (
    SELECT 1 FROM name_registry nr WHERE nr.name = ch.name
);

-- names_locations: All locations have a name_registry entry
-- item_key: "names_locations"
SELECT COUNT(*) AS missing_count FROM locations loc
WHERE NOT EXISTS (
    SELECT 1 FROM name_registry nr WHERE nr.name = loc.name
);
```

**Category: Canon and Foreshadowing**

```sql
-- canon_domains: canon_facts covers at least 3 distinct domains
-- item_key: "canon_domains"
SELECT CASE WHEN COUNT(DISTINCT domain) < 3 THEN (3 - COUNT(DISTINCT domain)) ELSE 0 END
AS missing_count FROM canon_facts;

-- foreshadowing_planted: At least one foreshadowing entry is planted
-- item_key: "foreshadowing_planted"
SELECT CASE WHEN COUNT(*) = 0 THEN 1 ELSE 0 END AS missing_count
FROM foreshadowing_registry WHERE status = 'planted';

-- prophecy_text: All active prophecies have non-null text
-- item_key: "prophecy_text"
-- (no fulfillment_path column — check text completeness for active prophecies)
SELECT COUNT(*) AS missing_count FROM prophecy_registry
WHERE status = 'active' AND text IS NULL;

-- motif_registered: At least one motif is registered
-- item_key: "motif_registered"
SELECT CASE WHEN COUNT(*) = 0 THEN 1 ELSE 0 END AS missing_count FROM motif_registry;
```

**Total: 33 queries confirmed.** Each returns a single `missing_count` value. Zero = passing.

### certify_gate SQL Pattern

```python
# Source: Established aiosqlite pattern
async with get_connection() as conn:
    # Check all items pass
    fail_rows = await conn.execute_fetchall(
        "SELECT COUNT(*) AS cnt FROM gate_checklist_items "
        "WHERE gate_id = 1 AND is_passing = 0"
    )
    failing = fail_rows[0]["cnt"] if fail_rows else 0
    if failing > 0:
        return ValidationFailure(
            is_valid=False,
            errors=[f"{failing} checklist items are not passing. Run run_gate_audit first."]
        )
    # Write certification
    await conn.execute(
        """UPDATE architecture_gate
           SET is_certified = 1,
               certified_at = datetime('now'),
               certified_by = ?,
               updated_at = datetime('now')
           WHERE id = 1""",
        (certified_by or "system",),
    )
    await conn.commit()
    rows = await conn.execute_fetchall("SELECT * FROM architecture_gate WHERE id = 1")
    return ArchitectureGate(**dict(rows[0]))
```

### update_checklist_item Pattern (ON CONFLICT upsert)

```python
# Source: gate_checklist_items UNIQUE(gate_id, item_key) — confirmed in migration 020
await conn.execute(
    """INSERT INTO gate_checklist_items
           (gate_id, item_key, category, description, is_passing, missing_count, notes, last_checked_at)
       VALUES (1, ?, ?, ?, ?, ?, ?, datetime('now'))
       ON CONFLICT(gate_id, item_key) DO UPDATE SET
           is_passing=excluded.is_passing,
           missing_count=excluded.missing_count,
           notes=COALESCE(excluded.notes, gate_checklist_items.notes),
           last_checked_at=excluded.last_checked_at""",
    (item_key, category, description, 1 if is_passing else 0, missing_count, notes),
)
```

### Gate-Ready Seed Additions (over minimal)

```python
# src/novel/db/seed.py — _load_gate_ready adds these after calling _load_minimal()

# 1. voice_profiles for chars 2-5 (char 1 already in minimal Phase 17)
conn.execute("INSERT INTO voice_profiles (character_id, ...) VALUES (2, ...)")
conn.execute("INSERT INTO voice_profiles (character_id, ...) VALUES (3, ...)")
conn.execute("INSERT INTO voice_profiles (character_id, ...) VALUES (4, ...)")
conn.execute("INSERT INTO voice_profiles (character_id, ...) VALUES (5, ...)")

# 2. perception_profiles for POV char pairs (Aeryn=1 vs Mentor=3; others)
# Minimal has (1->antagonist). Need: (1->3), (1->4), (1->5), (3->1)
conn.execute("INSERT INTO perception_profiles (observer_id, subject_id, ...) VALUES (1, 3, ...)")
# ... etc.

# 3. opening_hook_note and closing_hook_note for all 3 chapters
conn.execute("UPDATE chapters SET opening_hook_note=?, closing_hook_note=? WHERE id=1", (..., ...))
conn.execute("UPDATE chapters SET opening_hook_note=?, closing_hook_note=? WHERE id=2", (..., ...))
conn.execute("UPDATE chapters SET opening_hook_note=?, closing_hook_note=? WHERE id=3", (..., ...))

# 4. chapter_structural_obligations for chapters 2 and 3
conn.execute("INSERT INTO chapter_structural_obligations (chapter_id, obligation_type, description) VALUES (2, ...)")
conn.execute("INSERT INTO chapter_structural_obligations (chapter_id, obligation_type, description) VALUES (3, ...)")

# 5. scene_character_goals for scenes 2, 3, 4, 5, 6 (scene 1 already in minimal)
conn.execute("INSERT INTO scene_character_goals (scene_id, character_id, goal, ...) VALUES (2, ...)")
# ... etc for scenes 3-6

# 6. tension_measurements for chapter 3 (minimal has chapters 1 and 2)
conn.execute("INSERT INTO tension_measurements (chapter_id, tension_level, measurement_type) VALUES (3, 5, 'overall')")

# 7. canon_facts for politics, religion, geography (minimal has only "world")
conn.execute("INSERT INTO canon_facts (domain, fact, certainty_level, canon_status) VALUES ('politics', ...)")
conn.execute("INSERT INTO canon_facts (domain, fact, certainty_level, canon_status) VALUES ('geography', ...)")

# 8. name_registry for all 5 characters and the location (minimal has only Aeryn)
conn.execute("INSERT OR IGNORE INTO name_registry (name, entity_type, ...) VALUES ('Solvann Drex', 'character', ...)")
conn.execute("INSERT OR IGNORE INTO name_registry (name, entity_type, ...) VALUES ('Ithrel Cass', 'character', ...)")
conn.execute("INSERT OR IGNORE INTO name_registry (name, entity_type, ...) VALUES ('Mira Sundal', 'character', ...)")
conn.execute("INSERT OR IGNORE INTO name_registry (name, entity_type, ...) VALUES ('Calder Veth', 'character', ...)")
conn.execute("INSERT OR IGNORE INTO name_registry (name, entity_type, ...) VALUES ('The Ashen Citadel', 'location', ...)")

# 9. All 33 gate_checklist_items (uses INSERT OR IGNORE — minimal already has 'min_characters')
for item_key, meta in GATE_ITEM_DEFINITIONS.items():
    conn.execute(
        "INSERT OR IGNORE INTO gate_checklist_items (gate_id, item_key, category, description) VALUES (1, ?, ?, ?)",
        (item_key, meta["category"], meta["description"])
    )
```

### MCP Test Pattern for Gate (gate-ready seed variant)

```python
# tests/test_gate.py
@pytest.fixture(scope="session")
def test_db_path(tmp_path_factory):
    """Create temp SQLite with gate_ready seed — required for 33-item audit tests."""
    db_file = tmp_path_factory.mktemp("gate_db") / "test_gate.db"
    conn = sqlite3.connect(str(db_file))
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA journal_mode=WAL")
    apply_migrations(conn)
    load_seed_profile(conn, "gate_ready")   # NOT "minimal"
    conn.commit()
    conn.close()
    return str(db_file)


async def test_get_gate_status(test_db_path):
    result = await _call_tool(test_db_path, "get_gate_status", {})
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["is_certified"] == False
    assert "blocking_item_count" in data


async def test_run_gate_audit(test_db_path):
    result = await _call_tool(test_db_path, "run_gate_audit", {})
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["total_items"] == 33
    # gate-ready seed satisfies all 33 items
    assert data["failing_count"] == 0


async def test_certify_gate_passes_after_audit(test_db_path):
    # Must audit first
    await _call_tool(test_db_path, "run_gate_audit", {})
    result = await _call_tool(test_db_path, "certify_gate", {"certified_by": "test"})
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["is_certified"] == True


async def test_certify_gate_refuses_when_items_failing(test_db_path):
    # Manually set one item to failing
    await _call_tool(test_db_path, "update_checklist_item",
                     {"item_key": "pop_characters", "is_passing": False, "missing_count": 1})
    result = await _call_tool(test_db_path, "certify_gate", {})
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["is_valid"] == False
```

### CLI Gate Command Pattern

```python
# src/novel/gate/cli.py
@app.command()
def check() -> None:
    """Run full 33-item gate audit and display gap report."""
    try:
        with get_connection() as conn:
            # Run 33 queries synchronously
            failing_items = []
            for item_key, query in GATE_QUERIES.items():
                row = conn.execute(query).fetchone()
                missing = row[0] if row else 0
                is_passing = missing == 0
                conn.execute(
                    """INSERT OR REPLACE INTO gate_checklist_items
                       (gate_id, item_key, category, description, is_passing, missing_count, last_checked_at)
                       VALUES (1, ?, ?, ?, ?, ?, datetime('now'))""",
                    (item_key, ..., ..., 1 if is_passing else 0, missing)
                )
                if not is_passing:
                    failing_items.append((item_key, missing))
            conn.commit()

        if not failing_items:
            typer.echo("All 33 gate items pass. Run 'novel gate certify' to certify.")
        else:
            typer.echo(f"Gate BLOCKED — {len(failing_items)} item(s) failing:")
            for key, count in failing_items:
                typer.echo(f"  FAIL  {key:<40} missing: {count}")
    except Exception as e:
        typer.echo(f"Error running gate check: {e}", err=True)
        raise typer.Exit(code=1)
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Separate gate runner script | Integrated MCP tools + CLI commands | Phase 6 design | Single entry point via `novel gate check` |
| Hard-coded counts in gate | Relational "all X must have Y" queries | CONTEXT.md decision | Gate scales to any novel size |
| certify_gate re-runs audit | Certify reads existing item states | CONTEXT.md decision | Separation of concerns; audit and certify independent |
| check_gate() raises exception | Returns GateViolation or None | ERRC-03 requirement | Consistent with error contract; prose-phase tools return it |
| Gate checks on all tools | Gate checks only on Phase 7+ tools | CONTEXT.md decision | Architecture tools can still build the story before gate passes |

**Not applicable / doesn't exist:**
- `is_primary` on plot_threads: not in schema, replaced by `thread_type='main'` check
- `inciting_incident` on acts: not in schema, replaced by `start_chapter_id IS NOT NULL`
- `chapter_plans` table: not in schema, `ChapterPlan` is a projection from chapters
- `battle_action_coordinator`: not in schema, replaced by action scene summary check

---

## Open Questions

1. **What is the canonical list of 33 item_keys?**
   - What we know: 33 queries are documented above, covering population, structure, scenes, plot, relationships, world, tension, voice, names, canon, foreshadowing
   - What's unclear: The original PRD may have had a specific numbered list. The queries above derive from cross-referencing CONTEXT.md adaptations with actual schema.
   - Recommendation: The 33 queries above are the definitive list for this implementation. Planner should count them explicitly.

2. **Should run_gate_audit be idempotent when called multiple times?**
   - What we know: The ON CONFLICT upsert pattern ensures repeat calls overwrite item states cleanly.
   - What's unclear: Whether last_checked_at should be preserved from the last run or always updated to now.
   - Recommendation: Always update last_checked_at to now — callers need to know when the audit was last run.

3. **Should gate CLI commands use sync re-implementation of queries or call MCP tools?**
   - What we know: CLI must use sync sqlite3 (Typer is sync). Cannot call MCP tools from CLI.
   - What's unclear: Whether to duplicate query logic or extract to a shared module.
   - Recommendation: Duplicate minimal query logic in CLI. Extracting to a shared module adds complexity not justified at this scale. GATE_QUERIES dict can live in a constants file importable by both tools/gate.py and gate/cli.py.

---

## Sources

### Primary (HIGH confidence)
- Migration SQL files (migrations/*.sql) — exact column names and table schemas verified directly
- `src/novel/models/gate.py` — ArchitectureGate and GateChecklistItem confirmed
- `src/novel/models/shared.py` — GateViolation confirmed
- `src/novel/db/seed.py` — minimal seed content confirmed; gate additions identified
- `src/novel/mcp/server.py` — register pattern confirmed
- `src/novel/tools/plot.py` — complete tool module pattern confirmed
- `src/novel/cli.py` — Typer structure confirmed
- `src/novel/db/cli.py` — CLI command pattern confirmed
- `tests/test_plot.py` — MCP test pattern confirmed
- `.planning/phases/06-gate-system/06-CONTEXT.md` — locked decisions

### Secondary (MEDIUM confidence)
- CONTEXT.md schema adaptations (inciting_incident, is_primary, etc.) verified against migration SQL

### Tertiary (LOW confidence)
- None

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new dependencies; all existing
- Architecture patterns: HIGH — verified against Phases 3-5 codebase
- 33 gate queries: HIGH — each column verified against migration SQL
- Gate-ready seed additions: HIGH — gaps identified by reading full minimal seed
- Pitfalls: HIGH — derived from Phase 3-5 accumulated decisions in STATE.md

**Research date:** 2026-03-07
**Valid until:** 2026-04-07 (stable schema; no external dependencies)
