[← Documentation Index](../README.md)

# World Tools

Manages world-building entities: locations, factions, faction political states, cultures, eras, books, acts, artifacts, and object states. Locations have a JSON `sensory_profile` field; factions are UNIQUE by name. Political states are a separate time-stamped log not written by `upsert_faction`.

**Gate status:** All tools in this domain are gate-free.

**33 tools**

## Index

| Tool Name | Gate | Description |
|-----------|------|-------------|
| `get_location` | Free | Look up a single location by ID |
| `get_faction` | Free | Look up a single faction by ID |
| `get_faction_political_state` | Free | Return the political state for a faction at a specific chapter or the most recent state |
| `get_culture` | Free | Look up a single culture record by ID |
| `upsert_location` | Free | Create a new location or update an existing one |
| `upsert_faction` | Free | Create or update a faction |
| `get_book` | Free | Look up a single book by ID |
| `list_books` | Free | Return all books ordered by series_order then id |
| `upsert_book` | Free | Create or update a book record |
| `delete_book` | Free | Delete a book record by ID (FK-safe) |
| `get_era` | Free | Look up a single era by ID |
| `list_eras` | Free | Return all eras ordered by sequence_order then name |
| `upsert_era` | Free | Create or update an era record |
| `delete_era` | Free | Delete an era record by ID (FK-safe) |
| `delete_location` | Free | Delete a location record by ID (FK-safe) |
| `delete_faction` | Free | Delete a faction record by ID (FK-safe) |
| `upsert_culture` | Free | Create or update a culture record |
| `list_cultures` | Free | Return all cultures ordered by name |
| `delete_culture` | Free | Delete a culture record by ID (FK-safe) |
| `log_faction_political_state` | Free | Record a political state snapshot for a faction at a specific chapter |
| `get_current_faction_political_state` | Free | Return the most recent political state record for a faction |
| `delete_faction_political_state` | Free | Delete a faction political state entry by primary key |
| `get_act` | Free | Look up a single act by ID |
| `list_acts` | Free | Return all acts for a given book ordered by act_number |
| `upsert_act` | Free | Create or update an act record |
| `delete_act` | Free | Delete an act record by ID |
| `get_artifact` | Free | Look up a single artifact by ID |
| `list_artifacts` | Free | Return all artifacts ordered by name |
| `upsert_artifact` | Free | Create or update an artifact record |
| `delete_artifact` | Free | Delete an artifact record by ID (FK-safe) |
| `get_object_states` | Free | Return all state records for an artifact ordered by chapter_id |
| `log_object_state` | Free | Record the state of an artifact at a specific chapter |
| `delete_object_state` | Free | Delete an object state entry by primary key |

---

## `get_location`

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

## `get_faction`

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

## `get_faction_political_state`

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

## `get_culture`

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

## `upsert_location`

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

## `upsert_faction`

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

## `get_book`

**Purpose:** Look up a single book by ID, returning all fields.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `book_id` | `int` | Yes | Primary key of the book to retrieve |

**Returns:** `Book | NotFoundResponse` — `Book` with all fields if found; `NotFoundResponse` if no book with that ID exists.

**Invocation reason:** Called to load book metadata (title, series_order, word count targets) before performing chapter or act operations that require the book context.

**Gate status:** Gate-free.

**Tables touched:** Reads `books`.

---

## `list_books`

**Purpose:** Return all books ordered by series_order then id.

**Parameters:** None

**Returns:** `list[Book]` — All book records ordered by `series_order` (nulls last), then `id`. Returns an empty list if no books exist.

**Invocation reason:** Called when generating a project overview or building navigation for a multi-book series — provides the full list of books with their status and word count targets.

**Gate status:** Gate-free.

**Tables touched:** Reads `books`.

---

## `upsert_book`

**Purpose:** Create or update a book record.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `book_id` | `int \| None` | Yes | Existing book ID to update, or None to create |
| `title` | `str` | Yes | Book title (required) |
| `series_order` | `int \| None` | No | Position in the series (optional) |
| `word_count_target` | `int \| None` | No | Target word count (optional) |
| `actual_word_count` | `int` | No | Actual word count written so far (default: 0) |
| `status` | `str` | No | Drafting status — e.g. "planning", "drafting", "complete" (default: "planning") |
| `notes` | `str \| None` | No | Free-form notes (optional) |
| `canon_status` | `str` | No | Canon status — e.g. "draft", "canon" (default: "draft") |

