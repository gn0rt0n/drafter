---
created: 2026-03-09T17:04:25.175Z
title: Audit and add missing MCP CRUD operations for all schema tables
area: docs
files:
  - docs/schema.md
  - src/novel/tools/
---

## Problem

`docs/schema.md` documents many tables as "not writable via MCP" — meaning Claude can read data but cannot create or update records in those tables. This is an incomplete API: if Claude can't write to a table, it can't maintain that domain's data during a writing session.

Tables noted as read-only in schema.md need auditing to determine which ones genuinely should be writable via MCP and which are intentionally append-only or CLI-only.

## Solution

1. Audit `docs/schema.md` for all tables marked read-only or "not writable via MCP"
2. For each table, determine if a write/upsert MCP tool is warranted
3. Add missing `upsert_*` or `log_*` tools to the appropriate `src/novel/tools/*.py` domain files
4. Update schema.md to reflect corrected access patterns
5. Update requirements if new tools are added
