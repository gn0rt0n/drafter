[← Documentation Index](../README.md)

# Names Schema

The Names domain provides the name registry — a global catalog of every proper noun used in the novel. Used to check for duplicates and cultural consistency before committing to a name. Name tools are gate-free because naming is part of worldbuilding that occurs before gate certification.

> **Cross-domain FKs:** `name_registry.culture_id → cultures.id` (World). `name_registry.introduced_chapter_id → chapters.id` (Chapters).

## `name_registry`

Registry of every proper noun (character names, place names, object names) used in the novel. Used to check for duplicates and cultural consistency before committing to a name. The `name` column is UNIQUE.

| Field | Type | Description |
|-------|------|-------------|
| `id` | INTEGER PK | Primary key |
| `name` | TEXT | The registered name — UNIQUE |
| `entity_type` | TEXT | Type of entity: `character`, `location`, `artifact`, `faction`, etc. (default: `character`) |
| `culture_id` | INTEGER FK | References `cultures.id` — which culture this name belongs to (nullable) |
| `linguistic_notes` | TEXT | Pronunciation, etymology, or linguistic notes (nullable) |
| `introduced_chapter_id` | INTEGER FK | References `chapters.id` — when this name first appears (nullable) |
| `notes` | TEXT | Standard annotation field |
| `created_at` | TEXT | Standard audit timestamp |

**Constraints:** `UNIQUE(name)`.

**Populated by:** `register_name` (names domain), `upsert_name_registry_entry` (names.py), `delete_name_registry_entry` (names.py). Gate-free — name tools work during the worldbuilding phase without requiring gate certification.

---
