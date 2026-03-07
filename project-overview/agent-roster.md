# Epic Fantasy Novel: Complete Agent Roster
## All 40 Agents — Full Definitions, Corrected Phasing and Tier Assignments
### Version 2.0 — Updated with Gap Analysis Additions and Workflow Corrections

---

## How to Read This Document

Every agent is defined with:
- **Purpose** — the one-sentence job description
- **Why it exists as a separate role** — the justification for not merging it with something else
- **Workflow phase** — which phase this agent is active in
- **Core tasks** — what it actually does
- **Key context loaded** — which project files and database tables it needs
- **Handoff points** — which agents it feeds into or receives from
- **Sample invocations** — real prompts you would use to trigger it

---

## Critical Workflow Constraint

**No prose is written until the story is 100% architected and all story elements have been approved.**

This is not a preference — it is a hard architectural rule that governs the entire agent system. The implications:

- Agents in Phases 1–3 build the complete blueprint. Every chapter, every scene, every character state, every plot beat must be fully specified before Phase 5 begins.
- Phase 4 is a formal gate. The Architecture Completeness Auditor must certify the manuscript is ready. Nothing in Phase 5 begins without that certification.
- The Prose Writer is an executor, not a collaborator. It receives complete specifications and renders them. It never invents worldbuilding, never makes structural decisions, and never fills gaps by improvising. If a specification is incomplete, it stops and escalates.
- Scene Builder and Chapter Architect are architecture-phase agents, not drafting-support tools. They produce production specifications the Prose Writer executes from later.

---

## Phasing Model

### Phase 1 — Foundation Architecture
*Build the world, the characters, and the rules before touching structure.*

Story Architect, World Architect, Character Architect, Magic System Engineer,
Supernatural Voice Specialist (rules layer), Timeline Manager, Names and Linguistics Specialist,
Political Systems Analyst, Canon Keeper, Session Continuity Manager (ongoing from day one)

### Phase 2 — Structural Architecture
*Build the complete plot machinery, arc shapes, and narrative systems.*

Plot Systems Engineer, Subplot Coordinator, Arc Tracker, POV Manager,
Foreshadowing and Prophecy Tracker, Thematic Architecture Agent, Information State Tracker,
Relationship Dynamics Manager, Perception Profile Manager, Pacing and Tension Analyst

### Phase 3 — Scene and Chapter Architecture
*Translate structure into complete production specifications for every chapter and scene.*

Chapter Architect, Scene Builder, Battle and Action Coordinator,
Sensory and Atmosphere Specialist, Character Voice Auditor (voice reference cards),
Dialogue Specialist (beat-level planning), Chapter Hook Specialist (opening/closing specs)

### Phase 4 — Architecture Review and Approval Gate
*Verify the architecture is complete before a single prose sentence is written.*

Developmental Editor, Reader Experience Simulator, Architecture Completeness Auditor
**— Hard stop. No Phase 5 begins without the Architecture Completeness Auditor's certification. —**

### Phase 5 — Prose Execution
*Write the manuscript from the approved specifications.*

Prose Writer, Character Voice Auditor (active monitoring), Dialogue Specialist (line-level work),
Supernatural Voice Specialist (prose texture), Sensory and Atmosphere Specialist (active monitoring)

### Phase 6 — Editorial
*Revise, refine, and polish the completed manuscript.*

Developmental Editor, Line Editor, Copy Editor, Reader Experience Simulator,
Chapter Hook Specialist, Continuity Editor, Symbolism and Motif Tracker,
Lore Keeper / Story Bible Synchronizer

### Phase 7 — Publishing Preparation
*Package and position the manuscript for submission.*

Publishing Preparation Agent, Genre Analyst

*Session Continuity Manager and Project Manager are active across all phases.*

---

## Coverage Map: Original List vs. Final Roster

| Originally Proposed | Status | Final Agent Name |
|---|---|---|
| Story Architect | Kept, same name | Story Architect |
| Plot Systems Engineer | Kept, expanded | Plot Systems Engineer |
| Character Architect | Kept, same name | Character Architect |
| World Architect | Kept, same name | World Architect |
| Canon Keeper | Kept, same name | Canon Keeper |
| Scene Builder | Kept, moved to architecture phase | Scene Builder |
| Chapter Architect | Kept, moved to architecture phase | Chapter Architect |
| Story Bible Manager | Merged | Lore Keeper / Story Bible Synchronizer |

*New agents added through gap analysis and workflow review are marked NEW below.*

---

## Why Scale Justifies 40 Agents

On a 60,000-word novel, one editor handles structure, pacing, arcs, and prose. At 250,000 words across 55 chapters and multiple POV threads, that same editor would need to load so much context it would either lose coherence or require constant re-briefing.

The principle is narrow context, deep focus. A Timeline Manager loads only chronological data and reasons about it with complete precision. A general editor asked the same question gives a shallow answer buried in other concerns.

Each agent below is justified because at this scale, its domain is large enough to be a full-time job.

---

# TIER 1: STRUCTURAL AGENTS

---

## 1. Story Architect

**Purpose**: Owns the overall narrative structure. Sees the whole building, not the individual rooms.

**Why separate**: At 250,000 words, the distance between Chapter 1 and Chapter 55 is enormous. No agent doing detailed plot work can also maintain clear vision of the whole shape. Story Architect never goes below act-level thinking and deliberately avoids scene or chapter detail.

**Workflow phase**: Phase 1 (foundation), consulted throughout Phases 2–4

**Core tasks**:
- Build and maintain the three-act structure document
- Evaluate whether the story's central dramatic question is being answered
- Track the thematic throughline across all three acts — is it visible, developed, and resolved?
- Assess whether the protagonist's transformation is structurally supported
- Identify where the story's spine is being crowded out by subplots
- Flag structural imbalances: Act 2 too long, Act 3 rushed — the most common problem in long fantasy
- Evaluate the story's major turning points: inciting incident, midpoint, dark night of the soul, climax
- Assess act-level word count proportions against targets
- Escalate thematic concerns to Arc Tracker and Thematic Architecture Agent

**Key context loaded**:
`acts`, `chapters` (summaries only), `character_arcs` (arc summaries), `plot_threads` (main plot only), `tension_measurements`

**Handoff points**:
- Feeds structural decisions to Plot Systems Engineer and Chapter Architect
- Escalates thematic concerns to Arc Tracker and Thematic Architecture Agent
- Receives structural health questions from you

**Sample invocations**:
```
"Review the three-act structure document and the chapter summaries
for Acts 1 and 2. Is the midpoint turning point landing with enough
weight? Does the dark night of the soul feel earned given what's
been set up?"

"I think Act 2 is too long and the pacing is sagging in the middle
third. Give me a structural assessment and flag which chapters are
doing the least work."
```

---

## 2. Plot Systems Engineer

**Purpose**: Manages the mechanical logic of the plot — cause and effect, planted elements, consequence chains, and the machinery that makes a plot feel inevitable rather than coincidental.

**Why separate**: Plotting at this scale is a systems problem. A planted object in Chapter 4 might not pay off until Chapter 41. A character's decision in Chapter 12 might ripple into three POV threads. No other agent tracks this machinery specifically. Story Architect sees shape; this agent sees mechanics.

**Workflow phase**: Phase 2

**Core tasks**:
- Maintain the `chekovs_gun_registry`: everything introduced that needs a payoff, everything paid off that needs a setup
- Track cause-and-effect chains: decision → consequence → ripple effects across threads
- Identify plot holes — events that happen without sufficient cause, or causes with no visible effect
- Flag coincidence overuse: when plot convenience substitutes for logical consequence
- Track information flow: what do characters know, when did they learn it, was the learning plausible?
- Maintain the subplot tracker's mechanical status: introduced, developing, at crisis, resolved
- Identify dangling threads — subplots, objects, or promises that haven't resolved

**Key context loaded**:
`plot_threads`, `chapter_plot_threads`, `events`, `chapters`, `chekovs_gun_registry`

**Handoff points**:
- Feeds Subplot Coordinator with mechanical thread status
- Escalates timeline conflicts to Timeline Manager
- Feeds payoff gaps to Chapter Architect for resolution planning

**Sample invocations**:
```
"Audit the chekovs_gun_registry against all chapter plans through
Chapter 30. What has been planted with no payoff planned? What has
been paid off without sufficient setup?"

"[Character] makes a major decision in Chapter 18 that should affect
[Character B]'s thread. Trace the logical consequence chain forward
through the outline. Are the consequences showing up in the right places?"
```

---

## 3. Subplot Coordinator

**Purpose**: Tracks the full lifecycle of every subplot from introduction to resolution, ensuring nothing is forgotten and nothing overstays its welcome.

**Why separate**: A 250,000-word epic fantasy typically carries 8–15 active subplots simultaneously. Plot Systems Engineer tracks their mechanics; this agent tracks their narrative health and lifecycle. These are different questions: "Is this subplot mechanically consistent?" vs. "Is this subplot getting the page time it needs to land emotionally?"

**Workflow phase**: Phase 2, monitored through Phase 3

**Core tasks**:
- Maintain the `plot_threads` subplot registry: name, introduction point, POV characters involved, current status, expected resolution
- Flag subplots going too many chapters without a touchpoint — the forgotten thread problem
- Flag subplots receiving too much attention relative to their narrative weight
- Track subplot dependencies — subplots that cannot resolve until another subplot reaches a certain stage
- Identify when a subplot has outlived its usefulness and is now dead weight
- Maintain `subplot_touchpoint_log` with chapter-by-chapter contact records
- Track reader promise fulfillment: did the story deliver on what each subplot implied?

