# Phase 11: Update Schema, CLI, MCP, and Planning Docs to Support 7-Point Structure and 3-Act/7-Point Integration — Research

**Researched:** 2026-03-09
**Domain:** SQLite schema extension, Pydantic model authoring, FastMCP tool registration, gate system extension
**Confidence:** HIGH — all findings derived directly from reading the actual codebase

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **Story-level beats:** New `story_structure` table (not adding columns to `books` or `acts`); `UNIQUE(book_id)`; 7 chapter FK columns (`hook_chapter_id`, `plot_turn_1_chapter_id`, `pinch_1_chapter_id`, `midpoint_chapter_id`, `pinch_2_chapter_id`, `plot_turn_2_chapter_id`, `resolution_chapter_id`) all nullable; 3 additional chapter FKs for 3-act alignment (`act_1_inciting_incident_chapter_id`, `act_2_midpoint_chapter_id`, `act_3_climax_chapter_id`) nullable; `notes` text; standard `created_at`/`updated_at`; new migration `022_seven_point_structure.sql`
- **Arc beat storage:** New `arc_seven_point_beats` junction table (not adding columns to `character_arcs`); `UNIQUE(arc_id, beat_type)`; `beat_type` TEXT enum: `'hook'`, `'plot_turn_1'`, `'pinch_1'`, `'midpoint'`, `'pinch_2'`, `'plot_turn_2'`, `'resolution'`; `chapter_id` FK nullable; `notes` text; `created_at`/`updated_at`; same migration as `story_structure`
- **Gate expansion:** 2 new items in `GATE_ITEM_META` and `GATE_QUERIES`: `struct_story_beats` (category `"structure"`) and `arcs_seven_point_beats` (category `"plot"`); total becomes 36; update `_GATE_ITEM_COUNT` comment; sanity assert stays
- **New MCP tools:** `src/novel/tools/structure.py` with 4 tools: `get_story_structure`, `upsert_story_structure`, `get_arc_beats`, `upsert_arc_beat`; all gate-free; `register(mcp)` pattern; wire into `server.py`
- **Pydantic models:** `StoryStructure` and `ArcSevenPointBeat` in new `src/novel/models/structure.py`
- **Planning doc update:** `project-research/database-schema.md` — add both tables in appropriate sections

### Claude's Discretion

- Exact SQL for the 2 new gate queries (follow existing patterns)
- Whether models go in new `structure.py` or added to `models/arcs.py` — prefer new file for clarity (user prefers not crowding)
- Seed data additions for gate-ready profile (1 `story_structure` row + 7 `arc_seven_point_beats` rows per test arc)

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

---

## Summary

Phase 11 is a pure **extend-don't-modify** operation on an already-complete 10-phase codebase. All patterns are established. The work follows the exact same shape as every prior phase: new migration SQL, new Pydantic models, new tool module with `register(mcp)`, extend gate dicts, wire into server, update seed, update schema doc. Nothing invented from scratch.

The critical insight is that `gate.py` currently has **34** items (not 33 as some prose states — confirmed from `_GATE_ITEM_COUNT = len(GATE_QUERIES)` and `test_gate.py` which asserts 35 total rows including the `min_characters` legacy row). Adding 2 new gate items brings the GATE_QUERIES count to **36** and total checklist rows to **37** after a `run_gate_audit` against the updated gate-ready seed.

The `beat_type` validation approach uses TEXT with no CHECK constraint — confirmed across the entire codebase: every enum-like column (e.g., `arc_type`, `health_status`, `touchpoint_type`, `thread_type`) is plain TEXT with a DEFAULT. Validation is handled by tools, never by database CHECK constraints.

**Primary recommendation:** Follow the `arcs.py` / `models/arcs.py` pattern exactly. New migration 022, new `models/structure.py`, new `tools/structure.py`, extend `gate.py` dicts, extend `_load_gate_ready` in `seed.py`, extend `TABLE_MODEL_MAP` in `test_schema_validation.py`, add to `models/__init__.py`, wire one line into `server.py`.

---

## Standard Stack

All patterns are already established. No new libraries needed.

### Core (already installed)

| Library | Version | Purpose | Established By |
|---------|---------|---------|---------------|
| `mcp.server.fastmcp` | >=1.26.0 | MCP tool registration via `@mcp.tool()` | Phase 3 |
| `pydantic` | >=2.11 | Model definitions via `BaseModel` | Phase 2 |
| `aiosqlite` | latest | Async DB access in MCP tools | Phase 3 |
| `sqlite3` | stdlib | Sync DB access in seed/CLI | Phase 1 |

### No New Dependencies

