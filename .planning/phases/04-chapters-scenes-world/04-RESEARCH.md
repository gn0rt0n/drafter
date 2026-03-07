# Phase 4: Chapters, Scenes & World - Research

**Researched:** 2026-03-07
**Domain:** FastMCP tool module extension — chapters, scenes, world-building, magic domain tools
**Confidence:** HIGH

## Summary

Phase 4 adds 19 MCP tools across 4 new modules (chapters, scenes, world, magic) following the identical register(mcp: FastMCP) -> None pattern established in Phase 3. Every pattern needed already exists in the codebase: the upsert pattern is in characters.py, the log pattern is in relationships.py, the JSON field serialization pattern is in Scene.to_db_dict() and Location.to_db_dict(), and the in-memory FastMCP client test pattern is in test_characters.py and test_relationships.py.

The only novel element in this phase is check_magic_compliance — a read-only analysis tool that queries two tables and synthesizes a structured response rather than returning a single DB row. This pattern does not exist yet in the codebase. The logic is: query magic_system_elements for rules/limitations/costs, query practitioner_abilities to determine whether the character has the ability registered, derive `compliant = no violations AND character_has_ability` (when ability data exists), and return the structured dict.

The upsert_faction tool has a subtle edge: faction_political_states has UNIQUE(faction_id, chapter_id) and is a child table of factions. Inserting a new faction row is safe — the political state is logged separately via a hypothetical future tool. upsert_faction only writes to the factions table itself; faction_political_states is a distinct time-stamped log table, not an updatable field of the faction. No cross-table write needed.

**Primary recommendation:** Copy the Phase 3 tool module structure verbatim. All four new modules are mechanical extensions of the existing pattern, with check_magic_compliance as the one synthesis-pattern tool to implement carefully.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Tool module split:**
- 4 tool modules, matching the existing model file organization: `tools/chapters.py`, `tools/scenes.py`, `tools/world.py`, `tools/magic.py`
- `server.py` gets 4 more `register(mcp)` calls in sequence after Phase 3's two calls
- Each module exposes `register(mcp: FastMCP) -> None` — no deviation from the established pattern

**`get_chapter` vs `get_chapter_plan` distinction (CHAP-01 vs CHAP-02):**
- `get_chapter` returns the full `Chapter` model row — all fields including hook notes and structural fields
- `get_chapter_plan` returns a focused writing-guidance subset: `{chapter_id, summary, opening_state, closing_state, opening_hook_note, closing_hook_note, structural_function, hook_strength_rating}` — a TypedDict or small Pydantic model
- Same pattern as `get_character` (full row) vs state tools like `get_character_injuries` (focused subset)

**`check_magic_compliance` behavior (WRLD-08):**
- Inputs: `character_id: int`, `magic_element_id: int`, `action_description: str`
- Logic: Query `magic_system_elements` for rules/limitations/costs, query `practitioner_abilities` to check whether the character has the ability registered
- Returns a structured result: `{compliant: bool, violations: list[str], applicable_rules: list[str], character_has_ability: bool | None}`
- `compliant` is derived: True if no violations AND character_has_ability (when ability data exists)
- Does NOT write to `magic_use_log` — logging is a separate tool (`log_magic_use`, WRLD-07)
- This gives Claude structured data to reason about compliance without leaving judgment ambiguous

