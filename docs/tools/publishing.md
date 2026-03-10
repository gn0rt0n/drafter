[← Documentation Index](../README.md)

# Publishing Tools

Manages publishing assets (query letters, synopses), submission tracking, and submission status updates. Also manages development-internal documentation tasks and research notes.

**Gate status:** Mixed — see individual tool entries. The 5 publishing_assets and submission_tracker tools are gated; the 8 delete/documentation/research tools are gate-free.

**13 tools**

## Index

| Tool Name | Gate | Description |
|-----------|------|-------------|
| `get_publishing_assets` | Gated | Retrieve all publishing assets with optional filter |
| `upsert_publishing_asset` | Gated | Create or update a publishing asset |
| `get_submissions` | Gated | Retrieve all submission tracker entries |
| `log_submission` | Gated | Log a new submission (append-only) |
| `update_submission` | Gated | Partially update a submission tracker entry |
| `delete_publishing_asset` | Free | Delete a publishing asset by ID (FK-safe) |
| `delete_submission` | Free | Delete a submission tracker entry by ID (log-delete) |
| `get_documentation_tasks` | Free | Retrieve all documentation tasks with optional status filter |
| `upsert_documentation_task` | Free | Create or update a documentation task |
| `delete_documentation_task` | Free | Delete a documentation task by ID (FK-safe) |
| `get_research_notes` | Free | Retrieve all research notes with optional relevance filter |
| `upsert_research_note` | Free | Create or update a research note |
| `delete_research_note` | Free | Delete a research note by ID (FK-safe) |

---

## `get_publishing_assets`

**Purpose:** Retrieve all publishing assets with optional `asset_type` filter, ordered by `created_at DESC`.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `asset_type` | `str \| None` | No | Filter by category — "query_letter", "synopsis" |

**Returns:** `list[PublishingAsset] | GateViolation` — All matching `PublishingAsset` records ordered by `created_at DESC`; `GateViolation` if gate not certified.

**Invocation reason:** Called to review existing query letters or synopses before drafting a new version — ensures prior assets are considered and the new version represents an improvement.

**Gate status:** Requires gate certification.

**Tables touched:** Reads `publishing_assets`.

---

## `upsert_publishing_asset`

**Purpose:** Create or update a publishing asset. Two-branch upsert on `id` (PK — no named UNIQUE beyond PK).

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `title` | `str` | Yes | Title of the publishing asset |
| `content` | `str` | Yes | Full text content of the asset |
| `asset_id` | `int \| None` | No | Existing asset ID for update branch |
| `asset_type` | `str` | No (default: `"query_letter"`) | Category — "query_letter", "synopsis" |
| `version` | `int` | No (default: `1`) | Version number |
| `status` | `str` | No (default: `"draft"`) | Publication status |
| `notes` | `str \| None` | No | Additional notes |

**Returns:** `PublishingAsset | GateViolation` — The created or updated `PublishingAsset`; `GateViolation` if gate not certified.

**Invocation reason:** Called when creating or revising a query letter or synopsis — the None-id branch creates a new asset; the provided-id branch updates an existing one, enabling version management.

**Gate status:** Requires gate certification.

**Tables touched:** Reads `publishing_assets`. Writes `publishing_assets`.

---

## `get_submissions`

**Purpose:** Retrieve all submission tracker entries with optional `status` filter, ordered by `submitted_at DESC`.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `status` | `str \| None` | No | Filter by status — "pending", "accepted", "rejected" |

**Returns:** `list[SubmissionEntry] | GateViolation` — All matching `SubmissionEntry` records ordered by `submitted_at DESC`; `GateViolation` if gate not certified.

**Invocation reason:** Called to review the current submission pipeline — identifies pending submissions requiring follow-up and provides a complete submission history.

**Gate status:** Requires gate certification.

**Tables touched:** Reads `submission_tracker`.

---

## `log_submission`

**Purpose:** Log a new submission to an agency or publisher (append-only).

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `agency_or_publisher` | `str` | Yes | Name of the agency or publisher |
| `submitted_at` | `str` | Yes | ISO date/datetime of submission |
| `asset_id` | `int \| None` | No | FK to `publishing_assets` |
| `status` | `str` | No (default: `"pending"`) | Initial status |
| `notes` | `str \| None` | No | Additional notes |

**Returns:** `SubmissionEntry | GateViolation` — The newly created `SubmissionEntry` with id; `GateViolation` if gate not certified.

**Invocation reason:** Called when submitting a query letter or manuscript to an agency or publisher — creates a permanent submission record for tracking response timelines.

**Gate status:** Requires gate certification.

**Tables touched:** Writes `submission_tracker`.

---

## `update_submission`

**Purpose:** Partially update a submission tracker entry. SELECT-back after UPDATE detects missing rows.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `submission_id` | `int` | Yes | ID of the submission to update |
| `status` | `str` | Yes | New submission status |
| `response_at` | `str \| None` | No | Date/datetime when a response was received |
| `response_notes` | `str \| None` | No | Notes on the response |
| `follow_up_due` | `str \| None` | No | Date/datetime for next follow-up |

**Returns:** `SubmissionEntry | NotFoundResponse | GateViolation` — The updated `SubmissionEntry`; `NotFoundResponse` if `submission_id` not found (SQLite does not error on UPDATE of missing row — SELECT-back detects it); `GateViolation` if gate not certified.

**Invocation reason:** Called when a response is received from an agency — updates status from "pending" to "accepted" or "rejected" and records the response date and notes.

**Gate status:** Requires gate certification.

**Tables touched:** Reads `submission_tracker`. Writes `submission_tracker`.

---

## `delete_publishing_asset`