**Key context loaded**:
`plot_threads` (filtered is_subplot=true), `chapter_plot_threads`, `chapters`, `subplot_touchpoint_log`

**Handoff points**:
- Feeds Plot Systems Engineer with lifecycle data
- Feeds Chapter Architect with "which subplots need a touchpoint in this chapter" data

**Sample invocations**:
```
"Review the subplot registry and chapter plans through Chapter 25.
List every subplot and its current status. Flag any that haven't
appeared in more than 5 chapters."

"I'm planning Chapter 32. Which subplots are overdue for a touchpoint
and which are approaching their natural resolution point?"
```

---

## 4. Chapter Architect

**Purpose**: Builds the detailed pre-write plan for each individual chapter, translating outline beats into a scene-by-scene blueprint.

**Why separate — and why this is an architecture-phase agent**: There is a gap between a master outline entry ("Chapter 14: Kael reaches the fortress, discovers the betrayal") and an actual draftable chapter plan. That gap requires answering: How many scenes? What order? What is the opening hook? What is the closing hook? What does each scene accomplish? What is the chapter's structural function? At 55 chapters, this is a full discipline — not a footnote to the Plot Architect.

In this workflow, every chapter plan for all 55 chapters must be complete and approved before prose begins. Chapter Architect produces production specifications, not rough guides.

**Workflow phase**: Phase 3

**Core tasks**:
- Translate master outline beats into a detailed chapter plan
- Define each scene within the chapter: location, POV characters, scene goal, conflict, outcome
- Determine the chapter's opening hook and closing hook
- Populate `chapter_structural_obligations` for every subplot touchpoint, arc beat, and plot obligation the chapter must fulfill
- Ensure the chapter has a clear internal arc — it begins somewhere and ends somewhere different
- Set the chapter's word count target based on narrative weight
- Flag any worldbuilding, character, or magic documentation needed before the Prose Writer can execute
- Coordinate with Subplot Coordinator to ensure no thread goes too long without contact

**Key context loaded**:
`chapters`, `scenes`, `plot_threads`, `character_arcs`, `chapter_structural_obligations`, `subplot_touchpoint_log`, relevant story bible sections

**Handoff points**:
- Receives structural direction from Story Architect and Plot Systems Engineer
- Receives subplot obligation data from Subplot Coordinator
- Feeds completed chapter plans to Scene Builder
- Feeds chapter list to Architecture Completeness Auditor for gate check

**Sample invocations**:
```
"Build a detailed chapter plan for Chapter 19. The master outline
beat is [X]. POV is [Character]. We need to touch [subplot] and land
[emotional beat] before Chapter 20. Target 4,500 words."

"Review the chapter plan for Chapter 27 and tell me if it's doing
too much. What could be moved to Chapter 26 or 28 without disrupting
the structural obligations?"
```

---

## 5. Scene Builder

**Purpose**: Constructs individual scenes before drafting — defining what each scene is, what it must accomplish, and what every character in it wants.

**Why separate — and why this is an architecture-phase agent**: A chapter plan lists the scenes that exist. Scene Builder answers the deeper question: what is this scene actually doing? Every scene must have conflict, every character a goal, every outcome a change. At 250,000 words with 150–200 scenes, scenes without clear construction become filler.

In this workflow, every scene brief for every scene in all 55 chapters must be complete and approved before prose begins. The Prose Writer executes from these briefs. They are the source document.

**Workflow phase**: Phase 3

**Core tasks**:
- Define the scene's dramatic question: what is at stake?
- Populate `scene_character_goals` for every character present: goal, motivation, tactics, willingness to reveal, outcome
- Define the scene's conflict: what prevents immediate goal achievement?
- Determine the scene's outcome: what changes by the end?
- Classify scene type and narrative function — does it advance plot, develop character, deliver exposition, establish atmosphere? Ideally two or more simultaneously
- Flag scenes that are purely expository with no dramatic conflict — these are usually cuttable or combinable
- Identify the scene's emotional register and how it contrasts with surrounding scenes
- Ensure every scene brief is complete enough that the Prose Writer has zero architectural ambiguity

**Key context loaded**:
The chapter plan for the containing chapter, relevant character sheets, relevant location documents, `scenes`, `scene_character_goals`

**Handoff points**:
- Receives scene list from Chapter Architect
- Feeds completed scene briefs to Prose Writer (Phase 5)
- Escalates character goal conflicts to Character Architect

**Sample invocations**:
```
"Build the scene brief for Scene 3 of Chapter 14 — the confrontation
in the war council. [Character A] wants to expose [Character B].
[Character B] wants to deflect. What does each other council member
want? What is the dramatic question and what changes by the end?"

"I have three scenes in Chapter 22 that feel like connective tissue
with no real conflict. Analyze them and tell me how to either give
them dramatic stakes or fold them into adjacent scenes."
```

---

## 6. Pacing and Tension Analyst

**Purpose**: Reads the manuscript plan as a sequence of emotional experiences and assesses whether the rhythm of tension and release, action and rest, is working for a reader.

**Why separate**: Pacing is not structure. Structure is about what happens and when. Pacing is about how fast or slow the experience of reading is — scene density, ratio of action to reflection, frequency of revelations. A story can be structurally sound and pace terribly. At 250,000 words, even a 10% pacing problem is 25,000 words of friction.

**Workflow phase**: Phase 2 (structural map), Phase 3 (scene-level rhythm), Phase 4 (gate review), Phase 6 (prose-level)

**Core tasks**:
- Analyze the tension curve of any section: is tension rising, falling, or flat-lining?
- Maintain `tension_measurements` per chapter: start level, peak level, end level (1–10 scale)
- Maintain `pacing_beats`: escalations, relief valves, reversals, lulls, crises
- Identify reader reward and denial patterns: when does the story give vs. withhold? Is the ratio healthy?
- Flag sections that are all tension (reader fatigue) or all release (reader boredom)
- Evaluate chapter-ending hooks: are they generating forward momentum?
- Track the escalation arc: is each act's tension ceiling higher than the last?
- Assess pacing contrast between POV threads: when one thread is in crisis and another is pastoral, is the contrast intentional?
- Flag prose pace mismatches once in Phase 6: where sentence structure doesn't match emotional register

**Key context loaded**:
`chapters`, `scenes`, `pacing_beats`, `tension_measurements`, `plot_threads`

**Handoff points**:
- Reports pacing problems to Story Architect for structural intervention
- Reports scene-level issues to Scene Builder
- Reports prose-pace mismatches to Line Editor in Phase 6

**Sample invocations**:
```
"Analyze the tension curve for Chapters 20–28. Map the high and low
points. Is the arc escalating toward the Act 2 climax or is it uneven?
Where are the dead zones?"

"Read the chapter plans for [Character A]'s last 6 chapters and assess
the pacing of her thread. Is the reader being rewarded and denied at
the right intervals?"
```

---

## 7. Arc Tracker

**Purpose**: Tracks the shape and progress of every arc in the novel — character arcs, subplot arcs, and thematic arcs — ensuring each is progressing, has a visible midpoint shift, and is heading toward a meaningful resolution.

**Why separate**: Character Architect tracks character state — where is this character right now? Arc Tracker tracks character shape — is this character's journey drawing a meaningful curve? A character can be precisely documented and still have a flat arc because no one is monitoring the shape. These are distinct questions.

**Workflow phase**: Phase 2, monitored through Phase 4

**Core tasks**:
- Maintain `arc_health_log` for every major character: stated arc, expected midpoint shift, current progress, expected resolution
- Flag arcs that have stalled — characters who haven't had meaningful belief or behavior change in too many chapters
- Identify passive arcs — characters having things done to them rather than making meaningful choices
- Track thematic arcs: how does each POV character's story embody a different facet of the novel's central theme?
- Track subplot arcs: each subplot should have a beginning, middle, and end
- Identify arc collisions: two characters on converging arcs that should produce a meaningful scene when they meet
- Assess arc payoff: when an arc reaches resolution, is the payoff commensurate with the setup?

**Key context loaded**:
`character_arcs`, `chapter_character_arcs`, `arc_health_log`, `plot_threads`, `chapters`

**Handoff points**:
- Reports arc stalls to Story Architect and Chapter Architect
- Reports character arc concerns to Character Architect
- Feeds thematic arc analysis to Thematic Architecture Agent

**Sample invocations**:
```
"Audit all POV character arcs through Chapter 30. Which characters
have had meaningful arc progression in the last 8 chapters? Which
have stalled? What is the next expected beat for each?"

"[Character]'s arc moves from ruthless pragmatist to reluctant
idealist. Map where she currently sits on that arc based on the
chapter plans and tell me if the midpoint shift has landed."
```

---

## 8. Timeline Manager

**Purpose**: Maintains a precise chronological record of all events in the story — day by day when needed — and manages all time jumps, elapsed time, seasonal changes, and simultaneous events across POV threads.

**Why separate**: Multi-POV epic fantasy is chronologically treacherous. Thread A might cover three days while Thread B covers three weeks, and they have to re-sync when the characters meet. If you don't track this obsessively, you'll write a scene where two characters meet having both independently witnessed the same battle — one three days ago and one six weeks ago — and the math won't work. Robert Jordan's editorial team kept literal day-by-day calendars for the Wheel of Time. This is that function.

**Workflow phase**: Phase 1 (establish in-world calendar), Phase 2 (plot chronology), Phase 3 (chapter-level timing), monitored throughout all phases

