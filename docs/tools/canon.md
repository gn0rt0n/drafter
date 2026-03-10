[← Documentation Index](../README.md)

# Canon Tools

Manages the canonical record: canon facts, story decisions log, and continuity issues. Canon facts, decisions, and continuity issues all use append-only INSERT (no ON CONFLICT) — they are audit log tables.

**Gate status:** All tools in this domain require gate certification (returns `GateViolation` if not certified).

**10 tools**

## Index

| Tool Name | Gate | Description |
|-----------|------|-------------|
| `get_canon_facts` | Gated | Retrieve all canon facts for a domain |
| `log_canon_fact` | Gated | Log a new canon fact (append-only) |
| `log_decision` | Gated | Log a story decision with rationale |
| `get_decisions` | Gated | Retrieve the decisions log with optional filters |
| `log_continuity_issue` | Gated | Log a new continuity issue |
| `get_continuity_issues` | Gated | Retrieve open continuity issues |
| `resolve_continuity_issue` | Gated | Resolve a continuity issue by ID |
| `delete_canon_fact` | Gated | Delete a canon fact by ID (FK-safe) |
| `delete_continuity_issue` | Gated | Delete a continuity issue log entry by ID (log-delete) |
| `delete_decision` | Gated | Delete a story decision log entry by ID (log-delete) |

---

## `get_canon_facts`

**Purpose:** Retrieve all canon facts for a given domain, ordered by `created_at`.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `domain` | `str` | Yes | Domain to filter by — "magic", "geography", "general", etc. |

**Returns:** `list[CanonFact] | GateViolation` — All `CanonFact` records for the domain; `GateViolation` if gate not certified.

**Invocation reason:** Called before drafting a scene that involves domain-specific facts — ensures narrative content is consistent with established canon in that domain.

**Gate status:** Requires gate certification.

**Tables touched:** Reads `canon_facts`.

---

## `log_canon_fact`

**Purpose:** Log a new canon fact (append-only INSERT — creates a new row each call).

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `fact` | `str` | Yes | The canon fact text |
| `domain` | `str` | No (default: `"general"`) | Domain the fact belongs to |
| `source_chapter_id` | `int \| None` | No | Chapter where the fact was established |
| `source_event_id` | `int \| None` | No | Event that established the fact |
| `parent_fact_id` | `int \| None` | No | Parent fact this derives from |
| `certainty_level` | `str` | No (default: `"established"`) | Certainty level |
| `canon_status` | `str` | No (default: `"approved"`) | Canon status |
| `notes` | `str \| None` | No | Additional notes |

**Returns:** `CanonFact | GateViolation` — The newly created `CanonFact` record; `GateViolation` if gate not certified.

**Invocation reason:** Called when a story event definitively establishes a world fact — creates an authoritative record that future scenes can query to maintain consistency. Gate item `canon_domains` requires facts in at least 3 distinct domains.

**Gate status:** Requires gate certification.

**Tables touched:** Writes `canon_facts`.

---

## `log_decision`

**Purpose:** Log a story decision with rationale to the decisions log (append-only).

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `description` | `str` | Yes | Description of the decision made |
| `decision_type` | `str` | No (default: `"plot"`) | Type — "plot", "character", "world" |
| `rationale` | `str \| None` | No | Why this decision was made |
| `alternatives` | `str \| None` | No | Alternatives that were considered |
| `session_id` | `int \| None` | No | Writing session this decision was made in |
| `chapter_id` | `int \| None` | No | Chapter this decision applies to |

**Returns:** `StoryDecision | GateViolation` — The newly created `StoryDecision` record; `GateViolation` if gate not certified.

**Invocation reason:** Called when logging a completed story decision to maintain an audit trail of why narrative choices were made — enables later review of decision rationale and supports consistent storytelling across long manuscripts.

**Gate status:** Requires gate certification.

**Tables touched:** Writes `decisions_log`.

---

## `get_decisions`

**Purpose:** Retrieve the decisions log with optional filters by `decision_type` and/or `chapter_id`.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `decision_type` | `str \| None` | No | Filter by decision type |
| `chapter_id` | `int \| None` | No | Filter by chapter |

**Returns:** `list[StoryDecision] | GateViolation` — All matching `StoryDecision` records ordered by `created_at DESC`; `GateViolation` if gate not certified.

**Invocation reason:** Called when reviewing why specific narrative decisions were made — helpful during revision to understand the reasoning behind earlier choices and whether those choices still serve the story.

**Gate status:** Requires gate certification.

