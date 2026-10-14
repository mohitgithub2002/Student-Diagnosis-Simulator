"""Role-based access (FR-01) and the internal admin console (FR-25 to FR-27)."""

from datetime import date

from sqlalchemy import select

from app.core.db import get_sessionmaker
from app.core.security import hash_password
from app.models import Cycle, Report, StaffUser
from app.reports.wording import DISCLAIMER
from app.sim.api_player import play_cycle_via_api
from app.sim.simulator import PERSONAS
from tests.helpers import auth, give_consent, make_class, signup_school, unique_phone, upload


def staff_token(client, role: str) -> str:
    email = f"{role}-{unique_phone()}@revenuelogy.com"
    with get_sessionmaker()() as db:
        db.add(StaffUser(email=email, name=role.title(), password_hash=hash_password("reviewer-pass-1"), role=role))
        db.commit()
    r = client.post("/api/auth/staff/login", json={"email": email, "password": "reviewer-pass-1"})
    assert r.status_code == 200, r.text
    return r.json()["token"]


def test_role_boundaries(client):
    admin_a = signup_school(client, "School A")
    admin_b = signup_school(client, "School B")
    class_a = make_class(client, admin_a)
    phone = unique_phone()
    upload(client, admin_a, class_a["id"], [("Asha Rao", phone, "en")])
    parent = give_consent(client, phone)

    teacher_email = f"teacher-{unique_phone()}@schoola.in"
    assert (
        client.post(
            "/api/school/teachers",
            json={"name": "T", "email": teacher_email, "password": "teacher-pass"},
            headers=auth(admin_a),
        ).status_code
        == 201
    )
    teacher = client.post("/api/auth/staff/login", json={"email": teacher_email, "password": "teacher-pass"}).json()[
        "token"
    ]
    reviewer = staff_token(client, "reviewer")

    assert client.get("/api/school/dashboard", headers=auth(teacher)).status_code == 200
    assert (
        client.post("/api/school/classes", json={"grade": "8", "age_band": "11-14"}, headers=auth(teacher)).status_code
        == 403
    )
    assert client.get(f"/api/school/classes/{class_a['id']}/roster", headers=auth(admin_b)).status_code == 404
    assert client.get("/api/school/dashboard", headers=auth(parent)).status_code == 403
    assert client.get("/api/admin/items", headers=auth(admin_a)).status_code == 403
    assert client.get("/api/admin/items", headers=auth(parent)).status_code == 403
    assert client.get("/api/parent/children", headers=auth(admin_a)).status_code == 403
    assert client.get("/api/admin/review-queue", headers=auth(reviewer)).status_code == 200
    assert client.get("/api/admin/audit", headers=auth(reviewer)).status_code == 403
    assert client.get("/api/school/dashboard").status_code == 401
    assert client.get("/api/school/dashboard", headers=auth("not-a-token")).status_code == 401


def test_item_bank_management(client):
    reviewer = staff_token(client, "reviewer")
    listing = client.get("/api/admin/items?task_id=T9&language=hi&age_band=11-14", headers=auth(reviewer)).json()
    assert listing["total"] > 0 and all(i["language"] == "hi" for i in listing["items"])
    item_id = listing["items"][0]["id"]
    r = client.patch(
        f"/api/admin/items/{item_id}",
        json={"status": "retired", "tags": ["vocabulary", "reviewed"]},
        headers=auth(reviewer),
    )
    assert r.status_code == 200 and r.json()["status"] == "retired"
    new = {
        "id": "T9-1114-L03-en-900",
        "task_id": "T9",
        "age_band": "11-14",
        "level": 3,
        "language": "en",
        "content": {
            "kind": "choice",
            "prompt": "What does “brisk” mean?",
            "stem": {"sentence": "A brisk walk.", "word": "brisk"},
            "options": [{"id": "a", "text": "Quick"}, {"id": "b", "text": "Slow"}],
        },
        "answer_key": {"correct": "a"},
        "tags": ["vocabulary"],
    }
    assert client.post("/api/admin/items", json=new, headers=auth(reviewer)).status_code == 201
    assert client.post("/api/admin/items", json=new, headers=auth(reviewer)).status_code == 409
    tasks = client.get("/api/admin/tasks", headers=auth(reviewer)).json()
    assert len(tasks) == 23
    assert (
        client.patch(f"/api/admin/items/{item_id}", json={"status": "active"}, headers=auth(reviewer)).status_code
        == 200
    )


