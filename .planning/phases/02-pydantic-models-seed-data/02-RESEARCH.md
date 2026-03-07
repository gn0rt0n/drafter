# Phase 2: Pydantic Models & Seed Data - Research

**Researched:** 2026-03-07
**Domain:** Pydantic v2 models, SQLite schema introspection, seed data loading, pytest schema validation
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Seed data content**
- Named fantasy content — invented plausible fantasy names not tied to actual manuscript (not "Character 1" fixtures, not real novel characters)
- Richer than the minimum: 2 books, 5+ characters, 3+ chapters (not just the SEED-01 floor of 1 book/2-3 characters/1 chapter)
- Seed data lives as Python dicts in `src/novel/db/seed.py` — inline structures, no separate JSON/SQL files
- Populates every domain table with at least 1 representative row so every MCP tool has something to return

**JSON field handling**
- SQLite TEXT columns storing JSON are parsed to native Python types in Pydantic models: `List[str]`, `dict`, `Optional[dict]`, etc.
- Use specific types where the schema intent is known (e.g., `tags TEXT` → `List[str]`, `sensory_details TEXT` → `dict | None`)
- Every model that has JSON fields includes a `.to_db_dict()` method that serializes back to TEXT-encoded JSON for SQLite INSERTs/UPDATEs
- Nullable/optional columns use `str | None = None` syntax (Python 3.10+ union syntax, consistent with 3.12 target)

**Model file organization**
- One file per domain under `src/novel/models/`: `characters.py`, `world.py`, `chapters.py`, `plot.py`, `arcs.py`, `voice.py`, `sessions.py`, `timeline.py`, `canon.py`, `gate.py`, `publishing.py`, `magic.py`, `relationships.py`, `pacing.py` (14 files)
- Shared error contract types in `src/novel/models/shared.py`: `NotFoundResponse`, `ValidationFailure`, `GateViolation`
- `src/novel/models/__init__.py` re-exports all models for convenience (`from novel.models import Character, Scene, etc.`)
- Junction/state tables get their own Pydantic models (e.g., `CharacterKnowledge`, `CharacterInjury`, `CharacterBelief`) rather than being embedded in parent models

### Claude's Discretion

- Exact Pydantic field validators and model_validators for JSON parsing
- Test runner configuration (pytest setup.cfg or pyproject.toml)
- Exact split of models within domain files (some domains have many related tables)

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| SEED-01 | Minimal seed profile provides enough data to exercise every MCP domain (1 book min, 2-3 characters, 1 chapter, 2 scenes, 1 session, representative entries in each domain) | Insertion order for all 68 tables derived from FK dependency graph; all 46 core domain tables identified |
| SEED-03 | `novel db seed [profile]` CLI command loads a named seed profile | Existing `load_seed_profile` stub in `src/novel/db/seed.py` is already wired to `novel db seed` command — Phase 2 fills in the function body |
| TEST-01 | Schema validation test compares Pydantic model fields against `PRAGMA table_info` for every domain — fails if models drift from migrations | `PRAGMA table_info(table)` returns (cid, name, type, notnull, dflt_value, pk) — verified working against live database |
| TEST-02 | Clean-rebuild test runs `novel db migrate` from scratch, validates all FK constraints with `PRAGMA foreign_key_check`, and confirms all seed data inserts cleanly with `PRAGMA foreign_keys=ON` | `PRAGMA foreign_key_check` returns zero rows when no violations — verified working; in-memory seed insertion verified with FK enforcement ON |
</phase_requirements>

---

## Summary

Phase 2 has three parallel work streams: (1) defining Pydantic v2 models for all 14 domains plus shared error types, (2) implementing the `minimal` seed profile in `seed.py`, and (3) writing pytest tests that validate schema-model alignment and clean-rebuild FK integrity.

The Pydantic work is largely mechanical — each migration file maps directly to one or more model classes. The non-trivial parts are: handling JSON TEXT columns via `@field_validator(mode='before')` with JSON parsing, implementing `.to_db_dict()` on models that have JSON fields, and deciding which of the 68 tables belong in which of the 14 domain files (12 tables were left unassigned in CONTEXT.md and need to be distributed). The migrations are the ground truth — every model field name must match the corresponding SQL column name exactly.

The seed data work is also largely mechanical but requires careful insertion ordering. FK constraints are enforced at DML time when `PRAGMA foreign_keys=ON` is set. The correct order is: eras → books → cultures → factions → characters → acts → locations → chapters → scenes → (all other tables). The seed loader must insert data in this exact dependency order.

The test work is straightforward: `PRAGMA table_info(table)` gives column names; the schema validation test compares these against `model.model_fields` keys. `PRAGMA foreign_key_check` returns rows only when there are FK violations — zero rows means clean.

