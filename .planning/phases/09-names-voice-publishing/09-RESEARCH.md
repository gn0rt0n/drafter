# Phase 9: Names, Voice & Publishing - Research

**Researched:** 2026-03-07
**Domain:** FastMCP tool implementation — three new domains (names, voice, publishing) following the established Phase 3–8 pattern
**Confidence:** HIGH — all models exist, schema verified against migrations, patterns confirmed from 6 prior phases

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Module organization:**
- Three separate tool files: `src/novel/tools/names.py`, `src/novel/tools/voice.py`, `src/novel/tools/publishing.py`
- All models already exist — no new models required
- `NameRegistryEntry` in `src/novel/models/magic.py`; `VoiceProfile`, `VoiceDriftLog`, `SupernaturalVoiceGuideline` in `src/novel/models/voice.py`; `PublishingAsset`, `SubmissionEntry` in `src/novel/models/publishing.py`

**Name conflict detection:**
- `check_name(name)` uses `SELECT * FROM name_registry WHERE LOWER(name) = LOWER(?)` — case-insensitive exact match only
- No fuzzy/phonetic matching
- Returns conflicting `NameRegistryEntry` if found, `NotFoundResponse` if safe to use

**Name tools — gate-free:**
- All 4 name tools (`check_name`, `register_name`, `get_name_registry`, `generate_name_suggestions`) do NOT call `check_gate()`
- This is the only gate-free domain in this phase

**generate_name_suggestions — data retrieval, not AI generation:**
- Takes `culture_id` as required parameter
- Queries `name_registry WHERE culture_id = ?` returning existing names for that culture
- Also fetches `cultures.naming_conventions` from cultures table
- Returns: list of existing `NameRegistryEntry` records + culture's linguistic context
- If no match: return empty list + null linguistic context (not an error)

**register_name — append-only INSERT:**
- Inserts into `name_registry`; returns inserted `NameRegistryEntry`
- Raises conflict — returns `ValidationFailure` if name already exists (UNIQUE constraint)
- Caller should use `check_name` first

**get_name_registry — full registry with optional filters:**
- Returns all `NameRegistryEntry` records; optional `entity_type` and `culture_id` filters
- Ordered by `name ASC`

**Voice tools — gated:**
- All 5 tools call `check_gate()` at top
- `upsert_voice_profile` — two-branch: None-id INSERT + lastrowid; provided-id ON CONFLICT(character_id) DO UPDATE
- `log_voice_drift` — append-only INSERT; `is_resolved` field exists in schema but no resolve tool in Phase 9
- `get_voice_drift_log(character_id)` — ordered by `created_at DESC`

**Publishing tools — gated:**
- All 5 tools call `check_gate()` at top
- `upsert_publishing_asset` — two-branch: None-id INSERT + lastrowid; provided-id ON CONFLICT(id) DO UPDATE
- `update_submission` — partial UPDATE; only updates provided fields + `updated_at`; returns updated `SubmissionEntry` or `NotFoundResponse`

**Plan split (3 plans):**
- **09-01**: Names domain — `src/novel/tools/names.py` with 4 name tools (gate-free)
- **09-02**: Voice domain — `src/novel/tools/voice.py` with 5 voice tools
- **09-03**: Publishing domain — `src/novel/tools/publishing.py` with 5 publishing tools + server.py wiring for all 3 modules + in-memory FastMCP tests for all 14 tools

