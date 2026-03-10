[← Documentation Index](../README.md)

# Characters Tools

Manages the core character registry, character state across chapters (injuries, beliefs, knowledge, location), and character knowledge acquisition. All tools are gate-free because character data is needed during both worldbuilding and prose phases.

**Gate status:** All tools in this domain are gate-free.

**19 tools**

## Index

| Tool Name | Gate | Description |
|-----------|------|-------------|
| `get_character` | Free | Look up a single character by ID |
| `list_characters` | Free | Return all characters ordered alphabetically |
| `upsert_character` | Free | Create or update a character |
| `get_character_injuries` | Free | Return injury records for a character |
| `get_character_beliefs` | Free | Return all belief records for a character |
| `get_character_knowledge` | Free | Return knowledge records for a character |
| `log_character_knowledge` | Free | Insert a new knowledge record for a character |
| `get_character_location` | Free | Return location records for a character |
| `delete_character` | Free | Delete a character by ID (FK-safe) |
| `delete_character_knowledge` | Free | Delete a character knowledge record by ID (log-delete) |
| `log_character_belief` | Free | Append a belief record for a character |
| `delete_character_belief` | Free | Delete a character belief record by ID (log-delete) |
| `log_character_location` | Free | Append a location record for a character |
| `get_current_character_location` | Free | Return the most recent location record for a character |
| `delete_character_location` | Free | Delete a character location record by ID (log-delete) |
| `log_injury_state` | Free | Append an injury state record for a character |
| `delete_injury_state` | Free | Delete an injury state record by ID (log-delete) |
| `log_title_state` | Free | Append a title or role state record for a character |
| `delete_title_state` | Free | Delete a title state record by ID (log-delete) |

---

## `get_character`

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

## `list_characters`

**Purpose:** Return all characters ordered alphabetically by name.

**Parameters:** None

**Returns:** `list[Character]` — All character records. Returns an empty list if no characters have been created.

**Invocation reason:** Called when building a cast list, checking for name conflicts, or generating a project overview. Useful for roster validation before beginning a new chapter.

**Gate status:** Gate-free.

**Tables touched:** Reads `characters`.

---

## `upsert_character`

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

## `get_character_injuries`

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

## `get_character_beliefs`

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

## `get_character_knowledge`

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

## `log_character_knowledge`

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

## `get_character_location`

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

## `delete_character`

**Purpose:** Delete a character record by ID if no FK children reference it.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `character_id` | `int` | Yes | Primary key of the character to delete |

**Returns:** `NotFoundResponse | ValidationFailure | dict` — `{"deleted": True, "id": character_id}` on success; `NotFoundResponse` if character does not exist; `ValidationFailure` if FK constraints prevent deletion.

**Invocation reason:** Called to remove a character that was created in error or is no longer needed in the story — only safe when no arcs, relationships, or other records reference the character.

**Gate status:** Gate-free.

**Tables touched:** Reads `characters`. Writes `characters`.

---

## `delete_character_knowledge`

**Purpose:** Delete a character knowledge record by primary key.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `knowledge_id` | `int` | Yes | Primary key of the knowledge record to delete |

**Returns:** `NotFoundResponse | dict` — `{"deleted": True, "id": knowledge_id}` on success; `NotFoundResponse` if the record does not exist.

**Invocation reason:** Called to remove an incorrectly logged knowledge entry for a character — character_knowledge is a log table with no FK children so deletion is always safe.

**Gate status:** Gate-free.

**Tables touched:** Reads `character_knowledge`. Writes `character_knowledge`.

---

## `log_character_belief`

**Purpose:** Append a new belief record for a character at a specific chapter.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `character_id` | `int` | Yes | FK to the character holding this belief |
| `chapter_id` | `int` | Yes | Chapter at which this belief is held |
| `belief_text` | `str` | Yes | The belief content |
| `belief_type` | `str` | No | Category of belief — e.g. "core", "situational" (default: "core") |
| `certainty` | `str` | No | Certainty level — e.g. "certain", "uncertain" (default: "certain") |
| `formed_chapter_id` | `int \| None` | No | FK to chapter where this belief was formed (optional) |
| `notes` | `str \| None` | No | Free-form notes (optional) |

**Returns:** `CharacterBelief | NotFoundResponse | ValidationFailure` — The newly created `CharacterBelief`; `NotFoundResponse` if character_id or chapter_id does not exist; `ValidationFailure` on DB error.

**Invocation reason:** Called to record a character's belief state at a specific story point — establishes the belief history for consistency checking during later chapters.

**Gate status:** Gate-free.

**Tables touched:** Reads `characters`, `chapters`. Writes `character_beliefs`.

---

## `delete_character_belief`

**Purpose:** Delete a character belief record by primary key.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `belief_id` | `int` | Yes | Primary key of the belief record to delete |

**Returns:** `NotFoundResponse | dict` — `{"deleted": True, "id": belief_id}` on success; `NotFoundResponse` if the record does not exist.

**Invocation reason:** Called to remove an incorrectly logged belief entry — character_beliefs is a log table with no FK children so deletion is always safe.

**Gate status:** Gate-free.

