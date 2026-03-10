[← Documentation Index](../README.md)

# Foreshadowing Tools

Manages foreshadowing plants and payoffs, prophecies, motifs, thematic mirrors, and opposition pairs. `log_foreshadowing` is an upsert (allows payoff to be filled later); `log_motif_occurrence` is append-only.

**Gate status:** All tools in this domain require gate certification (returns `GateViolation` if not certified).

**18 tools**

## Index

| Tool Name | Gate | Description |
|-----------|------|-------------|
| `get_foreshadowing` | Gated | Retrieve foreshadowing entries with optional filters |
| `get_prophecies` | Gated | Retrieve all prophecy registry entries |
| `get_motifs` | Gated | Retrieve all motif registry entries |
| `get_motif_occurrences` | Gated | Retrieve motif occurrences with optional filters |
| `get_thematic_mirrors` | Gated | Retrieve all thematic mirror pairs |
| `get_opposition_pairs` | Gated | Retrieve all opposition pairs |
| `log_foreshadowing` | Gated | Log or update a foreshadowing entry (upsert) |
| `log_motif_occurrence` | Gated | Log a new motif occurrence (append-only) |
| `delete_foreshadowing` | Gated | Delete a foreshadowing entry by ID (log-delete) |
| `delete_motif_occurrence` | Gated | Delete a motif occurrence log entry by ID (log-delete) |
| `upsert_motif` | Gated | Create or update a motif registry entry |
| `delete_motif` | Gated | Delete a motif registry entry by ID (FK-safe) |
| `upsert_prophecy` | Gated | Create or update a prophecy registry entry |
| `delete_prophecy` | Gated | Delete a prophecy registry entry by ID (FK-safe) |
| `upsert_thematic_mirror` | Gated | Create or update a thematic mirror pair entry |
| `delete_thematic_mirror` | Gated | Delete a thematic mirror pair by ID (FK-safe) |
| `upsert_opposition_pair` | Gated | Create or update an opposition pair entry |
| `delete_opposition_pair` | Gated | Delete an opposition pair by ID (FK-safe) |

---

## `get_foreshadowing`

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

## `get_prophecies`

**Purpose:** Retrieve all prophecy registry entries ordered by `created_at`.

**Parameters:** None

**Returns:** `list[ProphecyEntry] | GateViolation` — All `ProphecyEntry` records; `GateViolation` if gate not certified.

**Invocation reason:** Called when planning chapters that fulfill or allude to prophecies — verifies the prophecy text and current fulfillment status.

**Gate status:** Requires gate certification.

**Tables touched:** Reads `prophecy_registry`.

---

## `get_motifs`

**Purpose:** Retrieve all motif registry entries ordered by `created_at`.

**Parameters:** None

**Returns:** `list[MotifEntry] | GateViolation` — All `MotifEntry` records; `GateViolation` if gate not certified.

**Invocation reason:** Called when reviewing thematic elements before drafting — ensures recurring motifs are consciously woven through scenes at appropriate frequencies.

**Gate status:** Requires gate certification.

**Tables touched:** Reads `motif_registry`.

---

## `get_motif_occurrences`

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

## `get_thematic_mirrors`

**Purpose:** Retrieve all thematic mirror pairs ordered by `created_at`.

**Parameters:** None

**Returns:** `list[ThematicMirror] | GateViolation` — All `ThematicMirror` records; `GateViolation` if gate not certified.

**Invocation reason:** Called when planning scenes that feature mirrored characters or situations — ensures the structural parallels are recognized and intentionally reinforced in the draft.

**Gate status:** Requires gate certification.

**Tables touched:** Reads `thematic_mirrors`.

---

## `get_opposition_pairs`

**Purpose:** Retrieve all opposition pairs ordered by `created_at`.

**Parameters:** None

**Returns:** `list[OppositionPair] | GateViolation` — All `OppositionPair` records; `GateViolation` if gate not certified.

**Invocation reason:** Called when drafting scenes featuring opposing forces — verifies the documented opposition dynamics to ensure scenes authentically capture the established conflict structure.

**Gate status:** Requires gate certification.

**Tables touched:** Reads `opposition_pairs`.

---

## `log_foreshadowing`

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

## `log_motif_occurrence`

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

## `delete_foreshadowing`

**Purpose:** Delete a foreshadowing entry by ID. Gate-gated. foreshadowing_registry is a log table with no FK children.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `foreshadowing_id` | `int` | Yes | Primary key of the foreshadowing entry to delete |

**Returns:** `GateViolation | NotFoundResponse | dict` — `{"deleted": True, "id": foreshadowing_id}` on success; `GateViolation` if gate not certified; `NotFoundResponse` if not found.

