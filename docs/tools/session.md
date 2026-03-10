[← Documentation Index](../README.md)

# Session Tools

Manages writing session lifecycle, project metrics snapshots, POV balance analysis, open questions, and agent run auditing. All tools require gate certification — session tools are prose-phase operations.

**Gate status:** All tools in this domain require gate certification (returns `GateViolation` if not certified).

**16 tools**

## Index

| Tool Name | Gate | Description |
|-----------|------|-------------|
| `start_session` | Gated | Start a new writing session with prior-session briefing |
| `close_session` | Gated | Close an open session and record summary |
| `get_last_session` | Gated | Retrieve the most recent session log entry |
| `log_agent_run` | Gated | Append an agent run entry to the audit trail |
| `get_project_metrics` | Gated | Retrieve live-computed project metrics |
| `log_project_snapshot` | Gated | Persist a project metrics snapshot |
| `get_pov_balance` | Gated | Retrieve live-computed POV balance across chapters |
| `get_open_questions` | Gated | Retrieve all unanswered open questions |
| `log_open_question` | Gated | Append a new open question to the log |
| `answer_open_question` | Gated | Mark an open question as answered |
| `delete_session_log` | Gated | Delete a session log entry by ID (FK-safe) |
| `delete_agent_run_log` | Gated | Delete an agent run log entry by ID (log-delete) |
| `delete_open_question` | Gated | Delete an open question log entry by ID (log-delete) |
| `delete_project_snapshot` | Gated | Delete a project metrics snapshot by ID (log-delete) |
| `log_pov_balance_snapshot` | Gated | Persist a POV balance snapshot for a chapter |
| `delete_pov_balance_snapshot` | Gated | Delete a POV balance snapshot by ID (log-delete) |

---

## `start_session`

**Purpose:** Start a new writing session and return a briefing from the prior session. Auto-closes any open session before creating the new one.

**Parameters:** None

**Returns:** `SessionStartResult | GateViolation` — `SessionStartResult` containing the new `SessionLog` and an optional prior-session briefing `SessionLog`; `GateViolation` if gate is not certified.

**Invocation reason:** Called at the very start of each writing session — auto-closes stale open sessions, creates a new session record, and provides the prior session's summary and carried-forward questions as context.

**Gate status:** Requires gate certification (returns `GateViolation` if not certified).

**Tables touched:** Reads `session_logs`. Writes `session_logs`.

---

## `close_session`

**Purpose:** Close an open session, record summary and metadata, and auto-populate `carried_forward` from unanswered open questions.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `session_id` | `int` | Yes | Primary key of the open session to close |
| `summary` | `str \| None` | No | Summary of work done this session |
| `word_count_delta` | `int` | No (default: `0`) | Net word count change this session |
| `chapters_touched` | `list[int] \| None` | No | List of chapter IDs worked on |

**Returns:** `SessionLog | NotFoundResponse | GateViolation` — Updated `SessionLog` row; `NotFoundResponse` if session not found or already closed; `GateViolation` if gate not certified.

**Invocation reason:** Called at the end of each writing session to record what was accomplished and snapshot all unanswered open questions into `carried_forward` for the next session's briefing.

**Gate status:** Requires gate certification.

**Tables touched:** Reads `session_logs`, `open_questions`. Writes `session_logs`.

---

## `get_last_session`

**Purpose:** Retrieve the most recently started session log entry.

**Parameters:** None

**Returns:** `SessionLog | NotFoundResponse | GateViolation` — Most recent `SessionLog`; `NotFoundResponse` if no sessions exist; `GateViolation` if gate not certified.

**Invocation reason:** Called to review what was last worked on when resuming a project — provides context without starting a new session.

**Gate status:** Requires gate certification.

**Tables touched:** Reads `session_logs`.

---

## `log_agent_run`

**Purpose:** Append an agent run entry to the audit trail (append-only, no UNIQUE constraint).

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `agent_name` | `str` | Yes | Name of the agent that ran |
| `tool_name` | `str` | Yes | Name of the tool the agent called |
| `input_summary` | `str \| None` | No | Brief description of the tool input |
| `output_summary` | `str \| None` | No | Brief description of the tool output |
| `duration_ms` | `int \| None` | No | Duration in milliseconds |
| `success` | `bool` | No (default: `True`) | Whether the run succeeded |
| `session_id` | `int \| None` | No | FK to session_logs |
| `error_message` | `str \| None` | No | Error description if success is False |

**Returns:** `AgentRunLog | GateViolation` — The newly created `AgentRunLog` row; `GateViolation` if gate not certified.