### Claude's Discretion
- All implementation details: SQL queries, row-to-model mapping, aiosqlite patterns
- Chapter plan response type (TypedDict vs small Pydantic model)
- Exact upsert conflict resolution logic for upsert_chapter, upsert_scene, upsert_scene_goal, upsert_location, upsert_faction
- Test fixture scope (session vs function level)
- Plan file split across the 3 plan slots

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| CHAP-01 | Claude can retrieve a chapter with its plan and metadata (`get_chapter`) | Full Chapter model is ready; SELECT * FROM chapters WHERE id = ? pattern established |
| CHAP-02 | Claude can retrieve a chapter's writing plan (`get_chapter_plan`) | Returns focused subset; new small Pydantic model or TypedDict; same table, different projection |
| CHAP-03 | Claude can retrieve a chapter's structural obligations (`get_chapter_obligations`) | chapter_structural_obligations table seeded; ChapterStructuralObligation model ready |
| CHAP-04 | Claude can retrieve a scene with full details (`get_scene`) | Scene model ready with JSON field_validator for narrative_functions |
| CHAP-05 | Claude can retrieve character goals for a scene (`get_scene_character_goals`) | SceneCharacterGoal model ready; seed inserts one goal for scene 1 |
| CHAP-06 | Claude can list all chapters in the book (`list_chapters`) | chapters table indexed on book_id; book_id filter required |
| CHAP-07 | Claude can create or update a chapter record (`upsert_chapter`) | UNIQUE(book_id, chapter_number) is conflict target |
| CHAP-08 | Claude can create or update a scene record (`upsert_scene`) | UNIQUE(chapter_id, scene_number) is conflict target; narrative_functions needs JSON serialization |
| CHAP-09 | Claude can create or update a character goal for a scene (`upsert_scene_goal`) | UNIQUE(scene_id, character_id) is conflict target; simple non-JSON upsert |
| WRLD-01 | Claude can retrieve a location with its sensory profile (`get_location`) | Location model with sensory_profile JSON field_validator ready; seed has 1 location |
| WRLD-02 | Claude can retrieve a faction's profile (`get_faction`) | Faction model ready; seed has 1 faction with leader_character_id |
| WRLD-03 | Claude can retrieve a faction's current political state (`get_faction_political_state`) | faction_political_states table; UNIQUE(faction_id, chapter_id); seed has 1 row for faction 1, chapter 1 |
| WRLD-04 | Claude can retrieve a culture record (`get_culture`) | Culture model ready; seed has 1 culture |
| WRLD-05 | Claude can retrieve a magic system element with its rules and limitations (`get_magic_element`) | MagicSystemElement model ready; seed has 1 element (Ember-Binding) |
| WRLD-06 | Claude can retrieve a character's practitioner abilities (`get_practitioner_abilities`) | PractitionerAbility model ready; seed inserts (char 1, magic_element 1, proficiency 3) |
| WRLD-07 | Claude can log a magic use event (`log_magic_use`) | magic_use_log is append-only (no UNIQUE); log pattern from log_character_knowledge |
| WRLD-08 | Claude can check whether a proposed magic action is compliant (`check_magic_compliance`) | Two-query synthesis tool; structured return type needed; no DB write |
| WRLD-09 | Claude can create or update a location record (`upsert_location`) | locations has no UNIQUE constraint — conflict on id; sensory_profile JSON serialization via to_db_dict() |
| WRLD-10 | Claude can create or update a faction record (`upsert_faction`) | factions has UNIQUE(name) — conflict target; does NOT write to faction_political_states |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `mcp.server.fastmcp` | bundled in mcp>=1.26.0,<2.0.0 | FastMCP instance and @mcp.tool() decorator | Project-locked; Phase 3 established |
| `aiosqlite` | >=0.17.0 | Async SQLite connection for all tool handlers | Project-locked; every existing tool uses it |
| `pydantic` | >=2.11 (v2) | Domain models, field_validator for JSON coercion | Project-locked; all 14 domain models use it |
| `novel.mcp.db.get_connection` | internal | Async context manager that sets WAL + FK ON | Project-locked; every tool uses this unchanged |
| `novel.models.shared` | internal | NotFoundResponse, ValidationFailure | Project-locked; all tools return these |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `json` (stdlib) | stdlib | Serialize narrative_functions, sensory_profile to TEXT for SQLite | Any tool writing a JSON-column field |
| `logging` (stdlib) | stdlib | logger.debug() for not-found, logger.error() on DB exceptions | Every tool module |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Small Pydantic model for ChapterPlan | TypedDict | Both work; Pydantic is consistent with rest of codebase and auto-serializes via FastMCP |
| ON CONFLICT(id) DO UPDATE | Raw UPDATE then SELECT | ON CONFLICT is simpler and atomic; raw UPDATE loses the insert-or-update branch |

**Installation:** No new packages needed. All dependencies are already in pyproject.toml.

## Architecture Patterns

