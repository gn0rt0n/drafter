# Epic Fantasy Novel: Claude Code Agent Ecosystem
## A Complete System for a 250,000-Word NYT-Caliber Epic Fantasy

---

## Purpose
Manage a 250,000 word Epic Fantasy Novel, or series of novels, and be abel to maintain continuity across all forms of writing such as timelines, character arcs, knowledge states, etc.

The goal is to build a system where you can ask any agent a question and it already knows the world, the characters, the rules, and the current state of the manuscript.

---

## Directory Structure

This is the foundation everything else builds on. Every major folder gets its own CLAUDE.md so agents working in that scope automatically have the right context loaded.

```
/fantasy-novel/
│
├── CLAUDE.md                          # Master project context (the "God file")
├── .claude/
│   └── settings.json                  # Permissions, allowed tools, MCP config
│
├── manuscript/
│   ├── CLAUDE.md                      # Prose voice, POV rules, chapter conventions
│   ├── chapters/
│   │   ├── act-1/
│   │   ├── act-2/
│   │   └── act-3/
│   ├── scenes/                        # Scene fragments before placement
│   └── drafts/                        # Full draft snapshots by date
│
├── story-bible/
│   ├── CLAUDE.md                      # How to interpret and use story bible materials
│   ├── characters/
│   │   ├── CLAUDE.md                  # Character voice and arc conventions
│   │   ├── pov-characters/            # Full sheets for each POV character
│   │   ├── supporting/
│   │   └── antagonists/
│   ├── world/
│   │   ├── CLAUDE.md
│   │   ├── geography/
│   │   ├── nations-and-factions/
│   │   ├── cultures-and-customs/
│   │   └── maps/                      # Map description files (and image refs)
│   ├── magic/
│   │   ├── CLAUDE.md                  # Magic system rules — treated as law
│   │   ├── system-rules.md
│   │   ├── costs-and-limits.md
│   │   └── known-practitioners.md
│   ├── history/
│   │   ├── CLAUDE.md
│   │   ├── deep-history.md            # Thousands of years back
│   │   ├── recent-history.md          # Last 100 years
│   │   └── in-story-timeline.md       # Events that happen during the novel
│   └── religions-and-mythology/
│
├── outlines/
│   ├── CLAUDE.md
│   ├── master-outline.md              # Full 55-chapter beat-by-beat outline
│   ├── three-act-structure.md
│   ├── pov-threads/
│   │   ├── pov-[character-1].md       # That character's complete arc thread
│   │   └── pov-[character-2].md
│   ├── chapter-plans/                 # Detailed pre-write plans per chapter
│   └── subplot-tracker.md
│
├── continuity/
│   ├── CLAUDE.md                      # Continuity checking rules and standards
│   ├── master-timeline.md             # Every event, every character, in order
│   ├── name-registry.md               # Every name in the book (people, places, things)
│   ├── contradictions-log.md          # Known issues to resolve
│   ├── chapter-summaries/             # One summary per chapter (auto-maintained)
│   └── relationship-map.md            # Who knows whom, when they met, how they feel
│
├── research/
│   ├── CLAUDE.md
│   ├── real-world-analogs/            # Historical parallels, cultural research
│   ├── genre-analysis/                # Comp titles, genre conventions studied
│   └── craft-notes/                   # Narrative technique reference material
│
├── editorial/
│   ├── CLAUDE.md
│   ├── feedback/                      # Notes from beta readers or self-review
│   ├── revision-plans/
│   └── cutting-room/                  # Cut scenes that might return
│
├── agents/
│   ├── README.md                      # How agents are invoked and what they do
│   ├── world-builder.md               # Agent system prompt / instructions
│   ├── character-architect.md
│   ├── plot-architect.md
│   ├── prose-writer.md
│   ├── continuity-editor.md
│   ├── lore-keeper.md
│   ├── developmental-editor.md
│   ├── line-editor.md
│   └── research-agent.md
│
└── scripts/
    ├── word-count.sh                  # Aggregate word counts by POV/act/chapter
    ├── continuity-check.sh            # Flags name inconsistencies across files
    ├── chapter-summary-sync.sh        # Prompts Claude to update summaries after edits
    └── export-manuscript.sh           # Combines chapters into a single clean file
```

---

## The CLAUDE.md Hierarchy

Think of these as a nested briefing system. The root CLAUDE.md is the project bible summary. Each subdirectory CLAUDE.md scopes down to what's relevant for that domain.

### Root CLAUDE.md — The God File

This is what every agent reads first. It should contain:

- **Project identity**: Title, genre, target word count, comp titles, tone
- **Status snapshot**: Current draft stage, last chapter completed, known blockers
- **POV roster**: Every POV character, their arc in one sentence
- **World identity**: The world's name, the central conflict, the thematic core
- **Magic system summary**: The one-paragraph version an agent needs to not violate it
- **Absolute rules**: Things that must never change (character deaths already written, world laws, etc.)
- **Agent directory**: What each agent is for and how to invoke it

### /manuscript/CLAUDE.md

- Prose style guide (POV mode: close third vs. first person, tense, sentence rhythm preferences)
- Chapter naming conventions
- Scene break notation
- How dialogue is handled
- Any stylistic models ("write in the register of Joe Abercrombie, not Brandon Sanderson")

### /story-bible/magic/CLAUDE.md

This one is critical and should be treated almost like a test suite. Every magic interaction in the manuscript must pass through the rules in this file. Include:

- Hard rules (never violable)
- Soft rules (can stretch with in-world justification)
- Known violations to fix (tracked separately)

### /continuity/CLAUDE.md

Instructions for the Continuity Editor agent:
- What consistency checks to run
- How to log contradictions without overwriting original content
- How to cross-reference the name registry

---

## Agent Roles

These are the specialized Claude Code personas. Each lives as a markdown file in `/agents/` and serves as the system prompt when you invoke that agent.

---

### 1. The World Builder

**Purpose**: Creates, expands, and maintains all worldbuilding material.

**Core tasks**:
- Generate geography, cities, cultures, and political systems from a high-level prompt
- Expand a sketch ("there's a desert empire to the south") into full documentation
- Answer questions like "what would the funeral customs of this culture look like?"
- Identify worldbuilding gaps when reviewing chapter drafts

**Key context it loads**: All of `/story-bible/world/`, `/story-bible/history/`, `/story-bible/religions-and-mythology/`

**Sample invocations**:
```
"Expand the Northern Confederacy into a full faction document covering
government, military, economy, and their view of the magic system."

"I'm writing a scene in Keth Varal. What sensory details are established
about this city? What's missing that I should define before drafting?"
```

---

### 2. The Character Architect

**Purpose**: Builds, maintains, and evolves character documentation.

**Core tasks**:
- Create full character sheets (biography, physical description, voice, wounds, wants/needs, arc)
- Track how a character's beliefs change across the manuscript
- Identify voice inconsistencies between chapters
- Generate "character in context" summaries — how does Character A currently view Character B, given everything that's happened so far?
- Manage the relationship map

**Key context it loads**: All of `/story-bible/characters/`, `/continuity/relationship-map.md`, `/continuity/chapter-summaries/`

**Sample invocations**:
```
"Summarize [Character]'s emotional state at the end of Chapter 22,
based on everything in their arc thread and the chapter summaries."

"I need a new minor character who is a spymaster for the Eastern Throne.
Create a full sheet consistent with the culture docs already in the bible."
```

---

### 3. The Plot Architect

**Purpose**: Manages structure, outlines, and narrative logic.

**Core tasks**:
- Build and maintain the master outline
- Manage individual POV thread outlines
- Identify structural problems ("this subplot disappears for 8 chapters")
- Suggest scene sequencing to maximize tension and pacing
- Check that each chapter advances at least two things (plot, character, or world)
- Track the subplot tracker for dangling threads

**Key context it loads**: `/outlines/`, `/continuity/master-timeline.md`, `/continuity/chapter-summaries/`

**Sample invocations**:
```
"Review the current master outline and list any subplots that go
more than 5 chapters without a touchpoint."

"I want to restructure Act 2 to tighten the pacing. Show me the
current chapter sequence for each POV thread and flag the slowest sections."
```

---

### 4. The Prose Writer

**Purpose**: The actual drafting agent. It writes scenes and chapters.

**Core tasks**:
- Draft scenes from a detailed chapter plan
- Continue a scene you've started
- Rewrite a scene in a different register or from a different angle
- Write dialogue-heavy scenes, action sequences, quiet character moments
- Apply the prose style defined in `/manuscript/CLAUDE.md`

**Key context it loads**: The chapter plan for the current scene, the relevant character sheets, the setting documents for the location, the most recent chapter summary for narrative momentum, and `/manuscript/CLAUDE.md` for style.

**Critical rule**: This agent should never invent worldbuilding facts. If something isn't in the story bible, it flags it rather than improvising.