Phase 11 introduces no new packages. All tooling is already in `pyproject.toml`.

---

## Architecture Patterns

### Migration File Pattern

All migrations follow the convention in `src/novel/migrations/`. Confirmed naming: `NNN_descriptive_name.sql`. New file: `022_seven_point_structure.sql`.

**Exact SQL for `022_seven_point_structure.sql`:**

```sql
-- Migration 022: Story structure (7-point beats at story level and per-arc)
CREATE TABLE IF NOT EXISTS story_structure (
    id                              INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id                         INTEGER NOT NULL REFERENCES books(id),
    hook_chapter_id                 INTEGER REFERENCES chapters(id),
    plot_turn_1_chapter_id          INTEGER REFERENCES chapters(id),
    pinch_1_chapter_id              INTEGER REFERENCES chapters(id),
    midpoint_chapter_id             INTEGER REFERENCES chapters(id),
    pinch_2_chapter_id              INTEGER REFERENCES chapters(id),
    plot_turn_2_chapter_id          INTEGER REFERENCES chapters(id),
    resolution_chapter_id           INTEGER REFERENCES chapters(id),
    act_1_inciting_incident_chapter_id  INTEGER REFERENCES chapters(id),
    act_2_midpoint_chapter_id       INTEGER REFERENCES chapters(id),
    act_3_climax_chapter_id         INTEGER REFERENCES chapters(id),
    notes                           TEXT,
    created_at                      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at                      TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(book_id)
);

CREATE TABLE IF NOT EXISTS arc_seven_point_beats (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    arc_id      INTEGER NOT NULL REFERENCES character_arcs(id),
    beat_type   TEXT    NOT NULL,
    chapter_id  INTEGER REFERENCES chapters(id),
    notes       TEXT,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE(arc_id, beat_type)
);
```

**Confirmed pattern from `003_acts.sql` and `017_arcs_chekhov.sql`:**
- `INTEGER PRIMARY KEY AUTOINCREMENT`
- FK columns as `INTEGER REFERENCES table(id)` — no explicit `ON DELETE`
- Nullable FK columns declared without `NOT NULL`
- TEXT NOT NULL DEFAULT (datetime('now')) for timestamps
- No CHECK constraints — TEXT columns are plain TEXT

### Pydantic Model Pattern

Source: `src/novel/models/arcs.py` — the closest analogue.

**New file: `src/novel/models/structure.py`**

```python
"""Structure domain Pydantic models — story-level 7-point beats and per-arc beats."""

from pydantic import BaseModel


class StoryStructure(BaseModel):
    """Represents a row in the story_structure table (migration 022)."""
    id: int | None = None
    book_id: int
    hook_chapter_id: int | None = None
    plot_turn_1_chapter_id: int | None = None
    pinch_1_chapter_id: int | None = None
    midpoint_chapter_id: int | None = None
    pinch_2_chapter_id: int | None = None
    plot_turn_2_chapter_id: int | None = None
    resolution_chapter_id: int | None = None
    act_1_inciting_incident_chapter_id: int | None = None
    act_2_midpoint_chapter_id: int | None = None
    act_3_climax_chapter_id: int | None = None
    notes: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class ArcSevenPointBeat(BaseModel):
    """Represents a row in the arc_seven_point_beats table (migration 022)."""
    id: int | None = None
    arc_id: int
    beat_type: str
    chapter_id: int | None = None
    notes: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
```

**Key rule confirmed:** Field names match SQL column names exactly. No aliasing. No to_db_dict() — these models have no JSON TEXT columns (confirmed from Phase 02-01 decision: "Only models with JSON TEXT columns get to_db_dict()").

### Tool Module Pattern

Source: `src/novel/tools/arcs.py` — 6 tools, all inside `register(mcp: FastMCP)`.

**New file: `src/novel/tools/structure.py`**

```python
"""Structure domain MCP tools — story-level 7-point beats and per-arc beats.

All 4 structure tools are registered via the register(mcp) function pattern.
Gate-free: these tools populate data that the gate checks, not data that
requires prior gate certification.

IMPORTANT: Never use the print function in this module. All logging goes to
stderr via the logging module — using print corrupts the stdio protocol.
"""

import logging

from mcp.server.fastmcp import FastMCP

from novel.mcp.db import get_connection
from novel.models.shared import NotFoundResponse, ValidationFailure
from novel.models.structure import ArcSevenPointBeat, StoryStructure

logger = logging.getLogger(__name__)

VALID_BEAT_TYPES = frozenset({
    "hook", "plot_turn_1", "pinch_1", "midpoint",
    "pinch_2", "plot_turn_2", "resolution",
})


def register(mcp: FastMCP) -> None:
    """Register all 4 structure domain tools with the given FastMCP instance."""

    @mcp.tool()
    async def get_story_structure(book_id: int) -> StoryStructure | NotFoundResponse:
        ...

    @mcp.tool()
    async def upsert_story_structure(
        book_id: int,
        hook_chapter_id: int | None = None,
        ...
    ) -> StoryStructure | ValidationFailure:
        ...

    @mcp.tool()
    async def get_arc_beats(arc_id: int) -> list[ArcSevenPointBeat]:
        ...

    @mcp.tool()
    async def upsert_arc_beat(
        arc_id: int,
        beat_type: str,
        chapter_id: int | None = None,
        notes: str | None = None,
    ) -> ArcSevenPointBeat | ValidationFailure:
        ...
```