### Module Structure (matches Phase 3 exactly)
```
src/novel/tools/
├── __init__.py         (exists)
├── characters.py       (Phase 3 — done)
├── relationships.py    (Phase 3 — done)
├── chapters.py         (Phase 4 — NEW)
├── scenes.py           (Phase 4 — NEW)
├── world.py            (Phase 4 — NEW)
└── magic.py            (Phase 4 — NEW)
```

### Pattern 1: Standard Tool Module Structure
**What:** Every tool module defines a single `register(mcp: FastMCP) -> None` function. All tools are local async functions decorated with `@mcp.tool()` inside register().
**When to use:** Every new tool module, no exceptions.
**Example:**
```python
# Source: src/novel/tools/characters.py (Phase 3)
import logging
from mcp.server.fastmcp import FastMCP
from novel.mcp.db import get_connection
from novel.models.chapters import Chapter
from novel.models.shared import NotFoundResponse, ValidationFailure

logger = logging.getLogger(__name__)

def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def get_chapter(chapter_id: int) -> Chapter | NotFoundResponse:
        async with get_connection() as conn:
            row = await conn.execute_fetchall(
                "SELECT * FROM chapters WHERE id = ?", (chapter_id,)
            )
            if not row:
                return NotFoundResponse(not_found_message=f"Chapter {chapter_id} not found")
            return Chapter(**dict(row[0]))
```

### Pattern 2: Upsert with None-id Creates, Provided-id Updates
**What:** Same two-branch INSERT pattern as upsert_character. None id → INSERT without id (AUTOINCREMENT fires), cursor.lastrowid for new id. Provided id → INSERT ... ON CONFLICT(id) DO UPDATE SET all fields.
**When to use:** upsert_chapter, upsert_scene, upsert_location (these have no natural unique key other than id for locations — or use the declared UNIQUE constraint).

**Conflict targets by table:**
| Table | UNIQUE Constraint | ON CONFLICT Target |
|-------|------------------|--------------------|
| chapters | UNIQUE(book_id, chapter_number) | ON CONFLICT(book_id, chapter_number) |
| scenes | UNIQUE(chapter_id, scene_number) | ON CONFLICT(chapter_id, scene_number) |
| scene_character_goals | UNIQUE(scene_id, character_id) | ON CONFLICT(scene_id, character_id) |
| factions | UNIQUE(name) | ON CONFLICT(name) |
| locations | no UNIQUE other than PK | ON CONFLICT(id) — use id-based two-branch pattern |

**Example (upsert with natural key — scenes pattern):**
```python
# Source: derived from src/novel/tools/characters.py upsert_relationship pattern
async def upsert_scene(
    scene_id: int | None,
    chapter_id: int,
    scene_number: int,
    # ... other fields ...
) -> Scene | ValidationFailure:
    async with get_connection() as conn:
        try:
            if scene_id is None:
                cursor = await conn.execute(
                    "INSERT INTO scenes (chapter_id, scene_number, ...) VALUES (?, ?, ...)",
                    (chapter_id, scene_number, ...),
                )
                new_id = cursor.lastrowid
                await conn.commit()
                row = await conn.execute_fetchall("SELECT * FROM scenes WHERE id = ?", (new_id,))
            else:
                await conn.execute(
                    """INSERT INTO scenes (id, chapter_id, scene_number, ...)
                       VALUES (?, ?, ?, ...)
                       ON CONFLICT(id) DO UPDATE SET
                           chapter_id=excluded.chapter_id,
                           scene_number=excluded.scene_number,
                           ...,
                           updated_at=datetime('now')""",
                    (scene_id, chapter_id, scene_number, ...),
                )
                await conn.commit()
                row = await conn.execute_fetchall("SELECT * FROM scenes WHERE id = ?", (scene_id,))
        except Exception as exc:
            logger.error("upsert_scene failed: %s", exc)
            return ValidationFailure(is_valid=False, errors=[str(exc)])
        return Scene(**dict(row[0]))
```

### Pattern 3: JSON Column Serialization (narrative_functions, sensory_profile)
**What:** Scene.narrative_functions and Location.sensory_profile are stored as TEXT JSON in SQLite. On read, the field_validator on each Pydantic model handles coercion automatically. On write, call `to_db_dict()` to get the JSON-serialized dict before passing to SQL.
**When to use:** Any INSERT/UPDATE on scenes (narrative_functions) or locations (sensory_profile).

