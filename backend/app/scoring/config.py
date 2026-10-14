"""Default scoring configuration (version 1.0.0).

Weights follow the Blueprint tables. Normalization ranges map each raw feature to 0-100 for an age band
until pilot norms exist. Everything marked PILOT is a placeholder to be set from pilot data; edits go
through a new ScoringConfig version in the admin console so every report stays traceable (FR-27).
"""

import copy

DEFAULT_VERSION = "1.0.0"

# feature -> {"lo", "hi", "invert"?, "bands"?: {band: [lo, hi]}}  (PILOT ranges)
FEATURES: dict[str, dict] = {
    "t1.forward_span": {"lo": 3, "hi": 8, "bands": {"15-18": [3, 9]}},
    "t1.backward_span": {"lo": 2, "hi": 7, "bands": {"15-18": [2, 8]}},
    "t1.accuracy": {"lo": 0.3, "hi": 1.0},
    "t5.long_chain_acc": {"lo": 0.0, "hi": 1.0},
    "t2.retention": {"lo": 0.4, "hi": 1.0},
    "t2.delayed_acc": {"lo": 0.25, "hi": 1.0},
    "t2.false_alarm_rate": {"lo": 0.0, "hi": 0.75, "invert": True},
    "t12.recall_acc": {"lo": 0.25, "hi": 1.0},
    "t3.hit_minus_fa": {"lo": 0.2, "hi": 0.95},
    "t3.rt_cv": {"lo": 0.15, "hi": 0.6, "invert": True},
    "t3.decline": {"lo": 0.0, "hi": 0.4, "invert": True},
    "all.distraction_rate": {"lo": 0.0, "hi": 0.3, "invert": True},
    "t4.median_rt_correct": {"lo": 700, "hi": 2200, "invert": True, "bands": {"15-18": [600, 1900]}},
    "t10.median_rt_correct": {"lo": 1500, "hi": 6000, "invert": True, "bands": {"15-18": [1200, 5000]}},
    "all.median_rt_correct": {"lo": 1000, "hi": 6000, "invert": True},
    "t5.level": {"lo": 1, "hi": 10},
    "t5.accuracy": {"lo": 0.3, "hi": 1.0},
    "t14.accuracy": {"lo": 0.0, "hi": 1.0},
    "t5.time_per_step": {"lo": 2000, "hi": 15000, "invert": True},
    "t6.level": {"lo": 1, "hi": 10},
    "t6.sequence_acc": {"lo": 0.25, "hi": 1.0},
    "t6.rotation_acc": {"lo": 0.25, "hi": 1.0},
    "t6.near_miss_share": {"lo": 0.0, "hi": 1.0},
    "t7.wpm_acc": {"lo": 60, "hi": 160, "bands": {"15-18": [80, 190]}},
    "t7.pause_rate": {"lo": 2, "hi": 20, "invert": True},
    "t8.silent_time_per_100w": {"lo": 25, "hi": 90, "invert": True, "bands": {"15-18": [20, 75]}},
    "t8.inference_acc": {"lo": 0.25, "hi": 1.0},
    "t8.direct_acc": {"lo": 0.25, "hi": 1.0},
    "t8.reread_rate": {"lo": 0.0, "hi": 2.0, "invert": True},
    "t9.weighted_acc": {"lo": 0.25, "hi": 1.0},
    "t9.accuracy": {"lo": 0.25, "hi": 1.0},
    "t9.clue_use": {"lo": 0.0, "hi": 0.6},
    "t11.unique_ratio": {"lo": 0.3, "hi": 0.8},
    "t10.estimate_acc": {"lo": 0.75, "hi": 1.0},
    "t10.compare_acc": {"lo": 0.5, "hi": 1.0},
    "t11.rubric": {"lo": 1, "hi": 4},
    "t22.rubric": {"lo": 1, "hi": 4},
    "t11.pause_rate": {"lo": 2, "hi": 20, "invert": True},
    "t12.far_acc": {"lo": 0.25, "hi": 1.0},
    "t12.near_acc": {"lo": 0.25, "hi": 1.0},
    "t12.gain": {"lo": -0.25, "hi": 0.5},
    "conf.abs_gap": {"lo": 0.0, "hi": 0.4, "invert": True},
    "conf.resolution": {"lo": -0.1, "hi": 0.4},
    "conf.hesitation_link": {"lo": -2000, "hi": 4000},
    "all.net_changes": {"lo": -0.5, "hi": 0.5},
    "t14.efficiency": {"lo": 0.6, "hi": 1.0},
    "t14.plan_ratio": {"lo": 0.05, "hi": 0.5},
    "t14.restarts": {"lo": 0.0, "hi": 3.0, "invert": True},
    "t5.first_click_ratio": {"lo": 0.1, "hi": 0.7},
    "t15.detection_rate": {"lo": 0.33, "hi": 1.0},
    "t15.review_net": {"lo": -0.34, "hi": 0.34},
    "t7.self_corrections": {"lo": 0.0, "hi": 4.0},
    "t16.fit": {"lo": 0.4, "hi": 1.0},
    "t16.unfinished_share": {"lo": 0.0, "hi": 0.6, "invert": True},
    "t16.unused_share": {"lo": 0.0, "hi": 0.5, "invert": True},
    "t17.timeout_share": {"lo": 0.0, "hi": 0.5, "invert": True},
    "conf.mean": {"lo": 0.2, "hi": 0.9},
    "t18.hard_share": {"lo": 0.0, "hi": 1.0},
    "all.hesitation": {"lo": 800, "hi": 8000, "invert": True},
    "t17.drop": {"lo": -0.05, "hi": 0.4, "invert": True},
    "t17.change_skip_increase": {"lo": 0.0, "hi": 0.3, "invert": True},
    "t17.rt_cv_change": {"lo": 0.0, "hi": 0.3, "invert": True},
    "t18.after_error_easy": {"lo": 0.0, "hi": 1.0, "invert": True},
    "t18.bonus": {"lo": 0.0, "hi": 1.0},
    "log.return_rate": {"lo": 0.0, "hi": 1.0},
    "t19.persist_s": {"lo": 5, "hi": 75, "bands": {"15-18": [8, 80]}},
    "t19.attempts": {"lo": 1, "hi": 4},
    "t20.retry_rate": {"lo": 0.0, "hi": 1.0},
    "t20.retry_after_ability": {"lo": 0.0, "hi": 1.0},
    "all.post_error_acc": {"lo": 0.3, "hi": 1.0},
    "log.on_schedule_rate": {"lo": 0.3, "hi": 1.0},
    "log.completion_rate": {"lo": 0.4, "hi": 1.0},
    "t21.study_days": {"lo": 0, "hi": 7},
    "t22.answered_rate": {"lo": 0.4, "hi": 1.0},
    "t22.mean_words": {"lo": 5, "hi": 50},
    "t22.speech_start_ms": {"lo": 500, "hi": 6000, "invert": True},
    "t11.word_count": {"lo": 5, "hi": 60},
    "t23.english_relative": {"lo": 0.6, "hi": 1.0},
    "t23.en_acc": {"lo": 0.33, "hi": 1.0},
    "t23.rt_ratio_inv": {"lo": 0.6, "hi": 1.1},
}

