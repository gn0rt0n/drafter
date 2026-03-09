# Phase 9: Names, Voice & Publishing - Context

**Gathered:** 2026-03-07
**Status:** Ready for planning

<domain>
## Phase Boundary

14 MCP tools across 3 sub-domains: Name registry (4 tools — conflict check, registration, full registry, cultural suggestions), Voice profiles (5 tools — get/upsert voice profiles, supernatural guidelines, log/retrieve voice drift), and Publishing assets (5 tools — get/upsert publishing assets, get/log/update submissions). All tools call check_gate() at the top. Server.py wiring for all 3 modules in the final plan. No CLI subcommands in this phase — name CLI is Phase 10.

</domain>

<decisions>
## Implementation Decisions

### Module organization
- Three separate tool files following established domain separation pattern: `src/novel/tools/names.py`, `src/novel/tools/voice.py`, `src/novel/tools/publishing.py`
- All models already exist: `NameRegistryEntry` in `src/novel/models/magic.py`; `VoiceProfile`, `VoiceDriftLog`, `SupernaturalVoiceGuideline` in `src/novel/models/voice.py`; `PublishingAsset`, `SubmissionEntry` in `src/novel/models/publishing.py`
- No new models required

### Name conflict detection — case-insensitive exact match
- `check_name(name)` queries `SELECT * FROM name_registry WHERE LOWER(name) = LOWER(?)` — case-insensitive exact match only
- No fuzzy/phonetic matching — the name_registry UNIQUE constraint is case-sensitive; tool extends it with case folding
- Returns the conflicting `NameRegistryEntry` if found, `null` (NotFoundResponse) if safe to use
- No `check_gate()` on names tools — name checking is useful during worldbuilding (pre-gate) AND during prose

### Name registry — gate-free
- All 4 name tools (`check_name`, `register_name`, `get_name_registry`, `generate_name_suggestions`) do NOT call `check_gate()`
- Rationale: name conflict checking and registration are worldbuilding operations that must work before the gate is certified; gating them would block legitimate pre-prose use
- This is the only tool domain in this phase that is gate-free (voice and publishing are prose-phase)

### generate_name_suggestions — data retrieval, not AI generation
- Takes `culture_id` (or `faction_id` via join) as required parameter
- Queries `name_registry WHERE culture_id = ?` to return existing names for that culture
- Also fetches `cultures.naming_conventions` or equivalent linguistic notes from the cultures table
- Returns: list of existing `NameRegistryEntry` records for the culture + the culture's linguistic context
- Claude uses this data to generate consistent new names — the tool itself does not generate names
- If no culture_id match: return empty list + null linguistic context (not an error)

### register_name — append-only INSERT
- Inserts into `name_registry`; returns inserted `NameRegistryEntry`
- Raises conflict (returns `ValidationFailure`) if name already exists (UNIQUE constraint)
- Caller should use `check_name` first to avoid conflicts

### get_name_registry — full registry, optional filters
- Returns all `NameRegistryEntry` records; accepts optional `entity_type` filter and optional `culture_id` filter
- Ordered by `name ASC`

### Voice tools — gated
- All 5 voice tools (`get_voice_profile`, `upsert_voice_profile`, `get_supernatural_voice_guidelines`, `log_voice_drift`, `get_voice_drift_log`) call `check_gate()` at the top
- `get_voice_profile(character_id)` — returns `VoiceProfile` or `NotFoundResponse`
- `upsert_voice_profile` — two-branch: None-id INSERT + lastrowid; provided-id ON CONFLICT(character_id) DO UPDATE (character_id is UNIQUE in voice_profiles)
- `get_supernatural_voice_guidelines()` — returns all `SupernaturalVoiceGuideline` rows; no required filter
- `log_voice_drift` — append-only INSERT; returns inserted `VoiceDriftLog` — consistent with all other `log_*` tools; `is_resolved` field exists in schema but no resolve tool in Phase 9 requirements
- `get_voice_drift_log(character_id)` — returns list of `VoiceDriftLog` for that character; ordered by `created_at DESC`

### Publishing tools — gated
- All 5 publishing tools call `check_gate()` at the top
- `get_publishing_assets(asset_type=None)` — returns list of `PublishingAsset`; optional `asset_type` filter (query_letter/synopsis/pitch); ordered by `created_at DESC`
- `upsert_publishing_asset` — two-branch: None-id INSERT + lastrowid; provided-id ON CONFLICT(id) DO UPDATE
- `get_submissions(status=None)` — returns list of `SubmissionEntry`; optional `status` filter (pending/accepted/rejected/withdrawn); ordered by `submitted_at DESC`
- `log_submission` — append-only INSERT into `submission_tracker`; returns inserted `SubmissionEntry`
- `update_submission(id, status, response_at=None, response_notes=None, follow_up_due=None)` — partial UPDATE; only updates provided fields + `updated_at`; returns updated `SubmissionEntry` or `NotFoundResponse`

