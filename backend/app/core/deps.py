"""Request authentication and role-based access (FR-01).

Roles and what they can reach mirror the PRD personas table:
- student: own sessions and own student report
- parent: own children's consent, parent report and progress
- school_admin / teacher: enrolment, consent and completion for their school; individual reports only
  when the parent chose to share with the school
- reviewer: de-identified reports, item statistics, scoring configuration
- superadmin: everything a reviewer can do plus the audit log
"""

from dataclasses import dataclass, field

import jwt
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import decode_token

ROLES = ("student", "parent", "school_admin", "teacher", "reviewer", "superadmin")


@dataclass
class Principal:
    role: str
    subject: str  # student id, phone hash, or staff user id
    school_id: int | None = None
    name: str = ""
    claims: dict = field(default_factory=dict)

    @property
    def actor_id(self) -> str:
        return f"{self.role}:{self.subject}"


def get_principal(authorization: str | None = Header(default=None)) -> Principal:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not signed in")
    try:
        claims = decode_token(authorization.split(" ", 1)[1])
    except jwt.PyJWTError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Session expired, please sign in again") from exc
    role = claims.get("role")
    if role not in ROLES:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Unknown role")
    return Principal(
        role=role,
        subject=str(claims.get("sub")),
        school_id=claims.get("school_id"),
        name=claims.get("name", ""),
        claims=claims,
    )


def require_roles(*roles: str):
    def checker(principal: Principal = Depends(get_principal)) -> Principal:
        if principal.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "This account cannot access that")
        return principal

    return checker


DB = Depends(get_db)


def get_session_db(db: Session = DB) -> Session:
    return db
