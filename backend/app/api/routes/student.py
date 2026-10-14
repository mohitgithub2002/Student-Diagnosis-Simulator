"""Student app endpoints: session list, bundle download, event and feature sync, completion, own report."""

import math
from datetime import UTC, datetime
from functools import lru_cache

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session as DbSession

from app.api.routes.reports_common import latest_released, report_payload
from app.api.schemas import EventBatch, FeatureBatch, ResumeState, StartSession, WarmupIn
from app.core.db import get_db
from app.core.deps import Principal, require_roles
from app.models import Cycle, EventReceipt, Feature, Item, ItemEvent, Session, Student
from app.scoring.checks import check
from app.services.bundle import build_bundle
from app.services.consent import require_participation
from app.services.scheduler import ensure_cycle, session_status
from app.workers.jobs import dispatch

router = APIRouter(prefix="/student", tags=["student"])
student_only = require_roles("student")

CLIENT_FEATURE_PREFIXES = ("t7.", "t11.", "t22.", "warmup.")
VOICE_CHANNELS = ("voice", "voice_vad")


def _student(db: DbSession, principal: Principal) -> Student:
    s = db.get(Student, principal.subject)
    if s is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Student not found")
    return s


def _cycle(db: DbSession, student: Student) -> Cycle:
    cycle = ensure_cycle(db, student)
    if cycle is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "not_scheduled")
    return cycle


def _session(cycle: Cycle, number: int) -> Session:
    s = next((x for x in cycle.sessions if x.number == number), None)
    if s is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Session not found")
    return s


@router.get("/home")
def home(principal: Principal = Depends(student_only), db: DbSession = Depends(get_db)) -> dict:
    student = _student(db, principal)
    consent = require_participation(db, student.id)
    cycle = ensure_cycle(db, student)
    db.commit()
    sessions = []
    if cycle:
        for s in cycle.sessions:
            sessions.append(
                {
                    "number": s.number,
                    "scheduled_for": s.scheduled_for,
                    "window_end": s.window_end,
                    "status": s.status,
                    "availability": session_status(s, cycle),
                }
            )
    return {
        "student": {
            "name": student.display_name,
            "language": student.language_pref,
            "age_band": student.school_class.age_band,
        },
        "voice_allowed": consent.voice,
        "cycle": {"number": cycle.number, "status": cycle.status} if cycle else None,
        "sessions": sessions,
        "report_ready": latest_released(db, student.id, "student") is not None,
    }


@router.post("/warmup")
def warmup(body: WarmupIn, principal: Principal = Depends(student_only), db: DbSession = Depends(get_db)) -> dict:
    student = _student(db, principal)
    require_participation(db, student.id)
    student.language_pref = body.language
    db.commit()
    return {"language": student.language_pref}


def _lookup(db: DbSession):
    @lru_cache(maxsize=256)
    def lookup(task_id: str, band: str, language: str) -> tuple:
        rows = db.scalars(
            select(Item).where(
                Item.task_id == task_id, Item.age_band == band, Item.language == language, Item.status == "active"
            )
        ).all()
        return tuple(
            {
                "id": r.id,
                "task_id": r.task_id,
                "level": r.level,
                "language": r.language,
                "content": r.content,
                "answer_key": r.answer_key,
                "tags": r.tags,
                "variant_group": r.variant_group,
                "age_band": r.age_band,
            }
            for r in rows
        )

    return lambda t, b, lang: list(lookup(t, b, lang))


def _t2_context(db: DbSession, cycle: Cycle) -> dict:
    s4 = next((s for s in cycle.sessions if s.number == 4), None)
    if s4 is None:
        return {}
    ev = db.scalars(
        select(ItemEvent).where(
            ItemEvent.session_id == s4.id, ItemEvent.task_id == "T2", ItemEvent.item_id.like("T2-%")
        )
    ).first()
    if ev is None:
        return {}
    item = db.get(Item, ev.item_id)
    return {"t2_item": ev.item_id, "t2_group": item.variant_group if item else None}


@router.post("/sessions/{number}/start")
def start_session(
    number: int, body: StartSession, principal: Principal = Depends(student_only), db: DbSession = Depends(get_db)
) -> dict:
    student = _student(db, principal)
    consent = require_participation(db, student.id)
    cycle = _cycle(db, student)
    session = _session(cycle, number)
    availability = session_status(session, cycle)
    if availability["state"] not in ("available", "in_progress"):
        raise HTTPException(status.HTTP_409_CONFLICT, availability["state"])
    if body.language:
        student.language_pref = body.language
    if session.started_at is None:
        session.started_at = datetime.now(UTC)
    session.status = "in_progress"
    session.device_type = body.device_type
    session.language = student.language_pref
    bundle = build_bundle(
        number, cycle.age_band, student.language_pref, session.seed, _lookup(db), _t2_context(db, cycle)
    )
    db.commit()
    return {
        "session_id": session.id,
        "number": number,
        "voice_allowed": consent.voice,
        "resume_state": session.resume_state or {},
        "bundle": bundle,
    }