**Invocation reason:** Called to remove a foreshadowing entry that was logged in error or retconned from the story.

**Gate status:** Gated — returns `GateViolation` if gate not certified.

**Tables touched:** Reads `foreshadowing_registry`. Writes `foreshadowing_registry`.

---

## `delete_motif_occurrence`

**Purpose:** Delete a motif occurrence entry by primary key. Gate-gated.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `motif_occurrence_id` | `int` | Yes | Primary key of the motif occurrence to delete |

**Returns:** `GateViolation | NotFoundResponse | dict` — `{"deleted": True, "id": motif_occurrence_id}` on success; `GateViolation` if gate not certified; `NotFoundResponse` if not found.

**Invocation reason:** Called to remove a motif occurrence that was logged in error — motif_occurrences is a log table with no FK children so deletion is always safe once gate-certified.

**Gate status:** Gated — returns `GateViolation` if gate not certified.

**Tables touched:** Reads `motif_occurrences`. Writes `motif_occurrences`.

---

## `upsert_motif`

**Purpose:** Create or update a motif in the motif_registry table.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `name` | `str` | Yes | Unique name for the motif (required) |
| `description` | `str` | Yes | Description of the motif (required) |
| `motif_id` | `int \| None` | No | Existing motif ID to update, or None to create |
| `motif_type` | `str` | No | Type of motif (default: "symbol") |
| `thematic_role` | `str \| None` | No | Thematic role the motif plays (optional) |
| `first_appearance_chapter_id` | `int \| None` | No | FK to chapter of first appearance (optional) |
| `notes` | `str \| None` | No | Additional notes (optional) |

**Returns:** `GateViolation | MotifEntry | ValidationFailure` — The created or updated `MotifEntry`; `GateViolation` if gate not certified; `ValidationFailure` on DB error.

**Invocation reason:** Called to define a recurring motif in the story — provides the structured record that motif occurrences reference via FK for frequency and pattern analysis.

**Gate status:** Gated — returns `GateViolation` if gate not certified.

**Tables touched:** Reads `motif_registry`. Writes `motif_registry`.

---

## `delete_motif`

**Purpose:** Delete a motif from motif_registry by ID. Gate-gated — FK-safe (motif_occurrences reference motif_id).

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `motif_id` | `int` | Yes | Primary key of the motif to delete |

**Returns:** `GateViolation | NotFoundResponse | ValidationFailure | dict` — `{"deleted": True, "id": motif_id}` on success; `GateViolation` if gate not certified; `NotFoundResponse` if not found; `ValidationFailure` if FK children (motif_occurrences) prevent deletion.

**Invocation reason:** Called to remove a motif that was created in error — only safe when no motif occurrences reference it.

**Gate status:** Gated — returns `GateViolation` if gate not certified.

**Tables touched:** Reads `motif_registry`. Writes `motif_registry`.

---

## `upsert_prophecy`

**Purpose:** Create or update a prophecy in the prophecy_registry table.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `name` | `str` | Yes | Name of the prophecy (required) |
| `text` | `str` | Yes | Full text of the prophecy (required) |
| `prophecy_id` | `int \| None` | No | Existing prophecy ID to update, or None to create |
| `subject_character_id` | `int \| None` | No | FK to characters — character the prophecy is about (optional) |
| `source_character_id` | `int \| None` | No | FK to characters — character who uttered it (optional) |
| `uttered_chapter_id` | `int \| None` | No | FK to chapters — chapter where uttered (optional) |
| `fulfilled_chapter_id` | `int \| None` | No | FK to chapters — chapter where fulfilled (optional) |
| `status` | `str` | No | Current status (default: "active") |
| `interpretation` | `str \| None` | No | Interpretation notes (optional) |
| `notes` | `str \| None` | No | Additional notes (optional) |
| `canon_status` | `str` | No | Canon status (default: "draft") |

**Returns:** `GateViolation | ProphecyEntry | ValidationFailure` — The created or updated `ProphecyEntry`; `GateViolation` if gate not certified; `ValidationFailure` on DB error.

**Invocation reason:** Called to define a prophecy or prediction within the story — provides the structured record for tracking prophecy fulfillment across the narrative.

**Gate status:** Gated — returns `GateViolation` if gate not certified.

**Tables touched:** Reads `prophecy_registry`. Writes `prophecy_registry`.

---

## `delete_prophecy`

**Purpose:** Delete a prophecy from prophecy_registry by ID. Gate-gated — FK-safe pattern.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `prophecy_id` | `int` | Yes | Primary key of the prophecy to delete |