### Claude's Discretion
- Exact SQL for all queries
- conftest.py extension for name/voice/publishing seed data
- Whether `generate_name_suggestions` joins to cultures table or relies solely on name_registry.culture_id filter
- Fixture scope and test helpers
- Error handling for UNIQUE constraint violations on register_name

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| NAME-01 | Claude can check whether a proposed name conflicts with existing names in the registry (`check_name`) | Case-insensitive LOWER() query on name_registry UNIQUE column; returns NameRegistryEntry or NotFoundResponse |
| NAME-02 | Claude can register a name in the registry with its cultural/linguistic context (`register_name`) | Append-only INSERT; UNIQUE constraint on name column handles duplicates; return ValidationFailure on IntegrityError |
| NAME-03 | Claude can retrieve the full name registry (`get_name_registry`) | SELECT with optional WHERE filters on entity_type and culture_id; ORDER BY name ASC |
| NAME-04 | Claude can get name suggestions following cultural/linguistic rules (`generate_name_suggestions`) | Query name_registry by culture_id + JOIN/SELECT cultures.naming_conventions; returns NameRegistryEntry list + linguistic context string |
| VOIC-01 | Claude can retrieve a character's voice profile (`get_voice_profile`) | SELECT from voice_profiles WHERE character_id = ?; returns VoiceProfile or NotFoundResponse; gated |
| VOIC-02 | Claude can retrieve supernatural voice guidelines (`get_supernatural_voice_guidelines`) | SELECT * from supernatural_voice_guidelines; returns list[SupernaturalVoiceGuideline]; gated |
| VOIC-03 | Claude can log a voice drift instance (`log_voice_drift`) | Append-only INSERT into voice_drift_log; returns VoiceDriftLog; gated |
| VOIC-04 | Claude can retrieve the voice drift log for a character (`get_voice_drift_log`) | SELECT WHERE character_id = ? ORDER BY created_at DESC; returns list[VoiceDriftLog]; gated |
| VOIC-05 | Claude can create or update a voice profile (`upsert_voice_profile`) | Two-branch upsert on voice_profiles; character_id UNIQUE; gated |
| PUBL-01 | Claude can retrieve publishing assets (`get_publishing_assets`) | SELECT with optional asset_type filter ORDER BY created_at DESC; returns list[PublishingAsset]; gated |
| PUBL-02 | Claude can create or update a publishing asset (`upsert_publishing_asset`) | Two-branch upsert on publishing_assets by id; gated |
| PUBL-03 | Claude can retrieve submission tracker entries (`get_submissions`) | SELECT with optional status filter ORDER BY submitted_at DESC; returns list[SubmissionEntry]; gated |
| PUBL-04 | Claude can log a new submission (`log_submission`) | Append-only INSERT into submission_tracker; returns SubmissionEntry; gated |
| PUBL-05 | Claude can update a submission's status (`update_submission`) | Partial UPDATE on submission_tracker; only updates provided fields; returns SubmissionEntry or NotFoundResponse; gated |
</phase_requirements>

---

## Summary

Phase 9 implements 14 new MCP tools across three domains: Names (4, gate-free), Voice (5, gated), and Publishing (5, gated). Every pattern in this phase is a direct application of patterns established in Phases 3–8 — no new technical territory is introduced. The phase splits into three sequenced plans: names first (simple, gate-free), voice second (upsert + append-only log), publishing third (upsert + append-only log + partial update + server.py wiring + full test suite).

The key architectural distinction is that name tools are gate-free — they serve worldbuilding operations that must work before the gate is certified. Voice and publishing tools are prose-phase tools gated by `check_gate()`. All models are verified against their migration files and already exist in the codebase.

The only area of genuine complexity is `generate_name_suggestions`, which combines two data sources (name_registry rows + cultures.naming_conventions text), and `update_submission`, which requires a partial UPDATE pattern not used in other Phase 9 tools. Both patterns have clear precedents in the codebase.

**Primary recommendation:** Implement in plan order (09-01 names, 09-02 voice, 09-03 publishing + tests). Use the foreshadowing/canon module as the direct template — they represent the most recent established patterns.

---

## Standard Stack

### Core (all already installed)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `mcp.server.fastmcp` | bundled with `mcp>=1.26.0,<2.0.0` | MCP server + tool registration | Project decision — NOT standalone fastmcp PyPI package |
| `aiosqlite` | current | Async SQLite connections in tool handlers | get_connection() returns aiosqlite.Connection |
| `pydantic` | v2 (>=2.11) | All model classes returned by tools | All 6 models already defined, v2 syntax throughout |

### No New Dependencies
Phase 9 requires zero new package installations. All required libraries are already in `pyproject.toml` and installed.

---

## Architecture Patterns

### Recommended Project Structure (additions only)
```
src/novel/tools/
├── names.py         # NEW — 09-01 — 4 name tools (gate-free)
├── voice.py         # NEW — 09-02 — 5 voice tools (gated)
├── publishing.py    # NEW — 09-03 — 5 publishing tools (gated)
└── [existing 13 modules unchanged]

tests/
├── test_names.py    # NEW — 09-03
├── test_voice.py    # NEW — 09-03
└── test_publishing.py  # NEW — 09-03
```