# skill -> list of [feature, weight]. Weight 0 = agreement-only signal (counts as evidence, not in the score).
SKILL_SIGNALS: dict[str, list[list]] = {
    "working_memory": [
        ["t1.backward_span", 2],
        ["t1.forward_span", 1],
        ["t1.accuracy", 0.5],
        ["t5.long_chain_acc", 0.5],
    ],
    "long_term_recall": [
        ["t2.retention", 2],
        ["t2.delayed_acc", 1],
        ["t2.false_alarm_rate", 0.5],
        ["t12.recall_acc", 1],
    ],
    "sustained_attention": [["t3.hit_minus_fa", 2], ["t3.rt_cv", 1], ["t3.decline", 1], ["all.distraction_rate", 1]],
    "processing_speed": [["t4.median_rt_correct", 1], ["t10.median_rt_correct", 1], ["all.median_rt_correct", 0.5]],
    "logical_reasoning": [["t5.level", 2], ["t5.accuracy", 1], ["t14.accuracy", 1], ["t5.time_per_step", 0.5]],
    "pattern_spatial": [["t6.level", 2], ["t6.sequence_acc", 1], ["t6.rotation_acc", 1], ["t6.near_miss_share", 0.5]],
    "reading_fluency": [["t7.wpm_acc", 2], ["t7.pause_rate", 0.5], ["t8.silent_time_per_100w", 1]],
    "reading_comprehension": [
        ["t8.inference_acc", 0.6],
        ["t8.direct_acc", 0.4],
        ["t8.reread_rate", 0],
        ["t9.accuracy", 0],
    ],
    "vocabulary": [["t9.weighted_acc", 2], ["t11.unique_ratio", 1], ["t9.clue_use", 0]],
    "number_sense": [["t10.estimate_acc", 1], ["t10.compare_acc", 1], ["t10.median_rt_correct", 0]],
    "expression": [["t11.rubric", 1], ["t22.rubric", 1], ["t11.pause_rate", 0.5]],
    "concept_transfer": [["t12.far_acc", 3], ["t12.near_acc", 2], ["t12.recall_acc", 1], ["t12.gain", 0]],
    "calibration": [
        ["conf.abs_gap", 2],
        ["conf.resolution", 1],
        ["all.net_changes", 0.5],
        ["conf.hesitation_link", 0.5],
    ],
    "strategy_planning": [
        ["t14.efficiency", 2],
        ["t14.plan_ratio", 1],
        ["t14.restarts", 1],
        ["t5.first_click_ratio", 0.5],
    ],
    "error_detection": [
        ["t15.detection_rate", 2],
        ["all.net_changes", 1],
        ["t15.review_net", 1],
        ["t7.self_corrections", 0.5],
    ],
    "time_management": [
        ["t16.fit", 1],
        ["t16.unfinished_share", 1],
        ["t16.unused_share", 0.5],
        ["t17.timeout_share", 0.5],
    ],
    "confidence": [["conf.mean", 1], ["t18.hard_share", 1], ["all.hesitation", 0.5]],
    "pressure_sensitivity": [["t17.drop", 2], ["t17.change_skip_increase", 1], ["t17.rt_cv_change", 0.5]],
    "motivation": [["t18.hard_share", 1], ["log.return_rate", 1], ["t18.bonus", 0.5], ["t18.after_error_easy", 0.5]],
    "resilience": [["t19.persist_s", 1], ["t20.retry_rate", 1], ["all.post_error_acc", 1]],
    "growth_mindset": [
        ["t20.retry_rate", 1],
        ["t18.hard_share", 1],
        ["t19.attempts", 0.5],
        ["t20.retry_after_ability", 0.5],
    ],
    "study_consistency": [
        ["log.on_schedule_rate", 1],
        ["log.return_rate", 1],
        ["log.completion_rate", 0.5],
        ["t21.study_days", 0.5],
    ],
    "communication": [
        ["t22.answered_rate", 1],
        ["t22.mean_words", 1],
        ["t22.speech_start_ms", 0.5],
        ["t11.word_count", 0.5],
    ],
    "language_comfort": [["t23.english_relative", 2], ["t23.en_acc", 1], ["t23.rt_ratio_inv", 1]],
}