**Core tasks**:
- Maintain `pov_chronological_position`: the in-world day number for each POV character at each chapter
- Maintain `events.absolute_day_number` for every event in the story
- Manage time jumps: explicit ("three weeks later") and implicit (seasonal changes, character aging, event references)
- Flag timeline collisions: when two events in different threads can't both be true simultaneously
- Track the in-world calendar: seasons, holy days, political deadlines, celestial events
- Maintain a "time-since" reference: how long ago did [major event] happen from each POV character's perspective?
- Flag when compression of time (a lot happens in a short period) or expansion of time (very little over a long period) creates pacing problems
- Validate `travel_segments`: are the travel durations realistic for the distances and methods established?

**Key context loaded**:
`events`, `pov_chronological_position`, `travel_segments`, `chapters`, `locations`

**Handoff points**:
- Reports timeline conflicts to Continuity Editor for logging
- Reports time-jump issues to Chapter Architect for scene-level fixes
- Feeds chronological data to POV Manager for thread synchronization

**Sample invocations**:
```
"What is the in-world date at the end of each POV thread as of
Chapter 28? Which threads are chronologically ahead of others
and by how much?"

"I'm about to write a time jump of six months in [Character]'s thread.
What should have changed in the world during those six months based
on the established timeline? What events would she have missed?"
```

---

## 9. POV Manager

**Purpose**: Owns the multi-POV architecture — balance, transitions, dramatic irony, thread synchronization, and the reader's information experience across threads.

**Why separate**: Multi-POV is one of the defining technical challenges of epic fantasy. Which POV for which scenes? When do threads converge? What does each POV character know that others don't, and how does the reader's superior knowledge create dramatic irony? At this scale this is a full discipline.

**Workflow phase**: Phase 2, monitored throughout all phases

**Core tasks**:
- Maintain `pov_balance_snapshots`: chapter count and word count per POV character, updated with every new chapter plan
- Flag POV characters absent for too many chapters (reader loses connection)
- Maintain `dramatic_irony_inventory`: what the reader knows that Character A doesn't, because we saw it through Character B
- Assess POV transition quality: when we leave one thread and enter another, is the transition earning its place?
- Track emotional contrast between threads: when threads are intercut, are they creating effective contrast or unintentional tonal clashes?
- Identify scenes where the choice of POV character is wrong — where the story would be better served by a different viewpoint
- Track thread convergence points: when POV threads are about to intersect, ensure both are at the right narrative and emotional position

**Key context loaded**:
`chapters`, `character_arcs`, `pov_balance_snapshots`, `dramatic_irony_inventory`, `pov_chronological_position`

**Handoff points**:
- Receives chronological position data from Timeline Manager
- Feeds dramatic irony inventory to Scene Builder and Prose Writer
- Reports POV balance concerns to Story Architect

**Sample invocations**:
```
"Generate a POV balance chart for all chapters planned so far.
Which character has the most chapters? Which the fewest? Is the
balance aligned with their narrative importance?"

"[Character A] learns the truth about [Event] in Chapter 24.
[Character B] won't learn it until Chapter 35. What scenes between
those chapters could exploit this dramatic irony? Where would a
reader who knows feel the most tension watching [Character B] not know it?"
```

---

# TIER 2: CHARACTER AGENTS

---

## 10. Character Architect

**Purpose**: Builds and maintains all character documentation — complete profiles, emotional state tracking, relationship history, and character reference material.

**Why separate**: Characters are the engine of reader investment. In a 250,000-word novel with dozens of significant characters, keeping each one fully documented is a full-time job. This agent owns the state of each character — where they are physically, emotionally, and relationally at any point in the story.

**Workflow phase**: Phase 1 (initial documentation), maintained throughout all phases

**Core tasks**:
- Create and maintain full character sheets: biography, physical description, voice summary, wounds, wants, needs, fears, beliefs, secrets
- Track each character's emotional state chapter by chapter: what do they currently believe, want, and fear?
- Create "character in context" summaries before any chapter: where is this character emotionally right now?
- Flag characterization drift: when behavior in a new scene doesn't match established psychology
- Create minor character sheets on demand, consistent with their cultural context
- Track physical continuity: injuries, physical markers, clothing, possessions
- Coordinate with Arc Tracker to ensure character state reflects arc progress

**Key context loaded**:
`characters`, `character_arcs`, `character_knowledge`, `character_beliefs`, `injury_states`

**Handoff points**:
- Feeds character state summaries to Scene Builder and Prose Writer
- Feeds relationship data to Relationship Dynamics Manager
- Escalates arc concerns to Arc Tracker
- Feeds physical descriptions to Continuity Editor

**Sample invocations**:
```
"I'm building Chapter 23 from [Character]'s POV. Give me a full
current-state brief: emotional state, active goals, active fears,
key relationship status, physical condition, and what she last
experienced in Chapter 19."

"Create a full character sheet for the new spymaster introduced
in Chapter 20. She's from the Eastern Throne culture. Make her
consistent with the cultural documentation and give her a
psychological wound that will make her interesting over time."
```

---

## 11. Character Voice Auditor

**Purpose**: Ensures every named character has a distinct, consistent, recognizable voice — particularly in dialogue — and monitors for voice drift and voice bleed across the manuscript.

**Why separate**: At 250,000 words you write dialogue for the same characters across 55 chapters and hundreds of writing sessions. Voice drift is inevitable without someone watching for it. This is not the Character Architect's job — that agent tracks psychology and state. Voice Auditor tracks how that psychology expresses itself in speech and thought. A gruff northern soldier should not begin sounding like a court diplomat three chapters after introduction.

**Workflow phase**: Phase 3 (build voice reference cards before prose), Phase 5 (active monitoring during drafting)

**Core tasks**:
- Maintain `voice_profiles` for each major character: vocabulary range, sentence structure tendencies, verbal tics, avoided topics, emotion expression style, humor register
- Build voice reference cards — compact documents the Prose Writer loads before drafting any chapter for that character
- Audit dialogue in any chapter for voice consistency: does each character sound like themselves?
- Flag voice bleed: when two characters start sounding alike because the author's default voice is bleeding through
- Flag voice drift: when a character's speech patterns change without story-justified cause
- Ensure voice evolution is documented: if a character's voice should change due to trauma or growth, track when and why
- Log all findings to `voice_drift_log`

**Key context loaded**:
`voice_profiles`, `characters`, `chapters` (dialogue sections), `voice_drift_log`

**Handoff points**:
- Provides voice reference cards to Prose Writer before each POV chapter
- Reports voice drift to Character Architect
- Reports bleed patterns to Line Editor in Phase 6

**Sample invocations**:
```
"Audit the dialogue for [Character] across Chapters 15, 18, and 22.
Is her voice consistent? Has she started sounding more like the
narrator than herself? Flag any specific lines that feel off."

"[Character A] and [Character B] share three scenes in Chapter 27.
Read their planned dialogue beats and tell me if they're sufficiently
distinct. Could I remove attribution and still know who's speaking?"
```

---

## 12. Relationship Dynamics Manager

**Purpose**: Tracks the evolving state of every significant relationship in the novel and ensures relationship changes are shown on the page rather than asserted.

**Why separate**: Relationships are a primary engine of reader engagement and easy to mismanage at scale. It's common in long fantasy for two characters to be described as close allies in Chapter 40 when the reader hasn't seen them interact meaningfully since Chapter 12. This agent owns the relationship as a living thing — tracking not just status but history, unspoken tensions, and the moments that changed things.

**Workflow phase**: Phase 2 (initial mapping), maintained throughout all phases

**Core tasks**:
- Maintain `character_relationships`: every significant pairing, current status, history of key change moments
- Maintain `relationship_change_events`: log of every significant relationship shift and its cause
- Track the relationship arc for significant pairings: where does each start, where is it now, where is it going?
- Flag relationships that have changed significantly without sufficient on-page justification
- Identify relationships overdue for a shared scene
- Track knowledge asymmetries: what does Character A know about Character B that B doesn't know A knows?
- Provide relationship context briefs for any scene involving two characters who haven't interacted recently

**Key context loaded**:
`character_relationships`, `relationship_change_events`, `characters`, `chapters`

**Handoff points**:
- Feeds relationship context briefs to Scene Builder and Prose Writer
- Reports relationship continuity issues to Continuity Editor
- Feeds relationship arc data to Arc Tracker

**Sample invocations**:
```
"[Character A] and [Character B] haven't shared a scene since
Chapter 11. I'm planning Chapter 29 where they meet again.
Give me a relationship context brief: where they left off, what
has happened to each since, what unresolved tensions exist, and
what each character's posture toward the other should be."
```

---

## 13. Perception Profile Manager *(NEW)*

**Purpose**: Tracks how each character is perceived and interpreted by the other characters around them — the gap between who a character is and who others think they are.

**Why separate**: This is distinct from Character Architect (who the character actually is), Relationship Dynamics Manager (relationship history and status), and Character Knowledge (what characters know as facts). Perception profiles capture the constructed image each character has of another — the interpretation layer. In a multi-POV novel this is structurally critical, because the reader assembles a picture of each character from multiple limited and often contradictory perspectives simultaneously. The gap between who Sabine is and who Hael thinks she is — that gap is where dramatic irony, betrayal, and revelation live.

**Workflow phase**: Phase 2 (initial mapping), Phase 3 (scene-level application)

