"""Seed profile loader — fills the database with named fantasy content for development and testing."""

import json
import sqlite3


def load_seed_profile(conn: sqlite3.Connection, profile: str) -> None:
    """Load a named seed profile into the database.

    Args:
        conn: Open sync SQLite connection (caller is responsible for open/close).
        profile: Seed profile name (e.g., "minimal", "gate_ready").

    Raises:
        ValueError: If profile name is not recognised.
    """
    profiles = {"minimal": _load_minimal, "gate_ready": _load_gate_ready}
    if profile not in profiles:
        raise ValueError(f"Unknown seed profile '{profile}'. Available: {list(profiles)}")
    profiles[profile](conn)


def _load_minimal(conn: sqlite3.Connection) -> None:
    """Insert minimal seed data in FK dependency order.

    World: Age of Embers / Kaelthari culture / Obsidian Court faction
    Books: The Void Between Stars (book 1), The Shattered Meridian (book 2)
    Characters: 5 named characters (protagonist, antagonist, mentor, ally, rival)
    Structure: 3 chapters, 2 scenes each, with supporting domain rows.
    """

    # -----------------------------------------------------------------------
    # Phase 1: Foundation entities — eras, books, cultures, factions
    # -----------------------------------------------------------------------

    cur = conn.execute(
        "INSERT INTO eras (name, sequence_order, date_start, date_end, summary, canon_status) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        ("The Age of Embers", 1, "Year 0 AE", "Year 400 AE",
         "An era of arcane collapse when the old star-forges fell silent and the world entered a long twilight.",
         "approved"),
    )
    era_id = cur.lastrowid

    cur = conn.execute(
        "INSERT INTO books (title, series_order, word_count_target, status, canon_status) VALUES (?, ?, ?, ?, ?)",
        ("The Void Between Stars", 1, 120000, "drafting", "approved"),
    )
    book_id_1 = cur.lastrowid

    cur = conn.execute(
        "INSERT INTO books (title, series_order, word_count_target, status, canon_status) VALUES (?, ?, ?, ?, ?)",
        ("The Shattered Meridian", 2, 130000, "planning", "draft"),
    )
    book_id_2 = cur.lastrowid  # noqa: F841 — captured for potential FK use

    cur = conn.execute(
        "INSERT INTO cultures (name, region, language_family, naming_conventions, values_beliefs, canon_status) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        ("Kaelthari", "The Ashen Wastes", "Vel-tongue root",
         "Compound names — first syllable denotes caste, final syllable denotes lineage.",
         "Honour through endurance; the ember that outlasts the blaze is worthy.",
         "approved"),
    )
    culture_id = cur.lastrowid

    # Faction inserted before characters (leader_character_id is nullable)
    cur = conn.execute(
        "INSERT INTO factions (name, faction_type, headquarters, goals, canon_status) VALUES (?, ?, ?, ?, ?)",
        ("The Obsidian Court", "political",
         "The Ashen Citadel",
         "Reclaim the lost star-forge schematics and restore arcane supremacy.",
         "approved"),
    )
    faction_id = cur.lastrowid

    conn.commit()

    # -----------------------------------------------------------------------
    # Phase 2: Characters (require era, culture, faction to exist)
    # -----------------------------------------------------------------------

    cur = conn.execute(
        "INSERT INTO characters (name, role, faction_id, culture_id, home_era_id, age, "
        "motivation, fear, strength, arc_summary, canon_status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("Aeryn Vael", "protagonist", faction_id, culture_id, era_id, 24,
         "Uncover the truth behind her father's disappearance.",
         "Becoming the instrument of the very power she fears.",
         "Relentless determination and deep empathy.",
         "From loyal servant of the Court to reluctant revolutionary.",
         "approved"),
    )
    char_id_protagonist = cur.lastrowid

    cur = conn.execute(
        "INSERT INTO characters (name, role, faction_id, culture_id, home_era_id, age, "
        "motivation, fear, strength, arc_summary, canon_status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("Solvann Drex", "antagonist", faction_id, culture_id, era_id, 51,
         "Restore the star-forges and reshape the world in the Kaelthari ideal.",
         "Irrelevance — to die having changed nothing.",
         "Strategic brilliance and the patience of decades.",
         "Convinced of righteousness until the cost becomes undeniable.",
         "approved"),
    )
    char_id_antagonist = cur.lastrowid

    cur = conn.execute(
        "INSERT INTO characters (name, role, culture_id, home_era_id, age, "
        "motivation, strength, arc_summary, canon_status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("Ithrel Cass", "mentor", culture_id, era_id, 67,
         "Ensure the mistakes of the Ember Collapse are never repeated.",
         "Deep knowledge of pre-collapse archives and calm under pressure.",
         "Passes from guardian to released teacher as Aeryn matures.",
         "approved"),
    )
    char_id_mentor = cur.lastrowid

    cur = conn.execute(
        "INSERT INTO characters (name, role, culture_id, home_era_id, age, "
        "motivation, strength, arc_summary, canon_status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("Mira Sundal", "ally", culture_id, era_id, 22,
         "Protect her younger siblings from the Court's conscription drafts.",
         "Street-level intelligence network and quick improvisation.",
         "Learns to trust beyond her immediate circle.",
         "approved"),
    )
    char_id_ally = cur.lastrowid

    cur = conn.execute(
        "INSERT INTO characters (name, role, faction_id, culture_id, home_era_id, age, "
        "motivation, fear, strength, arc_summary, canon_status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("Calder Veth", "rival", faction_id, culture_id, era_id, 26,
         "Prove he deserves the position that was given to Aeryn instead of him.",
         "Being seen as second-best forever.",
         "Tactical competence and a gift for reading people.",
         "From antagonistic rival to reluctant ally after a shared loss.",
         "approved"),
    )
    char_id_rival = cur.lastrowid

    # Update faction leader now that characters exist
    conn.execute(
        "UPDATE factions SET leader_character_id = ? WHERE id = ?",
        (char_id_antagonist, faction_id),
    )

    conn.commit()

    # -----------------------------------------------------------------------
    # Phase 3: Acts and locations (require books and factions)
    # -----------------------------------------------------------------------

    cur = conn.execute(
        "INSERT INTO acts (book_id, act_number, name, purpose, canon_status) VALUES (?, ?, ?, ?, ?)",
        (book_id_1, 1, "Act I — The Ember Threshold",
         "Establish Aeryn's world, introduce the threat, force her across the threshold.",
         "approved"),
    )
    act_id = cur.lastrowid

    sensory_profile = json.dumps({
        "sight": "Obsidian walls etched with dying stars; torchlight that never seems to reach the ceiling.",
        "sound": "Distant hammer-strikes from the forge levels; whispered protocol in every corridor.",
        "smell": "Ash and old iron undercut by the faint sweetness of binding-resin.",
        "touch": "Stone floors perpetually cold; metal fixtures that hum faintly under your palm.",
    })

    cur = conn.execute(
        "INSERT INTO locations (name, location_type, culture_id, controlling_faction_id, "
        "description, sensory_profile, strategic_value, canon_status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        ("The Ashen Citadel", "fortress", culture_id, faction_id,
         "Seat of the Obsidian Court, built atop the ruins of the first star-forge.",
         sensory_profile,
         "Controls the only known approach to the Ember Vaults.",
         "approved"),
    )
    location_id = cur.lastrowid

    conn.commit()

    # -----------------------------------------------------------------------
    # Phase 4: Chapters (require books, acts)
    # -----------------------------------------------------------------------

    cur = conn.execute(
        "INSERT INTO chapters (book_id, act_id, chapter_number, title, pov_character_id, "
        "status, summary, structural_function, canon_status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (book_id_1, act_id, 1, "The Last Ember Watch",
         char_id_protagonist, "drafting",
         "Aeryn keeps the final ember watch before the Court's quarterly review. "
         "She discovers a discrepancy in the archive manifest that should not exist.",
         "Inciting incident — the first crack in Aeryn's loyalty.",
         "approved"),
    )
    chapter_id_1 = cur.lastrowid

    cur = conn.execute(
        "INSERT INTO chapters (book_id, act_id, chapter_number, title, pov_character_id, "
        "status, summary, structural_function, canon_status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (book_id_1, act_id, 2, "Beneath the Vaultstone",
         char_id_protagonist, "planned",
         "Aeryn descends to the archive with Mira posing as a maintenance worker. "
         "They find the manifest discrepancy is not a clerical error — something was moved.",
         "Rising action — stakes confirmed, allies established.",
         "approved"),
    )
    chapter_id_2 = cur.lastrowid

    cur = conn.execute(
        "INSERT INTO chapters (book_id, act_id, chapter_number, title, pov_character_id, "
        "status, summary, structural_function, canon_status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (book_id_1, act_id, 3, "A Name in the Ashes",
         char_id_mentor, "planned",
         "Ithrel reveals what the moved archive actually contains and why Aeryn's father "
         "was the one who hid it. The mentor threshold is crossed.",
         "First threshold — Aeryn receives the call to full commitment.",
         "approved"),
    )
    chapter_id_3 = cur.lastrowid

    # Update act with chapter boundaries now that chapters exist
    conn.execute(
        "UPDATE acts SET start_chapter_id = ?, end_chapter_id = ? WHERE id = ?",
        (chapter_id_1, chapter_id_3, act_id),
    )

    conn.commit()

    # -----------------------------------------------------------------------
    # Phase 5: Scenes (require chapters)
    # -----------------------------------------------------------------------

    cur = conn.execute(
        "INSERT INTO scenes (chapter_id, scene_number, location_id, scene_type, summary, "
        "dramatic_question, scene_goal, status, canon_status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (chapter_id_1, 1, location_id, "action",
         "Aeryn completes the ember watch ritual alone in the upper forge hall.",
         "Will Aeryn notice the anomaly before the watch ends?",
         "Complete the watch without incident.",
         "drafting", "approved"),
    )
    scene_id_1_1 = cur.lastrowid

    cur = conn.execute(
        "INSERT INTO scenes (chapter_id, scene_number, location_id, scene_type, summary, "
        "dramatic_question, scene_goal, status, canon_status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (chapter_id_1, 2, location_id, "discovery",
         "Aeryn cross-checks the manifest and finds a reference to a sealed vault "
         "that does not appear in any official record.",
         "Does the discrepancy point to negligence — or concealment?",
         "Confirm the discrepancy is real before reporting it.",
         "drafting", "approved"),
    )
    scene_id_1_2 = cur.lastrowid

    cur = conn.execute(
        "INSERT INTO scenes (chapter_id, scene_number, location_id, scene_type, summary, "
        "dramatic_question, scene_goal, status, canon_status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (chapter_id_2, 1, location_id, "action",
         "Aeryn and Mira descend to the archive level under a maintenance cover story.",
         "Will their cover hold long enough to reach the restricted vault?",
         "Reach the vault without raising an alert.",
         "planned", "approved"),
    )
    scene_id_2_1 = cur.lastrowid

    cur = conn.execute(
        "INSERT INTO scenes (chapter_id, scene_number, location_id, scene_type, summary, "
        "dramatic_question, scene_goal, status, canon_status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (chapter_id_2, 2, location_id, "revelation",
         "Inside the vault, they find an empty cradle where something large once rested — "
         "and scratch marks in the stone that match no known tool.",
         "What was stored here, and who removed it?",
         "Gather evidence without being detected.",
         "planned", "approved"),
    )
    scene_id_2_2 = cur.lastrowid

    cur = conn.execute(
        "INSERT INTO scenes (chapter_id, scene_number, location_id, scene_type, summary, "
        "dramatic_question, scene_goal, status, canon_status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (chapter_id_3, 1, location_id, "conversation",
         "Aeryn confronts Ithrel with what she found. The mentor is not surprised.",
         "Will Ithrel finally tell the full truth about Aeryn's father?",
         "Understand why the archive was sealed.",
         "planned", "approved"),
    )
    scene_id_3_1 = cur.lastrowid

    cur = conn.execute(
        "INSERT INTO scenes (chapter_id, scene_number, location_id, scene_type, summary, "
        "dramatic_question, scene_goal, status, canon_status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (chapter_id_3, 2, location_id, "decision",
         "Ithrel gives Aeryn the archive key and tells her what it opens. "
         "She must choose whether to use it.",
         "Will Aeryn accept the burden her father left for her?",
         "Decide to pursue the truth regardless of cost.",
         "planned", "approved"),
    )
    scene_id_3_2 = cur.lastrowid

    conn.commit()

    # -----------------------------------------------------------------------
    # Phase 6: Artifacts, magic elements, supernatural elements
    # -----------------------------------------------------------------------

    cur = conn.execute(
        "INSERT INTO artifacts (name, artifact_type, current_owner_id, current_location_id, "
        "origin_era_id, description, significance, canon_status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        ("The Ember Key", "key", char_id_mentor, location_id, era_id,
         "A key forged from condensed star-ember, warm to the touch even after four centuries.",
         "Opens the sealed vault beneath the Ashen Citadel; passed from keeper to keeper.",
         "approved"),
    )
    artifact_id = cur.lastrowid

    cur = conn.execute(
        "INSERT INTO magic_system_elements (name, element_type, rules, limitations, costs, "
        "introduced_chapter_id, canon_status) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("Ember-Binding", "ability",
         "Practitioners channel residual star-ember energy to reinforce or seal physical objects.",
         "Cannot create new structure — only reinforce what already exists.",
         "Each binding drains a measurable fraction of the practitioner's stored ember-reserve.",
         chapter_id_1, "approved"),
    )
    magic_element_id = cur.lastrowid

    cur = conn.execute(
        "INSERT INTO supernatural_elements (name, element_type, description, rules, "
        "introduced_chapter_id, canon_status) VALUES (?, ?, ?, ?, ?, ?)",
        ("Void-Echoes", "phenomenon",
         "Fragments of collapsed star-forge energy that manifest as brief sensory hallucinations.",
         "Appear only in locations saturated with historical ember use; cannot be controlled.",
         chapter_id_2, "draft"),
    )
    supernatural_id = cur.lastrowid  # noqa: F841

    conn.commit()

    # -----------------------------------------------------------------------
    # Phase 7: Relationships and perception profiles
    # -----------------------------------------------------------------------

    cur = conn.execute(
        "INSERT INTO character_relationships (character_a_id, character_b_id, relationship_type, "
        "bond_strength, trust_level, current_status, history_summary, "
        "first_meeting_chapter_id, canon_status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (char_id_protagonist, char_id_mentor, "mentor-student", 8, 7, "trusting",
         "Ithrel recognised Aeryn's gift during her initiation examination and petitioned to supervise her.",
         chapter_id_1, "approved"),
    )
    relationship_id = cur.lastrowid

    conn.execute(
        "INSERT INTO character_relationships (character_a_id, character_b_id, relationship_type, "
        "bond_strength, trust_level, current_status, history_summary, canon_status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (char_id_protagonist, char_id_ally, "friendship", 7, 9, "close",
         "Childhood friends from the lower Citadel districts; Aeryn secured Mira a maintenance contract.",
         "approved"),
    )

    conn.execute(
        "INSERT INTO character_relationships (character_a_id, character_b_id, relationship_type, "
        "bond_strength, trust_level, current_status, history_summary, canon_status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (char_id_protagonist, char_id_rival, "rivalry", 3, 2, "tense",
         "Calder was passed over for Aeryn's appointment; he has not forgiven the slight.",
         "approved"),
    )

    conn.execute(
        "INSERT INTO perception_profiles (observer_id, subject_id, perceived_traits, "
        "trust_level, emotional_valence, misperceptions) VALUES (?, ?, ?, ?, ?, ?)",
        (char_id_protagonist, char_id_antagonist,
         "Decisive, inspiring, the architect of stability.",
         4, "conflicted",
         "She does not yet know he ordered her father's removal."),
    )

    conn.commit()

    # -----------------------------------------------------------------------
    # Phase 8: Events and timeline
    # -----------------------------------------------------------------------

    cur = conn.execute(
        "INSERT INTO events (name, event_type, chapter_id, location_id, in_story_date, "
        "summary, significance, canon_status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        ("The Final Ember Watch", "ritual", chapter_id_1, location_id, "Day 1, Month 3, Year 397 AE",
         "Aeryn performs the quarterly ember watch and discovers the archive discrepancy.",
         "The inciting event that sets the whole plot in motion.",
         "approved"),
    )
    event_id = cur.lastrowid

    conn.execute(
        "INSERT INTO event_participants (event_id, character_id, role) VALUES (?, ?, ?)",
        (event_id, char_id_protagonist, "actor"),
    )

    conn.execute(
        "INSERT INTO event_artifacts (event_id, artifact_id, involvement) VALUES (?, ?, ?)",
        (event_id, artifact_id, "Referenced in the manifest; its absence is the trigger."),
    )

    conn.execute(
        "INSERT INTO pov_chronological_position (character_id, chapter_id, in_story_date, "
        "day_number, location_id) VALUES (?, ?, ?, ?, ?)",
        (char_id_protagonist, chapter_id_1, "Day 1, Month 3, Year 397 AE", 1, location_id),
    )

    conn.execute(
        "INSERT INTO travel_segments (character_id, from_location_id, to_location_id, "
        "start_chapter_id, end_chapter_id, travel_method) VALUES (?, ?, ?, ?, ?, ?)",
        (char_id_protagonist, location_id, location_id,
         chapter_id_1, chapter_id_2, "foot"),
    )

    conn.commit()

    # -----------------------------------------------------------------------
    # Phase 9: Plot threads, arcs, structural obligations
    # -----------------------------------------------------------------------

    cur = conn.execute(
        "INSERT INTO plot_threads (name, thread_type, status, opened_chapter_id, "
        "summary, stakes, canon_status) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("The Hidden Vault", "main", "active", chapter_id_1,
         "Aeryn uncovers and pursues the secret of what was hidden in the sealed vault.",
         "If the Court retakes what was hidden, it gains the power to reignite the star-forges unchecked.",
         "approved"),
    )
    plot_thread_id = cur.lastrowid

    conn.execute(
        "INSERT INTO chapter_plot_threads (chapter_id, plot_thread_id, thread_role) VALUES (?, ?, ?)",
        (chapter_id_1, plot_thread_id, "open"),
    )

    conn.execute(
        "INSERT INTO chapter_plot_threads (chapter_id, plot_thread_id, thread_role) VALUES (?, ?, ?)",
        (chapter_id_2, plot_thread_id, "advance"),
    )

    conn.execute(
        "INSERT INTO chapter_structural_obligations (chapter_id, obligation_type, description) VALUES (?, ?, ?)",
        (chapter_id_1, "setup",
         "Establish Aeryn's competence and loyalty before fracturing it."),
    )

    cur = conn.execute(
        "INSERT INTO character_arcs (character_id, arc_type, starting_state, desired_state, "
        "lie_believed, truth_to_learn, opened_chapter_id, canon_status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (char_id_protagonist, "transformation",
         "Loyal, rule-following servant of the Court.",
         "Self-directed agent acting on her own moral compass.",
         "The Court's order is the only protection against another Collapse.",
         "The Court caused the Collapse to begin with.",
         chapter_id_1, "approved"),
    )
    arc_id = cur.lastrowid

    conn.execute(
        "INSERT INTO chapter_character_arcs (chapter_id, arc_id, arc_progression) VALUES (?, ?, ?)",
        (chapter_id_1, arc_id, "disruption"),
    )

    conn.execute(
        "INSERT INTO arc_health_log (arc_id, chapter_id, health_status, notes) VALUES (?, ?, ?, ?)",
        (arc_id, chapter_id_1, "on-track",
         "Disruption planted cleanly; Aeryn's doubt is nascent but credible."),
    )

    cur = conn.execute(
        "INSERT INTO chekovs_gun_registry (name, description, planted_chapter_id, planted_scene_id, "
        "status, canon_status) VALUES (?, ?, ?, ?, ?, ?)",
        ("The Scratch Marks", "Tool-marks in the vault stone that match no known Citadel instrument.",
         chapter_id_2, scene_id_2_2, "planted", "approved"),
    )
    chekov_id = cur.lastrowid  # noqa: F841

    conn.execute(
        "INSERT INTO subplot_touchpoint_log (plot_thread_id, chapter_id, touchpoint_type) VALUES (?, ?, ?)",
        (plot_thread_id, chapter_id_2, "advance"),
    )

    conn.commit()

    # -----------------------------------------------------------------------
    # Phase 10: Scene-level goals and pacing
    # -----------------------------------------------------------------------

    conn.execute(
        "INSERT INTO scene_character_goals (scene_id, character_id, goal, obstacle, outcome) VALUES (?, ?, ?, ?, ?)",
        (scene_id_1_1, char_id_protagonist,
         "Complete the ember watch without incident.",
         "Her attention keeps catching on a gap in the manifest.",
         "Watch completed but the discrepancy cannot be dismissed."),
    )

    conn.execute(
        "INSERT INTO pacing_beats (chapter_id, scene_id, beat_type, description, sequence_order) "
        "VALUES (?, ?, ?, ?, ?)",
        (chapter_id_1, scene_id_1_1, "establishment",
         "Aeryn alone in the forge hall — quiet, ritual, the world working as it should.",
         1),
    )

    conn.execute(
        "INSERT INTO pacing_beats (chapter_id, scene_id, beat_type, description, sequence_order) "
        "VALUES (?, ?, ?, ?, ?)",
        (chapter_id_1, scene_id_1_2, "complication",
         "The manifest entry that should not exist — the first real disruption of Aeryn's certainty.",
         2),
    )

    conn.execute(
        "INSERT INTO tension_measurements (chapter_id, tension_level, measurement_type, notes) "
        "VALUES (?, ?, ?, ?)",
        (chapter_id_1, 3, "overall",
         "Low baseline tension appropriate to an inciting chapter; dread is nascent."),
    )

    conn.execute(
        "INSERT INTO tension_measurements (chapter_id, tension_level, measurement_type, notes) "
        "VALUES (?, ?, ?, ?)",
        (chapter_id_2, 6, "overall",
         "Rising tension as the infiltration stakes become concrete."),
    )

    conn.commit()

    # -----------------------------------------------------------------------
    # Phase 11: Sessions, gate, questions, decisions
    # -----------------------------------------------------------------------

    cur = conn.execute(
        "INSERT INTO session_logs (summary, word_count_delta, carried_forward, chapters_touched) "
        "VALUES (?, ?, ?, ?)",
        ("Initial world-building session. Established Aeryn, the Citadel, and the inciting ember-watch scene.",
         1800,
         json.dumps(["Confirm vault scratch-mark lore consistency", "Draft Calder scene in Chapter 2"]),
         json.dumps([chapter_id_1])),
    )
    session_id = cur.lastrowid

    conn.execute(
        "INSERT INTO agent_run_log (session_id, agent_name, tool_name, input_summary, "
        "output_summary, duration_ms, success) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (session_id, "ContextAgent", "read_chapter",
         "chapter_id=1", "Returned chapter metadata and scene list.", 120, 1),
    )

    cur = conn.execute(
        "INSERT INTO architecture_gate (is_certified, checklist_version, notes) VALUES (?, ?, ?)",
        (0, 1, "Gate opened at project start. Not yet certified."),
    )
    gate_id = cur.lastrowid

    conn.execute(
        "INSERT INTO gate_checklist_items (gate_id, item_key, category, description) VALUES (?, ?, ?, ?)",
        (gate_id, "min_characters", "population",
         "At least 5 named characters with distinct roles."),
    )

    conn.execute(
        "INSERT INTO project_metrics_snapshots (word_count, chapter_count, scene_count, "
        "character_count, session_count) VALUES (?, ?, ?, ?, ?)",
        (1800, 3, 6, 5, 1),
    )

    conn.execute(
        "INSERT INTO pov_balance_snapshots (chapter_id, character_id, chapter_count, word_count) "
        "VALUES (?, ?, ?, ?)",
        (chapter_id_1, char_id_protagonist, 1, 1800),
    )

    conn.execute(
        "INSERT INTO open_questions (question, domain, session_id, priority) VALUES (?, ?, ?, ?)",
        ("What exactly did Aeryn's father hide in the vault, and why?",
         "plot", session_id, "high"),
    )

    conn.execute(
        "INSERT INTO decisions_log (decision_type, description, rationale, session_id, chapter_id) "
        "VALUES (?, ?, ?, ?, ?)",
        ("plot", "Vault contents remain unknown to the reader through Act I.",
         "Sustains the mystery and mirrors Aeryn's ignorance.",
         session_id, chapter_id_1),
    )

    conn.commit()

    # -----------------------------------------------------------------------
    # Phase 12: Canon facts, foreshadowing, prophecy, motifs
    # -----------------------------------------------------------------------

    cur = conn.execute(
        "INSERT INTO canon_facts (domain, fact, source_chapter_id, certainty_level, canon_status) "
        "VALUES (?, ?, ?, ?, ?)",
        ("world", "The Ashen Citadel was built atop the ruins of the first star-forge.",
         chapter_id_1, "established", "approved"),
    )
    canon_fact_id = cur.lastrowid  # noqa: F841

    conn.execute(
        "INSERT INTO continuity_issues (severity, description, chapter_id) VALUES (?, ?, ?)",
        ("minor", "Vault access protocol in Scene 2 may contradict the guard-rotation established in Scene 1.",
         chapter_id_2),
    )

    conn.execute(
        "INSERT INTO foreshadowing_registry (description, plant_chapter_id, plant_scene_id, "
        "foreshadowing_type, status) VALUES (?, ?, ?, ?, ?)",
        ("The scratch marks in the vault will later be identified as Star-Forge aperture scars.",
         chapter_id_2, scene_id_2_2, "object", "planted"),
    )

    cur = conn.execute(
        "INSERT INTO prophecy_registry (name, text, subject_character_id, uttered_chapter_id, "
        "status, canon_status) VALUES (?, ?, ?, ?, ?, ?)",
        ("The Ember Keeper's Burden",
         "When the last Keeper passes the key, the Void between stars shall close or widen — "
         "and the choice is the Keeper's alone.",
         char_id_protagonist, chapter_id_3, "active", "approved"),
    )
    prophecy_id = cur.lastrowid  # noqa: F841

    cur = conn.execute(
        "INSERT INTO motif_registry (name, motif_type, description, thematic_role, "
        "first_appearance_chapter_id) VALUES (?, ?, ?, ?, ?)",
        ("Dying Embers", "symbol",
         "Embers that survive longer than expected — used to represent resilience and hidden worth.",
         "Mirrors Aeryn's arc: diminished but not extinguished.",
         chapter_id_1),
    )
    motif_id = cur.lastrowid

    conn.execute(
        "INSERT INTO motif_occurrences (motif_id, chapter_id, scene_id, description, occurrence_type) "
        "VALUES (?, ?, ?, ?, ?)",
        (motif_id, chapter_id_1, scene_id_1_1,
         "The last ember in the forge-watch brazier that refuses to die as Aeryn watches.",
         "direct"),
    )

    conn.execute(
        "INSERT INTO thematic_mirrors (name, mirror_type, element_a_id, element_a_type, "
        "element_b_id, element_b_type, mirror_description, thematic_purpose) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        ("Aeryn and Solvann", "character",
         char_id_protagonist, "character",
         char_id_antagonist, "character",
         "Both are guardians of something fragile; both believe they are the rightful protector.",
         "Explores how identical motivations produce opposite moral outcomes."),
    )

    conn.execute(
        "INSERT INTO opposition_pairs (name, concept_a, concept_b, manifested_in) VALUES (?, ?, ?, ?)",
        ("Order vs Truth",
         "The Court's imposed order that suppresses dangerous knowledge.",
         "Aeryn's pursuit of truth regardless of the destabilising cost.",
         "The decision at the end of Chapter 3."),
    )

    conn.commit()

    # -----------------------------------------------------------------------
    # Phase 13: Reader experience tables
    # -----------------------------------------------------------------------

    conn.execute(
        "INSERT INTO reader_information_states (chapter_id, domain, information, revealed_how) "
        "VALUES (?, ?, ?, ?)",
        (chapter_id_1, "world",
         "The Ashen Citadel and Obsidian Court are established as powerful but secretive.",
         "Environmental detail and Aeryn's routine behaviour."),
    )

    conn.execute(
        "INSERT INTO reader_reveals (chapter_id, scene_id, reveal_type, planned_reveal) VALUES (?, ?, ?, ?)",
        (chapter_id_2, scene_id_2_2, "discovery",
         "The vault contained something significant that was deliberately removed."),
    )

    conn.execute(
        "INSERT INTO dramatic_irony_inventory (chapter_id, reader_knows, character_doesnt_know, "
        "irony_type, tension_level) VALUES (?, ?, ?, ?, ?)",
        (chapter_id_1,
         "Solvann ordered the vault contents removed before Aeryn was posted to ember-watch.",
         "Aeryn does not know her appointment was designed to give her access to the discovery.",
         "situational", 4),
    )

    conn.execute(
        "INSERT INTO reader_experience_notes (chapter_id, scene_id, note_type, content) "
        "VALUES (?, ?, ?, ?)",
        (chapter_id_1, scene_id_1_1, "pacing",
         "The watch ritual should feel meditative and slightly monotonous — "
         "reader's first breath before the story inhales."),
    )

    conn.execute(
        "INSERT INTO faction_political_states (faction_id, chapter_id, power_level, "
        "internal_state, noted_by_character_id) VALUES (?, ?, ?, ?, ?)",
        (faction_id, chapter_id_1, 8,
         "Publicly stable; internally fractured over the vault project.",
         char_id_protagonist),
    )

    conn.commit()

    # -----------------------------------------------------------------------
    # Phase 14: Publishing, research, documentation
    # -----------------------------------------------------------------------

    cur = conn.execute(
        "INSERT INTO publishing_assets (asset_type, title, content, version, status) VALUES (?, ?, ?, ?, ?)",
        ("query_letter", "Query Letter v1 — The Void Between Stars",
         "A twenty-four-year-old keeper's loyalty fractures when she discovers "
         "the archive her order swore to protect is missing something it was never supposed to lose...",
         1, "draft"),
    )
    asset_id = cur.lastrowid

    conn.execute(
        "INSERT INTO submission_tracker (asset_id, agency_or_publisher, submitted_at, status) "
        "VALUES (?, ?, ?, ?)",
        (asset_id, "Placeholder Agency (not yet submitted)", "2026-01-01", "pending"),
    )

    conn.execute(
        "INSERT INTO research_notes (topic, content, source, relevance) VALUES (?, ?, ?, ?)",
        ("Feudal archive management",
         "Historical archive keepers in medieval institutions often had quasi-clerical status. "
         "Their access to records made them politically dangerous.",
         "General historical research",
         "Grounds the Citadel's archive culture in plausible institutional logic."),
    )

    conn.execute(
        "INSERT INTO documentation_tasks (title, description, status, priority) VALUES (?, ?, ?, ?)",
        ("Map the Ember Vaults",
         "Create a spatial description of the three sub-levels beneath the Citadel for scene-setting.",
         "pending", "high"),
    )

    conn.commit()

    # -----------------------------------------------------------------------
    # Phase 15: Name registry, magic use log, practitioner abilities
    # -----------------------------------------------------------------------

    conn.execute(
        "INSERT INTO name_registry (name, entity_type, culture_id, linguistic_notes, "
        "introduced_chapter_id) VALUES (?, ?, ?, ?, ?)",
        ("Aeryn Vael", "character", culture_id,
         "Aeryn = keeper (Vel-tongue: aer = tend, yn = suffix of occupation). "
         "Vael = lineage marker for the lower forge-ward caste.",
         chapter_id_1),
    )

    conn.execute(
        "INSERT INTO practitioner_abilities (character_id, magic_element_id, proficiency_level, "
        "acquired_chapter_id) VALUES (?, ?, ?, ?)",
        (char_id_protagonist, magic_element_id, 3, chapter_id_1),
    )

    conn.execute(
        "INSERT INTO magic_use_log (chapter_id, scene_id, character_id, magic_element_id, "
        "action_description, compliance_status) VALUES (?, ?, ?, ?, ?, ?)",
        (chapter_id_1, scene_id_1_1, char_id_protagonist, magic_element_id,
         "Aeryn performs the ritual ember-binding seal on the forge-watch brazier at watch-close.",
         "compliant"),
    )

    conn.commit()

    # -----------------------------------------------------------------------
    # Phase 16: Character state tables
    # -----------------------------------------------------------------------

    conn.execute(
        "INSERT INTO character_knowledge (character_id, chapter_id, knowledge_type, content) "
        "VALUES (?, ?, ?, ?)",
        (char_id_protagonist, chapter_id_1, "discovery",
         "A vault reference appears in the archive manifest that has no corresponding record."),
    )

    conn.execute(
        "INSERT INTO character_beliefs (character_id, belief_type, content, strength, "
        "formed_chapter_id) VALUES (?, ?, ?, ?, ?)",
        (char_id_protagonist, "loyalty",
         "The Obsidian Court is the last bulwark against a second Collapse.",
         8, chapter_id_1),
    )

    conn.execute(
        "INSERT INTO character_locations (character_id, chapter_id, location_id) VALUES (?, ?, ?)",
        (char_id_protagonist, chapter_id_1, location_id),
    )

    conn.execute(
        "INSERT INTO injury_states (character_id, chapter_id, injury_type, description, severity) "
        "VALUES (?, ?, ?, ?, ?)",
        (char_id_rival, chapter_id_1, "psychological",
         "Festering resentment from the appointment slight; affects judgment under pressure.",
         "minor"),
    )

    conn.execute(
        "INSERT INTO title_states (character_id, chapter_id, title, granted_by) VALUES (?, ?, ?, ?)",
        (char_id_protagonist, chapter_id_1, "Keeper Third-Grade",
         "Obsidian Court Registry"),
    )

    conn.commit()

    # -----------------------------------------------------------------------
    # Phase 17: Voice tables
    # -----------------------------------------------------------------------

    conn.execute(
        "INSERT INTO voice_profiles (character_id, sentence_length, vocabulary_level, "
        "speech_patterns, verbal_tics, canon_status) VALUES (?, ?, ?, ?, ?, ?)",
        (char_id_protagonist, "mixed — short in crisis, longer when reasoning aloud",
         "formal with technical forge-vocabulary; drops register under stress",
         "Tends to repeat the last clause as a question when uncertain.",
         "Begins deflections with 'That's not — '",
         "approved"),
    )

    conn.execute(
        "INSERT INTO voice_drift_log (character_id, chapter_id, drift_type, description, severity) "
        "VALUES (?, ?, ?, ?, ?)",
        (char_id_protagonist, chapter_id_2, "register",
         "Aeryn slips into informal register mid-scene when startled — check for consistency.",
         "minor"),
    )

    conn.execute(
        "INSERT INTO supernatural_voice_guidelines (element_name, element_type, writing_rules, avoid) "
        "VALUES (?, ?, ?, ?)",
        ("Void-Echoes", "phenomenon",
         "Describe as fragmentary sensory intrusions — never full scenes. "
         "Keep under two sentences. Always anchor to a physical sensation first.",
         "Full dialogue, named figures, complete images."),
    )

    conn.commit()

    # -----------------------------------------------------------------------
    # Phase 18: Remaining junction / state tables
    # -----------------------------------------------------------------------

    # object_states requires artifact and chapter
    conn.execute(
        "INSERT INTO object_states (artifact_id, chapter_id, owner_id, location_id, condition) "
        "VALUES (?, ?, ?, ?, ?)",
        (artifact_id, chapter_id_1, char_id_mentor, location_id, "intact"),
    )

    # relationship_change_events
    conn.execute(
        "INSERT INTO relationship_change_events (relationship_id, chapter_id, event_id, "
        "change_type, description, bond_delta, trust_delta) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (relationship_id, chapter_id_1, event_id,
         "deepening",
         "Ithrel covers for Aeryn's late submission of the manifest anomaly report.",
         1, 2),
    )

    conn.commit()


