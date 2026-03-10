[← Documentation Index](../README.md)

# Relationships Tools

Manages character-to-character relationships (bidirectional bond) and directional perception profiles (how one character views another). Handles the canonical pair ordering so callers never need to know min/max storage order.

**Gate status:** All tools in this domain are gate-free.

**9 tools**

## Index

| Tool Name | Gate | Description |
|-----------|------|-------------|
| `get_relationship` | Free | Look up the relationship between two characters |
| `list_relationships` | Free | Return all relationships for a character |
| `upsert_relationship` | Free | Create or update a character relationship |
| `get_perception_profile` | Free | Return one character's perception of another |
| `upsert_perception_profile` | Free | Create or update a perception profile |
| `log_relationship_change` | Free | Record a change event for a relationship |
| `delete_relationship` | Free | Delete a relationship between two characters (FK-safe) |
| `delete_relationship_change` | Free | Delete a relationship change log entry by ID (log-delete) |
| `delete_perception_profile` | Free | Delete a perception profile between two characters (FK-safe) |

---

## `get_relationship`

**Purpose:** Look up the relationship between two characters, querying both canonical orderings.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `character_a_id` | `int` | Yes | First character ID in the pair |
| `character_b_id` | `int` | Yes | Second character ID in the pair |

**Returns:** `CharacterRelationship | NotFoundResponse` — `CharacterRelationship` if a row exists; `NotFoundResponse` if no relationship has been recorded between these two characters.

**Invocation reason:** Called before drafting a scene involving two characters — verifies their current bond strength, trust level, and relationship type to ensure interactions are consistent with established dynamics.

**Gate status:** Gate-free.

**Tables touched:** Reads `character_relationships`.

---

## `list_relationships`

**Purpose:** Return all relationships where the given character appears as either party.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `character_id` | `int` | Yes | ID of the character whose relationships to retrieve |

**Returns:** `list[CharacterRelationship]` — All relationships for the character ordered by `updated_at DESC`. Returns an empty list if the character has no recorded relationships.

**Invocation reason:** Called to build a complete social map of a character — useful when planning a scene that involves multiple relationships, or when auditing relationship coverage before gate certification.

**Gate status:** Gate-free.

**Tables touched:** Reads `character_relationships`.

---

## `upsert_relationship`

**Purpose:** Create or update the relationship between two characters, canonicalizing pair order.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `character_a_id` | `int` | Yes | First character ID (will be canonicalized to min) |
| `character_b_id` | `int` | Yes | Second character ID (will be canonicalized to max) |
| `relationship_type` | `str` | No (default: `"acquaintance"`) | Type label — "ally", "rival", "enemy", etc. |
| `bond_strength` | `int` | No (default: `0`) | Numeric bond intensity (positive = strong) |
| `trust_level` | `int` | No (default: `0`) | Numeric trust score (positive = high trust) |
| `current_status` | `str` | No (default: `"neutral"`) | Relationship status — "neutral", "active", "hostile" |
| `history_summary` | `str \| None` | No | Free-text summary of relationship history |
| `first_meeting_chapter_id` | `int \| None` | No | FK to chapters where they first met |
| `notes` | `str \| None` | No | Free-form notes |
| `canon_status` | `str` | No (default: `"draft"`) | Approval status — "draft" or "approved" |

**Returns:** `CharacterRelationship | ValidationFailure` — The created or updated `CharacterRelationship`; `ValidationFailure` on DB error.

**Invocation reason:** Called when establishing a relationship during worldbuilding, or updating it after a scene causes a significant shift in bond or trust. The canonicalization ensures exactly one row per pair regardless of argument order.

**Gate status:** Gate-free.

**Tables touched:** Reads `character_relationships`. Writes `character_relationships`.

---

## `get_perception_profile`

**Purpose:** Return the perception profile one character holds of another (directional).

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `observer_id` | `int` | Yes | ID of the character whose perception is recorded |
| `subject_id` | `int` | Yes | ID of the character being perceived |

**Returns:** `PerceptionProfile | NotFoundResponse` — `PerceptionProfile` for this (observer, subject) pair; `NotFoundResponse` if no profile has been recorded.

**Invocation reason:** Called before writing POV scenes where the narrator perceives another character — ensures the described perception (misperceptions, emotional valence, trust level) matches what was previously established.