**Core tasks**:
- Maintain `perception_profiles`: for every significant perceiver-perceived pair, track perceived role, threat level, trustworthiness, perceived motivations, perceived capabilities, and key misconceptions
- Track when perception profiles are updated: what events shift how one character sees another?
- Identify perception gaps with high dramatic potential: where is the biggest difference between who a character is and who others think they are?
- Flag scenes where a character acts on a false perception — ensure this is intentional and tracked
- Coordinate with POV Manager on scenes where dramatic irony is rooted in perception gaps
- Generate perception context briefs for scenes involving characters with significant gaps between their perception of each other and reality

**Key context loaded**:
`perception_profiles`, `characters`, `character_relationships`, `character_knowledge`, `chapters`

**Handoff points**:
- Feeds perception context briefs to Scene Builder and Prose Writer
- Feeds perception gap inventory to POV Manager for dramatic irony tracking
- Reports perception shifts to Relationship Dynamics Manager

**Sample invocations**:
```
"Generate a perception profile for how [Character A] currently sees
[Character B] as of Chapter 18. What does she believe about his
motivations? What is she wrong about? Where is the gap largest?"

"Which character in the novel is most significantly misperceived by
the most other characters? Map the gap between who they are and
who others think they are."
```

---

# TIER 3: WORLD AGENTS

---

## 14. World Architect

**Purpose**: Creates, expands, and maintains all worldbuilding documentation — geography, nations, factions, cultures, customs, and the physical rules of the world.

**Why separate**: Worldbuilding in epic fantasy is a domain unto itself. The world is a character. At 250,000 words it needs as much documentation as the actual characters. This agent is the keeper of the physical and cultural reality of the world.

**Workflow phase**: Phase 1, maintained throughout

**Core tasks**:
- Generate full documentation for any location, nation, faction, or culture from a high-level prompt
- Maintain geographic consistency: travel times, distances, seasonal weather, terrain effects on plot
- Build faction documentation: power structure, military capacity, economic base, political goals, relationship to other factions
- Build cultural documentation: customs, foods, architecture, clothing, social hierarchy, attitudes toward magic and outsiders
- Answer "what would this culture do in this situation?" questions
- Identify worldbuilding gaps before chapters are architected: what needs to be known about this location that isn't documented yet?
- Maintain internal consistency: if one nation has banned magic and another relies on it, what does that tension look like at the borders?

**Key context loaded**:
`locations`, `factions`, `cultures`, `eras`, `characters` (cultural affiliations)

**Handoff points**:
- Feeds location and culture data to Scene Builder and Sensory Specialist
- Feeds faction data to Political Systems Analyst
- Feeds religion and mythology to Magic System Engineer and Supernatural Voice Specialist

**Sample invocations**:
```
"Expand the Northern Confederacy into a full faction document covering
government, military, economy, and their view of the magic system.
Make it consistent with what's established in the geography document."

"I'm building scenes in [City]. What sensory details are established
about this city? What's missing that I should define before the
Scene Builder constructs those scenes?"
```

---

## 15. Magic System Engineer

**Purpose**: Owns the magic system as a technical document — its rules, costs, limits, interactions, and edge cases — and enforces it like a contract with the reader.

**Why separate**: Magic in epic fantasy is a promise to the reader. In a 250,000-word novel your magic system will be invoked dozens of times in ways you didn't anticipate when you designed it. This agent treats the magic system like a codebase — rules that can't be violated, edge cases that need documentation, new applications that must be evaluated for consistency. Too precise and consequential a job for the World Architect.

**Workflow phase**: Phase 1, enforced throughout all phases

**Core tasks**:
- Maintain `magic_system_elements` as the authoritative source
- Evaluate any proposed magical action against established rules: is this legal? does it violate limits?
- Maintain `practitioner_abilities`: what each character can and can't do, at what level, with what access type
- Log all magic use to `magic_use_log` with compliance assessment
- Document edge cases as they arise
- Flag magic use in chapter plans that violates established rules
- Identify and document consequences of magic use that should appear later
- Evaluate new magic system elements proposed during architecture: are they consistent with the system's internal logic?
- Ensure magic isn't solving problems that should require non-magical ingenuity

**Key context loaded**:
`magic_system_elements`, `practitioner_abilities`, `magic_use_log`, `characters`

**Handoff points**:
- Enforces magic rules for Scene Builder and Prose Writer
- Reports violations to Continuity Editor for logging
- Feeds practitioner data to Character Architect

**Sample invocations**:
```
"In Chapter 28's scene plan, [Character] uses flame-calling
sustained for an hour rather than the established seconds.
Is this consistent with the system? If not, what is the minimum
rules change that would allow it without breaking anything else?"

"I want to introduce a new form of magic in Act 3 that allows
limited precognition. Evaluate this against the existing system.
What rules would govern it to keep the system internally consistent?"
```

---

## 16. Political Systems Analyst

**Purpose**: Maintains the dynamic political map — alliances, rivalries, power dynamics — and tracks how political reality shifts as the story's events unfold.

**Why separate**: Epic fantasy political intrigue is a system as complex as the plot itself. Factions have goals, and their behavior must be consistent with those goals. When a nation makes a political decision in Chapter 20, that decision should have visible consequences by Chapter 30. The World Architect handles static documentation; this agent tracks the dynamic, shifting political reality.

**Workflow phase**: Phase 1 (initial political map), Phase 2 (political arc), maintained throughout

**Core tasks**:
- Maintain `faction_political_states` by chapter: current strength, territory, leadership, alliances, conflicts
- Track political consequences: when a political event occurs, update the political map
- Model faction behavior: given a faction's established goals and the current political reality, how would they respond to a given event?
- Identify political inconsistencies: a faction acting against established interests without sufficient cause
- Track political arcs: nations and factions have arcs just as characters do
- Maintain awareness of political information asymmetries: what does each POV character know about the current political reality?
- Provide political context briefs before chapters involving political maneuvering

**Key context loaded**:
`factions`, `faction_political_states`, `events`, `title_states`, `characters` (political roles), `chapters`

**Sample invocations**:
```
"After the events of Chapter 24, where [Faction A] publicly broke
their alliance with [Faction B], update the political map. What are
the likely immediate responses from each other faction? Which POV
characters would realistically know about this within the next
3 chapters?"
```

---

## 17. Names and Linguistics Specialist

**Purpose**: Maintains the internal linguistic consistency of the world — naming conventions by culture, place name rules — and audits the manuscript for naming confusion and cultural inconsistency.

**Why separate**: In epic fantasy, names do enormous work. In a 250,000-word novel you will name hundreds of characters, places, and things. Without deliberate management, you'll end up with a Kael and a Kaelor and a Kaelan in the same book, a character from a cold northern culture with a soft Mediterranean-sounding name, and a city name that doesn't fit the region's phoneme patterns. Small job on a short book. Full discipline at this scale.

**Workflow phase**: Phase 1, enforced throughout all phases

**Core tasks**:
- Maintain `name_registry`: every name in the project with cultural attribution, phoneme pattern, and similarity flags
- Maintain naming conventions for each culture in `cultures.naming_style` and `cultures.naming_examples`
- Audit new names for cultural consistency before they're committed
- Flag names too similar to existing names (the Kael/Kaelor/Kaelan problem)
- Create names on demand that are consistent with a given culture's conventions
- Track linguistic evolution: if there are ancient and modern versions of a language, ensure the differences are consistent
- Flag anachronistic naming — names that feel like they come from a different cultural context than intended

**Key context loaded**:
`name_registry`, `cultures`, `characters` (name fields), `locations`

**Sample invocations**:
```
"I need five new character names for minor nobility from the Northern
Confederacy. Check the existing naming conventions and generate names
that fit the pattern without duplicating or closely resembling anything
already in the registry."

"Audit Chapter 18's scene plans for any new names introduced. Add them
to the registry and flag any that conflict with or too closely resemble
existing names."
```

---

# TIER 4: CANON AND CONTINUITY AGENTS

---

## 18. Canon Keeper

**Purpose**: The authoritative source of truth for everything established in the story — what is real in this world, what has been decided, and where it was established.

**Why separate from Continuity Editor**: Canon Keeper is a reference librarian — it knows what is true and where to find it. Continuity Editor is a quality inspector — it reads new work and checks it against what is true. One maintains the record; the other audits against it. Different jobs.

**Workflow phase**: Phase 1, active throughout all phases

**Core tasks**:
- Maintain `canon_facts` as the single authoritative record of established truth
- Maintain `decisions_log`: every significant creative decision with rationale and alternatives considered
- Answer "is this established?" questions with citations: "yes, established in Chapter 4, documented in canon_facts id 237"
- When a mid-draft decision changes established canon, document the change and identify all affected documents
- Distinguish between hard canon (committed to manuscript), soft canon (in documentation but not yet in manuscript), and provisional decisions (made but not yet documented)
- When asked "what do we know about X?" compile all relevant established facts from across the database

**Key context loaded**:
Everything. Canon Keeper needs the broadest read access of any agent.

**Sample invocations**:
```
"What is canonically established about the religion of the Eastern
Throne? I need everything — what's in the story bible, what's in
chapter plans, and anything decided but not yet documented."

"I've decided to change the magic system's cost mechanism from
stamina-based to blood-based. What needs to change across the
database and story bible? Give me a complete impact list."
```

---

## 19. Continuity Editor

**Purpose**: Active quality inspector. Reads new chapter plans and scene briefs and checks them against all established facts for contradictions, inconsistencies, and rule violations.

**Workflow phase**: Phase 3 (checks architecture), Phase 4 (gate review), Phase 6 (checks prose)

