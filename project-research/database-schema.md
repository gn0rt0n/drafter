# Complete Narrative Database Schema
## Epic Fantasy Novel — Full Agent Ecosystem

---

## Architecture Overview

### Database as Authoritative Source

The database is the single source of truth. Markdown files are generated outputs — human-readable representations of database state, not editable source files. When you or an agent updates information, the change goes into the database first. Markdown is regenerated from the database on demand.

This means:
- No conflicting versions between a markdown file and "what's actually true"
- Every agent queries the database instead of parsing text
- Consistency is enforced by FK constraints and not by discipline
- Every fact is traceable to a source chapter, a decision, and a timestamp

### Recommended Stack
SQLite with an MCP

### The Markdown Sync Model

```
Database (authoritative)
    ↓  artisan novel:export
Markdown files (generated, read-only)
    ↓  Claude Code loads as context
Agents read structured data + prose context
    ↓  agent produces updates
Database updated via API or CLI
    ↓  artisan novel:export (selective)
Markdown regenerated for changed records
```

Agents never write directly to markdown files. They write to the database. Markdown regeneration is a separate step you control.

---

## Modeling Principles

These extend the sample schema principles for this specific implementation:

1. Every entity has a `canon_status`: `draft`, `approved`, `provisional`, `deprecated`
2. Every entity has `created_at`, `updated_at`, and `reviewed_at` timestamps
3. State-over-time tables use `chapter_id` as the temporal anchor — not calendar dates — because chapters are the unit of narrative time
4. Agent writes are logged in `agent_run_log` for full auditability
5. Soft deletes everywhere — nothing is hard-deleted during active development
6. `notes` text field on every table for freeform agent or author annotation
7. `source_file` on every entity for traceability back to the originating markdown document during initial import

---

## Section 1: Core Entity Tables

These are the stable nouns of your story world. They change only when worldbuilding decisions change, not with every chapter.

---

### `books`
```sql
id                  bigint PK
title               varchar
series_order        int
word_count_target   int
actual_word_count   int  -- computed/cached
status              enum(planning, architecting, drafting, revising, complete)
notes               text
canon_status        enum(draft, approved)
created_at          timestamp
updated_at          timestamp
```

---

### `acts`
```sql
id                  bigint PK
book_id             bigint FK -> books.id
act_number          int
name                varchar
purpose             text
word_count_target   int
start_chapter_id    bigint FK -> chapters.id nullable
end_chapter_id      bigint FK -> chapters.id nullable
structural_notes    text
canon_status        enum
created_at          timestamp
updated_at          timestamp
```

---

### `chapters`
```sql
id                      bigint PK
book_id                 bigint FK -> books.id
act_id                  bigint FK -> acts.id
chapter_number          int
title                   varchar
pov_character_id        bigint FK -> characters.id nullable
word_count_target       int
actual_word_count       int
status                  enum(planned, outlined, architected, approved, drafted, revised, final)
summary                 text
opening_state           text    -- world/character state entering chapter
closing_state           text    -- world/character state exiting chapter
opening_hook_note       text
closing_hook_note       text
hook_strength_rating    tinyint -- 1-5, set by Chapter Hook Specialist
time_marker             varchar -- in-world time reference ("Day 3 of the siege")
elapsed_days_from_start int     -- Timeline Manager maintains this
structural_function     text    -- what this chapter must accomplish architecturally
source_file             varchar
notes                   text
canon_status            enum
created_at              timestamp
updated_at              timestamp
reviewed_at             timestamp
```

---

### `scenes`
```sql
id                      bigint PK
chapter_id              bigint FK -> chapters.id
scene_number            int
location_id             bigint FK -> locations.id nullable
time_marker             varchar
summary                 text
scene_type              enum(action, dialogue, revelation, introspection, transition,
                              confrontation, ritual, travel, battle, political)
dramatic_question       text    -- Scene Builder: what is at stake in this scene
scene_goal              text    -- what the POV character wants
obstacle                text    -- what prevents immediate achievement
turn                    text    -- the moment the scene pivots
consequence             text    -- what changes by end of scene
emotional_function      text    -- what the reader should feel
narrative_functions     json    -- array: ['advances_plot','develops_character','delivers_exposition']
word_count_target       int
status                  enum(planned, constructed, approved, drafted, revised, final)
notes                   text
canon_status            enum
created_at              timestamp
updated_at              timestamp
```

---

### `characters`
```sql
id                      bigint PK
slug                    varchar unique
name                    varchar
aliases                 json
type                    enum(major, minor, background, historical, mentioned)
pov_status              enum(active, candidate, none, removed)
faction_id              bigint FK -> factions.id nullable
culture_id              bigint FK -> cultures.id nullable
birth_era_id            bigint FK -> eras.id nullable
status                  enum(alive, dead, missing, unknown, historical)
public_summary          text    -- what most people know about them
private_summary         text    -- who they really are
physical_description    text
core_wound              text    -- the formative damage that drives them
core_desire             text    -- what they fundamentally want
core_fear               text    -- what they fundamentally fear
misbelief               text    -- the false belief they carry into the story
arc_start_state         text    -- who they are at page 1
arc_mid_state           text    -- who they are at the midpoint
arc_end_state           text    -- who they are at the end (planned)
actual_arc_end_state    text    -- who they actually became (filled during revision)
voice_summary           text    -- brief voice fingerprint for quick reference
notes                   text
source_file             varchar
canon_status            enum
created_at              timestamp
updated_at              timestamp
```

---

### `locations`
```sql
id                          bigint PK
slug                        varchar unique
name                        varchar
type                        enum(continent, region, kingdom, city, fortress, village,
                                  ruin, wildlands, structure, geographic_feature)
parent_location_id          bigint FK -> locations.id nullable  -- hierarchical
culture_id                  bigint FK -> cultures.id nullable
political_owner_faction_id  bigint FK -> factions.id nullable
terrain_type                varchar
climate_type                varchar
description                 text
sensory_profile             text    -- smell, sound, light quality, texture
strategic_value             text
travel_days_from_capital    int nullable
notes                       text
source_file                 varchar
canon_status                enum
created_at                  timestamp
updated_at                  timestamp
```

---

