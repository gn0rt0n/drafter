[← Documentation Index](../README.md)

# Chapters Tools

Manages book chapters, chapter writing plans (a focused subset of chapter fields), and structural obligations. The structural obligations capture what each chapter must accomplish narratively.

**Gate status:** All tools in this domain are gate-free.

**8 tools**

## Index

| Tool Name | Gate | Description |
|-----------|------|-------------|
| `get_chapter` | Free | Look up a single chapter by ID |
| `get_chapter_plan` | Free | Return the writing-guidance subset of a chapter |
| `get_chapter_obligations` | Free | Return structural obligations for a chapter |
| `list_chapters` | Free | Return all chapters in a book |
| `upsert_chapter` | Free | Create or update a chapter |
| `delete_chapter` | Free | Delete a chapter by ID (FK-safe) |
| `upsert_chapter_obligation` | Free | Create or update a structural obligation for a chapter |
| `delete_chapter_obligation` | Free | Delete a chapter structural obligation by ID (log-delete) |

---

## `get_chapter`

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

## `get_chapter_plan`

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

## `get_chapter_obligations`

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

## `list_chapters`

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

## `upsert_chapter`

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

## `delete_chapter`

**Purpose:** Delete a chapter record by ID if no FK children reference it.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `chapter_id` | `int` | Yes | Primary key of the chapter to delete |

**Returns:** `NotFoundResponse | ValidationFailure | dict` — `{"deleted": True, "id": chapter_id}` on success; `NotFoundResponse` if not found; `ValidationFailure` if FK constraints prevent deletion.

**Invocation reason:** Called to remove a chapter that was created in error — only safe when no scenes, arcs, or other chapter-scoped records exist for it.

**Gate status:** Gate-free.

**Tables touched:** Reads `chapters`. Writes `chapters`.

---

## `upsert_chapter_obligation`

**Purpose:** Create or update a structural obligation for a chapter.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `chapter_id` | `int` | Yes | FK to the chapter this obligation belongs to |
| `obligation_type` | `str` | Yes | Type of obligation — e.g. "introduce", "resolve", "escalate" |
| `description` | `str` | Yes | Description of the narrative obligation |
| `obligation_id` | `int \| None` | No | Existing obligation ID to update, or None to create |
| `is_fulfilled` | `bool` | No | Whether the obligation has been met (default: False) |
| `notes` | `str \| None` | No | Free-form notes (optional) |

**Returns:** `ChapterObligation | NotFoundResponse | ValidationFailure` — The created or updated `ChapterObligation`; `NotFoundResponse` if chapter_id does not exist; `ValidationFailure` on DB error.

**Invocation reason:** Called during planning to record what narrative tasks a chapter must accomplish — used for consistency checking and completeness verification before marking a chapter as finished.

**Gate status:** Gate-free.

**Tables touched:** Reads `chapters`. Writes `chapter_obligations`.

---

## `delete_chapter_obligation`

**Purpose:** Delete a chapter obligation record by primary key.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `obligation_id` | `int` | Yes | Primary key of the obligation record to delete |

**Returns:** `NotFoundResponse | dict` — `{"deleted": True, "id": obligation_id}` on success; `NotFoundResponse` if the record does not exist.

**Invocation reason:** Called to remove an obligation that is no longer relevant — chapter_obligations is a leaf table with no FK children so deletion is always safe.

**Gate status:** Gate-free.

**Tables touched:** Reads `chapter_obligations`. Writes `chapter_obligations`.

---
