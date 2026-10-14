"""Public consent flow opened from the SMS/WhatsApp link (FR-03)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.routes.auth import parent_token
from app.api.schemas import ConsentSubmit
from app.core.audit import audit
from app.core.config import get_settings
from app.core.db import get_db
from app.core.deps import Principal
from app.core.security import decrypt_field
from app.services import messaging
from app.services.auth import check_lockout, create_otp, record_failure, verify_otp
from app.services.consent import NOTICE, consent_state, current_consent, record_consent, resolve_consent_link
from app.services.scheduler import ensure_cycle

router = APIRouter(prefix="/consent", tags=["consent"])


@router.get("/{token}")
def consent_page(token: str, db: Session = Depends(get_db)) -> dict:
    guardian = resolve_consent_link(db, token)
    student = guardian.student
    consent = current_consent(db, student.id)
    phone = decrypt_field(guardian.phone_enc)
    return {
        "student_first_name": student.display_name.split(" ")[0],
        "school": student.school_class.school.name,
        "language": guardian.language,
        "phone_hint": f"••••••{phone[-4:]}",
        "notice_version": get_settings().notice_version,
        "notice": NOTICE,
        "current": {
            "state": consent_state(consent),
            "voice": bool(consent and consent.voice),
            "share_with_school": bool(consent and consent.share_with_school),
        },
    }


@router.post("/{token}/otp", status_code=202)
def consent_otp(token: str, db: Session = Depends(get_db)) -> dict:
    guardian = resolve_consent_link(db, token)
    check_lockout(db, f"otp:{guardian.phone_hash}")
    code = create_otp(db, guardian.phone_hash, "consent")
    db.commit()
    messaging.send(decrypt_field(guardian.phone_enc), messaging.render("otp", guardian.language, code=code), "otp")
    return {"sent": True}


@router.post("/{token}")
def submit_consent(token: str, body: ConsentSubmit, db: Session = Depends(get_db)) -> dict:
    guardian = resolve_consent_link(db, token)
    key = f"otp:{guardian.phone_hash}"
    check_lockout(db, key)
    if not verify_otp(db, guardian.phone_hash, body.code, "consent"):
        record_failure(db, key)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "The code is incorrect or has expired")
    student = guardian.student
    consent = record_consent(
        db,
        student,
        guardian,
        participate=body.participate,
        voice=body.voice,
        share_with_school=body.share_with_school,
        language=body.language,
    )
    db.flush()
    if body.participate:
        ensure_cycle(db, student)
    audit(
        db,
        Principal(role="parent", subject=guardian.phone_hash),
        "consent_given",
        "student",
        student.id,
        participate=body.participate,
        voice=consent.voice,
        share=consent.share_with_school,
        notice_version=consent.notice_version,
    )
    db.commit()
    return {"state": consent_state(consent), "token": parent_token(guardian.phone_hash).token}
