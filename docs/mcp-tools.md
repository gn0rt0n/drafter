# Drafter MCP Tools Reference

**Status:** Derived from Python tool module source files — implementation-accurate as of Phase 11

**Quick stats:** 103 tools across 18 domain modules

**Transport:** FastMCP stdio transport (`mcp>=1.26.0,<2.0.0`). Tools are callable by any MCP client, including Claude Code. All tools are async and return structured Pydantic model data — no tool ever raises an uncaught exception.

---

## Error Contract

Every MCP tool in this system returns structured data — no tool ever raises an exception to the caller.

| Response Type | When Returned | Fields |
|---------------|---------------|--------|
| Normal return | Record found, operation succeeded | Tool-specific return model |
| `NotFoundResponse` | Requested record does not exist | `not_found_message: str` |
| `ValidationFailure` | Invalid input or DB constraint violation | `is_valid: bool (False)`, `errors: list[str]` |
| `GateViolation` | Gate not certified (gated tools only) | `requires_action: str` |

### Gate Check Pattern

Gated tools (Session, Timeline, Canon, Knowledge, Foreshadowing, Voice, Publishing domains) call `check_gate()` from `novel.mcp.gate` at the very start of their execution, before any database logic:

```python
async with get_connection() as conn:
    violation = await check_gate(conn)
    if violation:
        return violation
    # ... rest of tool logic
```

If `architecture_gate.is_certified = 0`, `check_gate()` returns a `GateViolation` immediately and the tool performs no database reads or writes.

---

## Index

| Tool Name | Domain | Gate | Description |
|-----------|--------|------|-------------|
| `get_character` | Characters | Free | Look up a single character by ID |
| `list_characters` | Characters | Free | Return all characters ordered alphabetically |
| `upsert_character` | Characters | Free | Create or update a character |
| `get_character_injuries` | Characters | Free | Return injury records for a character |
| `get_character_beliefs` | Characters | Free | Return all belief records for a character |
| `get_character_knowledge` | Characters | Free | Return knowledge records for a character |
| `log_character_knowledge` | Characters | Free | Insert a new knowledge record for a character |
| `get_character_location` | Characters | Free | Return location records for a character |
| `get_relationship` | Relationships | Free | Look up the relationship between two characters |
| `list_relationships` | Relationships | Free | Return all relationships for a character |
| `upsert_relationship` | Relationships | Free | Create or update a character relationship |
| `get_perception_profile` | Relationships | Free | Return one character's perception of another |
| `upsert_perception_profile` | Relationships | Free | Create or update a perception profile |
| `log_relationship_change` | Relationships | Free | Record a change event for a relationship |
| `get_chapter` | Chapters | Free | Look up a single chapter by ID |
| `get_chapter_plan` | Chapters | Free | Return the writing-guidance subset of a chapter |
| `get_chapter_obligations` | Chapters | Free | Return structural obligations for a chapter |
| `list_chapters` | Chapters | Free | Return all chapters in a book |
| `upsert_chapter` | Chapters | Free | Create or update a chapter |
| `get_scene` | Scenes | Free | Look up a single scene by ID |
| `get_scene_character_goals` | Scenes | Free | Return all per-character goals for a scene |
| `upsert_scene` | Scenes | Free | Create or update a scene |
| `upsert_scene_goal` | Scenes | Free | Create or update a per-character scene goal |
| `get_location` | World | Free | Look up a single location by ID |
| `get_faction` | World | Free | Look up a single faction by ID |
| `get_faction_political_state` | World | Free | Return the political state for a faction |
| `get_culture` | World | Free | Look up a single culture by ID |
| `upsert_location` | World | Free | Create or update a location |
| `upsert_faction` | World | Free | Create or update a faction |
| `get_magic_element` | Magic | Free | Look up a single magic system element by ID |
| `get_practitioner_abilities` | Magic | Free | Return all magic abilities for a character |
| `log_magic_use` | Magic | Free | Append a magic use event to the immutable log |
| `check_magic_compliance` | Magic | Free | Check whether a proposed magic action complies with rules |
| `get_plot_thread` | Plot | Free | Look up a single plot thread by ID |
| `list_plot_threads` | Plot | Free | List all plot threads with optional filters |
| `upsert_plot_thread` | Plot | Free | Create or update a plot thread |
| `get_chekovs_guns` | Arcs | Free | Retrieve Chekhov's gun entries from the registry |
| `get_arc` | Arcs | Free | Retrieve character arc(s) by arc_id or character_id |
| `get_arc_health` | Arcs | Free | Retrieve arc health log entries for a character |
| `get_subplot_touchpoint_gaps` | Arcs | Free | Return active subplots overdue for a touchpoint |
| `upsert_chekov` | Arcs | Free | Create or update a Chekhov's gun entry |
| `log_arc_health` | Arcs | Free | Append an arc health log entry |
| `get_gate_status` | Gate | Free | Return the current gate certification status |
| `get_gate_checklist` | Gate | Free | Return all gate checklist items |
| `run_gate_audit` | Gate | Free | Execute all gate evidence queries and update checklist |
| `update_checklist_item` | Gate | Free | Manually override a gate checklist item |
| `certify_gate` | Gate | Free | Certify the gate if all checklist items pass |
| `check_name` | Names | Free | Check if a name is already registered |
| `register_name` | Names | Free | Register a new name in the name registry |
| `get_name_registry` | Names | Free | Retrieve all name registry entries |
| `generate_name_suggestions` | Names | Free | Retrieve name data to support consistent name generation |
| `get_story_structure` | Structure | Free | Retrieve the story structure for a book |
| `upsert_story_structure` | Structure | Free | Create or update story structure 7-point beats |
| `get_arc_beats` | Structure | Free | Retrieve all 7-point beat records for a character arc |
| `upsert_arc_beat` | Structure | Free | Create or update a single 7-point arc beat |
| `start_session` | Session | Gated | Start a new writing session with prior-session briefing |
| `close_session` | Session | Gated | Close an open session and record summary |
| `get_last_session` | Session | Gated | Retrieve the most recent session log entry |
| `log_agent_run` | Session | Gated | Append an agent run entry to the audit trail |
| `get_project_metrics` | Session | Gated | Retrieve live-computed project metrics |
| `log_project_snapshot` | Session | Gated | Persist a project metrics snapshot |
| `get_pov_balance` | Session | Gated | Retrieve live-computed POV balance across chapters |
| `get_open_questions` | Session | Gated | Retrieve all unanswered open questions |
| `log_open_question` | Session | Gated | Append a new open question to the log |
| `answer_open_question` | Session | Gated | Mark an open question as answered |
| `get_pov_positions` | Timeline | Gated | Retrieve all POV positions at a given chapter |
| `get_pov_position` | Timeline | Gated | Retrieve a specific POV position at a chapter |
| `get_event` | Timeline | Gated | Retrieve a single timeline event by ID |
| `list_events` | Timeline | Gated | List timeline events with optional chapter filters |
| `get_travel_segments` | Timeline | Gated | Retrieve all travel segments for a character |
| `validate_travel_realism` | Timeline | Gated | Validate whether travel is realistic given elapsed time |
| `upsert_event` | Timeline | Gated | Create or update a timeline event |
| `upsert_pov_position` | Timeline | Gated | Create or update a POV chronological position |
| `get_canon_facts` | Canon | Gated | Retrieve all canon facts for a domain |
| `log_canon_fact` | Canon | Gated | Log a new canon fact (append-only) |
| `log_decision` | Canon | Gated | Log a story decision with rationale |
| `get_decisions` | Canon | Gated | Retrieve the decisions log with optional filters |
| `log_continuity_issue` | Canon | Gated | Log a new continuity issue |
| `get_continuity_issues` | Canon | Gated | Retrieve open continuity issues |
| `resolve_continuity_issue` | Canon | Gated | Resolve a continuity issue by ID |
| `get_reader_state` | Knowledge | Gated | Retrieve cumulative reader information state up to a chapter |
| `get_dramatic_irony_inventory` | Knowledge | Gated | Retrieve the dramatic irony inventory |
| `get_reader_reveals` | Knowledge | Gated | Retrieve planned and actual reader reveals |
| `upsert_reader_state` | Knowledge | Gated | Create or update a reader information state entry |
| `log_dramatic_irony` | Knowledge | Gated | Log a new dramatic irony entry (append-only) |
| `get_foreshadowing` | Foreshadowing | Gated | Retrieve foreshadowing entries with optional filters |
| `get_prophecies` | Foreshadowing | Gated | Retrieve all prophecy registry entries |
| `get_motifs` | Foreshadowing | Gated | Retrieve all motif registry entries |
| `get_motif_occurrences` | Foreshadowing | Gated | Retrieve motif occurrences with optional filters |
| `get_thematic_mirrors` | Foreshadowing | Gated | Retrieve all thematic mirror pairs |
| `get_opposition_pairs` | Foreshadowing | Gated | Retrieve all opposition pairs |
| `log_foreshadowing` | Foreshadowing | Gated | Log or update a foreshadowing entry (upsert) |
| `log_motif_occurrence` | Foreshadowing | Gated | Log a new motif occurrence (append-only) |
| `get_voice_profile` | Voice | Gated | Retrieve the voice profile for a character |
| `upsert_voice_profile` | Voice | Gated | Create or update a voice profile for a character |
| `get_supernatural_voice_guidelines` | Voice | Gated | Retrieve all supernatural voice guidelines |
| `log_voice_drift` | Voice | Gated | Log a voice drift event (append-only) |
| `get_voice_drift_log` | Voice | Gated | Retrieve voice drift log entries for a character |
| `get_publishing_assets` | Publishing | Gated | Retrieve all publishing assets with optional filter |
| `upsert_publishing_asset` | Publishing | Gated | Create or update a publishing asset |
| `get_submissions` | Publishing | Gated | Retrieve all submission tracker entries |
| `log_submission` | Publishing | Gated | Log a new submission (append-only) |
| `update_submission` | Publishing | Gated | Partially update a submission tracker entry |

---

## Characters Domain

Manages the core character registry, character state across chapters (injuries, beliefs, knowledge, location), and character knowledge acquisition. All tools are gate-free because character data is needed during both worldbuilding and prose phases.

**Gate status:** All tools in this domain are gate-free.

**8 tools**

---

#### `get_character`

**Purpose:** Look up a single character by primary key, returning all character fields.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `character_id` | `int` | Yes | Primary key of the character to retrieve |

**Returns:** `Character | NotFoundResponse` — `Character` with all fields if found; `NotFoundResponse` if no character with that ID exists.

**Invocation reason:** Called at the start of any scene draft to load the full character record before generating dialogue or action — ensures the agent has current motivation, flaw, arc summary, and voice signature before writing.

**Gate status:** Gate-free.

**Tables touched:** Reads `characters`.

---

#### `list_characters`

**Purpose:** Return all characters ordered alphabetically by name.

**Parameters:** None

**Returns:** `list[Character]` — All character records. Returns an empty list if no characters have been created.

**Invocation reason:** Called when building a cast list, checking for name conflicts, or generating a project overview. Useful for roster validation before beginning a new chapter.

**Gate status:** Gate-free.

**Tables touched:** Reads `characters`.

---

#### `upsert_character`

**Purpose:** Create a new character (when `character_id` is None) or update an existing character.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `character_id` | `int \| None` | Yes | Existing character ID to update, or None to create |
| `name` | `str` | Yes | Character's full name |
| `role` | `str` | No (default: `"supporting"`) | Narrative role — e.g. "protagonist", "antagonist", "supporting" |
| `faction_id` | `int \| None` | No | FK to factions table |
| `culture_id` | `int \| None` | No | FK to cultures table |
| `home_era_id` | `int \| None` | No | FK to eras table |
| `age` | `int \| None` | No | Character age in story-time |
| `physical_description` | `str \| None` | No | Appearance notes |
| `personality_core` | `str \| None` | No | Core personality summary |
| `backstory_summary` | `str \| None` | No | Brief backstory |
| `secret` | `str \| None` | No | Hidden information about the character |
| `motivation` | `str \| None` | No | What drives the character |
| `fear` | `str \| None` | No | What the character fears most |
| `flaw` | `str \| None` | No | Character's primary flaw |
| `strength` | `str \| None` | No | Character's primary strength |
| `arc_summary` | `str \| None` | No | Arc trajectory summary |
| `voice_signature` | `str \| None` | No | Distinctive speech patterns |
| `notes` | `str \| None` | No | Free-form notes |
| `canon_status` | `str` | No (default: `"draft"`) | Approval status — "draft" or "approved" |

