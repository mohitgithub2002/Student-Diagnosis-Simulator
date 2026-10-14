from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.schemas import OtpRequest, OtpVerify, SchoolSignup, StaffLogin, StudentLogin, TokenOut
from app.core.audit import audit
from app.core.config import get_settings
from app.core.db import get_db
from app.core.deps import Principal, get_principal
from app.core.security import (
    create_token,
    decrypt_field,
    hash_password,
    normalize_phone,
    phone_hash,
    pin_hash,
    verify_password,
)
from app.models import Guardian, School, SchoolClass, StaffUser, Student, StudentVisit
from app.services import messaging
from app.services.auth import check_lockout, clear_failures, create_otp, record_failure, verify_otp
from app.services.consent import require_participation

router = APIRouter(prefix="/auth", tags=["auth"])


def staff_token(user: StaffUser) -> TokenOut:
    token = create_token(
        {"sub": str(user.id), "role": user.role, "school_id": user.school_id, "name": user.name},
        get_settings().staff_token_ttl_minutes,
    )
    return TokenOut(token=token, role=user.role, name=user.name, school_id=user.school_id)


@router.post("/staff/login", response_model=TokenOut)
def staff_login(body: StaffLogin, db: Session = Depends(get_db)) -> TokenOut:
    key = f"staff:{body.email.lower()}"
    check_lockout(db, key)
    user = db.scalars(select(StaffUser).where(StaffUser.email == body.email.lower())).first()
    if user is None or not user.active or not verify_password(body.password, user.password_hash):
        record_failure(db, key)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Email or password is incorrect")
    clear_failures(db, key)
    audit(db, Principal(role=user.role, subject=str(user.id)), "staff_login")
    db.commit()
    return staff_token(user)


@router.post("/school-signup", response_model=TokenOut, status_code=201)
def school_signup(body: SchoolSignup, db: Session = Depends(get_db)) -> TokenOut:
    if db.scalars(select(StaffUser).where(StaffUser.email == body.admin_email.lower())).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "An account with this email already exists")
    school = School(
        name=body.school_name, city=body.city, contract_start=body.contract_start, contract_end=body.contract_end
    )
    db.add(school)
    db.flush()
    user = StaffUser(
        email=body.admin_email.lower(),
        name=body.admin_name,
        password_hash=hash_password(body.admin_password),
        role="school_admin",
        school_id=school.id,
    )
    db.add(user)
    db.flush()
    audit(db, Principal(role="school_admin", subject=str(user.id)), "school_signup", "school", school.id)
    db.commit()
    return staff_token(user)


@router.post("/student/login")
def student_login(body: StudentLogin, db: Session = Depends(get_db)) -> dict:
    code = body.class_code.strip().upper()
    key = f"class:{code}"
    check_lockout(db, key)
    school_class = db.scalars(select(SchoolClass).where(SchoolClass.class_code == code)).first()
    student = None
    if school_class:
        student = db.scalars(
            select(Student).where(
                Student.class_id == school_class.id, Student.pin_hash == pin_hash(school_class.id, body.pin)
            )
        ).first()
    if student is None:
        record_failure(db, key)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Class code or PIN is incorrect")
    clear_failures(db, key)
    require_participation(db, student.id)  # no data is collected without parental consent
    db.add(StudentVisit(student_id=student.id))
    db.commit()
    token = create_token(
        {"sub": student.id, "role": "student", "school_id": school_class.school_id, "name": student.display_name},
        get_settings().student_token_ttl_minutes,
    )
    return {
        "token": token,
        "role": "student",
        "student": {
            "id": student.id,
            "name": student.display_name,
            "language": student.language_pref,
            "age_band": school_class.age_band,
        },
    }


@router.post("/parent/otp", status_code=202)
def parent_otp(body: OtpRequest, db: Session = Depends(get_db)) -> dict:
    ph = phone_hash(body.phone)
    check_lockout(db, f"otp:{ph}")
    guardian = db.scalars(select(Guardian).where(Guardian.phone_hash == ph)).first()
    if guardian is not None:  # same response either way, so phone numbers cannot be probed
        code = create_otp(db, ph, "parent_login")
        db.commit()
        messaging.send(decrypt_field(guardian.phone_enc), messaging.render("otp", guardian.language, code=code), "otp")
    return {"sent": True}


@router.post("/parent/verify", response_model=TokenOut)
def parent_verify(body: OtpVerify, db: Session = Depends(get_db)) -> TokenOut:
    ph = phone_hash(body.phone)
    key = f"otp:{ph}"
    check_lockout(db, key)
    if not verify_otp(db, ph, body.code, "parent_login"):
        record_failure(db, key)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "The code is incorrect or has expired")
    clear_failures(db, key)
    db.commit()
    return parent_token(ph)


def parent_token(ph: str) -> TokenOut:
    token = create_token({"sub": ph, "role": "parent"}, get_settings().parent_token_ttl_minutes)
    return TokenOut(token=token, role="parent")


@router.get("/me")
def me(principal: Principal = Depends(get_principal)) -> dict:
    return {"role": principal.role, "name": principal.name, "school_id": principal.school_id}


__all__ = ["router", "parent_token", "normalize_phone"]
