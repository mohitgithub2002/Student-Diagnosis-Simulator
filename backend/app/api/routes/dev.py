"""Development-only helpers. Not mounted when SDS_ENVIRONMENT=prod."""

from fastapi import APIRouter

from app.services.messaging import dev_outbox

router = APIRouter(prefix="/dev", tags=["dev"])


@router.get("/outbox")
def outbox(limit: int = 50) -> list[dict]:
    """Messages the console SMS provider would have sent (OTPs, consent links)."""
    return [{"to": m.to, "kind": m.kind, "body": m.body, "at": m.at} for m in reversed(dev_outbox()[-limit:])]
