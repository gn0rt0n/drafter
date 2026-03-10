[← Documentation Index](../README.md)

# Gate Tools

Manages the architecture gate — the certification mechanism that blocks prose-phase tools until all 36 worldbuilding requirements are verified. Tools are gate-free themselves (they manage the gate, not use it).

**Gate status:** All tools in this domain are gate-free (gate tools manage the gate, they do not check it).

**6 tools**

## Index

| Tool Name | Gate | Description |
|-----------|------|-------------|
| `get_gate_status` | Free | Return the current gate certification status |
| `get_gate_checklist` | Free | Return all gate checklist items |
| `run_gate_audit` | Free | Execute all gate evidence queries and update checklist |
| `update_checklist_item` | Free | Manually override a gate checklist item |
| `certify_gate` | Free | Certify the gate if all checklist items pass |
| `delete_gate_checklist_item` | Free | Delete a gate checklist item by ID (admin cleanup) |

---

## `get_gate_status`

**Purpose:** Return the current certification status of the architecture gate.

**Parameters:** None

**Returns:** `dict | NotFoundResponse` — Dict with `gate_id`, `is_certified`, `certified_at`, `certified_by`, `blocking_item_count`; `NotFoundResponse` if the gate row (id=1) is missing.

**Invocation reason:** Called at the start of any session to determine whether the gate is certified — if not certified, prose-phase tools are blocked and the agent should focus on worldbuilding.

**Gate status:** Gate-free (gate tools are exempt from their own checks).

**Tables touched:** Reads `architecture_gate`, `gate_checklist_items`.

---

## `get_gate_checklist`

**Purpose:** Return all 36 checklist items for the architecture gate ordered by category and item_key.

**Parameters:** None

**Returns:** `list[GateChecklistItem]` — All checklist items ordered by `category, item_key`. Returns empty list if no items have been populated yet (run `run_gate_audit` to populate).

**Invocation reason:** Called to inspect the detailed breakdown of passing and failing gate items — identifies exactly which worldbuilding gaps remain before certification.

**Gate status:** Gate-free.

**Tables touched:** Reads `gate_checklist_items`.

---

## `run_gate_audit`

**Purpose:** Execute all 36 gate evidence queries, update `gate_checklist_items`, and return a `GateAuditReport`.

**Parameters:** None

**Returns:** `GateAuditReport | NotFoundResponse` — `GateAuditReport` with `total_items`, `passing_count`, `failing_count`, and full items list; `NotFoundResponse` if `architecture_gate id=1` is missing.

**Invocation reason:** Called after completing worldbuilding tasks to check whether the gate requirements are now satisfied. Does NOT certify the gate — call `certify_gate` separately after all items pass.

**Gate status:** Gate-free.

**Tables touched:** Reads all worldbuilding tables (36 SQL queries). Writes `gate_checklist_items`.

---

## `update_checklist_item`

**Purpose:** Manually override a gate checklist item's pass/fail state.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `item_key` | `str` | Yes | Unique key of the checklist item (e.g. "pop_characters") |
| `is_passing` | `bool` | Yes | Whether this item should be considered passing |
| `missing_count` | `int` | No (default: `0`) | Number of missing items (0 when is_passing=True) |
| `notes` | `str \| None` | No | Notes explaining the manual override |

**Returns:** `GateChecklistItem | NotFoundResponse` — The updated `GateChecklistItem`; `NotFoundResponse` if the item_key does not exist (run `run_gate_audit` first).

**Invocation reason:** Called when a gate item cannot be verified by SQL alone — allows human judgment to mark narrative completeness items as passing when the qualitative standard is met.

**Gate status:** Gate-free.

**Tables touched:** Reads `gate_checklist_items`. Writes `gate_checklist_items`.

---

## `certify_gate`

**Purpose:** Certify the architecture gate if all checklist items are passing. Does NOT re-run the audit.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `certified_by` | `str \| None` | No | Name/identifier of who is certifying (default: "system") |

**Returns:** `ArchitectureGate | ValidationFailure` — The updated `ArchitectureGate` with `is_certified=True`; `ValidationFailure` listing how many items are still failing.

**Invocation reason:** Called after `run_gate_audit` confirms all 36 items pass — locks the gate as certified and unblocks all prose-phase tools. Run `run_gate_audit` first, then `certify_gate`.

**Gate status:** Gate-free.

**Tables touched:** Reads `gate_checklist_items`. Writes `architecture_gate`.

---

## `delete_gate_checklist_item`

**Purpose:** Delete a gate checklist item by ID (admin cleanup). NOT gate-gated — this tool manages the gate itself.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `checklist_item_id` | `int` | Yes | Primary key of the gate checklist item to delete |

**Returns:** `NotFoundResponse | ValidationFailure | dict` — `{"deleted": True, "id": checklist_item_id}` on success; `NotFoundResponse` if not found; `ValidationFailure` if FK constraints prevent deletion.

**Invocation reason:** Called to remove stale or erroneous gate checklist items during gate administration — analogous to `update_checklist_item` in that it manages the gate rather than being subject to it.

**Gate status:** Gate-free.

**Tables touched:** Reads `gate_checklist_items`. Writes `gate_checklist_items`.

---
