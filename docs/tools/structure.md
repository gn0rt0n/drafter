[← Documentation Index](../README.md)

# Structure Tools

Manages story-level 7-point structural beats (story_structure table with one row per book) and per-arc 7-point beats (arc_seven_point_beats table). Gate-free because these tools populate data that gate checks evaluate.

**Gate status:** All tools in this domain are gate-free (structure tools populate data that gate queries check — they must work before certification).

**6 tools**

## Index

| Tool Name | Gate | Description |
|-----------|------|-------------|
| `get_story_structure` | Free | Retrieve the story structure for a book |
| `upsert_story_structure` | Free | Create or update story structure 7-point beats |
| `get_arc_beats` | Free | Retrieve all 7-point beat records for a character arc |
| `upsert_arc_beat` | Free | Create or update a single 7-point arc beat |
| `delete_story_structure` | Free | Delete a story structure record by ID (FK-safe) |
| `delete_arc_beat` | Free | Delete a 7-point arc beat record by ID (log-delete) |

---

## `get_story_structure`

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

## `upsert_story_structure`

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

## `get_arc_beats`

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

## `upsert_arc_beat`

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

## `delete_story_structure`

**Purpose:** Delete a story structure row by ID if no FK children reference it.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `story_structure_id` | `int` | Yes | Primary key of the story structure row to delete |

**Returns:** `NotFoundResponse | ValidationFailure | dict` — `{"deleted": True, "id": story_structure_id}` on success; `NotFoundResponse` if not found; `ValidationFailure` if FK constraints prevent deletion.

**Invocation reason:** Called to remove a story structure record that was created in error or superseded by a revised structure for the same book.

**Gate status:** Gate-free.

**Tables touched:** Reads `story_structure`. Writes `story_structure`.

---

## `delete_arc_beat`

**Purpose:** Delete an arc seven-point beat record by primary key.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `arc_beat_id` | `int` | Yes | Primary key of the arc seven-point beat to delete |

**Returns:** `NotFoundResponse | dict` — `{"deleted": True, "id": arc_beat_id}` on success; `NotFoundResponse` if the record does not exist.

**Invocation reason:** Called to remove an arc beat that was created in error — arc_seven_point_beats is a leaf table with no FK children so deletion is always safe.

**Gate status:** Gate-free.

**Tables touched:** Reads `arc_seven_point_beats`. Writes `arc_seven_point_beats`.

---
