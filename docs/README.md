# Drafter Documentation

Drafter is a Python MCP server + SQLite narrative database + CLI (`novel` command) for AI-assisted novel writing. It exposes 231 MCP tools across 18 domains, backed by 71 schema tables across 22 migrations.

Architecture: SQLite database (persistent narrative state) ← Python MCP server (FastMCP, async tools) ← Claude Code / any MCP client. Full architecture detail is in `project-overview/`.

---

## Tools Reference

| Domain | Tools | Gate | Reference |
|--------|-------|------|-----------|
| [Characters](tools/characters.md) | 19 | Free | tools/characters.md |
| [Relationships](tools/relationships.md) | 9 | Free | tools/relationships.md |
| [Chapters](tools/chapters.md) | 8 | Free | tools/chapters.md |
| [Scenes](tools/scenes.md) | 12 | Free | tools/scenes.md |
| [World](tools/world.md) | 33 | Free | tools/world.md |
| [Magic](tools/magic.md) | 14 | Free | tools/magic.md |
| [Plot](tools/plot.md) | 7 | Free | tools/plot.md |
| [Arcs](tools/arcs.md) | 15 | Free | tools/arcs.md |
| [Gate](tools/gate.md) | 6 | Free | tools/gate.md |
| [Names](tools/names.md) | 6 | Free | tools/names.md |
| [Structure](tools/structure.md) | 6 | Free | tools/structure.md |
| [Session](tools/session.md) | 16 | Gated | tools/session.md |
| [Timeline](tools/timeline.md) | 18 | Mixed | tools/timeline.md |
| [Canon](tools/canon.md) | 10 | Gated | tools/canon.md |
| [Knowledge](tools/knowledge.md) | 12 | Gated | tools/knowledge.md |
| [Foreshadowing](tools/foreshadowing.md) | 18 | Gated | tools/foreshadowing.md |
| [Voice](tools/voice.md) | 9 | Gated | tools/voice.md |
| [Publishing](tools/publishing.md) | 13 | Mixed | tools/publishing.md |

---

## Schema Reference

| Domain | Tables | Key Tables |
|--------|--------|------------|
| [Characters](schema/characters.md) | 6 | characters, character_knowledge, character_beliefs, character_locations |
| [Relationships](schema/relationships.md) | 3 | character_relationships, relationship_change_events, perception_profiles |
| [Chapters](schema/chapters.md) | 4 | chapters, chapter_structural_obligations, pacing_beats, tension_measurements |
| [Scenes](schema/scenes.md) | 2 | scenes, scene_character_goals |
| [World](schema/world.md) | 6 | cultures, factions, locations, artifacts, faction_political_states, object_states |
| [Magic](schema/magic.md) | 4 | magic_system_elements, practitioner_abilities, supernatural_elements, magic_use_log |
| [Plot](schema/plot.md) | 2 | plot_threads, chapter_plot_threads |
| [Arcs](schema/arcs.md) | 5 | character_arcs, chapter_character_arcs, arc_health_log, chekovs_gun_registry |
| [Gate](schema/gate.md) | 4 | architecture_gate*, gate_checklist_items, project_metrics_snapshots, pov_balance_snapshots |
| [Names](schema/names.md) | 1 | name_registry |
| [Structure](schema/structure.md) | 6 | eras, books, acts, story_structure, arc_seven_point_beats, schema_migrations* |
| [Session](schema/session.md) | 4 | session_logs, agent_run_log, open_questions, decisions_log |
| [Timeline](schema/timeline.md) | 5 | events, event_participants, event_artifacts, travel_segments, pov_chronological_position |
| [Canon](schema/canon.md) | 2 | canon_facts, continuity_issues |
| [Knowledge](schema/knowledge.md) | 4 | reader_information_states, reader_reveals, dramatic_irony_inventory, reader_experience_notes |
| [Foreshadowing](schema/foreshadowing.md) | 6 | foreshadowing_registry, prophecy_registry, motif_registry, motif_occurrences, thematic_mirrors |
| [Voice](schema/voice.md) | 3 | voice_profiles, voice_drift_log, supernatural_voice_guidelines |
| [Publishing](schema/publishing.md) | 4 | publishing_assets, submission_tracker, research_notes, documentation_tasks |

\* Intentionally read-only system table — see the schema file for justification.

---

## Quick Stats

- **Total MCP tools:** 231 (153 Free, 78 Gated)
- **Total schema tables:** 71 (69 with MCP write coverage, 2 intentionally read-only)
- **Migrations:** 22
- **Tool domains:** 18

---

## Error Contract

All MCP tools return structured data — no tool raises an uncaught exception.

| Response Type | When | Key Fields |
|---------------|------|------------|
| Normal return | Success | Tool-specific model |
| `NotFoundResponse` | Record not found | `not_found_message: str` |
| `ValidationFailure` | Invalid input / DB constraint | `is_valid: bool (False)`, `errors: list[str]` |
| `GateViolation` | Gate not certified (gated tools only) | `requires_action: str` |
