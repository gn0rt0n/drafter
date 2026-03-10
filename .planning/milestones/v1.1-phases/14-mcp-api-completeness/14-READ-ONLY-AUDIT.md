# Phase 14 — Read-Only Table Audit

Phase 14 goal: Every schema table in the drafter SQLite database either has at least one MCP write tool, or is explicitly documented here as intentionally read-only with justification.

Total schema tables: 71
Tables with MCP write tools: 69
Intentionally read-only tables: 2 (documented below)

## Intentionally Read-Only Tables

### schema_migrations

**Justification:** Managed exclusively by the migration runner (`novel db migrate` CLI command). This table records which SQL migration files have been applied. Writing to it outside the migration runner would corrupt the migration state and could cause destructive re-runs or skipped migrations. No MCP write tool is provided. Read access is also not exposed via MCP — migration state is an internal system concern.

### architecture_gate

**Justification:** Managed exclusively through the `certify_gate` tool flow. The gate system enforces narrative quality gates by controlling when Claude Code may advance to the next chapter. The `architecture_gate` table stores gate definitions and status; these are written only by `certify_gate` as part of the structured certification process. Exposing a direct write tool would bypass the gate enforcement mechanism that the system is designed to provide. Gate checklist items (`gate_checklist_items`) DO have write coverage via `delete_gate_checklist_item` in gate.py — only the parent `architecture_gate` table is read-only.

## Coverage Summary

All 69 remaining tables (non-system) have at least one MCP write tool as of Phase 14 completion. See 14-RESEARCH.md for the full per-table audit that guided Phase 14 planning.
