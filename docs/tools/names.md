[← Documentation Index](../README.md)

# Names Tools

Manages the name registry — a global uniqueness tracker for all names used in the story. Gate-free by locked design decision: name tools must work during worldbuilding before the gate is certified.

**Gate status:** All tools in this domain are gate-free (by design — name conflict checking is a pre-gate worldbuilding operation).

**6 tools**

## Index

| Tool Name | Gate | Description |
|-----------|------|-------------|
| `check_name` | Free | Check if a name is already registered |
| `register_name` | Free | Register a new name in the name registry |
| `get_name_registry` | Free | Retrieve all name registry entries |
| `generate_name_suggestions` | Free | Retrieve name data to support consistent name generation |
| `upsert_name_registry_entry` | Free | Create or update a name registry entry |
| `delete_name_registry_entry` | Free | Delete a name registry entry by ID (FK-safe) |

---

## `check_name`

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

## `register_name`

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

## `get_name_registry`

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

## `generate_name_suggestions`

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

## `upsert_name_registry_entry`

**Purpose:** Create or update a name registry entry.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `entry_id` | `int \| None` | Yes | Existing entry ID to update, or None to create |
| `name` | `str` | Yes | The name to register — must be unique in the registry (required) |
| `entity_type` | `str` | No | Category of entity (default: "character") |
| `culture_id` | `int \| None` | No | FK to cultures table (optional) |
| `linguistic_notes` | `str \| None` | No | Notes on name etymology or pronunciation (optional) |
| `introduced_chapter_id` | `int \| None` | No | FK to chapters — chapter where name first appears (optional) |
| `notes` | `str \| None` | No | Additional notes (optional) |

**Returns:** `NameRegistryEntry | ValidationFailure` — The created or updated `NameRegistryEntry`; `ValidationFailure` on DB error (e.g. UNIQUE constraint violation if name already exists).

**Invocation reason:** Called to register a new name after confirming availability via `check_name` — ensures all names used in the story are tracked for uniqueness and cultural consistency.

**Gate status:** Gate-free.

**Tables touched:** Reads `name_registry`. Writes `name_registry`.

---

## `delete_name_registry_entry`

**Purpose:** Delete a name registry entry by its integer primary key. FK-safe.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `name_registry_id` | `int` | Yes | Primary key (id) of the name registry entry to delete |

**Returns:** `NotFoundResponse | ValidationFailure | dict` — `{"deleted": True, "id": name_registry_id}` on success; `NotFoundResponse` if not found; `ValidationFailure` if FK constraints prevent deletion.

**Invocation reason:** Called to remove a name registry entry for a name that was retired or logged in error — uses the integer primary key (not the name string) for unambiguous deletion.

**Gate status:** Gate-free.

**Tables touched:** Reads `name_registry`. Writes `name_registry`.

---
