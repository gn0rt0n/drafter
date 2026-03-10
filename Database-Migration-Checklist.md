# Database Migration Checklist — Mercy, Twice Given → Drafter

_Work through this top-to-bottom. Each layer depends on the previous one — don't skip ahead._

---

## How to Use This

- Check off each item as you complete it
- The **Tools** column lists the MCP tool calls to use
- Process order is driven by FK dependencies: a row must exist before anything can reference it
- `Pacing-Map.md` is too large to process in one pass — do it act-by-act (Acts 1, 2, 3 separately)

---

## Layer 1 — World Foundation
*No FK dependencies. Must go first.*

### Era
- [ ] `01-Story-Bible/World/Timeline.md` → `upsert_era`
  - Pull: era name, sequence order, date range

### Cultures
- [ ] `01-Story-Bible/World/Kalder.md` → `upsert_culture`
- [ ] `01-Story-Bible/World/Verath.md` → `upsert_culture`

### Locations
- [ ] `01-Story-Bible/World/Geography.md` → `upsert_location` (frontier, the Wall, cities, Verath temple, prison, all named places)

### Factions
- [ ] `01-Story-Bible/World/Kalder.md` → `upsert_faction` (Kalder state/government)
- [ ] `01-Story-Bible/World/Verath.md` → `upsert_faction` (Verath state/government)
- [ ] `01-Story-Bible/World/Military-Structure.md` → `upsert_faction` (military units, ranks)
- [ ] `01-Story-Bible/World/Religion.md` → `upsert_faction` (Servants of the Crucible)

### Book + Acts
- [ ] `02-Structure/Three-Act-Overview.md` → `upsert_book` (Mercy, Twice Given — standalone novel)
- [ ] `02-Structure/Three-Act-Overview.md` → `upsert_act` ×4 (Act 1, Act 2, Act 3, Epilogue)

### Magic System
- [ ] `01-Story-Bible/World/Supernatural-Constraints.md` → `upsert_magic_system_element`
- [ ] `01-Story-Bible/World/Religion.md` → `upsert_magic_system_element` (Crucible mechanics)

---

## Layer 2 — Characters
*Need era, culture, faction to exist.*

### Primary POV Characters
- [ ] `01-Story-Bible/Characters/Hael.md` → `upsert_character`
- [ ] `01-Story-Bible/Characters/Asper.md` → `upsert_character`
- [ ] `01-Story-Bible/Characters/Sabine.md` → `upsert_character`

### Deceased Characters (still need records as FK targets)
- [ ] `01-Story-Bible/Characters/Sera.md` → `upsert_character` (status: deceased)
- [ ] `01-Story-Bible/Characters/Emren.md` → `upsert_character` (status: deceased Ch 31)
- [ ] `01-Story-Bible/Characters/Maura.md` → `upsert_character` (status: deceased Ch 31)

### Supporting Cast
- [ ] `01-Story-Bible/Characters/Supporting-Cast.md` → `upsert_character` (secondary/minor characters — data is sparse)

### Character Enrichment + Voice Profiles
- [ ] `01-Story-Bible/Characters/Hael-Perception-Profile.md` → `upsert_character` (enrichment) + `upsert_voice_profile`
- [ ] `01-Story-Bible/Characters/Asper-Perception-Profile.md` → `upsert_character` (enrichment) + `upsert_voice_profile`
- [ ] `01-Story-Bible/Characters/Sabine-Perception-Profile.md` → `upsert_character` (enrichment) + `upsert_voice_profile` ×2 (pre-jump and post-jump)
- [ ] `02-Structure/Sabine-Voice-Continuity.md` → `upsert_voice_profile` (supplements Sabine perception profile — pre/post jump detail)
- [ ] `05-Style/Prose-Reference.md` → `upsert_voice_profile` (Hael and Asper voice data if present)

---

## Layer 3 — Chapters
*Need book_id, act_id, pov_character_id.*

### Base Pass — skeleton records for all 55 chapters
- [ ] `02-Structure/Chapter-Index.md` → `upsert_chapter` ×55
  - Pull: chapter number, title, POV character, word count target, act, status