**Tables touched:** Reads `character_beliefs`. Writes `character_beliefs`.

---

## `log_character_location`

**Purpose:** Append a new location record for a character at a specific chapter.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `character_id` | `int` | Yes | FK to the character whose location to record |
| `chapter_id` | `int` | Yes | Chapter at which this location is recorded |
| `location_id` | `int \| None` | No | FK to locations table (optional) |
| `location_description` | `str \| None` | No | Free-text location description if no FK (optional) |
| `notes` | `str \| None` | No | Free-form notes (optional) |

**Returns:** `CharacterLocation | NotFoundResponse | ValidationFailure` — The newly created `CharacterLocation`; `NotFoundResponse` if character_id or chapter_id does not exist; `ValidationFailure` on DB error.

**Invocation reason:** Called to establish where a character is at a specific chapter — feeds the travel-realism validation and prevents scene placement contradictions.

**Gate status:** Gate-free.

**Tables touched:** Reads `characters`, `chapters`. Writes `character_locations`.

---

## `get_current_character_location`

**Purpose:** Return the most recent location record for a character.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `character_id` | `int` | Yes | ID of the character whose current location to retrieve |

**Returns:** `CharacterLocation | NotFoundResponse` — The most recent `CharacterLocation` for the character; `NotFoundResponse` if no location records exist.

**Invocation reason:** Called before placing a character in a scene to confirm their last known location — prevents scene continuity errors.

**Gate status:** Gate-free.

**Tables touched:** Reads `character_locations`.

---

## `delete_character_location`

**Purpose:** Delete a character location record by primary key.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `location_record_id` | `int` | Yes | Primary key of the location record to delete |

**Returns:** `NotFoundResponse | dict` — `{"deleted": True, "id": location_record_id}` on success; `NotFoundResponse` if the record does not exist.

**Invocation reason:** Called to remove an incorrectly logged location entry — character_locations is a log table with no FK children so deletion is always safe.

**Gate status:** Gate-free.

**Tables touched:** Reads `character_locations`. Writes `character_locations`.

---

## `log_injury_state`

**Purpose:** Append a new injury state record for a character at a specific chapter.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `character_id` | `int` | Yes | FK to the character whose injury to record |
| `chapter_id` | `int` | Yes | Chapter at which this injury state is recorded |
| `injury_description` | `str` | Yes | Description of the injury |
| `severity` | `str` | No | Severity level — e.g. "minor", "moderate", "severe" (default: "minor") |
| `is_healed` | `bool` | No | Whether the injury has healed (default: False) |
| `notes` | `str \| None` | No | Free-form notes (optional) |

**Returns:** `InjuryState | NotFoundResponse | ValidationFailure` — The newly created `InjuryState`; `NotFoundResponse` if character_id or chapter_id does not exist; `ValidationFailure` on DB error.

**Invocation reason:** Called to track a character's physical condition across chapters — used to ensure injury effects are consistently applied in subsequent scenes.

**Gate status:** Gate-free.

**Tables touched:** Reads `characters`, `chapters`. Writes `injury_states`.

---

## `delete_injury_state`

**Purpose:** Delete an injury state record by primary key.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `injury_id` | `int` | Yes | Primary key of the injury state record to delete |

**Returns:** `NotFoundResponse | dict` — `{"deleted": True, "id": injury_id}` on success; `NotFoundResponse` if the record does not exist.

**Invocation reason:** Called to remove an incorrectly logged injury entry — injury_states is a log table with no FK children so deletion is always safe.

**Gate status:** Gate-free.

**Tables touched:** Reads `injury_states`. Writes `injury_states`.

---

## `log_title_state`

**Purpose:** Append a new title/rank state record for a character at a specific chapter.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `character_id` | `int` | Yes | FK to the character whose title to record |
| `chapter_id` | `int` | Yes | Chapter at which this title state is recorded |
| `title` | `str` | Yes | The title or rank held |
| `title_type` | `str` | No | Category of title — e.g. "noble", "military", "religious" (default: "noble") |
| `is_current` | `bool` | No | Whether this is the current active title (default: True) |
| `notes` | `str \| None` | No | Free-form notes (optional) |

**Returns:** `TitleState | NotFoundResponse | ValidationFailure` — The newly created `TitleState`; `NotFoundResponse` if character_id or chapter_id does not exist; `ValidationFailure` on DB error.

**Invocation reason:** Called to record changes in a character's social standing or rank — ensures honorifics and titles are used consistently in dialogue and narration.

**Gate status:** Gate-free.

**Tables touched:** Reads `characters`, `chapters`. Writes `title_states`.

---

## `delete_title_state`

**Purpose:** Delete a title state record by primary key.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `title_id` | `int` | Yes | Primary key of the title state record to delete |

**Returns:** `NotFoundResponse | dict` — `{"deleted": True, "id": title_id}` on success; `NotFoundResponse` if the record does not exist.

**Invocation reason:** Called to remove an incorrectly logged title entry — title_states is a log table with no FK children so deletion is always safe.

**Gate status:** Gate-free.

**Tables touched:** Reads `title_states`. Writes `title_states`.

---