### `factions`
```sql
id                      bigint PK
name                    varchar
slug                    varchar unique
type                    enum(kingdom, order, guild, clan, cult, military, house,
                              religion, merchant, rebel, supernatural)
leader_character_id     bigint FK -> characters.id nullable
base_location_id        bigint FK -> locations.id nullable
public_goal             text
hidden_goal             text
resources_summary       text
military_strength       enum(none, minimal, moderate, strong, dominant)
notes                   text
source_file             varchar
canon_status            enum
created_at              timestamp
updated_at              timestamp
```

---

### `cultures`
```sql
id                          bigint PK
name                        varchar
region_id                   bigint FK -> locations.id nullable
values_summary              text
taboos_summary              text
naming_style                text        -- phoneme patterns, conventions
naming_examples             json        -- array of example names
religion_summary            text
social_structure_summary    text
gender_roles_summary        text
economic_basis              text
attitude_toward_outsiders   text
attitude_toward_magic       text
notes                       text
source_file                 varchar
canon_status                enum
created_at                  timestamp
updated_at                  timestamp
```

---

### `artifacts`
```sql
id                          bigint PK
name                        varchar
slug                        varchar unique
type                        varchar
origin_era_id               bigint FK -> eras.id nullable
current_holder_character_id bigint FK -> characters.id nullable
current_location_id         bigint FK -> locations.id nullable
public_description          text
true_nature                 text
capabilities                text
limitations                 text
risk_profile                text
secret_level                enum(public, known_to_few, secret, classified)
notes                       text
source_file                 varchar
canon_status                enum
created_at                  timestamp
updated_at                  timestamp
```

---

### `magic_system_elements`
```sql
id                      bigint PK
name                    varchar
category                enum(law, cost, force, rite, school, corruption,
                              limitation, edge_case, exception)
summary                 text
public_understanding    text    -- what in-world characters believe
true_rule               text    -- the actual rule
failure_mode            text    -- what happens when misused or violated
interaction_notes       text    -- how this element interacts with others
introduced_chapter_id   bigint FK -> chapters.id nullable
notes                   text
source_file             varchar
canon_status            enum
created_at              timestamp
updated_at              timestamp
```

---

### `supernatural_elements`
```sql
-- Broader than magic_system_elements
-- Covers divine laws, cosmic constraints, entity rules, spiritual mechanics
-- Magic System Engineer handles magic_system_elements
-- This table handles anything beyond character-level magic use
id                      bigint PK
name                    varchar
category                enum(divine_law, cosmic_rule, entity_constraint,
                              spiritual_mechanic, prophecy_mechanism, death_rule)
summary                 text
scope                   text    -- what/who does this apply to
known_exceptions        text
violation_consequence   text
introduced_chapter_id   bigint FK -> chapters.id nullable
notes                   text
source_file             varchar
canon_status            enum
created_at              timestamp
updated_at              timestamp
```

---

### `eras`
```sql
id                  bigint PK
name                varchar
sequence_order      int
date_start          varchar     -- in-world calendar notation
date_end            varchar
summary             text
certainty_level     enum(established, estimated, mythological, unknown)
notes               text
canon_status        enum
created_at          timestamp
updated_at          timestamp
```

---

## Section 2: Character State Tables

These track character state over time — not who a character is, but what they know, believe, feel, and where they are at any given point in the story.

---

### `character_relationships`
```sql
-- The most significant gap in the sample schema
-- Tracks every significant relationship between two characters
id                          bigint PK
character_a_id              bigint FK -> characters.id
character_b_id              bigint FK -> characters.id
relationship_type           enum(ally, enemy, mentor, student, lover, former_lover,
                                  family, rival, stranger, complicated, unknown_to_one)
relationship_status         enum(warm, neutral, cold, hostile, broken, secret, deceased_party)
first_meeting_event_id      bigint FK -> events.id nullable
current_dynamic             text    -- one-sentence current state
character_a_view_of_b       text    -- how A sees B (may differ from reality)
character_b_view_of_a       text    -- how B sees A
known_asymmetry             text    -- what one knows that the other doesn't
last_interaction_chapter_id bigint FK -> chapters.id nullable
notes                       text
canon_status                enum
created_at                  timestamp
updated_at                  timestamp
UNIQUE(character_a_id, character_b_id)  -- enforce one record per pair
```

---

### `relationship_change_events`
```sql
-- Log of every significant relationship shift
id                          bigint PK
relationship_id             bigint FK -> character_relationships.id
chapter_id                  bigint FK -> chapters.id
change_summary              text
previous_status             varchar
new_status                  varchar
cause_event_id              bigint FK -> events.id nullable
notes                       text
created_at                  timestamp
```

---

### `perception_profiles`
```sql
-- How character A perceives character B
-- Distinct from relationships (which track mutual status)
-- This tracks the constructed image each character has of another
id                          bigint PK
perceiver_character_id      bigint FK -> characters.id
perceived_character_id      bigint FK -> characters.id
perceived_name_used         varchar     -- what name/title perceiver uses
perceived_role              text        -- how perceiver categorizes perceived
perceived_threat_level      enum(none, low, moderate, high, critical)
perceived_trustworthiness   enum(trusted, neutral, suspect, untrustworthy, unknown)
perceived_motivations       text        -- what perceiver thinks drives perceived
perceived_capabilities      text        -- what perceiver thinks perceived can do
key_misconceptions          text        -- important things perceiver has wrong
perception_formed_chapter   bigint FK -> chapters.id nullable
last_updated_chapter        bigint FK -> chapters.id nullable
accuracy_note               text        -- author note on how wrong/right this is
notes                       text
canon_status                enum
created_at                  timestamp
updated_at                  timestamp
```

---

### `character_knowledge`
```sql
id                      bigint PK
character_id            bigint FK -> characters.id
knowledge_item          text
category                enum(fact, location, person, plan, secret, history, magic, political)
learned_in_event_id     bigint FK -> events.id nullable
learned_in_chapter_id   bigint FK -> chapters.id nullable
certainty_level         enum(certain, probable, suspected, rumored, false_belief)
source_character_id     bigint FK -> characters.id nullable  -- who told them
status                  enum(current, forgotten, disproven, irrelevant)
notes                   text
created_at              timestamp
updated_at              timestamp
```

---