def test_scoring_config_versions(client):
    reviewer = staff_token(client, "reviewer")
    superadmin = staff_token(client, "superadmin")
    default = client.get("/api/admin/scoring-configs/default", headers=auth(reviewer)).json()
    bad = {"version": "1.0.1", "config": {"skills": {"working_memory": [["no.such_feature", 1]]}}}
    assert client.post("/api/admin/scoring-configs", json=bad, headers=auth(reviewer)).status_code == 422
    default["thresholds"]["pressure_drop_threshold"] = 0.2
    ok = client.post(
        "/api/admin/scoring-configs",
        json={"version": "1.1.0", "config": default, "notes": "pilot"},
        headers=auth(reviewer),
    )
    assert ok.status_code == 201
    assert (
        client.post(
            "/api/admin/scoring-configs", json={"version": "1.1.0", "config": default}, headers=auth(reviewer)
        ).status_code
        == 409
    )
    assert client.post("/api/admin/scoring-configs/1.1.0/activate", headers=auth(reviewer)).status_code == 403
    assert client.post("/api/admin/scoring-configs/1.1.0/activate", headers=auth(superadmin)).status_code == 200
    versions = {
        c["version"]: c["active"] for c in client.get("/api/admin/scoring-configs", headers=auth(reviewer)).json()
    }
    assert versions == {"1.0.0": False, "1.1.0": True}
    assert client.post("/api/admin/scoring-configs/1.0.0/activate", headers=auth(superadmin)).status_code == 200


def test_review_queue_flow(client, relaxed_schedule):
    admin = signup_school(client)
    klass = make_class(client, admin, "15-18")
    phone = unique_phone()
    pin = upload(client, admin, klass["id"], [("Neha Gupta", phone, "en")])["created"][0]["pin"]
    give_consent(client, phone, voice=False)
    client.post(
        f"/api/school/classes/{klass['id']}/schedule",
        json={"start_date": date.today().isoformat()},
        headers=auth(admin),
    )
    token = client.post("/api/auth/student/login", json={"class_code": klass["class_code"], "pin": pin}).json()["token"]
    play_cycle_via_api(client, token, PERSONAS["careless"], "15-18")

    with get_sessionmaker()() as db:
        cycle = db.scalars(select(Cycle).join(Report, Report.cycle_id == Cycle.id).order_by(Cycle.id.desc())).first()
        report = db.scalars(select(Report).where(Report.cycle_id == cycle.id, Report.audience == "parent")).one()
        # Simulate a template change that slipped a banned word in, then route it to review.
        report.status = "in_review"
        report.released_at = None
        content = dict(report.content)
        content["intro"] = content["intro"] + " Reading is weak."
        report.content = content
        report.wording_flags = [{"rule": "banned_word", "path": "intro", "match": "weak"}]
        db.commit()
        report_id = report.id

    reviewer = staff_token(client, "reviewer")
    queue = client.get("/api/admin/review-queue", headers=auth(reviewer)).json()
    entry = next(q for q in queue if q["id"] == report_id)
    assert entry["student_ref"].startswith("S-") and "Neha" not in str(entry)
    detail = client.get(f"/api/admin/reports/{report_id}", headers=auth(reviewer)).json()
    assert "Neha" not in detail["preview_html"] and "the student" in detail["preview_html"]
    blocked = client.post(f"/api/admin/reports/{report_id}/approve", headers=auth(reviewer))
    assert blocked.status_code == 422
    fixed = dict(detail["content"])
    fixed["intro"] = fixed["intro"].replace(" Reading is weak.", "")
    edit = client.put(f"/api/admin/reports/{report_id}", json={"content": fixed}, headers=auth(reviewer)).json()
    assert edit["flags"] == []
    assert client.post(f"/api/admin/reports/{report_id}/approve", headers=auth(reviewer)).json()["status"] == "released"
    assert fixed["disclaimer"] == DISCLAIMER["en"]

    stats = client.get("/api/admin/items/stats?task_id=T4", headers=auth(reviewer)).json()
    assert stats and {"p_correct", "median_rt_ms", "error_tags"} <= set(stats[0])
    rel = client.get("/api/admin/reliability", headers=auth(reviewer)).json()
    assert set(rel) >= {"t1.backward_span", "t3.hit_minus_fa", "t17.relaxed_acc"}
    superadmin = staff_token(client, "superadmin")
    log = client.get("/api/admin/audit?limit=200", headers=auth(superadmin)).json()
    assert {"report_approved", "report_edited"} <= {row["action"] for row in log}