**Tables touched:** Reads `decisions_log`.

---

## `log_continuity_issue`

**Purpose:** Log a new continuity issue with severity triage (append-only).

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `description` | `str` | Yes | Description of the continuity issue |
| `severity` | `str` | No (default: `"minor"`) | Severity — "minor", "major", "critical" |
| `chapter_id` | `int \| None` | No | Chapter where the issue occurs |
| `scene_id` | `int \| None` | No | Scene where the issue occurs |
| `canon_fact_id` | `int \| None` | No | Canon fact this issue relates to |

**Returns:** `ContinuityIssue | GateViolation` — The newly created `ContinuityIssue` record; `GateViolation` if gate not certified.

**Invocation reason:** Called when detecting a contradiction between a draft and previously established facts — records the issue for later resolution without interrupting the drafting flow.

**Gate status:** Requires gate certification.

**Tables touched:** Writes `continuity_issues`.

---

## `get_continuity_issues`

**Purpose:** Retrieve open continuity issues with optional severity filter. Open issues only by default.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `severity` | `str \| None` | No | Filter by severity |
| `include_resolved` | `bool` | No (default: `False`) | Include resolved issues |

**Returns:** `list[ContinuityIssue] | GateViolation` — All matching `ContinuityIssue` records ordered by `created_at ASC`; `GateViolation` if gate not certified.

**Invocation reason:** Called during revision passes to systematically work through outstanding continuity issues — reviewing by severity ensures critical contradictions are resolved before minor ones.

**Gate status:** Requires gate certification.

**Tables touched:** Reads `continuity_issues`.

---

## `resolve_continuity_issue`

**Purpose:** Resolve a continuity issue by ID, recording the resolution note.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `issue_id` | `int` | Yes | ID of the continuity issue to resolve |
| `resolution_note` | `str` | Yes | Description of how the issue was resolved |

**Returns:** `ContinuityIssue | NotFoundResponse | GateViolation` — The updated `ContinuityIssue` with `is_resolved=True`; `NotFoundResponse` if issue_id not found (SELECT-back after UPDATE detects missing row); `GateViolation` if gate not certified.

**Invocation reason:** Called after editing a chapter to fix a documented continuity issue — marks the issue as resolved so it no longer appears in `get_continuity_issues` results.

**Gate status:** Requires gate certification.

**Tables touched:** Reads `continuity_issues`. Writes `continuity_issues`.

---

## `delete_canon_fact`

**Purpose:** Delete a canon fact entry by ID. Gate-gated — FK-safe pattern.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `canon_fact_id` | `int` | Yes | Primary key of the canon fact to delete |

**Returns:** `GateViolation | NotFoundResponse | ValidationFailure | dict` — `{"deleted": True, "id": canon_fact_id}` on success; `GateViolation` if gate not certified; `NotFoundResponse` if not found; `ValidationFailure` if FK constraints prevent deletion.

**Invocation reason:** Called to remove a canon fact that was logged in error or invalidated by a story revision — requires gate certification since canon management is a prose-phase operation.

**Gate status:** Gated — returns `GateViolation` if gate not certified.

**Tables touched:** Reads `canon_facts`. Writes `canon_facts`.

---

## `delete_continuity_issue`

**Purpose:** Delete a continuity issue entry by primary key. Gate-gated.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `issue_id` | `int` | Yes | Primary key of the continuity issue to delete |

**Returns:** `GateViolation | NotFoundResponse | dict` — `{"deleted": True, "id": issue_id}` on success; `GateViolation` if gate not certified; `NotFoundResponse` if not found.

**Invocation reason:** Called to remove a continuity issue that was logged in error — continuity_issues is a log table with no FK children so deletion is always safe once gate-certified.

**Gate status:** Gated — returns `GateViolation` if gate not certified.

**Tables touched:** Reads `continuity_issues`. Writes `continuity_issues`.

---

## `delete_decision`

**Purpose:** Delete a story decision log entry by primary key. Gate-gated.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `decision_id` | `int` | Yes | Primary key of the decision log entry to delete |

**Returns:** `GateViolation | NotFoundResponse | dict` — `{"deleted": True, "id": decision_id}` on success; `GateViolation` if gate not certified; `NotFoundResponse` if not found.

**Invocation reason:** Called to remove a decision log entry that was recorded in error — decisions_log is a log table with no FK children so deletion is always safe once gate-certified.

**Gate status:** Gated — returns `GateViolation` if gate not certified.

**Tables touched:** Reads `decisions_log`. Writes `decisions_log`.

---