**Invocation reason:** Called after each significant tool invocation during prose drafting to maintain an audit trail — useful for debugging multi-agent workflows and understanding which tools were called in a session.

**Gate status:** Requires gate certification.

**Tables touched:** Writes `agent_run_log`.

---

## `get_project_metrics`

**Purpose:** Retrieve live-computed project metrics (aggregated directly from DB, not stored snapshots).

**Parameters:** None

**Returns:** `ProjectMetricsSnapshot | GateViolation` — `ProjectMetricsSnapshot` with live `word_count` (from `actual_word_count`), `chapter_count`, `scene_count`, `character_count`, `session_count` (id and snapshot_at are None for live results); `GateViolation` if gate not certified.

**Invocation reason:** Called at the start of a session to assess current project progress — provides a live dashboard of word count and structural completion without persisting a snapshot.

**Gate status:** Requires gate certification.

**Tables touched:** Reads `chapters`, `scenes`, `characters`, `session_logs`.

---

## `log_project_snapshot`

**Purpose:** Persist a project metrics snapshot to the database for historical tracking.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `notes` | `str \| None` | No | Optional notes to store with the snapshot |

**Returns:** `ProjectMetricsSnapshot | GateViolation` — The newly created `ProjectMetricsSnapshot` row with `id` and `snapshot_at` populated; `GateViolation` if gate not certified.

**Invocation reason:** Called at significant milestones (completing a draft chapter, finishing a revision pass) to create a persistent progress record — enables tracking velocity and word count growth over time.

**Gate status:** Requires gate certification.

**Tables touched:** Reads `chapters`, `scenes`, `characters`, `session_logs`. Writes `project_metrics_snapshots`.

---

## `get_pov_balance`

**Purpose:** Retrieve live-computed POV balance across all chapters, grouped by POV character.

**Parameters:** None

**Returns:** `list[PovBalanceSnapshot] | GateViolation` — List of `PovBalanceSnapshot` records ordered by `chapter_count DESC`; `GateViolation` if gate not certified. Empty list if no chapters have POV characters assigned.

**Invocation reason:** Called during revision to check whether POV chapter distribution is proportional to each character's narrative importance — identifies characters who are over- or under-represented.

**Gate status:** Requires gate certification.

**Tables touched:** Reads `chapters`.

---

## `get_open_questions`

**Purpose:** Retrieve all unanswered open questions (answered_at IS NULL), optionally filtered by domain.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `domain` | `str \| None` | No | Optional domain filter — "plot", "character", "world" |

**Returns:** `list[OpenQuestion] | GateViolation` — All unanswered `OpenQuestion` records ordered by `created_at ASC`; `GateViolation` if gate not certified.

**Invocation reason:** Called at session start to review unresolved narrative questions from prior sessions — ensures no open plot or character question is forgotten across sessions.

**Gate status:** Requires gate certification.

**Tables touched:** Reads `open_questions`.

---

## `log_open_question`

**Purpose:** Append a new open question to the log (append-only — duplicate questions allowed).

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `question` | `str` | Yes | The question text |
| `domain` | `str \| None` | No (default: `"general"`) | Domain classification — "plot", "character", "world" |
| `session_id` | `int \| None` | No | FK to session_logs |
| `priority` | `str \| None` | No (default: `"normal"`) | Priority — "high", "normal", "low" |
| `notes` | `str \| None` | No | Freeform notes |

**Returns:** `OpenQuestion | GateViolation` — The newly created `OpenQuestion` row; `GateViolation` if gate not certified.

**Invocation reason:** Called during drafting whenever a narrative question arises that requires a decision — prevents questions from being lost and ensures they surface in the next session's briefing via `carried_forward`.

**Gate status:** Requires gate certification.

**Tables touched:** Writes `open_questions`.

---

## `answer_open_question`

**Purpose:** Mark an open question as answered, recording the answer and setting `answered_at`.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `question_id` | `int` | Yes | Primary key of the open_questions row |
| `answer` | `str` | Yes | The answer text to record |

**Returns:** `OpenQuestion | NotFoundResponse | GateViolation` — Updated `OpenQuestion` with `answered_at` populated; `NotFoundResponse` if question_id not found; `GateViolation` if gate not certified.

**Invocation reason:** Called when a narrative decision is made that resolves a previously logged open question — updates the record so the question no longer appears in `get_open_questions` results.

**Gate status:** Requires gate certification.

**Tables touched:** Reads `open_questions`. Writes `open_questions`.

---

## `delete_session_log`

**Purpose:** Delete a session log entry by ID. Gate-gated — session_logs may be referenced by agent_run_log via FK.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `session_log_id` | `int` | Yes | Primary key of the session log entry to delete |

