import io
import re
import uuid

from app.services.messaging import dev_outbox


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def signup_school(client, name="Test School") -> str:
    email = f"admin-{uuid.uuid4().hex[:8]}@sunrise-school.in"
    r = client.post(
        "/api/auth/school-signup",
        json={
            "school_name": name,
            "city": "Jaipur",
            "admin_name": "Asha Admin",
            "admin_email": email,
            "admin_password": "correct-horse-1",
        },
    )
    assert r.status_code == 201, r.text
    return r.json()["token"]


def make_class(client, token, age_band="11-14") -> dict:
    r = client.post(
        "/api/school/classes", json={"grade": "7", "section": "A", "age_band": age_band}, headers=auth(token)
    )
    assert r.status_code == 201, r.text
    return r.json()


def upload(client, token, class_id, rows: list[tuple[str, str, str]]) -> dict:
    csv = "name,parent_phone,parent_language\n" + "\n".join(",".join(r) for r in rows)
    r = client.post(
        f"/api/school/classes/{class_id}/students/upload",
        headers=auth(token),
        files={"file": ("students.csv", io.BytesIO(csv.encode()), "text/csv")},
    )
    assert r.status_code == 201, r.text
    return r.json()


def last_message(phone_digits: str, kind: str) -> str:
    for m in reversed(dev_outbox()):
        if m.kind == kind and m.to.endswith(phone_digits[-10:]):
            return m.body
    raise AssertionError(f"no {kind} message to {phone_digits}")


def consent_token(phone: str) -> str:
    body = last_message(phone, "consent_link")
    return re.search(r"/consent/([\w-]+)", body).group(1)


def last_otp(phone: str) -> str:
    return re.search(r"\b(\d{6})\b", last_message(phone, "otp")).group(1)


def give_consent(client, phone: str, participate=True, voice=True, share=False, language="en") -> str:
    token = consent_token(phone)
    assert client.post(f"/api/consent/{token}/otp").status_code == 202
    r = client.post(
        f"/api/consent/{token}",
        json={
            "code": last_otp(phone),
            "participate": participate,
            "voice": voice,
            "share_with_school": share,
            "language": language,
        },
    )
    assert r.status_code == 200, r.text
    return r.json()["token"]


def unique_phone() -> str:
    return "9" + str(uuid.uuid4().int)[:9]