### Upsert SQL Patterns

**`upsert_story_structure` — story_structure has UNIQUE(book_id):**

The `story_structure` table has `UNIQUE(book_id)`. This is analogous to `upsert_faction` which uses `ON CONFLICT(name)`. Two-branch pattern:

```sql
-- None id branch: plain INSERT, read back by lastrowid
INSERT INTO story_structure
    (book_id, hook_chapter_id, ..., updated_at)
VALUES (?, ?, ..., datetime('now'))

-- provided id branch: ON CONFLICT(book_id) DO UPDATE
INSERT INTO story_structure
    (book_id, hook_chapter_id, ..., updated_at)
VALUES (?, ?, ..., datetime('now'))
ON CONFLICT(book_id) DO UPDATE SET
    hook_chapter_id = excluded.hook_chapter_id,
    ...
    updated_at = datetime('now')
```

Actually, since `story_structure` has `UNIQUE(book_id)` (not UNIQUE on `id`), the preferred pattern is a **single-branch** upsert targeting `book_id` — no need for a "None id" branch since `book_id` is always the business key:

```sql
INSERT INTO story_structure (book_id, hook_chapter_id, ...)
VALUES (?, ?, ...)
ON CONFLICT(book_id) DO UPDATE SET
    hook_chapter_id = excluded.hook_chapter_id,
    ...,
    updated_at = datetime('now')
```

Read back with `SELECT * FROM story_structure WHERE book_id = ?`.

**`upsert_arc_beat` — arc_seven_point_beats has UNIQUE(arc_id, beat_type):**

```sql
INSERT INTO arc_seven_point_beats (arc_id, beat_type, chapter_id, notes, updated_at)
VALUES (?, ?, ?, ?, datetime('now'))
ON CONFLICT(arc_id, beat_type) DO UPDATE SET
    chapter_id = excluded.chapter_id,
    notes = excluded.notes,
    updated_at = datetime('now')
```

Read back with `SELECT * FROM arc_seven_point_beats WHERE arc_id = ? AND beat_type = ?`.

### Gate Extension Pattern

Source: `src/novel/tools/gate.py` — confirmed current count is **34** GATE_QUERIES items.

Adding 2 new items:

```python
# In GATE_ITEM_META:
"struct_story_beats": {
    "category": "structure",
    "description": (
        "Story-level 7-point beats are defined "
        "(story_structure row exists with all 7 beats populated)"
    ),
},
"arcs_seven_point_beats": {
    "category": "plot",
    "description": (
        "All POV character arcs have all 7-point beat chapters defined"
    ),
},

# In GATE_QUERIES:
"struct_story_beats": (
    "SELECT COUNT(*) AS missing_count FROM books b"
    " WHERE NOT EXISTS ("
    " SELECT 1 FROM story_structure ss"
    " WHERE ss.book_id = b.id"
    "   AND ss.hook_chapter_id IS NOT NULL"
    "   AND ss.plot_turn_1_chapter_id IS NOT NULL"
    "   AND ss.pinch_1_chapter_id IS NOT NULL"
    "   AND ss.midpoint_chapter_id IS NOT NULL"
    "   AND ss.pinch_2_chapter_id IS NOT NULL"
    "   AND ss.plot_turn_2_chapter_id IS NOT NULL"
    "   AND ss.resolution_chapter_id IS NOT NULL"
    ")"
),
"arcs_seven_point_beats": (
    "SELECT COUNT(DISTINCT ca.id) AS missing_count"
    " FROM character_arcs ca"
    " JOIN chapters ch ON ch.pov_character_id = ca.character_id"
    " WHERE ("
    "   SELECT COUNT(*) FROM arc_seven_point_beats ab"
    "   WHERE ab.arc_id = ca.id"
    "     AND ab.chapter_id IS NOT NULL"
    " ) < 7"
),
```