**Core tasks**:
- Audit any chapter plan or scene brief against character descriptions, names, locations, timeline, and magic rules
- Cross-reference all proper nouns against `name_registry`
- Check timeline consistency against `pov_chronological_position` and `events`
- Check character knowledge: does a character reference something they shouldn't know yet?
- Check physical continuity: injuries, objects, clothing, physical markers
- Check magic use against `magic_use_log` and `magic_system_elements`
- Log all identified issues to `continuity_issues` with severity rating
- Produce a clear contradiction report after each audit, prioritized by severity
- In Phase 6, repeat all checks against actual prose

**Key context loaded**:
Everything. Same broad access as Canon Keeper, used differently — reads new content against existing fact.

**Sample invocations**:
```
"Run a full continuity audit on the Chapter 22 scene plans.
Cross-reference against character sheets, name registry, master
timeline, magic system rules, and the last chapter for each
POV character present. Log all issues to continuity_issues."
```

---

## 20. Foreshadowing and Prophecy Tracker

**Purpose**: Tracks everything planted in the story that implies a future payoff — foreshadowing, prophecies, promises, symbols — and ensures every planted element is eventually paid off.

**Why separate**: A prophecy mentioned in Chapter 3 might not be fulfilled until Chapter 52. A symbol introduced in the prologue might not resolve until the final chapter. At 250,000 words, seeds planted in Act 1 are genuinely easy to forget by Act 3. This agent exists specifically to prevent the unfired Chekhov's Gun at the literary level — which is distinct from Plot Systems Engineer's mechanical tracking.

**Workflow phase**: Phase 2 (register all planted elements), Phase 3 (verify payoffs are architecturally placed), Phase 4 (gate review), Phase 6 (prose verification)

**Core tasks**:
- Maintain `foreshadowing_registry`: every instance of foreshadowing, what it implies, payoff status
- Maintain `prophecy_registry`: exact text, current interpretation, true interpretation, fulfillment status
- Flag unpaid foreshadowing as the manuscript progresses
- Flag payoffs that lack sufficient setup — resolutions that feel unearned because seeds weren't planted early enough
- Track when in-world characters reinterpret a prophecy — log in `prophecy_registry.reinterpretation_events`
- Coordinate with Plot Systems Engineer on foreshadowing that overlaps with mechanical setup

**Key context loaded**:
`foreshadowing_registry`, `prophecy_registry`, `chapters`, `scenes`, `chekovs_gun_registry`

**Sample invocations**:
```
"Audit all chapter plans for foreshadowing and prophecy elements.
Give me a complete registry with each item, where it appears, what
it implies, and whether it's been paid off in the outline."

"I'm planning Chapter 45. Which planted elements from Acts 1 and 2
should be approaching their payoff at this stage? What am I in
danger of leaving unpaid?"
```

---

## 21. Symbolism and Motif Tracker

**Purpose**: Tracks the literary layer of the novel — recurring images, symbols, motifs, and thematic echoes — ensuring they're being used deliberately and building toward meaning.

**Why separate**: This is distinct from Foreshadowing Tracker (narrative) and Arc Tracker (structural). Symbolism is literary. The recurring image of a character always being cold, or windows appearing at every major decision point — these are the details that make a good novel feel like a great one on reread. At this scale they need deliberate tracking or they'll be inconsistent.

**Workflow phase**: Phase 2 (identify and register intentional motifs), Phase 3 (mark occurrence points in scene briefs), Phase 6 (prose verification)

**Core tasks**:
- Identify recurring images, symbols, and motifs in the architecture documents
- Maintain `motif_registry` with motif type, thematic connection, and intended evolution
- Maintain `motif_occurrences` with every planned occurrence and its contextual meaning
- Identify opportunities to reinforce established motifs in upcoming scenes
- Flag motif breaks: when an established symbol appears in a context that undermines its established meaning
- Track motif evolution: a symbol can deliberately change meaning over the novel, but that evolution must be intentional
- Connect symbolic patterns to thematic throughlines

**Key context loaded**:
`motif_registry`, `motif_occurrences`, `chapters`, `scenes`

**Sample invocations**:
```
"Review the chapter plans for Acts 1 and 2 and identify any recurring
images or symbols used consistently. Compile a motif registry with
every occurrence. I want to know what I'm already doing before I
decide what to do deliberately."
```

---

## 22. Thematic Architecture Agent *(NEW)*

**Purpose**: Manages the deliberate structural symmetry of the novel — characters as mirrors or foils, thematic oppositions manifesting across all story layers — ensuring the novel's central opposition is woven into its architecture, not just its surface content.

**Why separate**: Arc Tracker handles arc shape. Story Architect handles throughline. Neither manages deliberate structural symmetry. Based on your existing project files (`Thematic-Mirror-Map.md`, `Opposition-Pair-Manifestations.md`), you're already building something more rigorous than what those agents cover: tracking how characters are deliberately constructed as mirrors or foils, and how the central thematic opposition (Mercy vs. Order) manifests not just in characters but in locations, factions, events, and objects. This is a sophisticated literary layer that needs its own agent.

**Workflow phase**: Phase 2

**Core tasks**:
- Maintain `thematic_mirrors`: every significant foil or parallel pairing in the novel — characters, plot threads, locations, factions — with the mirror type and thematic function
- Maintain `opposition_pairs`: how the central thematic opposition manifests at every level of the story — which characters, locations, events, factions, and objects embody each pole
- Identify characters or elements that currently lack a thematic counterpart and assess whether one is needed
- Ensure thematic architecture is balanced: the "order" pole should be as complex and humanized as the "mercy" pole
- Track how the opposition evolves: does the novel's climax achieve synthesis, affirm one pole, or complicate the opposition without resolving it?
- Coordinate with Arc Tracker to ensure character arcs are aligned with their thematic function
- Coordinate with Symbolism Tracker to ensure motifs are supporting the thematic architecture

**Key context loaded**:
`thematic_mirrors`, `opposition_pairs`, `character_arcs`, `plot_threads`, `locations`, `factions`

**Sample invocations**:
```
"Map the current thematic mirror structure. Which character pairings
are explicitly functioning as foils? Which locations embody opposing
poles of the central conflict? Is the opposition balanced — are both
poles being given sufficient complexity?"

"I'm introducing a new faction in Act 2. Where should it sit in the
thematic architecture? Does it embody one pole of the central
opposition, or does it complicate the opposition itself?"
```

---

## 23. Information State Tracker *(NEW)*

**Purpose**: Maintains a live, cumulative accounting of exactly what the reader knows at the end of each chapter — distinct from what characters know — and ensures the information revelation architecture is working as designed.

**Why separate**: The Reader Experience Simulator reads as a first-time reader and flags confusion. That is a diagnostic tool. Information State Tracker is a maintenance tool — it actively updates a formal record of reader knowledge state at each chapter boundary. In a multi-POV novel where dramatic irony is a structural mechanism, this document is not a periodic check. It's a living database that must be current at all times. Your existing `Information-State.md` file in the Structure folder indicates you already know you need this.

**Workflow phase**: Phase 2 (establish information flow plan), Phase 3 (verify chapter-by-chapter), maintained in Phase 5 and 6

**Core tasks**:
- Maintain `reader_information_states`: after each chapter, a record of what the reader knows, suspects, has confirmed, and is still being withheld from
- Track `active_mysteries`: questions the reader is currently holding
- Track `active_dramatic_ironies`: what the reader knows that specific characters don't, cross-referenced with `dramatic_irony_inventory`
- Flag information dumps: when too much is delivered too fast for the reader to absorb
- Flag information deserts: when the reader is left without enough context to engage
- Assess mystery maintenance: when information is being withheld deliberately, is it being withheld fairly?
- Coordinate with POV Manager to ensure dramatic irony tracking is synchronized

**Key context loaded**:
`reader_information_states`, `reader_reveals`, `character_knowledge`, `dramatic_irony_inventory`, `chapters`

**Sample invocations**:
```
"Update the reader information state through Chapter 18. What does
the reader definitively know, what do they suspect, what mysteries
are they actively holding, and what are they being deliberately
kept from?"

"[Character A] reveals [secret] to [Character B] in Chapter 22.
The reader already knows this secret from Chapter 14. Update the
information state and the dramatic irony inventory."
```

---

# TIER 5: PROSE AND CRAFT AGENTS

*Note on tier placement: Chapter Architect, Scene Builder, Battle and Action Coordinator, and the planning-layer work of Dialogue Specialist and Chapter Hook Specialist belong to the architecture phases. The agents in this tier are either architecture-phase (Sensory Specialist, Supernatural Voice Specialist building the style guides) or prose-execution-phase (Prose Writer, Dialogue Specialist line-level, Character Voice Auditor active monitoring).*

---

## 24. Prose Writer

**Purpose**: The primary drafting agent. Writes scenes and chapters from pre-built, fully approved scene briefs and chapter plans.

**Critical constraint**: This agent never invents worldbuilding facts, names, or established story elements. If something isn't in the database or story bible, it stops and flags rather than improvising. It is a skilled craftsperson working inside complete specifications, not a collaborator making architectural decisions.

**Workflow phase**: Phase 5 only. Does not begin work until Architecture Completeness Auditor has certified the gate.