### `character_beliefs`
```sql
id                      bigint PK
character_id            bigint FK -> characters.id
belief_statement        text
belief_type             enum(assumption, ideology, rumor, falsehood, superstition,
                              misinterpretation, propaganda)
formed_in_chapter_id    bigint FK -> chapters.id nullable
truth_status            enum(true, false, partially_true, unknown, complicated)
truth_revealed_chapter  bigint FK -> chapters.id nullable
notes                   text
created_at              timestamp
updated_at              timestamp
```

---

### `character_locations`
```sql
-- Where each character is, chapter by chapter
id              bigint PK
character_id    bigint FK -> characters.id
location_id     bigint FK -> locations.id
chapter_id      bigint FK -> chapters.id
event_id        bigint FK -> events.id nullable
entry_type      enum(arrives, present, departs, referenced_absent, unknown)
notes           text
created_at      timestamp
```

---

### `injury_states`
```sql
id                  bigint PK
character_id        bigint FK -> characters.id
chapter_id          bigint FK -> chapters.id  -- chapter injury was sustained
injury_description  text
severity            enum(minor, moderate, serious, critical, permanent)
body_part           varchar
functional_effect   text    -- what this prevents or impairs
healing_status      enum(fresh, healing, healed, permanent, worsened)
expected_heal_chapter bigint FK -> chapters.id nullable
notes               text
created_at          timestamp
updated_at          timestamp
```

---

### `title_states`
```sql
id                  bigint PK
character_id        bigint FK -> characters.id
title_name          varchar
faction_id          bigint FK -> factions.id nullable
status              enum(held, lost, contested, claimed, historical)
start_event_id      bigint FK -> events.id nullable
end_event_id        bigint FK -> events.id nullable
notes               text
created_at          timestamp
updated_at          timestamp
```

---

### `voice_profiles`
```sql
-- Character Voice Auditor maintains this
id                          bigint PK
character_id                bigint FK -> characters.id
vocabulary_range            enum(limited, working, educated, elevated, archaic)
sentence_structure_notes    text    -- short/clipped vs. long/flowing, etc.
verbal_tics                 json    -- array of specific patterns or phrases
topics_avoided              text
emotion_expression_style    enum(direct, indirect, deflective, performative, suppressed)
humor_register              enum(none, dry, dark, self_deprecating, warm, absent)
register_notes              text    -- formal/informal contexts
voice_evolution_notes       text    -- how voice should change over arc
reference_chapters          json    -- array of chapter_ids for best voice samples
created_by_agent            varchar
notes                       text
canon_status                enum
created_at                  timestamp
updated_at                  timestamp
```

---

### `voice_drift_log`
```sql
id                  bigint PK
character_id        bigint FK -> characters.id
chapter_id          bigint FK -> chapters.id
scene_id            bigint FK -> scenes.id nullable
drift_description   text
example_text        text    -- the offending line or passage
severity            enum(minor, moderate, significant)
resolution_status   enum(open, resolved, accepted)
resolution_notes    text
detected_by_agent   varchar
created_at          timestamp
updated_at          timestamp
```

---

## Section 3: Plot and Arc Tables

---

### `plot_threads`
```sql
id                          bigint PK
name                        varchar
slug                        varchar unique
category                    enum(main_plot, political, military, personal, mystery,
                                  magical, relational, thematic, supernatural)
is_subplot                  boolean default false
summary                     text
stakes_summary              text
start_chapter_id            bigint FK -> chapters.id nullable
expected_payoff_chapter_id  bigint FK -> chapters.id nullable
actual_payoff_chapter_id    bigint FK -> chapters.id nullable
current_status              enum(planned, introduced, active, dormant, approaching_resolution,
                                  resolved, broken, abandoned)
parent_thread_id            bigint FK -> plot_threads.id nullable  -- for nested subplots
notes                       text
source_file                 varchar
canon_status                enum
created_at                  timestamp
updated_at                  timestamp
```

---

### `chapter_plot_threads`
```sql
-- Pivot: which plot threads appear in which chapters
chapter_id      bigint FK -> chapters.id
plot_thread_id  bigint FK -> plot_threads.id
role            enum(introduces, advances, complicates, delays, revisits, resolves, references)
strength        enum(minor, moderate, major, dominant)
notes           text
PRIMARY KEY (chapter_id, plot_thread_id)
```

---

### `chapter_structural_obligations`
```sql
-- What each chapter is required to accomplish architecturally
-- Chapter Architect writes this; Architecture Completeness Auditor checks it
id                  bigint PK
chapter_id          bigint FK -> chapters.id
obligation_type     enum(subplot_touchpoint, arc_beat, plot_advancement,
                          revelation, setup, payoff, character_introduction,
                          world_establishment, thematic_beat)
reference_id        bigint nullable     -- FK to the relevant plot_thread, character_arc, etc.
reference_type      varchar nullable    -- 'plot_thread', 'character_arc', 'foreshadowing', etc.
description         text
is_fulfilled        boolean default false
fulfillment_notes   text
created_at          timestamp
updated_at          timestamp
```

---

### `character_arcs`
```sql
id                  bigint PK
character_id        bigint FK -> characters.id
arc_name            varchar
arc_type            enum(moral, emotional, political, spiritual, corruption,
                          redemption, disillusionment, awakening, fall, survival)
starting_state      text
midpoint_shift      text    -- what changes at the structural midpoint
desired_end_state   text    -- planned resolution
actual_end_state    text    -- filled during revision
status              enum(planned, in_progress, at_midpoint, approaching_end, complete, stalled)
arc_health_rating   tinyint -- 1-5, maintained by Arc Tracker
notes               text
source_file         varchar
canon_status        enum
created_at          timestamp
updated_at          timestamp
```

---

### `chapter_character_arcs`
```sql
chapter_id          bigint FK -> chapters.id
character_arc_id    bigint FK -> character_arcs.id
role                enum(reinforces, pressures, regresses, transforms, resolves,
                          introduces, tests, reveals)
notes               text
PRIMARY KEY (chapter_id, character_arc_id)
```

---

### `arc_health_log`
```sql
-- Arc Tracker writes periodic health assessments
id                      bigint PK
character_arc_id        bigint FK -> character_arcs.id
assessed_through_chapter bigint FK -> chapters.id
health_rating           tinyint     -- 1-5
assessment_notes        text
issues_flagged          text
recommendations         text
assessed_by_agent       varchar
created_at              timestamp
```

---