**Returns:** `Character | ValidationFailure` — The created or updated `Character`; `ValidationFailure` with error list on DB constraint violation.

**Invocation reason:** Called during worldbuilding to establish the cast, and during revision to update motivation, arc notes, or canon status. When `character_id` is None, the AUTOINCREMENT PK is assigned and returned.

**Gate status:** Gate-free.

**Tables touched:** Reads `characters`. Writes `characters`.

---

#### `get_character_injuries`

**Purpose:** Return injury records for a character, optionally scoped to chapters up to a given chapter.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `character_id` | `int` | Yes | ID of the character whose injuries to retrieve |
| `chapter_id` | `int \| None` | No | If provided, returns only injuries with chapter_id <= this value |

**Returns:** `list[InjuryState] | NotFoundResponse` — List of `InjuryState` records ordered by `chapter_id DESC`; `NotFoundResponse` if the character does not exist.

**Invocation reason:** Called before drafting a scene to verify the character's current physical state — checking whether old injuries still affect their capabilities or have healed by a given chapter.

**Gate status:** Gate-free.

**Tables touched:** Reads `characters`, `injury_states`.

---

#### `get_character_beliefs`

**Purpose:** Return all belief records for a character.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `character_id` | `int` | Yes | ID of the character whose beliefs to retrieve |

**Returns:** `list[CharacterBelief] | NotFoundResponse` — List of `CharacterBelief` records ordered by `created_at DESC`; `NotFoundResponse` if the character does not exist.

**Invocation reason:** Called at the start of each chapter draft to check whether the POV character's beliefs have evolved since the last session — ensures dialogue and internal monologue accurately reflect current worldview.

**Gate status:** Gate-free.

**Tables touched:** Reads `characters`, `character_beliefs`.

---

#### `get_character_knowledge`

**Purpose:** Return knowledge records for a character, optionally scoped by chapter.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `character_id` | `int` | Yes | ID of the character whose knowledge to retrieve |
| `chapter_id` | `int \| None` | No | If provided, returns only records with chapter_id <= this value |

**Returns:** `list[CharacterKnowledge] | NotFoundResponse` — List of `CharacterKnowledge` records ordered by `chapter_id DESC`; `NotFoundResponse` if the character does not exist.

**Invocation reason:** Called to check what a character knows at a specific story point — prevents the agent from writing a character as having knowledge they couldn't yet possess, maintaining narrative information consistency.

**Gate status:** Gate-free.

**Tables touched:** Reads `characters`, `character_knowledge`.

---

#### `log_character_knowledge`

**Purpose:** Insert a new knowledge record for a character at a specific chapter.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `character_id` | `int` | Yes | ID of the character acquiring knowledge |
| `chapter_id` | `int` | Yes | Chapter at which this knowledge was acquired |
| `knowledge_type` | `str` | No (default: `"fact"`) | Type — "fact", "rumor", "secret", etc. |
| `content` | `str` | No (default: `""`) | The knowledge content |
| `source` | `str \| None` | No | Where the character learned this |
| `is_secret` | `bool` | No (default: `False`) | Whether this knowledge is secret |
| `notes` | `str \| None` | No | Free-form notes |

**Returns:** `CharacterKnowledge | NotFoundResponse | ValidationFailure` — The newly created `CharacterKnowledge` with assigned id; `NotFoundResponse` if the character doesn't exist; `ValidationFailure` on DB error.

**Invocation reason:** Called immediately after writing a scene where a character learns new information — records the acquisition for future knowledge-consistency checks.

**Gate status:** Gate-free.

**Tables touched:** Reads `characters`. Writes `character_knowledge`.

---

#### `get_character_location`

**Purpose:** Return location records for a character, optionally scoped to chapters up to a given chapter.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `character_id` | `int` | Yes | ID of the character whose locations to retrieve |
| `chapter_id` | `int \| None` | No | If provided, returns only records with chapter_id <= this value |

**Returns:** `list[CharacterLocation] | NotFoundResponse` — List of `CharacterLocation` records ordered by `chapter_id DESC`; `NotFoundResponse` if the character does not exist.

**Invocation reason:** Called to verify where a character is at a specific story point — prevents placing a character in a scene at a location they couldn't have reached given their last known position.

**Gate status:** Gate-free.

**Tables touched:** Reads `characters`, `character_locations`.

---

## Relationships Domain

Manages character-to-character relationships (bidirectional bond) and directional perception profiles (how one character views another). Handles the canonical pair ordering so callers never need to know min/max storage order.

**Gate status:** All tools in this domain are gate-free.

**6 tools**

---

#### `get_relationship`

**Purpose:** Look up the relationship between two characters, querying both canonical orderings.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `character_a_id` | `int` | Yes | First character ID in the pair |
| `character_b_id` | `int` | Yes | Second character ID in the pair |

**Returns:** `CharacterRelationship | NotFoundResponse` — `CharacterRelationship` if a row exists; `NotFoundResponse` if no relationship has been recorded between these two characters.

**Invocation reason:** Called before drafting a scene involving two characters — verifies their current bond strength, trust level, and relationship type to ensure interactions are consistent with established dynamics.

**Gate status:** Gate-free.

**Tables touched:** Reads `character_relationships`.

---

#### `list_relationships`

**Purpose:** Return all relationships where the given character appears as either party.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `character_id` | `int` | Yes | ID of the character whose relationships to retrieve |

**Returns:** `list[CharacterRelationship]` — All relationships for the character ordered by `updated_at DESC`. Returns an empty list if the character has no recorded relationships.

**Invocation reason:** Called to build a complete social map of a character — useful when planning a scene that involves multiple relationships, or when auditing relationship coverage before gate certification.

**Gate status:** Gate-free.

**Tables touched:** Reads `character_relationships`.

---

#### `upsert_relationship`

**Purpose:** Create or update the relationship between two characters, canonicalizing pair order.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `character_a_id` | `int` | Yes | First character ID (will be canonicalized to min) |
| `character_b_id` | `int` | Yes | Second character ID (will be canonicalized to max) |
| `relationship_type` | `str` | No (default: `"acquaintance"`) | Type label — "ally", "rival", "enemy", etc. |
| `bond_strength` | `int` | No (default: `0`) | Numeric bond intensity (positive = strong) |
| `trust_level` | `int` | No (default: `0`) | Numeric trust score (positive = high trust) |
| `current_status` | `str` | No (default: `"neutral"`) | Relationship status — "neutral", "active", "hostile" |
| `history_summary` | `str \| None` | No | Free-text summary of relationship history |
| `first_meeting_chapter_id` | `int \| None` | No | FK to chapters where they first met |
| `notes` | `str \| None` | No | Free-form notes |
| `canon_status` | `str` | No (default: `"draft"`) | Approval status — "draft" or "approved" |

**Returns:** `CharacterRelationship | ValidationFailure` — The created or updated `CharacterRelationship`; `ValidationFailure` on DB error.

**Invocation reason:** Called when establishing a relationship during worldbuilding, or updating it after a scene causes a significant shift in bond or trust. The canonicalization ensures exactly one row per pair regardless of argument order.

**Gate status:** Gate-free.

**Tables touched:** Reads `character_relationships`. Writes `character_relationships`.

---

#### `get_perception_profile`

**Purpose:** Return the perception profile one character holds of another (directional).

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `observer_id` | `int` | Yes | ID of the character whose perception is recorded |
| `subject_id` | `int` | Yes | ID of the character being perceived |

**Returns:** `PerceptionProfile | NotFoundResponse` — `PerceptionProfile` for this (observer, subject) pair; `NotFoundResponse` if no profile has been recorded.

**Invocation reason:** Called before writing POV scenes where the narrator perceives another character — ensures the described perception (misperceptions, emotional valence, trust level) matches what was previously established.

**Gate status:** Gate-free.

**Tables touched:** Reads `perception_profiles`.

---

#### `upsert_perception_profile`

**Purpose:** Create or update the perception profile for an (observer, subject) pair.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `observer_id` | `int` | Yes | ID of the observing character |
| `subject_id` | `int` | Yes | ID of the subject character being perceived |
| `chapter_id` | `int \| None` | No | Chapter at which this perception snapshot applies |
| `perceived_traits` | `str \| None` | No | Free-text description of perceived personality traits |
| `trust_level` | `int` | No (default: `0`) | Observer's trust rating of the subject |
| `emotional_valence` | `str` | No (default: `"neutral"`) | Emotional orientation — "neutral", "trusting", "wary" |
| `misperceptions` | `str \| None` | No | Known misperceptions the observer holds |
| `notes` | `str \| None` | No | Free-form notes |

**Returns:** `PerceptionProfile | ValidationFailure` — The created or updated `PerceptionProfile`; `ValidationFailure` on DB error.

**Invocation reason:** Called after a scene that shifts how a character perceives another — recording the updated misperceptions or emotional valence for use in future POV scenes.

**Gate status:** Gate-free.

**Tables touched:** Reads `perception_profiles`. Writes `perception_profiles`.

---

#### `log_relationship_change`

**Purpose:** Record a change event for an existing relationship, with deltas for bond and trust.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `relationship_id` | `int` | Yes | FK to `character_relationships.id` — must exist |
| `chapter_id` | `int \| None` | No | Chapter at which this change occurred |
| `event_id` | `int \| None` | No | FK to story events table |
| `change_type` | `str` | No (default: `"shift"`) | Nature — "shift", "breakthrough", "rupture" |
| `description` | `str` | No (default: `""`) | Human-readable description of what changed |
| `bond_delta` | `int` | No (default: `0`) | Change in bond strength (positive = stronger) |
| `trust_delta` | `int` | No (default: `0`) | Change in trust level (positive = more trust) |

**Returns:** `RelationshipChangeEvent | NotFoundResponse | ValidationFailure` — The newly created `RelationshipChangeEvent` with assigned id; `NotFoundResponse` if `relationship_id` does not exist; `ValidationFailure` on DB error.

**Invocation reason:** Called after drafting a scene where a relationship meaningfully shifts — creates an audit trail of relationship progression that informs later narrative decisions.

**Gate status:** Gate-free.

**Tables touched:** Reads `character_relationships`. Writes `relationship_change_events`.

---

## Chapters Domain

Manages book chapters, chapter writing plans (a focused subset of chapter fields), and structural obligations. The structural obligations capture what each chapter must accomplish narratively.

**Gate status:** All tools in this domain are gate-free.

**5 tools**

---

#### `get_chapter`

**Purpose:** Look up a single chapter by ID, returning all fields.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `chapter_id` | `int` | Yes | Primary key of the chapter to retrieve |

**Returns:** `Chapter | NotFoundResponse` — Full `Chapter` record; `NotFoundResponse` if chapter does not exist.

**Invocation reason:** Called when opening a chapter draft — loads word count target, POV character, structural function, hook notes, and status to orient the drafting session.

**Gate status:** Gate-free.

**Tables touched:** Reads `chapters`.

---

#### `get_chapter_plan`

**Purpose:** Return the focused writing-guidance subset of a chapter (8 fields).

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `chapter_id` | `int` | Yes | Primary key of the chapter |

**Returns:** `ChapterPlan | NotFoundResponse` — `ChapterPlan` with summary, opening/closing state, hook notes, structural function, and hook rating; `NotFoundResponse` if chapter does not exist.

**Invocation reason:** Called at the start of a drafting session as a lightweight alternative to `get_chapter` — provides only the writing-relevant fields without fetching the full metadata set, reducing response size.

**Gate status:** Gate-free.

**Tables touched:** Reads `chapters`.

---

#### `get_chapter_obligations`

**Purpose:** Return all structural obligations for a chapter.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `chapter_id` | `int` | Yes | Primary key of the chapter to query |

**Returns:** `list[ChapterStructuralObligation] | NotFoundResponse` — List of obligations ordered by id; `NotFoundResponse` if chapter does not exist. An empty list is valid for a chapter with no obligations recorded.