**Gate status:** Gate-free.

**Tables touched:** Reads `perception_profiles`.

---

## `upsert_perception_profile`

**Purpose:** Create or update the perception profile for an (observer, subject) pair.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `observer_id` | `int` | Yes | ID of the observing character |
| `subject_id` | `int` | Yes | ID of the subject character being perceived |
| `chapter_id` | `int \| None` | No | Chapter at which this perception snapshot applies |
| `perceived_traits` | `str \| None` | No | Free-text description of perceived personality traits |
| `trust_level` | `int` | No (default: `0`) | Observer's trust rating of the subject |
| `emotional_valence` | `str` | No (default: `"neutral"`) | Emotional orientation — "neutral", "trusting", "wary" |
| `misperceptions` | `str \| None` | No | Known misperceptions the observer holds |
| `notes` | `str \| None` | No | Free-form notes |

**Returns:** `PerceptionProfile | ValidationFailure` — The created or updated `PerceptionProfile`; `ValidationFailure` on DB error.

**Invocation reason:** Called after a scene that shifts how a character perceives another — recording the updated misperceptions or emotional valence for use in future POV scenes.

**Gate status:** Gate-free.

**Tables touched:** Reads `perception_profiles`. Writes `perception_profiles`.

---

## `log_relationship_change`

**Purpose:** Record a change event for an existing relationship, with deltas for bond and trust.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `relationship_id` | `int` | Yes | FK to `character_relationships.id` — must exist |
| `chapter_id` | `int \| None` | No | Chapter at which this change occurred |
| `event_id` | `int \| None` | No | FK to story events table |
| `change_type` | `str` | No (default: `"shift"`) | Nature — "shift", "breakthrough", "rupture" |
| `description` | `str` | No (default: `""`) | Human-readable description of what changed |
| `bond_delta` | `int` | No (default: `0`) | Change in bond strength (positive = stronger) |
| `trust_delta` | `int` | No (default: `0`) | Change in trust level (positive = more trust) |

**Returns:** `RelationshipChangeEvent | NotFoundResponse | ValidationFailure` — The newly created `RelationshipChangeEvent` with assigned id; `NotFoundResponse` if `relationship_id` does not exist; `ValidationFailure` on DB error.

**Invocation reason:** Called after drafting a scene where a relationship meaningfully shifts — creates an audit trail of relationship progression that informs later narrative decisions.

**Gate status:** Gate-free.

**Tables touched:** Reads `character_relationships`. Writes `relationship_change_events`.

---

## `delete_relationship`

**Purpose:** Delete a character relationship record by ID if no FK children reference it.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `relationship_id` | `int` | Yes | Primary key of the relationship to delete |

**Returns:** `NotFoundResponse | ValidationFailure | dict` — `{"deleted": True, "id": relationship_id}` on success; `NotFoundResponse` if not found; `ValidationFailure` if FK constraints prevent deletion.

**Invocation reason:** Called to remove a relationship record that was created in error — only safe when no relationship_change_events or perception_profiles reference it.

**Gate status:** Gate-free.

**Tables touched:** Reads `character_relationships`. Writes `character_relationships`.

---

## `delete_relationship_change`

**Purpose:** Delete a relationship change event record by primary key.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `change_id` | `int` | Yes | Primary key of the relationship change event to delete |

**Returns:** `NotFoundResponse | dict` — `{"deleted": True, "id": change_id}` on success; `NotFoundResponse` if the record does not exist.

**Invocation reason:** Called to remove an incorrectly logged relationship change event — relationship_change_events is a log table with no FK children so deletion is always safe.

**Gate status:** Gate-free.

**Tables touched:** Reads `relationship_change_events`. Writes `relationship_change_events`.

---

## `delete_perception_profile`

**Purpose:** Delete a perception profile record by ID if no FK children reference it.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `profile_id` | `int` | Yes | Primary key of the perception profile to delete |

**Returns:** `NotFoundResponse | ValidationFailure | dict` — `{"deleted": True, "id": profile_id}` on success; `NotFoundResponse` if not found; `ValidationFailure` if FK constraints prevent deletion.

**Invocation reason:** Called to remove a perception profile created in error — safe when no child records reference this profile.

**Gate status:** Gate-free.

**Tables touched:** Reads `perception_profiles`. Writes `perception_profiles`.

---
