[← Documentation Index](../README.md)

# Plot Tools

Manages plot threads (main, subplot, backstory). Does NOT touch the `chapter_plot_threads` junction table — that is managed via chapter tools.

**Gate status:** All tools in this domain are gate-free.

**7 tools**

## Index

| Tool Name | Gate | Description |
|-----------|------|-------------|
| `get_plot_thread` | Free | Look up a single plot thread by ID |
| `list_plot_threads` | Free | List all plot threads with optional filters |
| `upsert_plot_thread` | Free | Create or update a plot thread |
| `delete_plot_thread` | Free | Delete a plot thread by ID (FK-safe) |
| `link_chapter_to_plot_thread` | Free | Link a chapter to a plot thread (upsert junction) |
| `unlink_chapter_from_plot_thread` | Free | Remove the link between a chapter and a plot thread |
| `get_plot_threads_for_chapter` | Free | Return all plot threads linked to a chapter |

---

## `get_plot_thread`

**Purpose:** Look up a single plot thread by ID, returning all fields.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `plot_thread_id` | `int` | Yes | Primary key of the plot thread |

**Returns:** `PlotThread | NotFoundResponse` — Full `PlotThread` record; `NotFoundResponse` if thread does not exist.

**Invocation reason:** Called when preparing to draft a chapter to load the current status, stakes, and summary of the plot threads active in that chapter.

**Gate status:** Gate-free.

**Tables touched:** Reads `plot_threads`.

---

## `list_plot_threads`

**Purpose:** List all plot threads with optional `thread_type` and/or `status` filters.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `thread_type` | `str \| None` | No | Filter by type — "main", "subplot", "backstory" |
| `status` | `str \| None` | No | Filter by status — "active", "resolved", "dormant" |

**Returns:** `list[PlotThread]` — All matching plot threads ordered by id. Returns empty list if no threads match.

**Invocation reason:** Called to audit active plot threads before starting a new chapter — ensures all active threads are consciously tracked and none are neglected.

**Gate status:** Gate-free.

**Tables touched:** Reads `plot_threads`.

---

## `upsert_plot_thread`

**Purpose:** Create a new plot thread or update an existing one. Does NOT touch `chapter_plot_threads`.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `plot_thread_id` | `int \| None` | Yes | Existing thread ID to update, or None to create |
| `name` | `str` | Yes | Plot thread name |
| `thread_type` | `str \| None` | No (default: `"main"`) | Type — "main", "subplot", "backstory" |
| `status` | `str \| None` | No (default: `"active"`) | Status — "active", "resolved", "dormant" |
| `opened_chapter_id` | `int \| None` | No | FK to chapters where thread opens |
| `closed_chapter_id` | `int \| None` | No | FK to chapters where thread closes |
| `parent_thread_id` | `int \| None` | No | FK to plot_threads for nested subplots |
| `summary` | `str \| None` | No | Narrative summary |
| `resolution` | `str \| None` | No | How the thread resolves |
| `stakes` | `str \| None` | No | Stakes involved |
| `notes` | `str \| None` | No | Free-form notes |
| `canon_status` | `str \| None` | No (default: `"draft"`) | Canon status — "draft", "canon", "cut" |

**Returns:** `PlotThread | ValidationFailure` — The created or updated `PlotThread`; `ValidationFailure` on DB error.

**Invocation reason:** Called to establish plot threads during outlining and update their status when resolved. Uses ON CONFLICT(id) to prevent duplicate rows in a table that has FK children.

**Gate status:** Gate-free.

**Tables touched:** Reads `plot_threads`. Writes `plot_threads`.

---

## `delete_plot_thread`

**Purpose:** Delete a plot thread by ID if no FK children reference it.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `plot_thread_id` | `int` | Yes | Primary key of the plot thread to delete |

**Returns:** `NotFoundResponse | ValidationFailure | dict` — `{"deleted": True, "id": plot_thread_id}` on success; `NotFoundResponse` if not found; `ValidationFailure` if FK constraints prevent deletion (chapter_plot_threads or subplot_touchpoint_log reference the thread).

**Invocation reason:** Called to remove a plot thread that was created in error or restructured out of the narrative — only safe when no chapter links or subplot touchpoints reference it.

**Gate status:** Gate-free.

**Tables touched:** Reads `plot_threads`. Writes `plot_threads`.

---

## `link_chapter_to_plot_thread`

**Purpose:** Link a chapter to a plot thread via the chapter_plot_threads junction table. Idempotent: updates thread_role and notes if the link already exists.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `chapter_id` | `int` | Yes | FK to chapters table (required) |
| `plot_thread_id` | `int` | Yes | FK to plot_threads table (required) |
| `thread_role` | `str` | No | Role of this chapter in the thread — e.g. "advance", "introduce", "resolve" (default: "advance") |
| `notes` | `str \| None` | No | Free-form notes about this chapter-thread association (optional) |

**Returns:** `ChapterPlotThread | NotFoundResponse | ValidationFailure` — The created or updated `ChapterPlotThread`; `NotFoundResponse` if chapter_id or plot_thread_id does not exist; `ValidationFailure` on DB error.

**Invocation reason:** Called during chapter planning to associate a chapter with the plot threads it advances — enables tracking of which chapters drive which threads across the narrative.

**Gate status:** Gate-free.

**Tables touched:** Reads `chapters`, `plot_threads`. Writes `chapter_plot_threads`.

---

## `unlink_chapter_from_plot_thread`

**Purpose:** Remove the link between a chapter and a plot thread. Idempotent: returns NotFoundResponse if the link does not exist.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `chapter_id` | `int` | Yes | FK to chapters table (required) |
| `plot_thread_id` | `int` | Yes | FK to plot_threads table (required) |

**Returns:** `NotFoundResponse | dict` — `{"unlinked": True, "chapter_id": chapter_id, "plot_thread_id": plot_thread_id}` on success; `NotFoundResponse` if the link does not exist.

**Invocation reason:** Called when a chapter's role in a plot thread is removed during restructuring — cleans up the junction table after plot changes.

**Gate status:** Gate-free.

**Tables touched:** Reads `chapter_plot_threads`. Writes `chapter_plot_threads`.

---

## `get_plot_threads_for_chapter`

**Purpose:** Get all plot thread associations for a chapter.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `chapter_id` | `int` | Yes | Primary key of the chapter to query |

**Returns:** `list[ChapterPlotThread]` — All `ChapterPlotThread` records for the chapter ordered by `plot_thread_id`. Returns an empty list if no associations exist.

**Invocation reason:** Called before drafting a chapter to confirm which plot threads it is responsible for advancing — ensures the agent has the full narrative context before writing.

**Gate status:** Gate-free.

**Tables touched:** Reads `chapter_plot_threads`.

---