**Invocation reason:** Called before drafting to enumerate what the chapter must accomplish structurally — ensures the draft fulfills all obligations before moving on. Required for gate certification (`struct_chapter_obligations` gate item).

**Gate status:** Gate-free.

**Tables touched:** Reads `chapters`, `chapter_structural_obligations`.

---

#### `list_chapters`

**Purpose:** Return all chapters in a book ordered by chapter number.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `book_id` | `int` | Yes | ID of the book whose chapters to list |

**Returns:** `list[Chapter]` — All chapters ordered by `chapter_number`. Returns an empty list if the book has no chapters.

**Invocation reason:** Called to get a full chapter roster for a book — useful for building table of contents, auditing POV coverage, or checking which chapters still need structural obligations recorded.

**Gate status:** Gate-free.

**Tables touched:** Reads `chapters`.

---

#### `upsert_chapter`

**Purpose:** Create a new chapter or update an existing one.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `chapter_id` | `int \| None` | Yes | Existing chapter ID to update, or None to create |
| `book_id` | `int` | Yes | FK to books table |
| `chapter_number` | `int` | Yes | Position in the book |
| `act_id` | `int \| None` | No | FK to acts table |
| `title` | `str \| None` | No | Chapter title |
| `pov_character_id` | `int \| None` | No | FK to characters for POV |
| `word_count_target` | `int \| None` | No | Target word count |
| `summary` | `str \| None` | No | Brief summary of events |
| `opening_state` | `str \| None` | No | Story state at chapter open |
| `closing_state` | `str \| None` | No | Story state at chapter close |
| `opening_hook_note` | `str \| None` | No | Notes on the opening hook |
| `closing_hook_note` | `str \| None` | No | Notes on the closing hook |
| `hook_strength_rating` | `int \| None` | No | Rating 1-10 for hook effectiveness |
| `structural_function` | `str \| None` | No | Narrative role of this chapter |
| `status` | `str` | No (default: `"planned"`) | Chapter status — "planned", "drafted", "revised" |
| `notes` | `str \| None` | No | Free-form notes |

**Returns:** `Chapter | ValidationFailure` — The created or updated `Chapter`; `ValidationFailure` on DB error.

**Invocation reason:** Called during outlining to populate the chapter skeleton, and during revision to update status and notes. Multiple gate items check chapter fields (summary, hooks, POV, structural function) — this tool populates them.

**Gate status:** Gate-free.

**Tables touched:** Reads `chapters`. Writes `chapters`.

---

## Scenes Domain

Manages individual scenes within chapters, including per-character scene goals. Scenes are the atomic narrative unit: each has a dramatic question, goal, obstacle, turn, and consequence.

**Gate status:** All tools in this domain are gate-free.

**4 tools**

---

#### `get_scene`

**Purpose:** Look up a single scene by ID with `narrative_functions` parsed from JSON to `list[str]`.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `scene_id` | `int` | Yes | Primary key of the scene to retrieve |

**Returns:** `Scene | NotFoundResponse` — Full `Scene` record with `narrative_functions` as list; `NotFoundResponse` if scene does not exist.

**Invocation reason:** Called before drafting a scene to verify its dramatic structure — ensures the agent knows the dramatic question, obstacle, and emotional function before generating content.

**Gate status:** Gate-free.

**Tables touched:** Reads `scenes`.

---

#### `get_scene_character_goals`

**Purpose:** Return all per-character goals for a scene.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `scene_id` | `int` | Yes | Primary key of the scene |

**Returns:** `list[SceneCharacterGoal] | NotFoundResponse` — List of goals ordered by id; `NotFoundResponse` if scene does not exist. An empty list is valid for a scene with no goals recorded.

**Invocation reason:** Called when preparing to draft a multi-character scene — ensures each character's goal and obstacle within the scene are captured before generating interaction dynamics.

**Gate status:** Gate-free.

**Tables touched:** Reads `scenes`, `scene_character_goals`.

---

#### `upsert_scene`

**Purpose:** Create a new scene or update an existing one; serializes `narrative_functions` to JSON.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `scene_id` | `int \| None` | Yes | Existing scene ID to update, or None to create |
| `chapter_id` | `int` | Yes | FK to chapters table |
| `scene_number` | `int` | Yes | Position within the chapter |
| `location_id` | `int \| None` | No | FK to locations table |
| `time_marker` | `str \| None` | No | Narrative time label |
| `summary` | `str \| None` | No | Brief description of scene events |
| `scene_type` | `str` | No (default: `"action"`) | Type: "action", "dialogue", "transition" |
| `dramatic_question` | `str \| None` | No | Central tension this scene answers |
| `scene_goal` | `str \| None` | No | What the POV character wants |
| `obstacle` | `str \| None` | No | What stands in the way of the goal |
| `turn` | `str \| None` | No | How the scene pivots or resolves |
| `consequence` | `str \| None` | No | Aftermath of the scene turn |
| `emotional_function` | `str \| None` | No | Emotional beat this scene serves |
| `narrative_functions` | `list[str] \| None` | No | List of narrative roles, e.g. ["setup", "payoff"] |
| `word_count_target` | `int \| None` | No | Target word count |
| `status` | `str` | No (default: `"planned"`) | Scene status — "planned", "drafted", "revised" |
| `notes` | `str \| None` | No | Free-form notes |

**Returns:** `Scene | ValidationFailure` — The created or updated `Scene`; `ValidationFailure` on DB error.

**Invocation reason:** Called during outlining to plan scene structure, and after drafting to update status and summary. Gate items `scene_summary`, `scene_dramatic_question`, and `scene_goals` are populated via this tool and `upsert_scene_goal`.

**Gate status:** Gate-free.

**Tables touched:** Reads `scenes`. Writes `scenes`.

---

#### `upsert_scene_goal`

**Purpose:** Create or update a per-character goal for a scene, using ON CONFLICT(scene_id, character_id).

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `scene_id` | `int` | Yes | FK to scenes table |
| `character_id` | `int` | Yes | FK to characters table |
| `goal` | `str` | Yes | What this character wants during the scene |
| `obstacle` | `str \| None` | No | What prevents achieving the goal |
| `outcome` | `str \| None` | No | How the goal attempt resolved |
| `notes` | `str \| None` | No | Free-form notes |

**Returns:** `SceneCharacterGoal | ValidationFailure` — The created or updated `SceneCharacterGoal`; `ValidationFailure` on DB error.

**Invocation reason:** Called when planning a scene to record each character's competing objective — ensures multi-character scenes have documented goal conflicts before the agent begins drafting.

**Gate status:** Gate-free.

**Tables touched:** Reads `scene_character_goals`. Writes `scene_character_goals`.

---

## World Domain

Manages world-building entities: locations, factions, faction political states, and cultures. Locations have a JSON `sensory_profile` field; factions are UNIQUE by name. Political states are a separate time-stamped log not written by `upsert_faction`.

**Gate status:** All tools in this domain are gate-free.

**6 tools**

---

#### `get_location`

**Purpose:** Look up a single location by ID; `sensory_profile` is returned as a parsed dict.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `location_id` | `int` | Yes | Primary key of the location |

**Returns:** `Location | NotFoundResponse` — Full `Location` record; `NotFoundResponse` if location does not exist.

**Invocation reason:** Called before drafting a scene set in a specific location — loads sensory profile, description, and strategic value to inform atmospheric writing.

**Gate status:** Gate-free.

**Tables touched:** Reads `locations`.

---

#### `get_faction`

**Purpose:** Look up a single faction by ID, returning the full faction profile.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `faction_id` | `int` | Yes | Primary key of the faction |

**Returns:** `Faction | NotFoundResponse` — Full `Faction` record; `NotFoundResponse` if faction does not exist.

**Invocation reason:** Called before writing scenes where a faction's goals, resources, or alliances drive character motivation — ensures narrative accuracy for faction-driven plot threads.

**Gate status:** Gate-free.

**Tables touched:** Reads `factions`.

---

#### `get_faction_political_state`

**Purpose:** Return the political state for a faction at a specific chapter or the most recent state.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `faction_id` | `int` | Yes | ID of the faction |
| `chapter_id` | `int \| None` | No | If provided, returns state for that exact chapter; if None, returns most recent |

**Returns:** `FactionPoliticalState | NotFoundResponse` — `FactionPoliticalState` for the faction; `NotFoundResponse` if no political state has been recorded.

**Invocation reason:** Called when writing scenes involving political intrigue — verifies the current power level, stability, and internal conflicts of a faction at the relevant story point.

**Gate status:** Gate-free.

**Tables touched:** Reads `faction_political_states`.

---

#### `get_culture`

**Purpose:** Look up a single culture record by ID.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `culture_id` | `int` | Yes | Primary key of the culture |

**Returns:** `Culture | NotFoundResponse` — Full `Culture` record; `NotFoundResponse` if culture does not exist.

**Invocation reason:** Called to retrieve naming conventions, customs, and values for a culture before writing characters from that culture — ensures authentic cultural portrayal.

**Gate status:** Gate-free.

**Tables touched:** Reads `cultures`.

---

#### `upsert_location`

**Purpose:** Create a new location or update an existing one; serializes `sensory_profile` dict to JSON.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `location_id` | `int \| None` | Yes | Existing location ID to update, or None to create |
| `name` | `str` | Yes | Location name |
| `location_type` | `str \| None` | No | Category — "city", "wilderness", "building" |
| `parent_location_id` | `int \| None` | No | FK to parent location |
| `culture_id` | `int \| None` | No | FK to cultures table |
| `controlling_faction_id` | `int \| None` | No | FK to factions table |
| `description` | `str \| None` | No | Narrative description |
| `sensory_profile` | `dict \| None` | No | Dict of sensory details — sight, sound, smell, etc. |
| `strategic_value` | `str \| None` | No | Strategic importance notes |
| `accessibility` | `str \| None` | No | How accessible the location is |
| `notable_features` | `str \| None` | No | Distinctive features |
| `notes` | `str \| None` | No | Free-form notes |

**Returns:** `Location | ValidationFailure` — The created or updated `Location`; `ValidationFailure` on DB error.

**Invocation reason:** Called during worldbuilding to establish the geography. When `location_id` is None, a new location is inserted with AUTOINCREMENT PK. Gate item `pop_locations` requires all locations have a description.

**Gate status:** Gate-free.

**Tables touched:** Reads `locations`. Writes `locations`.

---

#### `upsert_faction`

**Purpose:** Create or update a faction. When `faction_id` is None, merges by name (ON CONFLICT(name)). Does NOT write to `faction_political_states`.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `faction_id` | `int \| None` | Yes | Existing faction ID to update, or None to create/merge by name |
| `name` | `str` | Yes | Faction name (UNIQUE constraint) |
| `faction_type` | `str \| None` | No | Category — "political", "military", etc. |
| `leader_character_id` | `int \| None` | No | FK to characters for faction leader |
| `headquarters` | `str \| None` | No | Description or location of HQ |
| `size_estimate` | `str \| None` | No | Estimated membership size |
| `goals` | `str \| None` | No | Faction goals and objectives |
| `resources` | `str \| None` | No | Available resources |
| `weaknesses` | `str \| None` | No | Known weaknesses |
| `alliances` | `str \| None` | No | Current alliance descriptions |
| `conflicts` | `str \| None` | No | Current conflict descriptions |
| `notes` | `str \| None` | No | Free-form notes |

**Returns:** `Faction | ValidationFailure` — The created or updated `Faction`; `ValidationFailure` on DB error.

**Invocation reason:** Called during worldbuilding to establish factions, and during revision to update goals or leadership. The None-id branch always re-queries by name (lastrowid is 0 on conflict), ensuring the returned record is accurate.

**Gate status:** Gate-free.

**Tables touched:** Reads `factions`. Writes `factions`.

---

## Magic Domain

Manages the magic system, practitioner abilities, magic use events, and compliance checking. `check_magic_compliance` is read-only; `log_magic_use` is append-only (no UNIQUE constraint).

**Gate status:** All tools in this domain are gate-free.

**4 tools**

---

#### `get_magic_element`

**Purpose:** Look up a single magic system element by ID, returning rules, limitations, costs, and exceptions.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `magic_element_id` | `int` | Yes | Primary key of the magic element |

**Returns:** `MagicSystemElement | NotFoundResponse` — Full `MagicSystemElement` record; `NotFoundResponse` if element does not exist.

