# Phase 2: Pydantic Models & Seed Data - Context

**Gathered:** 2026-03-07
**Status:** Ready for planning

<domain>
## Phase Boundary

Typed Pydantic v2 models for all 14 narrative domains plus shared error contract types (NotFoundResponse, ValidationFailure, GateViolation). A minimal seed profile that populates every domain table with representative data. Schema validation tests that catch model-to-migration drift. The gate-ready seed profile (SEED-02) is explicitly out of scope — that's Phase 6.

</domain>

<decisions>
## Implementation Decisions

### Seed Data Content
- Named fantasy content — invented plausible fantasy names not tied to actual manuscript (not "Character 1" fixtures, not real novel characters)
- Richer than the minimum: 2 books, 5+ characters, 3+ chapters (not just the SEED-01 floor of 1 book/2-3 characters/1 chapter)
- Seed data lives as Python dicts in `src/novel/db/seed.py` — inline structures, no separate JSON/SQL files
- Populates every domain table with at least 1 representative row so every MCP tool has something to return

### JSON Field Handling
- SQLite TEXT columns storing JSON are parsed to native Python types in Pydantic models: `List[str]`, `dict`, `Optional[dict]`, etc.
- Use specific types where the schema intent is known (e.g., `tags TEXT` → `List[str]`, `sensory_details TEXT` → `dict | None`)
- Every model that has JSON fields includes a `.to_db_dict()` method that serializes back to TEXT-encoded JSON for SQLite INSERTs/UPDATEs
- Nullable/optional columns use `str | None = None` syntax (Python 3.10+ union syntax, consistent with 3.12 target)

### Model File Organization
- One file per domain under `src/novel/models/`: `characters.py`, `world.py`, `chapters.py`, `plot.py`, `arcs.py`, `voice.py`, `sessions.py`, `timeline.py`, `canon.py`, `gate.py`, `publishing.py`, `magic.py`, `relationships.py`, `pacing.py` (14 files)
- Shared error contract types in `src/novel/models/shared.py`: `NotFoundResponse`, `ValidationFailure`, `GateViolation`
- `src/novel/models/__init__.py` re-exports all models for convenience (`from novel.models import Character, Scene, etc.`)
- Junction/state tables get their own Pydantic models (e.g., `CharacterKnowledge`, `CharacterInjury`, `CharacterBelief`) rather than being embedded in parent models

### Claude's Discretion
- Exact Pydantic field validators and model_validators for JSON parsing
- Test runner configuration (pytest setup.cfg or pyproject.toml)
- Exact split of models within domain files (some domains have many related tables)

</decisions>

<specifics>
## Specific Ideas

- Seed data should feel like a real fantasy world in miniature — named characters with roles, named places with descriptions, a plausible book structure
- No specific novel references — invent names that feel epic-fantasy appropriate
- The `.to_db_dict()` pattern should be consistent across all models that need it (not ad hoc per tool)

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/novel/db/seed.py`: Stub `load_seed_profile(conn, profile)` raises ValueError — Phase 2 implements this with the actual profile data
- `src/novel/db/connection.py`: `get_connection()` sync context manager — seed loader uses this pattern
- `src/novel/models/__init__.py`: Empty placeholder, ready to be populated with re-exports
- All 21 migration files: Definitive schema source for model field derivation

### Established Patterns
- Nullable FK pattern: `factions.leader_character_id` and `acts.start_chapter_id` are nullable — corresponding Pydantic fields should be `int | None = None`
- Boolean pattern: `INTEGER NOT NULL DEFAULT 0` columns map to `bool` in Pydantic (Pydantic v2 coerces 0/1 to False/True)
- Timestamp pattern: All entity tables have `created_at` and `updated_at` as `TEXT NOT NULL DEFAULT (datetime('now'))` — models use `str` or `datetime`
- `str | None = None` nullable syntax established in this phase for all future phases

### Integration Points
- `novel.db.seed.load_seed_profile` is already wired into `novel db seed` CLI command (Phase 1) — Phase 2 just fills in the function body
- Phase 3+ MCP tools: `from novel.models import Character, Scene, ...` — the `__init__.py` re-export pattern must be in place before Phase 3

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 02-pydantic-models-seed-data*
*Context gathered: 2026-03-07*
