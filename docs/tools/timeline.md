[← Documentation Index](../README.md)

# Timeline Tools

Manages story timeline events, POV character chronological positions, and travel segment tracking. Includes travel realism validation.

**Gate status:** Mixed — see individual tool entries. The 8 pre-Phase-14 timeline CRUD tools are gated; `log_travel_segment`, `delete_event`, `delete_pov_position`, `delete_travel_segment`, and all 6 event junction tools are gate-free.

**18 tools**

## Index

| Tool Name | Gate | Description |
|-----------|------|-------------|
| `get_pov_positions` | Gated | Retrieve all POV character chronological positions at a chapter |
| `get_pov_position` | Gated | Retrieve a specific POV character's chronological position at a chapter |
| `get_event` | Gated | Retrieve a single timeline event by primary key |
| `list_events` | Gated | List timeline events with optional chapter or chapter-range filters |
| `get_travel_segments` | Gated | Retrieve all travel segments for a character ordered chronologically |
| `validate_travel_realism` | Gated | Validate whether travel between locations is realistic given elapsed in-story time |
| `upsert_event` | Gated | Create or update a timeline event |
| `upsert_pov_position` | Gated | Create or update a POV character chronological position at a chapter |
| `log_travel_segment` | Free | Append a travel segment record for a character |
| `delete_event` | Free | Delete a timeline event by ID (FK-safe) |
| `delete_pov_position` | Free | Delete a POV chronological position row by its integer primary key |
| `delete_travel_segment` | Free | Delete a travel segment by primary key |
| `add_event_participant` | Free | Associate a character with a timeline event |
| `remove_event_participant` | Free | Remove a character from a timeline event |
| `get_event_participants` | Free | Return all characters associated with a timeline event |
| `add_event_artifact` | Free | Associate an artifact with a timeline event |
| `remove_event_artifact` | Free | Remove an artifact from a timeline event |
| `get_event_artifacts` | Free | Return all artifacts associated with a timeline event |

---

## `get_pov_positions`

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

## `get_pov_position`

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

## `get_event`

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

## `list_events`

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

## `get_travel_segments`

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

## `validate_travel_realism`

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

## `upsert_event`

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

## `upsert_pov_position`

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

## `log_travel_segment`

**Purpose:** Append a travel segment record for a character. Pre-checks character_id and optionally start_chapter_id. NOT gate-gated.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `character_id` | `int` | Yes | FK to characters — the travelling character (required) |
| `from_location_id` | `int \| None` | No | FK to locations — starting location (optional) |
| `to_location_id` | `int \| None` | No | FK to locations — destination location (optional) |
| `start_chapter_id` | `int \| None` | No | FK to chapters — chapter where travel begins (optional) |
| `end_chapter_id` | `int \| None` | No | FK to chapters — chapter where travel ends (optional) |
| `start_event_id` | `int \| None` | No | FK to events — event triggering this travel (optional) |
| `elapsed_days` | `int \| None` | No | Number of in-story days the journey takes (optional) |
| `travel_method` | `str \| None` | No | Mode of travel — e.g. "walking", "horse", "ship" (optional) |
| `notes` | `str \| None` | No | Free-form notes (optional) |

**Returns:** `TravelSegment | NotFoundResponse | ValidationFailure` — The newly created `TravelSegment`; `NotFoundResponse` if character_id or start_chapter_id does not exist; `ValidationFailure` on DB error.

**Invocation reason:** Called to record a character's journey between locations — feeds the travel realism validation and POV position tracking.

**Gate status:** Gate-free.

**Tables touched:** Reads `characters`, `chapters`. Writes `travel_segments`.

---

## `delete_event`

**Purpose:** Delete a timeline event by ID if no FK children reference it. NOT gate-gated.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `event_id` | `int` | Yes | Primary key of the timeline event to delete |

**Returns:** `NotFoundResponse | ValidationFailure | dict` — `{"deleted": True, "id": event_id}` on success; `NotFoundResponse` if not found; `ValidationFailure` if FK constraints prevent deletion (event_participants or event_artifacts reference the event).

**Invocation reason:** Called to remove a timeline event that was created in error — only safe when no participants or artifacts are linked to it.

**Gate status:** Gate-free.

**Tables touched:** Reads `events`. Writes `events`.

---

## `delete_pov_position`

**Purpose:** Delete a POV chronological position row by its integer primary key. FK-safe. NOT gate-gated.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `pov_position_id` | `int` | Yes | Primary key (id) of the pov_chronological_position row to delete |

**Returns:** `NotFoundResponse | ValidationFailure | dict` — `{"deleted": True, "id": pov_position_id}` on success; `NotFoundResponse` if not found; `ValidationFailure` if FK constraints prevent deletion.

**Invocation reason:** Called to remove a POV position record that was created in error — uses the integer primary key for unambiguous deletion.

**Gate status:** Gate-free.

**Tables touched:** Reads `pov_chronological_position`. Writes `pov_chronological_position`.