**Invocation reason:** Called before writing a magic scene to verify the rules and limitations of the magic being invoked — prevents rule inconsistencies across chapters.

**Gate status:** Gate-free.

**Tables touched:** Reads `magic_system_elements`.

---

#### `get_practitioner_abilities`

**Purpose:** Return all registered magic abilities for a character, ordered by ID.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `character_id` | `int` | Yes | Primary key of the character |

**Returns:** `list[PractitionerAbility] | NotFoundResponse` — List of `PractitionerAbility` records; `NotFoundResponse` if the character does not exist. An empty list is valid for characters with no registered abilities.

**Invocation reason:** Called before a magic compliance check to understand which elements a character is registered to use — informs `check_magic_compliance` and narrative accuracy decisions.

**Gate status:** Gate-free.

**Tables touched:** Reads `characters`, `practitioner_abilities`.

---

#### `log_magic_use`

**Purpose:** Append a magic use event to the immutable magic use log (append-only, no UNIQUE constraint).

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `chapter_id` | `int` | Yes | FK to chapters table — chapter where magic was used |
| `character_id` | `int` | Yes | FK to characters table — character who performed magic |
| `action_description` | `str` | Yes | Free-text description of the magic action |
| `magic_element_id` | `int \| None` | No | FK to magic_system_elements |
| `scene_id` | `int \| None` | No | FK to scenes table |
| `cost_paid` | `str \| None` | No | Description of the cost the character paid |
| `compliance_status` | `str` | No (default: `"compliant"`) | "compliant", "non_compliant", or "unchecked" |
| `notes` | `str \| None` | No | Free-form notes |

**Returns:** `MagicUseLog | NotFoundResponse | ValidationFailure` — The newly created `MagicUseLog` row; `NotFoundResponse` if chapter does not exist; `ValidationFailure` on DB error.

**Invocation reason:** Called after drafting a magic scene to record the event — maintains an audit trail for later continuity checking and ensures compliance status is tracked alongside the narrative.

**Gate status:** Gate-free.

**Tables touched:** Reads `chapters`. Writes `magic_use_log`.

---

#### `check_magic_compliance`

**Purpose:** Check whether a character's proposed magic action complies with system rules. READ-ONLY — does not write to `magic_use_log`.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `character_id` | `int` | Yes | ID of the character performing the action |
| `magic_element_id` | `int` | Yes | ID of the magic element being invoked |
| `action_description` | `str` | Yes | Free-text description of the proposed action |

**Returns:** `MagicComplianceResult | NotFoundResponse` — `MagicComplianceResult` with `compliant` flag, `violations` list, `applicable_rules` list, and `character_has_ability` status; `NotFoundResponse` if the magic element does not exist.

**Invocation reason:** Called before writing a magic scene to pre-validate compliance — if violations are detected, the agent adjusts the scene plan before drafting; if compliant, proceeds then calls `log_magic_use`.

**Gate status:** Gate-free.

**Tables touched:** Reads `magic_system_elements`, `practitioner_abilities`.

---

## Plot Domain

Manages plot threads (main, subplot, backstory). Does NOT touch the `chapter_plot_threads` junction table — that is managed via chapter tools.

**Gate status:** All tools in this domain are gate-free.

**3 tools**

---

#### `get_plot_thread`

**Purpose:** Look up a single plot thread by ID, returning all fields.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `plot_thread_id` | `int` | Yes | Primary key of the plot thread |

**Returns:** `PlotThread | NotFoundResponse` — Full `PlotThread` record; `NotFoundResponse` if thread does not exist.

**Invocation reason:** Called when preparing to draft a chapter to load the current status, stakes, and summary of the plot threads active in that chapter.

**Gate status:** Gate-free.

**Tables touched:** Reads `plot_threads`.

---

#### `list_plot_threads`

**Purpose:** List all plot threads with optional `thread_type` and/or `status` filters.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `thread_type` | `str \| None` | No | Filter by type — "main", "subplot", "backstory" |
| `status` | `str \| None` | No | Filter by status — "active", "resolved", "dormant" |

**Returns:** `list[PlotThread]` — All matching plot threads ordered by id. Returns empty list if no threads match.

**Invocation reason:** Called to audit active plot threads before starting a new chapter — ensures all active threads are consciously tracked and none are neglected.

**Gate status:** Gate-free.

**Tables touched:** Reads `plot_threads`.

---

#### `upsert_plot_thread`

**Purpose:** Create a new plot thread or update an existing one. Does NOT touch `chapter_plot_threads`.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `plot_thread_id` | `int \| None` | Yes | Existing thread ID to update, or None to create |
| `name` | `str` | Yes | Plot thread name |
| `thread_type` | `str \| None` | No (default: `"main"`) | Type — "main", "subplot", "backstory" |
| `status` | `str \| None` | No (default: `"active"`) | Status — "active", "resolved", "dormant" |
| `opened_chapter_id` | `int \| None` | No | FK to chapters where thread opens |
| `closed_chapter_id` | `int \| None` | No | FK to chapters where thread closes |
| `parent_thread_id` | `int \| None` | No | FK to plot_threads for nested subplots |
| `summary` | `str \| None` | No | Narrative summary |
| `resolution` | `str \| None` | No | How the thread resolves |
| `stakes` | `str \| None` | No | Stakes involved |
| `notes` | `str \| None` | No | Free-form notes |
| `canon_status` | `str \| None` | No (default: `"draft"`) | Canon status — "draft", "canon", "cut" |

**Returns:** `PlotThread | ValidationFailure` — The created or updated `PlotThread`; `ValidationFailure` on DB error.

**Invocation reason:** Called to establish plot threads during outlining and update their status when resolved. Uses ON CONFLICT(id) to prevent duplicate rows in a table that has FK children.

**Gate status:** Gate-free.

**Tables touched:** Reads `plot_threads`. Writes `plot_threads`.

---

## Arcs Domain

Manages character arcs, Chekhov's gun registry, subplot touchpoint tracking, and arc health logging. `get_arc` is dual-mode (by arc_id or character_id). `log_arc_health` and `upsert_chekov` use separate branching patterns.

**Gate status:** All tools in this domain are gate-free.

**6 tools**

---

#### `get_chekovs_guns`

**Purpose:** Retrieve Chekhov's gun entries, optionally filtered by status or limited to unresolved-only.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `status` | `str \| None` | No | Optional filter — "planted", "fired" (ignored when `unresolved_only=True`) |
| `unresolved_only` | `bool` | No (default: `False`) | When True, returns only guns with status="planted" AND payoff_chapter_id IS NULL |

**Returns:** `list[ChekhovGun]` — All matching `ChekhovGun` records ordered by id. Empty list if none match.

**Invocation reason:** Called at chapter review checkpoints to inventory all planted story elements that haven't yet paid off — prevents narrative loose ends from going unresolved.

**Gate status:** Gate-free.

**Tables touched:** Reads `chekovs_gun_registry`.

---

#### `get_arc`

**Purpose:** Retrieve character arc(s) by arc_id or character_id; dual-mode with `arc_id` taking precedence.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `arc_id` | `int \| None` | No | Primary key of a specific arc (takes precedence) |
| `character_id` | `int \| None` | No | Character whose arcs to retrieve (used when arc_id not provided) |

**Returns:** `CharacterArc | list[CharacterArc] | NotFoundResponse | ValidationFailure` — Single `CharacterArc` when `arc_id` provided; `list[CharacterArc]` (may be empty) when only `character_id` provided; `NotFoundResponse` if arc_id not found; `ValidationFailure` if neither parameter provided.

**Invocation reason:** Called before drafting a chapter to load a POV character's arc state — lie_believed, truth_to_learn, and arc summary are essential context for maintaining consistent character transformation.

**Gate status:** Gate-free.

**Tables touched:** Reads `character_arcs`.

---

#### `get_arc_health`

**Purpose:** Retrieve arc health log entries for a character, optionally filtered to one arc.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `character_id` | `int` | Yes | Primary key of the character |
| `arc_id` | `int \| None` | No | Optional arc filter |

**Returns:** `list[ArcHealthLog]` — Health log entries ordered by `chapter_id ASC`. Empty list is valid when no health logs exist.

**Invocation reason:** Called during revision to review how the character arc has been tracking — seeing a pattern of "at-risk" health assessments signals where narrative attention is needed.

**Gate status:** Gate-free.

**Tables touched:** Reads `arc_health_log`, `character_arcs`.

---

#### `get_subplot_touchpoint_gaps`

**Purpose:** Return active subplots that are overdue for a touchpoint based on the threshold.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `threshold_chapters` | `int` | No (default: `5`) | Chapters without touchpoint before subplot is overdue |

**Returns:** `list[dict]` — List of dicts with keys: `plot_thread_id`, `name`, `last_touchpoint_chapter_id`, `chapters_since_touchpoint`. Ordered by `chapters_since_touchpoint DESC` (NULLs last). Empty when no subplots exceed the threshold.

**Invocation reason:** Called during chapter planning to catch neglected subplots — if a subplot hasn't appeared in 5 chapters, the agent should consider weaving it back into the upcoming chapter.

**Gate status:** Gate-free.

**Tables touched:** Reads `plot_threads`, `subplot_touchpoint_log`, `chapters`.

---

#### `upsert_chekov`

**Purpose:** Create a new Chekhov's gun entry or update an existing one. Two-branch because no UNIQUE beyond PK.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `chekov_id` | `int \| None` | Yes | Existing gun id to update, or None to create |
| `name` | `str` | Yes | Name/label for the element |
| `description` | `str` | Yes | Description of the planted element |
| `planted_chapter_id` | `int \| None` | No | Chapter where element was planted |
| `planted_scene_id` | `int \| None` | No | Scene where element was planted |
| `payoff_chapter_id` | `int \| None` | No | Chapter where element pays off |
| `payoff_scene_id` | `int \| None` | No | Scene where element pays off |
| `status` | `str \| None` | No (default: `"planted"`) | Status — "planted", "fired" |
| `notes` | `str \| None` | No | Free-form notes |
| `canon_status` | `str \| None` | No (default: `"draft"`) | Canon status — "draft", "canon" |

**Returns:** `ChekhovGun | ValidationFailure` — The created or updated `ChekhovGun`; `ValidationFailure` on DB error.

**Invocation reason:** Called when planting a narrative element that must pay off later; called again with the same id to fill in `payoff_chapter_id` when the element fires.

**Gate status:** Gate-free.

**Tables touched:** Reads `chekovs_gun_registry`. Writes `chekovs_gun_registry`.

---

#### `log_arc_health`

**Purpose:** Append an arc health log entry for a character arc at a chapter (append-only).

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `arc_id` | `int` | Yes | FK to character_arcs — the arc being assessed |
| `chapter_id` | `int` | Yes | FK to chapters — the chapter at which the assessment is recorded |
| `health_status` | `str` | No (default: `"on-track"`) | Status — "on-track", "at-risk", "derailed" |
| `notes` | `str \| None` | No | Free-form notes about the arc's health |

**Returns:** `ArcHealthLog | ValidationFailure` — The newly created `ArcHealthLog` row; `ValidationFailure` on DB error.

**Invocation reason:** Called after completing each chapter draft to record an arc health snapshot — creates a progression log that surfaces trends during manuscript review.

**Gate status:** Gate-free.

**Tables touched:** Writes `arc_health_log`.

---

## Gate Domain

Manages the architecture gate — the certification mechanism that blocks prose-phase tools until all 36 worldbuilding requirements are verified. Tools are gate-free themselves (they manage the gate, not use it).

**Gate status:** All tools in this domain are gate-free (gate tools manage the gate, they do not check it).

**5 tools**

---

#### `get_gate_status`

**Purpose:** Return the current certification status of the architecture gate.

**Parameters:** None

**Returns:** `dict | NotFoundResponse` — Dict with `gate_id`, `is_certified`, `certified_at`, `certified_by`, `blocking_item_count`; `NotFoundResponse` if the gate row (id=1) is missing.

**Invocation reason:** Called at the start of any session to determine whether the gate is certified — if not certified, prose-phase tools are blocked and the agent should focus on worldbuilding.

**Gate status:** Gate-free (gate tools are exempt from their own checks).

**Tables touched:** Reads `architecture_gate`, `gate_checklist_items`.