**Returns:** `Book | ValidationFailure` — The created or updated `Book`; `ValidationFailure` on DB error.

**Invocation reason:** Called during project initialization to create book records for a series, and during production to update word count progress and drafting status.

**Gate status:** Gate-free.

**Tables touched:** Reads `books`. Writes `books`.

---

## `delete_book`

**Purpose:** Delete a book record by ID if no FK children reference it.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `book_id` | `int` | Yes | Primary key of the book to delete |

**Returns:** `NotFoundResponse | ValidationFailure | dict` — `{"deleted": True, "id": book_id}` on success; `NotFoundResponse` if not found; `ValidationFailure` if FK constraints prevent deletion (acts, chapters, or story structures reference the book).

**Invocation reason:** Called to remove a book that was created in error — only safe when no acts, chapters, or story structures exist for it.

**Gate status:** Gate-free.

**Tables touched:** Reads `books`. Writes `books`.

---

## `get_era`

**Purpose:** Look up a single era by ID, returning all fields.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `era_id` | `int` | Yes | Primary key of the era to retrieve |

**Returns:** `Era | NotFoundResponse` — `Era` with all fields if found; `NotFoundResponse` if no era with that ID exists.

**Invocation reason:** Called to load era details for worldbuilding context — provides date ranges and certainty level before placing artifacts or characters in historical settings.

**Gate status:** Gate-free.

**Tables touched:** Reads `eras`.

---

## `list_eras`

**Purpose:** Return all eras ordered by sequence_order then name.

**Parameters:** None

**Returns:** `list[Era]` — All era records ordered by `sequence_order` (nulls last), then `name`. Returns an empty list if no eras exist.

**Invocation reason:** Called when building a timeline overview or resolving chronological references in worldbuilding — provides the full historical sequence of eras.

**Gate status:** Gate-free.

**Tables touched:** Reads `eras`.

---

## `upsert_era`

**Purpose:** Create or update an era record.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `era_id` | `int \| None` | Yes | Existing era ID to update, or None to create |
| `name` | `str` | Yes | Era name (required) |
| `sequence_order` | `int \| None` | No | Chronological order position (optional) |
| `date_start` | `str \| None` | No | Start date as text string (optional) |
| `date_end` | `str \| None` | No | End date as text string (optional) |
| `summary` | `str \| None` | No | Brief summary of the era (optional) |
| `certainty_level` | `str` | No | How established this era is (default: "established") |
| `notes` | `str \| None` | No | Free-form notes (optional) |
| `canon_status` | `str` | No | Canon status — e.g. "draft", "canon" (default: "draft") |

**Returns:** `Era | ValidationFailure` — The created or updated `Era`; `ValidationFailure` on DB error.

**Invocation reason:** Called during worldbuilding to define historical eras that provide context for artifacts and character backstories.

**Gate status:** Gate-free.

**Tables touched:** Reads `eras`. Writes `eras`.

---

## `delete_era`

**Purpose:** Delete an era record by ID if no FK children reference it.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `era_id` | `int` | Yes | Primary key of the era to delete |

**Returns:** `NotFoundResponse | ValidationFailure | dict` — `{"deleted": True, "id": era_id}` on success; `NotFoundResponse` if not found; `ValidationFailure` if FK constraints prevent deletion (artifacts or characters reference the era).

**Invocation reason:** Called to remove an era that was created in error — only safe when no artifacts or characters reference it via origin_era_id or home_era_id.

**Gate status:** Gate-free.

**Tables touched:** Reads `eras`. Writes `eras`.

---

## `delete_location`

**Purpose:** Delete a location record by ID if no FK children reference it.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `location_id` | `int` | Yes | Primary key of the location to delete |

**Returns:** `NotFoundResponse | ValidationFailure | dict` — `{"deleted": True, "id": location_id}` on success; `NotFoundResponse` if not found; `ValidationFailure` if FK constraints prevent deletion.

**Invocation reason:** Called to remove a location that was created in error — only safe when no factions, characters, or other records reference it.

**Gate status:** Gate-free.

**Tables touched:** Reads `locations`. Writes `locations`.

---

## `delete_faction`

**Purpose:** Delete a faction record by ID if no FK children reference it.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `faction_id` | `int` | Yes | Primary key of the faction to delete |

**Returns:** `NotFoundResponse | ValidationFailure | dict` — `{"deleted": True, "id": faction_id}` on success; `NotFoundResponse` if not found; `ValidationFailure` if FK constraints prevent deletion (faction_political_states or characters reference the faction).