**Primary recommendation:** Write models first (Wave 1, can parallelize per-domain), then seed data (Wave 2, single file), then tests (Wave 3, two test files). Models must exist before seed data can be written against them, and both must exist before tests can verify them.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pydantic | 2.12.5 (installed) | Data validation, model definitions | Project decision (Pydantic v2); already installed via `mcp>=1.26.0` dependency |
| pytest | >=8.x | Test runner | Standard Python testing; already in `[tool.pytest.ini_options]` in pyproject.toml with `testpaths = ["tests"]` |
| sqlite3 | stdlib | Schema introspection in tests | `PRAGMA table_info()` and `PRAGMA foreign_key_check` are stdlib operations |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| json | stdlib | JSON serialization in `to_db_dict()` and `@field_validator` | All models with JSON TEXT columns |
| typing | stdlib (3.12+) | `Optional`, `Union` — use `X | None` syntax instead | Only needed for pre-3.10 compatibility; this project targets 3.12, use union syntax directly |
| pydantic.field_validator | pydantic v2 | JSON TEXT → Python type coercion before validation | Models with `sensory_profile`, `narrative_functions`, `carried_forward`, `chapters_touched` |
| pydantic.model_validator | pydantic v2 | Cross-field validation if needed | Optional for Phase 2; held in reserve |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `@field_validator(mode='before')` | `model_validator(mode='before')` | field_validator is per-field (cleaner, composable); model_validator is whole-model (only needed for cross-field rules) |
| Python dict seed data | JSON files or SQL INSERT files | CONTEXT.md locked: inline Python dicts in seed.py; no external files |
| pytest only | unittest | pytest is the project standard (already configured in pyproject.toml) |

**Installation:**
```bash
uv add --dev pytest
```

Note: `pydantic` is already installed as a transitive dependency of `mcp>=1.26.0,<2.0.0` (version 2.12.5 confirmed). No additional install needed for production code.

---

## Architecture Patterns

### Recommended Project Structure for Phase 2

```
src/novel/
├── models/
│   ├── __init__.py          # re-exports all models
│   ├── shared.py            # NotFoundResponse, ValidationFailure, GateViolation
│   ├── characters.py        # Character, CharacterKnowledge, CharacterBelief,
│   │                        # CharacterLocation, InjuryState, TitleState, CharacterArc
│   ├── relationships.py     # CharacterRelationship, RelationshipChangeEvent, PerceptionProfile
│   ├── world.py             # Book, Era, Act, Culture, Faction, Location, Artifact,
│   │                        # ObjectState, FactionPoliticalState
│   ├── chapters.py          # Chapter, ChapterStructuralObligation
│   ├── scenes.py            # Scene, SceneCharacterGoal
│   ├── plot.py              # PlotThread, ChapterPlotThread, ChapterCharacterArc
│   ├── arcs.py              # CharacterArc, ArcHealthLog, ChekhovGun, SubplotTouchpoint
│   ├── voice.py             # VoiceProfile, VoiceDriftLog, SupernaturalVoiceGuideline
│   ├── sessions.py          # SessionLog, AgentRunLog, ProjectMetricsSnapshot,
│   │                        # PovBalanceSnapshot, OpenQuestion, DecisionsLog
│   ├── timeline.py          # Event, EventParticipant, EventArtifact, TravelSegment,
│   │                        # PovChronologicalPosition
│   ├── canon.py             # CanonFact, ContinuityIssue, ForeshadowingEntry,
│   │                        # ProphecyEntry, MotifEntry, MotifOccurrence,
│   │                        # ThematicMirror, OppositionPair, ReaderInformationState,
│   │                        # ReaderReveal, DramaticIronyEntry, ReaderExperienceNote
│   ├── gate.py              # ArchitectureGate, GateChecklistItem
│   ├── publishing.py        # PublishingAsset, SubmissionEntry, ResearchNote,
│   │                        # DocumentationTask
│   ├── magic.py             # MagicSystemElement, SupernaturalElement, MagicUseLog,
│   │                        # PractitionerAbility, NameRegistryEntry
│   └── pacing.py            # PacingBeat, TensionMeasurement
├── db/
│   └── seed.py              # load_seed_profile() — implement 'minimal' profile
tests/
├── __init__.py
├── test_schema_validation.py  # TEST-01: model fields vs PRAGMA table_info
└── test_clean_rebuild.py      # TEST-02: migrate + FK check + seed
```

### Pattern 1: Pydantic v2 BaseModel with JSON field parsing

**What:** Model for a domain entity table. TEXT columns that store JSON are parsed by a `@field_validator(mode='before')` that handles both raw strings (from SQLite) and already-parsed types (from Python code).

**When to use:** Any model with JSON TEXT columns (`sensory_profile`, `narrative_functions`, `carried_forward`, `chapters_touched`).

```python
# Source: Pydantic v2 docs — field_validator with mode='before'
from pydantic import BaseModel, field_validator
import json


class Location(BaseModel):
    id: int | None = None
    name: str
    location_type: str | None = None
    parent_location_id: int | None = None
    culture_id: int | None = None
    controlling_faction_id: int | None = None
    description: str | None = None
    sensory_profile: dict | None = None   # JSON TEXT in SQLite
    strategic_value: str | None = None
    accessibility: str | None = None
    notable_features: str | None = None
    notes: str | None = None
    canon_status: str = "draft"
    source_file: str | None = None
    created_at: str | None = None
    updated_at: str | None = None

    @field_validator("sensory_profile", mode="before")
    @classmethod
    def parse_sensory_profile(cls, v: object) -> dict | None:
        if isinstance(v, str):
            return json.loads(v)
        return v

    def to_db_dict(self) -> dict:
        """Serialize for SQLite INSERT/UPDATE — JSON fields re-encoded to TEXT."""
        d = self.model_dump()
        if d["sensory_profile"] is not None:
            d["sensory_profile"] = json.dumps(d["sensory_profile"])
        return d
```