---

#### `get_gate_checklist`

**Purpose:** Return all 36 checklist items for the architecture gate ordered by category and item_key.

**Parameters:** None

**Returns:** `list[GateChecklistItem]` — All checklist items ordered by `category, item_key`. Returns empty list if no items have been populated yet (run `run_gate_audit` to populate).

**Invocation reason:** Called to inspect the detailed breakdown of passing and failing gate items — identifies exactly which worldbuilding gaps remain before certification.

**Gate status:** Gate-free.

**Tables touched:** Reads `gate_checklist_items`.

---

#### `run_gate_audit`

**Purpose:** Execute all 36 gate evidence queries, update `gate_checklist_items`, and return a `GateAuditReport`.

**Parameters:** None

**Returns:** `GateAuditReport | NotFoundResponse` — `GateAuditReport` with `total_items`, `passing_count`, `failing_count`, and full items list; `NotFoundResponse` if `architecture_gate id=1` is missing.

**Invocation reason:** Called after completing worldbuilding tasks to check whether the gate requirements are now satisfied. Does NOT certify the gate — call `certify_gate` separately after all items pass.

**Gate status:** Gate-free.

**Tables touched:** Reads all worldbuilding tables (36 SQL queries). Writes `gate_checklist_items`.

---

#### `update_checklist_item`

**Purpose:** Manually override a gate checklist item's pass/fail state.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `item_key` | `str` | Yes | Unique key of the checklist item (e.g. "pop_characters") |
| `is_passing` | `bool` | Yes | Whether this item should be considered passing |
| `missing_count` | `int` | No (default: `0`) | Number of missing items (0 when is_passing=True) |
| `notes` | `str \| None` | No | Notes explaining the manual override |

**Returns:** `GateChecklistItem | NotFoundResponse` — The updated `GateChecklistItem`; `NotFoundResponse` if the item_key does not exist (run `run_gate_audit` first).

**Invocation reason:** Called when a gate item cannot be verified by SQL alone — allows human judgment to mark narrative completeness items as passing when the qualitative standard is met.

**Gate status:** Gate-free.

**Tables touched:** Reads `gate_checklist_items`. Writes `gate_checklist_items`.

---

#### `certify_gate`

**Purpose:** Certify the architecture gate if all checklist items are passing. Does NOT re-run the audit.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `certified_by` | `str \| None` | No | Name/identifier of who is certifying (default: "system") |

**Returns:** `ArchitectureGate | ValidationFailure` — The updated `ArchitectureGate` with `is_certified=True`; `ValidationFailure` listing how many items are still failing.

**Invocation reason:** Called after `run_gate_audit` confirms all 36 items pass — locks the gate as certified and unblocks all prose-phase tools. Run `run_gate_audit` first, then `certify_gate`.

**Gate status:** Gate-free.

**Tables touched:** Reads `gate_checklist_items`. Writes `architecture_gate`.

---

## Names Domain

Manages the name registry — a global uniqueness tracker for all names used in the story. Gate-free by locked design decision: name tools must work during worldbuilding before the gate is certified.

**Gate status:** All tools in this domain are gate-free (by design — name conflict checking is a pre-gate worldbuilding operation).

**4 tools**

---

#### `check_name`

**Purpose:** Check if a name is already registered using a case-insensitive exact match.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `name` | `str` | Yes | The name to look up (case-insensitive) |

**Returns:** `NameRegistryEntry | NotFoundResponse` — `NameRegistryEntry` if the name is taken; `NotFoundResponse` with "safe to use" message if not found.

**Invocation reason:** Called before creating a new character or location to avoid UNIQUE constraint conflicts — prevents introducing a name that has already been registered in any entity category.

**Gate status:** Gate-free.

**Tables touched:** Reads `name_registry`.

---

#### `register_name`

**Purpose:** Register a new name in the name registry. Returns `ValidationFailure` if the name already exists.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `name` | `str` | Yes | The name to register (must be unique) |
| `entity_type` | `str` | No (default: `"character"`) | Category — "character", "location", etc. |
| `culture_id` | `int \| None` | No | FK to cultures table |
| `linguistic_notes` | `str \| None` | No | Notes on etymology or pronunciation |
| `introduced_chapter_id` | `int \| None` | No | FK to chapters where name first appears |
| `notes` | `str \| None` | No | Additional notes |

**Returns:** `NameRegistryEntry | ValidationFailure` — `NameRegistryEntry` with id on success; `ValidationFailure` if the name already exists (wraps `aiosqlite.IntegrityError`).

**Invocation reason:** Called during character and location creation to register the name centrally — ensures the gate item `names_characters` and `names_locations` can be satisfied. Use `check_name` first to avoid errors.

**Gate status:** Gate-free.

**Tables touched:** Writes `name_registry`.

---

#### `get_name_registry`

**Purpose:** Retrieve all name registry entries with optional filters by `entity_type` and/or `culture_id`.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `entity_type` | `str \| None` | No | Filter by entity category — "character", "location" |
| `culture_id` | `int \| None` | No | Filter by culture FK |

**Returns:** `list[NameRegistryEntry]` — All matching entries ordered by `name ASC`. Empty list if no entries match.

**Invocation reason:** Called to audit name coverage — verifying that all characters and locations have been registered before gate certification, or reviewing existing names before generating new ones.

**Gate status:** Gate-free.

**Tables touched:** Reads `name_registry`.

---

#### `generate_name_suggestions`

**Purpose:** Retrieve existing names and linguistic context for a culture to support consistent name generation.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `culture_id` | `int` | Yes | FK to cultures table |

**Returns:** `NameSuggestionsResult` — Contains `existing_names` (list of `NameRegistryEntry`), `linguistic_context` (naming conventions string or None), and `culture_id`. Never returns an error — missing culture returns None for `linguistic_context`.

**Invocation reason:** Called when creating new characters or locations from a specific culture — provides the existing name patterns and linguistic conventions so new names fit established cultural phonetics.

**Gate status:** Gate-free.

**Tables touched:** Reads `name_registry`, `cultures`.

---

## Structure Domain

Manages story-level 7-point structural beats (story_structure table with one row per book) and per-arc 7-point beats (arc_seven_point_beats table). Gate-free because these tools populate data that gate checks evaluate.

**Gate status:** All tools in this domain are gate-free (structure tools populate data that gate queries check — they must work before certification).

**4 tools**

---

#### `get_story_structure`

**Purpose:** Retrieve the story structure row for a book.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `book_id` | `int` | Yes | Primary key of the book |

**Returns:** `StoryStructure | NotFoundResponse` — `StoryStructure` record with all 7 beat chapter references and 3-act references; `NotFoundResponse` if no structure has been defined for the book.

**Invocation reason:** Called at the start of chapter planning to verify which story-level structural beats have been assigned to which chapters — ensures the current chapter draft fits the overall narrative architecture.

**Gate status:** Gate-free.

**Tables touched:** Reads `story_structure`.

---

#### `upsert_story_structure`

**Purpose:** Create or update the story structure for a book (single-branch ON CONFLICT(book_id)).

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `book_id` | `int` | Yes | Primary key of the book |
| `hook_chapter_id` | `int \| None` | No | Chapter containing the story hook |
| `plot_turn_1_chapter_id` | `int \| None` | No | Chapter of first plot turn |
| `pinch_1_chapter_id` | `int \| None` | No | Chapter of first pinch point |
| `midpoint_chapter_id` | `int \| None` | No | Chapter of the midpoint |
| `pinch_2_chapter_id` | `int \| None` | No | Chapter of second pinch point |
| `plot_turn_2_chapter_id` | `int \| None` | No | Chapter of second plot turn |
| `resolution_chapter_id` | `int \| None` | No | Chapter of the resolution |
| `act_1_inciting_incident_chapter_id` | `int \| None` | No | 3-act inciting incident chapter |
| `act_2_midpoint_chapter_id` | `int \| None` | No | 3-act Act 2 midpoint chapter |
| `act_3_climax_chapter_id` | `int \| None` | No | 3-act climax chapter |
| `notes` | `str \| None` | No | Free-form notes |

**Returns:** `StoryStructure | ValidationFailure` — The created or updated `StoryStructure` record; `ValidationFailure` on DB error.

**Invocation reason:** Called during outlining to map the 7-point structure to specific chapters — required for the `struct_story_beats` gate item which checks all 7 beat chapter references are non-null.

**Gate status:** Gate-free.

**Tables touched:** Reads `story_structure`. Writes `story_structure`.

---

#### `get_arc_beats`

**Purpose:** Retrieve all 7-point beat records for a character arc, ordered by beat_type.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `arc_id` | `int` | Yes | Primary key of the arc |

**Returns:** `list[ArcSevenPointBeat]` — All beat records ordered by `beat_type`. Empty list is valid for arcs with no beats yet defined.

**Invocation reason:** Called when reviewing a character's arc against the 7-point structure — checks whether all beats (hook, plot_turn_1, pinch_1, midpoint, pinch_2, plot_turn_2, resolution) have been assigned chapters.

**Gate status:** Gate-free.

**Tables touched:** Reads `arc_seven_point_beats`.

---

#### `upsert_arc_beat`

**Purpose:** Create or update a single 7-point beat for a character arc. Validates `beat_type` at the Python level.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `arc_id` | `int` | Yes | FK to character_arcs |
| `beat_type` | `str` | Yes | One of: "hook", "plot_turn_1", "pinch_1", "midpoint", "pinch_2", "plot_turn_2", "resolution" |
| `chapter_id` | `int \| None` | No | Chapter where this beat occurs |
| `notes` | `str \| None` | No | Free-form notes |

**Returns:** `ArcSevenPointBeat | ValidationFailure` — The created or updated `ArcSevenPointBeat`; `ValidationFailure` on invalid `beat_type` or DB error.

**Invocation reason:** Called when mapping a character's arc to the 7-point structure — required for the `arcs_seven_point_beats` gate item which checks all 7 beats have a chapter_id assigned.

**Gate status:** Gate-free.

**Tables touched:** Reads `arc_seven_point_beats`. Writes `arc_seven_point_beats`.

---

## Session Domain

Manages writing session lifecycle, project metrics snapshots, POV balance analysis, open questions, and agent run auditing. All tools require gate certification — session tools are prose-phase operations.

**Gate status:** All tools in this domain require gate certification (returns `GateViolation` if not certified).

**10 tools**

---

#### `start_session`

**Purpose:** Start a new writing session and return a briefing from the prior session. Auto-closes any open session before creating the new one.

**Parameters:** None

**Returns:** `SessionStartResult | GateViolation` — `SessionStartResult` containing the new `SessionLog` and an optional prior-session briefing `SessionLog`; `GateViolation` if gate is not certified.

**Invocation reason:** Called at the very start of each writing session — auto-closes stale open sessions, creates a new session record, and provides the prior session's summary and carried-forward questions as context.

**Gate status:** Requires gate certification (returns `GateViolation` if not certified).

**Tables touched:** Reads `session_logs`. Writes `session_logs`.

---

#### `close_session`

**Purpose:** Close an open session, record summary and metadata, and auto-populate `carried_forward` from unanswered open questions.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `session_id` | `int` | Yes | Primary key of the open session to close |
| `summary` | `str \| None` | No | Summary of work done this session |
| `word_count_delta` | `int` | No (default: `0`) | Net word count change this session |
| `chapters_touched` | `list[int] \| None` | No | List of chapter IDs worked on |

**Returns:** `SessionLog | NotFoundResponse | GateViolation` — Updated `SessionLog` row; `NotFoundResponse` if session not found or already closed; `GateViolation` if gate not certified.

**Invocation reason:** Called at the end of each writing session to record what was accomplished and snapshot all unanswered open questions into `carried_forward` for the next session's briefing.

**Gate status:** Requires gate certification.

**Tables touched:** Reads `session_logs`, `open_questions`. Writes `session_logs`.

---

#### `get_last_session`

**Purpose:** Retrieve the most recently started session log entry.

**Parameters:** None

**Returns:** `SessionLog | NotFoundResponse | GateViolation` — Most recent `SessionLog`; `NotFoundResponse` if no sessions exist; `GateViolation` if gate not certified.

**Invocation reason:** Called to review what was last worked on when resuming a project — provides context without starting a new session.