### Pattern 1: Gate-Free Tool Module (names domain)
**What:** Tool module where no tools call `check_gate()` — all 4 name tools are worldbuilding-phase tools.
**When to use:** Only for domains that must work before gate certification (names, worldbuilding data).
**Example:**
```python
# Source: established in Phases 3–4 (characters, world) — confirmed pattern
from novel.mcp.db import get_connection
from novel.models.magic import NameRegistryEntry
from novel.models.shared import NotFoundResponse, ValidationFailure
# NO: from novel.mcp.gate import check_gate  -- intentionally omitted for names

def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def check_name(name: str) -> NameRegistryEntry | NotFoundResponse:
        async with get_connection() as conn:
            # No check_gate() call
            async with conn.execute(
                "SELECT * FROM name_registry WHERE LOWER(name) = LOWER(?)",
                (name,),
            ) as cursor:
                row = await cursor.fetchone()
            if row is None:
                return NotFoundResponse(not_found_message=f"Name '{name}' is not in the registry — safe to use")
            return NameRegistryEntry(**dict(row))
```

### Pattern 2: Gated Tool Module (voice and publishing domains)
**What:** Tool module where every tool calls `check_gate(conn)` before any DB logic.
**When to use:** All prose-phase domains (Phase 7+).
**Example:**
```python
# Source: canon.py, foreshadowing.py — Phase 8 (most recent template)
from novel.mcp.gate import check_gate

def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def get_voice_profile(character_id: int) -> VoiceProfile | NotFoundResponse | GateViolation:
        async with get_connection() as conn:
            gate = await check_gate(conn)
            if gate is not None:
                return gate
            async with conn.execute(
                "SELECT * FROM voice_profiles WHERE character_id = ?",
                (character_id,),
            ) as cursor:
                row = await cursor.fetchone()
            if row is None:
                return NotFoundResponse(not_found_message=f"No voice profile for character {character_id}")
            return VoiceProfile(**dict(row))
```

### Pattern 3: Two-Branch Upsert (voice_profiles, publishing_assets)
**What:** None-id → INSERT + lastrowid; provided-id → INSERT ON CONFLICT DO UPDATE; always SELECT back.
**When to use:** All "profile/state" tools — upsert_voice_profile, upsert_publishing_asset.
**Example:**
```python
# Source: foreshadowing.py log_foreshadowing (Phase 08-03) — confirmed working
async def upsert_voice_profile(
    character_id: int,
    profile_id: int | None = None,
    sentence_length: str | None = None,
    # ... other fields
) -> VoiceProfile | GateViolation:
    async with get_connection() as conn:
        gate = await check_gate(conn)
        if gate is not None:
            return gate

        if profile_id is None:
            cursor = await conn.execute(
                "INSERT INTO voice_profiles (character_id, sentence_length, ...) VALUES (?, ?, ...)",
                (character_id, sentence_length, ...),
            )
            new_id = cursor.lastrowid
        else:
            await conn.execute(
                """INSERT INTO voice_profiles (id, character_id, sentence_length, ...)
                   VALUES (?, ?, ?, ...)
                   ON CONFLICT(character_id) DO UPDATE SET
                       sentence_length=excluded.sentence_length,
                       ...,
                       updated_at=datetime('now')""",
                (profile_id, character_id, sentence_length, ...),
            )
            new_id = profile_id

        await conn.commit()
        async with conn.execute("SELECT * FROM voice_profiles WHERE id = ?", (new_id,)) as cur:
            row = await cur.fetchone()
        return VoiceProfile(**dict(row))
```

### Pattern 4: Append-Only INSERT (log_voice_drift, log_submission)
**What:** Plain INSERT, no ON CONFLICT — each call creates a new immutable record.
**When to use:** All `log_*` tools — voice drift, submissions.
**Example:**
```python
# Source: log_motif_occurrence (foreshadowing.py), log_canon_fact (canon.py)
cursor = await conn.execute(
    "INSERT INTO voice_drift_log (character_id, chapter_id, scene_id, drift_type, description, severity) "
    "VALUES (?, ?, ?, ?, ?, ?)",
    (character_id, chapter_id, scene_id, drift_type, description, severity),
)
new_id = cursor.lastrowid
await conn.commit()
async with conn.execute("SELECT * FROM voice_drift_log WHERE id = ?", (new_id,)) as cur:
    row = await cur.fetchone()
return VoiceDriftLog(**dict(row))
```