```python
# Source: src/novel/models/scenes.py
scene = Scene(chapter_id=1, scene_number=1, narrative_functions=["setup", "tension"])
db_data = scene.to_db_dict()
# db_data["narrative_functions"] == '["setup", "tension"]'  (string, not list)

# On write — use to_db_dict():
await conn.execute(
    "INSERT INTO scenes (..., narrative_functions, ...) VALUES (..., ?, ...)",
    (..., db_data["narrative_functions"], ...),
)

# On read — Chapter(**dict(row[0])) handles JSON parsing automatically via field_validator
```

### Pattern 4: Log Tool (append-only INSERT, no conflict resolution)
**What:** log_magic_use inserts a new row every call — no upsert, no conflict target. Pattern matches log_character_knowledge from Phase 3. Returns the newly created record.
**When to use:** log_magic_use (WRLD-07).

```python
# Source: derived from src/novel/tools/characters.py log_character_knowledge
async def log_magic_use(
    chapter_id: int,
    character_id: int,
    magic_element_id: int | None,
    action_description: str,
    scene_id: int | None = None,
    cost_paid: str | None = None,
    compliance_status: str = "compliant",
    notes: str | None = None,
) -> MagicUseLog | NotFoundResponse | ValidationFailure:
    async with get_connection() as conn:
        # Verify chapter + character exist first
        exists = await conn.execute_fetchall("SELECT id FROM chapters WHERE id = ?", (chapter_id,))
        if not exists:
            return NotFoundResponse(not_found_message=f"Chapter {chapter_id} not found")
        try:
            cursor = await conn.execute(
                """INSERT INTO magic_use_log
                   (chapter_id, scene_id, character_id, magic_element_id,
                    action_description, cost_paid, compliance_status, notes, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))""",
                (chapter_id, scene_id, character_id, magic_element_id,
                 action_description, cost_paid, compliance_status, notes),
            )
            await conn.commit()
            new_id = cursor.lastrowid
            row = await conn.execute_fetchall("SELECT * FROM magic_use_log WHERE id = ?", (new_id,))
            return MagicUseLog(**dict(row[0]))
        except Exception as exc:
            logger.error("log_magic_use failed: %s", exc)
            return ValidationFailure(is_valid=False, errors=[str(exc)])
```

### Pattern 5: Synthesis Tool — check_magic_compliance (NEW in Phase 4)
**What:** Two-query read-only tool. Queries magic_system_elements for rules/limitations/costs, queries practitioner_abilities for character ability registration. Derives compliance and returns a structured Pydantic model or dict. Does NOT write to magic_use_log.
**When to use:** Only for check_magic_compliance (WRLD-08).

```python
# No direct precedent in Phase 3 — this is new territory
# Define a small Pydantic response model in magic.py or in models/shared.py

from pydantic import BaseModel

class MagicComplianceResult(BaseModel):
    compliant: bool
    violations: list[str]
    applicable_rules: list[str]
    character_has_ability: bool | None  # None = ability not relevant for this element_type

@mcp.tool()
async def check_magic_compliance(
    character_id: int,
    magic_element_id: int,
    action_description: str,
) -> MagicComplianceResult | NotFoundResponse:
    async with get_connection() as conn:
        element_rows = await conn.execute_fetchall(
            "SELECT * FROM magic_system_elements WHERE id = ?", (magic_element_id,)
        )
        if not element_rows:
            return NotFoundResponse(not_found_message=f"MagicSystemElement {magic_element_id} not found")
        element = element_rows[0]

        ability_rows = await conn.execute_fetchall(
            "SELECT * FROM practitioner_abilities WHERE character_id = ? AND magic_element_id = ?",
            (character_id, magic_element_id),
        )
        character_has_ability = bool(ability_rows) if ability_rows is not None else None

        # Collect applicable rules
        applicable_rules = []
        if element["rules"]:
            applicable_rules.append(element["rules"])
        if element["limitations"]:
            applicable_rules.append(element["limitations"])
        if element["costs"]:
            applicable_rules.append(element["costs"])

        # Derive violations — currently structural (ability check)
        violations = []
        if character_has_ability is False:
            violations.append(
                f"Character {character_id} has no registered ability for element {magic_element_id}"
            )

        compliant = len(violations) == 0 and (character_has_ability is True or character_has_ability is None)
        return MagicComplianceResult(
            compliant=compliant,
            violations=violations,
            applicable_rules=applicable_rules,
            character_has_ability=character_has_ability,
        )
```