**Invocation reason:** Called to remove a faction that was created in error — only safe when no political states or characters reference it.

**Gate status:** Gate-free.

**Tables touched:** Reads `factions`. Writes `factions`.

---

## `upsert_culture`

**Purpose:** Create or update a culture record. When `culture_id` is None, merges by name (ON CONFLICT(name)).

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `culture_id` | `int \| None` | Yes | Existing culture ID to update, or None to create/merge by name |
| `name` | `str` | Yes | Culture name — UNIQUE constraint (required) |
| `region` | `str \| None` | No | Geographic region of the culture (optional) |
| `language_family` | `str \| None` | No | Language family or linguistic grouping (optional) |
| `naming_conventions` | `str \| None` | No | Naming patterns and conventions (optional) |
| `social_structure` | `str \| None` | No | Description of social hierarchy (optional) |
| `values_beliefs` | `str \| None` | No | Core values and belief systems (optional) |
| `taboos` | `str \| None` | No | Cultural taboos and prohibitions (optional) |
| `aesthetic_style` | `str \| None` | No | Artistic and aesthetic preferences (optional) |
| `notes` | `str \| None` | No | Free-form notes (optional) |
| `canon_status` | `str` | No | Canon status (default: "draft") |
| `source_file` | `str \| None` | No | Source seed file if applicable (optional) |

**Returns:** `Culture | ValidationFailure` — The created or updated `Culture`; `ValidationFailure` on DB error.

**Invocation reason:** Called during worldbuilding to establish cultures that inform naming conventions, social dynamics, and location character — used by the names domain and character backstory tools.

**Gate status:** Gate-free.

**Tables touched:** Reads `cultures`. Writes `cultures`.

---

## `list_cultures`

**Purpose:** Return all cultures ordered by name.

**Parameters:** None

**Returns:** `list[Culture]` — All culture records ordered alphabetically by `name`. Returns an empty list if no cultures exist.

**Invocation reason:** Called when selecting a culture for a new location or character, or when auditing cultural diversity across the world — provides a full list for selection.

**Gate status:** Gate-free.

**Tables touched:** Reads `cultures`.

---

## `delete_culture`

**Purpose:** Delete a culture record by ID if no FK children reference it.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `culture_id` | `int` | Yes | Primary key of the culture to delete |

**Returns:** `NotFoundResponse | ValidationFailure | dict` — `{"deleted": True, "id": culture_id}` on success; `NotFoundResponse` if not found; `ValidationFailure` if FK constraints prevent deletion (locations or name_registry reference the culture).

**Invocation reason:** Called to remove a culture that was created in error — only safe when no locations or name registry entries reference it.

**Gate status:** Gate-free.

**Tables touched:** Reads `cultures`. Writes `cultures`.

---

## `log_faction_political_state`

**Purpose:** Record a political state snapshot for a faction at a specific chapter.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `faction_id` | `int` | Yes | FK to the faction whose state to record (required) |
| `chapter_id` | `int` | Yes | Chapter at which this state is recorded (required) |
| `power_level` | `int` | No | Power level 1-10 (default: 5) |
| `alliances` | `str \| None` | No | Current alliances description (optional) |
| `conflicts` | `str \| None` | No | Current conflicts description (optional) |
| `internal_state` | `str \| None` | No | Internal faction state description (optional) |
| `noted_by_character_id` | `int \| None` | No | FK to characters — who noted this state (optional) |
| `notes` | `str \| None` | No | Free-form notes (optional) |

**Returns:** `FactionPoliticalState | NotFoundResponse | ValidationFailure` — The newly created `FactionPoliticalState`; `NotFoundResponse` if faction_id does not exist; `ValidationFailure` on DB error.

**Invocation reason:** Called after major political events to snapshot a faction's current standing — provides historical context for how power dynamics evolved across the narrative.

**Gate status:** Gate-free.

**Tables touched:** Reads `factions`. Writes `faction_political_states`.

---

## `get_current_faction_political_state`

**Purpose:** Return the most recent political state record for a faction.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `faction_id` | `int` | Yes | ID of the faction whose most recent political state to retrieve |

**Returns:** `FactionPoliticalState | NotFoundResponse` — The most recent `FactionPoliticalState` for the faction; `NotFoundResponse` if no political state records exist.

**Invocation reason:** Called before drafting a scene involving a faction to confirm its current power level and alliance state — ensures faction behavior is consistent with its documented political trajectory.

