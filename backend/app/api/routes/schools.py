"""School admin and teacher endpoints: onboarding, consent tracker, scheduling, completion dashboard
(FR-23) and individual reports only where the parent chose to share them."""

import csv
import io
from collections import Counter

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.routes.reports_common import latest_released, report_payload
from app.api.schemas import ClassIn, ScheduleIn, TeacherIn
from app.core.audit import audit
from app.core.db import get_db
from app.core.deps import Principal, require_roles
from app.core.security import (
    encrypt_field,
    generate_class_code,
    generate_pin,
    hash_password,
    normalize_phone,
    phone_hash,
    pin_hash,
)
from app.models import Guardian, School, SchoolClass, StaffUser, Student
from app.services.consent import consent_state, current_consent, issue_consent_link
from app.services.scheduler import active_cycle, ensure_cycle

router = APIRouter(prefix="/school", tags=["school"])
staff = require_roles("school_admin", "teacher")
admin_only = require_roles("school_admin")


def _school(db: Session, principal: Principal) -> School:
    school = db.get(School, principal.school_id) if principal.school_id else None
    if school is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "School not found")
    return school


def _class(db: Session, principal: Principal, class_id: int) -> SchoolClass:
    c = db.get(SchoolClass, class_id)
    if c is None or c.school_id != principal.school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Class not found")
    return c


def _student(db: Session, principal: Principal, student_id: str) -> Student:
    s = db.get(Student, student_id)
    if s is None or s.school_class.school_id != principal.school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Student not found")
    return s


@router.get("")
def school_info(principal: Principal = Depends(staff), db: Session = Depends(get_db)) -> dict:
    school = _school(db, principal)
    return {
        "id": school.id,
        "name": school.name,
        "city": school.city,
        "contract_start": school.contract_start,
        "contract_end": school.contract_end,
        "classes": [
            {
                "id": c.id,
                "grade": c.grade,
                "section": c.section,
                "age_band": c.age_band,
                "class_code": c.class_code,
                "cycle_start": c.cycle_start,
                "session_mode": c.session_mode,
                "students": len(c.students),
            }
            for c in school.classes
        ],
    }


@router.post("/classes", status_code=201)
def create_class(body: ClassIn, principal: Principal = Depends(admin_only), db: Session = Depends(get_db)) -> dict:
    school = _school(db, principal)
    for _ in range(5):
        code = generate_class_code()
        if not db.scalars(select(SchoolClass).where(SchoolClass.class_code == code)).first():
            break
    c = SchoolClass(
        school_id=school.id, grade=body.grade, section=body.section, age_band=body.age_band, class_code=code
    )
    db.add(c)
    db.flush()
    audit(db, principal, "class_created", "class", c.id)
    db.commit()
    return {"id": c.id, "class_code": c.class_code, "grade": c.grade, "section": c.section, "age_band": c.age_band}


def _unique_pin(db: Session, class_id: int, taken: set[str]) -> str:
    for _ in range(200):
        pin = generate_pin()
        h = pin_hash(class_id, pin)
        if (
            h not in taken
            and not db.scalars(select(Student).where(Student.class_id == class_id, Student.pin_hash == h)).first()
        ):
            taken.add(h)
            return pin
    raise HTTPException(status.HTTP_409_CONFLICT, "Could not allocate a unique PIN for this class")


@router.post("/classes/{class_id}/students/upload", status_code=201)
async def upload_students(
    class_id: int,
    file: UploadFile = File(...),
    principal: Principal = Depends(admin_only),
    db: Session = Depends(get_db),
) -> dict:
    """CSV columns: name, parent_phone, [parent_language en|hi], [student_language en|hi|hinglish].
    PINs are shown once here; only a keyed hash is stored."""
    c = _class(db, principal, class_id)
    raw = (await file.read()).decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(raw))
    if not reader.fieldnames or not {"name", "parent_phone"} <= {f.strip().lower() for f in reader.fieldnames}:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "CSV needs columns: name, parent_phone")
    created, errors, taken = [], [], set()
    for line, row in enumerate(reader, start=2):
        row = {k.strip().lower(): (v or "").strip() for k, v in row.items() if k}
        name, phone = row.get("name", ""), row.get("parent_phone", "")
        digits = "".join(ch for ch in phone if ch.isdigit())
        if not name or len(digits) < 10:
            errors.append({"line": line, "error": "name and a 10-digit parent phone are required"})
            continue
        pin = _unique_pin(db, c.id, taken)
        student = Student(
            class_id=c.id,
            display_name=name[:120],
            pin_hash=pin_hash(c.id, pin),
            language_pref=row.get("student_language")
            if row.get("student_language") in ("en", "hi", "hinglish")
            else "en",
        )
        guardian = Guardian(
            phone_enc=encrypt_field(normalize_phone(phone)),
            phone_hash=phone_hash(phone),
            language=row.get("parent_language") if row.get("parent_language") in ("en", "hi") else "en",
        )
        student.guardians.append(guardian)
        db.add(student)
        db.flush()
        issue_consent_link(db, guardian, c.school.name)
        created.append({"student_id": student.id, "name": student.display_name, "pin": pin})
    audit(db, principal, "students_uploaded", "class", c.id, count=len(created))
    db.commit()
    return {"class_code": c.class_code, "created": created, "errors": errors}


@router.post("/students/{student_id}/pin")
def reset_pin(student_id: str, principal: Principal = Depends(admin_only), db: Session = Depends(get_db)) -> dict:
    s = _student(db, principal, student_id)
    pin = _unique_pin(db, s.class_id, set())
    s.pin_hash = pin_hash(s.class_id, pin)
    audit(db, principal, "pin_reset", "student", s.id)
    db.commit()
    return {"student_id": s.id, "pin": pin}