### Enrichment Pass — structural and pacing detail
- [ ] `02-Structure/Pacing-Map.md` (Act 1, Ch 1–13) → `upsert_chapter` (structural function, hook notes, opening/closing state, notes)
- [ ] `02-Structure/Pacing-Map.md` (Act 2, Ch 14–38) → `upsert_chapter`
- [ ] `02-Structure/Pacing-Map.md` (Act 3 + Epilogue, Ch 39–55) → `upsert_chapter`

### Summary Pass
- [ ] `02-Structure/Story-Summary.md` → `upsert_chapter` ×55 (summary field per chapter)

### Chapter Obligations — scene beats become obligation records
- [ ] `02-Structure/Pacing-Map.md` (Act 1) → `upsert_chapter_obligation` (each Scene Beat bullet = one obligation)
- [ ] `02-Structure/Pacing-Map.md` (Act 2) → `upsert_chapter_obligation`
- [ ] `02-Structure/Pacing-Map.md` (Act 3 + Epilogue) → `upsert_chapter_obligation`

### Tension Measurements
- [ ] `02-Structure/Tension-Arc.md` → tension_measurements (Timeline tools — tension level per chapter)

---

## Layer 4 — Arcs + Story Structure
*Need character_id and chapter_id.*

### Character Arcs
- [ ] `02-Structure/Arc-Maps.md` → `upsert_arc` ×3 (one arc per POV character: Hael, Asper, Sabine)

### Arc 7-Point Beats (up to 21 records: 7 beats × 3 characters)
- [ ] `02-Structure/Arc-Maps.md` → `upsert_arc_beat` (Hael — all 7 beats)
- [ ] `02-Structure/Arc-Maps.md` → `upsert_arc_beat` (Asper — all 7 beats)
- [ ] `02-Structure/Arc-Maps.md` → `upsert_arc_beat` (Sabine — all 7 beats)

### Arc–Chapter Links
- [ ] `02-Structure/Arc-Maps.md` → `link_chapter_to_arc` (junction records)

### Story-Level 7-Point Structure
- [ ] `02-Structure/Three-Act-Overview.md` + `02-Structure/Arc-Maps.md` → `upsert_story_structure` (story-level beats mapped to chapters)

---

## Layer 5 — Relationships
*Need character_ids.*

### Relationship Records
- [ ] `01-Story-Bible/Characters/` (main character files) + `02-Structure/Story-Summary.md` → `upsert_character_relationship`
  - Hael ↔ Asper (friends → enemies)
  - Hael ↔ Sabine (antagonist → surrogate family)
  - Asper ↔ Sabine (father/daughter)
  - Hael ↔ Emren (father/son)
  - Hael ↔ Sera (husband/wife, deceased)
  - Asper ↔ Maura (husband/wife, deceased)

### Relationship Change Events
- [ ] `02-Structure/Information-State.md` → `upsert_relationship_change_event` (tracks when and how relationships shift by chapter)

---

## Layer 6 — Plot Threads
*Need chapter_ids.*

### Thematic Threads
- [ ] `01-Story-Bible/Themes/Mercy-vs-Order.md` → `upsert_plot_thread` (the central philosophical conflict as a tracked thread)