### Pattern 2: Simple model (no JSON fields)

**What:** Model with only scalar fields. No `@field_validator` or `to_db_dict()` needed.

**When to use:** Most models — characters, books, chapters, scenes without JSON columns.

```python
from pydantic import BaseModel


class Character(BaseModel):
    id: int | None = None
    name: str
    role: str = "supporting"
    faction_id: int | None = None
    culture_id: int | None = None
    home_era_id: int | None = None
    age: int | None = None
    physical_description: str | None = None
    personality_core: str | None = None
    backstory_summary: str | None = None
    secret: str | None = None
    motivation: str | None = None
    fear: str | None = None
    flaw: str | None = None
    strength: str | None = None
    arc_summary: str | None = None
    voice_signature: str | None = None
    notes: str | None = None
    canon_status: str = "draft"
    source_file: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    reviewed_at: str | None = None
```

### Pattern 3: Boolean fields (SQLite INTEGER 0/1)

**What:** SQLite stores booleans as INTEGER 0/1. Pydantic v2 coerces 0 → False and 1 → True automatically for `bool` fields. No validator needed.

```python
class CharacterKnowledge(BaseModel):
    id: int | None = None
    character_id: int
    chapter_id: int
    knowledge_type: str = "fact"
    content: str
    source: str | None = None
    is_secret: bool = False       # SQLite INTEGER 0/1; Pydantic v2 coerces automatically
    notes: str | None = None
    created_at: str | None = None
```

### Pattern 4: Shared error contract types (shared.py)

**What:** The three error response types used by every MCP tool. These are not tied to any database table — they are response envelopes for the error contract.

```python
# src/novel/models/shared.py
from pydantic import BaseModel


class NotFoundResponse(BaseModel):
    """Returned by MCP tools when a record is not found.

    Tools return this instead of raising an exception.
    """
    not_found_message: str


class ValidationFailure(BaseModel):
    """Returned by MCP tools on validation failure."""
    is_valid: bool = False
    errors: list[str]


class GateViolation(BaseModel):
    """Returned by prose-phase tools when the architecture gate is not certified."""
    requires_action: str
```

### Pattern 5: __init__.py re-export

**What:** `src/novel/models/__init__.py` re-exports all models so downstream code uses `from novel.models import Character` rather than `from novel.models.characters import Character`.

```python
# src/novel/models/__init__.py
from novel.models.shared import NotFoundResponse, ValidationFailure, GateViolation
from novel.models.characters import (
    Character, CharacterKnowledge, CharacterBelief,
    CharacterLocation, InjuryState, TitleState,
)
from novel.models.relationships import (
    CharacterRelationship, RelationshipChangeEvent, PerceptionProfile,
)
from novel.models.world import Book, Era, Act, Culture, Faction, Location, Artifact
# ... etc for all 14 domain files

__all__ = [
    "NotFoundResponse", "ValidationFailure", "GateViolation",
    "Character", "CharacterKnowledge", "CharacterBelief",
    # ... complete list
]
```

### Pattern 6: Seed data — insertion order

**What:** The seed loader inserts data in FK dependency order. Inserting in the wrong order with `PRAGMA foreign_keys=ON` will raise `IntegrityError: FOREIGN KEY constraint failed`.

