[← Documentation Index](../README.md)

# Arcs Tools

Manages character arcs, Chekhov's gun registry, subplot touchpoint tracking, and arc health logging. `get_arc` is dual-mode (by arc_id or character_id). `log_arc_health` and `upsert_chekov` use separate branching patterns.

**Gate status:** All tools in this domain are gate-free.

**15 tools**

## Index

| Tool Name | Gate | Description |
|-----------|------|-------------|
| `get_chekovs_guns` | Free | Retrieve Chekhov's gun entries from the registry |
| `get_arc` | Free | Retrieve character arc(s) by arc_id or character_id |
| `get_arc_health` | Free | Retrieve arc health log entries for a character |
| `get_subplot_touchpoint_gaps` | Free | Return active subplots overdue for a touchpoint |
| `upsert_chekov` | Free | Create or update a Chekhov's gun entry |
| `log_arc_health` | Free | Append an arc health log entry |
| `delete_arc` | Free | Delete a character arc by ID (FK-safe) |
| `delete_arc_health_log` | Free | Delete an arc health log entry by ID (log-delete) |
| `delete_chekov` | Free | Delete a Chekhov's gun entry by ID (FK-safe) |
| `upsert_arc` | Free | Create or update a character arc record |
| `log_subplot_touchpoint` | Free | Append a subplot touchpoint log entry |
| `delete_subplot_touchpoint` | Free | Delete a subplot touchpoint log entry by ID (log-delete) |
| `link_chapter_to_arc` | Free | Link a chapter to a character arc (upsert junction) |
| `unlink_chapter_from_arc` | Free | Remove the link between a chapter and a character arc |
| `get_arcs_for_chapter` | Free | Return all character arcs linked to a chapter |

---

## `get_chekovs_guns`

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

## `get_arc`

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

## `get_arc_health`

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

## `get_subplot_touchpoint_gaps`

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

## `upsert_chekov`

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

## `log_arc_health`

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

## `delete_arc`

**Purpose:** Delete a character arc by ID if no FK children reference it.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `arc_id` | `int` | Yes | Primary key of the character arc to delete |

**Returns:** `NotFoundResponse | ValidationFailure | dict` — `{"deleted": True, "id": arc_id}` on success; `NotFoundResponse` if not found; `ValidationFailure` if FK constraints prevent deletion (chapter_character_arcs, arc_health_log, or arc_seven_point_beats reference the arc).

**Invocation reason:** Called to remove a character arc that was created in error — only safe when no chapter links, health logs, or beat records reference it.

**Gate status:** Gate-free.

**Tables touched:** Reads `character_arcs`. Writes `character_arcs`.

---

## `delete_arc_health_log`

**Purpose:** Delete an arc health log entry by primary key.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `arc_health_log_id` | `int` | Yes | Primary key of the arc health log entry to delete |

**Returns:** `NotFoundResponse | dict` — `{"deleted": True, "id": arc_health_log_id}` on success; `NotFoundResponse` if the record does not exist.

**Invocation reason:** Called to remove an incorrectly logged arc health entry — arc_health_log is a log table with no FK children so deletion is always safe.

**Gate status:** Gate-free.

**Tables touched:** Reads `arc_health_log`. Writes `arc_health_log`.

---

## `delete_chekov`

**Purpose:** Delete a Chekhov's gun registry entry by ID.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `chekov_id` | `int` | Yes | Primary key of the Chekhov's gun entry to delete |

**Returns:** `NotFoundResponse | ValidationFailure | dict` — `{"deleted": True, "id": chekov_id}` on success; `NotFoundResponse` if not found; `ValidationFailure` if FK constraints prevent deletion.

**Invocation reason:** Called to remove a Chekhov's gun entry that was registered in error or written out of the story.

**Gate status:** Gate-free.

**Tables touched:** Reads `chekovs_gun_registry`. Writes `chekovs_gun_registry`.

---

## `upsert_arc`

**Purpose:** Create or update a character arc. Pre-checks that character_id exists.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `character_id` | `int` | Yes | FK to characters — the character this arc belongs to (required) |
| `arc_type` | `str` | No | Type of arc — e.g. "growth", "fall", "flat" (default: "growth") |
| `arc_id` | `int \| None` | No | Existing arc ID to update, or None to create |
| `starting_state` | `str \| None` | No | Narrative state the character starts in (optional) |
| `desired_state` | `str \| None` | No | Narrative state the character strives toward (optional) |
| `wound` | `str \| None` | No | Core wound driving the character's flaw (optional) |
| `lie_believed` | `str \| None` | No | Lie the character believes (optional) |
| `truth_to_learn` | `str \| None` | No | Truth the character must learn (optional) |
| `opened_chapter_id` | `int \| None` | No | Chapter where this arc begins (optional) |
| `closed_chapter_id` | `int \| None` | No | Chapter where this arc concludes (optional) |
| `notes` | `str \| None` | No | Free-form notes (optional) |
| `canon_status` | `str` | No | Canon status (default: "draft") |

