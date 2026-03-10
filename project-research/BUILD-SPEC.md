# Novel Plugin — Build Specification
## Authoritative Reference for Implementation
### Version 1.0 — Post-Architecture Review

---

## Purpose of This Document

This document is the **single authoritative reference** for building the novel-plugin system. It captures architectural decisions made after reviewing the PRD and agent roster, and supersedes the original PRD (`drafter-prd.md`) where they conflict.

**Open a new session?** Read this document first. It tells you what's been decided, what the final component inventory is, and which batch to work on next.

**Reference documents** (do not edit these for decisions — update this spec instead):
- `drafter-prd.md` — Original system design and build sequence
- `agent-roster.md` — Full agent definitions (all 40 original roles)
- `database-schema.md` — SQLite schema and migration files
- `mcp-tools.md` — Full MCP tool domain listing

---

## System Overview

Four integrated layers:

| Layer | Repo | Purpose |
|---|---|---|
| Claude Code Plugin (`novel-plugin/`) | `novel-plugin/` | Interface: agents, skills, commands, MCP config |
| Python MCP Server | `novel-tools/mcp/` | Engine: exposes SQLite as typed tool calls |
| SQLite Database | `your-novel/.db/` | Truth: all canonical story data |
| Python CLI (`novel`) | `novel-tools/novel/` | Operations: migrate, export, import, query, session, gate |

---

## Architectural Decisions

### Decision 1: Agents vs. Skills Split (Revised)

The original PRD specified 20 agents and 20 skills. After review, **6 skills were converted to agents** because they represent deliberate analytical sessions, not passive monitoring.

**Framework for the split:**
- **Skills** = watchdogs. They monitor passively, fire without being asked, catch issues during active work.
- **Agents** = consultants. You sit down with them for a structured session with a defined output.

**The 6 conversions:**

| Original Skill | Now Agent | Reason |
|---|---|---|
| `pacing-tension-analyst` | ✅ Agent | Pacing audit is a deliberate session, not passive monitoring. "Chapter rhythm" appears in general discussion — high over-fire risk. |
| `foreshadowing-tracker` | ✅ Agent | Planted/payoff audits produce structured reports. "Foreshadowing" appears in conversation constantly — would over-fire badly. |
| `symbolism-motif-tracker` | ✅ Agent | Deep analytical work requiring full story context. Not passive monitoring. |
| `thematic-architecture` | ✅ Agent | Structural thinking session with a deliverable. Should not watch passively. |
| `information-state-tracker` | ✅ Agent | Requires loading full reader-state context. This is session work. |
| `relationship-dynamics` | ✅ Agent | Character relationship deep-dives are deliberate, not ambient. |

**Final inventory: 26 agents, 14 skills.**

---

### Decision 2: Skill Co-Activation Strategy

At 20 skills, a single complex prompt (e.g. "write the opening scene for Chapter 12") could trigger 7+ skills simultaneously — context bloat, conflicting guidance, degraded output.

**Two-part solution:**

**Part 1 — Phase gating in every skill description.**
Every skill description must explicitly state which phases it activates in and what it does NOT activate on.

```
# Bad:
"Activates when working with scene settings, atmosphere, and mood"

# Good:
"Activates during Phase 5 prose drafting when establishing scene
settings, sensory details, or atmosphere — NOT during architecture
planning, structural review, or general chapter discussion"
```

**Part 2 — Narrow trigger phrases.**
Skill descriptions are tested with negative cases (should NOT trigger) as well as positive. Use `/skill-creator` eval loop to verify.

Required eval test structure for each skill:
- 2–3 "should trigger" cases
- 2–3 "should NOT trigger" cases (adjacent topics that should not activate this skill)

---

### Decision 3: Gate Enforcement Is Instruction-Based

The architecture gate (prose-phase skills refuse without certification) is enforced by instructions in skill SKILL.md files, backed by an MCP tool call (`get_gate_status()`). This is **not a hard technical barrier** — it relies on well-written skill instructions.

Implication: the `prose-writer` SKILL.md and its `references/gate-protocol.md` are the most critical files in the entire plugin. They must be written last (after gate is understood), and they must be unambiguous.

---

### Decision 4: Agent Scope Discipline

All 26 agents have access to all MCP tools. Scope control lives in the agent's markdown file. Every agent file must explicitly specify:
- **Primary read tables** — where it loads context from
- **Authorized writes** — what it's allowed to create or update
- **Off-limits** — tables it should treat as read-only

This prevents an Arc Tracker from accidentally writing to `characters`, a Canon Keeper from modifying `chapter_plans`, etc.

---

