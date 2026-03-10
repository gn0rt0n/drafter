[← Documentation Index](../README.md)

# Knowledge Tools

Manages reader-facing information asymmetry: what the reader knows vs what characters know. Includes dramatic irony inventory, reader reveals, and reader information states. All tools are gated.

**Gate status:** All tools in this domain require gate certification (returns `GateViolation` if not certified).

**12 tools**

## Index

| Tool Name | Gate | Description |
|-----------|------|-------------|
| `get_reader_state` | Gated | Retrieve cumulative reader information state up to a chapter |
| `get_dramatic_irony_inventory` | Gated | Retrieve the dramatic irony inventory |
| `get_reader_reveals` | Gated | Retrieve planned and actual reader reveals |
| `upsert_reader_state` | Gated | Create or update a reader information state entry |
| `log_dramatic_irony` | Gated | Log a new dramatic irony entry (append-only) |
| `delete_reader_state` | Gated | Delete a reader information state entry by ID (FK-safe) |
| `delete_dramatic_irony` | Gated | Delete a dramatic irony log entry by ID (log-delete) |
| `upsert_reader_reveal` | Gated | Create or update a planned or actual reader reveal |
| `delete_reader_reveal` | Gated | Delete a reader reveal entry by ID (FK-safe) |
| `get_reader_experience_notes` | Gated | Retrieve reader experience notes with optional filters |
| `log_reader_experience_note` | Gated | Append a reader experience note (append-only) |
| `delete_reader_experience_note` | Gated | Delete a reader experience note by ID (log-delete) |

---

## `get_reader_state`

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

## `get_dramatic_irony_inventory`

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

## `get_reader_reveals`

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

## `upsert_reader_state`

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

## `log_dramatic_irony`

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

## `delete_reader_state`

**Purpose:** Delete a reader information state entry by ID. Gate-gated — FK-safe pattern.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `reader_state_id` | `int` | Yes | Primary key of the reader state entry to delete |

**Returns:** `GateViolation | NotFoundResponse | ValidationFailure | dict` — `{"deleted": True, "id": reader_state_id}` on success; `GateViolation` if gate not certified; `NotFoundResponse` if not found; `ValidationFailure` if FK constraints prevent deletion.

**Invocation reason:** Called to remove a reader information state entry that was logged in error — requires gate certification since knowledge management is a prose-phase operation.

**Gate status:** Gated — returns `GateViolation` if gate not certified.

**Tables touched:** Reads `reader_information_states`. Writes `reader_information_states`.

---

## `delete_dramatic_irony`

**Purpose:** Delete a dramatic irony entry by primary key. Gate-gated.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `dramatic_irony_id` | `int` | Yes | Primary key of the dramatic irony entry to delete |

**Returns:** `GateViolation | NotFoundResponse | dict` — `{"deleted": True, "id": dramatic_irony_id}` on success; `GateViolation` if gate not certified; `NotFoundResponse` if not found.

**Invocation reason:** Called to remove a dramatic irony entry that was logged in error — dramatic_irony_inventory is a log table with no FK children so deletion is always safe once gate-certified.

**Gate status:** Gated — returns `GateViolation` if gate not certified.

**Tables touched:** Reads `dramatic_irony_inventory`. Writes `dramatic_irony_inventory`.

---

## `upsert_reader_reveal`

**Purpose:** Create or update a reader reveal entry. Pre-checks chapter_id if provided.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `reveal_id` | `int \| None` | Yes | Existing reveal ID to update, or None to create |
| `reveal_type` | `str` | Yes | Category of reader reveal — e.g. "exposition", "twist", "confirmation" (required) |
| `chapter_id` | `int \| None` | No | FK to chapters where the reveal occurs (optional) |
| `scene_id` | `int \| None` | No | FK to scenes where the reveal occurs (optional) |
| `character_id` | `int \| None` | No | FK to characters involved in the reveal (optional) |
| `planned_reveal` | `str \| None` | No | Description of the planned reveal (optional) |
| `actual_reveal` | `str \| None` | No | Description of what was actually revealed (optional) |
| `reader_impact` | `str \| None` | No | Notes on the reader's expected experience (optional) |
| `notes` | `str \| None` | No | Free-form notes (optional) |