### Narrative Threads
- [ ] `02-Structure/Three-Act-Overview.md` + `02-Structure/Story-Summary.md` → `upsert_plot_thread`:
  - The Lie (Lie 1.0 and Lie 2.0 lifecycle)
  - The war escalation
  - Sabine's truth-discovery arc
  - The mercy thread (Sera's mercy → the midpoint rescue → Ch 52 climax)
- [ ] Same sources → `link_chapter_to_plot_thread` (chapter × thread junction records)

---

## Layer 7 — Timeline Events
*Need character_ids, chapter_ids.*

### Pre-Novel History
- [ ] `01-Story-Bible/World/Timeline.md` → `upsert_event` (historical events before Ch 1)

### Novel Events
- [ ] `02-Structure/Story-Summary.md` + `02-Structure/Information-State.md` → `upsert_event` + `upsert_event_participant`
  - Sera's death (Ch 8)
  - Hael's desertion (Ch 8)
  - Asper's arrest of Hael (Ch 9)
  - The Lie told to Emren (Ch 10)
  - Prison break (Ch 13)
  - Emren + Maura deaths (Ch 31)
  - The midpoint rescue — Hael saves unconscious Sabine (Ch 30–31)
  - Asper's atrocity + Lie 2.0 (Ch 32)
  - Exile (Ch 34)
  - The tent confrontation / climax (Ch 49–52)
  - Asper's death + confession (Ch 52)
- [ ] `02-Structure/Information-State.md` → `upsert_travel_segment` (character movements between locations)

---

## Layer 8 — Knowledge / Information State
*Need character_ids, chapter_ids.*

- [ ] `02-Structure/Information-State.md` → `upsert_reader_information_state` (reader knowledge vs. character knowledge per chapter)
- [ ] `02-Structure/Information-State.md` → `upsert_reader_reveal` (major revelation moments)
- [ ] `02-Structure/Information-State.md` → dramatic_irony_inventory
  - Key item: Hael knows he saved Sabine (Ch 30–31); Sabine does not; reader knows both

---

## Layer 9 — Foreshadowing + Canon
*Need chapter_ids.*

### Motifs
- [ ] `01-Story-Bible/Themes/Symbols-and-Motifs.md` → `upsert_motif` (each symbol/motif = one motif_registry record)

### Thematic Mirrors
- [ ] `01-Story-Bible/Themes/Thematic-Mirror-Map.md` → foreshadowing_registry (thematic_mirrors table)

### Planted Foreshadowing in Chapters
- [ ] `02-Structure/Pacing-Map.md` (Act 1) → `upsert_foreshadowing`
  - Key plants: farmer disagreement (Ch 1), Sera's cough (Ch 2), Hael's lie to Emren (Ch 5), Asper's "I make one exception for everyone" (Ch 7)
- [ ] `02-Structure/Pacing-Map.md` (Act 2) → `upsert_foreshadowing`
  - Key plant: Hael rescues unconscious Sabine — she never knows (Ch 30–31), scar on her left forearm
- [ ] `02-Structure/Pacing-Map.md` (Act 3 + Epilogue) → `upsert_foreshadowing` (payoffs)

### Canon Facts
- [ ] `02-Structure/Story-Summary.md` → `upsert_canon_fact` (deaths, lies told, confirmed knowledge states, irreversible events)

---

## Layer 10 — Publishing
*Mostly FK-independent — can be done anytime after Layer 1.*

- [ ] `02-Structure/Genre-Classification.md` → publishing asset metadata
- [ ] `08-Publishing/Query-Letter.md` → `upsert_publishing_asset`
- [ ] `08-Publishing/Synopsis.md` → `upsert_publishing_asset`
- [ ] `08-Publishing/Comps.md` → `upsert_publishing_asset`
- [ ] `08-Publishing/Submission-Tracker.md` → `upsert_submission_tracker`

---

## Documents to Skip (Process/Analytical Artifacts)

These don't produce DB rows — they are planning work product:

| File | Why Skip |
|------|----------|
| `02-Structure/Gap-Analysis.md` | Structural analysis, resolved by current chapter set |
| `02-Structure/Rules-Framework.md` | Constraint reference for planning, not story data |
| `02-Structure/Format-Decisions.md` | Decision log |
| `02-Structure/Authority-Protocol.md` | Process doc |
| `02-Structure/Transfer-Protocol.md` | Process doc |
| `02-Structure/POV-Distribution.md` | Fully covered by Chapter-Index + Pacing-Map |
| `02-Structure/Time-Jump-Bridge-Spec.md` | Consult alongside Pacing-Map for bridge chapters — not a separate pass |
| `01-Story-Bible/World/Opposition-Pair-Manifestations.md` | Analytical — informs plot thread framing but isn't itself a DB record |

---

## Notes

- **Pacing-Map.md** is the workhorse for Layers 2, 3, and 9. At 28k tokens it must be processed act-by-act.
- **Story-Summary.md** is the backstop for anything ambiguous — if a field is unclear from the dedicated source file, check here.
- **Supporting-Cast.md** is sparse (mostly template stubs for unnamed characters). Create placeholder records with what exists and fill in later.
- After completing Layer 4, run `get_gate_status` to see how many of the 36 gate checklist items are satisfied.