**Correct insertion order:**
1. `eras` (no FKs)
2. `books` (no FKs)
3. `cultures` (no FKs)
4. `factions` (no FK deps on characters yet — `leader_character_id` nullable)
5. `characters` (FK: factions nullable, cultures nullable, eras nullable)
6. `acts` (FK: books; start/end chapter FKs nullable)
7. `locations` (FK: cultures, factions, locations self-ref nullable)
8. `chapters` (FK: books, acts, characters nullable for pov_character_id)
9. `scenes` (FK: chapters, locations nullable)
10. `artifacts` (FK: characters, locations, eras all nullable)
11. `magic_system_elements` (FK: chapters nullable)
12. `supernatural_elements` (FK: chapters nullable)
13. `character_relationships` (FK: characters, chapters nullable)
14. `perception_profiles` (FK: characters, chapters nullable)
15. `voice_profiles` (FK: characters)
16. `events` (FK: chapters, locations nullable)
17. `pov_chronological_position` (FK: characters, chapters)
18. `travel_segments` (FK: characters, locations, events nullable, chapters nullable)
19. `plot_threads` (FK: chapters nullable, self-ref nullable)
20. `character_arcs` (FK: characters, chapters nullable)
21. `chapter_plot_threads` (FK: chapters, plot_threads)
22. `chapter_structural_obligations` (FK: chapters)
23. `chekovs_gun_registry` (FK: chapters, scenes nullable)
24. `arc_health_log` (FK: character_arcs, chapters)
25. `scene_character_goals` (FK: scenes, characters)
26. `pacing_beats` (FK: chapters, scenes nullable)
27. `tension_measurements` (FK: chapters)
28. `session_logs` (no upstream FKs)
29. `architecture_gate` (no FKs)
30. `gate_checklist_items` (FK: architecture_gate)
31. `open_questions` (FK: session_logs nullable)
32. `decisions_log` (FK: session_logs nullable, chapters nullable)
33. `canon_facts` (FK: chapters, events nullable, self-ref nullable)
34. `foreshadowing_registry` (FK: chapters, scenes nullable)
35. `prophecy_registry` (FK: characters nullable, chapters nullable)
36. `motif_registry` (FK: chapters nullable)
37. `motif_occurrences` (FK: motif_registry, chapters, scenes nullable)
38. `reader_information_states` (FK: chapters)
39. `reader_reveals` (FK: chapters, scenes, characters — all nullable)
40. `dramatic_irony_inventory` (FK: chapters, characters nullable)
41. `faction_political_states` (FK: factions, chapters, characters nullable)
42. `practitioner_abilities` (FK: characters, magic_system_elements, chapters nullable)
43. `name_registry` (FK: cultures nullable, chapters nullable)
44. `publishing_assets` (no FKs)
45. `submission_tracker` (FK: publishing_assets nullable)
46. Remaining tables: `character_knowledge`, `character_beliefs`, `character_locations`, `injury_states`, `title_states`, `voice_drift_log`, `event_participants`, `event_artifacts`, `chapter_character_arcs`, `subplot_touchpoint_log`, `object_states`, `continuity_issues`, `opposition_pairs`, `thematic_mirrors`, `reader_experience_notes`, `research_notes`, `documentation_tasks`, `project_metrics_snapshots`, `pov_balance_snapshots`, `agent_run_log`, `magic_use_log`, `relationship_change_events`

**Seed loader pattern:**
```python
# src/novel/db/seed.py
import sqlite3
import json


MINIMAL_SEED = {
    "eras": [
        {"name": "The Age of Embers", "sequence_order": 1, "certainty_level": "established",
         "canon_status": "approved"},
    ],
    "books": [
        {"title": "The Void Between Stars", "series_order": 1, "status": "drafting",
         "word_count_target": 120000, "canon_status": "draft"},
        {"title": "The Shattered Meridian", "series_order": 2, "status": "planning",
         "word_count_target": 110000, "canon_status": "draft"},
    ],
    # ... etc
}


def load_seed_profile(conn: sqlite3.Connection, profile: str) -> None:
    profiles = {"minimal": _load_minimal}
    if profile not in profiles:
        raise ValueError(f"Unknown seed profile '{profile}'. Available: {list(profiles)}")
    profiles[profile](conn)


def _load_minimal(conn: sqlite3.Connection) -> None:
    """Insert minimal seed data in FK dependency order."""
    # Insert eras first, capture returned IDs via lastrowid
    ...
```

### Pattern 7: Schema validation test (TEST-01)

**What:** For each model class, derive the set of model field names, then compare against column names from `PRAGMA table_info`. This catches model drift from schema changes.

```python
# tests/test_schema_validation.py
import sqlite3
import pytest
from novel.models import Character, Scene, Chapter, Location  # etc.
from novel.db.connection import get_connection


TABLE_MODEL_MAP = {
    "characters": Character,
    "scenes": Scene,
    "chapters": Chapter,
    "locations": Location,
    # ... all 68 tables that have models
}


def get_table_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return {row[1] for row in rows}  # row[1] = column name


def get_model_fields(model_class) -> set[str]:
    return set(model_class.model_fields.keys())


@pytest.mark.parametrize("table,model_class", TABLE_MODEL_MAP.items())
def test_model_matches_schema(table, model_class, db_conn):
    db_cols = get_table_columns(db_conn, table)
    model_fields = get_model_fields(model_class)
    missing_from_model = db_cols - model_fields
    extra_in_model = model_fields - db_cols
    assert not missing_from_model, f"{model_class.__name__} missing fields: {missing_from_model}"
    assert not extra_in_model, f"{model_class.__name__} has extra fields: {extra_in_model}"
```

### Pattern 8: Clean-rebuild test (TEST-02)

**What:** Open in-memory SQLite, run all migrations, check FK integrity, then run seed loader and check FK integrity again.

```python
# tests/test_clean_rebuild.py
import sqlite3
from novel.db.migrations import apply_migrations
from novel.db.seed import load_seed_profile


def test_migrate_and_fk_check():
    """All migrations apply cleanly with zero FK violations."""
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys=ON")
    apply_migrations(conn)
    violations = conn.execute("PRAGMA foreign_key_check").fetchall()
    assert violations == [], f"FK violations after migrate: {violations}"


def test_seed_minimal_fk_check():
    """Minimal seed inserts cleanly with FK enforcement and has zero violations."""
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys=ON")
    apply_migrations(conn)
    load_seed_profile(conn, "minimal")
    violations = conn.execute("PRAGMA foreign_key_check").fetchall()
    assert violations == [], f"FK violations after seed: {violations}"


def test_seed_minimal_coverage():
    """Every domain table has at least 1 row after minimal seed."""
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys=ON")
    apply_migrations(conn)
    load_seed_profile(conn, "minimal")

    # Tables that must have at least 1 row
    required = [
        "books", "characters", "chapters", "scenes", "cultures", "factions",
        "locations", "events", "plot_threads", "character_arcs", "session_logs",
        "canon_facts", "voice_profiles", "magic_system_elements",
        # ... complete list
    ]
    for table in required:
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        assert count >= 1, f"Table '{table}' has 0 rows after minimal seed"
```

