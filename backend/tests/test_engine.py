"""Scoring engine behaviour on simulated personas with planted patterns."""

import json
from collections import Counter
from datetime import date

import pytest

from app.scoring.engine import evidence_level, normalize, score
from app.scoring.skills import SKILL_IDS
from app.sim.simulator import PERSONAS, Persona, Player, engine_inputs


def run(persona: Persona, lookup, items_by_id, band="11-14", config=None):
    played = Player(persona, band, lookup, date(2026, 10, 1)).play_cycle()
    return score(engine_inputs(played, band, items_by_id), config, "test")


@pytest.fixture(scope="module")
def results(lookup, items_by_id):
    return {name: run(p, lookup, items_by_id) for name, p in PERSONAS.items()}


def test_all_24_skills_scored_for_a_complete_cycle(results):
    r = results["balanced"]
    assert set(r["skills"]) == set(SKILL_IDS)
    assert all(s["score"] is not None for s in r["skills"].values())
    assert all(s["evidence"] in ("High", "Medium", "Low") for s in r["skills"].values())


def test_every_scored_skill_rests_on_two_or_more_signals(results):
    for r in results.values():
        for s in r["skills"].values():
            if s["score"] is not None:
                assert len(s["signals"]) >= 2


def test_deterministic(lookup, items_by_id):
    a = run(PERSONAS["balanced"], lookup, items_by_id)
    b = run(PERSONAS["balanced"], lookup, items_by_id)
    assert json.dumps(a, sort_keys=True, default=str) == json.dumps(b, sort_keys=True, default=str)


def test_pressure_sensitive_persona(results):
    r = results["pressure_sensitive"]
    pattern = next(p for p in r["patterns"] if p["type"] == "pressure_pattern")
    assert pattern["evidence"] in ("High", "Medium")
    assert pattern["data"]["sessions"] == [5, 7]
    assert r["skills"]["pressure_sensitivity"]["score"] < results["balanced"]["skills"]["pressure_sensitivity"]["score"]
    assert any(t["tag"] == "pressure_error" for t in r["error_tags"])


def test_language_gap_persona_gets_adjusted_scores(results):
    r = results["language_gap"]
    assert r["language_gap"] > 0.15
    adjusted = [k for k, s in r["skills"].items() if s["language_adjusted"]]
    assert set(adjusted) <= {"reading_fluency", "reading_comprehension", "vocabulary", "expression"}
    assert adjusted
    pattern = next(p for p in r["patterns"] if p["type"] == "language_adjustment")
    assert pattern["evidence"] in ("High", "Medium")


def test_underconfident_persona(results):
    r = results["underconfident"]
    pattern = next(p for p in r["patterns"] if p["type"] == "confidence_mismatch")
    assert pattern["direction"] == "underconfident"
    assert pattern["evidence"] in ("High", "Medium")


def test_careless_persona_gets_careless_tags(results):
    careless = Counter(t["tag"] for t in results["careless"]["error_tags"])["careless_slip"]
    balanced = Counter(t["tag"] for t in results["balanced"]["error_tags"])["careless_slip"]
    assert careless >= 8
    assert careless > 2 * balanced


def test_strong_memory_is_a_strength(results):
    wm = results["strong_memory"]["skills"]["working_memory"]
    assert wm["band"] == "strength"
    assert wm["evidence"] in ("High", "Medium")


def test_tags_only_on_wrong_answers_and_one_each(results, lookup, items_by_id):
    for r in results.values():
        ids = [t["event_id"] for t in r["error_tags"]]
        assert len(ids) == len(set(ids))
        assert {t["tag"] for t in r["error_tags"]} <= {
            "concept_gap",
            "careless_slip",
            "pressure_error",
            "language_barrier",
            "attention_lapse",
            "guess",
        }


def test_calibration_needs_60_rated_items(lookup, items_by_id):
    played = Player(PERSONAS["balanced"], "11-14", lookup, date(2026, 10, 1)).play_cycle()
    inputs = engine_inputs(played, "11-14", items_by_id)
    for e in inputs["events"]:
        e["confidence"] = None
    r = score(inputs, None, "test")
    assert r["skills"]["calibration"]["score"] is None
    assert "60" in r["skills"]["calibration"]["gate"]


def test_missing_sessions_lower_evidence(lookup, items_by_id):
    played = Player(PERSONAS["balanced"], "11-14", lookup, date(2026, 10, 1)).play_cycle()
    played["sessions"] = [s for s in played["sessions"] if s["number"] in (1, 2, 3)]
    r = score(engine_inputs(played, "11-14", items_by_id), None, "test")
    assert r["skills"]["pressure_sensitivity"]["score"] is None
    assert r["skills"]["sustained_attention"]["score"] is None


def test_evidence_levels():
    assert evidence_level(3, 2) == "High"
    assert evidence_level(2, 2) == "Medium"
    assert evidence_level(3, 1) == "Medium"
    assert evidence_level(2, 1) == "Low"
    assert evidence_level(1, 3) == "Low"


def test_normalize_respects_band_and_direction():
    cfg = {"x": {"lo": 0, "hi": 10}, "y": {"lo": 0, "hi": 10, "invert": True, "bands": {"15-18": [0, 20]}}}
    assert normalize("x", 5, "11-14", cfg) == 50
    assert normalize("x", 20, "11-14", cfg) == 100
    assert normalize("y", 5, "11-14", cfg) == 50
    assert normalize("y", 5, "15-18", cfg) == 75


def test_config_version_changes_scores(lookup, items_by_id):
    import copy

    from app.scoring.config import DEFAULT_CONFIG

    cfg = copy.deepcopy(DEFAULT_CONFIG)
    cfg["skills"]["working_memory"] = [["t1.forward_span", 1], ["t1.accuracy", 1]]
    a = run(PERSONAS["strong_memory"], lookup, items_by_id)
    b = run(PERSONAS["strong_memory"], lookup, items_by_id, config=cfg)
    assert [s["feature"] for s in b["skills"]["working_memory"]["signals"]] == ["t1.forward_span", "t1.accuracy"]
    assert a["skills"]["working_memory"]["score"] != b["skills"]["working_memory"]["score"]
