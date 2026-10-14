"""Report content rules (FR-18 to FR-20) and the wording check (FR-19), using engine output directly."""

from datetime import date

import pytest

from app.reports.generator import build_parent, build_student, personalize
from app.reports.render import render_html, render_pdf
from app.reports.wording import DISCLAIMER, EVIDENCE, SKILL_TEXT
from app.reports.wording_check import check_report
from app.scoring.config import FEATURES, SKILL_SIGNALS
from app.scoring.engine import score
from app.scoring.skills import SKILL_IDS
from app.sim.simulator import PERSONAS, Player, engine_inputs


def scores_and_summary(result: dict) -> tuple[dict, dict]:
    scores = {
        k: {
            "skill": k,
            "score": s["score"],
            "band": s["band"],
            "evidence": s["evidence"],
            "language_adjusted": s["language_adjusted"],
            "detail": {"signals": s["signals"], "cues": s.get("cues", [])},
        }
        for k, s in result["skills"].items()
    }
    from collections import Counter

    summary = {
        "profile": result["profile"],
        "patterns": result["patterns"],
        "error_tags": dict(Counter(t["tag"] for t in result["error_tags"])),
        "wrong_answers": 40,
    }
    return scores, summary


@pytest.fixture(scope="module", params=["balanced", "pressure_sensitive", "language_gap", "underconfident"])
def built(request, lookup, items_by_id):
    played = Player(PERSONAS[request.param], "11-14", lookup, date(2026, 10, 1)).play_cycle()
    return scores_and_summary(score(engine_inputs(played, "11-14", items_by_id), None, "1.0.0"))


@pytest.mark.parametrize("lang", ["en", "hi"])
def test_generated_reports_pass_the_wording_check(built, lang):
    scores, summary = built
    parent = build_parent(scores, summary, lang, "1.0.0", 7, 1)
    student = build_student(scores, summary, lang, "1.0.0", 1)
    assert check_report(parent) == []
    assert check_report(student) == []
    assert parent["disclaimer"] == student["disclaimer"] == DISCLAIMER[lang]
    assert len(student["strengths"]) <= 3 and len(student["areas_to_grow"]) <= 2 and student.get("action")
    assert len(parent["layers"]) == 5 and sum(len(layer["skills"]) for layer in parent["layers"]) == 24
    for finding in parent["strengths"] + parent["areas_to_grow"] + parent["patterns"]:
        assert finding["evidence_line"] and finding["evidence_level"] in ("High", "Medium")
    for area in parent["areas_to_grow"]:
        assert area["action_home"] and area["action_school"]
    assert "overall" not in parent and "rank" not in str(parent).lower()


def test_strengths_come_first_and_low_evidence_stays_internal(built):
    scores, summary = built
    parent = build_parent(scores, summary, "en", "1.0.0", 7, 1)
    shown = {f["skill_id"] for f in parent["strengths"] + parent["areas_to_grow"]}
    assert all(scores[s]["evidence"] in ("High", "Medium") for s in shown)
    for layer in parent["layers"]:
        for row in layer["skills"]:
            if scores[row["skill_id"]]["evidence"] == "Low":
                assert row["band"] == "insufficient"


def test_language_adjusted_skills_are_never_areas_to_grow(lookup, items_by_id):
    played = Player(PERSONAS["language_gap"], "11-14", lookup, date(2026, 10, 1)).play_cycle()
    scores, summary = scores_and_summary(score(engine_inputs(played, "11-14", items_by_id), None, "1.0.0"))
    parent = build_parent(scores, summary, "en", "1.0.0", 7, 1)
    adjusted = {k for k, s in scores.items() if s["language_adjusted"]}
    assert adjusted and not adjusted & {a["skill_id"] for a in parent["areas_to_grow"]}
    assert any(p["type"] == "language_adjustment" for p in parent["patterns"])


def test_wording_check_catches_banned_words():
    base = {
        "audience": "parent",
        "language": "en",
        "disclaimer": DISCLAIMER["en"],
        "strengths": [],
        "areas_to_grow": [],
        "patterns": [],
    }
    for text in (
        "Reading is weak",
        "a slow learner",
        "shows signs of ADHD",
        "may have dyslexia",
        "ranked 3rd in class",
        "class topper",
        "90th percentile",
    ):
        assert check_report({**base, "intro": text}), text
    assert check_report({**base, "intro": "पढ़ाई में कमज़ोर"})
    assert check_report({**base, "disclaimer": ""})[0]["rule"] == "missing_disclaimer"
    assert check_report({**base, "overall_score": 71})[0]["rule"] == "single_overall_number"
    assert check_report({**base, "intro": "Ask her to add the numbers, oddly enough."}) == []


def test_all_wording_tables_cover_every_skill_and_feature():
    assert set(SKILL_TEXT) == set(SKILL_IDS)
    for texts in SKILL_TEXT.values():
        assert set(texts) == {"en", "hi"} and all(len(t) == 6 for t in texts.values())
    used = {f for signals in SKILL_SIGNALS.values() for f, _ in signals}
    assert used <= set(EVIDENCE), used - set(EVIDENCE)
    assert used <= set(FEATURES)


def test_pdf_renders_in_hindi(built):
    scores, summary = built
    content = personalize(build_parent(scores, summary, "hi", "1.0.0", 7, 1), "रिया")
    html = render_html(content, "रिया")
    assert "रिया" in html and "{name}" not in html
    pdf = render_pdf(content, "रिया")
    assert pdf[:4] == b"%PDF" and len(pdf) > 5000
