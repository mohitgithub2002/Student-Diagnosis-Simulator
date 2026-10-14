"""Internal admin console (FR-25 to FR-27): item bank, review queue, versioned scoring config, audit log.
Reviewers see de-identified data only: no names, phones or raw media."""

import statistics
from collections import defaultdict
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import case, func, select, update
from sqlalchemy.orm import Session

from app.api.schemas import ItemIn, ItemPatch, ReportEdit, ScoringConfigIn
from app.content.tasks import TASKS
from app.core.audit import audit
from app.core.db import get_db
from app.core.deps import Principal, require_roles
from app.core.security import pseudonym
from app.models import AuditLog, Cycle, ErrorTag, Feature, Item, ItemEvent, Report, ScoringConfig
from app.models import Session as Sess
from app.reports.generator import personalize
from app.reports.render import render_html
from app.reports.wording_check import check_report
from app.scoring.config import DEFAULT_CONFIG, validate
from app.workers.jobs import dispatch

router = APIRouter(prefix="/admin", tags=["admin"])
reviewer = require_roles("reviewer", "superadmin")
superadmin = require_roles("superadmin")
BLOCKING = {"banned_word", "missing_disclaimer", "single_overall_number"}


@router.get("/tasks")
def tasks(_: Principal = Depends(reviewer), db: Session = Depends(get_db)) -> list[dict]:
    counts = dict(
        db.execute(select(Item.task_id, func.count()).where(Item.status == "active").group_by(Item.task_id)).all()
    )
    return [
        {
            "id": t["id"],
            "name": t["name"],
            "layer": t["layer"],
            "primitive": t["primitive"],
            "sessions": t["sessions"],
            "adaptive": t.get("adaptive", False),
            "active_items": counts.get(t["id"], 0),
        }
        for t in TASKS
    ]


@router.get("/items")
def list_items(
    task_id: str | None = None,
    age_band: str | None = None,
    language: str | None = None,
    level: int | None = None,
    status_: str | None = Query(default=None, alias="status"),
    tag: str | None = None,
    limit: int = Query(default=100, le=500),
    offset: int = 0,
    _: Principal = Depends(reviewer),
    db: Session = Depends(get_db),
) -> dict:
    q = select(Item)
    for col, val in (
        (Item.task_id, task_id),
        (Item.age_band, age_band),
        (Item.language, language),
        (Item.level, level),
        (Item.status, status_),
    ):
        if val is not None:
            q = q.where(col == val)
    rows = db.scalars(q.order_by(Item.task_id, Item.age_band, Item.level, Item.id)).all()
    if tag:
        rows = [r for r in rows if tag in (r.tags or [])]
    page = rows[offset : offset + limit]
    return {"total": len(rows), "items": [_item(r) for r in page]}


def _item(r: Item) -> dict:
    return {
        "id": r.id,
        "task_id": r.task_id,
        "age_band": r.age_band,
        "level": r.level,
        "language": r.language,
        "content": r.content,
        "answer_key": r.answer_key,
        "tags": r.tags,
        "variant_group": r.variant_group,
        "status": r.status,
    }


@router.post("/items", status_code=201)
def add_item(body: ItemIn, principal: Principal = Depends(reviewer), db: Session = Depends(get_db)) -> dict:
    if db.get(Item, body.id):
        raise HTTPException(status.HTTP_409_CONFLICT, "An item with this id already exists")
    if body.task_id not in {t["id"] for t in TASKS}:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Unknown task")
    if "kind" not in body.content:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "content.kind is required")
    item = Item(**body.model_dump())
    db.add(item)
    audit(db, principal, "item_added", "item", body.id)
    db.commit()
    return _item(item)


@router.patch("/items/{item_id}")
def patch_item(
    item_id: str, body: ItemPatch, principal: Principal = Depends(reviewer), db: Session = Depends(get_db)
) -> dict:
    item = db.get(Item, item_id)
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Item not found")
    changes = body.model_dump(exclude_none=True)
    for k, v in changes.items():
        setattr(item, k, v)
    audit(db, principal, "item_updated", "item", item_id, fields=sorted(changes))
    db.commit()
    return _item(item)