**Gate status:** Gate-free.

**Tables touched:** Reads `faction_political_states`.

---

## `delete_faction_political_state`

**Purpose:** Delete a faction political state entry by primary key.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `political_state_id` | `int` | Yes | Primary key of the political state entry to delete |

**Returns:** `NotFoundResponse | dict` — `{"deleted": True, "id": political_state_id}` on success; `NotFoundResponse` if the record does not exist.

**Invocation reason:** Called to remove an incorrectly logged political state entry — faction_political_states is a log table with no FK children so deletion is always safe.

**Gate status:** Gate-free.

**Tables touched:** Reads `faction_political_states`. Writes `faction_political_states`.

---

## `get_act`

**Purpose:** Look up a single act by ID, returning all fields.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `act_id` | `int` | Yes | Primary key of the act to retrieve |

**Returns:** `Act | NotFoundResponse` — `Act` with all fields if found; `NotFoundResponse` if no act with that ID exists.

**Invocation reason:** Called to load act structure details before outlining chapters within that act — provides the act's narrative purpose and word count target.

**Gate status:** Gate-free.

**Tables touched:** Reads `acts`.

---

## `list_acts`

**Purpose:** Return all acts for a given book, ordered by act_number.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `book_id` | `int` | Yes | ID of the book whose acts to list |

**Returns:** `list[Act]` — All act records for the book ordered by `act_number`. Returns an empty list if no acts exist.

**Invocation reason:** Called when reviewing the structural outline of a book — shows all acts with their boundaries and purposes for structural planning.

**Gate status:** Gate-free.

**Tables touched:** Reads `acts`.

---

## `upsert_act`

**Purpose:** Create or update an act record. Pre-checks that book_id exists before writing.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `act_id` | `int \| None` | Yes | Existing act ID to update, or None to create |
| `book_id` | `int` | Yes | FK to books — the book this act belongs to (required) |
| `act_number` | `int` | Yes | Act number within the book — UNIQUE per book (required) |
| `name` | `str \| None` | No | Act name or title (optional) |
| `purpose` | `str \| None` | No | Narrative purpose of the act (optional) |
| `word_count_target` | `int \| None` | No | Target word count for this act (optional) |
| `start_chapter_id` | `int \| None` | No | FK to chapters — first chapter of the act (optional) |
| `end_chapter_id` | `int \| None` | No | FK to chapters — last chapter of the act (optional) |
| `structural_notes` | `str \| None` | No | Notes on act structure (optional) |
| `canon_status` | `str` | No | Canon status (default: "draft") |

**Returns:** `Act | NotFoundResponse | ValidationFailure` — The created or updated `Act`; `NotFoundResponse` if book_id does not exist; `ValidationFailure` on DB error.

**Invocation reason:** Called during structural planning to define the book's act structure before populating chapters — start/end chapter IDs can be updated later once chapters are created.

**Gate status:** Gate-free.

**Tables touched:** Reads `books`. Writes `acts`.

---

## `delete_act`

**Purpose:** Delete an act record by ID.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `act_id` | `int` | Yes | Primary key of the act to delete |

**Returns:** `NotFoundResponse | ValidationFailure | dict` — `{"deleted": True, "id": act_id}` on success; `NotFoundResponse` if not found; `ValidationFailure` if FK constraints prevent deletion.

**Invocation reason:** Called to remove an act that was created in error or restructured out of the narrative.

**Gate status:** Gate-free.

**Tables touched:** Reads `acts`. Writes `acts`.

---

## `get_artifact`

**Purpose:** Look up a single artifact by ID, returning all fields.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `artifact_id` | `int` | Yes | Primary key of the artifact to retrieve |

**Returns:** `Artifact | NotFoundResponse` — `Artifact` with all fields if found; `NotFoundResponse` if no artifact with that ID exists.

**Invocation reason:** Called before placing an artifact in a scene to confirm its current owner, location, and magical properties — ensures consistent artifact handling.

**Gate status:** Gate-free.

**Tables touched:** Reads `artifacts`.

---

## `list_artifacts`

**Purpose:** Return all artifacts ordered by name.

**Parameters:** None

**Returns:** `list[Artifact]` — All artifact records ordered alphabetically by `name`. Returns an empty list if no artifacts exist.

**Invocation reason:** Called when generating a world inventory or checking for prop continuity across chapters — provides the full list of tracked artifacts.