**Returns:** `GateViolation | NotFoundResponse | ValidationFailure | dict` — `{"deleted": True, "id": session_log_id}` on success; `GateViolation` if gate not certified; `NotFoundResponse` if not found; `ValidationFailure` if FK constraints prevent deletion.

**Invocation reason:** Called to remove a session log entry that was created in error — requires gate certification since session management is a prose-phase operation.

**Gate status:** Gated — returns `GateViolation` if gate not certified.

**Tables touched:** Reads `session_logs`. Writes `session_logs`.

---

## `delete_agent_run_log`

**Purpose:** Delete an agent run log entry by primary key. Gate-gated.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `agent_run_log_id` | `int` | Yes | Primary key of the agent run log entry to delete |

**Returns:** `GateViolation | NotFoundResponse | dict` — `{"deleted": True, "id": agent_run_log_id}` on success; `GateViolation` if gate not certified; `NotFoundResponse` if not found.

**Invocation reason:** Called to remove an agent run log entry that was created in error — agent_run_log is an append-only log with no FK children so deletion is always safe once gate-certified.

**Gate status:** Gated — returns `GateViolation` if gate not certified.

**Tables touched:** Reads `agent_run_log`. Writes `agent_run_log`.

---

## `delete_open_question`

**Purpose:** Delete an open question by primary key. Gate-gated.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `open_question_id` | `int` | Yes | Primary key of the open question to delete |

**Returns:** `GateViolation | NotFoundResponse | dict` — `{"deleted": True, "id": open_question_id}` on success; `GateViolation` if gate not certified; `NotFoundResponse` if not found.

**Invocation reason:** Called to remove an open question that was logged in error or is no longer relevant — open_questions is a log table with no FK children so deletion is always safe once gate-certified.

**Gate status:** Gated — returns `GateViolation` if gate not certified.

**Tables touched:** Reads `open_questions`. Writes `open_questions`.

---

## `delete_project_snapshot`

**Purpose:** Delete a project metrics snapshot by primary key. Gate-gated.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `snapshot_id` | `int` | Yes | Primary key of the project metrics snapshot to delete |

**Returns:** `GateViolation | NotFoundResponse | dict` — `{"deleted": True, "id": snapshot_id}` on success; `GateViolation` if gate not certified; `NotFoundResponse` if not found.

**Invocation reason:** Called to remove an obsolete or incorrectly logged project metrics snapshot — project_metrics_snapshots is a log table with no FK children so deletion is always safe once gate-certified.

**Gate status:** Gated — returns `GateViolation` if gate not certified.

**Tables touched:** Reads `project_metrics_snapshots`. Writes `project_metrics_snapshots`.

---

## `log_pov_balance_snapshot`

**Purpose:** Append a POV balance snapshot entry to the log. Gate-gated. Pre-checks chapter_id if provided.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `chapter_id` | `int \| None` | No | FK to chapters — chapter context for this snapshot (optional) |
| `character_id` | `int \| None` | No | FK to characters — character whose POV balance is recorded (optional) |
| `chapter_count` | `int` | No | Number of chapters from this character's POV (default: 0) |
| `word_count` | `int` | No | Word count from this character's POV (default: 0) |

**Returns:** `PovBalanceSnapshot | GateViolation | NotFoundResponse | ValidationFailure` — The newly created `PovBalanceSnapshot`; `GateViolation` if gate not certified; `NotFoundResponse` if chapter_id does not exist; `ValidationFailure` on DB error.

**Invocation reason:** Called periodically during production to track POV distribution across chapters — enables detection of POV imbalance that could signal under-served character arcs.

**Gate status:** Gated — returns `GateViolation` if gate not certified.

**Tables touched:** Reads `chapters`. Writes `pov_balance_snapshots`.

---

## `delete_pov_balance_snapshot`

**Purpose:** Delete a POV balance snapshot entry by primary key. Gate-gated.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `snapshot_id` | `int` | Yes | Primary key of the POV balance snapshot to delete |

**Returns:** `GateViolation | NotFoundResponse | dict` — `{"deleted": True, "id": snapshot_id}` on success; `GateViolation` if gate not certified; `NotFoundResponse` if not found.

**Invocation reason:** Called to remove an incorrectly logged POV balance snapshot — pov_balance_snapshots is a log table with no FK children so deletion is always safe once gate-certified.

**Gate status:** Gated — returns `GateViolation` if gate not certified.

**Tables touched:** Reads `pov_balance_snapshots`. Writes `pov_balance_snapshots`.

---