### `chekovs_gun_registry`
```sql
-- Plot Systems Engineer maintains this
-- Every planted element that requires a payoff
id                      bigint PK
name                    varchar
description             text
planted_chapter_id      bigint FK -> chapters.id
planted_scene_id        bigint FK -> scenes.id nullable
element_type            enum(object, character_trait, information, location,
                              ability, relationship, promise, foreshadowing)
payoff_planned          boolean default false
payoff_chapter_id       bigint FK -> chapters.id nullable
payoff_description      text
status                  enum(planted, pending_payoff, paid_off, removed, deferred)
notes                   text
canon_status            enum
created_at              timestamp
updated_at              timestamp
```

---

### `subplot_touchpoint_log`
```sql
-- Subplot Coordinator tracks chapter-by-chapter subplot contact
id                  bigint PK
plot_thread_id      bigint FK -> plot_threads.id
chapter_id          bigint FK -> chapters.id
touchpoint_type     enum(direct, referenced, consequence, setup)
description         text
chapters_since_last int     -- computed/maintained
notes               text
created_at          timestamp
```

---

## Section 4: Timeline and Chronology Tables

---

### `events`
```sql
id                      bigint PK
name                    varchar
slug                    varchar unique
type                    enum(battle, revelation, travel, death, treaty, betrayal,
                              ritual, discovery, political, personal, supernatural,
                              time_skip, natural_disaster, birth, coronation)
event_date              varchar     -- in-world calendar
absolute_day_number     int         -- day from story start, maintained by Timeline Manager
relative_time_label     varchar     -- "three days after the battle"
location_id             bigint FK -> locations.id nullable
summary                 text
objective_outcome       text
pov_characters_present  json        -- quick reference array
source_chapter_id       bigint FK -> chapters.id nullable
notes                   text
canon_status            enum
created_at              timestamp
updated_at              timestamp
```

---

### `event_participants`
```sql
event_id        bigint FK -> events.id
character_id    bigint FK -> characters.id
role            enum(present, instigator, victim, witness, commander,
                      target, bystander, absent_affected)
notes           text
PRIMARY KEY (event_id, character_id)
```

---

### `event_artifacts`
```sql
event_id        bigint FK -> events.id
artifact_id     bigint FK -> artifacts.id
role            enum(used, revealed, moved, damaged, stolen, destroyed, created, found)
notes           text
PRIMARY KEY (event_id, artifact_id)
```

---

### `travel_segments`
```sql
id                          bigint PK
character_id                bigint FK -> characters.id
from_location_id            bigint FK -> locations.id
to_location_id              bigint FK -> locations.id
departure_event_id          bigint FK -> events.id nullable
arrival_event_id            bigint FK -> events.id nullable
departure_chapter_id        bigint FK -> chapters.id nullable
arrival_chapter_id          bigint FK -> chapters.id nullable
estimated_duration_days     int
actual_duration_days        int
travel_method               varchar
companions                  json        -- array of character_ids
realism_flag                boolean     -- Timeline Manager flags unrealistic timing
realism_notes               text
notes                       text
created_at                  timestamp
updated_at                  timestamp
```

---

### `pov_chronological_position`
```sql
-- Timeline Manager maintains this
-- The in-world date/day for each POV character at each chapter
-- Critical for multi-POV sync
id                      bigint PK
character_id            bigint FK -> characters.id
chapter_id              bigint FK -> chapters.id
absolute_day_number     int         -- which in-world day this chapter starts on for this POV
in_world_date_label     varchar
days_ahead_of_slowest   int         -- how far this thread is ahead of the slowest thread
sync_notes              text        -- flags if threads are diverging problematically
created_at              timestamp
updated_at              timestamp
UNIQUE(character_id, chapter_id)
```

---

## Section 5: Knowledge, Reader State, and Information Tables

---

### `reader_reveals`
```sql
-- When the reader learns something (may differ from any character learning it)
id                          bigint PK
reveal_statement            text
revealed_in_chapter_id      bigint FK -> chapters.id
revealed_in_scene_id        bigint FK -> scenes.id nullable
revealed_to_character_id    bigint FK -> characters.id nullable  -- null if reader-only
reveal_type                 enum(direct, implied, ironic, contradictory, dramatic_irony)
setup_chapter_id            bigint FK -> chapters.id nullable
setup_adequacy_note         text
notes                       text
canon_status                enum
created_at                  timestamp
updated_at                  timestamp
```

---

### `reader_information_states`
```sql
-- Information State Tracker maintains this
-- Cumulative snapshot of what the reader knows at the END of each chapter
-- Distinct from reader_reveals (which tracks individual revelations)
id                          bigint PK
after_chapter_id            bigint FK -> chapters.id unique
known_facts_summary         text    -- narrative summary of reader's knowledge state
active_mysteries            json    -- array of questions the reader is holding
confirmed_facts             json    -- array of things definitively established
suspected_facts             json    -- things implied but not confirmed
active_dramatic_ironies     json    -- what reader knows that characters don't
information_gaps            text    -- what reader still doesn't know (intentional)
updated_by_agent            varchar
notes                       text
created_at                  timestamp
updated_at                  timestamp
```

---

### `dramatic_irony_inventory`
```sql
-- POV Manager maintains this
-- What does the reader know that specific characters don't?
id                              bigint PK
irony_statement                 text        -- "Reader knows X, but Character A doesn't"
reader_knows_from_chapter_id    bigint FK -> chapters.id
uninformed_character_id         bigint FK -> characters.id
character_learns_chapter_id     bigint FK -> chapters.id nullable  -- when/if they learn it
irony_type                      enum(simple, compounded, tragic, comic, sustained)
tension_potential               enum(low, medium, high, critical)
status                          enum(active, resolved, expired, never_resolved)
scenes_that_exploit_this        json    -- array of scene_ids
notes                           text
created_at                      timestamp
updated_at                      timestamp
```

---

## Section 6: Pacing, Structure, and Tension Tables

---

### `pacing_beats`
```sql
-- Pacing and Tension Analyst maps these
-- Discrete pacing events: escalations, relief valves, reversals, etc.
id                  bigint PK
chapter_id          bigint FK -> chapters.id
scene_id            bigint FK -> scenes.id nullable
beat_type           enum(escalation, relief, reversal, revelation, misdirection,
                          lull, crisis, recovery, acceleration, plateau)
intensity_level     tinyint     -- 1-10
description         text
reader_effect       text        -- intended reader experience
notes               text
created_at          timestamp
```

