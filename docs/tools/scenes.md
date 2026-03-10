[← Documentation Index](../README.md)

# Scenes Tools

Manages individual scenes within chapters, including per-character scene goals. Scenes are the atomic narrative unit: each has a dramatic question, goal, obstacle, turn, and consequence.

**Gate status:** All tools in this domain are gate-free.

**12 tools**

## Index

| Tool Name | Gate | Description |
|-----------|------|-------------|
| `get_scene` | Free | Look up a single scene by ID |
| `get_scene_character_goals` | Free | Return all per-character goals for a scene |
| `upsert_scene` | Free | Create or update a scene |
| `upsert_scene_goal` | Free | Create or update a per-character scene goal |
| `delete_scene` | Free | Delete a scene by ID (FK-safe) |
| `delete_scene_goal` | Free | Delete a per-character scene goal by ID (log-delete) |
| `get_pacing_beats` | Free | Retrieve all pacing beats for a chapter |
| `log_pacing_beat` | Free | Append a pacing beat record for a chapter |
| `delete_pacing_beat` | Free | Delete a pacing beat record by ID (log-delete) |
| `get_tension_measurements` | Free | Retrieve all tension measurements for a chapter |
| `log_tension_measurement` | Free | Append a tension measurement record for a chapter |
| `delete_tension_measurement` | Free | Delete a tension measurement record by ID (log-delete) |

---

## `get_scene`

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

## `get_scene_character_goals`

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

## `upsert_scene`

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

## `upsert_scene_goal`

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

## `delete_scene`

**Purpose:** Delete a scene record by ID if no FK children reference it.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `scene_id` | `int` | Yes | Primary key of the scene to delete |

**Returns:** `NotFoundResponse | ValidationFailure | dict` — `{"deleted": True, "id": scene_id}` on success; `NotFoundResponse` if not found; `ValidationFailure` if FK constraints prevent deletion.

**Invocation reason:** Called to remove a scene that was created in error — only safe when no scene goals or other scene-scoped records exist for it.

**Gate status:** Gate-free.

**Tables touched:** Reads `scenes`. Writes `scenes`.

---

## `delete_scene_goal`

**Purpose:** Delete a scene character goal record by primary key.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `goal_id` | `int` | Yes | Primary key of the scene goal record to delete |

**Returns:** `NotFoundResponse | dict` — `{"deleted": True, "id": goal_id}` on success; `NotFoundResponse` if the record does not exist.

**Invocation reason:** Called to remove an incorrectly created scene goal entry — scene_character_goals is a leaf table with no FK children so deletion is always safe.

**Gate status:** Gate-free.

**Tables touched:** Reads `scene_character_goals`. Writes `scene_character_goals`.

---

## `get_pacing_beats`

**Purpose:** Return all pacing beat records for a scene or chapter.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `chapter_id` | `int \| None` | No | Filter to beats for this chapter |
| `scene_id` | `int \| None` | No | Filter to beats for this scene |

**Returns:** `list[PacingBeat]` — List of `PacingBeat` records ordered by `sequence_order`. Returns an empty list if no beats exist.

**Invocation reason:** Called to review the structural rhythm of a chapter before drafting — confirms that tension rises and falls as intended across the sequence of beats.

**Gate status:** Gate-free.

**Tables touched:** Reads `pacing_beats`.

---

## `log_pacing_beat`

**Purpose:** Append a new pacing beat record for a chapter.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `chapter_id` | `int` | Yes | FK to the chapter this beat belongs to |
| `description` | `str` | Yes | Description of the pacing beat |
| `sequence_order` | `int` | Yes | Position of this beat in the chapter's sequence |
| `scene_id` | `int \| None` | No | FK to associated scene (optional) |
| `notes` | `str \| None` | No | Free-form notes (optional) |

**Returns:** `PacingBeat | NotFoundResponse | ValidationFailure` — The newly created `PacingBeat`; `NotFoundResponse` if chapter_id does not exist; `ValidationFailure` on DB error.

**Invocation reason:** Called during scene planning to record each narrative beat's pacing role — enables the agent to verify rhythm and tension structure before committing to a draft.

**Gate status:** Gate-free.

**Tables touched:** Reads `chapters`. Writes `pacing_beats`.

---

## `delete_pacing_beat`

**Purpose:** Delete a pacing beat record by primary key.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `beat_id` | `int` | Yes | Primary key of the pacing beat to delete |

**Returns:** `NotFoundResponse | dict` — `{"deleted": True, "id": beat_id}` on success; `NotFoundResponse` if the record does not exist.

**Invocation reason:** Called to remove an incorrectly logged pacing beat — pacing_beats is a leaf table with no FK children so deletion is always safe.

**Gate status:** Gate-free.

**Tables touched:** Reads `pacing_beats`. Writes `pacing_beats`.

---

## `get_tension_measurements`

**Purpose:** Return all tension measurement records for a chapter.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `chapter_id` | `int` | Yes | Chapter whose tension measurements to retrieve |

**Returns:** `list[TensionMeasurement]` — List of `TensionMeasurement` records ordered by `id`. Returns an empty list if no measurements exist.

**Invocation reason:** Called to audit the tension arc of a chapter — confirms that tension measurements align with the expected narrative trajectory before finalizing the chapter.

**Gate status:** Gate-free.

**Tables touched:** Reads `tension_measurements`.

---

## `log_tension_measurement`

**Purpose:** Append a new tension measurement record for a chapter.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `chapter_id` | `int` | Yes | FK to the chapter this measurement belongs to |
| `measurement_type` | `str` | Yes | Type of tension being measured — e.g. "conflict", "suspense", "emotional" |
| `level` | `int` | Yes | Tension level on a 1-10 scale |
| `notes` | `str \| None` | No | Free-form notes (optional) |

**Returns:** `TensionMeasurement | NotFoundResponse | ValidationFailure` — The newly created `TensionMeasurement`; `NotFoundResponse` if chapter_id does not exist; `ValidationFailure` on DB error.

**Invocation reason:** Called after drafting a chapter to record the tension profile — provides data for pacing analysis across the full manuscript.

**Gate status:** Gate-free.

**Tables touched:** Reads `chapters`. Writes `tension_measurements`.

---

## `delete_tension_measurement`

**Purpose:** Delete a tension measurement record by primary key.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `measurement_id` | `int` | Yes | Primary key of the tension measurement to delete |

**Returns:** `NotFoundResponse | dict` — `{"deleted": True, "id": measurement_id}` on success; `NotFoundResponse` if the record does not exist.

**Invocation reason:** Called to remove an incorrectly logged tension measurement — tension_measurements is a leaf table with no FK children so deletion is always safe.

**Gate status:** Gate-free.

**Tables touched:** Reads `tension_measurements`. Writes `tension_measurements`.

---