### Pattern 5: Partial UPDATE (update_submission)
**What:** Build SET clause dynamically — only include provided fields. Check SELECT-back for NotFoundResponse.
**When to use:** `update_submission` — the only partial UPDATE tool in this phase.
**Example:**
```python
# Source: resolve_continuity_issue (canon.py) for the SELECT-back after UPDATE pattern
# Phase 9 extends this with dynamic field inclusion
async def update_submission(
    submission_id: int,
    status: str,
    response_at: str | None = None,
    response_notes: str | None = None,
    follow_up_due: str | None = None,
) -> SubmissionEntry | NotFoundResponse | GateViolation:
    async with get_connection() as conn:
        gate = await check_gate(conn)
        if gate is not None:
            return gate

        # Build partial SET clause
        fields = {"status": status, "updated_at": "datetime('now')"}
        if response_at is not None:
            fields["response_at"] = response_at
        if response_notes is not None:
            fields["response_notes"] = response_notes
        if follow_up_due is not None:
            fields["follow_up_due"] = follow_up_due

        # Separate literal SQL expressions from parameterized values
        set_parts = []
        params = []
        for col, val in fields.items():
            if col == "updated_at":
                set_parts.append(f"{col}=datetime('now')")
            else:
                set_parts.append(f"{col}=?")
                params.append(val)
        params.append(submission_id)

        await conn.execute(
            f"UPDATE submission_tracker SET {', '.join(set_parts)} WHERE id = ?",
            params,
        )
        await conn.commit()

        async with conn.execute("SELECT * FROM submission_tracker WHERE id = ?", (submission_id,)) as cur:
            row = await cur.fetchone()
        if row is None:
            return NotFoundResponse(not_found_message=f"Submission {submission_id} not found")
        return SubmissionEntry(**dict(row))
```

### Pattern 6: generate_name_suggestions — dual-source query
**What:** Fetch existing names for a culture from name_registry AND fetch naming_conventions from cultures.
**When to use:** Only for `generate_name_suggestions` (NAME-04).
**Example:**
```python
# Two separate queries — simpler than JOIN for the discrete return structure
async def generate_name_suggestions(culture_id: int) -> dict | GateViolation:
    # Note: gate-FREE — no check_gate call
    async with get_connection() as conn:
        # Existing names for this culture
        async with conn.execute(
            "SELECT * FROM name_registry WHERE culture_id = ? ORDER BY name ASC",
            (culture_id,),
        ) as cursor:
            name_rows = await cursor.fetchall()

        # Culture linguistic context
        async with conn.execute(
            "SELECT naming_conventions FROM cultures WHERE id = ?",
            (culture_id,),
        ) as cursor:
            culture_row = await cursor.fetchone()

        existing_names = [NameRegistryEntry(**dict(r)) for r in name_rows]
        linguistic_context = culture_row["naming_conventions"] if culture_row else None

        return {
            "existing_names": existing_names,
            "linguistic_context": linguistic_context,
            "culture_id": culture_id,
        }
```

**Note on return type:** Because `generate_name_suggestions` returns a heterogeneous dict (list of NameRegistryEntry + a string field), the return type annotation cannot use a single Pydantic model without a new wrapper. Options at Claude's discretion:
1. Return a `dict` with two keys — FastMCP serializes as one TextContent block
2. Define a thin inline `NameSuggestionsResult(BaseModel)` in names.py directly (not in models/) — keeps models/ clean
3. Return two separate calls — but that contradicts the single-tool design

Option 2 (inline result model in names.py) is recommended for clean type annotations and test assertions.

### Pattern 7: UNIQUE Constraint Handling for register_name
**What:** Catch `aiosqlite.IntegrityError` (wraps `sqlite3.IntegrityError`) and return `ValidationFailure`.
**When to use:** `register_name` — name column has a UNIQUE constraint in name_registry.
**Example:**
```python
# Source: Phase 03-02 decision — use ON CONFLICT semantics for tables with FK children
# For name_registry (no FK children), catching IntegrityError is simpler and cleaner
import aiosqlite

try:
    cursor = await conn.execute(
        "INSERT INTO name_registry (name, entity_type, culture_id, linguistic_notes, ...) "
        "VALUES (?, ?, ?, ?, ...)",
        (name, entity_type, culture_id, linguistic_notes, ...),
    )
    new_id = cursor.lastrowid
    await conn.commit()
except aiosqlite.IntegrityError:
    return ValidationFailure(
        is_valid=False,
        errors=[f"Name '{name}' already exists in the registry. Use check_name to verify before registering."],
    )
```