### Pattern 6: Focused Subset Response (get_chapter_plan — CHAP-02)
**What:** Same table as get_chapter but returns a narrow subset of fields as a small Pydantic model. No join required — just SELECT specific columns or SELECT * and construct from partial fields.
**When to use:** get_chapter_plan only.

```python
class ChapterPlan(BaseModel):
    """Writing-focused subset returned by get_chapter_plan."""
    chapter_id: int
    summary: str | None
    opening_state: str | None
    closing_state: str | None
    opening_hook_note: str | None
    closing_hook_note: str | None
    structural_function: str | None
    hook_strength_rating: int | None

@mcp.tool()
async def get_chapter_plan(chapter_id: int) -> ChapterPlan | NotFoundResponse:
    async with get_connection() as conn:
        row = await conn.execute_fetchall(
            "SELECT * FROM chapters WHERE id = ?", (chapter_id,)
        )
        if not row:
            return NotFoundResponse(not_found_message=f"Chapter {chapter_id} not found")
        r = dict(row[0])
        return ChapterPlan(
            chapter_id=r["id"],
            summary=r["summary"],
            opening_state=r["opening_state"],
            closing_state=r["closing_state"],
            opening_hook_note=r["opening_hook_note"],
            closing_hook_note=r["closing_hook_note"],
            structural_function=r["structural_function"],
            hook_strength_rating=r["hook_strength_rating"],
        )
```

### server.py Wiring (Plan 3 or 4)
```python
# src/novel/mcp/server.py — add 4 lines after Phase 3 imports/calls
from novel.tools import characters, relationships, chapters, scenes, world, magic

characters.register(mcp)
relationships.register(mcp)
chapters.register(mcp)
scenes.register(mcp)
world.register(mcp)
magic.register(mcp)
```

### Anti-Patterns to Avoid
- **Using print() anywhere in tool modules:** Corrupts stdio protocol. Always use `logger.debug()` or `logger.error()`.
- **Raising exceptions instead of returning error types:** Always return NotFoundResponse or ValidationFailure. Never raise.
- **Writing narrative_functions or sensory_profile as raw Python objects:** Must call `to_db_dict()` before INSERT. SQLite stores TEXT, not Python lists/dicts.
- **Importing mcp globally in tool modules:** The FastMCP instance is always passed via register(mcp). Never import `mcp` from server in a tool module.
- **Writing to faction_political_states in upsert_faction:** faction_political_states is a separate time-stamped log table. upsert_faction only writes to the factions table.
- **Using INSERT OR REPLACE on tables with FK children:** Use ON CONFLICT DO UPDATE instead. INSERT OR REPLACE deletes the old row (breaking FK children). Phase 3 documented this for upsert_relationship — apply same discipline here.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| JSON TEXT column coercion | Custom parse logic in tool handler | `field_validator` on Pydantic model + `to_db_dict()` | Already implemented on Scene and Location models — reuse it |
| Async SQLite connection | Direct aiosqlite.connect() calls | `get_connection()` async context manager from novel.mcp.db | Sets WAL + FK ON on every connection; essential |
| MagicComplianceResult shape | ad-hoc dict return | Small Pydantic model (MagicComplianceResult) | FastMCP serializes Pydantic models cleanly; dict serialization is less predictable |
| Checking both chapter and scene exist for log_magic_use | Custom existence check per log tool | Reuse the FK constraint — catch IntegrityError in the except block | FK check is enforced by SQLite when PRAGMA foreign_keys=ON is set; existence check before INSERT is optional but follows the established pattern for user-facing error messages |

**Key insight:** All the plumbing (connection management, FK enforcement, JSON coercion, error contract) is already implemented. Phase 4 is purely tool authoring on top of an established foundation.

## Common Pitfalls

