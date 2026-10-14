"""Session scheduler (FR-09): 7 sessions, one every second day over 14 days, each with a 3-day make-up
window. Sessions run in order."""

import random
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session as DbSession

from app.core.config import get_settings
from app.models import Cycle, SchoolClass, Session, Student


def today() -> date:
    return datetime.now(UTC).date()


def create_cycle(db: DbSession, student: Student, school_class: SchoolClass, start: date) -> Cycle:
    settings = get_settings()
    number = (db.scalar(select(func.max(Cycle.number)).where(Cycle.student_id == student.id)) or 0) + 1
    last_day = start + timedelta(days=settings.session_interval_days * (settings.sessions_per_cycle - 1))
    cycle = Cycle(
        student_id=student.id,
        number=number,
        age_band=school_class.age_band,
        start_date=start,
        end_date=last_day + timedelta(days=settings.makeup_window_days),
    )
    rng = random.Random(f"{student.id}:{number}")
    for n in range(1, settings.sessions_per_cycle + 1):
        scheduled = start + timedelta(days=settings.session_interval_days * (n - 1))
        cycle.sessions.append(
            Session(
                number=n,
                scheduled_for=scheduled,
                window_end=scheduled + timedelta(days=settings.makeup_window_days),
                seed=rng.randrange(1, 2**31),
            )
        )
    db.add(cycle)
    return cycle


def active_cycle(db: DbSession, student_id: str) -> Cycle | None:
    return db.scalars(select(Cycle).where(Cycle.student_id == student_id).order_by(Cycle.number.desc())).first()


def ensure_cycle(db: DbSession, student: Student) -> Cycle | None:
    """Create the student's cycle when their class has a schedule and they have none yet."""
    cycle = active_cycle(db, student.id)
    school_class = student.school_class
    if cycle is None and school_class.cycle_start is not None:
        cycle = create_cycle(db, student, school_class, school_class.cycle_start)
        db.flush()
    return cycle


def session_status(session: Session, cycle: Cycle, on: date | None = None) -> dict:
    """Availability of one session, given the others in its cycle."""
    on = on or today()
    relaxed = get_settings().is_dev and _relaxed()

    def missed(s: Session) -> bool:
        return not relaxed and _missed(s, on)

    if session.status == "completed":
        return {"state": "completed"}
    if missed(session):
        return {"state": "missed"}
    if any(s.number < session.number and s.status != "completed" and not missed(s) for s in cycle.sessions):
        return {"state": "locked", "reason": "finish_previous"}
    if on < session.scheduled_for and not relaxed:
        return {"state": "upcoming", "opens_on": session.scheduled_for.isoformat()}
    return {
        "state": "in_progress" if session.status == "in_progress" else "available",
        "makeup": on > session.scheduled_for,
        "closes_on": session.window_end.isoformat(),
    }


def _missed(session: Session, on: date) -> bool:
    return session.status != "completed" and on > session.window_end


def _relaxed() -> bool:
    import os

    return os.environ.get("SDS_RELAX_SCHEDULE", "") == "1"