### Anti-Patterns to Avoid
- **print() anywhere in tool modules:** Corrupts stdio protocol. Use `logger = logging.getLogger(__name__)` exclusively.
- **check_gate() in name tools:** Intentionally omitted. Adding it blocks legitimate worldbuilding use.
- **INSERT OR REPLACE for upsert:** Deletes the row and re-inserts, breaking FK children. Use `ON CONFLICT DO UPDATE` instead.
- **Assuming UPDATE affected a row:** SQLite UPDATE does not error on missing rows. Always SELECT back after UPDATE to detect missing IDs (see `resolve_continuity_issue` pattern in canon.py).
- **Global mcp import:** The `mcp` object is always the one passed into `register(mcp: FastMCP)` — never imported globally.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Async SQLite connection | Custom connection pool | `novel.mcp.db.get_connection()` | WAL + FK pragmas already set; reuse established context manager |
| Gate certification check | Manual SQL query | `novel.mcp.gate.check_gate(conn)` | Established helper — consistent GateViolation contract |
| Error response models | Custom dicts | `NotFoundResponse`, `ValidationFailure`, `GateViolation` from `novel.models.shared` | Error contract established in Phase 3 — TEST-03 validates compliance |
| Domain models | New Pydantic models | Existing models in magic.py, voice.py, publishing.py | All 6 models verified against migration SQL |
| MCP test client | Custom client setup | `create_connected_server_and_client_session(mcp)` from `mcp.shared.memory` | Standard in-memory FastMCP test pattern used in all Phase 3–8 tests |

**Key insight:** Every building block for Phase 9 already exists. The work is wiring them together following established patterns — not building new infrastructure.

---

## Common Pitfalls

### Pitfall 1: check_gate() in name tools
**What goes wrong:** Adding `check_gate()` to name tools blocks worldbuilding operations that must work before gate certification.
**Why it happens:** Copying the gated tool template without reading the CONTEXT.md gate-free decision.
**How to avoid:** The `names.py` module deliberately omits `from novel.mcp.gate import check_gate` entirely.
**Warning signs:** A `check_gate()` call anywhere in `names.py`.

### Pitfall 2: UNIQUE constraint handling for register_name
**What goes wrong:** Plain INSERT raises `aiosqlite.IntegrityError` if name already exists, which propagates as an unhandled exception to the MCP caller — violating the error contract (ERRC-01/02).
**Why it happens:** Forgetting to wrap INSERT in try/except for UNIQUE-constrained tables.
**How to avoid:** Wrap INSERT in `try/except aiosqlite.IntegrityError` and return `ValidationFailure`. Remind caller to use `check_name` first.
**Warning signs:** No try/except block around the INSERT in `register_name`.

