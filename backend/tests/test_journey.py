"""End-to-end through the HTTP API: onboarding, consent, 7 sessions, reports, sharing, withdrawal."""

from datetime import date

from sqlalchemy import func, select

from app.core.db import get_sessionmaker
from app.models import Cycle, DeletionRecord, Feature, ItemEvent, Report, SkillScore, Student
from app.sim.api_player import play_cycle_via_api
from app.sim.simulator import PERSONAS
from tests.helpers import auth, give_consent, last_otp, make_class, signup_school, unique_phone, upload


def test_full_journey(client, relaxed_schedule):
    admin = signup_school(client, "Sunrise Public School")
    klass = make_class(client, admin)
    phone_a, phone_b = unique_phone(), unique_phone()
    up = upload(client, admin, klass["id"], [("Riya Sharma", phone_a, "hi"), ("Kabir Khan", phone_b, "en")])
    assert len(up["created"]) == 2 and all(len(s["pin"]) == 4 for s in up["created"])
    riya, kabir = up["created"]

    # No data before consent: the student cannot log in.
    r = client.post("/api/auth/student/login", json={"class_code": klass["class_code"], "pin": riya["pin"]})
    assert r.status_code == 403 and r.json()["detail"] == "consent_required"

    parent_token = give_consent(client, phone_a, participate=True, voice=True, share=True, language="hi")
    give_consent(client, phone_b, participate=False)

    tracker = client.get(f"/api/school/classes/{klass['id']}/roster", headers=auth(admin)).json()
    states = {s["name"]: s["consent"] for s in tracker["students"]}
    assert states == {"Riya Sharma": "yes", "Kabir Khan": "no"}

    sched = client.post(
        f"/api/school/classes/{klass['id']}/schedule",
        json={"start_date": date.today().isoformat(), "mode": "lab"},
        headers=auth(admin),
    )
    assert sched.status_code == 200 and sched.json()["cycles_created"] == 1

    login = client.post("/api/auth/student/login", json={"class_code": klass["class_code"], "pin": riya["pin"]})
    assert login.status_code == 200, login.text
    student_token = login.json()["token"]
    home = client.get("/api/student/home", headers=auth(student_token)).json()
    assert len(home["sessions"]) == 7 and home["voice_allowed"] is True

    # Sessions must run in order.
    assert client.post("/api/student/sessions/2/start", json={}, headers=auth(student_token)).status_code == 409

    results = play_cycle_via_api(client, student_token, PERSONAS["balanced"], "11-14")
    assert results[-1]["cycle_completed"] is True
    assert sum(r["events"] for r in results) > 200

    with get_sessionmaker()() as db:
        cycle = db.scalars(select(Cycle).where(Cycle.student_id == riya["student_id"])).one()
        assert cycle.status == "scored" and cycle.scoring_version == "1.0.0"
        assert db.scalar(select(func.count()).select_from(SkillScore).where(SkillScore.cycle_id == cycle.id)) == 24
        reports = db.scalars(select(Report).where(Report.cycle_id == cycle.id)).all()
        assert {r.audience for r in reports} == {"parent", "student"}
        assert {r.language for r in reports if r.audience == "parent"} == {"hi"}
        assert all(r.status == "released" for r in reports), [r.wording_flags for r in reports]
        assert "Riya" not in str([r.content for r in reports])  # names are not stored in report content

    children = client.get("/api/parent/children", headers=auth(parent_token)).json()
    assert children[0]["report_ready"] is True and children[0]["progress"]["sessions_completed"] == 7
    rep = client.get(f"/api/parent/children/{riya['student_id']}/report", headers=auth(parent_token)).json()
    assert rep["content"]["language"] == "hi" and "Riya" in rep["content"]["title"]
    assert rep["content"]["disclaimer"].startswith("यह एक स्क्रीनिंग")
    en = client.get(f"/api/parent/children/{riya['student_id']}/report?lang=en", headers=auth(parent_token)).json()
    assert en["content"]["language"] == "en"
    assert en["content"]["disclaimer"].startswith("This is a screening profile")
    for finding in en["content"]["strengths"] + en["content"]["areas_to_grow"]:
        assert finding["evidence_line"] and finding["evidence_level"] in ("High", "Medium")
    pdf = client.get(f"/api/parent/children/{riya['student_id']}/report?fmt=pdf", headers=auth(parent_token))
    assert pdf.status_code == 200 and pdf.content[:4] == b"%PDF"

    student_rep = client.get("/api/student/report", headers=auth(student_token)).json()["content"]
    assert len(student_rep["strengths"]) <= 3 and len(student_rep["areas_to_grow"]) <= 2
    assert "evidence_line" not in str(student_rep) and "score" not in student_rep

    # Shared with school: the school can open it; dashboard shows completion.
    shared = client.get("/api/school/reports", headers=auth(admin)).json()
    assert [s["name"] for s in shared] == ["Riya Sharma"]
    assert client.get(f"/api/school/reports/{riya['student_id']}", headers=auth(admin)).status_code == 200
    assert client.get(f"/api/school/reports/{kabir['student_id']}", headers=auth(admin)).status_code == 403
    dash = client.get("/api/school/dashboard", headers=auth(admin)).json()
    assert dash["classes"][0]["completed_all"] == 1 and dash["classes"][0]["consent"]["no"] == 1

    # Withdrawal deletes everything about the student and confirms to the parent.
    with get_sessionmaker()() as db:
        session_ids = [
            s.id for c in db.scalars(select(Cycle).where(Cycle.student_id == riya["student_id"])) for s in c.sessions
        ]
    w = client.post(f"/api/parent/children/{riya['student_id']}/withdraw", headers=auth(parent_token))
    assert w.status_code == 202
    with get_sessionmaker()() as db:
        assert db.get(Student, riya["student_id"]) is None
        assert db.scalars(select(Cycle).where(Cycle.student_id == riya["student_id"])).first() is None
        for model in (ItemEvent, Feature):
            assert db.scalar(select(func.count()).select_from(model).where(model.session_id.in_(session_ids))) == 0
        record = db.scalars(select(DeletionRecord).order_by(DeletionRecord.id.desc())).first()
        assert record.completed_at is not None and record.pending_student_id is None and record.confirmation_sent
    assert client.get("/api/parent/children", headers=auth(parent_token)).json() == []


