[← Documentation Index](../README.md)

# Magic Tools

Manages the magic system, practitioner abilities, magic use events, and compliance checking. `check_magic_compliance` is read-only; `log_magic_use` is append-only (no UNIQUE constraint).

**Gate status:** All tools in this domain are gate-free.

**14 tools**

## Index

| Tool Name | Gate | Description |
|-----------|------|-------------|
| `get_magic_element` | Free | Look up a single magic system element by ID |
| `get_practitioner_abilities` | Free | Return all magic abilities for a character |
| `log_magic_use` | Free | Append a magic use event to the immutable log |
| `check_magic_compliance` | Free | Check whether a proposed magic action complies with rules |
| `upsert_magic_element` | Free | Create or update a magic system element record |
| `list_magic_elements` | Free | Return all magic system elements ordered by name |
| `upsert_practitioner_ability` | Free | Create or update a practitioner ability for a character |
| `delete_magic_element` | Free | Delete a magic system element by ID (FK-safe) |
| `delete_practitioner_ability` | Free | Delete a practitioner ability by ID (FK-safe) |
| `delete_magic_use_log` | Free | Delete a magic use log entry by ID (log-delete) |
| `get_supernatural_element` | Free | Look up a single supernatural element by ID |
| `list_supernatural_elements` | Free | Return all supernatural elements ordered by name |
| `upsert_supernatural_element` | Free | Create or update a supernatural element record |
| `delete_supernatural_element` | Free | Delete a supernatural element by ID (FK-safe) |

---

## `get_magic_element`

**Purpose:** Look up a single magic system element by ID, returning rules, limitations, costs, and exceptions.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `magic_element_id` | `int` | Yes | Primary key of the magic element |

**Returns:** `MagicSystemElement | NotFoundResponse` — Full `MagicSystemElement` record; `NotFoundResponse` if element does not exist.

**Invocation reason:** Called before writing a magic scene to verify the rules and limitations of the magic being invoked — prevents rule inconsistencies across chapters.

**Gate status:** Gate-free.

**Tables touched:** Reads `magic_system_elements`.

---

## `get_practitioner_abilities`

**Purpose:** Return all registered magic abilities for a character, ordered by ID.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `character_id` | `int` | Yes | Primary key of the character |

**Returns:** `list[PractitionerAbility] | NotFoundResponse` — List of `PractitionerAbility` records; `NotFoundResponse` if the character does not exist. An empty list is valid for characters with no registered abilities.

**Invocation reason:** Called before a magic compliance check to understand which elements a character is registered to use — informs `check_magic_compliance` and narrative accuracy decisions.

**Gate status:** Gate-free.

**Tables touched:** Reads `characters`, `practitioner_abilities`.

---

## `log_magic_use`

**Purpose:** Append a magic use event to the immutable magic use log (append-only, no UNIQUE constraint).

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `chapter_id` | `int` | Yes | FK to chapters table — chapter where magic was used |
| `character_id` | `int` | Yes | FK to characters table — character who performed magic |
| `action_description` | `str` | Yes | Free-text description of the magic action |
| `magic_element_id` | `int \| None` | No | FK to magic_system_elements |
| `scene_id` | `int \| None` | No | FK to scenes table |
| `cost_paid` | `str \| None` | No | Description of the cost the character paid |
| `compliance_status` | `str` | No (default: `"compliant"`) | "compliant", "non_compliant", or "unchecked" |
| `notes` | `str \| None` | No | Free-form notes |

**Returns:** `MagicUseLog | NotFoundResponse | ValidationFailure` — The newly created `MagicUseLog` row; `NotFoundResponse` if chapter does not exist; `ValidationFailure` on DB error.

**Invocation reason:** Called after drafting a magic scene to record the event — maintains an audit trail for later continuity checking and ensures compliance status is tracked alongside the narrative.

**Gate status:** Gate-free.

**Tables touched:** Reads `chapters`. Writes `magic_use_log`.

---

## `check_magic_compliance`

**Purpose:** Check whether a character's proposed magic action complies with system rules. READ-ONLY — does not write to `magic_use_log`.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `character_id` | `int` | Yes | ID of the character performing the action |
| `magic_element_id` | `int` | Yes | ID of the magic element being invoked |
| `action_description` | `str` | Yes | Free-text description of the proposed action |

