"""Identity schema: restricted-access personal data and consent."""

import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy import JSON, Boolean, Date, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import IDENTITY, Base, utcnow

AGE_BANDS = ("11-14", "15-18")
STUDENT_LANGUAGES = ("en", "hi", "hinglish")
REPORT_LANGUAGES = ("en", "hi")
STAFF_ROLES = ("school_admin", "teacher", "reviewer", "superadmin")


class School(Base):
    __tablename__ = "schools"
    __table_args__ = {"schema": IDENTITY}

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    city: Mapped[str] = mapped_column(String(100), default="")
    contract_start: Mapped[date | None] = mapped_column(Date)
    contract_end: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    classes: Mapped[list["SchoolClass"]] = relationship(back_populates="school", order_by="SchoolClass.id")


class SchoolClass(Base):
    __tablename__ = "classes"
    __table_args__ = {"schema": IDENTITY}

    id: Mapped[int] = mapped_column(primary_key=True)
    school_id: Mapped[int] = mapped_column(ForeignKey(f"{IDENTITY}.schools.id", ondelete="CASCADE"), index=True)
    grade: Mapped[str] = mapped_column(String(20))
    section: Mapped[str] = mapped_column(String(20), default="")
    age_band: Mapped[str] = mapped_column(String(5))
    class_code: Mapped[str] = mapped_column(String(12), unique=True)
    # Cycle scheduling: start date of the current cycle and where sessions run (lab | home | both).
    cycle_start: Mapped[date | None] = mapped_column(Date)
    session_mode: Mapped[str] = mapped_column(String(10), default="lab")
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    school: Mapped[School] = relationship(back_populates="classes")
    students: Mapped[list["Student"]] = relationship(back_populates="school_class", order_by="Student.display_name")


class Student(Base):
    __tablename__ = "students"
    __table_args__ = (UniqueConstraint("class_id", "pin_hash", name="uq_student_class_pin"), {"schema": IDENTITY})

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    class_id: Mapped[int] = mapped_column(ForeignKey(f"{IDENTITY}.classes.id", ondelete="CASCADE"), index=True)
    display_name: Mapped[str] = mapped_column(String(120))
    pin_hash: Mapped[str] = mapped_column(String(64))
    language_pref: Mapped[str] = mapped_column(String(10), default="en")
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    school_class: Mapped[SchoolClass] = relationship(back_populates="students")
    guardians: Mapped[list["Guardian"]] = relationship(back_populates="student", cascade="all, delete-orphan")


class Guardian(Base):
    __tablename__ = "guardians"
    __table_args__ = {"schema": IDENTITY}

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[str] = mapped_column(ForeignKey(f"{IDENTITY}.students.id", ondelete="CASCADE"), index=True)
    phone_enc: Mapped[str] = mapped_column(String(300))
    phone_hash: Mapped[str] = mapped_column(String(64), index=True)
    language: Mapped[str] = mapped_column(String(5), default="en")
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    student: Mapped[Student] = relationship(back_populates="guardians")


class ConsentLink(Base):
    """Single-purpose token sent to a guardian by SMS so they can open the consent page."""

    __tablename__ = "consent_links"
    __table_args__ = {"schema": IDENTITY}

    id: Mapped[int] = mapped_column(primary_key=True)
    guardian_id: Mapped[int] = mapped_column(ForeignKey(f"{IDENTITY}.guardians.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    expires_at: Mapped[datetime]


class Consent(Base):
    """Append-only consent log: every change is a new row; the newest row is the current state."""

    __tablename__ = "consents"
    __table_args__ = {"schema": IDENTITY}

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[str] = mapped_column(ForeignKey(f"{IDENTITY}.students.id", ondelete="CASCADE"), index=True)
    guardian_id: Mapped[int] = mapped_column(ForeignKey(f"{IDENTITY}.guardians.id", ondelete="CASCADE"))
    participate: Mapped[bool] = mapped_column(Boolean)
    voice: Mapped[bool] = mapped_column(Boolean, default=False)
    camera: Mapped[bool] = mapped_column(Boolean, default=False)
    share_with_school: Mapped[bool] = mapped_column(Boolean, default=False)
    notice_version: Mapped[str] = mapped_column(String(40))
    notice_language: Mapped[str] = mapped_column(String(5), default="en")
    given_at: Mapped[datetime] = mapped_column(default=utcnow)
    withdrawn_at: Mapped[datetime | None]


class StaffUser(Base):
    __tablename__ = "staff_users"
    __table_args__ = {"schema": IDENTITY}

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(200), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    password_hash: Mapped[str] = mapped_column(String(100))
    role: Mapped[str] = mapped_column(String(20))
    school_id: Mapped[int | None] = mapped_column(ForeignKey(f"{IDENTITY}.schools.id", ondelete="CASCADE"))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)


class OtpChallenge(Base):
    __tablename__ = "otp_challenges"
    __table_args__ = {"schema": IDENTITY}

    id: Mapped[int] = mapped_column(primary_key=True)
    phone_hash: Mapped[str] = mapped_column(String(64), index=True)
    code_hash: Mapped[str] = mapped_column(String(64))
    purpose: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    expires_at: Mapped[datetime]
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    consumed_at: Mapped[datetime | None]


class AuthFailure(Base):
    """Failed-login counter per key (class code, phone hash, email) for lockout."""

    __tablename__ = "auth_failures"
    __table_args__ = {"schema": IDENTITY}

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    count: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[datetime | None]
    updated_at: Mapped[datetime] = mapped_column(default=utcnow)


class AuditLog(Base):
    __tablename__ = "audit_log"
    __table_args__ = {"schema": IDENTITY}

    id: Mapped[int] = mapped_column(primary_key=True)
    at: Mapped[datetime] = mapped_column(default=utcnow, index=True)
    actor_role: Mapped[str] = mapped_column(String(20))
    actor_id: Mapped[str] = mapped_column(String(80))
    action: Mapped[str] = mapped_column(String(60))
    target_type: Mapped[str] = mapped_column(String(40), default="")
    target_id: Mapped[str] = mapped_column(String(80), default="")
    detail: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class DeletionRecord(Base):
    """De-identified proof that a withdrawal was honoured. Holds no personal data."""

    __tablename__ = "deletion_records"
    __table_args__ = {"schema": IDENTITY}

    id: Mapped[int] = mapped_column(primary_key=True)
    subject_ref: Mapped[str] = mapped_column(String(64), index=True)
    # Needed only until the deletion job runs; cleared on completion.
    pending_student_id: Mapped[str | None] = mapped_column(String(36))
    reason: Mapped[str] = mapped_column(String(40), default="withdrawal")
    requested_at: Mapped[datetime] = mapped_column(default=utcnow)
    due_by: Mapped[datetime]
    completed_at: Mapped[datetime | None]
    confirmation_sent: Mapped[bool] = mapped_column(Boolean, default=False)
