from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Cycle, Report
from app.reports.generator import personalize, render_language_variant
from app.reports.render import render_html, render_pdf
from app.reports.wording_check import check_report


def latest_released(db: Session, student_id: str, audience: str) -> Report | None:
    return db.scalars(
        select(Report)
        .join(Cycle, Cycle.id == Report.cycle_id)
        .where(Cycle.student_id == student_id, Report.audience == audience, Report.status == "released")
        .order_by(Cycle.number.desc(), Report.released_at.desc(), Report.id.desc())
    ).first()


def localized_content(db: Session, report: Report, lang: str | None) -> dict:
    """Return the report in the requested language when it can be regenerated from the same scores
    without losing a reviewer's edits; otherwise the stored version."""
    if not lang or lang == report.language or lang not in ("en", "hi") or report.reviewed_by:
        return report.content
    content = render_language_variant(db, report, lang)
    return report.content if check_report(content) else content


def report_payload(db: Session, report: Report, name: str, lang: str | None, fmt: str = "json"):
    content = personalize(localized_content(db, report, lang), name)
    if fmt == "pdf":
        return render_pdf(content, name)
    if fmt == "html":
        return {"html": render_html(content, name)}
    return {
        "id": report.id,
        "status": report.status,
        "released_at": report.released_at,
        "scoring_version": report.scoring_version,
        "content": content,
    }