**Gate status:** Gate-free.

**Tables touched:** Reads `artifacts`.

---

## `upsert_artifact`

**Purpose:** Create or update an artifact record.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `artifact_id` | `int \| None` | Yes | Existing artifact ID to update, or None to create |
| `name` | `str` | Yes | Artifact name (required) |
| `artifact_type` | `str \| None` | No | Category — e.g. "weapon", "relic", "document" (optional) |
| `current_owner_id` | `int \| None` | No | FK to characters — current owner (optional) |
| `current_location_id` | `int \| None` | No | FK to locations — current location (optional) |
| `origin_era_id` | `int \| None` | No | FK to eras — era of origin (optional) |
| `description` | `str \| None` | No | Narrative description (optional) |
| `significance` | `str \| None` | No | Story significance (optional) |
| `magical_properties` | `str \| None` | No | Magical or special properties (optional) |
| `history` | `str \| None` | No | Historical background (optional) |
| `notes` | `str \| None` | No | Free-form notes (optional) |
| `canon_status` | `str` | No | Canon status (default: "draft") |
| `source_file` | `str \| None` | No | Source seed file if applicable (optional) |

**Returns:** `Artifact | ValidationFailure` — The created or updated `Artifact`; `ValidationFailure` on DB error.

**Invocation reason:** Called during worldbuilding to register significant objects — provides a record of each artifact's properties and history for consistent prop handling in scenes.

**Gate status:** Gate-free.

**Tables touched:** Reads `artifacts`. Writes `artifacts`.

---

## `delete_artifact`

**Purpose:** Delete an artifact record by ID if no FK children reference it.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `artifact_id` | `int` | Yes | Primary key of the artifact to delete |

**Returns:** `NotFoundResponse | ValidationFailure | dict` — `{"deleted": True, "id": artifact_id}` on success; `NotFoundResponse` if not found; `ValidationFailure` if FK constraints prevent deletion (object_states or event_artifacts reference the artifact).

**Invocation reason:** Called to remove an artifact that was created in error — only safe when no object states or event artifact links exist for it.

**Gate status:** Gate-free.

**Tables touched:** Reads `artifacts`. Writes `artifacts`.

---

## `get_object_states`

**Purpose:** Return all state records for an artifact, ordered by chapter_id.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `artifact_id` | `int` | Yes | ID of the artifact whose state history to retrieve |

**Returns:** `list[ObjectState]` — All `ObjectState` records for the artifact ordered by `chapter_id`. Returns an empty list if no states have been recorded.

**Invocation reason:** Called to review the ownership and condition history of an artifact across the narrative — confirms the artifact's current state before placing it in a new scene.

**Gate status:** Gate-free.

**Tables touched:** Reads `object_states`.

---

## `log_object_state`

**Purpose:** Record the state of an artifact at a specific chapter. Pre-checks both artifact_id and chapter_id FKs.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `artifact_id` | `int` | Yes | FK to the artifact whose state to record (required) |
| `chapter_id` | `int` | Yes | Chapter at which this state is recorded (required) |
| `condition` | `str` | No | State of the artifact — e.g. "intact", "damaged", "destroyed" (default: "intact") |
| `owner_id` | `int \| None` | No | FK to characters — current owner at this chapter (optional) |
| `location_id` | `int \| None` | No | FK to locations — current location at this chapter (optional) |
| `notes` | `str \| None` | No | Free-form notes (optional) |

**Returns:** `ObjectState | NotFoundResponse | ValidationFailure` — The newly created `ObjectState`; `NotFoundResponse` if artifact_id or chapter_id do not exist; `ValidationFailure` on DB error.

**Invocation reason:** Called after any chapter where an artifact changes hands, location, or condition — maintains a complete audit trail of the artifact's state across the story.

**Gate status:** Gate-free.

**Tables touched:** Reads `artifacts`, `chapters`. Writes `object_states`.

---

## `delete_object_state`

**Purpose:** Delete an object state entry by primary key.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `object_state_id` | `int` | Yes | Primary key of the object state entry to delete |

**Returns:** `NotFoundResponse | dict` — `{"deleted": True, "id": object_state_id}` on success; `NotFoundResponse` if the record does not exist.

**Invocation reason:** Called to remove an incorrectly logged object state entry — object_states is a leaf table with no FK children so deletion is always safe.

**Gate status:** Gate-free.

**Tables touched:** Reads `object_states`. Writes `object_states`.

---