### Anti-Patterns to Avoid

- **Embedding model_fields in __init__ constructor manually**: Use `BaseModel` field definitions — Pydantic v2 auto-generates `__init__` from them.
- **Using `Optional[X]` from typing**: This project targets Python 3.12; use `X | None` union syntax instead.
- **Storing `id` as required field**: Always make `id: int | None = None` — models are used both for creating records (no id yet) and returning existing records.
- **Using `model.dict()` (deprecated)**: Use `model.model_dump()` in Pydantic v2. `model.dict()` still works but is deprecated and will be removed.
- **Using `Model.parse_obj()` (deprecated)**: Use `Model.model_validate()` in Pydantic v2.
- **Forgetting to call `conn.commit()` after seed inserts**: Each seed batch should be committed. With WAL mode and `PRAGMA foreign_keys=ON`, uncommitted data is not visible to other connections.
- **Inserting junction tables before their parent entities**: `chapter_plot_threads` requires both `chapters` and `plot_threads` to exist. Follow the FK dependency order strictly.
- **`to_db_dict()` serializing id=None as NULL**: SQLite will ignore `id=None` in an INSERT with the correct column list, but always exclude `id` from INSERT column lists when creating new records.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| JSON string parsing in models | Custom `__init__` parsing | `@field_validator(mode='before')` | Pydantic v2 validators handle both string and already-parsed input cleanly |
| Model field introspection | `vars(model)`, `__dict__` | `model.model_fields` | `model_fields` is the official Pydantic v2 API for schema introspection |
| Schema comparison in tests | Manual SQL result parsing | `PRAGMA table_info()` | SQLite built-in; returns (cid, name, type, notnull, dflt_value, pk) |
| FK validation in tests | Writing JOIN queries | `PRAGMA foreign_key_check` | SQLite built-in; returns one row per FK violation across all tables |
| Seed ID tracking | Manual `last_insert_rowid()` chaining | `conn.lastrowid` after `conn.execute()` | `cursor.lastrowid` after an INSERT is the canonical approach; no global state needed |

**Key insight:** All schema introspection needed for TEST-01 and TEST-02 is available via SQLite's own PRAGMA system. No third-party schema comparison libraries are needed.

---

## Complete Table-to-Model Mapping

All 68 user tables, their domain file, and their Pydantic model class name:

### characters.py
| Table | Model Class |
|-------|-------------|
| characters | Character |
| character_knowledge | CharacterKnowledge |
| character_beliefs | CharacterBelief |
| character_locations | CharacterLocation |
| injury_states | InjuryState |
| title_states | TitleState |

### relationships.py
| Table | Model Class |
|-------|-------------|
| character_relationships | CharacterRelationship |
| relationship_change_events | RelationshipChangeEvent |
| perception_profiles | PerceptionProfile |

### world.py
| Table | Model Class |
|-------|-------------|
| books | Book |
| eras | Era |
| acts | Act |
| cultures | Culture |
| factions | Faction |
| locations | Location |
| artifacts | Artifact |
| object_states | ObjectState |
| faction_political_states | FactionPoliticalState |

### chapters.py
| Table | Model Class |
|-------|-------------|
| chapters | Chapter |
| chapter_structural_obligations | ChapterStructuralObligation |

### scenes.py
| Table | Model Class |
|-------|-------------|
| scenes | Scene |
| scene_character_goals | SceneCharacterGoal |

### plot.py
| Table | Model Class |
|-------|-------------|
| plot_threads | PlotThread |
| chapter_plot_threads | ChapterPlotThread |
| chapter_character_arcs | ChapterCharacterArc |

### arcs.py
| Table | Model Class |
|-------|-------------|
| character_arcs | CharacterArc |
| arc_health_log | ArcHealthLog |
| chekovs_gun_registry | ChekhovGun |
| subplot_touchpoint_log | SubplotTouchpoint |

### voice.py
| Table | Model Class |
|-------|-------------|
| voice_profiles | VoiceProfile |
| voice_drift_log | VoiceDriftLog |
| supernatural_voice_guidelines | SupernaturalVoiceGuideline |

### sessions.py
| Table | Model Class |
|-------|-------------|
| session_logs | SessionLog |
| agent_run_log | AgentRunLog |
| project_metrics_snapshots | ProjectMetricsSnapshot |
| pov_balance_snapshots | PovBalanceSnapshot |
| open_questions | OpenQuestion |
| decisions_log | DecisionsLogEntry |

