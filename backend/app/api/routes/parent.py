"""Parent portal: children, consent changes, withdrawal (FR-04) and reports (FR-18, FR-20)."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.routes.reports_common import latest_released, report_payload
from app.api.schemas import ConsentChoices
from app.core.audit import audit
from app.core.db import get_db
from app.core.deps import Principal, require_roles
from app.models import Guardian
from app.services.consent import consent_state, current_consent, record_consent
from app.services.scheduler import active_cycle, ensure_cycle
from app.services.withdrawal import request_withdrawal
from app.workers.jobs import dispatch

router = APIRouter(prefix="/parent", tags=["parent"])
parent = require_roles("parent")


def _guardian_for(db: Session, principal: Principal, student_id: str) -> Guardian:
    g = db.scalars(
        select(Guardian).where(Guardian.phone_hash == principal.subject, Guardian.student_id == student_id)
    ).first()
    if g is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Child not found")
    return g


@router.get("/children")
def children(principal: Principal = Depends(parent), db: Session = Depends(get_db)) -> list[dict]:
    out = []
    for g in db.scalars(select(Guardian).where(Guardian.phone_hash == principal.subject)).all():
        s = g.student
        consent = current_consent(db, s.id)
        cycle = active_cycle(db, s.id)
        report = latest_released(db, s.id, "parent")
        out.append(
            {
                "student_id": s.id,
                "name": s.display_name,
                "school": s.school_class.school.name,
                "class": f"{s.school_class.grade}{s.school_class.section}",
                "language": g.language,
                "consent": {
                    "state": consent_state(consent),
                    "voice": bool(consent and consent.voice),
                    "share_with_school": bool(consent and consent.share_with_school),
                    "notice_version": consent.notice_version if consent else None,
                    "given_at": consent.given_at if consent else None,
                },
                "progress": {
                    "sessions_completed": sum(1 for x in cycle.sessions if x.status == "completed") if cycle else 0,
                    "sessions_total": 7,
                    "cycle": cycle.number if cycle else None,
                    "next_session": next((x.scheduled_for for x in cycle.sessions if x.status != "completed"), None)
                    if cycle
                    else None,
                },
                "report_ready": report is not None,
            }
        )
    return out


@router.post("/children/{student_id}/consent")
def change_consent(
    student_id: str, body: ConsentChoices, principal: Principal = Depends(parent), db: Session = Depends(get_db)
) -> dict:
    g = _guardian_for(db, principal, student_id)
    consent = record_consent(
        db,
        g.student,
        g,
        participate=body.participate,
        voice=body.voice,
        share_with_school=body.share_with_school,
        language=body.language,
    )
    db.flush()
    if body.participate:
        ensure_cycle(db, g.student)
    audit(
        db,
        principal,
        "consent_changed",
        "student",
        student_id,
        participate=body.participate,
        voice=consent.voice,
        share=consent.share_with_school,
    )
    db.commit()
    return {"state": consent_state(consent)}


@router.post("/children/{student_id}/withdraw", status_code=202)
def withdraw(student_id: str, principal: Principal = Depends(parent), db: Session = Depends(get_db)) -> dict:
    g = _guardian_for(db, principal, student_id)
    record = request_withdrawal(db, g.student, g)
    audit(db, principal, "consent_withdrawn", "deletion", record.id)
    db.commit()
    dispatch("delete_student", record.id)
    return {"withdrawn": True, "deletion_due_by": record.due_by}


@router.get("/children/{student_id}/report")
def parent_report(
    student_id: str,
    lang: str | None = Query(default=None),
    fmt: str = Query(default="json"),
    principal: Principal = Depends(parent),
    db: Session = Depends(get_db),
):
    g = _guardian_for(db, principal, student_id)
    rep = latest_released(db, student_id, "parent")
    if rep is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "The report is not ready yet")
    audit(db, principal, "report_viewed", "report", rep.id, fmt=fmt)
    db.commit()
    payload = report_payload(db, rep, g.student.display_name, lang or g.language, fmt)
    if isinstance(payload, bytes):
        return Response(
            payload,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="profile-report-{rep.id}.pdf"'},
        )
    return payload
