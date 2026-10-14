from typing import Any

from sqlalchemy.orm import Session

from app.core.deps import Principal
from app.models import AuditLog


def audit(
    db: Session,
    principal: Principal | None,
    action: str,
    target_type: str = "",
    target_id: str | int = "",
    **detail: Any,
) -> None:
    """Record access to identity data, reports and configuration. Caller commits."""
    db.add(
        AuditLog(
            actor_role=principal.role if principal else "system",
            actor_id=principal.subject if principal else "system",
            action=action,
            target_type=target_type,
            target_id=str(target_id),
            detail=detail,
        )
    )