Update the comment on `_GATE_ITEM_COUNT`:

```python
_GATE_ITEM_COUNT = len(GATE_QUERIES)  # 36 items — store once for tool use
```

**CRITICAL:** The `assert set(GATE_QUERIES) == set(GATE_ITEM_META)` check will fail at import time if the two dicts are not updated in lockstep. Both dicts MUST receive both new keys simultaneously.

### server.py Wiring

Source: `src/novel/mcp/server.py` — confirmed pattern.

Add to the import line and add one register call:

```python
# Import line (extend existing):
from novel.tools import (
    characters, relationships, chapters, scenes, world, magic,
    plot, arcs, gate, session, timeline, canon, knowledge,
    foreshadowing, names, voice, publishing, structure
)

# New registration block (after Phase 9 block):
# Register domain tools — Phase 11
structure.register(mcp)
```

### models/__init__.py Extension

Add to the import and __all__ sections:

```python
from novel.models.structure import StoryStructure, ArcSevenPointBeat

# In __all__:
"StoryStructure",
"ArcSevenPointBeat",
```

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Upsert with conflict | Custom SELECT then INSERT/UPDATE | `ON CONFLICT(col) DO UPDATE SET` | Established pattern, atomic, handles race conditions |
| Enum validation | CHECK constraint in SQL | Python-level validation in tool | Confirmed: ALL existing enum-like columns are plain TEXT; no CHECK constraints exist anywhere in the 21 migrations |
| Model-schema drift detection | Manual | `test_schema_validation.py` TABLE_MODEL_MAP | Extend the existing map; test already parameterized |
| Tool registration | `@app.tool()` at module level | `register(mcp: FastMCP)` local function pattern | Established in Phase 3; module-level decoration breaks hot-reload and testing |

---

## Common Pitfalls

### Pitfall 1: Gate Dict Mismatch
**What goes wrong:** Adding a key to `GATE_ITEM_META` but not `GATE_QUERIES` (or vice versa) — the `assert set(GATE_QUERIES) == set(GATE_ITEM_META)` at module import time throws `AssertionError` and the entire MCP server fails to start.
**Why it happens:** Two separate dicts with the same key namespace.
**How to avoid:** Update both dicts in the same edit. The assert fires immediately on import, so failures are caught at test time, not silently.

### Pitfall 2: test_gate.py Count Assertions
**What goes wrong:** `test_get_gate_checklist_returns_items` asserts `len(items) == 35`. After Phase 11, the gate-ready seed populates 36 new GATE_ITEM_META items + 1 `min_characters` legacy row = **37 total rows**. The test will fail unless updated.
**Why it happens:** The test hardcodes `== 35`.
**How to avoid:** Update the assertion in `test_gate.py` from `== 35` to `== 37`. Also update `test_run_gate_audit_returns_expected_items` which asserts `data["total_items"] == 35` — change to `== 37`.

**Exact lines to update in `tests/test_gate.py`:**
- Line 97: `assert len(items) == 35` → `== 37`
- Line 118: `assert data["total_items"] == 35` → `== 37`
- Line 121: `assert len(data["items"]) == 35` → `== 37`
- Comment on line 7: "34 GATE_ITEM_META + 1 min_characters" → "36 GATE_ITEM_META + 1 min_characters"
- Comment on line 92: "34 GATE_ITEM_META + 1 min_characters = 35" → "36 GATE_ITEM_META + 1 min_characters = 37"
- Comment on line 114: "all 34 SQL queries" → "all 36 SQL queries"

### Pitfall 3: TABLE_MODEL_MAP Not Updated
**What goes wrong:** `test_schema_validation.py` has a registry-driven `TABLE_MODEL_MAP`. If new tables are not added, the schema validation test does not cover the new tables — silent gap.
**Why it happens:** The test only validates tables it knows about.
**How to avoid:** Add both new tables to `TABLE_MODEL_MAP`:
```python
"story_structure": StoryStructure,
"arc_seven_point_beats": ArcSevenPointBeat,
```
Also add imports at the top of the test file.

### Pitfall 4: Migration Runner File Count
**What goes wrong:** `src/novel/db/migrations.py` likely discovers migrations by scanning the directory. If it uses glob or sorted os.listdir, adding `022_seven_point_structure.sql` should auto-register. But if there's a hardcoded list or count check, it will fail.
**How to avoid:** Confirm the migration runner uses directory scanning (not a hardcoded list). From established patterns, the runner sorts numerically by filename prefix — `022_` sorts after `021_` correctly.

