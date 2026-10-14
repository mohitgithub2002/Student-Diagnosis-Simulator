"""Load a cycle from the database, run the engine with the active scoring config, store the results."""

from collections import Counter
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session as DbSession

from app.models import (
    Cycle,
    ErrorTag,
    Feature,
    Item,
    ItemEvent,
    ScoringConfig,
    SkillScore,
    Student,
    StudentVisit,
)
from app.scoring.engine import score


def active_config(db: DbSession) -> ScoringConfig:
    cfg = db.scalars(select(ScoringConfig).where(ScoringConfig.active.is_(True))).first()
    if cfg is None:
        from app.content.seed import seed_scoring_config

        seed_scoring_config(db)
        db.flush()
        cfg = db.scalars(select(ScoringConfig).where(ScoringConfig.active.is_(True))).one()
    return cfg


def load_inputs(db: DbSession, cycle: Cycle) -> dict[str, Any]:
    number_of = {s.id: s.number for s in cycle.sessions}
    rows = db.scalars(select(ItemEvent).where(ItemEvent.session_id.in_(list(number_of)))).all()
    items = {i.id: i for i in db.scalars(select(Item).where(Item.id.in_({r.item_id for r in rows}))).all()}
    events = []
    for r in rows:
        item = items.get(r.item_id)
        if item is None:
            continue
        events.append(
            {
                "id": r.id,
                "session": number_of[r.session_id],
                "task": r.task_id,
                "item_id": r.item_id,
                "seq": r.seq,
                "response_ms": r.response_ms,
                "first_click_ms": r.first_click_ms,
                "answer": r.answer,
                "correct": r.correct,
                "changes": r.changes,
                "change_log": r.change_log or [],
                "skipped": r.skipped,
                "retries": r.retries,
                "confidence": r.confidence,
                "idle_ms": r.idle_ms,
                "max_idle_ms": r.max_idle_ms,
                "switches": r.switches,
                "level": item.level,
                "language": r.language,
                "condition": r.condition,
                "extra": r.extra or {},
                "content": item.content,
                "key": item.answer_key,
                "tags": item.tags or [],
                "variant_group": item.variant_group,
                "kind": item.content.get("kind"),
            }
        )
    client = [
        {
            "session": number_of[f.session_id],
            "name": f.name,
            "value": f.value,
            "channel": f.source_channel,
            "task": f.task_id,
            "item_id": f.item_id,
        }
        for f in db.scalars(
            select(Feature).where(Feature.session_id.in_(list(number_of)), Feature.derived.is_(False))
        ).all()
    ]
    visits = [v.at for v in db.scalars(select(StudentVisit).where(StudentVisit.student_id == cycle.student_id))]
    text_langs = Counter(e["language"] for e in events if e["task"] in ("T8", "T9"))
    student = db.get(Student, cycle.student_id)
    text_language = text_langs.most_common(1)[0][0] if text_langs else (student.language_pref if student else "en")
    sessions = [
        {
            "number": s.number,
            "scheduled_for": s.scheduled_for,
            "started_at": s.started_at,
            "completed_at": s.completed_at,
        }
        for s in cycle.sessions
    ]
    return {
        "age_band": cycle.age_band,
        "events": events,
        "client_features": client,
        "sessions": sessions,
        "visits": visits,
        "text_language": "en" if text_language == "en" else text_language,
    }


def score_cycle(db: DbSession, cycle_id: int) -> dict[str, Any]:
    cycle = db.get(Cycle, cycle_id)
    if cycle is None:
        raise ValueError(f"cycle {cycle_id} not found")
    cfg = active_config(db)
    inputs = load_inputs(db, cycle)
    result = score(inputs, cfg.config, cfg.version)
    session_id = {s.number: s.id for s in cycle.sessions}

    db.execute(delete(Feature).where(Feature.session_id.in_(list(session_id.values())), Feature.derived.is_(True)))
    db.execute(delete(SkillScore).where(SkillScore.cycle_id == cycle.id, SkillScore.scoring_version == cfg.version))
    db.execute(delete(ErrorTag).where(ErrorTag.cycle_id == cycle.id, ErrorTag.scoring_version == cfg.version))
    for f in result["features"]:
        if f["session"] in session_id:
            db.add(
                Feature(
                    session_id=session_id[f["session"]],
                    name=f["name"],
                    value=f["value"],
                    source_channel=f["channel"],
                    task_id=f["task"],
                    derived=True,
                )
            )
    for skill, s in result["skills"].items():
        db.add(
            SkillScore(
                cycle_id=cycle.id,
                skill_id=skill,
                score=s["score"],
                raw_score=s["raw_score"],
                evidence_level=s["evidence"],
                relative_band=s["band"],
                language_adjusted=s["language_adjusted"],
                scoring_version=cfg.version,
                detail={
                    "signals": s["signals"],
                    "gate": s["gate"],
                    "agreeing": s["agreeing"],
                    "agree_sessions": s["agree_sessions"],
                    "cues": s.get("cues", []),
                },
            )
        )
    for t in result["error_tags"]:
        db.add(
            ErrorTag(
                cycle_id=cycle.id,
                item_event_id=t["event_id"],
                item_id=t["item_id"],
                tag=t["tag"],
                rule_id=t["rule_id"],
                scoring_version=cfg.version,
            )
        )
    tag_counts = Counter(t["tag"] for t in result["error_tags"])
    wrong_total = sum(1 for e in inputs.get("events", []) if e.get("correct") is False)
    cycle.summary = {
        "profile": result["profile"],
        "patterns": result["patterns"],
        "error_tags": dict(tag_counts),
        "wrong_answers": wrong_total,
        "flags": result["flags"],
        "language_gap": result["language_gap"],
        "rated_items": result["rated_items"],
        "distraction_events": len(result["distraction_event_ids"]),
    }
    cycle.status = "scored"
    cycle.scored_at = datetime.now(UTC)
    cycle.scoring_version = cfg.version
    db.commit()
    return result
