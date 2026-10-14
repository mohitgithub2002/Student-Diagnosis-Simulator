"""Report generator (FR-18 to FR-20): parent and student reports from the same scores.

Content is stored as structured JSON with a "{name}" placeholder; names are filled in only when a parent
or the student views the report, so reviewers and stored data never carry the name.
"""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session as DbSession

from app.models import Cycle, Report, SkillScore, Student
from app.reports import wording as W
from app.reports.wording_check import check_report
from app.scoring.skills import SKILLS, SKILLS_BY_ID
from app.services.consent import current_consent

SHOWN = ("High", "Medium")


def _evidence_line(score: dict, lang: str, limit: int = 2) -> str:
    signals = sorted(score["detail"].get("signals", []), key=lambda s: (-(s.get("agrees") or False), -s["weight"]))
    phrases = []
    for sig in signals:
        phrase = W.evidence_phrase(sig["feature"], sig["value"], lang)
        if phrase:
            phrases.append(phrase)
        if len(phrases) >= limit:
            break
    return " ".join(phrases)


def _select(scores: dict[str, dict], summary: dict) -> tuple[list[dict], list[dict]]:
    mean = summary.get("profile", {}).get("mean", 0)
    usable = [s for s in scores.values() if s["band"] != "insufficient" and s["evidence"] in SHOWN]
    pressure_confirmed = any(
        p["type"] == "pressure_pattern" and p["evidence"] in SHOWN for p in summary.get("patterns", [])
    )
    clear = sorted([s for s in usable if s["band"] == "strength"], key=lambda s: -s["score"])
    relative = sorted([s for s in usable if s["band"] == "typical" and s["score"] > mean], key=lambda s: -s["score"])
    strengths = [{**s, "clear": True} for s in clear] + [{**s, "clear": False} for s in relative]

    def can_grow(s: dict) -> bool:
        if s["language_adjusted"]:
            return False  # language comfort is reported instead (Blueprint B: vocabulary cue)
        return not (s["skill"] == "pressure_sensitivity" and not pressure_confirmed)

    grow_clear = sorted([s for s in usable if s["band"] == "grow" and can_grow(s)], key=lambda s: s["score"])
    grow_fill = sorted(
        [s for s in usable if s["band"] == "typical" and s["score"] < mean and can_grow(s)], key=lambda s: s["score"]
    )
    areas = grow_clear + [s for s in grow_fill if s not in grow_clear]
    return strengths, areas


def build_parent(
    scores: dict[str, dict], summary: dict, lang: str, version: str, sessions_completed: int, cycle_number: int
) -> dict[str, Any]:
    ui = W.UI[lang]
    strengths, areas = _select(scores, summary)
    content: dict[str, Any] = {
        "audience": "parent",
        "language": lang,
        "scoring_version": version,
        "generated_at": datetime.now(UTC).isoformat(),
        "cycle": cycle_number,
        "title": ui["parent_title"],
        "intro": ui["intro"].replace("{sessions}", str(sessions_completed)),
        "strengths": [],
        "areas_to_grow": [],
        "patterns": [],
    }
    for s in strengths[:3]:
        text = W.SKILL_TEXT[s["skill"]][lang]
        content["strengths"].append(
            {
                "skill_id": s["skill"],
                "title": SKILLS_BY_ID[s["skill"]]["name"][lang],
                "text": text[1],
                "clear": s["clear"],
                "evidence_line": _evidence_line(s, lang),
                "evidence_level": s["evidence"],
            }
        )
    for s in areas[:3]:
        text = W.SKILL_TEXT[s["skill"]][lang]
        content["areas_to_grow"].append(
            {
                "skill_id": s["skill"],
                "title": SKILLS_BY_ID[s["skill"]]["name"][lang],
                "text": text[3],
                "action_home": text[4],
                "action_school": text[5],
                "evidence_line": _evidence_line(s, lang),
                "evidence_level": s["evidence"],
            }
        )
    for p in summary.get("patterns", []):
        if p["evidence"] not in SHOWN:
            continue
        key = f"{p['type']}:{p['direction']}" if p["type"] == "confidence_mismatch" else p["type"]
        texts = W.PATTERN_TEXT[key][lang]
        data = dict(p["data"])
        for field in ("relaxed", "pressure", "native", "english"):
            if field in data:
                data[field] = round(data[field] * 100)
        data["sessions"] = (" और " if lang == "hi" else " and ").join(str(x) for x in data.get("sessions", []))
        content["patterns"].append(
            {
                "type": p["type"],
                "text": texts[1],
                "evidence_line": texts[2].format(**data),
                "evidence_level": p["evidence"],
            }
        )
    tags = summary.get("error_tags", {})
    total_wrong = summary.get("wrong_answers", 0)
    tagged = sum(tags.values())
    content["root_causes"] = {
        "summary": ui["tagged"].format(tagged=tagged, total=total_wrong) if total_wrong else "",
        "items": [
            {"tag": tag, "label": W.TAG_TEXT[tag][lang][0], "count": count, "suggestion": W.TAG_TEXT[tag][lang][1]}
            for tag, count in sorted(tags.items(), key=lambda kv: (-kv[1], kv[0]))[:3]
        ],
    }
    content["layers"] = []
    for layer in ("cognitive", "academic", "metacognitive", "emotional", "behavioral"):
        from app.content.tasks import LAYERS

        rows = []
        for skill in [s for s in SKILLS if s["layer"] == layer]:
            sc = scores[skill["id"]]
            band = sc["band"] if sc["evidence"] in SHOWN else "insufficient"
            rows.append(
                {
                    "skill_id": skill["id"],
                    "title": skill["name"][lang],
                    "band": band,
                    "band_label": ui["band"][band],
                    "language_adjusted": sc["language_adjusted"],
                    "evidence_level": sc["evidence"] if band != "insufficient" else "",
                }
            )
        content["layers"].append({"layer": layer, "title": LAYERS[layer][lang], "skills": rows})
    early = sum(1 for s in scores.values() if s["band"] in ("strength", "grow") and s["evidence"] == "Low")
    early += sum(1 for p in summary.get("patterns", []) if p["evidence"] == "Low")
    content["early_signals"] = {"count": early, "text": ui["early_text"].format(n=early) if early else ""}
    notes = []
    for s in scores.values():
        if s["evidence"] in SHOWN:
            for cue in s["detail"].get("cues", []):
                if cue in W.CUE_TEXT:
                    notes.append({"skill_id": s["skill"], "text": W.CUE_TEXT[cue][lang]})
    content["notes"] = notes
    content["disclaimer"] = W.DISCLAIMER[lang]
    return content