### Pitfall 5: Gate-Ready Seed Must Include New Tables
**What goes wrong:** The gate-ready seed calls `_load_gate_ready` which iterates `GATE_ITEM_META` to populate `gate_checklist_items`. The 2 new gate items will be inserted. But the SQL queries for `struct_story_beats` and `arcs_seven_point_beats` will FAIL (return missing_count > 0) unless the seed also inserts rows into `story_structure` and `arc_seven_point_beats`.
**Why it happens:** `run_gate_audit` runs all queries including the 2 new ones against seed data; if seed has no `story_structure` row, `struct_story_beats` returns missing_count=1.
**How to avoid:** In `_load_gate_ready`, after the existing arc insertion, add:
1. One `story_structure` row for book_id=1 with all 7 beat chapter FKs set (can use chapter_id=1, 2, 3 for the first few and repeat for the rest — seed only needs values, not narrative accuracy)
2. For each test arc (arc_id=1 for protagonist, arc_id=2 for mentor/Ithrel Cass): insert 7 `arc_seven_point_beats` rows with `chapter_id` set

### Pitfall 6: upsert_story_structure is Single-Branch (Not Two-Branch)
**What goes wrong:** Using a two-branch None-id/provided-id pattern where it isn't needed.
**Why it doesn't apply:** `story_structure` has `UNIQUE(book_id)`, making `book_id` the natural conflict key. The right pattern is single-branch: INSERT with ON CONFLICT(book_id) DO UPDATE. No need to check `id is None`. This is simpler than the two-branch `upsert_chekov` pattern.

---

## Code Examples

### get_story_structure Tool

```python
@mcp.tool()
async def get_story_structure(book_id: int) -> StoryStructure | NotFoundResponse:
    """Retrieve the story-level 7-point structure for a book.

    Args:
        book_id: Primary key of the book to retrieve structure for.

    Returns:
        StoryStructure record, or NotFoundResponse if no story_structure
        row exists for this book yet.
    """
    async with get_connection() as conn:
        rows = await conn.execute_fetchall(
            "SELECT * FROM story_structure WHERE book_id = ?",
            (book_id,),
        )
        if not rows:
            return NotFoundResponse(
                not_found_message=f"No story structure found for book {book_id}."
            )
        return StoryStructure(**dict(rows[0]))
```

### upsert_story_structure Tool (single-branch ON CONFLICT(book_id))

```python
@mcp.tool()
async def upsert_story_structure(
    book_id: int,
    hook_chapter_id: int | None = None,
    plot_turn_1_chapter_id: int | None = None,
    pinch_1_chapter_id: int | None = None,
    midpoint_chapter_id: int | None = None,
    pinch_2_chapter_id: int | None = None,
    plot_turn_2_chapter_id: int | None = None,
    resolution_chapter_id: int | None = None,
    act_1_inciting_incident_chapter_id: int | None = None,
    act_2_midpoint_chapter_id: int | None = None,
    act_3_climax_chapter_id: int | None = None,
    notes: str | None = None,
) -> StoryStructure | ValidationFailure:
    """Create or update the story-level 7-point structure for a book.

    Single-branch upsert using ON CONFLICT(book_id) — one row per book.
    All beat chapter FKs are nullable; populate progressively.
    """
    async with get_connection() as conn:
        try:
            await conn.execute(
                """INSERT INTO story_structure
                       (book_id, hook_chapter_id, plot_turn_1_chapter_id,
                        pinch_1_chapter_id, midpoint_chapter_id,
                        pinch_2_chapter_id, plot_turn_2_chapter_id,
                        resolution_chapter_id, act_1_inciting_incident_chapter_id,
                        act_2_midpoint_chapter_id, act_3_climax_chapter_id,
                        notes, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                   ON CONFLICT(book_id) DO UPDATE SET
                       hook_chapter_id = excluded.hook_chapter_id,
                       plot_turn_1_chapter_id = excluded.plot_turn_1_chapter_id,
                       pinch_1_chapter_id = excluded.pinch_1_chapter_id,
                       midpoint_chapter_id = excluded.midpoint_chapter_id,
                       pinch_2_chapter_id = excluded.pinch_2_chapter_id,
                       plot_turn_2_chapter_id = excluded.plot_turn_2_chapter_id,
                       resolution_chapter_id = excluded.resolution_chapter_id,
                       act_1_inciting_incident_chapter_id = excluded.act_1_inciting_incident_chapter_id,
                       act_2_midpoint_chapter_id = excluded.act_2_midpoint_chapter_id,
                       act_3_climax_chapter_id = excluded.act_3_climax_chapter_id,
                       notes = excluded.notes,
                       updated_at = datetime('now')""",
                (
                    book_id,
                    hook_chapter_id, plot_turn_1_chapter_id,
                    pinch_1_chapter_id, midpoint_chapter_id,
                    pinch_2_chapter_id, plot_turn_2_chapter_id,
                    resolution_chapter_id, act_1_inciting_incident_chapter_id,
                    act_2_midpoint_chapter_id, act_3_climax_chapter_id,
                    notes,
                ),
            )
            await conn.commit()
            rows = await conn.execute_fetchall(
                "SELECT * FROM story_structure WHERE book_id = ?",
                (book_id,),
            )
            return StoryStructure(**dict(rows[0]))
        except Exception as exc:
            logger.error("upsert_story_structure failed: %s", exc)
            return ValidationFailure(is_valid=False, errors=[str(exc)])
```