@router.get("/items/stats")
def item_stats(
    task_id: str | None = None, min_n: int = 1, _: Principal = Depends(reviewer), db: Session = Depends(get_db)
) -> list[dict]:
    """Difficulty (share correct), median response time and root-cause tag counts per item."""
    q = (
        select(
            ItemEvent.item_id,
            func.count(),
            func.avg(case((ItemEvent.correct.is_(True), 1.0), else_=0.0)),
            func.percentile_cont(0.5).within_group(ItemEvent.response_ms),
        )
        .where(ItemEvent.correct.is_not(None))
        .group_by(ItemEvent.item_id)
    )
    if task_id:
        q = q.where(ItemEvent.item_id.like(f"{task_id}-%"))
    tags: dict[str, dict[str, int]] = defaultdict(dict)
    for item_id, tag, n in db.execute(
        select(ErrorTag.item_id, ErrorTag.tag, func.count()).group_by(ErrorTag.item_id, ErrorTag.tag)
    ).all():
        tags[item_id][tag] = n
    out = []
    for item_id, n, p, med in db.execute(q).all():
        if n < min_n:
            continue
        out.append(
            {
                "item_id": item_id,
                "n": n,
                "p_correct": round(float(p or 0), 3),
                "median_rt_ms": round(float(med)) if med is not None else None,
                "error_tags": tags.get(item_id, {}),
            }
        )
    return sorted(out, key=lambda r: r["p_correct"])


@router.get("/reliability")
def reliability(_: Principal = Depends(reviewer), db: Session = Depends(get_db)) -> dict:
    """Retest reliability on repeated tasks (PRD success metric: r >= 0.7 for T1, T3, T17)."""
    pairs = {
        "t1.backward_span": (1, 7),
        "t1.forward_span": (1, 7),
        "t3.hit_minus_fa": (4, 7),
        "t17.relaxed_acc": (5, 7),
        "t17.drop": (5, 7),
    }
    rows = db.execute(
        select(Sess.cycle_id, Sess.number, Feature.name, Feature.value)
        .join(Feature, Feature.session_id == Sess.id)
        .where(Feature.derived.is_(True), Feature.name.in_(list(pairs)))
    ).all()
    values: dict[str, dict[int, dict[int, float]]] = defaultdict(lambda: defaultdict(dict))
    for cycle_id, number, name, value in rows:
        values[name][cycle_id][number] = value
    out = {}
    for name, (a, b) in pairs.items():
        xs, ys = [], []
        for per in values[name].values():
            if a in per and b in per:
                xs.append(per[a])
                ys.append(per[b])
        r = None
        if len(xs) >= 3 and statistics.pstdev(xs) > 0 and statistics.pstdev(ys) > 0:
            r = round(statistics.correlation(xs, ys), 3)
        out[name] = {"sessions": [a, b], "n": len(xs), "r": r}
    return out


def _deidentified(report: Report) -> dict:
    return personalize(report.content, "छात्र" if report.language == "hi" else "the student")


@router.get("/review-queue")
def review_queue(_: Principal = Depends(reviewer), db: Session = Depends(get_db)) -> list[dict]:
    rows = db.execute(
        select(Report, Cycle.student_id)
        .join(Cycle, Cycle.id == Report.cycle_id)
        .where(Report.status == "in_review")
        .order_by(Report.created_at)
    ).all()
    return [
        {
            "id": r.id,
            "student_ref": pseudonym(sid),
            "audience": r.audience,
            "language": r.language,
            "scoring_version": r.scoring_version,
            "flags": r.wording_flags,
            "created_at": r.created_at,
        }
        for r, sid in rows
    ]


@router.get("/reports/{report_id}")
def get_report(report_id: int, principal: Principal = Depends(reviewer), db: Session = Depends(get_db)) -> dict:
    report = db.get(Report, report_id)
    if report is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Report not found")
    cycle = db.get(Cycle, report.cycle_id)
    audit(db, principal, "report_reviewed_view", "report", report.id)
    db.commit()
    content = _deidentified(report)
    return {
        "id": report.id,
        "student_ref": pseudonym(cycle.student_id),
        "status": report.status,
        "audience": report.audience,
        "language": report.language,
        "scoring_version": report.scoring_version,
        "flags": report.wording_flags,
        "content": report.content,
        "preview_html": render_html(content, "छात्र" if report.language == "hi" else "the student"),
    }


