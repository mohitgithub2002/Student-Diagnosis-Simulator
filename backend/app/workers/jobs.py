"""Background jobs. Run through Celery in production, inline when SDS_CELERY_EAGER is set."""

import logging

from app.core.config import get_settings
from app.core.db import get_sessionmaker

log = logging.getLogger("sds.jobs")


def score_and_report(cycle_id: int) -> None:
    from app.reports.generator import generate_reports
    from app.scoring.runner import score_cycle

    with get_sessionmaker()() as db:
        score_cycle(db, cycle_id)
        generate_reports(db, cycle_id)


def delete_student(record_id: int) -> None:
    from app.services.withdrawal import delete_student_data

    with get_sessionmaker()() as db:
        delete_student_data(db, record_id)


def sweep_withdrawals() -> int:
    from app.services.withdrawal import sweep

    with get_sessionmaker()() as db:
        return sweep(db)


JOBS = {
    "score_and_report": score_and_report,
    "delete_student": delete_student,
    "sweep_withdrawals": sweep_withdrawals,
}


def dispatch(name: str, *args) -> None:
    if get_settings().celery_eager:
        JOBS[name](*args)
        return
    from app.workers.celery_app import celery_app

    celery_app.send_task(f"sds.{name}", args=list(args))