### upsert_arc_beat Tool

```python
@mcp.tool()
async def upsert_arc_beat(
    arc_id: int,
    beat_type: str,
    chapter_id: int | None = None,
    notes: str | None = None,
) -> ArcSevenPointBeat | ValidationFailure:
    """Create or update a single 7-point beat for a character arc.

    ON CONFLICT(arc_id, beat_type) DO UPDATE — one row per beat per arc.
    beat_type must be one of: hook, plot_turn_1, pinch_1, midpoint,
    pinch_2, plot_turn_2, resolution.
    """
    if beat_type not in VALID_BEAT_TYPES:
        return ValidationFailure(
            is_valid=False,
            errors=[
                f"Invalid beat_type '{beat_type}'. "
                f"Must be one of: {sorted(VALID_BEAT_TYPES)}"
            ],
        )
    async with get_connection() as conn:
        try:
            await conn.execute(
                """INSERT INTO arc_seven_point_beats
                       (arc_id, beat_type, chapter_id, notes, updated_at)
                   VALUES (?, ?, ?, ?, datetime('now'))
                   ON CONFLICT(arc_id, beat_type) DO UPDATE SET
                       chapter_id = excluded.chapter_id,
                       notes = excluded.notes,
                       updated_at = datetime('now')""",
                (arc_id, beat_type, chapter_id, notes),
            )
            await conn.commit()
            rows = await conn.execute_fetchall(
                "SELECT * FROM arc_seven_point_beats WHERE arc_id = ? AND beat_type = ?",
                (arc_id, beat_type),
            )
            return ArcSevenPointBeat(**dict(rows[0]))
        except Exception as exc:
            logger.error("upsert_arc_beat failed: %s", exc)
            return ValidationFailure(is_valid=False, errors=[str(exc)])
```

### get_arc_beats Tool

```python
@mcp.tool()
async def get_arc_beats(arc_id: int) -> list[ArcSevenPointBeat]:
    """Retrieve all 7-point beat records for a character arc.

    Returns all beats defined so far — may be partial (0-7 records).
    Empty list is valid: an arc with no beats defined yet.

    Args:
        arc_id: Primary key of the character arc.

    Returns:
        List of ArcSevenPointBeat records ordered by beat_type (may be empty).
    """
    async with get_connection() as conn:
        rows = await conn.execute_fetchall(
            "SELECT * FROM arc_seven_point_beats WHERE arc_id = ? ORDER BY beat_type",
            (arc_id,),
        )
        return [ArcSevenPointBeat(**dict(r)) for r in rows]
```

### Gate Query Examples (with rationale)

```python
# struct_story_beats — count books that have no story_structure row
# OR have any of the 7 beat chapter FKs as NULL
"struct_story_beats": (
    "SELECT COUNT(*) AS missing_count FROM books b"
    " WHERE NOT EXISTS ("
    " SELECT 1 FROM story_structure ss"
    " WHERE ss.book_id = b.id"
    "   AND ss.hook_chapter_id IS NOT NULL"
    "   AND ss.plot_turn_1_chapter_id IS NOT NULL"
    "   AND ss.pinch_1_chapter_id IS NOT NULL"
    "   AND ss.midpoint_chapter_id IS NOT NULL"
    "   AND ss.pinch_2_chapter_id IS NOT NULL"
    "   AND ss.plot_turn_2_chapter_id IS NOT NULL"
    "   AND ss.resolution_chapter_id IS NOT NULL"
    ")"
),

# arcs_seven_point_beats — count POV character arcs missing any of the 7 beats
# "POV arc" = arc belonging to a character who appears as pov_character_id in any chapter
"arcs_seven_point_beats": (
    "SELECT COUNT(DISTINCT ca.id) AS missing_count"
    " FROM character_arcs ca"
    " WHERE EXISTS ("
    "   SELECT 1 FROM chapters ch"
    "   WHERE ch.pov_character_id = ca.character_id"
    " )"
    " AND ("
    "   SELECT COUNT(*) FROM arc_seven_point_beats ab"
    "   WHERE ab.arc_id = ca.id"
    "     AND ab.chapter_id IS NOT NULL"
    " ) < 7"
),
```