def test_events_are_idempotent_and_rescored_on_server(client, relaxed_schedule):
    admin = signup_school(client)
    klass = make_class(client, admin)
    phone = unique_phone()
    pin = upload(client, admin, klass["id"], [("Dev Patel", phone, "en")])["created"][0]["pin"]
    give_consent(client, phone, voice=False)
    client.post(
        f"/api/school/classes/{klass['id']}/schedule",
        json={"start_date": date.today().isoformat()},
        headers=auth(admin),
    )
    token = client.post("/api/auth/student/login", json={"class_code": klass["class_code"], "pin": pin}).json()["token"]
    bundle = client.post("/api/student/sessions/1/start", json={}, headers=auth(token)).json()["bundle"]
    t4 = next(t for t in bundle["tasks"] if t["task_id"] == "T4")["items"][0]
    wrong = "same" if t4["answer_key"]["correct"] == "different" else "different"
    event = {
        "client_event_id": "evt-00000001",
        "item_id": t4["id"],
        "task_id": "T4",
        "seq": 1,
        "response_ms": 900,
        "answer": wrong,
        "client_correct": True,
    }
    first = client.post("/api/student/sessions/1/events", json={"events": [event]}, headers=auth(token)).json()
    again = client.post("/api/student/sessions/1/events", json={"events": [event]}, headers=auth(token)).json()
    assert first["accepted"] == 1 and again == {"accepted": 0, "duplicates": 1, "rejected": 0}
    with get_sessionmaker()() as db:
        ev = db.scalars(select(ItemEvent).where(ItemEvent.client_event_id == "evt-00000001")).one()
        assert ev.correct is False  # the server's answer key wins over the device's claim
    # Voice features are dropped without voice consent; text features are kept.
    feats = client.post(
        "/api/student/sessions/1/features",
        headers=auth(token),
        json={
            "features": [
                {"name": "t7.wpm", "value": 120, "channel": "voice", "task_id": "T7"},
                {"name": "t11.word_count", "value": 30, "channel": "text", "task_id": "T11"},
                {"name": "x.secret", "value": 1, "channel": "text"},
            ]
        },
    ).json()
    assert feats == {"accepted": 1, "rejected": 2}


def test_parent_otp_login_and_lockout(client):
    admin = signup_school(client)
    klass = make_class(client, admin)
    phone = unique_phone()
    upload(client, admin, klass["id"], [("Meera Iyer", phone, "en")])
    assert client.post("/api/auth/parent/otp", json={"phone": phone}).status_code == 202
    assert client.post("/api/auth/parent/otp", json={"phone": "9999999999"}).status_code == 202  # no enumeration
    code = last_otp(phone)
    bad = client.post(
        "/api/auth/parent/verify", json={"phone": phone, "code": "000000" if code != "000000" else "111111"}
    )
    assert bad.status_code == 401
    ok = client.post("/api/auth/parent/verify", json={"phone": phone, "code": code})
    assert ok.status_code == 200 and ok.json()["role"] == "parent"
    for _ in range(5):
        client.post("/api/auth/student/login", json={"class_code": klass["class_code"], "pin": "0000"})
    locked = client.post("/api/auth/student/login", json={"class_code": klass["class_code"], "pin": "0000"})
    assert locked.status_code == 429