### timeline.py
| Table | Model Class |
|-------|-------------|
| events | Event |
| event_participants | EventParticipant |
| event_artifacts | EventArtifact |
| travel_segments | TravelSegment |
| pov_chronological_position | PovChronologicalPosition |

### canon.py
| Table | Model Class |
|-------|-------------|
| canon_facts | CanonFact |
| continuity_issues | ContinuityIssue |
| foreshadowing_registry | ForeshadowingEntry |
| prophecy_registry | ProphecyEntry |
| motif_registry | MotifEntry |
| motif_occurrences | MotifOccurrence |
| thematic_mirrors | ThematicMirror |
| opposition_pairs | OppositionPair |
| reader_information_states | ReaderInformationState |
| reader_reveals | ReaderReveal |
| dramatic_irony_inventory | DramaticIronyEntry |
| reader_experience_notes | ReaderExperienceNote |

### gate.py
| Table | Model Class |
|-------|-------------|
| architecture_gate | ArchitectureGate |
| gate_checklist_items | GateChecklistItem |

### publishing.py
| Table | Model Class |
|-------|-------------|
| publishing_assets | PublishingAsset |
| submission_tracker | SubmissionEntry |
| research_notes | ResearchNote |
| documentation_tasks | DocumentationTask |

### magic.py
| Table | Model Class |
|-------|-------------|
| magic_system_elements | MagicSystemElement |
| supernatural_elements | SupernaturalElement |
| magic_use_log | MagicUseLog |
| practitioner_abilities | PractitionerAbility |
| name_registry | NameRegistryEntry |

### pacing.py
| Table | Model Class |
|-------|-------------|
| pacing_beats | PacingBeat |
| tension_measurements | TensionMeasurement |

**Total: 68 tables, 68 model classes, 14 domain files + shared.py**

---

## JSON Fields Summary

These are the only TEXT columns that store JSON and require `@field_validator + to_db_dict()`:

| Table | Column | Python Type | Notes |
|-------|--------|-------------|-------|
| locations | sensory_profile | `dict \| None` | `{sight, sound, smell, touch, taste}` |
| scenes | narrative_functions | `list[str] \| None` | JSON array |
| session_logs | carried_forward | `list[str] \| None` | JSON array of carried-forward items |
| session_logs | chapters_touched | `list[int] \| None` | JSON array of chapter IDs |

All other TEXT columns are plain strings or enum values — no JSON parsing required.

---

## Common Pitfalls

### Pitfall 1: `model.dict()` vs `model.model_dump()` in Pydantic v2

**What goes wrong:** `model.dict()` works in Pydantic v2 but emits a deprecation warning and will be removed. Code written against Pydantic v1 docs uses `model.dict()`.

**Why it happens:** Pydantic v2 introduced `model_dump()` as the canonical method; `dict()` is a backward-compat alias.

**How to avoid:** Always use `model.model_dump()`. Same for `Model.parse_obj()` → `Model.model_validate()`.

**Warning signs:** `PydanticDeprecatedSince20` warnings in test output.

### Pitfall 2: `@field_validator` classmethod requirement in Pydantic v2

**What goes wrong:** In Pydantic v2, `@field_validator` functions must be decorated with `@classmethod` AND `@field_validator`. Omitting `@classmethod` raises a `PydanticUserError`.

**Why it happens:** Pydantic v1 used instance methods for validators; v2 requires class methods.

**How to avoid:**
```python
@field_validator("sensory_profile", mode="before")
@classmethod
def parse_sensory_profile(cls, v):
    if isinstance(v, str):
        return json.loads(v)
    return v
```

**Warning signs:** `PydanticUserError: A non-classmethod validator function was used` on model class definition.

### Pitfall 3: Seed insertion order FK violation

**What goes wrong:** Inserting `chapters` before `books`, or `scenes` before `chapters` with `PRAGMA foreign_keys=ON` raises `IntegrityError: FOREIGN KEY constraint failed`.

**Why it happens:** FK enforcement is DML-time, not DDL-time. The seed loader must insert parent records before child records.

**How to avoid:** Follow the FK dependency order from Pattern 6 above. Never insert a child record until its parent record exists.

**Warning signs:** `sqlite3.IntegrityError: FOREIGN KEY constraint failed` during `load_seed_profile`.

### Pitfall 4: ID capture in seed data

**What goes wrong:** Many seed records require parent IDs that were just inserted. Using hardcoded IDs (e.g., assuming `book_id = 1`) is fragile — if the seed runs on a database that already has data, the IDs will be wrong.

**Why it happens:** SQLite AUTOINCREMENT means the next ID depends on current table state.

**How to avoid:** After each INSERT, capture the ID via `cursor.lastrowid`:
```python
cursor = conn.execute("INSERT INTO books (title) VALUES (?)", ("The Void Between Stars",))
book_id = cursor.lastrowid
```
Then use `book_id` for all subsequent inserts that reference this book. Never hardcode IDs.

**Warning signs:** FK violations when running seed on a non-empty database.

### Pitfall 5: `thematic_mirrors` has no typed FKs