def build_student(scores: dict[str, dict], summary: dict, lang: str, version: str, cycle_number: int) -> dict[str, Any]:
    ui = W.UI[lang]
    strengths, areas = _select(scores, summary)
    content: dict[str, Any] = {
        "audience": "student",
        "language": lang,
        "scoring_version": version,
        "generated_at": datetime.now(UTC).isoformat(),
        "cycle": cycle_number,
        "title": ui["student_title"],
        "intro": ui["student_intro"],
        "strengths": [
            {
                "skill_id": s["skill"],
                "title": SKILLS_BY_ID[s["skill"]]["name"][lang],
                "text": W.SKILL_TEXT[s["skill"]][lang][0],
            }
            for s in strengths[:3]
        ],
        "areas_to_grow": [
            {
                "skill_id": s["skill"],
                "title": SKILLS_BY_ID[s["skill"]]["name"][lang],
                "text": W.SKILL_TEXT[s["skill"]][lang][2],
            }
            for s in areas[:2]
        ],
    }
    if areas:
        content["action"] = W.STUDENT_ACTION[areas[0]["skill"]][lang]
    elif strengths:
        content["action"] = W.STUDENT_ACTION[strengths[0]["skill"]][lang]
    for p in summary.get("patterns", []):
        if p["evidence"] in SHOWN:
            key = f"{p['type']}:{p['direction']}" if p["type"] == "confidence_mismatch" else p["type"]
            content["note"] = W.PATTERN_TEXT[key][lang][0]
            break
    content["disclaimer"] = W.DISCLAIMER[lang]
    return content


def personalize(value: Any, name: str) -> Any:
    if isinstance(value, str):
        return value.replace("{name}", name)
    if isinstance(value, dict):
        return {k: personalize(v, name) for k, v in value.items()}
    if isinstance(value, list):
        return [personalize(v, name) for v in value]
    return value


def quality_flags(scores: dict[str, dict]) -> list[dict]:
    scored = sum(1 for s in scores.values() if s["band"] != "insufficient")
    if scored < 12:
        return [{"rule": "low_coverage", "path": "skills", "match": f"{scored} of 24 skills scored"}]
    return []


def scores_for(db: DbSession, cycle: Cycle) -> dict[str, dict]:
    rows = db.scalars(
        select(SkillScore).where(SkillScore.cycle_id == cycle.id, SkillScore.scoring_version == cycle.scoring_version)
    ).all()
    return {
        r.skill_id: {
            "skill": r.skill_id,
            "score": r.score,
            "band": r.relative_band,
            "evidence": r.evidence_level,
            "language_adjusted": r.language_adjusted,
            "detail": r.detail or {},
        }
        for r in rows
    }


def generate_reports(db: DbSession, cycle_id: int) -> list[Report]:
    cycle = db.get(Cycle, cycle_id)
    if cycle is None or not cycle.scoring_version:
        raise ValueError("cycle must be scored first")
    student = db.get(Student, cycle.student_id)
    consent = current_consent(db, cycle.student_id)
    parent_lang = "en"
    if student and student.guardians:
        guardian = next((g for g in student.guardians if consent and g.id == consent.guardian_id), student.guardians[0])
        parent_lang = guardian.language if guardian.language in ("en", "hi") else "en"
    student_lang = "hi" if student and student.language_pref == "hi" else "en"
    scores = scores_for(db, cycle)
    summary = cycle.summary or {}
    completed = sum(1 for s in cycle.sessions if s.status == "completed")

    db.execute(delete(Report).where(Report.cycle_id == cycle.id, Report.status != "released"))
    reports = []
    contents = [
        (
            "parent",
            parent_lang,
            build_parent(scores, summary, parent_lang, cycle.scoring_version, completed, cycle.number),
        ),
        ("student", student_lang, build_student(scores, summary, student_lang, cycle.scoring_version, cycle.number)),
    ]
    now = datetime.now(UTC)
    for audience, lang, content in contents:
        flags = check_report(content) + (quality_flags(scores) if audience == "parent" else [])
        report = Report(
            cycle_id=cycle.id,
            audience=audience,
            language=lang,
            scoring_version=cycle.scoring_version,
            content=content,
            wording_flags=flags,
            status="in_review" if flags else "released",
            released_at=None if flags else now,
        )
        db.add(report)
        reports.append(report)
    db.commit()
    return reports


def render_language_variant(db: DbSession, report: Report, language: str) -> dict:
    """Rebuild a released report's content in another language from the same stored scores (FR-20)."""
    cycle = db.get(Cycle, report.cycle_id)
    scores = scores_for(db, cycle)
    completed = sum(1 for s in cycle.sessions if s.status == "completed")
    if report.audience == "parent":
        return build_parent(scores, cycle.summary or {}, language, report.scoring_version, completed, cycle.number)
    return build_student(scores, cycle.summary or {}, language, report.scoring_version, cycle.number)