---

### `tension_measurements`
```sql
-- Pacing and Tension Analyst maintains rolling tension map
id                      bigint PK
chapter_id              bigint FK -> chapters.id
tension_start_level     tinyint     -- 1-10 at chapter open
tension_peak_level      tinyint     -- 1-10 highest point
tension_end_level       tinyint     -- 1-10 at chapter close
assessment_notes        text
issues_flagged          text
assessed_by_agent       varchar
created_at              timestamp
```

---

### `scene_character_goals`
```sql
-- Scene Builder defines each character's goal/stake in each scene
id                  bigint PK
scene_id            bigint FK -> scenes.id
character_id        bigint FK -> characters.id
goal                text    -- what this character wants in this scene
motivation          text    -- why they want it
tactics             text    -- what they're willing to do to get it
willing_to_reveal   text    -- what they'd expose under pressure
outcome             text    -- what they actually achieve/lose
notes               text
created_at          timestamp
updated_at          timestamp
```

---

## Section 7: Canon, Continuity, and Integrity Tables

---

### `canon_facts`
```sql
id                      bigint PK
fact_statement          text
category                enum(character, world, magic, political, historical,
                              supernatural, timeline, relationship, plot)
source_file             varchar
source_chapter_id       bigint FK -> chapters.id nullable
source_event_id         bigint FK -> events.id nullable
confidence_level        enum(certain, probable, inferred, disputed)
canon_status            enum(canon, provisional, deprecated, contradicted)
superseded_by_id        bigint FK -> canon_facts.id nullable
notes                   text
created_at              timestamp
updated_at              timestamp
```

---

### `continuity_issues`
```sql
-- Continuity Editor writes all issues here
-- Replaces the flat contradictions-log.md file
id                          bigint PK
issue_type                  enum(character_name, place_name, timeline, magic_violation,
                                  physical_continuity, knowledge_violation,
                                  relationship_inconsistency, geographical_error,
                                  voice_drift, plot_logic, world_rule)
severity                    enum(critical, major, minor, cosmetic)
description                 text
chapter_id                  bigint FK -> chapters.id nullable
scene_id                    bigint FK -> scenes.id nullable
conflicting_fact_a          text
conflicting_fact_b          text
canon_fact_id               bigint FK -> canon_facts.id nullable
resolution_status           enum(open, in_progress, resolved, accepted_as_is, deferred)
resolution_notes            text
detected_by_agent           varchar
resolved_at                 timestamp nullable
notes                       text
created_at                  timestamp
updated_at                  timestamp
```

---

### `decisions_log`
```sql
-- Canon Keeper logs every significant creative decision here
-- The authoritative record of "why we did it this way"
id                      bigint PK
decision_summary        text
decision_type           enum(character, plot, world, magic, structural, style,
                              naming, timeline, pov, theme)
rationale               text
alternatives_considered text
affected_entities       json    -- array of {type, id} references
made_in_session_id      bigint FK -> session_logs.id nullable
chapter_context_id      bigint FK -> chapters.id nullable
is_locked               boolean default false  -- locked decisions cannot be changed without explicit override
notes                   text
created_at              timestamp
updated_at              timestamp
```

---

### `foreshadowing_registry`
```sql
-- Foreshadowing and Prophecy Tracker maintains this
id                          bigint PK
name                        varchar
description                 text
planted_chapter_id          bigint FK -> chapters.id
planted_scene_id            bigint FK -> scenes.id nullable
foreshadowing_type          enum(direct, symbolic, atmospheric, structural, dialogue, action)
what_it_implies             text
intended_payoff             text
payoff_chapter_id           bigint FK -> chapters.id nullable
payoff_scene_id             bigint FK -> scenes.id nullable
status                      enum(planted, active, paid_off, redirected, abandoned)
reader_visibility           enum(obvious, subtle, invisible_until_reread)
notes                       text
canon_status                enum
created_at                  timestamp
updated_at                  timestamp
```

---

### `prophecy_registry`
```sql
id                          bigint PK
name                        varchar
exact_text                  text        -- verbatim prophecy as it appears in the story
source_character_id         bigint FK -> characters.id nullable
delivered_chapter_id        bigint FK -> chapters.id nullable
current_interpretation      text        -- what characters currently believe it means
true_interpretation         text        -- what it actually means (author knowledge)
fulfillment_status          enum(unfulfilled, partially_fulfilled, fulfilled,
                                  subverted, reinterpreted, false_prophecy)
fulfillment_chapter_id      bigint FK -> chapters.id nullable
reinterpretation_events     json        -- array of chapter_ids where interpretation shifted
notes                       text
canon_status                enum
created_at                  timestamp
updated_at                  timestamp
```

---

### `object_states`
```sql
-- Track artifact/object location and status chapter by chapter
id                          bigint PK
artifact_id                 bigint FK -> artifacts.id
chapter_id                  bigint FK -> chapters.id
holder_character_id         bigint FK -> characters.id nullable
location_id                 bigint FK -> locations.id nullable
state_note                  text
visibility_status           enum(public, hidden, secret, lost, destroyed, unknown)
notes                       text
created_at                  timestamp
```

---

## Section 8: Literary Layer Tables

---

### `motif_registry`
```sql
-- Symbolism and Motif Tracker maintains this
id                      bigint PK
name                    varchar
description             text
motif_type              enum(object, color, action, phrase, condition, animal,
                              weather, number, spatial, sonic)
thematic_connection     text    -- how this motif connects to theme
intended_evolution      text    -- how meaning of motif should shift over story
first_occurrence_chapter bigint FK -> chapters.id nullable
status                  enum(active, completed, abandoned)
notes                   text
canon_status            enum
created_at              timestamp
updated_at              timestamp
```

---

### `motif_occurrences`
```sql
id                  bigint PK
motif_id            bigint FK -> motif_registry.id
chapter_id          bigint FK -> chapters.id
scene_id            bigint FK -> scenes.id nullable
context_description text
meaning_at_this_point text   -- how the motif functions at this occurrence
is_evolution_point  boolean -- does this occurrence shift the motif's meaning
notes               text
created_at          timestamp
```

---