---

## `delete_travel_segment`

**Purpose:** Delete a travel segment by primary key. NOT gate-gated.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `travel_segment_id` | `int` | Yes | Primary key of the travel segment to delete |

**Returns:** `NotFoundResponse | dict` — `{"deleted": True, "id": travel_segment_id}` on success; `NotFoundResponse` if not found.

**Invocation reason:** Called to remove an incorrectly logged travel segment — travel_segments is a log table with no FK children so deletion is always safe.

**Gate status:** Gate-free.

**Tables touched:** Reads `travel_segments`. Writes `travel_segments`.

---

## `add_event_participant`

**Purpose:** Associate a character with a timeline event. Idempotent: updates role and notes if the association already exists. NOT gate-gated.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `event_id` | `int` | Yes | FK to events — the event to associate the character with (required) |
| `character_id` | `int` | Yes | FK to characters — the character to associate (required) |
| `role` | `str \| None` | No | Role the character plays in the event (optional; defaults to "participant" per DB schema) |
| `notes` | `str \| None` | No | Freeform notes about the character's involvement (optional) |

**Returns:** `EventParticipant | NotFoundResponse | ValidationFailure` — The created or updated `EventParticipant`; `NotFoundResponse` if event_id or character_id does not exist; `ValidationFailure` on DB error.

**Invocation reason:** Called after logging a timeline event to record which characters were present — used to build event participant lists for narrative reference.

**Gate status:** Gate-free.

**Tables touched:** Reads `events`, `characters`. Writes `event_participants`.

---

## `remove_event_participant`

**Purpose:** Remove a character from a timeline event. Idempotent: returns NotFoundResponse if the association does not exist. NOT gate-gated.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `event_id` | `int` | Yes | FK to events (required) |
| `character_id` | `int` | Yes | FK to characters (required) |

**Returns:** `NotFoundResponse | dict` — `{"removed": True, "event_id": event_id, "character_id": character_id}` on success; `NotFoundResponse` if the association does not exist.

**Invocation reason:** Called to remove a character from an event that was added in error or retconned out of a scene.

**Gate status:** Gate-free.

**Tables touched:** Reads `event_participants`. Writes `event_participants`.

---

## `get_event_participants`

**Purpose:** Return all characters associated with a timeline event. Verifies the event exists first.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `event_id` | `int` | Yes | Primary key of the event to look up participants for |

**Returns:** `list[EventParticipant] | NotFoundResponse` — List of `EventParticipant` records (may be empty); `NotFoundResponse` if the event does not exist.

**Invocation reason:** Called before drafting a scene to confirm which characters are participating in a specific timeline event — ensures all participants are accounted for in the scene.

**Gate status:** Gate-free.

**Tables touched:** Reads `events`, `event_participants`.

---

## `add_event_artifact`

**Purpose:** Associate an artifact with a timeline event. Idempotent: updates involvement if the association already exists. NOT gate-gated.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `event_id` | `int` | Yes | FK to events — the event to associate the artifact with (required) |
| `artifact_id` | `int` | Yes | FK to artifacts — the artifact to associate (required) |
| `involvement` | `str \| None` | No | Description of the artifact's role — e.g. "weapon", "target", "trophy" (optional) |

**Returns:** `EventArtifact | NotFoundResponse | ValidationFailure` — The created or updated `EventArtifact`; `NotFoundResponse` if event_id or artifact_id does not exist; `ValidationFailure` on DB error.

**Invocation reason:** Called to link a significant prop or artifact to the event where it plays a role — enables artifact tracking across the story timeline.

**Gate status:** Gate-free.

**Tables touched:** Reads `events`, `artifacts`. Writes `event_artifacts`.

---

## `remove_event_artifact`

**Purpose:** Remove an artifact from a timeline event. NOT gate-gated.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `event_id` | `int` | Yes | FK to events (required) |
| `artifact_id` | `int` | Yes | FK to artifacts (required) |

**Returns:** `NotFoundResponse | dict` — `{"removed": True, "event_id": event_id, "artifact_id": artifact_id}` on success; `NotFoundResponse` if the association does not exist.

**Invocation reason:** Called to remove an artifact link from an event that was added in error or retconned.

**Gate status:** Gate-free.

**Tables touched:** Reads `event_artifacts`. Writes `event_artifacts`.

---

## `get_event_artifacts`

**Purpose:** Return all artifacts associated with a timeline event. Verifies the event exists first.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `event_id` | `int` | Yes | Primary key of the event to look up artifacts for |

**Returns:** `list[EventArtifact] | NotFoundResponse` — List of `EventArtifact` records (may be empty); `NotFoundResponse` if the event does not exist.

**Invocation reason:** Called to audit which artifacts are involved in a specific event — useful for prop continuity checks and scene prop verification.

**Gate status:** Gate-free.

**Tables touched:** Reads `events`, `event_artifacts`.

---