### Decision 5: MCP Path Configuration

The plugin's `.mcp.json` stores placeholder paths. Actual paths are set per-machine in the novel project's `.claude/settings.json`. This must be documented as a one-time setup step — and a `novel install` CLI subcommand should write these paths automatically to reduce manual error.

---

### Decision 6: Skills Built with `/skill-creator`

All 14 skills are built and evaluated using the `skill-creator` plugin, not written manually. The eval loop verifies triggering reliability before a skill is considered complete.

Build order for skills (priority order from PRD, revised to exclude converted agents):

**Tier 1 (build first — other content depends on these):**
1. `continuity-editor`
2. `timeline-manager`
3. `prose-writer`
4. `character-voice-auditor`
5. `names-linguistics`
6. `lore-keeper`

**Tier 2:**
7. `dialogue-specialist`
8. `perception-profiles`
9. `sensory-atmosphere`
10. `supernatural-voice`
11. `battle-action-coordinator`
12. `chapter-hook-specialist`
13. `line-editor`
14. `copy-editor`

---

## Final Component Inventory

### Agents (26 total)

**Original 20 architects + editors** (unchanged from PRD):
`story-architect`, `plot-systems-engineer`, `subplot-coordinator`, `chapter-architect`, `scene-builder`, `arc-tracker`, `pov-manager`, `character-architect`, `world-architect`, `magic-system-engineer`, `political-systems-analyst`, `canon-keeper`, `developmental-editor`, `reader-experience-simulator`, `architecture-completeness-auditor`, `session-continuity-manager`, `project-manager`, `publishing-preparation-agent`, `genre-analyst`, `research-agent`

**6 converted from skills:**
`pacing-tension-analyst`, `foreshadowing-tracker`, `symbolism-motif-tracker`, `thematic-architecture`, `information-state-tracker`, `relationship-dynamics`

### Skills (14 total)

All phase-gated. All built and evaluated with `/skill-creator`.

`continuity-editor`, `timeline-manager`, `character-voice-auditor`, `names-linguistics`, `lore-keeper`, `prose-writer`, `dialogue-specialist`, `perception-profiles`, `sensory-atmosphere`, `supernatural-voice`, `battle-action-coordinator`, `chapter-hook-specialist`, `line-editor`, `copy-editor`

### Slash Commands (9 total, unchanged from PRD)

`/novel:session-start`, `/novel:session-close`, `/novel:gate-check`, `/novel:gate-status`, `/novel:pov-balance`, `/novel:arc-health`, `/novel:thread-gaps`, `/novel:export-chapter`, `/novel:export-all`

### MCP Server (1)

`novel` server via `uv run`. 14 tool domains, ~80 tools. See `mcp-tools.md`.

---

## Build Sequence


| Batch | Scope | Done When |
|---|---|---|
| **1 — Plugin Scaffold** | Directory structure, `plugin.json`, `.mcp.json`, README, 9 slash commands | Plugin loads in Claude Code; MCP tools accessible; commands execute |
| **2 — Agents Batch 1** | 13 architecture-phase agents (Phases 1–3): Story Architect through Canon Keeper + 3 converted analytical agents | All agents invokable; MCP tools load correctly; scope boundaries specified |
| **3 — Agents Batch 2** | 13 remaining agents: Phase 4 gate agents, ongoing agents, Phase 7 agents + 3 remaining converted agents | All agents invokable; gate agents produce correct certification/gap report format |
| **4 — Skills Tier 1** | 6 priority skills with eval loop | All 6 skills trigger reliably on positive cases; do NOT trigger on negative cases; phase gating verified |
| **5 — Skills Tier 2** | 8 remaining skills with eval loop | Same verification standard as Tier 1 |
| **6 — Gate + Integration** | Populate 33-item gate checklist, run end-to-end test, verify prose-phase skill enforcement | `/novel:gate-check` produces accurate gap report; `prose-writer` skill refuses without certification; full rebuild works on clean machine |

---

## Known Risks

| Risk | Mitigation |
|---|---|
| Skill over-activation | Phase gating + narrow trigger phrases + `/skill-creator` eval on negative cases |
| Agent scope bleed | Explicit read/write/off-limits in every agent file |
| Gate as soft enforcement | `prose-writer` SKILL.md and `references/gate-protocol.md` written last, reviewed carefully |
| MCP path config per machine | `novel install` command automates path writing |
| 26 agent file quality | Use `agent-creator` for all agent system prompts; budget time for iteration |
| Context bloat during prose | Phase-gated skills + converted analytical agents = fewer simultaneous activations |

---


---

*Last updated: 2026-03-09 — Post-architecture review session*