### `thematic_mirrors`
```sql
-- Thematic Architecture Agent maintains this
-- Structural pairings: characters or arcs that mirror or contrast each other
id                          bigint PK
name                        varchar
element_a_type              varchar     -- 'character', 'plot_thread', 'location', 'faction'
element_a_id                bigint
element_b_type              varchar
element_b_id                bigint
mirror_type                 enum(foil, parallel, inversion, echo, contrast)
thematic_function           text        -- what this pairing illuminates about the theme
how_it_manifests            text        -- concrete ways this shows up in the story
notes                       text
canon_status                enum
created_at                  timestamp
updated_at                  timestamp
```

---

### `opposition_pairs`
```sql
-- Thematic Architecture Agent: how the central opposition manifests
-- e.g., Mercy vs Order showing up in locations, objects, events, not just characters
id                      bigint PK
opposition_name         varchar     -- e.g., "Mercy vs Order"
element_type            varchar     -- 'character', 'location', 'faction', 'event', 'object', 'theme'
element_id              bigint
which_pole              enum(pole_a, pole_b, synthesis, tension_point)
manifestation           text        -- how this element embodies its pole
chapter_id              bigint FK -> chapters.id nullable  -- when this manifestation peaks
notes                   text
canon_status            enum
created_at              timestamp
updated_at              timestamp
```

---

### `supernatural_voice_guidelines`
```sql
-- Supernatural Voice Specialist maintains this
-- How the supernatural sounds and feels in prose, not what it can do
id                          bigint PK
element_type                varchar     -- which supernatural element this applies to
prose_register              text        -- formal, fragmented, elevated, alien, etc.
sentence_structure_notes    text
vocabulary_restrictions     text        -- words to avoid or prefer
sensory_texture             text        -- how it should feel to read
rhythm_notes                text        -- pace, cadence, silence usage
contrast_with_normal_prose  text        -- how it should differ from surrounding text
reference_examples          text        -- example passages that nail this register
notes                       text
canon_status                enum
created_at                  timestamp
updated_at                  timestamp
```

---

## Section 9: World State Tables

---

### `faction_political_states`
```sql
-- Political Systems Analyst tracks the dynamic political map over time
-- The factions table is static; this captures how political reality shifts
id                          bigint PK
faction_id                  bigint FK -> factions.id
as_of_chapter_id            bigint FK -> chapters.id
political_strength          enum(ascending, stable, declining, crisis, collapsed)
territory_summary           text
current_leader_id           bigint FK -> characters.id nullable
active_goals                text
active_threats              text
current_alliances           json    -- array of faction_ids
current_conflicts           json    -- array of faction_ids
notes                       text
created_at                  timestamp
```

---

### `name_registry`
```sql
-- Names and Linguistics Specialist maintains this
-- Every name in the manuscript with cultural attribution and phoneme notes
id                      bigint PK
name                    varchar
name_type               enum(character, location, faction, artifact, magic_term,
                              title, creature, cultural_term, deity)
reference_id            bigint nullable     -- FK to the relevant entity
reference_type          varchar nullable
culture_id              bigint FK -> cultures.id nullable
phoneme_pattern         varchar     -- e.g., "CV-CVC" or "consonant cluster + vowel"
similar_names           json        -- array of potentially confusing similar names
similarity_flags        json        -- names within edit distance 2 already in registry
introduced_chapter_id   bigint FK -> chapters.id nullable
notes                   text
created_at              timestamp
updated_at              timestamp
```

---

### `magic_use_log`
```sql
-- Magic System Engineer tracks every instance of magic in the manuscript
id                          bigint PK
chapter_id                  bigint FK -> chapters.id
scene_id                    bigint FK -> scenes.id nullable
practitioner_character_id   bigint FK -> characters.id
magic_element_id            bigint FK -> magic_system_elements.id nullable
description                 text
cost_paid                   text    -- what the practitioner spent/risked
scale                       enum(minor, moderate, major, exceptional)
is_rules_compliant          boolean
violation_notes             text    -- if not compliant, what rule is violated
continuity_notes            text    -- lingering effects that should appear later
reviewed_by_agent           varchar
created_at                  timestamp
updated_at                  timestamp
```

---

### `practitioner_abilities`
```sql
-- What each character can and can't do with magic
id                          bigint PK
character_id                bigint FK -> characters.id
magic_element_id            bigint FK -> magic_system_elements.id
ability_level               enum(none, minimal, developing, competent, expert, master)
access_type                 enum(innate, trained, granted, stolen, ritual, item_based)
established_chapter_id      bigint FK -> chapters.id nullable
limitations                 text
notes                       text
canon_status                enum
created_at                  timestamp
updated_at                  timestamp
```

---

## Section 10: Research and Documentation Tables

---

### `research_notes`
```sql
id                  bigint PK
topic               varchar
category            enum(military, medical, political, religious, geographic,
                          cultural, linguistic, historical, craft, genre)
summary             text
source_citation     text
applies_to          text    -- which story elements this informs
status              enum(raw, reviewed, adopted, rejected, needs_more)
notes               text
created_at          timestamp
updated_at          timestamp
```

---

### `open_questions`
```sql
-- Formal tracking of all unanswered research and story questions
id                      bigint PK
question                text
category                enum(research, plot, character, world, magic, timeline,
                              structure, style, continuity)
priority                enum(blocking, high, medium, low)
raised_in_session_id    bigint FK -> session_logs.id nullable
raised_by_agent         varchar
answer                  text nullable
answered_in_session_id  bigint FK -> session_logs.id nullable
status                  enum(open, in_progress, answered, deferred, abandoned)
notes                   text
created_at              timestamp
updated_at              timestamp
```

---

### `documentation_tasks`
```sql
id                  bigint PK
trigger_type        enum(new_chapter, revision, structural_edit, lore_update,
                          decision_change, agent_flag)
trigger_ref         varchar
file_path           varchar
table_name          varchar nullable    -- which DB table needs updating
task_summary        text
priority            enum(blocking, high, medium, low)
status              enum(pending, in_progress, complete, deferred)
owner_role          varchar     -- which agent is responsible
notes               text
created_at          timestamp
updated_at          timestamp
completed_at        timestamp nullable
```

---

## Section 11: Publishing Tables

---