**Purpose:** Delete a publishing asset by ID (FK-safe — submission_tracker references publishing_assets via asset_id FK).

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `asset_id` | `int` | Yes | Primary key of the publishing_assets row to delete |

**Returns:** `NotFoundResponse | ValidationFailure | dict` — Dict with `deleted=True` and `id` on success; `NotFoundResponse` if asset not found; `ValidationFailure` if linked submission_tracker entries exist.

**Invocation reason:** Called to remove a publishing asset record that is no longer needed — e.g., after a draft version is superseded. Returns `ValidationFailure` if submissions still reference the asset.

**Gate status:** Gate-free.

**Tables touched:** Reads `publishing_assets`. Writes `publishing_assets`.

---

## `delete_submission`

**Purpose:** Delete a submission tracker entry by ID (log-delete — submission_tracker is an append-only log with no FK children).

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `submission_id` | `int` | Yes | Primary key of the submission_tracker row to delete |

**Returns:** `NotFoundResponse | dict` — Dict with `deleted=True` and `id` on success; `NotFoundResponse` if submission not found.

**Invocation reason:** Called to remove an erroneously entered submission record or clean up test data. The submission_tracker table has no FK children so no try/except is needed.

**Gate status:** Gate-free.

**Tables touched:** Reads `submission_tracker`. Writes `submission_tracker`.

---

## `get_documentation_tasks`

**Purpose:** Retrieve all documentation tasks with an optional status filter.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `status` | `str \| None` | No | Filter by task status (e.g. `"pending"`, `"in_progress"`, `"done"`) |

**Returns:** `list[DocumentationTask]` — List of `DocumentationTask` records ordered by `id` ASC (may be empty).

**Invocation reason:** Called to review outstanding documentation tasks — pass `status="pending"` to see only pending work, or omit to retrieve all tasks.

**Gate status:** Gate-free.

**Tables touched:** Reads `documentation_tasks`.

---

## `upsert_documentation_task`

**Purpose:** Create or update a documentation task (two-branch upsert on `id` PK — create if no `task_id`, update if `task_id` provided).

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `title` | `str` | Yes | Title of the documentation task |
| `task_id` | `int \| None` | No | Existing task ID for update branch |
| `status` | `str` | No (default: `"pending"`) | Task status |
| `description` | `str \| None` | No | Detailed description of the task |
| `priority` | `str` | No (default: `"normal"`) | Task priority |
| `due_chapter_id` | `int \| None` | No | FK to `chapters` — chapter when task is due |
| `completed_at` | `str \| None` | No | ISO datetime when task was completed |
| `notes` | `str \| None` | No | Additional notes |

**Returns:** `DocumentationTask | ValidationFailure` — The created or updated `DocumentationTask` record; `ValidationFailure` on error.

**Invocation reason:** Called to create a new documentation task or update an existing one — e.g., mark a task as completed by providing `task_id` and `status="done"`.

**Gate status:** Gate-free.

**Tables touched:** Reads `documentation_tasks`. Writes `documentation_tasks`.

---

## `delete_documentation_task`

**Purpose:** Delete a documentation task by ID (FK-safe pattern for consistency, though documentation_tasks is unlikely to have FK children).

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `task_id` | `int` | Yes | Primary key of the documentation_tasks row to delete |

**Returns:** `NotFoundResponse | ValidationFailure | dict` — Dict with `deleted=True` and `id` on success; `NotFoundResponse` if task not found; `ValidationFailure` if a FK constraint prevents deletion.

**Invocation reason:** Called to remove a completed or cancelled documentation task from the tracking table.

**Gate status:** Gate-free.

**Tables touched:** Reads `documentation_tasks`. Writes `documentation_tasks`.

---

## `get_research_notes`

**Purpose:** Retrieve all research notes with an optional relevance filter (LIKE match — partial values supported).

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `relevance` | `str \| None` | No | Filter by relevance using `LIKE '%value%'` match |

**Returns:** `list[ResearchNote]` — List of `ResearchNote` records ordered by `id` ASC (may be empty).

**Invocation reason:** Called to look up research notes on a topic — pass a keyword as `relevance` to find notes with matching relevance tags, or omit to retrieve all notes.

**Gate status:** Gate-free.

**Tables touched:** Reads `research_notes`.

---

## `upsert_research_note`

**Purpose:** Create or update a research note (two-branch upsert on `id` PK — create if no `note_id`, update if `note_id` provided).

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `topic` | `str` | Yes | Topic or subject of the research note |
| `content` | `str` | Yes | Full content/body of the research note |
| `note_id` | `int \| None` | No | Existing note ID for update branch |
| `source` | `str \| None` | No | Source reference for the research |
| `relevance` | `str \| None` | No | How this research relates to the novel |
| `notes` | `str \| None` | No | Additional notes |

**Returns:** `ResearchNote | ValidationFailure` — The created or updated `ResearchNote` record; `ValidationFailure` on error.

**Invocation reason:** Called to record research findings relevant to the novel — e.g., historical facts, cultural details, or technical information that informs the narrative.

**Gate status:** Gate-free.

**Tables touched:** Reads `research_notes`. Writes `research_notes`.

---

## `delete_research_note`

**Purpose:** Delete a research note by ID (FK-safe pattern — research_notes is a leaf table with no FK children).

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `note_id` | `int` | Yes | Primary key of the research_notes row to delete |

**Returns:** `NotFoundResponse | ValidationFailure | dict` — Dict with `deleted=True` and `id` on success; `NotFoundResponse` if note not found; `ValidationFailure` if a FK constraint prevents deletion.

**Invocation reason:** Called to remove obsolete research notes that are no longer relevant to the novel.

**Gate status:** Gate-free.

**Tables touched:** Reads `research_notes`. Writes `research_notes`.

---
