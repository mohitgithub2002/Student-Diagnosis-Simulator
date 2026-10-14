"""Demo dataset: a school with two classes, consented students, completed cycles and released reports.

    uv run python -m app.cli demo

Everything goes through the real HTTP API in-process, so the demo exercises the same code paths as the
apps. Students and phone numbers are fictional.
"""

import os
import re
from datetime import date
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.db import get_sessionmaker
from app.core.security import hash_password
from app.models import StaffUser
from app.sim.api_player import play_cycle_via_api
from app.sim.simulator import PERSONAS

DEMO_ADMIN = ("admin@sunrise-demo.in", "demo-admin-123")
DEMO_TEACHER = ("teacher@sunrise-demo.in", "demo-teacher-123")
DEMO_REVIEWER = ("reviewer@revenuelogy-demo.in", "demo-reviewer-123")
DEMO_SUPERADMIN = ("superadmin@revenuelogy-demo.in", "demo-super-123")

ROSTER = [
    # name, parent phone, parent language, persona, completes cycle, consent choices (voice, share)
    ("Riya Sharma", "9810000001", "hi", "pressure_sensitive", True, (True, True)),
    ("Kabir Khan", "9810000002", "en", "strong_memory", True, (True, False)),
    ("Ananya Iyer", "9810000003", "en", "underconfident", True, (False, True)),
    ("Arjun Verma", "9810000004", "hi", "language_gap", True, (True, False)),
    ("Meera Nair", "9810000005", "en", "careless", False, (True, False)),
    ("Dev Patel", "9810000006", "en", "balanced", False, None),  # parent has not responded yet
]


def _otp(client: TestClient, phone: str) -> str:
    outbox = client.get("/api/dev/outbox?limit=500").json()
    body = next(m["body"] for m in outbox if m["kind"] == "otp" and m["to"].endswith(phone))
    return re.search(r"\b(\d{6})\b", body).group(1)


def _consent_token(client: TestClient, phone: str) -> str:
    outbox = client.get("/api/dev/outbox?limit=500").json()
    body = next(m["body"] for m in outbox if m["kind"] == "consent_link" and m["to"].endswith(phone))
    return re.search(r"/consent/([\w-]+)", body).group(1)


def _staff(email: str, password: str, role: str) -> None:
    with get_sessionmaker()() as db:
        if not db.scalars(select(StaffUser).where(StaffUser.email == email)).first():
            db.add(
                StaffUser(
                    email=email, name=role.replace("_", " ").title(), password_hash=hash_password(password), role=role
                )
            )
            db.commit()


def build_demo(students: int = 6) -> dict[str, Any]:
    os.environ["SDS_RELAX_SCHEDULE"] = "1"  # play all 7 sessions now instead of over 14 days
    from app.main import app

    with TestClient(app) as client:
        login = client.post("/api/auth/staff/login", json={"email": DEMO_ADMIN[0], "password": DEMO_ADMIN[1]})
        if login.status_code == 200:
            return {"message": "Demo data already exists", **credentials(client, login.json()["token"])}
        admin = client.post(
            "/api/auth/school-signup",
            json={
                "school_name": "Sunrise Public School (demo)",
                "city": "Jaipur",
                "admin_name": "Asha Admin",
                "admin_email": DEMO_ADMIN[0],
                "admin_password": DEMO_ADMIN[1],
            },
        ).json()["token"]
        headers = {"Authorization": f"Bearer {admin}"}
        client.post(
            "/api/school/teachers",
            json={"name": "Mr. Joseph", "email": DEMO_TEACHER[0], "password": DEMO_TEACHER[1]},
            headers=headers,
        )
        _staff(*DEMO_REVIEWER, "reviewer")
        _staff(*DEMO_SUPERADMIN, "superadmin")

        klass = client.post(
            "/api/school/classes", json={"grade": "7", "section": "A", "age_band": "11-14"}, headers=headers
        ).json()
        client.post("/api/school/classes", json={"grade": "10", "section": "B", "age_band": "15-18"}, headers=headers)
        roster = ROSTER[:students]
        csv = "name,parent_phone,parent_language\n" + "\n".join(f"{n},{p},{lang}" for n, p, lang, *_ in roster)
        created = client.post(
            f"/api/school/classes/{klass['id']}/students/upload",
            headers=headers,
            files={"file": ("roster.csv", csv.encode(), "text/csv")},
        ).json()["created"]
        pins = {c["name"]: c["pin"] for c in created}

        for _name, phone, lang, _persona, _completes, choices in roster:
            if choices is None:
                continue
            token = _consent_token(client, phone)
            client.post(f"/api/consent/{token}/otp")
            client.post(
                f"/api/consent/{token}",
                json={
                    "code": _otp(client, phone),
                    "participate": True,
                    "voice": choices[0],
                    "share_with_school": choices[1],
                    "language": lang,
                },
            ).raise_for_status()
        client.post(
            f"/api/school/classes/{klass['id']}/schedule",
            json={"start_date": date.today().isoformat(), "mode": "lab"},
            headers=headers,
        ).raise_for_status()

        for name, _phone, _lang, persona, completes, choices in roster:
            if choices is None:
                continue
            student = client.post(
                "/api/auth/student/login", json={"class_code": klass["class_code"], "pin": pins[name]}
            ).json()["token"]
            if completes:
                play_cycle_via_api(client, student, PERSONAS[persona], "11-14")
        return {"message": "Demo data created", **credentials(client, admin, klass["class_code"], pins)}


def credentials(
    client: TestClient, admin_token: str, class_code: str | None = None, pins: dict[str, str] | None = None
) -> dict[str, Any]:
    out: dict[str, Any] = {
        "school_admin": DEMO_ADMIN,
        "teacher": DEMO_TEACHER,
        "reviewer": DEMO_REVIEWER,
        "superadmin": DEMO_SUPERADMIN,
        "parents": {name: phone for name, phone, *_ in ROSTER},
        "note": "Parent and consent OTPs appear at GET /api/dev/outbox (console SMS provider).",
    }
    if class_code:
        out["class_code"] = class_code
    if pins:
        out["student_pins"] = pins
    return out