### Plan split (3 plans)
- **09-01**: Names domain — `src/novel/tools/names.py` with all 4 name tools (check_name, register_name, get_name_registry, generate_name_suggestions); gate-free
- **09-02**: Voice domain — `src/novel/tools/voice.py` with all 5 voice tools (get_voice_profile, upsert_voice_profile, get_supernatural_voice_guidelines, log_voice_drift, get_voice_drift_log)
- **09-03**: Publishing domain — `src/novel/tools/publishing.py` with all 5 publishing tools + server.py wiring for all 3 modules + in-memory FastMCP tests for all 14 tools

### Claude's Discretion
- Exact SQL for all queries
- conftest.py extension for name/voice/publishing seed data
- Whether `generate_name_suggestions` joins to cultures table or relies solely on name_registry.culture_id filter
- Fixture scope and test helpers
- Error handling for UNIQUE constraint violations on register_name

</decisions>

<specifics>
## Specific Ideas

No specific requirements — user delegated all implementation decisions to Claude. Follow established patterns from Phases 3–8.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `novel.models.magic.NameRegistryEntry`: Ready to use — id, name, entity_type, culture_id, linguistic_notes, introduced_chapter_id, notes, created_at
- `novel.models.voice.VoiceProfile`: Ready — character_id UNIQUE, full voice fields, canon_status
- `novel.models.voice.VoiceDriftLog`: Ready — character_id, drift_type, severity, is_resolved
- `novel.models.voice.SupernaturalVoiceGuideline`: Ready — element_name, element_type, writing_rules, avoid, example_phrases
- `novel.models.publishing.PublishingAsset`: Ready — asset_type, title, content, version, status
- `novel.models.publishing.SubmissionEntry`: Ready — asset_id FK, agency_or_publisher, submitted_at, status, response fields
- `novel.mcp.gate.check_gate(conn)` — import and call at top of voice/publishing tools (NOT name tools)
- `novel.mcp.db.get_connection()` — async context manager; WAL + FK pragmas already set
- `novel.models.shared`: `NotFoundResponse`, `ValidationFailure`, `GateViolation` — error contract types

### Established Patterns
- `register(mcp: FastMCP) -> None` with local async functions decorated with `@mcp.tool()`
- Append-only INSERT for all `log_*` tools — no ON CONFLICT
- Upsert two-branch pattern for profile/state tools
- `NotFoundResponse` for missing single records, empty list for missing collections
- No `print()` — `logging.getLogger(__name__)` only
- Cursor.lastrowid for INSERT row ID (aiosqlite)
- FastMCP serializes `list[T]` as N TextContent blocks — tests use `[json.loads(c.text) for c in result.content]`
- MCP session entered per-test (not per-fixture) — anyio cancel scope teardown issue

### Integration Points
- `server.py`: add `from novel.tools import names, voice, publishing; names.register(mcp); voice.register(mcp); publishing.register(mcp)` in 09-03
- Create `src/novel/tools/names.py`, `src/novel/tools/voice.py`, `src/novel/tools/publishing.py` (new files)
- `tests/`: add `test_names.py`, `test_voice.py`, `test_publishing.py` in 09-03

### Schema Notes
- `name_registry` (migration 021): id, name UNIQUE, entity_type, culture_id→cultures(id), linguistic_notes, introduced_chapter_id→chapters(id), notes, created_at
- `voice_profiles` (migration 014): id, character_id UNIQUE, all voice fields, canon_status, created_at, updated_at
- `voice_drift_log` (migration 014): id, character_id, chapter_id, scene_id, drift_type, description, severity, is_resolved, created_at
- `supernatural_voice_guidelines` (migration 021): id, element_name, element_type, writing_rules, avoid, example_phrases, notes, created_at, updated_at
- `publishing_assets` (migration 021): id, asset_type, title, content, version, status, notes, created_at, updated_at
- `submission_tracker` (migration 021): id, asset_id→publishing_assets(id), agency_or_publisher, submitted_at, status, response_at, response_notes, follow_up_due, notes, created_at, updated_at

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 09-names-voice-publishing*
*Context gathered: 2026-03-07*