**Returns:** `MagicComplianceResult | NotFoundResponse` — `MagicComplianceResult` with `compliant` flag, `violations` list, `applicable_rules` list, and `character_has_ability` status; `NotFoundResponse` if the magic element does not exist.

**Invocation reason:** Called before writing a magic scene to pre-validate compliance — if violations are detected, the agent adjusts the scene plan before drafting; if compliant, proceeds then calls `log_magic_use`.

**Gate status:** Gate-free.

**Tables touched:** Reads `magic_system_elements`, `practitioner_abilities`.

---

## `upsert_magic_element`

**Purpose:** Create or update a magic system element.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `element_id` | `int \| None` | Yes | Existing element ID to update, or None to create |
| `name` | `str` | Yes | Name of the magic element (required) |
| `element_type` | `str` | Yes | Category — e.g. "ability", "spell", "rule" (required) |
| `rules` | `str \| None` | No | Rules governing this element (optional) |
| `limitations` | `str \| None` | No | Limitations of this element (optional) |
| `costs` | `str \| None` | No | Costs associated with using this element (optional) |
| `exceptions` | `str \| None` | No | Known exceptions to the rules (optional) |
| `introduced_chapter_id` | `int \| None` | No | FK to chapters — chapter where element first appears (optional) |
| `notes` | `str \| None` | No | Additional notes (optional) |
| `canon_status` | `str` | No | Canon status (default: "draft") |

**Returns:** `MagicSystemElement | ValidationFailure` — The created or updated `MagicSystemElement`; `ValidationFailure` on DB error.

**Invocation reason:** Called during worldbuilding to define the magic system rules and elements — provides the structured data that `check_magic_compliance` uses to validate scenes.

**Gate status:** Gate-free.

**Tables touched:** Reads `magic_system_elements`. Writes `magic_system_elements`.

---

## `list_magic_elements`

**Purpose:** Return all magic system elements ordered by name.

**Parameters:** None

**Returns:** `list[MagicSystemElement]` — All magic system element records ordered alphabetically by `name`. Returns an empty list if no elements exist.

**Invocation reason:** Called when auditing the full magic system or selecting elements for compliance checks — provides a complete list of all defined magic rules and abilities.

**Gate status:** Gate-free.

**Tables touched:** Reads `magic_system_elements`.

---

## `upsert_practitioner_ability`

**Purpose:** Create or update a practitioner ability linking a character to a magic element. Pre-checks that both character_id and magic_element_id exist.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `ability_id` | `int \| None` | Yes | Existing ability ID to update, or None to create |
| `character_id` | `int` | Yes | FK to characters — character who has the ability (required) |
| `magic_element_id` | `int` | Yes | FK to magic_system_elements — element the character can use (required) |
| `proficiency_level` | `int` | No | Proficiency level 1-10 (default: 1) |
| `acquired_chapter_id` | `int \| None` | No | FK to chapters — chapter where ability was acquired (optional) |
| `notes` | `str \| None` | No | Additional notes (optional) |

**Returns:** `PractitionerAbility | NotFoundResponse | ValidationFailure` — The created or updated `PractitionerAbility`; `NotFoundResponse` if character or magic element does not exist; `ValidationFailure` on DB error.

**Invocation reason:** Called when a character gains or improves a magical ability — this record is used by `check_magic_compliance` to confirm a character is authorized to use a specific element.

**Gate status:** Gate-free.

**Tables touched:** Reads `characters`, `magic_system_elements`. Writes `practitioner_abilities`.

---

## `delete_magic_element`

**Purpose:** Delete a magic system element by ID if no FK children reference it.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `magic_element_id` | `int` | Yes | Primary key of the magic element to delete |

**Returns:** `NotFoundResponse | ValidationFailure | dict` — `{"deleted": True, "id": magic_element_id}` on success; `NotFoundResponse` if not found; `ValidationFailure` if FK constraints prevent deletion (practitioner_abilities or magic_use_log reference the element).

**Invocation reason:** Called to remove a magic element that was created in error — only safe when no practitioner abilities or magic use logs reference it.

**Gate status:** Gate-free.