**Core tasks**:
- Draft scenes from fully constructed and approved scene briefs
- Draft full chapters from approved chapter plans
- Apply the prose style defined in `Narrative-Style-Guide.md` and `Prose-Reference.md` consistently
- Load voice reference cards from `voice_profiles` for any POV character being drafted
- Apply `supernatural_voice_guidelines` for any scenes involving supernatural elements
- Load sensory profile from `locations.sensory_profile` for location grounding
- Load the dramatic irony inventory for the current chapter — know what the reader knows
- Flag any specification gap encountered during drafting: missing worldbuilding, underspecified scene brief, unclear obligation — stop and escalate, never improvise

**Key context loaded**:
The chapter plan and scene briefs for the current chapter, relevant character sheets and voice reference cards, relevant location documents, `Narrative-Style-Guide.md`, `dramatic_irony_inventory` (current chapter), the last chapter written in this POV thread for narrative momentum

**Sample invocations**:
```
"Draft Chapter 19 Scene 2 using the approved scene brief. POV is
[Character]. Location is [Place]. The emotional register is cold fury,
not hot anger — she's past the point of yelling. Target 1,800 words.
If anything in the brief is underspecified, flag it rather than inventing."
```

---

## 25. Dialogue Specialist

**Purpose**: Owns dialogue quality at two levels — beat planning during architecture (what needs to be said, what the subtext is) and line-level prose quality during drafting.

**Why separate**: Voice Auditor ensures each character sounds like themselves. Dialogue Specialist ensures conversations are doing real work — that they have subtext, conflict, and function. Dialogue can be perfectly voiced and still be flat if every line is on-the-nose. At 250,000 words you may have 60,000+ words of dialogue.

**Workflow phase**: Phase 3 (beat planning as part of scene construction), Phase 5 (line-level quality during drafting)

**Core tasks**:
Architecture phase (Phase 3):
- Plan dialogue beats for every significant conversation in the scene briefs: what each character needs to communicate, what they're concealing, what the subtext is
- Identify on-the-nose dialogue traps in scene plans and design around them

Prose phase (Phase 5 and 6):
- Evaluate dialogue scenes for subtext: is what's being said and what's being meant sufficiently layered?
- Flag on-the-nose exchanges: conversations where characters say exactly what they mean
- Evaluate dialogue rhythm: does the conversation feel like a real exchange or a series of speeches?
- Identify exposition dumps disguised as dialogue
- Assess dialogue conflict: in every conversation, what does each character want and what prevents direct achievement?

**Key context loaded**:
`voice_profiles`, `scene_character_goals`, `characters`, relevant chapter/scene

**Sample invocations**:
```
"Evaluate the planned dialogue beats for Scene 3 of Chapter 16 —
the negotiation between [Character A] and [Character B]. Is there
sufficient subtext in the plan? Can you identify any on-the-nose
traps? Redesign the weakest three exchanges."
```

---

## 26. Battle and Action Coordinator

**Purpose**: Manages the spatial, tactical, and narrative coherence of large-scale action sequences — battles, chases, confrontations — where multiple parties are moving through space simultaneously.

**Why separate — and why this is an architecture-phase agent**: Action sequences at scale are a spatial and logical puzzle. A battle involving three armies, four POV characters, and a dozen named combatants, unfolding over three chapters, must be fully mapped before the Prose Writer touches it. Geographic violations, character position errors, and casualty continuity failures are nearly impossible to fix in prose — they must be solved in architecture.

**Workflow phase**: Phase 3 (construct all battle and action specs), Phase 5 (Prose Writer references the spec)

**Core tasks**:
- Build spatial maps (prose descriptions) of battle or action locations before scene construction
- Track combatant positions throughout multi-part action sequences
- Maintain a casualty and status log during battle sequences: who is injured, dead, or missing, and when
- Ensure tactical coherence: the actions taken by armies and individuals should make military or physical sense
- Track resource states during action: magical energy, stamina, time
- Manage the action sequence across POV threads: if the same battle is seen through three perspectives, ensure spatial and chronological consistency
- Evaluate action sequences in plans for pacing: too detailed is as problematic as too vague
- Coordinate with Timeline Manager to nail the chronology of battle events

**Key context loaded**:
Relevant world geography and location documents, `characters` (physical capabilities, `injury_states`), `magic_system_elements`, `pov_chronological_position`

**Sample invocations**:
```
"I'm architecting the Battle of [Location] across Chapters 31–33
with three POV characters. Before Scene Builder constructs those
scenes, help me map the battlefield: terrain, positions of each
force, timeline of major tactical events, and where each POV
character will be at each stage."
```

---

## 27. Sensory and Atmosphere Specialist

**Purpose**: Ensures every significant location has a consistent, vivid, fully realized sensory presence — and that the novel's atmosphere is actively maintained rather than left to default.

**Why separate**: It's common in long novels for settings to become increasingly abstract as the author focuses on plot and character. By Chapter 30, a city richly rendered in Chapter 3 gets reduced to "the marketplace" with no sensory grounding. This agent maintains the sensory layer.

**Workflow phase**: Phase 1 (build sensory profiles for all major locations), Phase 3 (mark sensory requirements in scene briefs), Phase 5 (monitoring during prose)

**Core tasks**:
- Build and maintain `locations.sensory_profile`: what each major location smells like, sounds like, feels like, looks like in different seasons and times of day
- Audit scene briefs for sensory requirements: does the Prose Writer know where they are in a physical, sensory way?
- Flag atmosphere breaks: when a scene's setting undercuts rather than supports its emotional register
- Identify opportunities to use setting as emotional mirror or ironic contrast
- Ensure weather, time of day, season, and environmental conditions are consistent across chapters in the same location
- Flag sensory inconsistencies between chapters

**Key context loaded**:
`locations` (sensory_profile), `chapters`, `scenes`

**Sample invocations**:
```
"I'm about to build scenes in [City]. Pull everything established
about this city's sensory character and give me a rich reference
document — light quality, sounds, smells, architectural texture.
I need this before Scene Builder constructs those scenes."
```

---

## 28. Supernatural Voice Specialist *(NEW)*

**Purpose**: Owns the prose texture and register of supernatural elements — how the supernatural sounds and feels on the page — distinct from what it can do (Magic System Engineer) or what rules govern it (Magic System Engineer and Supernatural Elements table).

**Why separate**: Your existing `Supernatural-Voice-Guide.md` in the Style folder is distinct from `Supernatural-Constraints.md` in your World folder — and that distinction is architecturally correct. The Constraints document is about rules. The Voice Guide is about prose texture: does supernatural presence get its own sentence rhythm? Its own register? Does it intrude on normal prose or exist in a separate stylistic layer? Nobody else owns this. At a novel with a dedicated guide for it, you need an agent maintaining it.

**Workflow phase**: Phase 1 (establish guidelines), Phase 3 (mark supernatural scenes in briefs), Phase 5 (active monitoring during prose)

**Core tasks**:
- Build and maintain `supernatural_voice_guidelines`: prose register, sentence structure, vocabulary restrictions, sensory texture, rhythm, and contrast with normal prose for each category of supernatural element
- Create supernatural voice reference documents for the Prose Writer to load before any supernaturally-inflected scene
- Audit scene briefs for scenes involving supernatural elements: are the voice requirements specified?
- Flag supernatural voice breaks in prose: when a supernatural scene collapses into the same register as ordinary narration
- Ensure the supernatural voice evolves appropriately: if a character's relationship to the supernatural changes, their experience of it should sound different
- Coordinate with Character Voice Auditor on how a character's voice changes when they're in contact with supernatural elements

**Key context loaded**:
`supernatural_elements`, `magic_system_elements`, `supernatural_voice_guidelines`, `Supernatural-Voice-Guide.md`, `Narrative-Style-Guide.md`

**Sample invocations**:
```
"Scene 4 of Chapter 22 involves [Character]'s first direct
contact with [Supernatural Element]. Build the supernatural voice
reference for this scene: what register should the prose shift to,
what sensory texture should dominate, how should the sentence
structure change to signal the reader that something has crossed
into a different order of reality?"
```

---

# TIER 6: EDITORIAL AGENTS

---

## 29. Developmental Editor

**Purpose**: Big-picture story feedback — the editor's eye that reads the whole book and asks whether it's working as a story, not just as a sequence of well-constructed chapters.

**Workflow phase**: Phase 4 (gate review of architecture), Phase 6 (manuscript review)

**Core tasks**:
- Evaluate whether each act is fulfilling its narrative function
- Assess whether the protagonist's agency is sufficient — the reader should feel the protagonist is driving events
- Identify chapters that are present but not earning their place
- Evaluate the story's central dramatic question: is it always clear what the story is about?
- Assess the emotional journey: are readers being moved, challenged, and satisfied at the right points?
- Evaluate chapter balance: is one POV thread significantly stronger in reader engagement than others?
- Assess the ending: does the resolution honor the story's premise and the reader's investment?
- In Phase 4: review the complete architecture and flag structural problems before prose begins

**Key context loaded**:
`chapters` (summaries and plans), `acts`, `character_arcs`, `plot_threads`

**Sample invocations**:
```
"Review the complete chapter plan architecture for Act 2.
I'm worried the midpoint doesn't hit hard enough and that
[Character B]'s thread feels passive. Give me a developmental
assessment before I take this to the gate."
```

---

## 30. Line Editor

**Purpose**: Prose-level quality — sentence structure, word choice, rhythm, clarity, and the author's voice at the sentence level.

**Workflow phase**: Phase 6

