# Requirements: Drafter

**Defined:** 2026-03-09
**Core Value:** Claude Code can query and update all story data through typed MCP tool calls — no raw SQL, no markdown parsing — enabling consistent AI collaboration at novel scale.

## v1.1 Requirements

### Tech Debt

- [x] **DEBT-01**: Gate count displays "36 items" in all output — gate.py, cli.py corrected
- [x] **DEBT-02**: `novel db seed gate-ready` CLI help text uses underscore (gate_ready, not gate-ready)
- [x] **DEBT-03**: docs/README.md migration description is accurate (no false auto-apply claim)
- [x] **DEBT-04**: docs/README.md export command name is correct
- [x] **DEBT-05**: docs/README.md GateViolation type name is correct
- [x] **DEBT-06**: docs/README.md table names are correct
- [x] **DEBT-07**: pydantic declared as direct dependency in pyproject.toml
- [x] **DEBT-08**: gate audit and certify are consistent — both check/report 36 items

### MCP API

- [x] **MCP-01**: Every schema table either has an MCP write tool, or is documented as intentionally read-only with justification
- [x] **MCP-02**: New write tools implement the established error contract (null for not-found, is_valid: false for validation failures, requires_action for gate violations)

### Documentation

- [ ] **DOCS-01**: docs/mcp-tools.md updated to reflect newly added write tools from MCP phase, then split into per-domain files
- [ ] **DOCS-02**: docs/schema.md updated to reflect read-only justifications and any new write tools from MCP phase, then split into per-domain files
- [ ] **DOCS-03**: Master index file (docs/README.md or docs/index.md) links to all per-domain doc files

## Out of Scope

| Feature | Reason |
|---------|--------|
| Plugin integration (novel-plugin/) | Separate repo, separate milestone |
| New narrative domains or schema tables | v1.0 schema is complete; additions are future scope |
| Web UI or API layer | CLI + MCP only by design |
| Performance optimization | No perf issues reported; premature |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| DEBT-01 | Phase 13 | Complete |
| DEBT-02 | Phase 13 | Complete |
| DEBT-03 | Phase 13 | Complete |
| DEBT-04 | Phase 13 | Complete |
| DEBT-05 | Phase 13 | Complete |
| DEBT-06 | Phase 13 | Complete |
| DEBT-07 | Phase 13 | Complete |
| DEBT-08 | Phase 13 | Complete |
| MCP-01 | Phase 14 | Complete |
| MCP-02 | Phase 14 | Complete |
| DOCS-01 | Phase 15 | Pending |
| DOCS-02 | Phase 15 | Pending |
| DOCS-03 | Phase 15 | Pending |

**Coverage:**
- v1.1 requirements: 13 total
- Mapped to phases: 13
- Unmapped: 0 ✓

---
*Requirements defined: 2026-03-09*
*Last updated: 2026-03-09 — traceability mapped to Phases 13–15*