### Seed Data for Gate-Ready

```python
# In _load_gate_ready, after arcs_pov block:

# --- struct_story_beats: book_id=1 needs story_structure with all 7 beats ---
conn.execute(
    """INSERT OR IGNORE INTO story_structure
           (book_id, hook_chapter_id, plot_turn_1_chapter_id, pinch_1_chapter_id,
            midpoint_chapter_id, pinch_2_chapter_id, plot_turn_2_chapter_id,
            resolution_chapter_id, act_1_inciting_incident_chapter_id,
            act_2_midpoint_chapter_id, act_3_climax_chapter_id, notes)
       VALUES (1, 1, 1, 2, 2, 3, 3, 3, 1, 2, 3,
               'Gate-ready seed: beat chapters assigned for structural completeness.')"""
)

# --- arcs_seven_point_beats: all POV arcs (arc_id=1 protagonist, arc_id=2 mentor) ---
# need 7 rows each with chapter_id IS NOT NULL
_BEAT_TYPES = [
    "hook", "plot_turn_1", "pinch_1",
    "midpoint", "pinch_2", "plot_turn_2", "resolution",
]
for arc_id in (1, 2):
    for beat_type in _BEAT_TYPES:
        conn.execute(
            "INSERT OR IGNORE INTO arc_seven_point_beats "
            "(arc_id, beat_type, chapter_id, notes) VALUES (?, ?, 1, 'gate-ready seed')",
            (arc_id, beat_type),
        )
```

---

## database-schema.md Update Location

The new tables belong in **Section 3: Plot and Arc Tables** (confirmed from the schema doc structure: `## Section 3: Plot and Arc Tables`). This is where `character_arcs`, `chapter_character_arcs`, and `arc_health_log` live. The new tables are directly related to arc structure.

Add after the `arc_health_log` subsection:

```markdown
### `story_structure`
```sql
id                                  bigint PK
book_id                             bigint FK -> books.id UNIQUE (one row per book)
hook_chapter_id                     bigint FK -> chapters.id nullable
plot_turn_1_chapter_id              bigint FK -> chapters.id nullable
pinch_1_chapter_id                  bigint FK -> chapters.id nullable
midpoint_chapter_id                 bigint FK -> chapters.id nullable
pinch_2_chapter_id                  bigint FK -> chapters.id nullable
plot_turn_2_chapter_id              bigint FK -> chapters.id nullable
resolution_chapter_id               bigint FK -> chapters.id nullable
act_1_inciting_incident_chapter_id  bigint FK -> chapters.id nullable  -- 3-act alignment: Act 1→2 inciting incident
act_2_midpoint_chapter_id           bigint FK -> chapters.id nullable  -- 3-act alignment: Act 2 midpoint
act_3_climax_chapter_id             bigint FK -> chapters.id nullable  -- 3-act alignment: Act 2→3 climax
notes                               text
created_at                          timestamp
updated_at                          timestamp
```
One row per book. The 7 beat fields (hook through resolution) represent the Story Architect's 7-point structural map. The 3 act-alignment fields satisfy PRD gate item 12's `inciting_incident`, `midpoint`, `climax` requirements without modifying the `acts` table.

---

### `arc_seven_point_beats`
```sql
id          bigint PK
arc_id      bigint FK -> character_arcs.id
beat_type   text NOT NULL  -- 'hook' | 'plot_turn_1' | 'pinch_1' | 'midpoint' | 'pinch_2' | 'plot_turn_2' | 'resolution'
chapter_id  bigint FK -> chapters.id nullable  -- can be recorded before chapter is locked
notes       text
created_at  timestamp
updated_at  timestamp
UNIQUE(arc_id, beat_type)
```
Junction table: one row per beat per arc. Upsertable on (arc_id, beat_type). Partial population is valid — arcs are populated progressively. All 7 beats with non-null chapter_id required to pass gate item `arcs_seven_point_beats`.
```

---

## Complete File Checklist

The following files require changes in Phase 11 (HIGH confidence, derived from reading actual codebase):