**Returns:** `GateViolation | ReaderReveal | NotFoundResponse | ValidationFailure` — The created or updated `ReaderReveal`; `GateViolation` if gate not certified; `NotFoundResponse` if chapter_id does not exist; `ValidationFailure` on DB error.

**Invocation reason:** Called to plan a deliberate information disclosure to the reader — tracks the gap between planned and actual reveals for consistency and reader experience analysis.

**Gate status:** Gated — returns `GateViolation` if gate not certified.

**Tables touched:** Reads `chapters`. Writes `reader_reveals`.

---

## `delete_reader_reveal`

**Purpose:** Delete a reader reveal entry by ID. Gate-gated — FK-safe pattern.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `reveal_id` | `int` | Yes | Primary key of the reader reveal entry to delete |

**Returns:** `GateViolation | NotFoundResponse | ValidationFailure | dict` — `{"deleted": True, "id": reveal_id}` on success; `GateViolation` if gate not certified; `NotFoundResponse` if not found; `ValidationFailure` if FK constraints prevent deletion.

**Invocation reason:** Called to remove a reader reveal that was logged in error or retconned from the story.

**Gate status:** Gated — returns `GateViolation` if gate not certified.

**Tables touched:** Reads `reader_reveals`. Writes `reader_reveals`.

---

## `get_reader_experience_notes`

**Purpose:** Retrieve all reader experience notes for a given chapter.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `chapter_id` | `int` | Yes | The chapter whose reader experience notes to retrieve |

**Returns:** `list[ReaderExperienceNote] | GateViolation` — List of `ReaderExperienceNote` records ordered by `id` (may be empty); `GateViolation` if gate not certified.

**Invocation reason:** Called to review the reader experience notes logged for a chapter — used for pacing and reader impact analysis during revision.

**Gate status:** Gated — returns `GateViolation` if gate not certified.

**Tables touched:** Reads `reader_experience_notes`.

---

## `log_reader_experience_note`

**Purpose:** Log a new reader experience note (append-only). Pre-checks chapter_id and scene_id if provided.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `note_type` | `str` | Yes | Category of note — e.g. "pacing", "tension", "confusion", "satisfaction" (required) |
| `content` | `str` | Yes | The note content describing the reader experience (required) |
| `chapter_id` | `int \| None` | No | FK to chapters (optional; validated if provided) |
| `scene_id` | `int \| None` | No | FK to scenes (optional; validated if provided) |

**Returns:** `ReaderExperienceNote | GateViolation | NotFoundResponse | ValidationFailure` — The newly created `ReaderExperienceNote`; `GateViolation` if gate not certified; `NotFoundResponse` if chapter_id or scene_id does not exist; `ValidationFailure` on DB error.

**Invocation reason:** Called during or after drafting to record observations about the expected reader experience — accumulates feedback used for revision planning.

**Gate status:** Gated — returns `GateViolation` if gate not certified.

**Tables touched:** Reads `chapters`, `scenes`. Writes `reader_experience_notes`.

---

## `delete_reader_experience_note`

**Purpose:** Delete a reader experience note by primary key. Gate-gated.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `note_id` | `int` | Yes | Primary key of the reader experience note to delete |

**Returns:** `GateViolation | NotFoundResponse | dict` — `{"deleted": True, "id": note_id}` on success; `GateViolation` if gate not certified; `NotFoundResponse` if not found.

**Invocation reason:** Called to remove a reader experience note that was logged in error — reader_experience_notes is a log table with no FK children so deletion is always safe once gate-certified.

**Gate status:** Gated — returns `GateViolation` if gate not certified.

**Tables touched:** Reads `reader_experience_notes`. Writes `reader_experience_notes`.

---