### `publishing_assets`
```sql
-- Publishing Preparation Agent maintains this
id                      bigint PK
asset_type              enum(logline, elevator_pitch, query_letter, synopsis_short,
                              synopsis_long, back_cover_copy, comp_analysis,
                              author_bio, chapter_sample)
version                 int
content                 text
word_count              int
target_audience         varchar
submission_notes        text
is_current              boolean default false
status                  enum(draft, reviewed, approved, submitted, archived)
notes                   text
created_at              timestamp
updated_at              timestamp
```

---

### `submission_tracker`
```sql
id                      bigint PK
agency_or_publisher     varchar
agent_name              varchar nullable
submission_date         date
query_version_id        bigint FK -> publishing_assets.id nullable
synopsis_version_id     bigint FK -> publishing_assets.id nullable
pages_submitted         int nullable
submission_status       enum(queried, partial_requested, full_requested,
                              rejected, withdrawn, offer, closed)
response_date           date nullable
response_notes          text
follow_up_date          date nullable
notes                   text
created_at              timestamp
updated_at              timestamp
```

---

## Section 12: Session and Project Management Tables

---

### `session_logs`
```sql
-- Session Continuity Manager writes here at start and end of every session
id                          bigint PK
session_date                date
session_number              int
session_type                enum(architecture, worldbuilding, character, plotting,
                                  scene_construction, prose, revision, editorial,
                                  continuity_check, research, publishing)
objectives_set              text    -- what this session intended to accomplish
work_completed              text    -- what was actually done
decisions_made              json    -- array of decision_log ids made this session
files_modified              json    -- array of file paths
chapters_worked             json    -- array of chapter_ids
open_items_at_close         text    -- unresolved items to carry forward
next_session_priorities     text    -- recommended starting point for next session
agent_runs                  json    -- array of agent_run_log ids from this session
notes                       text
created_at                  timestamp
closed_at                   timestamp nullable
```

---

### `agent_run_log`
```sql
-- Full audit trail of every agent operation
id                  bigint PK
session_id          bigint FK -> session_logs.id nullable
agent_name          varchar
run_type            enum(analysis, creation, update, audit, query, export)
input_summary       text    -- what the agent was asked to do
output_summary      text    -- what it produced
tables_read         json    -- array of table names
tables_written      json    -- array of table names
records_created     int
records_updated     int
issues_flagged      int
duration_seconds    int nullable
notes               text
created_at          timestamp
```

---

### `architecture_gate`
```sql
-- Architecture Completeness Auditor maintains this
-- The formal gate before prose begins
id                          bigint PK
gate_name                   varchar     -- "Pre-Prose Architecture Gate"
status                      enum(open, in_progress, passed, failed, waived)
assessed_date               date nullable
assessor_agent              varchar
overall_pass                boolean nullable
blocking_issues_count       int
non_blocking_issues_count   int
assessment_notes            text
passed_at                   timestamp nullable
notes                       text
created_at                  timestamp
updated_at                  timestamp
```

---

### `gate_checklist_items`
```sql
id                      bigint PK
gate_id                 bigint FK -> architecture_gate.id
checklist_item          text        -- the specific thing being verified
category                enum(chapters, scenes, characters, world, magic,
                              timeline, arcs, foreshadowing, continuity, research)
is_blocking             boolean     -- if false, can pass gate with this open
is_passed               boolean default false
failure_notes           text
evidence_query          text        -- the SQL query or file that verifies this
notes                   text
checked_at              timestamp nullable
created_at              timestamp
updated_at              timestamp
```

---

### `project_metrics_snapshots`
```sql
-- Project Manager writes periodic snapshots
id                              bigint PK
snapshot_date                   date
total_word_count                int
act_1_word_count                int
act_2_word_count                int
act_3_word_count                int
chapters_planned                int
chapters_architected            int
chapters_approved               int
chapters_drafted                int
chapters_final                  int
scenes_total                    int
scenes_constructed              int
scenes_approved                 int
open_continuity_issues          int
open_continuity_critical        int
arc_health_average              decimal(3,1)
pov_balance_json                json    -- {character_id: chapter_count} snapshot
days_since_last_session         int
estimated_completion_date       date nullable
notes                           text
created_at                      timestamp
```

---

### `pov_balance_snapshots`
```sql
id                          bigint PK
snapshot_chapter_id         bigint FK -> chapters.id
character_id                bigint FK -> characters.id
chapter_count               int
word_count_estimate         int
percentage_of_total         decimal(5,2)
chapters_since_last_pov     int
status                      enum(on_target, ahead, behind, absent_too_long)
notes                       text
created_at                  timestamp
```

---

### `reader_experience_notes`
```sql
-- Reader Experience Simulator writes here
id                          bigint PK
chapter_id                  bigint FK -> chapters.id
scene_id                    bigint FK -> scenes.id nullable
issue_type                  enum(confusion, information_gap, information_dump,
                                  pacing_friction, mystery_leak, reward_gap,
                                  character_loss, orientation_failure)
description                 text
reader_likely_question      text    -- what the reader is probably wondering here
severity                    enum(minor, moderate, significant, blocking)
resolution_status           enum(open, resolved, accepted)
resolution_notes            text
assessed_by_agent           varchar
created_at                  timestamp
updated_at                  timestamp
```

---

## Section 13: Key Relationships Summary

```sql
-- Entity Hierarchy
books -> acts -> chapters -> scenes
characters -> character_arcs -> chapter_character_arcs -> chapters
characters -> character_knowledge, character_beliefs, character_locations, injury_states
characters <-> characters via character_relationships + perception_profiles

-- Plot Machinery
plot_threads <-> chapters via chapter_plot_threads
chekovs_gun_registry -> chapters (planted) -> chapters (payoff)
foreshadowing_registry -> chapters (planted) -> chapters (payoff)
prophecy_registry -> chapters (delivered) -> chapters (fulfilled)

-- Timeline
events -> locations
events <-> characters via event_participants
events <-> artifacts via event_artifacts
chapters -> pov_chronological_position -> characters
travel_segments -> characters, locations, events

-- Literary Layer
motif_registry -> motif_occurrences -> chapters, scenes
thematic_mirrors -> (polymorphic: characters, plot_threads, locations, factions)
opposition_pairs -> (polymorphic)
dramatic_irony_inventory -> chapters, characters

-- Agent Operations
session_logs -> agent_run_log -> (all tables)
architecture_gate -> gate_checklist_items
decisions_log -> session_logs
open_questions -> session_logs
```