**Returns:** `GateViolation | NotFoundResponse | ValidationFailure | dict` — `{"deleted": True, "id": prophecy_id}` on success; `GateViolation` if gate not certified; `NotFoundResponse` if not found; `ValidationFailure` if FK constraints prevent deletion.

**Invocation reason:** Called to remove a prophecy that was created in error or written out of the story.

**Gate status:** Gated — returns `GateViolation` if gate not certified.

**Tables touched:** Reads `prophecy_registry`. Writes `prophecy_registry`.

---

## `upsert_thematic_mirror`

**Purpose:** Create or update a thematic mirror in the thematic_mirrors table.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `name` | `str` | Yes | Name of the thematic mirror (required) |
| `element_a_id` | `int` | Yes | ID of the first element being mirrored (required) |
| `element_b_id` | `int` | Yes | ID of the second element being mirrored (required) |
| `mirror_id` | `int \| None` | No | Existing mirror ID to update, or None to create |
| `mirror_type` | `str` | No | Type of mirror relationship (default: "character") |
| `element_a_type` | `str` | No | Type of first element (default: "character") |
| `element_b_type` | `str` | No | Type of second element (default: "character") |
| `mirror_description` | `str \| None` | No | Description of the mirror relationship (optional) |
| `thematic_purpose` | `str \| None` | No | Thematic purpose of the mirror (optional) |
| `notes` | `str \| None` | No | Additional notes (optional) |

**Returns:** `GateViolation | ThematicMirror | ValidationFailure` — The created or updated `ThematicMirror`; `GateViolation` if gate not certified; `ValidationFailure` on DB error.

**Invocation reason:** Called to document a deliberate structural parallel between two story elements — used for thematic coherence analysis and pattern tracking.

**Gate status:** Gated — returns `GateViolation` if gate not certified.

**Tables touched:** Reads `thematic_mirrors`. Writes `thematic_mirrors`.

---

## `delete_thematic_mirror`

**Purpose:** Delete a thematic mirror from thematic_mirrors by ID. Gate-gated — thematic_mirrors has no FK children.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `mirror_id` | `int` | Yes | Primary key of the thematic mirror to delete |

**Returns:** `GateViolation | NotFoundResponse | ValidationFailure | dict` — `{"deleted": True, "id": mirror_id}` on success; `GateViolation` if gate not certified; `NotFoundResponse` if not found; `ValidationFailure` on DB error.

**Invocation reason:** Called to remove a thematic mirror that was defined in error or restructured out of the story.

**Gate status:** Gated — returns `GateViolation` if gate not certified.

**Tables touched:** Reads `thematic_mirrors`. Writes `thematic_mirrors`.

---

## `upsert_opposition_pair`

**Purpose:** Create or update an opposition pair in the opposition_pairs table.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `name` | `str` | Yes | Name of the opposition pair (required) |
| `concept_a` | `str` | Yes | First concept in the opposition (required) |
| `concept_b` | `str` | Yes | Second concept in the opposition (required) |
| `pair_id` | `int \| None` | No | Existing pair ID to update, or None to create |
| `manifested_in` | `str \| None` | No | How the opposition manifests in the narrative (optional) |
| `resolved_chapter_id` | `int \| None` | No | FK to chapters where the opposition resolves (optional) |
| `notes` | `str \| None` | No | Additional notes (optional) |

**Returns:** `GateViolation | OppositionPair | ValidationFailure` — The created or updated `OppositionPair`; `GateViolation` if gate not certified; `ValidationFailure` on DB error.

**Invocation reason:** Called to document a thematic tension between opposing concepts — tracks whether and how the opposition resolves across the narrative arc.

**Gate status:** Gated — returns `GateViolation` if gate not certified.

**Tables touched:** Reads `opposition_pairs`. Writes `opposition_pairs`.

---

## `delete_opposition_pair`

**Purpose:** Delete an opposition pair from opposition_pairs by ID. Gate-gated — opposition_pairs has no FK children.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `pair_id` | `int` | Yes | Primary key of the opposition pair to delete |

**Returns:** `GateViolation | NotFoundResponse | ValidationFailure | dict` — `{"deleted": True, "id": pair_id}` on success; `GateViolation` if gate not certified; `NotFoundResponse` if not found; `ValidationFailure` on DB error.

**Invocation reason:** Called to remove an opposition pair that was defined in error or resolved into a different narrative structure.

**Gate status:** Gated — returns `GateViolation` if gate not certified.

**Tables touched:** Reads `opposition_pairs`. Writes `opposition_pairs`.

---
