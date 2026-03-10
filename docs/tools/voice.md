[← Documentation Index](../README.md)

# Voice Tools

Manages character voice profiles, supernatural voice guidelines, and voice drift detection. All tools are gated — voice is a prose-phase concern requiring gate certification.

**Gate status:** All tools in this domain require gate certification (returns `GateViolation` if not certified).

**9 tools**

## Index

| Tool Name | Gate | Description |
|-----------|------|-------------|
| `get_voice_profile` | Gated | Retrieve the voice profile for a character |
| `upsert_voice_profile` | Gated | Create or update a voice profile for a character |
| `get_supernatural_voice_guidelines` | Gated | Retrieve all supernatural voice guidelines ordered by element_name |
| `log_voice_drift` | Gated | Log a voice drift event for a character (append-only) |
| `get_voice_drift_log` | Gated | Retrieve voice drift log entries for a character |
| `delete_voice_profile` | Gated | Delete a voice profile by ID (FK-safe) |
| `delete_voice_drift` | Gated | Delete a voice drift log entry by primary key |
| `upsert_supernatural_voice_guideline` | Gated | Create or update a supernatural voice guideline |
| `delete_supernatural_voice_guideline` | Gated | Delete a supernatural voice guideline by ID (FK-safe) |

---

## `get_voice_profile`

**Purpose:** Retrieve the voice profile for a character.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `character_id` | `int` | Yes | ID of the character whose voice profile to fetch |

**Returns:** `VoiceProfile | NotFoundResponse | GateViolation` — `VoiceProfile` if found; `NotFoundResponse` if no profile exists for the character; `GateViolation` if gate not certified.

**Invocation reason:** Called before writing dialogue for a character — loads sentence length preferences, verbal tics, vocabulary level, and dialogue sample to ensure the agent maintains consistent voice across all scenes.

**Gate status:** Requires gate certification.

**Tables touched:** Reads `voice_profiles`.

---

## `upsert_voice_profile`

**Purpose:** Create or update a voice profile for a character. Two-branch upsert on `character_id` (UNIQUE column).

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `character_id` | `int` | Yes | ID of the character (UNIQUE — one profile per character) |
| `profile_id` | `int \| None` | No | Existing profile ID for update branch |
| `sentence_length` | `str \| None` | No | Typical sentence length style |
| `vocabulary_level` | `str \| None` | No | Vocabulary complexity level |
| `speech_patterns` | `str \| None` | No | Notable speech patterns |
| `verbal_tics` | `str \| None` | No | Repeated verbal tics or mannerisms |
| `avoids` | `str \| None` | No | Words or constructions the character avoids |
| `internal_voice_notes` | `str \| None` | No | Notes on internal monologue voice |
| `dialogue_sample` | `str \| None` | No | Sample dialogue illustrating the voice |
| `notes` | `str \| None` | No | Additional notes |
| `canon_status` | `str` | No (default: `"draft"`) | Canon status |

**Returns:** `VoiceProfile | GateViolation` — The created or updated `VoiceProfile`; `GateViolation` if gate not certified.

**Invocation reason:** Called during worldbuilding (after gate certification) to establish each character's documented voice, and during revision to refine the voice guidelines based on what emerged during drafting. Gate item `voice_pov` checks all POV characters have a profile.

**Gate status:** Requires gate certification.

**Tables touched:** Reads `voice_profiles`. Writes `voice_profiles`.

---

## `get_supernatural_voice_guidelines`

**Purpose:** Retrieve all supernatural voice guidelines ordered by `element_name`.

**Parameters:** None

**Returns:** `list[SupernaturalVoiceGuideline] | GateViolation` — All guidelines ordered by `element_name ASC`; `GateViolation` if gate not certified.

**Invocation reason:** Called before writing scenes involving supernatural entities — loads the documented voice rules for non-human speech patterns to maintain consistency across appearances.

**Gate status:** Requires gate certification.

**Tables touched:** Reads `supernatural_voice_guidelines`.

---

## `log_voice_drift`

**Purpose:** Log a voice drift event for a character (append-only).

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `character_id` | `int` | Yes | ID of the character exhibiting voice drift |
| `description` | `str` | Yes | Description of the drift observed |
| `drift_type` | `str` | No (default: `"vocabulary"`) | Category — "vocabulary", "syntax", "tone" |
| `severity` | `str` | No (default: `"minor"`) | Severity — "minor", "moderate", "major" |
| `chapter_id` | `int \| None` | No | Chapter where drift was observed |
| `scene_id` | `int \| None` | No | Scene where drift was observed |