### Pitfall 1: Forgetting to_db_dict() on Scene and Location Writes
**What goes wrong:** INSERT stores `narrative_functions` as Python list repr (e.g., `"['setup', 'tension']"`) instead of valid JSON. json.loads() then fails on read, crashing the field_validator.
**Why it happens:** Model looks like a plain dict but has a JSON TEXT column that needs explicit serialization.
**How to avoid:** Always call `scene.to_db_dict()` or `location.to_db_dict()` before extracting field values for INSERT/UPDATE. Never use `model.model_dump()` directly for these tables.
**Warning signs:** Tests fail with `json.JSONDecodeError` when reading back a row that was just written.

### Pitfall 2: check_magic_compliance Returning Incorrect `compliant` Value
**What goes wrong:** `compliant` is `True` even though character lacks the ability, because the None/False distinction is muddled.
**Why it happens:** `ability_rows` is an empty list (falsy) but may be confused with None or with "ability concept not applicable."
**How to avoid:** `character_has_ability = bool(ability_rows)` where True=has ability, False=no ability registered. `compliant = len(violations) == 0 and character_has_ability`. The `character_has_ability: bool | None` field in the return is `None` only when the element type does not require practitioner registration (implementation decision can treat False as "registered but absent" and None as "N/A").
**Warning signs:** check_magic_compliance returns `{compliant: true}` for a character with no practitioner_abilities row.

### Pitfall 3: upsert_scene Writing narrative_functions with Wrong Conflict Target
**What goes wrong:** ON CONFLICT(id) instead of ON CONFLICT(chapter_id, scene_number) for scenes — or vice versa. The wrong conflict target causes either silent duplicate inserts or a SQLite "no such conflict target" error.
**Why it happens:** Tables have different UNIQUE constraints. Not all use id as the conflict target.
**How to avoid:** Refer to the conflict targets table in Architecture Patterns above. scenes uses UNIQUE(chapter_id, scene_number). The two-branch pattern (None id → fresh INSERT, provided id → ON CONFLICT(id) DO UPDATE) is always safe if you use the id branch correctly.
**Warning signs:** Two calls to upsert_scene with the same chapter_id/scene_number create two rows instead of updating one.

### Pitfall 4: get_faction_political_state Returning Wrong Row
**What goes wrong:** Returns any political state row for the faction, not the most recent one, leading to stale data.
**Why it happens:** faction_political_states has UNIQUE(faction_id, chapter_id) so multiple rows can exist for one faction (one per chapter). The tool should return the row for a specific chapter or the latest by chapter_id.
**How to avoid:** get_faction_political_state should accept `faction_id` and optionally `chapter_id`. If no chapter_id: return most recent row (`ORDER BY chapter_id DESC LIMIT 1`). If chapter_id provided: return that specific row.
**Warning signs:** Tests fail because the returned row doesn't match the seed's chapter_id=1 entry.

### Pitfall 5: upsert_scene_goal Using Wrong Conflict Resolution
**What goes wrong:** INSERT OR REPLACE instead of ON CONFLICT DO UPDATE for scene_character_goals — breaks FK child rows if any exist.
**Why it happens:** INSERT OR REPLACE deletes the old row before inserting the new one, which would cascade-delete any referencing rows.
**How to avoid:** Always use ON CONFLICT(scene_id, character_id) DO UPDATE SET ... for scene_character_goals.
**Warning signs:** FK violation errors or phantom row deletion in tests.

### Pitfall 6: list_chapters Returning All Books' Chapters
**What goes wrong:** `list_chapters` returns chapters from all books rather than filtering by `book_id`.
**Why it happens:** The chapters table has rows for multiple books; without a WHERE clause, all are returned.
**How to avoid:** `list_chapters(book_id: int)` with `WHERE book_id = ?`. The seed has two books (id=1 and id=2); book 1 has 3 chapters.
**Warning signs:** list_chapters returns 3+ chapters when seed only puts 3 in book 1.

## Code Examples

Verified patterns from official sources:

### get_character_obligations (get_chapter_obligations pattern)
```python
# Source: derived from src/novel/tools/characters.py get_character_injuries
@mcp.tool()
async def get_chapter_obligations(chapter_id: int) -> list[ChapterStructuralObligation] | NotFoundResponse:
    async with get_connection() as conn:
        exists = await conn.execute_fetchall("SELECT id FROM chapters WHERE id = ?", (chapter_id,))
        if not exists:
            return NotFoundResponse(not_found_message=f"Chapter {chapter_id} not found")
        rows = await conn.execute_fetchall(
            "SELECT * FROM chapter_structural_obligations WHERE chapter_id = ? ORDER BY id",
            (chapter_id,),
        )
        return [ChapterStructuralObligation(**dict(row)) for row in rows]
```