THRESHOLDS: dict = {
    # Noise guard: drop items answered in under 1 second or with long idle gaps from speed and accuracy.
    "noise_min_response_ms": 1000,
    "noise_exempt_tasks": ["T3", "T4", "T10", "T17"],  # rapid-response tasks by design
    "noise_max_idle_ms": 20000,
    # Relative profile (student vs own average across all scored skills).
    "relative_sd": 1.0,
    "min_profile_sd": 5.0,
    "agreement_sd": 0.5,
    "min_signals": 2,
    # Skill-specific rules from the Blueprint.
    "speed_min_accuracy": 0.8,
    "span_accuracy": 0.8,
    "calibration_min_items": 60,
    "growth_min_events": 3,
    "pressure_drop_threshold": 0.15,  # PILOT
    "language_gap_threshold": 0.15,  # PILOT
    "language_gap_min_items": 2,  # at least this many more matched items right in Hindi/Hinglish
    "language_adjust_factor": 0.5,  # PILOT
    "language_adjusted_skills": ["reading_fluency", "reading_comprehension", "vocabulary", "expression"],
    "mismatch_gap": 0.15,
    "unsure_correct_share": 0.5,
    "sure_wrong_share": 0.6,
    # Root-cause tagging.
    "careless_rt_ratio": 0.5,
    "guess_rt_ratio": 0.5,
    "guess_level_margin": 2,
    "guess_chance_margin": 0.15,
    "concept_min_errors": 3,
    "concept_rt_ratio": 0.8,
    "pressure_idle_ms": 3000,
    "attention_idle_ms": 5000,
    "language_rt_ratio": 1.3,
}

DEFAULT_CONFIG: dict = {"features": FEATURES, "skills": SKILL_SIGNALS, "thresholds": THRESHOLDS}


def merged(config: dict | None) -> dict:
    """Fill gaps in a stored config with defaults so older versions still score."""
    base = copy.deepcopy(DEFAULT_CONFIG)
    if not config:
        return base
    for key in ("features", "skills", "thresholds"):
        base[key].update(config.get(key, {}))
    return base


def validate(config: dict) -> list[str]:
    errors = []
    cfg = merged(config)
    for skill, signals in cfg["skills"].items():
        for feature, weight in signals:
            if feature not in cfg["features"]:
                errors.append(f"{skill}: unknown feature {feature}")
            if not isinstance(weight, int | float) or weight < 0:
                errors.append(f"{skill}: weight for {feature} must be a non-negative number")
    for name, spec in cfg["features"].items():
        if spec.get("hi") == spec.get("lo"):
            errors.append(f"{name}: lo and hi must differ")
    return errors