**What goes wrong:** `thematic_mirrors` uses `element_a_id` and `element_b_id` as generic integer IDs (not FK-constrained) with `element_a_type` and `element_b_type` as discriminators. There is no FK to validate. The Pydantic model cannot enforce referential integrity for this table.

**Why it happens:** The table is a polymorphic association — it can mirror any two entities (characters, locations, etc.).

**How to avoid:** In the `ThematicMirror` model, declare `element_a_id: int` and `element_b_id: int` as plain integers (not FK references). Document this in the model docstring. `PRAGMA foreign_key_check` will never catch violations here — integrity must be maintained by the application layer.

**Warning signs:** Assuming `PRAGMA foreign_key_check` will catch all data integrity issues.

### Pitfall 6: `id` field default for model reuse

**What goes wrong:** Setting `id: int` (required) in a model means it cannot be used for creating new records (no id yet) without special handling.

**Why it happens:** Developers write models only for read use cases.

**How to avoid:** Always `id: int | None = None`. When building INSERT statements from `model.model_dump()`, exclude `id` from the column list: `{k: v for k, v in model.model_dump().items() if k != 'id'}`.

### Pitfall 7: `PRAGMA foreign_key_check` only works with FK enforcement ON

**What goes wrong:** `PRAGMA foreign_key_check` returns zero rows even when FK violations exist, if `PRAGMA foreign_keys=OFF`.

**Why it happens:** `PRAGMA foreign_key_check` does its own FK verification but only checks the currently-enforced constraints. With FK enforcement off, some versions of SQLite still run the check; but the safe approach is to always enable FK enforcement before checking.

**How to avoid:** In TEST-02, set `PRAGMA foreign_keys=ON` before running `PRAGMA foreign_key_check`. The test verifies migrations are correct, not just that FK enforcement is bypassed.

---

## Code Examples

### Character model (no JSON fields)
```python
# Source: Pydantic v2 docs + PRAGMA table_info(characters) output
from pydantic import BaseModel


class Character(BaseModel):
    id: int | None = None
    name: str
    role: str = "supporting"
    faction_id: int | None = None
    culture_id: int | None = None
    home_era_id: int | None = None
    age: int | None = None
    physical_description: str | None = None
    personality_core: str | None = None
    backstory_summary: str | None = None
    secret: str | None = None
    motivation: str | None = None
    fear: str | None = None
    flaw: str | None = None
    strength: str | None = None
    arc_summary: str | None = None
    voice_signature: str | None = None
    notes: str | None = None
    canon_status: str = "draft"
    source_file: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    reviewed_at: str | None = None
```

### Scene model (with JSON field)
```python
# Source: Pydantic v2 docs + PRAGMA table_info(scenes) output
from pydantic import BaseModel, field_validator
import json


class Scene(BaseModel):
    id: int | None = None
    chapter_id: int
    scene_number: int
    location_id: int | None = None
    time_marker: str | None = None
    summary: str | None = None
    scene_type: str = "action"
    dramatic_question: str | None = None
    scene_goal: str | None = None
    obstacle: str | None = None
    turn: str | None = None
    consequence: str | None = None
    emotional_function: str | None = None
    narrative_functions: list[str] | None = None   # JSON TEXT in SQLite
    word_count_target: int | None = None
    status: str = "planned"
    notes: str | None = None
    canon_status: str = "draft"
    created_at: str | None = None
    updated_at: str | None = None

    @field_validator("narrative_functions", mode="before")
    @classmethod
    def parse_narrative_functions(cls, v: object) -> list[str] | None:
        if isinstance(v, str):
            return json.loads(v)
        return v

    def to_db_dict(self) -> dict:
        d = self.model_dump()
        if d["narrative_functions"] is not None:
            d["narrative_functions"] = json.dumps(d["narrative_functions"])
        return d
```

### Shared error types
```python
# Source: Phase 2 design — ERRC-01, ERRC-02, ERRC-03 contract (implemented in Phase 3)
from pydantic import BaseModel


class NotFoundResponse(BaseModel):
    not_found_message: str


class ValidationFailure(BaseModel):
    is_valid: bool = False
    errors: list[str]


class GateViolation(BaseModel):
    requires_action: str
```

### Schema validation test fixture
```python
# Source: pytest docs + sqlite3 PRAGMA table_info
import sqlite3
import pytest
from novel.db.migrations import apply_migrations


@pytest.fixture(scope="session")
def db_conn():
    """In-memory SQLite with all migrations applied."""
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys=ON")
    apply_migrations(conn)
    yield conn
    conn.close()
```