**Returns:** `VoiceDriftLog | GateViolation` — The newly created `VoiceDriftLog` record; `GateViolation` if gate not certified.

**Invocation reason:** Called when the drafting agent detects that a character's dialogue has drifted from their established voice profile — creates an audit record for the revision pass.

**Gate status:** Requires gate certification.

**Tables touched:** Writes `voice_drift_log`.

---

## `get_voice_drift_log`

**Purpose:** Retrieve voice drift log entries for a character, ordered by `created_at DESC`. Empty list is valid.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `character_id` | `int` | Yes | ID of the character whose drift log to fetch |

**Returns:** `list[VoiceDriftLog] | GateViolation` — All drift entries ordered by `created_at DESC`; `GateViolation` if gate not certified. Empty list is a valid response (no drift = good voice consistency).

**Invocation reason:** Called during a voice consistency review pass — examines the drift history to identify patterns in how and where a character's voice breaks down.

**Gate status:** Requires gate certification.

**Tables touched:** Reads `voice_drift_log`.

---

## `delete_voice_profile`

**Purpose:** Delete a voice profile by ID. Gate-gated — FK-safe pattern.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `voice_profile_id` | `int` | Yes | Primary key of the voice profile to delete |

**Returns:** `GateViolation | NotFoundResponse | ValidationFailure | dict` — `{"deleted": True, "id": voice_profile_id}` on success; `GateViolation` if gate not certified; `NotFoundResponse` if not found; `ValidationFailure` if FK constraints prevent deletion.

**Invocation reason:** Called to remove a voice profile that was created in error — requires gate certification since voice management is a prose-phase operation.

**Gate status:** Gated — returns `GateViolation` if gate not certified.

**Tables touched:** Reads `voice_profiles`. Writes `voice_profiles`.

---

## `delete_voice_drift`

**Purpose:** Delete a voice drift log entry by primary key. Gate-gated.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `voice_drift_id` | `int` | Yes | Primary key of the voice drift log entry to delete |

**Returns:** `GateViolation | NotFoundResponse | dict` — `{"deleted": True, "id": voice_drift_id}` on success; `GateViolation` if gate not certified; `NotFoundResponse` if not found.

**Invocation reason:** Called to remove a voice drift entry that was logged in error — voice_drift_log is an append-only log with no FK children so deletion is always safe once gate-certified.

**Gate status:** Gated — returns `GateViolation` if gate not certified.

**Tables touched:** Reads `voice_drift_log`. Writes `voice_drift_log`.

---

## `upsert_supernatural_voice_guideline`

**Purpose:** Create or update a supernatural voice guideline. Gate-gated.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `guideline_id` | `int \| None` | Yes | Existing guideline ID to update, or None to create |
| `element_name` | `str` | Yes | Name of the supernatural element — UNIQUE in table (required) |
| `writing_rules` | `str` | Yes | Writing rules for this element's voice (required) |
| `element_type` | `str` | No | Category of element — e.g. "creature", "spirit" (default: "creature") |
| `avoid` | `str \| None` | No | Things to avoid when writing this element (optional) |
| `example_phrases` | `str \| None` | No | Example phrases for this element's voice (optional) |
| `notes` | `str \| None` | No | Additional notes (optional) |

**Returns:** `GateViolation | SupernaturalVoiceGuideline | ValidationFailure` — The created or updated `SupernaturalVoiceGuideline`; `GateViolation` if gate not certified; `ValidationFailure` on DB error.

**Invocation reason:** Called to define writing rules for supernatural entities — ensures consistent and distinctive voice treatment for non-human characters and phenomena.

**Gate status:** Gated — returns `GateViolation` if gate not certified.

**Tables touched:** Reads `supernatural_voice_guidelines`. Writes `supernatural_voice_guidelines`.

---

## `delete_supernatural_voice_guideline`

**Purpose:** Delete a supernatural voice guideline by ID. Gate-gated — FK-safe pattern.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `guideline_id` | `int` | Yes | Primary key of the supernatural voice guideline to delete |

**Returns:** `GateViolation | NotFoundResponse | ValidationFailure | dict` — `{"deleted": True, "id": guideline_id}` on success; `GateViolation` if gate not certified; `NotFoundResponse` if not found; `ValidationFailure` if FK constraints prevent deletion.

**Invocation reason:** Called to remove a supernatural voice guideline that was created in error or for an entity written out of the story.

**Gate status:** Gated — returns `GateViolation` if gate not certified.

**Tables touched:** Reads `supernatural_voice_guidelines`. Writes `supernatural_voice_guidelines`.

---