### Pitfall 3: Partial UPDATE without SELECT-back
**What goes wrong:** `update_submission` calls UPDATE but does not SELECT back, so it cannot detect a missing submission_id — returns a fabricated object instead of `NotFoundResponse`.
**Why it happens:** Assuming UPDATE raises an error when the WHERE clause matches zero rows (it doesn't in SQLite).
**How to avoid:** Always SELECT back after UPDATE and check `row is None` → return `NotFoundResponse`. Confirmed pattern from Phase 08-01 (`resolve_continuity_issue`).
**Warning signs:** `update_submission` does not have a SELECT-back after the UPDATE.

### Pitfall 4: upsert_voice_profile using wrong UNIQUE column
**What goes wrong:** The ON CONFLICT clause targets the wrong column — voice_profiles has `UNIQUE(character_id)` not `UNIQUE(id)`.
**Why it happens:** Confusion about whether to conflict on `id` (PK) or `character_id` (domain UNIQUE).
**How to avoid:** Migration 014 confirms `character_id INTEGER NOT NULL UNIQUE`. The ON CONFLICT clause must be `ON CONFLICT(character_id) DO UPDATE`.
**Warning signs:** ON CONFLICT targeting `id` in voice_profiles upsert.

### Pitfall 5: generate_name_suggestions — None culture_id in name_registry rows
**What goes wrong:** Filtering `WHERE culture_id = ?` returns nothing if all names have `culture_id = NULL`, even if rows exist.
**Why it happens:** SQLite NULL semantics — `NULL = 1` is false; `NULL IS NULL` is true. If seed names have NULL culture_id, the filter returns empty.
**How to avoid:** Seed conftest.py for test_names.py must insert at least one name_registry row with a non-null `culture_id` matching the test culture. Tests use the gate_ready seed which may or may not have this — conftest extension needed.
**Warning signs:** test_generate_name_suggestions getting an empty list when it should have results.

### Pitfall 6: server.py wiring — import order
**What goes wrong:** Importing names/voice/publishing before the modules exist causes ImportError when running the test suite for earlier plans (09-01, 09-02).
**Why it happens:** Adding all three imports to server.py in plan 09-01.
**How to avoid:** Server.py is wired in plan 09-03 only (after all three tool modules exist). Plans 09-01 and 09-02 do NOT touch server.py.
**Warning signs:** server.py import block updated before plan 09-03.

### Pitfall 7: Test isolation — names tests do NOT need gate certification
**What goes wrong:** Applying the `certified_gate` fixture (from foreshadowing tests) to test_names.py where gate-free tools are being tested.
**Why it happens:** Copy-pasting the test file structure from foreshadowing.py without adjusting for the gate-free domain.
**How to avoid:** `test_names.py` does NOT need a `certified_gate` fixture. Name tools run without gate. The fixture only applies to `test_voice.py` and `test_publishing.py`.
**Warning signs:** `certified_gate` autouse fixture in test_names.py.

---

## Code Examples

Verified from actual project source (Phases 3–8):

### Module header and register() skeleton
```python
# Source: /src/novel/tools/foreshadowing.py (Phase 08-03)
"""Names domain MCP tools.

All 4 name tools are registered via the register(mcp) function pattern.
This module is standalone — it does not modify server.py; wiring happens in
the server module.

IMPORTANT: Never use the print function in this module. All logging goes to
stderr via the logging module — using print corrupts the stdio protocol.
"""
import logging

from mcp.server.fastmcp import FastMCP

from novel.mcp.db import get_connection
from novel.models.magic import NameRegistryEntry
from novel.models.shared import NotFoundResponse, ValidationFailure

logger = logging.getLogger(__name__)


def register(mcp: FastMCP) -> None:
    """Register all 4 name domain tools with the given FastMCP instance."""

    @mcp.tool()
    async def check_name(name: str) -> NameRegistryEntry | NotFoundResponse:
        ...
```

### Conditional WHERE clause building
```python
# Source: canon.py get_decisions, foreshadowing.py get_foreshadowing (Phase 08)
conditions: list[str] = []
params: list[object] = []

if entity_type is not None:
    conditions.append("entity_type = ?")
    params.append(entity_type)
if culture_id is not None:
    conditions.append("culture_id = ?")
    params.append(culture_id)

where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
sql = f"SELECT * FROM name_registry {where_clause} ORDER BY name ASC"

async with conn.execute(sql, params) as cursor:
    rows = await cursor.fetchall()
return [NameRegistryEntry(**dict(row)) for row in rows]
```

### Test structure (gated domain — voice/publishing)
```python
# Source: tests/test_foreshadowing.py (Phase 08-03)
@pytest.fixture(scope="session")
def test_db_path(tmp_path_factory):
    db_file = tmp_path_factory.mktemp("voice_db") / "test_voice.db"
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
    if cur.fetchone()[0] == 0:
        conn.execute("INSERT INTO architecture_gate (is_certified, certified_by, certified_at) "
                     "VALUES (1, 'test-suite', datetime('now'))")
    else:
        conn.execute("UPDATE architecture_gate SET is_certified=1, certified_by='test-suite', "
                     "certified_at=datetime('now') WHERE id=1")
    conn.commit()
    conn.close()

async def _call_tool(db_path: str, tool_name: str, args: dict):
    os.environ["NOVEL_DB_PATH"] = db_path
    async with create_connected_server_and_client_session(mcp) as session:
        return await session.call_tool(tool_name, args)
```

### server.py wiring (plan 09-03)
```python
# Source: /src/novel/mcp/server.py — extend existing import block
from novel.tools import characters, relationships, chapters, scenes, world, magic, plot, arcs, gate, session, timeline, canon, knowledge, foreshadowing, names, voice, publishing

# Register domain tools — Phase 9
names.register(mcp)
voice.register(mcp)
publishing.register(mcp)
```

---

## Schema Verification

All column names verified against actual migration SQL files. This is the ground truth as established by Phase 02-01 decision.

### name_registry (migration 021)
```
id              INTEGER PK AUTOINCREMENT
name            TEXT NOT NULL UNIQUE
entity_type     TEXT NOT NULL DEFAULT 'character'
culture_id      INTEGER REFERENCES cultures(id)   -- nullable
linguistic_notes TEXT
introduced_chapter_id INTEGER REFERENCES chapters(id)  -- nullable
notes           TEXT
created_at      TEXT NOT NULL DEFAULT (datetime('now'))
```
**Note:** No `updated_at` column — `NameRegistryEntry.created_at` only.

### voice_profiles (migration 014)
```
id                    INTEGER PK AUTOINCREMENT
character_id          INTEGER NOT NULL UNIQUE REFERENCES characters(id)
sentence_length       TEXT
vocabulary_level      TEXT
speech_patterns       TEXT
verbal_tics           TEXT
avoids                TEXT
internal_voice_notes  TEXT
dialogue_sample       TEXT
notes                 TEXT
canon_status          TEXT NOT NULL DEFAULT 'draft'
created_at            TEXT NOT NULL DEFAULT (datetime('now'))
updated_at            TEXT NOT NULL DEFAULT (datetime('now'))
```
**UNIQUE:** `character_id` — ON CONFLICT target for upsert.

### voice_drift_log (migration 014)
```
id              INTEGER PK AUTOINCREMENT
character_id    INTEGER NOT NULL REFERENCES characters(id)
chapter_id      INTEGER REFERENCES chapters(id)    -- nullable
scene_id        INTEGER REFERENCES scenes(id)      -- nullable
drift_type      TEXT NOT NULL DEFAULT 'vocabulary'
description     TEXT NOT NULL
severity        TEXT NOT NULL DEFAULT 'minor'
is_resolved     INTEGER NOT NULL DEFAULT 0
created_at      TEXT NOT NULL DEFAULT (datetime('now'))
```
**Note:** No `updated_at` column. `is_resolved` exists but no Phase 9 resolve tool.

### supernatural_voice_guidelines (migration 021)
```
id              INTEGER PK AUTOINCREMENT
element_name    TEXT NOT NULL UNIQUE
element_type    TEXT NOT NULL DEFAULT 'creature'
writing_rules   TEXT NOT NULL
avoid           TEXT
example_phrases TEXT
notes           TEXT
created_at      TEXT NOT NULL DEFAULT (datetime('now'))
updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
```

### publishing_assets (migration 021)
```
id              INTEGER PK AUTOINCREMENT
asset_type      TEXT NOT NULL DEFAULT 'query_letter'
title           TEXT NOT NULL
content         TEXT NOT NULL
version         INTEGER NOT NULL DEFAULT 1
status          TEXT NOT NULL DEFAULT 'draft'
notes           TEXT
created_at      TEXT NOT NULL DEFAULT (datetime('now'))
updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
```
**Note:** No UNIQUE constraint beyond PK — ON CONFLICT(id) for upsert.

### submission_tracker (migration 021)
```
id                    INTEGER PK AUTOINCREMENT
asset_id              INTEGER REFERENCES publishing_assets(id)  -- nullable
agency_or_publisher   TEXT NOT NULL
submitted_at          TEXT NOT NULL
status                TEXT NOT NULL DEFAULT 'pending'
response_at           TEXT
response_notes        TEXT
follow_up_due         TEXT
notes                 TEXT
created_at            TEXT NOT NULL DEFAULT (datetime('now'))
updated_at            TEXT NOT NULL DEFAULT (datetime('now'))
```

### cultures (migration 004) — relevant for generate_name_suggestions
```
naming_conventions   TEXT   -- the field returned as linguistic_context
```

---

## Seed Data Notes for Tests

The `gate_ready` seed (used in voice and publishing tests) and `minimal` seed (candidate for names tests) both have:
- `culture_id = 1` (Kaelthari culture, naming_conventions = "Compound names — first syllable denotes caste, final syllable denotes lineage.")
- Characters with `id` values 1–5 (protagonist=1, antagonist=2, mentor=3, ally=4, rival=5)
- Chapters with `id` values 1–3
- Scenes with `id` values in chapters 1–3

**Neither seed currently populates:**
- `name_registry` — test_names.py conftest must INSERT at least 2 rows: one with `culture_id=1` for generate_name_suggestions, one with a different name for conflict detection
- `voice_profiles` — test_voice.py conftest must INSERT at least 1 row (for get_voice_profile); upsert_voice_profile test can create one
- `supernatural_voice_guidelines` — conftest INSERT needed for get_supernatural_voice_guidelines to return non-empty list
- `voice_drift_log` — log_voice_drift tests create rows; get_voice_drift_log needs at least 1 pre-existing row
- `publishing_assets` — conftest INSERT needed for get_publishing_assets
- `submission_tracker` — conftest INSERT needed for get_submissions and update_submission

The `09-03` plan must either extend conftest.py with Phase 9 seed data or use per-test raw sqlite3 inserts (following the Phase 05 pattern of in-test raw inserts for missing seed data). Extending conftest.py with a separate session-scoped fixture per test file is the cleaner approach.

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Global mcp import | `register(mcp: FastMCP)` closure pattern | Phase 03-01 | Tools use locally passed mcp, not global state |
| INSERT OR REPLACE | ON CONFLICT DO UPDATE / two-branch upsert | Phase 03-02 | FK children preserved |
| Fixture-scoped MCP session | Per-test `_call_tool()` with session open/close | Phase 03-03 | anyio cancel scope teardown fixed |
| Synchronous DB in tests | Synchronous sqlite3 for gate cert fixture | Phase 07-03 | Avoids async fixture lifecycle issues |
| Single source of truth | Migration SQL files (not plan prose, not model docstrings) | Phase 02-01 | Column names verified against .sql files |

---

## Open Questions

1. **Return type for generate_name_suggestions**
   - What we know: Returns two distinct types — `list[NameRegistryEntry]` and a `str | None` linguistic context — that cannot be expressed as a single Pydantic model without a wrapper
   - What's unclear: Whether to use a dict return, an inline result model in names.py, or some other approach
   - Recommendation: Define `NameSuggestionsResult(BaseModel)` inline in `names.py` with `existing_names: list[NameRegistryEntry]`, `linguistic_context: str | None`, `culture_id: int`. This gives clean type annotations, testable field access, and avoids adding to the models/ directory for a projection type.

2. **Test seed data strategy for test_names.py**
   - What we know: Neither minimal nor gate_ready seed populates name_registry
   - What's unclear: Whether to use raw per-test sqlite3 inserts or a dedicated fixture
   - Recommendation: Add a session-scoped `_insert_name_seed(test_db_path)` fixture in test_names.py that inserts 2–3 name_registry rows directly. This keeps the conftest.py file clean and avoids modifying the shared seed profiles.

3. **Minimal seed vs gate_ready seed for test_names.py**
   - What we know: Name tools are gate-free — they do not require a certified gate
   - What's unclear: Whether to use minimal or gate_ready seed for the names test fixture
   - Recommendation: Use `gate_ready` seed for consistency — all Phase 8 tests use it, and it provides the richer world data (cultures with naming_conventions populated). The gate certification fixture is simply not added to test_names.py.

---

## Sources

### Primary (HIGH confidence)
- `/src/novel/migrations/014_voice.sql` — confirmed voice_profiles and voice_drift_log schema (column names, UNIQUE constraints)
- `/src/novel/migrations/021_literary_publishing.sql` — confirmed name_registry, supernatural_voice_guidelines, publishing_assets, submission_tracker schema
- `/src/novel/migrations/004_cultures.sql` — confirmed cultures.naming_conventions column exists
- `/src/novel/models/magic.py` — confirmed NameRegistryEntry fields
- `/src/novel/models/voice.py` — confirmed VoiceProfile, VoiceDriftLog, SupernaturalVoiceGuideline fields
- `/src/novel/models/publishing.py` — confirmed PublishingAsset, SubmissionEntry fields
- `/src/novel/tools/foreshadowing.py` — confirmed tool registration pattern, upsert two-branch, append-only log, list serialization
- `/src/novel/tools/canon.py` — confirmed conditional WHERE pattern, append-only INSERT, SELECT-back after UPDATE for NotFoundResponse
- `/src/novel/mcp/gate.py` — confirmed check_gate() signature and return contract
- `/src/novel/mcp/server.py` — confirmed import pattern for domain tool registration
- `/tests/test_foreshadowing.py` — confirmed test structure: session-scoped DB, per-test _call_tool(), certified_gate autouse fixture
- `/tests/conftest.py` — confirmed base fixture structure
- `/src/novel/db/seed.py` (preview) — confirmed culture_id=1 (Kaelthari), character IDs 1–5, chapter IDs 1–3

### Secondary (MEDIUM confidence)
- `.planning/phases/09-names-voice-publishing/09-CONTEXT.md` — user-locked implementation decisions (authoritative for this phase)
- `.planning/STATE.md` — accumulated decisions from Phases 02–08

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries already installed, no new dependencies
- Architecture patterns: HIGH — directly verified from existing Phase 3–8 source code
- Schema: HIGH — verified against actual migration SQL files (ground truth per Phase 02-01 decision)
- Pitfalls: HIGH — drawn from actual Phase 02–08 STATE.md accumulated decisions
- Seed data: MEDIUM — seed.py partially read; names/voice/publishing rows confirmed absent from seed profiles; character and culture IDs confirmed

**Research date:** 2026-03-07
**Valid until:** 2026-04-07 (stable codebase — no external dependencies changing)