### Seed ID capture pattern
```python
# Source: sqlite3 docs — cursor.lastrowid
def _load_minimal(conn: sqlite3.Connection) -> None:
    # eras
    cur = conn.execute(
        "INSERT INTO eras (name, sequence_order, certainty_level, canon_status) VALUES (?, ?, ?, ?)",
        ("The Age of Embers", 1, "established", "approved")
    )
    era_id = cur.lastrowid

    # books
    cur = conn.execute(
        "INSERT INTO books (title, series_order, status, word_count_target, canon_status) VALUES (?, ?, ?, ?, ?)",
        ("The Void Between Stars", 1, "drafting", 120000, "draft")
    )
    book_id_1 = cur.lastrowid

    # cultures, factions (no FK deps)
    cur = conn.execute(
        "INSERT INTO cultures (name, region) VALUES (?, ?)",
        ("Kaelthari", "The Northern Reaches")
    )
    culture_id = cur.lastrowid

    # characters (FK: faction_id, culture_id, home_era_id all nullable)
    cur = conn.execute(
        "INSERT INTO characters (name, role, culture_id, home_era_id) VALUES (?, ?, ?, ?)",
        ("Mira Vayne", "protagonist", culture_id, era_id)
    )
    char_id_1 = cur.lastrowid

    conn.commit()
    # ... continue with chapters, scenes, etc.
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `model.dict()` | `model.model_dump()` | Pydantic v2 (2023) | `dict()` is deprecated alias, will be removed |
| `Model.parse_obj(data)` | `Model.model_validate(data)` | Pydantic v2 (2023) | `parse_obj()` is deprecated |
| `@validator` decorator | `@field_validator` | Pydantic v2 (2023) | `@validator` is removed in v2 |
| `class Config: orm_mode = True` | `model_config = ConfigDict(from_attributes=True)` | Pydantic v2 (2023) | `orm_mode` removed; `from_attributes` is the v2 equivalent |
| `Optional[X]` from typing | `X \| None` | Python 3.10+ | Both work in 3.12; `X \| None` is preferred for this project |

**Deprecated/outdated:**
- `pydantic.validator` (v1): Replaced by `field_validator` in v2. Do not use.
- `model.dict()`: Deprecated in v2. Use `model.model_dump()`.
- `Model.from_orm()`: Deprecated in v2. Use `Model.model_validate(obj, from_attributes=True)`.

---

## Open Questions

1. **Character arc duplication between characters.py and arcs.py**
   - What we know: CONTEXT.md lists `character_arcs` table. Both `characters.py` and `arcs.py` could logically contain `CharacterArc`.
   - What's unclear: Whether `CharacterArc` belongs in `characters.py` (it's fundamentally about a character) or `arcs.py` (it's the arc domain).
   - Recommendation: Place `CharacterArc` in `arcs.py` (matching the CONTEXT.md file name — `arcs.py` covers "arcs domain"). Import it in `characters.py` if needed, but keep the source in `arcs.py`. The `__init__.py` re-export makes this transparent to downstream code.

2. **`to_db_dict()` vs `model_dump()` for models without JSON fields**
   - What we know: CONTEXT.md says every model with JSON fields gets `to_db_dict()`. Models without JSON fields do not require it.
   - What's unclear: Whether non-JSON models should also have `to_db_dict()` for uniformity.
   - Recommendation: Only implement `to_db_dict()` on models with JSON fields. For non-JSON models, `model.model_dump(exclude={"id"})` is sufficient for INSERT construction. Uniformity at the cost of complexity is not warranted here.

3. **session_logs `chapters_touched` type**
   - What we know: Column comment says "JSON array of chapter IDs".
   - What's unclear: Whether this should be `list[int]` (chapter IDs) or `list[str]` (chapter numbers as strings).
   - Recommendation: `list[int] | None` — chapter IDs are integers in the database. The JSON encoding is `json.dumps([1, 2, 3])` not `json.dumps(["1", "2", "3"])`.

---

## Sources

### Primary (HIGH confidence)
- Pydantic v2 official docs — `field_validator`, `model_dump`, `model_validate`, `model_fields`
  - Verified via `uv run python -c "import pydantic; print(pydantic.VERSION)"` → 2.12.5
  - https://docs.pydantic.dev/latest/concepts/validators/
- SQLite PRAGMA docs — `PRAGMA table_info`, `PRAGMA foreign_key_check`, `PRAGMA foreign_key_list`
  - Verified via direct execution against live database
  - https://www.sqlite.org/pragma.html
- Project migration files — definitive schema source for all 68 table definitions
  - Read directly from `src/novel/migrations/001-021`
- sqlite3 Python stdlib — `cursor.lastrowid` for post-INSERT ID capture
  - https://docs.python.org/3.12/library/sqlite3.html

### Secondary (MEDIUM confidence)
- Pydantic v2 migration guide — deprecated v1 patterns and their v2 replacements
  - https://docs.pydantic.dev/latest/migration/

### Tertiary (LOW confidence)
- None — all claims verified against primary sources.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — Pydantic 2.12.5 installed and verified; all patterns tested via direct execution
- Architecture (model patterns): HIGH — verified working via `uv run python` against installed Pydantic v2
- Table-to-model mapping: HIGH — derived directly from 21 migration files, all 68 tables verified against sqlite_master
- JSON field identification: HIGH — identified from SQL column comments in migration files, 4 total
- Seed insertion order: HIGH — derived from FK dependency analysis verified in-memory with `PRAGMA foreign_keys=ON`
- Test patterns: HIGH — `PRAGMA table_info`, `PRAGMA foreign_key_check` verified against live database

**Research date:** 2026-03-07
**Valid until:** 2026-09-07 (Pydantic v2 is stable; SQLite PRAGMA API is stable)