**Gate status:** Requires gate certification.

**Tables touched:** Reads `session_logs`.

---

#### `log_agent_run`

**Purpose:** Append an agent run entry to the audit trail (append-only, no UNIQUE constraint).

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `agent_name` | `str` | Yes | Name of the agent that ran |
| `tool_name` | `str` | Yes | Name of the tool the agent called |
| `input_summary` | `str \| None` | No | Brief description of the tool input |
| `output_summary` | `str \| None` | No | Brief description of the tool output |
| `duration_ms` | `int \| None` | No | Duration in milliseconds |
| `success` | `bool` | No (default: `True`) | Whether the run succeeded |
| `session_id` | `int \| None` | No | FK to session_logs |
| `error_message` | `str \| None` | No | Error description if success is False |

**Returns:** `AgentRunLog | GateViolation` — The newly created `AgentRunLog` row; `GateViolation` if gate not certified.

**Invocation reason:** Called after each significant tool invocation during prose drafting to maintain an audit trail — useful for debugging multi-agent workflows and understanding which tools were called in a session.

**Gate status:** Requires gate certification.

**Tables touched:** Writes `agent_run_log`.

---

#### `get_project_metrics`

**Purpose:** Retrieve live-computed project metrics (aggregated directly from DB, not stored snapshots).

**Parameters:** None

**Returns:** `ProjectMetricsSnapshot | GateViolation` — `ProjectMetricsSnapshot` with live `word_count` (from `actual_word_count`), `chapter_count`, `scene_count`, `character_count`, `session_count` (id and snapshot_at are None for live results); `GateViolation` if gate not certified.

**Invocation reason:** Called at the start of a session to assess current project progress — provides a live dashboard of word count and structural completion without persisting a snapshot.

**Gate status:** Requires gate certification.

**Tables touched:** Reads `chapters`, `scenes`, `characters`, `session_logs`.

---

#### `log_project_snapshot`

**Purpose:** Persist a project metrics snapshot to the database for historical tracking.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `notes` | `str \| None` | No | Optional notes to store with the snapshot |

**Returns:** `ProjectMetricsSnapshot | GateViolation` — The newly created `ProjectMetricsSnapshot` row with `id` and `snapshot_at` populated; `GateViolation` if gate not certified.

**Invocation reason:** Called at significant milestones (completing a draft chapter, finishing a revision pass) to create a persistent progress record — enables tracking velocity and word count growth over time.

**Gate status:** Requires gate certification.

**Tables touched:** Reads `chapters`, `scenes`, `characters`, `session_logs`. Writes `project_metrics_snapshots`.

---

#### `get_pov_balance`

**Purpose:** Retrieve live-computed POV balance across all chapters, grouped by POV character.

**Parameters:** None

**Returns:** `list[PovBalanceSnapshot] | GateViolation` — List of `PovBalanceSnapshot` records ordered by `chapter_count DESC`; `GateViolation` if gate not certified. Empty list if no chapters have POV characters assigned.

**Invocation reason:** Called during revision to check whether POV chapter distribution is proportional to each character's narrative importance — identifies characters who are over- or under-represented.

**Gate status:** Requires gate certification.

**Tables touched:** Reads `chapters`.

---

#### `get_open_questions`

**Purpose:** Retrieve all unanswered open questions (answered_at IS NULL), optionally filtered by domain.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `domain` | `str \| None` | No | Optional domain filter — "plot", "character", "world" |

**Returns:** `list[OpenQuestion] | GateViolation` — All unanswered `OpenQuestion` records ordered by `created_at ASC`; `GateViolation` if gate not certified.

**Invocation reason:** Called at session start to review unresolved narrative questions from prior sessions — ensures no open plot or character question is forgotten across sessions.

**Gate status:** Requires gate certification.

**Tables touched:** Reads `open_questions`.

---

#### `log_open_question`

**Purpose:** Append a new open question to the log (append-only — duplicate questions allowed).

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `question` | `str` | Yes | The question text |
| `domain` | `str \| None` | No (default: `"general"`) | Domain classification — "plot", "character", "world" |
| `session_id` | `int \| None` | No | FK to session_logs |
| `priority` | `str \| None` | No (default: `"normal"`) | Priority — "high", "normal", "low" |
| `notes` | `str \| None` | No | Freeform notes |

**Returns:** `OpenQuestion | GateViolation` — The newly created `OpenQuestion` row; `GateViolation` if gate not certified.

**Invocation reason:** Called during drafting whenever a narrative question arises that requires a decision — prevents questions from being lost and ensures they surface in the next session's briefing via `carried_forward`.

**Gate status:** Requires gate certification.

**Tables touched:** Writes `open_questions`.

---

#### `answer_open_question`

**Purpose:** Mark an open question as answered, recording the answer and setting `answered_at`.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `question_id` | `int` | Yes | Primary key of the open_questions row |
| `answer` | `str` | Yes | The answer text to record |

**Returns:** `OpenQuestion | NotFoundResponse | GateViolation` — Updated `OpenQuestion` with `answered_at` populated; `NotFoundResponse` if question_id not found; `GateViolation` if gate not certified.

**Invocation reason:** Called when a narrative decision is made that resolves a previously logged open question — updates the record so the question no longer appears in `get_open_questions` results.

**Gate status:** Requires gate certification.

**Tables touched:** Reads `open_questions`. Writes `open_questions`.

---

## Timeline Domain

Manages story timeline events, POV character chronological positions, and travel segment tracking. Includes travel realism validation. All tools are gated.

**Gate status:** All tools in this domain require gate certification (returns `GateViolation` if not certified).

**8 tools**

---

#### `get_pov_positions`

**Purpose:** Retrieve all POV character chronological positions at a given chapter.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `chapter_id` | `int` | Yes | The chapter to look up positions for |

**Returns:** `list[PovChronologicalPosition] | GateViolation` — All `PovChronologicalPosition` records for the chapter ordered by `character_id ASC`; `GateViolation` if gate not certified. Empty list if no positions recorded.

**Invocation reason:** Called when opening a multi-POV chapter to verify where all POV characters are positioned in the story timeline — prevents chronological contradictions.

**Gate status:** Requires gate certification.

**Tables touched:** Reads `pov_chronological_position`.

---

#### `get_pov_position`

**Purpose:** Retrieve a specific POV character's chronological position at a given chapter.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `character_id` | `int` | Yes | The character whose position to retrieve |
| `chapter_id` | `int` | Yes | The chapter at which to retrieve the position |

**Returns:** `PovChronologicalPosition | NotFoundResponse | GateViolation` — The `PovChronologicalPosition` record; `NotFoundResponse` if not found; `GateViolation` if gate not certified.

**Invocation reason:** Called before writing a chapter from a specific POV to verify the in-story date and location at that point in the timeline.

**Gate status:** Requires gate certification.

**Tables touched:** Reads `pov_chronological_position`.

---

#### `get_event`

**Purpose:** Retrieve a single timeline event by primary key.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `event_id` | `int` | Yes | Primary key of the events row |

**Returns:** `Event | NotFoundResponse | GateViolation` — Full `Event` record; `NotFoundResponse` if not found; `GateViolation` if gate not certified.

**Invocation reason:** Called to retrieve the details of a specific story event when referencing it in scene or chapter drafts — verifies event type, in-story date, and significance.

**Gate status:** Requires gate certification.

**Tables touched:** Reads `events`.

---

#### `list_events`

**Purpose:** List timeline events with optional chapter or chapter-range filters.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `chapter_id` | `int \| None` | No | Exact chapter filter (takes priority over range) |
| `start_chapter` | `int \| None` | No | Lower bound of chapter range (inclusive) |
| `end_chapter` | `int \| None` | No | Upper bound of chapter range (inclusive) |

**Returns:** `list[Event] | GateViolation` — `Event` records ordered by `chapter_id ASC, id ASC`; `GateViolation` if gate not certified. Empty list if no events match.

**Invocation reason:** Called when planning a chapter to understand what story events occur at that point in the timeline — ensures scene drafts are consistent with recorded events.

**Gate status:** Requires gate certification.

**Tables touched:** Reads `events`.

---

#### `get_travel_segments`

**Purpose:** Retrieve all travel segments for a character ordered chronologically. Returns empty list (not NotFoundResponse) when no travel exists.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `character_id` | `int` | Yes | The character whose travel segments to retrieve |

**Returns:** `list[TravelSegment] | GateViolation` — All `TravelSegment` records ordered by `start_chapter_id ASC, id ASC`; `GateViolation` if gate not certified.

**Invocation reason:** Called before drafting a chapter where a character arrives at a new location — verifies the travel history to ensure the journey is logistically consistent.

**Gate status:** Requires gate certification.

**Tables touched:** Reads `travel_segments`.

---

#### `validate_travel_realism`

**Purpose:** Validate whether travel between locations is realistic given elapsed in-story time.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `travel_segment_id` | `int \| None` | No | Validate a single travel segment by ID |
| `character_id` | `int \| None` | No | Validate all travel segments for a character |

**Returns:** `TravelValidationResult | GateViolation` — `TravelValidationResult` with `is_realistic`, `issues` list, and optional `segment`; `GateViolation` if gate not certified. At least one of the ID parameters must be provided.

**Invocation reason:** Called when a character travels between locations to verify the journey is plausible — checks elapsed_days, travel_method, and missing endpoints; returns specific issues for correction.

**Gate status:** Requires gate certification.

**Tables touched:** Reads `travel_segments`.

---

#### `upsert_event`

**Purpose:** Create or update a timeline event. Two-branch upsert on event_id.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `name` | `str` | Yes | Event name |
| `event_type` | `str \| None` | No (default: `"plot"`) | Type — "conflict", "revelation", "travel" |
| `chapter_id` | `int \| None` | No | Chapter where the event occurs |
| `location_id` | `int \| None` | No | Location where the event occurs |
| `in_story_date` | `str \| None` | No | In-story date string |
| `duration` | `str \| None` | No | Duration description |
| `summary` | `str \| None` | No | Brief summary |
| `significance` | `str \| None` | No | Narrative significance notes |
| `notes` | `str \| None` | No | Freeform notes |
| `canon_status` | `str \| None` | No (default: `"draft"`) | Canon status — "draft", "confirmed" |
| `event_id` | `int \| None` | No | If provided, update the existing event with this ID |

**Returns:** `Event | GateViolation` — The created or updated `Event` row; `GateViolation` if gate not certified.

**Invocation reason:** Called after drafting a chapter to record significant story events for timeline consistency — creates a queryable record of when events occur relative to chapters.

**Gate status:** Requires gate certification.

**Tables touched:** Reads `events`. Writes `events`.

---

#### `upsert_pov_position`

**Purpose:** Create or update a POV character chronological position at a chapter.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `character_id` | `int` | Yes | The POV character |
| `chapter_id` | `int` | Yes | The chapter at which to record the position |
| `in_story_date` | `str \| None` | No | In-story date string at this position |
| `day_number` | `int \| None` | No | Story day number at this position |
| `location_id` | `int \| None` | No | Location at this chapter |
| `notes` | `str \| None` | No | Freeform notes |

**Returns:** `PovChronologicalPosition | GateViolation` — The created or updated `PovChronologicalPosition` row; `GateViolation` if gate not certified.

**Invocation reason:** Called after completing each chapter draft to record the POV character's story-time position — builds the chronological record that prevents timeline inconsistencies in later chapters.

**Gate status:** Requires gate certification.

**Tables touched:** Reads `pov_chronological_position`. Writes `pov_chronological_position`.

---

## Canon Domain

Manages the canonical record: canon facts, story decisions log, and continuity issues. Canon facts, decisions, and continuity issues all use append-only INSERT (no ON CONFLICT) — they are audit log tables.

**Gate status:** All tools in this domain require gate certification (returns `GateViolation` if not certified).

**7 tools**

---

#### `get_canon_facts`

**Purpose:** Retrieve all canon facts for a given domain, ordered by `created_at`.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `domain` | `str` | Yes | Domain to filter by — "magic", "geography", "general", etc. |

**Returns:** `list[CanonFact] | GateViolation` — All `CanonFact` records for the domain; `GateViolation` if gate not certified.

**Invocation reason:** Called before drafting a scene that involves domain-specific facts — ensures narrative content is consistent with established canon in that domain.