---

## Section 14: Agent-to-Table Ownership Map

| Agent | Primary Tables (Write) | Primary Tables (Read) |
|---|---|---|
| Story Architect | acts, tension_measurements | acts, chapters, character_arcs, plot_threads |
| Plot Systems Engineer | chekovs_gun_registry, plot_threads | chapters, events, chapter_plot_threads |
| Subplot Coordinator | subplot_touchpoint_log, plot_threads | chapter_plot_threads, chapters |
| Chapter Architect | chapters, chapter_structural_obligations | plot_threads, character_arcs, scenes |
| Scene Builder | scenes, scene_character_goals | chapters, characters, locations |
| Pacing Analyst | pacing_beats, tension_measurements | chapters, scenes |
| Arc Tracker | arc_health_log, character_arcs | chapter_character_arcs, chapters |
| Timeline Manager | pov_chronological_position, events | travel_segments, chapters |
| POV Manager | pov_balance_snapshots, dramatic_irony_inventory | chapters, character_arcs |
| Character Architect | characters, character_arcs | character_knowledge, character_beliefs |
| Voice Auditor | voice_profiles, voice_drift_log | characters, chapters |
| Relationship Manager | character_relationships, relationship_change_events | events, chapters |
| Perception Profile Manager | perception_profiles | characters, character_relationships |
| World Architect | locations, factions, cultures | all world tables |
| Magic System Engineer | magic_system_elements, magic_use_log, practitioner_abilities | characters, chapters |
| Political Systems Analyst | faction_political_states | factions, events, title_states |
| Names Specialist | name_registry | characters, locations, cultures |
| Canon Keeper | canon_facts, decisions_log | all tables |
| Continuity Editor | continuity_issues | all tables |
| Foreshadowing Tracker | foreshadowing_registry, prophecy_registry | chapters, scenes |
| Symbolism Tracker | motif_registry, motif_occurrences | chapters, scenes |
| Thematic Architecture | thematic_mirrors, opposition_pairs | character_arcs, plot_threads |
| Information State Tracker | reader_information_states | reader_reveals, character_knowledge |
| Supernatural Voice | supernatural_voice_guidelines | supernatural_elements |
| Prose Writer | chapters (word count, status) | all architecture tables |
| Dialogue Specialist | scenes (dialogue notes) | voice_profiles, characters |
| Battle Coordinator | events, travel_segments | locations, characters, chapters |
| Sensory Specialist | locations (sensory_profile) | locations, chapters |
| Developmental Editor | arc_health_log, reader_experience_notes | all chapter/arc tables |
| Line Editor | chapters (prose notes) | voice_profiles, style docs |
| Copy Editor | chapters (corrections) | name_registry, canon_facts |
| Reader Experience Simulator | reader_experience_notes | reader_information_states, chapters |
| Chapter Hook Specialist | chapters (hook ratings) | chapters, pacing_beats |
| Architecture Completeness Auditor | architecture_gate, gate_checklist_items | all tables |
| Session Continuity Manager | session_logs | decisions_log, open_questions |
| Project Manager | project_metrics_snapshots | all status/count fields |
| Publishing Preparation Agent | publishing_assets, submission_tracker | characters, plot_threads |
| Genre Analyst | publishing_assets (comp analysis) | all story tables |

---

## Section 15: Practical Implementation Notes

### Laravel Model Approach

Each table above becomes a Laravel Eloquent model. The polymorphic relationships (thematic_mirrors, opposition_pairs, chapter_structural_obligations) use Laravel's standard `morphTo` / `morphMany` pattern.

### Filament Admin Panel

Build one Filament resource per major entity group:

- **Manuscript** — Books, Acts, Chapters, Scenes
- **Characters** — Characters, Arcs, Relationships, Perceptions, Voice Profiles
- **World** — Locations, Factions, Cultures, Eras, Magic
- **Plot** — Plot Threads, Chekhov's Guns, Foreshadowing, Prophecy
- **Timeline** — Events, Travel Segments, POV Positions
- **Continuity** — Issues, Canon Facts, Decisions Log
- **Literary** — Motifs, Thematic Mirrors, Opposition Pairs
- **Reader** — Reveals, Information States, Dramatic Irony
- **Project** — Sessions, Agent Runs, Architecture Gate, Metrics

### Claude Code Agent Queries

Each agent gets a set of pre-built queries it runs at the start of a session. Example for Timeline Manager:

```sql
-- Current chronological position of all POV threads
SELECT c.name, ch.chapter_number, ch.title, p.absolute_day_number, p.sync_notes
FROM pov_chronological_position p
JOIN characters c ON p.character_id = c.id
JOIN chapters ch ON p.chapter_id = ch.id
WHERE ch.id = (
    SELECT MAX(chapter_id) FROM pov_chronological_position
    WHERE character_id = p.character_id
)
ORDER BY p.absolute_day_number;

-- Characters who haven't appeared in 5+ chapters
SELECT c.name, MAX(ch.chapter_number) as last_chapter,
       (SELECT MAX(chapter_number) FROM chapters) - MAX(ch.chapter_number) as chapters_absent
FROM chapters ch
JOIN characters c ON ch.pov_character_id = c.id
WHERE c.pov_status = 'active'
GROUP BY c.id
HAVING chapters_absent >= 5;
```

### Markdown Export Strategy

One artisan command per major entity type:

```bash
php artisan novel:export chapters      # Regenerate all chapter markdown files
php artisan novel:export characters    # Regenerate all character sheets
php artisan novel:export timeline      # Regenerate master timeline
php artisan novel:export bible         # Full story bible regeneration
php artisan novel:export --chapter=22  # Single chapter export
```

Markdown files are stored in git. The database is the source; the files are the snapshot. When Claude Code needs prose context it loads the markdown. When it needs structured queries it hits the database.

### Migration Order

Build tables in this sequence to satisfy FK constraints:

1. `books`, `eras`, `cultures`
2. `locations`, `factions`
3. `characters`
4. `acts`, `chapters`, `scenes`
5. `events`, `travel_segments`
6. `character_arcs`, `plot_threads`, `artifacts`, `magic_system_elements`
7. All pivot and state tables
8. All tracking and log tables
9. `session_logs`, `agent_run_log`, `architecture_gate`