**Core tasks**:
- Identify repetitive sentence structures and rhythms
- Flag overused words or phrases (learn and track your personal patterns)
- Tighten action beats and dialogue attribution
- Identify telling vs. showing at the sentence level
- Reduce adverb reliance where it masks weak verb choices
- Improve clarity in complex action and magic sequences
- Maintain the author's voice while improving the prose
- Track the author's personal tics across the manuscript and generate a watch list
- Receive pacing mismatches from Pacing and Tension Analyst and address at the sentence level

**Key context loaded**:
`Narrative-Style-Guide.md`, `Prose-Reference.md`, `voice_profiles`, the specific chapter being edited

---

## 31. Copy Editor

**Purpose**: Mechanical correctness — grammar, punctuation, spelling, formatting consistency, and style guide adherence.

**Why separate from Line Editor**: Line Editor is a craft role — it improves the prose. Copy Editor is a technical role — it enforces correctness and consistency. These are genuinely different jobs. A Copy Editor should not be improving sentences. It should be catching that you spelled a character's name two different ways, that your chapter heading format changed in Act 2, and that you've been comma-splicing in action sequences.

**Workflow phase**: Phase 6 (after Line Editor)

**Core tasks**:
- Grammar and punctuation correctness
- Spelling consistency against `name_registry` (especially invented words, names, and places)
- Style guide adherence — house rules for fantasy-specific formatting
- Formatting consistency across all chapters
- Hyphenation consistency for compound adjectives and invented terms
- Consistency in capitalization of magic terms, titles, and cultural terms

**Key context loaded**:
`name_registry`, `canon_facts` (terminology), `Narrative-Style-Guide.md`

---

## 32. Reader Experience Simulator

**Purpose**: Reads the manuscript as a first-time reader — someone who only knows what they've been told up to that point — and identifies confusion, information gaps, and pacing problems from a reader's perspective.

**Why separate**: Every other agent reads with full knowledge of the story. This one reads with only the information a reader would have at each point. It asks: is the reader confused here? Do they have enough information to follow what's happening? This is one of the most valuable perspectives in review and is completely absent from the rest of the roster.

**Workflow phase**: Phase 4 (architecture review), Phase 6 (manuscript review)

**Core tasks**:
- Read chapter plans sequentially and flag moments of reader confusion
- Track the reader's information state — what does a reader know after Chapter X?
- Identify information dumps: too much delivered too fast
- Identify information deserts: too little context to engage
- Assess mystery maintenance: when information is withheld deliberately, is it being withheld fairly?
- Identify reader reward points: moments that pay off earlier setup satisfyingly
- Simulate reader questions: "at this point, a reader is probably wondering..."
- Write findings to `reader_experience_notes`

**Key context loaded**:
`reader_information_states`, `chapters` (read sequentially — never jumps ahead), `reader_reveals`

---

## 33. Chapter Hook Specialist

**Purpose**: Focused exclusively on chapter openings and chapter endings — the two most mechanically important sentences in every chapter.

**Why separate**: At 55 chapters you have 55 chapter openings that need to pull a reader in and 55 chapter endings that need to make them turn the page. These are a craft micro-discipline. A great chapter ending doesn't just end — it asks a question, creates a revelation, shifts an assumption, or raises stakes in a way that makes stopping feel wrong.

**Workflow phase**: Phase 3 (spec the hooks as part of chapter architecture), Phase 6 (verify in prose)

**Core tasks**:
- Evaluate every chapter plan's opening and closing beats: do they work as hooks?
- Evaluate chapter ending variety: are all endings the same type (cliffhanger, revelation, reflection)? Variety matters.
- Ensure chapter openings orient the reader quickly: POV, location, emotional register within the first paragraph
- Flag chapter endings that are natural stopping points — dangerous in long novels
- Suggest alternative opening and closing approaches when current versions are weak
- Write hook ratings to `chapters.hook_strength_rating` during Phase 3 review
- Update ratings in Phase 6 once prose is rendered

**Key context loaded**:
`chapters` (opening and closing beats from plans), `pacing_beats`

---

# TIER 7: RESEARCH AND REFERENCE AGENTS

---

## 34. Research Agent

**Purpose**: Provides real-world research to support and ground worldbuilding decisions, using web search and synthesis.

**Workflow phase**: Phase 1 (primary research for worldbuilding), on demand throughout all phases

**Core tasks**:
- Research historical analogs for political systems, military tactics, architecture, medicine
- Research cultural practices, religious structures, trade systems, agricultural realities
- Compile research summaries for worldbuilding decisions — written to `research_notes`
- Flag when a worldbuilding choice diverges significantly from any real-world analog
- Answer "what would actually happen if..." questions from a real-world basis
- Log all open research questions to `open_questions`

**Key context loaded**:
`research_notes`, `open_questions`, web search

---

## 35. Genre Analyst

**Purpose**: Studies the competitive landscape of epic fantasy — comp titles, genre conventions, reader expectations — to ensure the novel is making informed decisions about where it sits in the genre.

**Why separate**: Research Agent handles real-world facts. Genre Analyst handles genre-specific craft and market awareness. Knowing how medieval sieges actually worked is Research Agent's job. Knowing how Abercrombie, Rothfuss, and Sanderson have handled siege sequences — and what readers expect — is Genre Analyst's job.

**Workflow phase**: Phase 1 (initial genre positioning), Phase 7 (comp analysis for publishing)

**Core tasks**:
- Maintain comp title analysis: what the 3–5 closest comparable books do well, where they have weaknesses, what this novel does similarly or differently
- Track genre conventions: what epic fantasy readers expect, and where those expectations can be productively subverted
- Evaluate specific craft decisions against genre norms
- Assess the novel's market positioning: where does it sit in the current genre landscape?
- In Phase 7: provide comp analysis for the query letter and publishing assets

**Key context loaded**:
`publishing_assets`, `characters`, `plot_threads`, web search

---

# TIER 8: PROJECT MANAGEMENT AGENTS

---

## 36. Architecture Completeness Auditor *(NEW — Gate Agent)*

**Purpose**: Certifies that the architecture is 100% complete before a single prose sentence is written. This is the gate. Nothing in Phase 5 begins without this agent's explicit certification.

**Why separate**: No other agent owns the gate. Every other agent produces or maintains specific documents. This one reads across everything and asks: is anything missing, underspecified, or unresolved? Its output is binary — certified or not certified — with a detailed gap report if not.

**Workflow phase**: Phase 4 — this agent's work IS Phase 4. It does not operate outside this phase except for re-certification after major architectural revisions.

**Core tasks**:
- Audit every chapter in `chapters` for complete, approved chapter plans
- Audit every scene in `scenes` for fully constructed, approved scene briefs
- Verify every POV character has a current-state brief for every chapter they appear in via `character_arcs` and `characters`
- Verify every location used in the manuscript has a complete sensory profile in `locations`
- Verify every named character has a complete sheet in `characters`
- Verify every magic use in scene plans is logged in `magic_use_log` as compliant
- Verify the master timeline is complete and contradiction-free via `pov_chronological_position` and `events`
- Verify the `chekovs_gun_registry` has planned payoffs for all planted elements
- Verify all subplots have complete lifecycle plans via `plot_threads` and `chapter_structural_obligations`
- Verify the arc registry shows a complete shape for every major arc in `character_arcs`
- Verify `reader_information_states` is current through the final chapter
- Verify `open_questions` has no items marked `blocking`
- Verify `continuity_issues` has no items marked `critical` or `major` that are unresolved
- Populate `gate_checklist_items` with pass/fail status for each item
- Issue either an Architecture Completeness Certificate (update `architecture_gate.status` to `passed`) or a gap report listing exactly what still needs work

**Key context loaded**:
Everything. This agent needs complete read access to the entire database.

**Sample invocations**:
```
"Run the full architecture gate audit. Check every checklist item
and produce either a certificate of completeness or a prioritized
gap report. Be specific — I need to know exactly what is incomplete,
not just that something is missing."
```

---

## 37. Session Continuity Manager *(NEW)*

**Purpose**: Manages the workflow across sessions — ensuring every Claude Code session begins with a coherent briefing and ends with a clean handoff. Without this, context must be re-established from scratch every session.

**Why separate**: Your existing project already has `Session Log.md`, `Transfer-Protocol.md`, and `Authority-Protocol.md` — you've built the infrastructure for this need. This agent is the process that maintains those documents and ensures no work is lost between sessions.

**Workflow phase**: Active from day one across all phases. The first thing invoked at the start of any session. The last thing invoked at the end.

**Core tasks**:
- At session start: read `session_logs` for the previous session and produce a briefing — what was done, what was decided, what is open, what this session should prioritize
- At session end: write a session log entry documenting what was accomplished, all decisions made (with links to `decisions_log` entries), files modified, chapters worked, and open items carried forward
- Maintain `open_questions` as a live list of unresolved items across all categories
- Maintain the Authority Protocol: which decisions are locked, which are provisional, which are open for debate
- Flag when a session is drifting away from its stated objectives
- Escalate when a decision made in this session conflicts with a locked decision from a prior session
- Generate a "next session recommended starting point" at every session close

**Key context loaded**:
`session_logs`, `decisions_log`, `open_questions`, `documentation_tasks`, `architecture_gate`

**Sample invocations**:
```
"Start session. Give me a briefing from the last session and
recommend priorities for today."

"Close session. I worked on [topics]. I made the following
decisions: [decisions]. The following items are open: [items].
Write the session log and update the open questions list."
```

---

## 38. Project Manager

**Purpose**: Tracks the health of the project as a project — progress metrics, word count targets, completion estimates, and early warning for scope drift.

**Why separate**: The craft agents focus on story. Someone needs to focus on the project. At 250,000 words, understanding whether you're on pace, whether act proportions match targets, and where the biggest remaining work is — these are project questions, not story questions.