**Gate status:** Requires gate certification.

**Tables touched:** Reads `canon_facts`.

---

#### `log_canon_fact`

**Purpose:** Log a new canon fact (append-only INSERT — creates a new row each call).

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `fact` | `str` | Yes | The canon fact text |
| `domain` | `str` | No (default: `"general"`) | Domain the fact belongs to |
| `source_chapter_id` | `int \| None` | No | Chapter where the fact was established |
| `source_event_id` | `int \| None` | No | Event that established the fact |
| `parent_fact_id` | `int \| None` | No | Parent fact this derives from |
| `certainty_level` | `str` | No (default: `"established"`) | Certainty level |
| `canon_status` | `str` | No (default: `"approved"`) | Canon status |
| `notes` | `str \| None` | No | Additional notes |

**Returns:** `CanonFact | GateViolation` — The newly created `CanonFact` record; `GateViolation` if gate not certified.

**Invocation reason:** Called when a story event definitively establishes a world fact — creates an authoritative record that future scenes can query to maintain consistency. Gate item `canon_domains` requires facts in at least 3 distinct domains.

**Gate status:** Requires gate certification.

**Tables touched:** Writes `canon_facts`.

---

#### `log_decision`

**Purpose:** Log a story decision with rationale to the decisions log (append-only).

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `description` | `str` | Yes | Description of the decision made |
| `decision_type` | `str` | No (default: `"plot"`) | Type — "plot", "character", "world" |
| `rationale` | `str \| None` | No | Why this decision was made |
| `alternatives` | `str \| None` | No | Alternatives that were considered |
| `session_id` | `int \| None` | No | Writing session this decision was made in |
| `chapter_id` | `int \| None` | No | Chapter this decision applies to |

**Returns:** `StoryDecision | GateViolation` — The newly created `StoryDecision` record; `GateViolation` if gate not certified.

**Invocation reason:** Called when logging a completed story decision to maintain an audit trail of why narrative choices were made — enables later review of decision rationale and supports consistent storytelling across long manuscripts.

**Gate status:** Requires gate certification.

**Tables touched:** Writes `decisions_log`.

---

#### `get_decisions`

**Purpose:** Retrieve the decisions log with optional filters by `decision_type` and/or `chapter_id`.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `decision_type` | `str \| None` | No | Filter by decision type |
| `chapter_id` | `int \| None` | No | Filter by chapter |

**Returns:** `list[StoryDecision] | GateViolation` — All matching `StoryDecision` records ordered by `created_at DESC`; `GateViolation` if gate not certified.

**Invocation reason:** Called when reviewing why specific narrative decisions were made — helpful during revision to understand the reasoning behind earlier choices and whether those choices still serve the story.

**Gate status:** Requires gate certification.

**Tables touched:** Reads `decisions_log`.

---

#### `log_continuity_issue`

**Purpose:** Log a new continuity issue with severity triage (append-only).

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `description` | `str` | Yes | Description of the continuity issue |
| `severity` | `str` | No (default: `"minor"`) | Severity — "minor", "major", "critical" |
| `chapter_id` | `int \| None` | No | Chapter where the issue occurs |
| `scene_id` | `int \| None` | No | Scene where the issue occurs |
| `canon_fact_id` | `int \| None` | No | Canon fact this issue relates to |

**Returns:** `ContinuityIssue | GateViolation` — The newly created `ContinuityIssue` record; `GateViolation` if gate not certified.

**Invocation reason:** Called when detecting a contradiction between a draft and previously established facts — records the issue for later resolution without interrupting the drafting flow.

**Gate status:** Requires gate certification.

**Tables touched:** Writes `continuity_issues`.

---

#### `get_continuity_issues`

**Purpose:** Retrieve open continuity issues with optional severity filter. Open issues only by default.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `severity` | `str \| None` | No | Filter by severity |
| `include_resolved` | `bool` | No (default: `False`) | Include resolved issues |

**Returns:** `list[ContinuityIssue] | GateViolation` — All matching `ContinuityIssue` records ordered by `created_at ASC`; `GateViolation` if gate not certified.

**Invocation reason:** Called during revision passes to systematically work through outstanding continuity issues — reviewing by severity ensures critical contradictions are resolved before minor ones.

**Gate status:** Requires gate certification.

**Tables touched:** Reads `continuity_issues`.

---

#### `resolve_continuity_issue`

**Purpose:** Resolve a continuity issue by ID, recording the resolution note.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `issue_id` | `int` | Yes | ID of the continuity issue to resolve |
| `resolution_note` | `str` | Yes | Description of how the issue was resolved |

**Returns:** `ContinuityIssue | NotFoundResponse | GateViolation` — The updated `ContinuityIssue` with `is_resolved=True`; `NotFoundResponse` if issue_id not found (SELECT-back after UPDATE detects missing row); `GateViolation` if gate not certified.

**Invocation reason:** Called after editing a chapter to fix a documented continuity issue — marks the issue as resolved so it no longer appears in `get_continuity_issues` results.

**Gate status:** Requires gate certification.

**Tables touched:** Reads `continuity_issues`. Writes `continuity_issues`.

---

## Knowledge Domain

Manages reader-facing information asymmetry: what the reader knows vs what characters know. Includes dramatic irony inventory, reader reveals, and reader information states. All tools are gated.

**Gate status:** All tools in this domain require gate certification (returns `GateViolation` if not certified).

**5 tools**

---

#### `get_reader_state`

**Purpose:** Retrieve cumulative reader information state up to a given chapter (all rows with chapter_id <= requested).

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `chapter_id` | `int` | Yes | Chapter boundary (inclusive) — returns all state from chapter 1 through this chapter |

**Returns:** `list[ReaderInformationState] | GateViolation` — All `ReaderInformationState` records up to the chapter ordered by `chapter_id ASC`; `GateViolation` if gate not certified.

**Invocation reason:** Called before drafting a chapter to understand the cumulative information advantage the reader has at that story point — ensures dramatic irony is leveraged correctly and no reveals are accidentally repeated.

**Gate status:** Requires gate certification.

**Tables touched:** Reads `reader_information_states`.

---

#### `get_dramatic_irony_inventory`

**Purpose:** Retrieve the dramatic irony inventory, unresolved only by default.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `include_resolved` | `bool` | No (default: `False`) | If True, include resolved entries |
| `chapter_id` | `int \| None` | No | Optional chapter filter |

**Returns:** `list[DramaticIronyEntry] | GateViolation` — All matching `DramaticIronyEntry` records ordered by `created_at ASC`; `GateViolation` if gate not certified.

**Invocation reason:** Called during chapter planning to inventory active dramatic irony situations — ensures the agent exploits known information gaps when writing character reactions and dialogue.

**Gate status:** Requires gate certification.

**Tables touched:** Reads `dramatic_irony_inventory`.

---

#### `get_reader_reveals`

**Purpose:** Retrieve planned and actual reader reveals with optional chapter filter.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `chapter_id` | `int \| None` | No | Optional chapter filter |

**Returns:** `list[ReaderReveal] | GateViolation` — All matching `ReaderReveal` records ordered by `created_at ASC`; `GateViolation` if gate not certified.

**Invocation reason:** Called when planning a chapter's information revelations — verifies what has been planned vs what has actually been written, ensuring the reveal schedule is on track.

**Gate status:** Requires gate certification.

**Tables touched:** Reads `reader_reveals`.

---

#### `upsert_reader_state`

**Purpose:** Create or update a reader information state entry. Two-branch upsert: by (chapter_id, domain) when no id provided; by primary key when id provided.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `chapter_id` | `int` | Yes | Chapter this reader state entry is associated with |
| `domain` | `str` | Yes | Knowledge domain — "magic", "character", "plot" |
| `information` | `str` | Yes | The information state description |
| `reader_state_id` | `int \| None` | No | If provided, upsert by primary key; otherwise upsert by (chapter_id, domain) |
| `revealed_how` | `str \| None` | No | How this was revealed to the reader |
| `notes` | `str \| None` | No | Freeform notes |

**Returns:** `ReaderInformationState | GateViolation` — The created or updated `ReaderInformationState` row; `GateViolation` if gate not certified.

**Invocation reason:** Called after completing a chapter that reveals new information to the reader — records the revelation so future reader_state queries accurately reflect cumulative reader knowledge.

**Gate status:** Requires gate certification.

**Tables touched:** Reads `reader_information_states`. Writes `reader_information_states`.

---

#### `log_dramatic_irony`

**Purpose:** Log a new dramatic irony entry (append-only — each call creates a distinct record).

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `chapter_id` | `int` | Yes | Chapter where this dramatic irony begins |
| `reader_knows` | `str` | Yes | Description of what the reader knows |
| `character_doesnt_know` | `str` | Yes | Description of what the character doesn't know |
| `character_id` | `int \| None` | No | Optional FK to the character who doesn't know |
| `irony_type` | `str` | No (default: `"situational"`) | Type — "situational", "tragic", "comic" |
| `tension_level` | `int` | No (default: `5`) | Tension intensity 1-10 |
| `resolved_chapter_id` | `int \| None` | No | Chapter where the irony resolves (if known) |
| `notes` | `str \| None` | No | Freeform notes |

**Returns:** `DramaticIronyEntry | GateViolation` — The newly created `DramaticIronyEntry` row; `GateViolation` if gate not certified.

**Invocation reason:** Called after creating a scene where the reader is given information a character lacks — registers the irony for subsequent exploitation in the reader's experience.

**Gate status:** Requires gate certification.

**Tables touched:** Writes `dramatic_irony_inventory`.

---

## Foreshadowing Domain

Manages foreshadowing plants and payoffs, prophecies, motifs, thematic mirrors, and opposition pairs. `log_foreshadowing` is an upsert (allows payoff to be filled later); `log_motif_occurrence` is append-only.

**Gate status:** All tools in this domain require gate certification (returns `GateViolation` if not certified).

**8 tools**

---

#### `get_foreshadowing`

**Purpose:** Retrieve foreshadowing entries with optional status and chapter filters.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `status` | `str \| None` | No | Filter by status — "planted", "paid_off" |
| `chapter_id` | `int \| None` | No | Filter by `plant_chapter_id` |

**Returns:** `list[ForeshadowingEntry] | GateViolation` — All matching `ForeshadowingEntry` records ordered by `plant_chapter_id ASC`; `GateViolation` if gate not certified.

**Invocation reason:** Called before drafting a chapter to review planted but unpaid foreshadowing — ensures the agent can weave callbacks to earlier planted elements and advance them toward payoff.

**Gate status:** Requires gate certification.

**Tables touched:** Reads `foreshadowing_registry`.

---

#### `get_prophecies`

**Purpose:** Retrieve all prophecy registry entries ordered by `created_at`.

**Parameters:** None

**Returns:** `list[ProphecyEntry] | GateViolation` — All `ProphecyEntry` records; `GateViolation` if gate not certified.

**Invocation reason:** Called when planning chapters that fulfill or allude to prophecies — verifies the prophecy text and current fulfillment status.

**Gate status:** Requires gate certification.

**Tables touched:** Reads `prophecy_registry`.

---

#### `get_motifs`

**Purpose:** Retrieve all motif registry entries ordered by `created_at`.

**Parameters:** None

**Returns:** `list[MotifEntry] | GateViolation` — All `MotifEntry` records; `GateViolation` if gate not certified.

**Invocation reason:** Called when reviewing thematic elements before drafting — ensures recurring motifs are consciously woven through scenes at appropriate frequencies.

**Gate status:** Requires gate certification.

**Tables touched:** Reads `motif_registry`.

---

#### `get_motif_occurrences`

**Purpose:** Retrieve motif occurrences filtered by motif and/or chapter.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `motif_id` | `int \| None` | No | Filter by motif |
| `chapter_id` | `int \| None` | No | Filter by chapter |

**Returns:** `list[MotifOccurrence] | GateViolation` — All matching `MotifOccurrence` records ordered by `created_at ASC`; `GateViolation` if gate not certified.

**Invocation reason:** Called to audit how frequently a motif has appeared and where — informs pacing decisions about whether to include another occurrence or allow a gap before the next appearance.

**Gate status:** Requires gate certification.

**Tables touched:** Reads `motif_occurrences`.

---

#### `get_thematic_mirrors`