### list_chapters with book_id filter
```python
# Source: derived from src/novel/tools/characters.py list_characters
@mcp.tool()
async def list_chapters(book_id: int) -> list[Chapter]:
    async with get_connection() as conn:
        rows = await conn.execute_fetchall(
            "SELECT * FROM chapters WHERE book_id = ? ORDER BY chapter_number",
            (book_id,),
        )
        return [Chapter(**dict(row)) for row in rows]
```

### get_scene (JSON field auto-coercion)
```python
# Source: derived from get_character; JSON coercion handled by Scene.field_validator
@mcp.tool()
async def get_scene(scene_id: int) -> Scene | NotFoundResponse:
    async with get_connection() as conn:
        row = await conn.execute_fetchall("SELECT * FROM scenes WHERE id = ?", (scene_id,))
        if not row:
            return NotFoundResponse(not_found_message=f"Scene {scene_id} not found")
        return Scene(**dict(row[0]))  # field_validator parses narrative_functions JSON automatically
```

### Test pattern for this phase
```python
# Source: src/novel/tests/test_characters.py + test_relationships.py (Phase 3)
# Session-scoped DB fixture per test file (use unique tmp dir name per file):
@pytest.fixture(scope="session")
def test_db_path(tmp_path_factory):
    db_file = tmp_path_factory.mktemp("chap_db") / "test_chaps.db"
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

async def test_get_chapter_found(test_db_path):
    result = await _call_tool(test_db_path, "get_chapter", {"chapter_id": 1})
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["chapter_number"] == 1
    assert data["title"] == "The Last Ember Watch"
```

## Seed Data Reference

The minimal seed provides the following test data for Phase 4 tools:

| Domain | Table | Seed IDs | Notes |
|--------|-------|----------|-------|
| chapters | chapters | id=1,2,3; book_id=1; act_id=1 | chapter 1 = "The Last Ember Watch", pov=char 1 |
| scenes | scenes | id=1–6; 2 per chapter | scene 1,2 in ch1; 3,4 in ch2; 5,6 in ch3 |
| scene_goals | scene_character_goals | 1 row: scene_id=1, character_id=1 | goal, obstacle, outcome populated |
| chapter_obligations | chapter_structural_obligations | 1 row: chapter_id=1, type="setup" | description populated |
| locations | locations | id=1 — "The Ashen Citadel" | sensory_profile JSON with 4 keys |
| factions | factions | id=1 — "The Obsidian Court" | leader_character_id=2 (antagonist) |
| faction_political | faction_political_states | 1 row: faction_id=1, chapter_id=1, power_level=8 | |
| cultures | cultures | id=1 — "Kaelthari" | |
| magic_elements | magic_system_elements | id=1 — "Ember-Binding" | rules, limitations, costs populated |
| practitioner | practitioner_abilities | 1 row: character_id=1, magic_element_id=1, proficiency=3 | |
| magic_log | magic_use_log | 1 row: chapter_id=1, scene_id=1, char_id=1, element_id=1 | compliance_status="compliant" |

**Key test constants** (use these in tests, not magic numbers):
- `chapter_id=1` — seeded chapter with full metadata
- `scene_id=1` — seeded scene in chapter 1 with character goal
- `location_id=1` — seeded location with sensory_profile
- `faction_id=1` — seeded faction with political state
- `culture_id=1` — seeded culture
- `magic_element_id=1` — seeded magic element with rules/limitations/costs
- `character_id=1` — protagonist; has practitioner ability for element 1
- `character_id=9999` — use for not-found tests

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Register tools at module level | register(mcp: FastMCP) -> None pattern | Phase 3 | Enables in-memory testing without global server import |
| INSERT OR REPLACE for upserts | ON CONFLICT DO UPDATE | Phase 3 | Preserves FK child rows |
| Direct aiosqlite.connect() in tools | get_connection() context manager | Phase 1/3 | WAL + FK ON set on every connection |
| cursor.lastrowid on Connection | cursor.lastrowid on cursor from execute() | Phase 3 | aiosqlite.Connection does not expose lastrowid |