def _load_gate_ready(conn: sqlite3.Connection) -> None:
    """Extend minimal seed to satisfy all 34 architecture gate checklist items.

    Calls _load_minimal() first, then adds the rows needed for each gate check.
    All queries are relational ('all X must have Y'), so 3 chapters / 5 characters
    / 6 scenes is sufficient — no need for 55 chapters or 6 POV characters.

    Seed IDs from minimal: characters 1-5, chapters 1-3, scenes 1-6,
    faction id=1 (Obsidian Court), location id=1 (The Ashen Citadel),
    book id=1, act id=1.
    """
    _load_minimal(conn)

    # --- voice_pov: all POV characters (ch1=char1, ch2=char1, ch3=char3) need voice_profiles ---
    # minimal has voice_profile for char 1 (protagonist) only; ch3 POV is char 3 (mentor)
    for char_id, speech, sentence_length in [
        (2, "Clipped, tactical, rarely offers more than necessary.", "short"),
        (3, "Measured and deliberate, always three steps ahead.", "long"),
        (4, "Warm but guarded; uses humour to deflect.", "mixed"),
        (5, "Formal register with archaic phrasing.", "long"),
    ]:
        conn.execute(
            "INSERT OR IGNORE INTO voice_profiles "
            "(character_id, speech_patterns, sentence_length, canon_status) "
            "VALUES (?, ?, ?, 'approved')",
            (char_id, speech, sentence_length),
        )

    # --- rel_pov_pairs: all POV character pairs need character_relationships ---
    # minimal has (1,3),(1,4),(1,5) — add (1,2) for antagonist and (3,*) pairs
    # Minimal seed chapters: ch1 POV=char1, ch2 POV=char1, ch3 POV=char3
    # POV chars are 1 and 3, so the only pair needed is (1,3) — already in minimal.
    # Add remaining character pairs for completeness and gate query coverage:
    for a, b, rel_type in [
        (1, 2, "rivalry"),
        (2, 3, "neutral"),
        (2, 4, "ally"),
        (2, 5, "rival"),
        (3, 4, "neutral"),
        (3, 5, "neutral"),
        (4, 5, "ally"),
    ]:
        conn.execute(
            "INSERT OR IGNORE INTO character_relationships "
            "(character_a_id, character_b_id, relationship_type, trust_level, "
            "bond_strength, current_status, canon_status) "
            "VALUES (?, ?, ?, 3, 2, 'neutral', 'approved')",
            (min(a, b), max(a, b), rel_type),
        )

    # --- rel_perception: all POV chars need >= 1 perception_profile entry ---
    # minimal has observer=1 -> subject=2 (antagonist); add observer=3 (mentor)
    conn.execute(
        "INSERT OR IGNORE INTO perception_profiles "
        "(observer_id, subject_id, trust_level, emotional_valence) "
        "VALUES (3, 1, 5, 'trusting')",
    )

    # --- struct_chapters_hooks: all 3 chapters need opening_hook_note + closing_hook_note ---
    for ch_id, opening, closing in [
        (1, "Open on the moment of refusal — Aeryn denies the summons.",
            "Close on the cost: the letter burns, but the seal is already copied."),
        (2, "Open mid-action — the citadel gate already closing.",
            "Close on a revelation: the informant is family."),
        (3, "Open in silence — the empty council chamber says everything.",
            "Close on a decision that cannot be undone."),
    ]:
        conn.execute(
            "UPDATE chapters SET opening_hook_note=?, closing_hook_note=? WHERE id=?",
            (opening, closing, ch_id),
        )

    # --- struct_chapter_obligations: chapters 2 and 3 need obligations (ch1 already in minimal) ---
    for ch_id, ob_type, desc in [
        (2, "introduce_complication", "Reveal the faction's deeper agenda behind the contract."),
        (3, "resolve_thread", "Close the 'missing seal' subplot before the midpoint break."),
    ]:
        conn.execute(
            "INSERT INTO chapter_structural_obligations "
            "(chapter_id, obligation_type, description) VALUES (?, ?, ?)",
            (ch_id, ob_type, desc),
        )

    # --- scene_goals: scenes 2-6 need scene_character_goals (scene 1 already in minimal) ---
    for scene_id, char_id, goal in [
        (2, 2, "Obtain the contract seal before Aeryn notices it missing."),
        (3, 1, "Reach the inner vault without triggering the ward sequence."),
        (4, 3, "Delay the council vote by any means necessary."),
        (5, 1, "Extract the informant without breaking cover."),
        (6, 2, "Confirm the seal is genuine — or expose the forgery."),
    ]:
        conn.execute(
            "INSERT OR IGNORE INTO scene_character_goals "
            "(scene_id, character_id, goal) VALUES (?, ?, ?)",
            (scene_id, char_id, goal),
        )

    # --- pacing_tension + pacing_beats: chapter 3 needs rows (ch1+ch2 already in minimal) ---
    conn.execute(
        "INSERT INTO tension_measurements "
        "(chapter_id, tension_level, measurement_type) VALUES (3, 7, 'overall')"
    )
    conn.execute(
        "INSERT INTO pacing_beats "
        "(chapter_id, beat_type, description) VALUES (3, 'climax', 'The council vote and its aftermath.')"
    )

    # --- canon_domains: need >= 3 distinct domains (minimal has 'world' only) ---
    for domain, fact in [
        ("politics", "The Obsidian Court controls all trade licences east of the Vel."),
        ("geography", "The Ashen Wastes cannot be crossed without a Kaelthari guide."),
    ]:
        conn.execute(
            "INSERT INTO canon_facts "
            "(domain, fact, certainty_level, canon_status) VALUES (?, ?, 'confirmed', 'approved')",
            (domain, fact),
        )

    # --- names_characters + names_locations: all 5 chars + location need name_registry ---
    # minimal has only 'Aeryn Vael'
    for name, entity_type in [
        ("Solvann Drex", "character"),
        ("Ithrel Cass", "character"),
        ("Mira Sundal", "character"),
        ("Calder Veth", "character"),
        ("The Ashen Citadel", "location"),
    ]:
        conn.execute(
            "INSERT OR IGNORE INTO name_registry "
            "(name, entity_type) VALUES (?, ?)",
            (name, entity_type),
        )

    # --- All 34 gate_checklist_items with item_key, category, description ---
    # Use INSERT OR IGNORE — minimal already has 'min_characters' row (if any)
    # Import GATE_ITEM_META from tools.gate to avoid duplication
    from novel.tools.gate import GATE_ITEM_META
    for item_key, meta in GATE_ITEM_META.items():
        conn.execute(
            "INSERT OR IGNORE INTO gate_checklist_items "
            "(gate_id, item_key, category, description) VALUES (1, ?, ?, ?)",
            (item_key, meta["category"], meta["description"]),
        )

    conn.commit()
