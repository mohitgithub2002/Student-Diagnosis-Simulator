"""Login lockout and OTP challenges."""

from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import generate_otp, keyed_hash
from app.models import AuthFailure, OtpChallenge


def _now() -> datetime:
    return datetime.now(UTC)


def check_lockout(db: Session, key: str) -> None:
    row = db.get(AuthFailure, key)
    if row and row.locked_until and row.locked_until > _now():
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Too many attempts. Please wait and try again.")


def record_failure(db: Session, key: str) -> None:
    settings = get_settings()
    row = db.get(AuthFailure, key) or AuthFailure(key=key, count=0)
    row.count += 1
    row.updated_at = _now()
    if row.count >= settings.login_max_failures:
        row.locked_until = _now() + timedelta(minutes=settings.login_lockout_minutes)
        row.count = 0
    db.add(row)
    db.commit()


def clear_failures(db: Session, key: str) -> None:
    row = db.get(AuthFailure, key)
    if row:
        db.delete(row)


def create_otp(db: Session, phone_hash: str, purpose: str) -> str:
    settings = get_settings()
    code = generate_otp()
    db.add(
        OtpChallenge(
            phone_hash=phone_hash,
            code_hash=keyed_hash(code, scope=f"otp:{phone_hash}"),
            purpose=purpose,
            expires_at=_now() + timedelta(seconds=settings.otp_ttl_seconds),
        )
    )
    return code


def verify_otp(db: Session, phone_hash: str, code: str, purpose: str) -> bool:
    settings = get_settings()
    challenge = db.scalars(
        select(OtpChallenge)
        .where(
            OtpChallenge.phone_hash == phone_hash,
            OtpChallenge.purpose == purpose,
            OtpChallenge.consumed_at.is_(None),
        )
        .order_by(OtpChallenge.id.desc())
    ).first()
    if challenge is None or challenge.expires_at < _now() or challenge.attempts >= settings.otp_max_attempts:
        return False
    challenge.attempts += 1
    if challenge.code_hash != keyed_hash(code.strip(), scope=f"otp:{phone_hash}"):
        db.commit()
        return False
    challenge.consumed_at = _now()
    db.commit()
    return True
