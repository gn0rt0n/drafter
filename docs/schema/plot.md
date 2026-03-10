[← Documentation Index](../README.md)

# Plot Schema

The Plot domain manages named narrative threads and their chapter-level coverage. The `chapter_plot_threads` junction table lives here (not in chapters.md) because plot threads are the primary entity — the junction exists to attach chapters to threads, mirroring how `arc_seven_point_beats` lives in structure.md because structure.py owns it.

> **Cross-domain FKs:** `plot_threads.opened_chapter_id` / `closed_chapter_id → chapters.id` (Chapters). `chapter_plot_threads.chapter_id → chapters.id` (Chapters). `subplot_touchpoint_log.chapter_id → chapters.id` (Chapters). All plot tools are gate-free.

## `plot_threads`

Named narrative threads with type, status, open/close chapters, and optional parent thread for subplot nesting. The self-referential `parent_thread_id` allows subplots to reference their parent thread.

| Field | Type | Description |
|-------|------|-------------|
| `id` | INTEGER PK | Primary key |
| `name` | TEXT | Thread name |
| `thread_type` | TEXT | Type: `main`, `subplot`, `backstory`, `mystery` (default: `main`) |
| `status` | TEXT | Status: `active`, `resolved`, `dormant`, `abandoned` (default: `active`) |
| `opened_chapter_id` | INTEGER FK | References `chapters.id` — chapter where thread opens (nullable) |
| `closed_chapter_id` | INTEGER FK | References `chapters.id` — chapter where thread closes (nullable) |
| `parent_thread_id` | INTEGER FK | References `plot_threads.id` — parent thread for subplots (nullable self-ref) |
| `summary` | TEXT | Narrative summary of the thread |
| `resolution` | TEXT | How the thread resolves |
| `stakes` | TEXT | What is at stake in this thread |
| `notes` | TEXT | Standard annotation field |
| `canon_status` | TEXT | Approval status (default: `draft`) |
| `created_at` | TEXT | Standard audit timestamp |
| `updated_at` | TEXT | Standard audit timestamp |

**Populated by:** `upsert_plot_thread` (plot domain).

---

## `chapter_plot_threads`

Junction table linking chapters to the plot threads active in them. Tracks the role each thread plays in a given chapter. Junction table — MCP tools in plot.py: `link_chapter_to_plot_thread`, `unlink_chapter_from_plot_thread`, `get_plot_threads_for_chapter`.

| Field | Type | Description |
|-------|------|-------------|
| `id` | INTEGER PK | Primary key |
| `chapter_id` | INTEGER FK | References `chapters.id` |
| `plot_thread_id` | INTEGER FK | References `plot_threads.id` (Plot domain) |
| `thread_role` | TEXT | How the thread appears in this chapter: `advance`, `introduce`, `resolve`, `cameo` (default: `advance`) |
| `notes` | TEXT | Standard annotation field |
| `created_at` | TEXT | Standard audit timestamp |

**Constraints:** `UNIQUE(chapter_id, plot_thread_id)`.

**Populated by:** `link_chapter_to_plot_thread` (plot.py), `unlink_chapter_from_plot_thread` (plot.py). Read via `get_plot_threads_for_chapter`.

---