@router.post("/students/{student_id}/consent-link", status_code=202)
def resend_consent(student_id: str, principal: Principal = Depends(admin_only), db: Session = Depends(get_db)) -> dict:
    s = _student(db, principal, student_id)
    for g in s.guardians:
        issue_consent_link(db, g, s.school_class.school.name)
    audit(db, principal, "consent_link_resent", "student", s.id)
    db.commit()
    return {"sent": len(s.guardians)}


@router.post("/teachers", status_code=201)
def create_teacher(body: TeacherIn, principal: Principal = Depends(admin_only), db: Session = Depends(get_db)) -> dict:
    user = StaffUser(
        email=body.email.lower(),
        name=body.name,
        password_hash=hash_password(body.password),
        role="teacher",
        school_id=principal.school_id,
    )
    db.add(user)
    try:
        db.flush()
    except IntegrityError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, "An account with this email already exists") from exc
    audit(db, principal, "teacher_created", "staff", user.id)
    db.commit()
    return {"id": user.id, "email": user.email, "name": user.name}


@router.post("/classes/{class_id}/schedule")
def schedule(
    class_id: int, body: ScheduleIn, principal: Principal = Depends(admin_only), db: Session = Depends(get_db)
) -> dict:
    c = _class(db, principal, class_id)
    c.cycle_start = body.start_date
    c.session_mode = body.mode
    created = 0
    for s in c.students:
        if consent_state(current_consent(db, s.id)) == "yes" and active_cycle(db, s.id) is None:
            ensure_cycle(db, s)
            created += 1
    audit(db, principal, "class_scheduled", "class", c.id, start=str(body.start_date))
    db.commit()
    return {"class_id": c.id, "cycle_start": c.cycle_start, "mode": c.session_mode, "cycles_created": created}


def _progress(db: Session, s: Student) -> dict:
    cycle = active_cycle(db, s.id)
    done = sum(1 for x in cycle.sessions if x.status == "completed") if cycle else 0
    return {
        "cycle": cycle.number if cycle else None,
        "sessions_completed": done,
        "cycle_status": cycle.status if cycle else None,
    }


@router.get("/classes/{class_id}/roster")
def roster(class_id: int, principal: Principal = Depends(staff), db: Session = Depends(get_db)) -> dict:
    """Consent tracker and completion per student. No scores or behavioural detail."""
    c = _class(db, principal, class_id)
    rows = []
    for s in c.students:
        consent = current_consent(db, s.id)
        rows.append(
            {
                "student_id": s.id,
                "name": s.display_name,
                "consent": consent_state(consent),
                "shared_with_school": bool(consent and consent.share_with_school and not consent.withdrawn_at),
                **_progress(db, s),
            }
        )
    audit(db, principal, "roster_viewed", "class", c.id)
    db.commit()
    return {
        "class": {
            "id": c.id,
            "grade": c.grade,
            "section": c.section,
            "class_code": c.class_code,
            "age_band": c.age_band,
            "cycle_start": c.cycle_start,
        },
        "students": rows,
    }


@router.get("/dashboard")
def dashboard(principal: Principal = Depends(staff), db: Session = Depends(get_db)) -> dict:
    school = _school(db, principal)
    classes = []
    for c in school.classes:
        consent_counts: Counter = Counter()
        completion: Counter = Counter()
        finished = reports = 0
        for s in c.students:
            consent_counts[consent_state(current_consent(db, s.id))] += 1
            p = _progress(db, s)
            completion[p["sessions_completed"]] += 1
            if p["sessions_completed"] >= 7:
                finished += 1
            if p["cycle_status"] == "scored":
                reports += 1
        enrolled = len(c.students)
        classes.append(
            {
                "id": c.id,
                "grade": c.grade,
                "section": c.section,
                "age_band": c.age_band,
                "enrolled": enrolled,
                "consent": {k: consent_counts.get(k, 0) for k in ("yes", "pending", "no", "withdrawn")},
                "sessions_completed_histogram": {str(k): completion.get(k, 0) for k in range(8)},
                "completed_all": finished,
                "completion_rate": round(finished / enrolled, 3) if enrolled else 0,
                "reports_ready": reports,
                "cycle_start": c.cycle_start,
            }
        )
    return {"school": school.name, "classes": classes}


@router.get("/reports")
def shared_reports(principal: Principal = Depends(staff), db: Session = Depends(get_db)) -> list[dict]:
    school = _school(db, principal)
    out = []
    for c in school.classes:
        for s in c.students:
            consent = current_consent(db, s.id)
            if not (consent and consent.share_with_school and consent.participate and not consent.withdrawn_at):
                continue
            rep = latest_released(db, s.id, "parent")
            if rep:
                out.append(
                    {
                        "student_id": s.id,
                        "name": s.display_name,
                        "class": f"{c.grade}{c.section}",
                        "released_at": rep.released_at,
                    }
                )
    return out


@router.get("/reports/{student_id}")
def shared_report(
    student_id: str,
    lang: str | None = Query(default=None),
    fmt: str = "json",
    principal: Principal = Depends(staff),
    db: Session = Depends(get_db),
):
    s = _student(db, principal, student_id)
    consent = current_consent(db, s.id)
    if not (consent and consent.share_with_school and consent.participate and not consent.withdrawn_at):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "The parent has not shared this report with the school")
    rep = latest_released(db, s.id, "parent")
    if rep is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No released report yet")
    audit(db, principal, "shared_report_viewed", "report", rep.id)
    db.commit()
    payload = report_payload(db, rep, s.display_name, lang, fmt)
    return payload if not isinstance(payload, bytes) else Response(payload, media_type="application/pdf")