**Tables touched:** Reads `magic_system_elements`. Writes `magic_system_elements`.

---

## `delete_practitioner_ability`

**Purpose:** Delete a practitioner ability record by ID.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `ability_id` | `int` | Yes | Primary key of the practitioner ability to delete |

**Returns:** `NotFoundResponse | ValidationFailure | dict` — `{"deleted": True, "id": ability_id}` on success; `NotFoundResponse` if not found; `ValidationFailure` if FK constraints prevent deletion.

**Invocation reason:** Called to remove a character's magic ability when it is retconned or was logged in error.

**Gate status:** Gate-free.

**Tables touched:** Reads `practitioner_abilities`. Writes `practitioner_abilities`.

---

## `delete_magic_use_log`

**Purpose:** Delete a magic use log entry by primary key.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `magic_use_log_id` | `int` | Yes | Primary key of the magic use log entry to delete |

**Returns:** `NotFoundResponse | dict` — `{"deleted": True, "id": magic_use_log_id}` on success; `NotFoundResponse` if the record does not exist.

**Invocation reason:** Called to remove an incorrectly logged magic use entry — magic_use_log is an append-only log with no FK children so deletion is always safe.

**Gate status:** Gate-free.

**Tables touched:** Reads `magic_use_log`. Writes `magic_use_log`.

---

## `get_supernatural_element`

**Purpose:** Look up a single supernatural element by ID, returning all fields.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `element_id` | `int` | Yes | Primary key of the supernatural element to retrieve |

**Returns:** `SupernaturalElement | NotFoundResponse` — `SupernaturalElement` with all fields if found; `NotFoundResponse` if no element with that ID exists.

**Invocation reason:** Called to load a supernatural element's rules and voice guidelines before writing a scene featuring it — ensures consistent narrative treatment.

**Gate status:** Gate-free.

**Tables touched:** Reads `supernatural_elements`.

---

## `list_supernatural_elements`

**Purpose:** Return all supernatural elements ordered by name.

**Parameters:** None

**Returns:** `list[SupernaturalElement]` — All supernatural element records ordered alphabetically by `name`. Returns an empty list if no elements exist.

**Invocation reason:** Called when auditing the supernatural world or selecting elements for scene planning — provides a complete list of all defined supernatural entities and phenomena.

**Gate status:** Gate-free.

**Tables touched:** Reads `supernatural_elements`.

---

## `upsert_supernatural_element`

**Purpose:** Create or update a supernatural element record.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `element_id` | `int \| None` | Yes | Existing element ID to update, or None to create |
| `name` | `str` | Yes | Name of the supernatural element (required) |
| `element_type` | `str` | Yes | Category — e.g. "creature", "curse", "blessing", "entity" (required) |
| `description` | `str \| None` | No | Description of the supernatural element (optional) |
| `rules` | `str \| None` | No | Rules governing this element (optional) |
| `voice_guidelines` | `str \| None` | No | Voice/writing guidelines for this element (optional) |
| `introduced_chapter_id` | `int \| None` | No | FK to chapters — chapter where element first appears (optional) |
| `notes` | `str \| None` | No | Additional notes (optional) |
| `canon_status` | `str` | No | Canon status (default: "draft") |

**Returns:** `SupernaturalElement | ValidationFailure` — The created or updated `SupernaturalElement`; `ValidationFailure` on DB error.

**Invocation reason:** Called during worldbuilding to define supernatural phenomena — provides the rules and voice guidelines used for consistent narrative treatment.

**Gate status:** Gate-free.

**Tables touched:** Reads `supernatural_elements`. Writes `supernatural_elements`.

---

## `delete_supernatural_element`

**Purpose:** Delete a supernatural element record by ID.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `element_id` | `int` | Yes | Primary key of the supernatural element to delete |

**Returns:** `NotFoundResponse | ValidationFailure | dict` — `{"deleted": True, "id": element_id}` on success; `NotFoundResponse` if not found; `ValidationFailure` if FK constraints prevent deletion.

**Invocation reason:** Called to remove a supernatural element that was created in error or written out of the story.

**Gate status:** Gate-free.

**Tables touched:** Reads `supernatural_elements`. Writes `supernatural_elements`.

---