**Returns:** `CharacterArc | NotFoundResponse | ValidationFailure` — The created or updated `CharacterArc`; `NotFoundResponse` if character_id does not exist; `ValidationFailure` on DB error.

**Invocation reason:** Called during character planning to define the arc structure — the wound, lie, and truth fields are used for consistent character voice and narrative coherence checking.

**Gate status:** Gate-free.

**Tables touched:** Reads `characters`. Writes `character_arcs`.

---

## `log_subplot_touchpoint`

**Purpose:** Append a subplot touchpoint entry to the log. Pre-checks that both plot_thread_id and chapter_id exist.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `plot_thread_id` | `int` | Yes | FK to plot_threads — the subplot receiving this touchpoint (required) |
| `chapter_id` | `int` | Yes | FK to chapters — the chapter where the touchpoint occurs (required) |
| `touchpoint_type` | `str` | No | Type of touchpoint — e.g. "advance", "callback", "resolve" (default: "advance") |
| `notes` | `str \| None` | No | Free-form notes about this touchpoint (optional) |

**Returns:** `SubplotTouchpoint | NotFoundResponse | ValidationFailure` — The newly created `SubplotTouchpoint`; `NotFoundResponse` if plot_thread_id or chapter_id does not exist; `ValidationFailure` on DB error.

**Invocation reason:** Called after drafting a chapter that touches a subplot — prevents subplot threads from going unacknowledged too long between appearances.

**Gate status:** Gate-free.

**Tables touched:** Reads `plot_threads`, `chapters`. Writes `subplot_touchpoint_log`.

---

## `delete_subplot_touchpoint`

**Purpose:** Delete a subplot touchpoint log entry by primary key.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `touchpoint_id` | `int` | Yes | Primary key of the subplot touchpoint entry to delete |

**Returns:** `NotFoundResponse | dict` — `{"deleted": True, "id": touchpoint_id}` on success; `NotFoundResponse` if the record does not exist.

**Invocation reason:** Called to remove an incorrectly logged subplot touchpoint — subplot_touchpoint_log is a log table with no FK children so deletion is always safe.

**Gate status:** Gate-free.

**Tables touched:** Reads `subplot_touchpoint_log`. Writes `subplot_touchpoint_log`.

---

## `link_chapter_to_arc`

**Purpose:** Link a chapter to a character arc via the chapter_character_arcs junction table. Idempotent: updates arc_progression and notes if the link already exists.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `chapter_id` | `int` | Yes | FK to chapters table (required) |
| `arc_id` | `int` | Yes | FK to character_arcs table (required) |
| `arc_progression` | `str` | No | Progression state in this chapter — e.g. "advance", "climax", "setup", "stasis" (default: "advance") |
| `notes` | `str \| None` | No | Free-form notes about this chapter-arc association (optional) |

**Returns:** `ChapterCharacterArc | NotFoundResponse | ValidationFailure` — The created or updated `ChapterCharacterArc`; `NotFoundResponse` if chapter_id or arc_id does not exist; `ValidationFailure` on DB error.

**Invocation reason:** Called during chapter planning to associate a chapter with the character arcs it advances — enables tracking of arc progression across the full manuscript.

**Gate status:** Gate-free.

**Tables touched:** Reads `chapters`, `character_arcs`. Writes `chapter_character_arcs`.

---

## `unlink_chapter_from_arc`

**Purpose:** Remove the link between a chapter and a character arc. Idempotent: returns NotFoundResponse if the link does not exist.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `chapter_id` | `int` | Yes | FK to chapters table (required) |
| `arc_id` | `int` | Yes | FK to character_arcs table (required) |

**Returns:** `NotFoundResponse | dict` — `{"unlinked": True, "chapter_id": chapter_id, "arc_id": arc_id}` on success; `NotFoundResponse` if the link does not exist.

**Invocation reason:** Called when a chapter's role in a character arc is removed during restructuring — cleans up the junction table after story changes.

**Gate status:** Gate-free.

**Tables touched:** Reads `chapter_character_arcs`. Writes `chapter_character_arcs`.

---

## `get_arcs_for_chapter`

**Purpose:** Get all character arc associations for a chapter.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `chapter_id` | `int` | Yes | Primary key of the chapter to query |

**Returns:** `list[ChapterCharacterArc]` — All `ChapterCharacterArc` records for the chapter ordered by `arc_id`. Returns an empty list if no associations exist.

**Invocation reason:** Called before drafting a chapter to confirm which character arcs it is responsible for advancing — ensures the agent has the full arc context before writing.

**Gate status:** Gate-free.

**Tables touched:** Reads `chapter_character_arcs`.

---