**Sample invocations**:
```
"Draft Chapter 14 using the plan in /outlines/chapter-plans/ch-14.md.
POV is [Character]. The scene takes place in [Location].
Tone is tense but restrained — she doesn't know she's being watched yet."
```

---

### 5. The Continuity Editor

**Purpose**: The consistency enforcer. This agent is paranoid by design.

**Core tasks**:
- Scan a newly written chapter against all established facts
- Check character names, place names, and spell names against the name registry
- Flag timeline violations (a character can't be in two places, an event referenced out of order)
- Check magic use against the magic system rules
- Check physical descriptions against character sheets
- Maintain and update `contradictions-log.md`

**Key context it loads**: Everything. This agent needs broad read access.

**Sample invocations**:
```
"Run a continuity check on Chapter 22. Cross-reference against the
name registry, character sheets, magic rules, and master timeline.
Log any issues to contradictions-log.md."
```

---

### 6. The Lore Keeper

**Purpose**: The living story bible. Keeps documentation current as the manuscript evolves.

**Core tasks**:
- After a chapter is written, update relevant story bible entries
- When the author makes a decision mid-draft ("actually, let's say the magic costs blood, not stamina"), propagate that change across all affected documents
- Maintain the chapter summaries after each chapter is finalized
- Generate a "state of the world" snapshot at any given chapter
- Answer lore questions with citations ("where is this established?")

**Key context it loads**: All of `/story-bible/`, `/continuity/`

**Sample invocations**:
```
"Chapter 18 introduces a new faction. Extract all new lore from this
chapter and create/update the relevant story bible entries."

"I've decided to change the capital city's name from Varath to Valdenmoor.
Find every reference to Varath across the project and flag them for update."
```

---

### 7. The Developmental Editor

**Purpose**: Big-picture story feedback. Treats the manuscript like a story structure problem.

**Core tasks**:
- Evaluate whether each act is doing its job (setup, confrontation, resolution)
- Identify where the protagonist's agency feels weak
- Flag scenes that are present but not earning their place
- Check that the thematic throughline is visible across all three acts
- Compare the POV thread balance (is one character getting far more page time than intended?)
- Evaluate chapter endings — are they generating forward momentum?

**Key context it loads**: `/outlines/`, `/continuity/chapter-summaries/`, `/story-bible/characters/pov-characters/`

**Sample invocations**:
```
"Read the chapter summaries for Act 2 and give me a developmental
assessment. I'm worried the midpoint doesn't hit hard enough and
that [Character B]'s thread feels passive."
```

---

### 8. The Line Editor

**Purpose**: Prose-level quality. Reads sentence by sentence.

**Core tasks**:
- Identify repetitive sentence structures
- Flag overused words or phrases (you'll have your personal tics — this agent learns them)
- Tighten dialogue attribution and action beats
- Improve clarity in complex action sequences
- Reduce adverb reliance and telling vs. showing issues
- Maintain the author's voice while improving the prose

**Key context it loads**: `/manuscript/CLAUDE.md` (style guide), the specific chapter being edited.

**Sample invocations**:
```
"Line edit Chapter 7. Preserve my voice but tighten the prose.
Flag anything that feels like telling rather than showing, and
list any words used more than 3 times in the chapter."
```

---

### 9. The Research Agent

**Purpose**: Brings real-world knowledge into the worldbuilding process without contaminating the fiction.

**Core tasks**:
- Research historical analogs for political systems, military tactics, trade routes, architecture
- Pull in accurate information about medieval medicine, agriculture, metallurgy, etc.
- Identify genre conventions and how comparable books have handled specific challenges
- Answer "what would actually happen if..." questions from a real-world basis

**Key context it loads**: `/research/`, uses web search tool when available.

**Sample invocations**:
```
"I'm building a siege sequence for Chapter 31. Research medieval siege
warfare tactics — specifically how defenders would respond to a sustained
blockade over multiple months. Summarize for fiction use."
```

---

### 10. The POV Manager (Specialized Coordinator)

**Purpose**: This is an orchestration agent specifically for multi-POV management — a unique challenge in epic fantasy.

**Core tasks**:
- Track where each POV character is geographically and emotionally at any point in the story
- Ensure POV transitions feel earned and aren't jarring
- Identify moments where two POV threads should intersect
- Flag when a POV character "goes dark" for too many chapters
- Maintain a POV balance chart (chapter count per character)
- Manage dramatic irony — what does the reader know that Character A doesn't, because we saw it through Character B?

**Key context it loads**: All POV thread outlines, master timeline, chapter summaries sorted by POV.

**Sample invocations**:
```
"Give me a chapter-by-chapter POV breakdown from Chapter 20 to 35.
Flag any character who disappears for more than 4 chapters and
identify where dramatic irony opportunities exist between threads."
```

---

## MCP Servers to Configure

These extend what Claude Code can do inside your project.

**Filesystem MCP** — Essential. Gives Claude Code structured read/write access to your entire novel directory. Configure allowed paths carefully so agents can read broadly but only write to their designated areas.

**Web Search** — Attach to the Research Agent specifically. You probably don't want web search running by default for writing agents, but the Research Agent should have it.

**Custom Story Bible MCP (advanced)** — Worth building eventually. A lightweight local server that exposes your story bible as a queryable API. Instead of loading entire files, agents can ask "what are all facts about Character X?" and get a filtered response. This becomes important as your bible grows past 100,000 words.

---

## Bash Scripts to Build Early

These are simple but will save hours.

**`word-count.sh`**
Aggregates word counts across the whole manuscript, broken down by POV character and by Act. Gives you a real-time progress dashboard.

**`continuity-check.sh`**
Runs a basic name consistency pass — compares every proper noun in a new chapter against the name registry. Catches typos in character names before they compound.

**`chapter-summary-sync.sh`**
After you finalize a chapter, this prompts Claude to read it and update the chapter summary in `/continuity/chapter-summaries/`. Keeps the summaries current without manual work.

**`export-manuscript.sh`**
Concatenates all chapters in order into a single clean file, stripping metadata headers. Produces a submission-ready or beta-reader-ready draft with one command.

**`pov-thread-extract.sh`**
Pulls all chapters for a single POV character into a temporary file so you can read or review just that character's journey end-to-end.

---

## Workflow: How It All Connects

Here's the typical loop once the system is running:

1. **Plot Architect** updates the chapter plan for the next chapter
2. **Lore Keeper** confirms all referenced locations, characters, and objects are documented
3. **Prose Writer** drafts the chapter from the plan
4. **Continuity Editor** runs a check on the new chapter
5. **Lore Keeper** updates story bible entries and chapter summary
6. **POV Manager** updates the POV balance chart
7. **Line Editor** polishes the prose (on a second pass, not first draft)
8. Chapter is finalized and moved to the appropriate act folder

Every few chapters, run the **Developmental Editor** for a structural health check.

---

## The Root CLAUDE.md Template

This is what your root-level file should look like structurally. Fill in your actual content.

```markdown
# [NOVEL TITLE] — Master Project Context

## Project Identity
- Genre: Dark Epic Fantasy
- Target length: 250,000 words
- POV mode: Close third person, multiple POV
- Tense: Past
- Tone: [Your tone markers — e.g., "Morally complex, grim but not nihilistic"]
- Comp titles: [Your 2-3 comp titles and what you're borrowing from each]

## Current Status
- Draft stage: [First draft / Revision / etc.]
- Last completed chapter: [Number and title]
- Current focus: [What you're working on right now]
- Open blockers: [Anything unresolved that agents should know about]

## POV Characters
| Character | Role | Arc Summary |
|-----------|------|-------------|
| [Name] | [Function in story] | [One sentence arc] |

## World Overview
- World name: [Name]
- Central conflict: [One paragraph]
- Thematic core: [The question this novel is asking]

## Magic System (Summary)
[3-5 sentences. Enough that an agent won't violate it. Full rules in /story-bible/magic/]

## Absolute Rules (Do Not Violate)
- [List of locked facts — deaths, betrayals, reveals that are already committed]

## Agent Directory
- World Builder: Worldbuilding creation and expansion
- Character Architect: Character sheets and relationship management
- Plot Architect: Structure, outlines, POV threads
- Prose Writer: Scene and chapter drafting
- Continuity Editor: Consistency checking and contradiction logging
- Lore Keeper: Story bible maintenance
- Developmental Editor: Big-picture story feedback
- Line Editor: Prose-level editing
- Research Agent: Real-world research support
- POV Manager: Multi-POV coordination
```

---

## Scaling Notes

Start with the Lore Keeper, Prose Writer, and Continuity Editor as your core three. Those three running together cover 80% of your daily workflow. Add the specialized agents as you need them.

As the project grows past 150,000 words, the Continuity Editor becomes increasingly important — contradiction risk compounds as the manuscript grows. Consider running it after every chapter at that point, not just periodically.

The story bible will eventually grow large enough that even Claude Code's context window has to be managed carefully. That's when the custom MCP server becomes worth building — so agents can query what they need rather than loading everything.
