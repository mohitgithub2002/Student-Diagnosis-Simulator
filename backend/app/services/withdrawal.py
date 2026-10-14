"""Withdrawal (FR-04): delete all of a student's data and confirm to the parent."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.orm import Session as DbSession

from app.core.config import get_settings
from app.core.security import decrypt_field, keyed_hash
from app.models import (
    Consent,
    Cycle,
    DeletionRecord,
    EventReceipt,
    Guardian,
    ItemEvent,
    Session,
    Student,
    StudentVisit,
)
from app.services import messaging


def request_withdrawal(db: DbSession, student: Student, guardian: Guardian) -> DeletionRecord:
    now = datetime.now(UTC)
    db.add(
        Consent(
            student_id=student.id,
            guardian_id=guardian.id,
            participate=False,
            voice=False,
            camera=False,
            share_with_school=False,
            notice_version=get_settings().notice_version,
            notice_language=guardian.language,
            given_at=now,
            withdrawn_at=now,
        )
    )
    record = DeletionRecord(
        subject_ref=keyed_hash(student.id, scope="deletion"),
        pending_student_id=student.id,
        requested_at=now,
        due_by=now + timedelta(days=get_settings().withdrawal_deadline_days),
    )
    db.add(record)
    db.flush()
    return record


def delete_student_data(db: DbSession, record_id: int) -> bool:
    record = db.get(DeletionRecord, record_id)
    if record is None or record.completed_at is not None or record.pending_student_id is None:
        return False
    student = db.get(Student, record.pending_student_id)
    if student is not None:
        # Confirm first, while we still hold the contact details.
        for guardian in student.guardians:
            messaging.send(
                decrypt_field(guardian.phone_enc),
                messaging.render("withdrawal_confirmed", guardian.language, name=student.display_name),
                kind="withdrawal_confirmed",
            )
        record.confirmation_sent = True

    student_id = record.pending_student_id
    session_ids = select(Session.id).join(Cycle).where(Cycle.student_id == student_id)
    db.execute(delete(ItemEvent).where(ItemEvent.session_id.in_(session_ids)))
    db.execute(delete(EventReceipt).where(EventReceipt.session_id.in_(session_ids)))
    for cycle in db.scalars(select(Cycle).where(Cycle.student_id == student_id)).all():
        db.delete(cycle)  # cascades sessions, features, skill scores, error tags, reports
    db.execute(delete(StudentVisit).where(StudentVisit.student_id == student_id))
    db.execute(delete(Consent).where(Consent.student_id == student_id))
    if student is not None:
        db.delete(student)  # cascades guardians and their consent links
    record.pending_student_id = None
    record.completed_at = datetime.now(UTC)
    db.commit()
    return True


def sweep(db: DbSession) -> int:
    """Daily safety net: finish any deletion that has not run yet."""
    pending = db.scalars(select(DeletionRecord.id).where(DeletionRecord.completed_at.is_(None))).all()
    return sum(1 for record_id in pending if delete_student_data(db, record_id))