**Deprecated/outdated:**
- Standalone `fastmcp` PyPI package: Do not use. Use `mcp.server.fastmcp` from the bundled SDK.

## Open Questions

1. **ChapterPlan response model location**
   - What we know: Needs to be a small Pydantic model; could live in models/chapters.py or be defined locally in tools/chapters.py
   - What's unclear: Convention preference — models/ vs tools/
   - Recommendation: Define ChapterPlan in `models/chapters.py` alongside Chapter and ChapterStructuralObligation. Keeps models co-located, avoids circular imports.

2. **MagicComplianceResult model location**
   - What we know: Needed only by check_magic_compliance in tools/magic.py
   - What's unclear: Whether it belongs in models/magic.py or models/shared.py or tools/magic.py locally
   - Recommendation: Define in `models/magic.py` alongside MagicSystemElement, MagicUseLog, PractitionerAbility. Consistent with ChapterPlan placement above.

3. **get_faction_political_state chapter_id parameter**
   - What we know: faction_political_states has UNIQUE(faction_id, chapter_id) — multiple rows per faction, one per chapter
   - What's unclear: Does WRLD-03 expect the latest state (no chapter_id arg) or a specific chapter's state?
   - Recommendation: Accept optional `chapter_id: int | None = None`. When None, return most recent row (ORDER BY chapter_id DESC LIMIT 1). When provided, return that exact row. Return NotFoundResponse if no rows exist for the faction. This matches the chapter-scoped pattern from get_character_injuries.

## Sources

### Primary (HIGH confidence)
- `src/novel/tools/characters.py` — canonical upsert, get, list, log patterns
- `src/novel/tools/relationships.py` — canonical ON CONFLICT DO UPDATE, NotFoundResponse patterns
- `src/novel/models/chapters.py` — Chapter and ChapterStructuralObligation field definitions
- `src/novel/models/scenes.py` — Scene with narrative_functions JSON field_validator and to_db_dict()
- `src/novel/models/world.py` — Location with sensory_profile JSON; Faction; Culture; FactionPoliticalState
- `src/novel/models/magic.py` — MagicSystemElement, MagicUseLog, PractitionerAbility field definitions
- `src/novel/models/shared.py` — NotFoundResponse, ValidationFailure, GateViolation
- `src/novel/migrations/008_chapters.sql` — chapters table schema with UNIQUE(book_id, chapter_number)
- `src/novel/migrations/009_scenes.sql` — scenes table schema with UNIQUE(chapter_id, scene_number)
- `src/novel/migrations/011_magic.sql` — magic_system_elements table schema
- `src/novel/migrations/016_plot_threads.sql` — chapter_structural_obligations table schema
- `src/novel/migrations/018_scene_pacing.sql` — scene_character_goals with UNIQUE(scene_id, character_id)
- `src/novel/migrations/021_literary_publishing.sql` — faction_political_states, magic_use_log, practitioner_abilities schemas
- `src/novel/db/seed.py` — complete seed data: exact IDs and field values for all test assertions
- `tests/test_characters.py` — canonical Phase 4 test structure (session-scoped DB, _call_tool helper, per-test MCP session)
- `src/novel/mcp/server.py` — current register call sequence; where to add 4 new calls
- `.planning/config.json` — nyquist_validation: false (no validation section needed)

### Secondary (MEDIUM confidence)
- `.planning/STATE.md` accumulated decisions — Phase 03-02: ON CONFLICT DO UPDATE over INSERT OR REPLACE for FK-parented tables; Phase 03-03: MCP session per-test not per-fixture

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries are project-locked, already installed, already in use
- Architecture: HIGH — direct inspection of Phase 3 source code; patterns are concrete and verified
- Pitfalls: HIGH — most pitfalls derived from actual Phase 3 decisions recorded in STATE.md and confirmed by code inspection
- check_magic_compliance: MEDIUM — logic is correct per CONTEXT.md spec, but synthesis pattern is new in this codebase

**Research date:** 2026-03-07
**Valid until:** Stable — research validity tied to codebase, not external ecosystem changes