def _shown_at(ms: float | None) -> datetime:
    if ms and ms > 1e12:  # plausible epoch milliseconds
        try:
            return datetime.fromtimestamp(ms / 1000, tz=UTC)
        except (OverflowError, OSError, ValueError):
            pass
    return datetime.now(UTC)


@router.post("/sessions/{number}/events")
def ingest_events(
    number: int, body: EventBatch, principal: Principal = Depends(student_only), db: DbSession = Depends(get_db)
) -> dict:
    student = _student(db, principal)
    require_participation(db, student.id)
    cycle = _cycle(db, student)
    session = _session(cycle, number)
    if session.status not in ("in_progress", "completed"):
        raise HTTPException(status.HTTP_409_CONFLICT, "session_not_started")
    items = {i.id: i for i in db.scalars(select(Item).where(Item.id.in_({e.item_id for e in body.events}))).all()}
    accepted = duplicates = rejected = 0
    for e in body.events:
        item = items.get(e.item_id)
        if item is None:
            rejected += 1
            continue
        inserted = db.execute(
            insert(EventReceipt)
            .values(client_event_id=e.client_event_id, session_id=session.id)
            .on_conflict_do_nothing(index_elements=["client_event_id"])
            .returning(EventReceipt.client_event_id)
        ).first()
        if inserted is None:
            duplicates += 1
            continue
        correct = check(item.content, item.answer_key, e.answer, e.extra, e.skipped)
        db.add(
            ItemEvent(
                client_event_id=e.client_event_id,
                session_id=session.id,
                item_id=item.id,
                task_id=e.task_id,
                seq=e.seq,
                shown_at=_shown_at(e.shown_at_ms),
                response_ms=e.response_ms,
                first_click_ms=e.first_click_ms,
                answer=e.answer,
                correct=correct,
                changes=e.changes,
                change_log=e.change_log,
                skipped=e.skipped,
                retries=e.retries,
                confidence=e.confidence,
                idle_ms=e.idle_ms,
                max_idle_ms=e.max_idle_ms,
                switches=e.switches,
                level=item.level,
                language=item.language if item.language != "xx" else (e.language or "xx"),
                condition=e.condition,
                extra=e.extra,
            )
        )
        accepted += 1
    db.commit()
    return {"accepted": accepted, "duplicates": duplicates, "rejected": rejected}


@router.post("/sessions/{number}/features")
def ingest_features(
    number: int, body: FeatureBatch, principal: Principal = Depends(student_only), db: DbSession = Depends(get_db)
) -> dict:
    student = _student(db, principal)
    consent = require_participation(db, student.id)
    cycle = _cycle(db, student)
    session = _session(cycle, number)
    if session.status not in ("in_progress", "completed"):
        raise HTTPException(status.HTTP_409_CONFLICT, "session_not_started")
    accepted = rejected = 0
    for f in body.features:
        if not f.name.startswith(CLIENT_FEATURE_PREFIXES) or not math.isfinite(f.value):
            rejected += 1
            continue
        if f.channel in VOICE_CHANNELS and not consent.voice:
            rejected += 1  # voice features are only kept with the parent's voice consent
            continue
        db.add(
            Feature(
                session_id=session.id,
                name=f.name,
                value=f.value,
                source_channel=f.channel,
                task_id=f.task_id,
                item_id=f.item_id,
                derived=False,
            )
        )
        accepted += 1
    db.commit()
    return {"accepted": accepted, "rejected": rejected}


@router.put("/sessions/{number}/state")
def save_state(
    number: int, body: ResumeState, principal: Principal = Depends(student_only), db: DbSession = Depends(get_db)
) -> dict:
    student = _student(db, principal)
    require_participation(db, student.id)
    session = _session(_cycle(db, student), number)
    session.resume_state = body.state
    db.commit()
    return {"saved": True}


@router.post("/sessions/{number}/complete")
def complete_session(
    number: int, principal: Principal = Depends(student_only), db: DbSession = Depends(get_db)
) -> dict:
    student = _student(db, principal)
    require_participation(db, student.id)
    cycle = _cycle(db, student)
    session = _session(cycle, number)
    if session.status != "in_progress":
        raise HTTPException(status.HTTP_409_CONFLICT, "session_not_in_progress")
    session.status = "completed"
    session.completed_at = datetime.now(UTC)
    session.resume_state = {}
    finished = number == 7
    if finished:
        cycle.status = "completed"
        cycle.completed_at = datetime.now(UTC)
    db.commit()
    if finished:
        dispatch("score_and_report", cycle.id)
    return {"completed": True, "cycle_completed": finished}


@router.get("/report")
def student_report(principal: Principal = Depends(student_only), db: DbSession = Depends(get_db)):
    student = _student(db, principal)
    require_participation(db, student.id)
    rep = latest_released(db, student.id, "student")
    if rep is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Your report is not ready yet")
    return report_payload(db, rep, student.display_name, None)