| File | Change | New vs Modify |
|------|--------|---------------|
| `src/novel/migrations/022_seven_point_structure.sql` | New migration | NEW |
| `src/novel/models/structure.py` | New Pydantic models | NEW |
| `src/novel/tools/structure.py` | New MCP tool module | NEW |
| `src/novel/tools/gate.py` | Add 2 keys to both dicts + update comment | MODIFY |
| `src/novel/mcp/server.py` | Import + register structure | MODIFY |
| `src/novel/models/__init__.py` | Import + __all__ extension | MODIFY |
| `src/novel/db/seed.py` | Add story_structure + arc_seven_point_beats rows to gate_ready | MODIFY |
| `tests/test_schema_validation.py` | Add TABLE_MODEL_MAP entries + imports | MODIFY |
| `tests/test_gate.py` | Update hardcoded item count assertions (35→37) | MODIFY |
| `tests/test_structure.py` | New domain test file | NEW |
| `project-research/database-schema.md` | Add both table definitions in Section 3 | MODIFY |

---

## State of the Art

| Old Approach | Current Approach | Impact |
|--------------|-----------------|--------|
| "Gate has 33 items" (PRD/ROADMAP prose) | Actually 34 items (confirmed: `len(GATE_QUERIES)` = 34, `_GATE_ITEM_COUNT = 34`) | Adding 2 = 36 total; test assertions must change to 37 (36 + min_characters) |
| PRD gate item 15 mentions "7-point beats on character_arc" | Phase 11 uses junction table instead of columns on character_arcs | More flexible, partial population supported |
| PRD gate item 12 mentions "inciting_incident/midpoint/climax on acts" | Phase 11 puts these on story_structure, not acts | Avoids modifying existing acts table |

---

## Open Questions

1. **Gate query for `struct_story_beats` — should it check all books or only book_id=1?**
   - What we know: The seed has book_id=1 only. The gate queries are relational ("all X must have Y").
   - What's unclear: If multiple books exist (seed has book_id=1 and book_id=2), should book 2 (status='planning') be required to have a story_structure row?
   - Recommendation: Query against all books (no `WHERE book_id = 1` filter) — consistent with other gate queries that are relational and size-agnostic. Gate-ready seed only has book_id=1 with structure; book_id=2 would be a gate blocker unless excluded. Consider `WHERE books.status NOT IN ('planning')` or simply document that the gate is per-active-book. Simplest: let the gate require all books. Seed inserts story_structure for book_id=1 only, so ensure minimal seed does NOT insert a story_structure row for book_id=2.

2. **`arcs_seven_point_beats` gate — should it check all character_arcs or only POV arcs?**
   - What we know: PRD gate item 15 specifies "all 6 POV characters have a character_arc with all 7-point beat chapters defined."
   - What's unclear: Minor characters also have arcs in theory. Checking all arcs would be too strict.
   - Recommendation (already in CONTEXT.md): Gate checks arcs belonging to POV characters (`characters who appear as pov_character_id in at least one chapter`). Matches the pattern from `arcs_pov` gate query.

---

## Sources

### Primary (HIGH confidence — read directly from codebase)

- `src/novel/tools/gate.py` — exact GATE_ITEM_META and GATE_QUERIES dicts, count = 34, assertion pattern
- `src/novel/models/arcs.py` — Pydantic v2 model pattern (field names = SQL column names, all nullable fields as `int | None = None`)
- `src/novel/tools/arcs.py` — register(mcp) pattern, two-branch upsert, ON CONFLICT(id) DO UPDATE shape
- `src/novel/mcp/server.py` — wiring pattern, import style
- `src/novel/migrations/017_arcs_chekhov.sql` — table creation pattern (TEXT not CHECK, nullable FK syntax)
- `src/novel/migrations/003_acts.sql` — table creation pattern for reference tables
- `src/novel/db/seed.py` — gate_ready seed structure, INSERT OR IGNORE pattern, how GATE_ITEM_META is imported and iterated
- `tests/test_schema_validation.py` — TABLE_MODEL_MAP structure, exact assertions that require updating
- `tests/test_gate.py` — exact count assertions (35) that must become 37
- `src/novel/models/__init__.py` — re-export pattern
- `.planning/config.json` — `nyquist_validation: false` (skip Validation Architecture section)

---

## Metadata

**Confidence breakdown:**
- Migration SQL: HIGH — pattern confirmed from 21 existing migrations
- Pydantic models: HIGH — pattern confirmed from arcs.py
- Tool implementation: HIGH — confirmed from arcs.py exact shape
- Gate queries: MEDIUM-HIGH — query shape confirmed from 34 existing queries; exact subquery formulation is new (but follows NOT EXISTS and COUNT(*) patterns already in use)
- Seed data: HIGH — _load_gate_ready pattern confirmed; INSERT OR IGNORE usage confirmed
- Test file updates: HIGH — exact line numbers and current values confirmed from reading test_gate.py

**Research date:** 2026-03-09
**Valid until:** Stable — this is internal codebase research, no external dependencies