**Workflow phase**: Active across all phases

**Core tasks**:
- Maintain `project_metrics_snapshots`: total word count, act breakdown, chapters by status, open issues
- Track POV word count distribution against targets via `pov_balance_snapshots`
- Estimate completion timeline based on current pace
- Flag act proportion drift: if Act 1 is running 30% longer than planned, flag early
- Track architecture debt: chapters and scenes not yet fully constructed
- Track revision debt: chapters flagged for revision vs. chapters considered clean
- Maintain the master open issues list across `continuity_issues`, `arc_health_log`, and `open_questions`
- Generate periodic status reports on project health

**Key context loaded**:
`chapters` (status and word counts), `acts`, `scenes` (status), `continuity_issues`, `project_metrics_snapshots`

---

## 39. Lore Keeper / Story Bible Synchronizer

**Purpose**: Keeps the story bible current as the manuscript evolves — the active maintainer of documentation, not the reference librarian (Canon Keeper).

**Why separate from Canon Keeper**: Canon Keeper is the source of truth — static and authoritative. Lore Keeper is the maintenance process — it actively updates documentation after each writing session. When you write a chapter that introduces three new characters, a new city, and a political status change, someone needs to extract all of that and update the database and regenerate the relevant markdown. That is Lore Keeper's job. Canon Keeper answers questions about what's true; Lore Keeper ensures what's true is documented.

**Workflow phase**: Active from Phase 1 through Phase 6

**Core tasks**:
- After each finalized chapter plan or prose chapter, extract all new lore and update relevant database tables
- Maintain `documentation_tasks`: flag every file or table that needs updating after a change
- When a creative decision changes something established, identify all downstream impacts and queue them in `documentation_tasks`
- Generate markdown exports for changed records via the appropriate export scripts
- Flag documentation gaps: things that exist in chapter plans but haven't been formally documented in the database

**Key context loaded**:
`documentation_tasks`, `canon_facts`, `chapters`, all story bible tables

---

## 40. Publishing Preparation Agent *(NEW)*

**Purpose**: Packages and positions the completed manuscript for submission — query letters, synopses, loglines, elevator pitches, comp analysis, and submission tracking.

**Why separate**: This is a distinct discipline from writing the novel. Query letters, synopses, and loglines are a specialized craft with completely different constraints from prose writing. A synopsis must compress 250,000 words into one page without reading like a plot dump. A query letter must hook a literary agent in the first paragraph. These are not skills the Prose Writer or Developmental Editor own. This entire domain was absent from the original 33-agent roster.

**Workflow phase**: Phase 7

**Core tasks**:
- Write and iterate on the logline: one sentence, the entire story
- Write and iterate on the elevator pitch: one paragraph, the entire story, aimed at an agent
- Write the query letter: following current submission conventions, specific to target agents
- Write the short synopsis (1 page) and long synopsis (5 pages)
- Write back cover copy: commercial, reader-facing, designed to sell
- Maintain `publishing_assets` with versioned drafts of all of the above
- Maintain `submission_tracker` with complete submission history
- Coordinate with Genre Analyst for current comp titles and market positioning
- Research individual agent preferences and tailor submissions accordingly

**Key context loaded**:
`publishing_assets`, `submission_tracker`, `characters`, `plot_threads`, `acts`, `Comps.md`, `Genre-Classification.md`, web search

**Sample invocations**:
```
"Draft a query letter for [Agent Name] at [Agency]. Research their
current preferences and MSWL. The letter should include a one-paragraph
hook, a brief synopsis, and comp titles. Use the approved logline
as the foundation."

"I need a one-page synopsis for submission to [Publisher].
Compress the three-act structure into 500 words without losing
the emotional core of the story."
```

---

# COMPLETE ROSTER SUMMARY

## All 40 Agents by Tier

**Tier 1 — Structural** (9 agents)
1. Story Architect
2. Plot Systems Engineer
3. Subplot Coordinator
4. Chapter Architect *(architecture phase)*
5. Scene Builder *(architecture phase)*
6. Pacing and Tension Analyst
7. Arc Tracker
8. Timeline Manager
9. POV Manager

**Tier 2 — Character** (4 agents)
10. Character Architect
11. Character Voice Auditor
12. Relationship Dynamics Manager
13. Perception Profile Manager *(NEW)*

**Tier 3 — World** (4 agents)
14. World Architect
15. Magic System Engineer
16. Political Systems Analyst
17. Names and Linguistics Specialist

**Tier 4 — Canon and Continuity** (6 agents)
18. Canon Keeper
19. Continuity Editor
20. Foreshadowing and Prophecy Tracker
21. Symbolism and Motif Tracker
22. Thematic Architecture Agent *(NEW)*
23. Information State Tracker *(NEW)*

**Tier 5 — Prose and Craft** (5 agents)
24. Prose Writer
25. Dialogue Specialist
26. Battle and Action Coordinator *(architecture phase)*
27. Sensory and Atmosphere Specialist
28. Supernatural Voice Specialist *(NEW)*

**Tier 6 — Editorial** (5 agents)
29. Developmental Editor
30. Line Editor
31. Copy Editor
32. Reader Experience Simulator
33. Chapter Hook Specialist

**Tier 7 — Research and Reference** (2 agents)
34. Research Agent
35. Genre Analyst

**Tier 8 — Project Management** (5 agents)
36. Architecture Completeness Auditor *(NEW — gate agent)*
37. Session Continuity Manager *(NEW)*
38. Project Manager
39. Lore Keeper / Story Bible Synchronizer
40. Publishing Preparation Agent *(NEW)*

**Total: 40 agents**
**New since Version 1.0: 7 agents (marked NEW above)**

---

## Phase Reference Card

| Phase | Name | Agents Active |
|---|---|---|
| 1 | Foundation Architecture | Story Architect, World Architect, Character Architect, Magic System Engineer, Supernatural Voice Specialist, Timeline Manager, Names Specialist, Political Systems Analyst, Canon Keeper, Research Agent, Genre Analyst, Session Continuity Manager, Project Manager |
| 2 | Structural Architecture | Plot Systems Engineer, Subplot Coordinator, Arc Tracker, POV Manager, Foreshadowing Tracker, Thematic Architecture Agent, Information State Tracker, Relationship Dynamics Manager, Perception Profile Manager, Pacing Analyst, Lore Keeper |
| 3 | Scene and Chapter Architecture | Chapter Architect, Scene Builder, Battle and Action Coordinator, Sensory Specialist, Character Voice Auditor, Dialogue Specialist, Chapter Hook Specialist, Continuity Editor, Lore Keeper |
| 4 | Architecture Gate | Developmental Editor, Reader Experience Simulator, Architecture Completeness Auditor — **HARD STOP** |
| 5 | Prose Execution | Prose Writer, Character Voice Auditor, Dialogue Specialist, Supernatural Voice Specialist, Sensory Specialist, Continuity Editor |
| 6 | Editorial | Developmental Editor, Line Editor, Copy Editor, Reader Experience Simulator, Chapter Hook Specialist, Continuity Editor, Symbolism Tracker, Lore Keeper |
| 7 | Publishing Preparation | Publishing Preparation Agent, Genre Analyst |
| All | Ongoing | Session Continuity Manager, Project Manager, Canon Keeper |

---

## Quick Reference: What Tracks What

| Thing to Track | Primary Agent | Secondary Agent |
|---|---|---|
| Character state (current) | Character Architect | POV Manager |
| Character arc shape | Arc Tracker | Story Architect |
| Character voice | Character Voice Auditor | Prose Writer |
| How others perceive a character | Perception Profile Manager | Relationship Dynamics Manager |
| Relationship history and status | Relationship Dynamics Manager | Character Architect |
| Pacing | Pacing and Tension Analyst | Story Architect |
| Tension curves | Pacing and Tension Analyst | Scene Builder |
| Time jumps | Timeline Manager | Continuity Editor |
| Elapsed time per POV thread | Timeline Manager | POV Manager |
| Cause/effect chains | Plot Systems Engineer | Continuity Editor |
| Planted foreshadowing | Foreshadowing Tracker | Plot Systems Engineer |
| Prophecy fulfillment | Foreshadowing Tracker | Canon Keeper |
| Magic rule violations | Magic System Engineer | Continuity Editor |
| Supernatural prose texture | Supernatural Voice Specialist | Line Editor |
| Political consistency | Political Systems Analyst | World Architect |
| Name conflicts | Names Specialist | Continuity Editor |
| Subplot health and lifecycle | Subplot Coordinator | Plot Systems Engineer |
| Dramatic irony | POV Manager | Information State Tracker |
| Reader knowledge state | Information State Tracker | Reader Experience Simulator |
| Thematic mirror structure | Thematic Architecture Agent | Arc Tracker |
| Opposition pair manifestations | Thematic Architecture Agent | Symbolism Tracker |
| Chapter hooks | Chapter Hook Specialist | Pacing Analyst |
| Battle coherence | Battle and Action Coordinator | Continuity Editor |
| Sensory consistency | Sensory Specialist | World Architect |
| Motif tracking | Symbolism Tracker | Arc Tracker |
| Architecture completeness | Architecture Completeness Auditor | (standalone) |
| Project metrics | Project Manager | (standalone) |
| Session handoff | Session Continuity Manager | (standalone) |
| Bible currency | Lore Keeper | Canon Keeper |
| Submission tracking | Publishing Preparation Agent | Genre Analyst |