@router.put("/reports/{report_id}")
def edit_report(
    report_id: int, body: ReportEdit, principal: Principal = Depends(reviewer), db: Session = Depends(get_db)
) -> dict:
    report = db.get(Report, report_id)
    if report is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Report not found")
    if report.status == "released":
        raise HTTPException(status.HTTP_409_CONFLICT, "Released reports cannot be edited")
    report.content = body.content
    report.wording_flags = check_report(body.content)
    report.reviewed_by = principal.actor_id
    report.reviewed_at = datetime.now(UTC)
    audit(db, principal, "report_edited", "report", report.id, flags=len(report.wording_flags))
    db.commit()
    return {"id": report.id, "flags": report.wording_flags}


@router.post("/reports/{report_id}/approve")
def approve_report(report_id: int, principal: Principal = Depends(reviewer), db: Session = Depends(get_db)) -> dict:
    report = db.get(Report, report_id)
    if report is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Report not found")
    blocking = [f for f in check_report(report.content) if f["rule"] in BLOCKING]
    if blocking:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, {"message": "Fix the wording before approving", "flags": blocking}
        )
    report.status = "released"
    report.reviewed_by = principal.actor_id
    report.reviewed_at = report.released_at = datetime.now(UTC)
    audit(db, principal, "report_approved", "report", report.id)
    db.commit()
    return {"id": report.id, "status": report.status}


@router.get("/scoring-configs")
def list_configs(_: Principal = Depends(reviewer), db: Session = Depends(get_db)) -> list[dict]:
    rows = db.scalars(select(ScoringConfig).order_by(ScoringConfig.created_at)).all()
    return [
        {
            "version": r.version,
            "active": r.active,
            "notes": r.notes,
            "created_by": r.created_by,
            "created_at": r.created_at,
            "config": r.config,
        }
        for r in rows
    ]


@router.get("/scoring-configs/default")
def default_config(_: Principal = Depends(reviewer)) -> dict:
    return DEFAULT_CONFIG


@router.post("/scoring-configs", status_code=201)
def create_config(
    body: ScoringConfigIn, principal: Principal = Depends(reviewer), db: Session = Depends(get_db)
) -> dict:
    if db.get(ScoringConfig, body.version):
        raise HTTPException(status.HTTP_409_CONFLICT, "Versions are immutable; choose a new version number")
    errors = validate(body.config)
    if errors:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, {"errors": errors})
    db.add(ScoringConfig(version=body.version, config=body.config, notes=body.notes, created_by=principal.actor_id))
    audit(db, principal, "scoring_config_created", "scoring_config", body.version)
    db.commit()
    return {"version": body.version, "active": False}


@router.post("/scoring-configs/{version}/activate")
def activate_config(version: str, principal: Principal = Depends(superadmin), db: Session = Depends(get_db)) -> dict:
    cfg = db.get(ScoringConfig, version)
    if cfg is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Unknown version")
    db.execute(update(ScoringConfig).values(active=False))
    cfg.active = True
    audit(db, principal, "scoring_config_activated", "scoring_config", version)
    db.commit()
    return {"version": version, "active": True}


@router.post("/cycles/{cycle_id}/rescore", status_code=202)
def rescore(cycle_id: int, principal: Principal = Depends(superadmin), db: Session = Depends(get_db)) -> dict:
    cycle = db.get(Cycle, cycle_id)
    if cycle is None or cycle.status not in ("completed", "scored"):
        raise HTTPException(status.HTTP_409_CONFLICT, "Cycle is not complete")
    audit(db, principal, "cycle_rescored", "cycle", cycle_id)
    db.commit()
    dispatch("score_and_report", cycle_id)
    return {"queued": True}


@router.get("/audit")
def audit_log(
    limit: int = Query(default=100, le=1000), _: Principal = Depends(superadmin), db: Session = Depends(get_db)
) -> list[dict]:
    rows = db.scalars(select(AuditLog).order_by(AuditLog.id.desc()).limit(limit)).all()
    return [
        {
            "at": r.at,
            "actor_role": r.actor_role,
            "actor_id": r.actor_id,
            "action": r.action,
            "target_type": r.target_type,
            "target_id": r.target_id,
            "detail": r.detail,
        }
        for r in rows
    ]