**Purpose:** Retrieve all thematic mirror pairs ordered by `created_at`.

**Parameters:** None

**Returns:** `list[ThematicMirror] | GateViolation` — All `ThematicMirror` records; `GateViolation` if gate not certified.

**Invocation reason:** Called when planning scenes that feature mirrored characters or situations — ensures the structural parallels are recognized and intentionally reinforced in the draft.

**Gate status:** Requires gate certification.

**Tables touched:** Reads `thematic_mirrors`.

---

#### `get_opposition_pairs`

**Purpose:** Retrieve all opposition pairs ordered by `created_at`.

**Parameters:** None

**Returns:** `list[OppositionPair] | GateViolation` — All `OppositionPair` records; `GateViolation` if gate not certified.

**Invocation reason:** Called when drafting scenes featuring opposing forces — verifies the documented opposition dynamics to ensure scenes authentically capture the established conflict structure.

**Gate status:** Requires gate certification.

**Tables touched:** Reads `opposition_pairs`.

---

#### `log_foreshadowing`

**Purpose:** Log or update a foreshadowing entry. Two-branch upsert: plain INSERT when no id; ON CONFLICT(id) DO UPDATE when id provided (allows payoff to be filled in later).

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `description` | `str` | Yes | Description of the foreshadowing plant or callback |
| `plant_chapter_id` | `int` | Yes | Chapter where the foreshadowing is planted |
| `foreshadowing_id` | `int \| None` | No | If provided, upsert the existing entry |
| `plant_scene_id` | `int \| None` | No | Scene where foreshadowing is planted |
| `payoff_chapter_id` | `int \| None` | No | Chapter where it pays off |
| `payoff_scene_id` | `int \| None` | No | Scene where it pays off |
| `foreshadowing_type` | `str` | No (default: `"direct"`) | Type of foreshadowing |
| `status` | `str` | No (default: `"planted"`) | Status — "planted", "paid_off" |
| `notes` | `str \| None` | No | Additional notes |

**Returns:** `ForeshadowingEntry | GateViolation` — The created or updated `ForeshadowingEntry` record; `GateViolation` if gate not certified.

**Invocation reason:** Called when planting a foreshadowing element (None id creates new row), and again when the payoff occurs (provided id fills in `payoff_chapter_id` and sets status to "paid_off"). Gate item `foreshadowing_planted` requires at least one planted entry.

**Gate status:** Requires gate certification.

**Tables touched:** Reads `foreshadowing_registry`. Writes `foreshadowing_registry`.

---

#### `log_motif_occurrence`

**Purpose:** Log a new motif occurrence (append-only — each call creates a distinct record).

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `motif_id` | `int` | Yes | FK to `motif_registry` |
| `chapter_id` | `int` | Yes | Chapter where the motif appears |
| `scene_id` | `int \| None` | No | Scene where the motif appears |
| `description` | `str \| None` | No | Description of how the motif manifests |
| `occurrence_type` | `str` | No (default: `"direct"`) | Type — "direct", "symbolic", "inverted" |
| `notes` | `str \| None` | No | Additional notes |

**Returns:** `MotifOccurrence | GateViolation` — The newly created `MotifOccurrence` record; `GateViolation` if gate not certified.

**Invocation reason:** Called after drafting a scene that features a recurring motif — records each appearance as a discrete historical event for frequency analysis and thematic review.

**Gate status:** Requires gate certification.

**Tables touched:** Writes `motif_occurrences`.

---

## Voice Domain

Manages character voice profiles, supernatural voice guidelines, and voice drift detection. All tools are gated — voice is a prose-phase concern requiring gate certification.

**Gate status:** All tools in this domain require gate certification (returns `GateViolation` if not certified).

**5 tools**

---

#### `get_voice_profile`

**Purpose:** Retrieve the voice profile for a character.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `character_id` | `int` | Yes | ID of the character whose voice profile to fetch |

**Returns:** `VoiceProfile | NotFoundResponse | GateViolation` — `VoiceProfile` if found; `NotFoundResponse` if no profile exists for the character; `GateViolation` if gate not certified.

**Invocation reason:** Called before writing dialogue for a character — loads sentence length preferences, verbal tics, vocabulary level, and dialogue sample to ensure the agent maintains consistent voice across all scenes.

**Gate status:** Requires gate certification.

**Tables touched:** Reads `voice_profiles`.

---

#### `upsert_voice_profile`

**Purpose:** Create or update a voice profile for a character. Two-branch upsert on `character_id` (UNIQUE column).

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `character_id` | `int` | Yes | ID of the character (UNIQUE — one profile per character) |
| `profile_id` | `int \| None` | No | Existing profile ID for update branch |
| `sentence_length` | `str \| None` | No | Typical sentence length style |
| `vocabulary_level` | `str \| None` | No | Vocabulary complexity level |
| `speech_patterns` | `str \| None` | No | Notable speech patterns |
| `verbal_tics` | `str \| None` | No | Repeated verbal tics or mannerisms |
| `avoids` | `str \| None` | No | Words or constructions the character avoids |
| `internal_voice_notes` | `str \| None` | No | Notes on internal monologue voice |
| `dialogue_sample` | `str \| None` | No | Sample dialogue illustrating the voice |
| `notes` | `str \| None` | No | Additional notes |
| `canon_status` | `str` | No (default: `"draft"`) | Canon status |

**Returns:** `VoiceProfile | GateViolation` — The created or updated `VoiceProfile`; `GateViolation` if gate not certified.

**Invocation reason:** Called during worldbuilding (after gate certification) to establish each character's documented voice, and during revision to refine the voice guidelines based on what emerged during drafting. Gate item `voice_pov` checks all POV characters have a profile.

**Gate status:** Requires gate certification.

**Tables touched:** Reads `voice_profiles`. Writes `voice_profiles`.

---

#### `get_supernatural_voice_guidelines`

**Purpose:** Retrieve all supernatural voice guidelines ordered by `element_name`.

**Parameters:** None

**Returns:** `list[SupernaturalVoiceGuideline] | GateViolation` — All guidelines ordered by `element_name ASC`; `GateViolation` if gate not certified.

**Invocation reason:** Called before writing scenes involving supernatural entities — loads the documented voice rules for non-human speech patterns to maintain consistency across appearances.

**Gate status:** Requires gate certification.

**Tables touched:** Reads `supernatural_voice_guidelines`.

---

#### `log_voice_drift`

**Purpose:** Log a voice drift event for a character (append-only).

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `character_id` | `int` | Yes | ID of the character exhibiting voice drift |
| `description` | `str` | Yes | Description of the drift observed |
| `drift_type` | `str` | No (default: `"vocabulary"`) | Category — "vocabulary", "syntax", "tone" |
| `severity` | `str` | No (default: `"minor"`) | Severity — "minor", "moderate", "major" |
| `chapter_id` | `int \| None` | No | Chapter where drift was observed |
| `scene_id` | `int \| None` | No | Scene where drift was observed |

**Returns:** `VoiceDriftLog | GateViolation` — The newly created `VoiceDriftLog` record; `GateViolation` if gate not certified.

**Invocation reason:** Called when the drafting agent detects that a character's dialogue has drifted from their established voice profile — creates an audit record for the revision pass.

**Gate status:** Requires gate certification.

**Tables touched:** Writes `voice_drift_log`.

---

#### `get_voice_drift_log`

**Purpose:** Retrieve voice drift log entries for a character, ordered by `created_at DESC`. Empty list is valid.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `character_id` | `int` | Yes | ID of the character whose drift log to fetch |

**Returns:** `list[VoiceDriftLog] | GateViolation` — All drift entries ordered by `created_at DESC`; `GateViolation` if gate not certified. Empty list is a valid response (no drift = good voice consistency).

**Invocation reason:** Called during a voice consistency review pass — examines the drift history to identify patterns in how and where a character's voice breaks down.

**Gate status:** Requires gate certification.

**Tables touched:** Reads `voice_drift_log`.

---

## Publishing Domain

Manages publishing assets (query letters, synopses), submission tracking, and submission status updates. All tools are gated — publishing is a final-stage prose-phase operation.

**Gate status:** All tools in this domain require gate certification (returns `GateViolation` if not certified).

**5 tools**

---

#### `get_publishing_assets`

**Purpose:** Retrieve all publishing assets with optional `asset_type` filter, ordered by `created_at DESC`.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `asset_type` | `str \| None` | No | Filter by category — "query_letter", "synopsis" |

**Returns:** `list[PublishingAsset] | GateViolation` — All matching `PublishingAsset` records ordered by `created_at DESC`; `GateViolation` if gate not certified.

**Invocation reason:** Called to review existing query letters or synopses before drafting a new version — ensures prior assets are considered and the new version represents an improvement.

**Gate status:** Requires gate certification.

**Tables touched:** Reads `publishing_assets`.

---

#### `upsert_publishing_asset`

**Purpose:** Create or update a publishing asset. Two-branch upsert on `id` (PK — no named UNIQUE beyond PK).

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `title` | `str` | Yes | Title of the publishing asset |
| `content` | `str` | Yes | Full text content of the asset |
| `asset_id` | `int \| None` | No | Existing asset ID for update branch |
| `asset_type` | `str` | No (default: `"query_letter"`) | Category — "query_letter", "synopsis" |
| `version` | `int` | No (default: `1`) | Version number |
| `status` | `str` | No (default: `"draft"`) | Publication status |
| `notes` | `str \| None` | No | Additional notes |

**Returns:** `PublishingAsset | GateViolation` — The created or updated `PublishingAsset`; `GateViolation` if gate not certified.

**Invocation reason:** Called when creating or revising a query letter or synopsis — the None-id branch creates a new asset; the provided-id branch updates an existing one, enabling version management.

**Gate status:** Requires gate certification.

**Tables touched:** Reads `publishing_assets`. Writes `publishing_assets`.

---

#### `get_submissions`

**Purpose:** Retrieve all submission tracker entries with optional `status` filter, ordered by `submitted_at DESC`.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `status` | `str \| None` | No | Filter by status — "pending", "accepted", "rejected" |

**Returns:** `list[SubmissionEntry] | GateViolation` — All matching `SubmissionEntry` records ordered by `submitted_at DESC`; `GateViolation` if gate not certified.

**Invocation reason:** Called to review the current submission pipeline — identifies pending submissions requiring follow-up and provides a complete submission history.

**Gate status:** Requires gate certification.

**Tables touched:** Reads `submission_tracker`.

---

#### `log_submission`

**Purpose:** Log a new submission to an agency or publisher (append-only).

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `agency_or_publisher` | `str` | Yes | Name of the agency or publisher |
| `submitted_at` | `str` | Yes | ISO date/datetime of submission |
| `asset_id` | `int \| None` | No | FK to `publishing_assets` |
| `status` | `str` | No (default: `"pending"`) | Initial status |
| `notes` | `str \| None` | No | Additional notes |

**Returns:** `SubmissionEntry | GateViolation` — The newly created `SubmissionEntry` with id; `GateViolation` if gate not certified.

**Invocation reason:** Called when submitting a query letter or manuscript to an agency or publisher — creates a permanent submission record for tracking response timelines.

**Gate status:** Requires gate certification.

**Tables touched:** Writes `submission_tracker`.

---

#### `update_submission`

**Purpose:** Partially update a submission tracker entry. SELECT-back after UPDATE detects missing rows.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `submission_id` | `int` | Yes | ID of the submission to update |
| `status` | `str` | Yes | New submission status |
| `response_at` | `str \| None` | No | Date/datetime when a response was received |
| `response_notes` | `str \| None` | No | Notes on the response |
| `follow_up_due` | `str \| None` | No | Date/datetime for next follow-up |

**Returns:** `SubmissionEntry | NotFoundResponse | GateViolation` — The updated `SubmissionEntry`; `NotFoundResponse` if `submission_id` not found (SQLite does not error on UPDATE of missing row — SELECT-back detects it); `GateViolation` if gate not certified.

**Invocation reason:** Called when a response is received from an agency — updates status from "pending" to "accepted" or "rejected" and records the response date and notes.

**Gate status:** Requires gate certification.

**Tables touched:** Reads `submission_tracker`. Writes `submission_tracker`.

---

*End of Drafter MCP Tools Reference — 103 tools across 18 domains*
