from collections import Counter

from app.content.tasks import SESSION_PLAN, TASKS
from app.scoring.checks import check
from app.services.bundle import build_bundle


def test_23_tasks_and_session_plan():
    assert [t["id"] for t in TASKS] == [f"T{i}" for i in range(1, 24)]
    planned = {tid for s in SESSION_PLAN.values() for tid, _ in s["tasks"]}
    assert planned == {f"T{i}" for i in range(1, 24)} - {"T13"}  # T13 is embedded in every task
    assert len(SESSION_PLAN) == 7


def test_item_bank_is_deterministic_and_unique(items):
    from app.content.seed import all_items

    ids = [i["id"] for i in items]
    assert len(ids) == len(set(ids))
    assert [i["id"] for i in all_items()] == ids
    tasks = Counter(i["task_id"] for i in items)
    assert set(tasks) == {f"T{i}" for i in range(1, 24)} - {"T13"}


def test_every_answer_key_is_accepted_by_the_checker(items):
    for it in items:
        c, k = it["content"], it["answer_key"]
        if c["kind"] == "choice" and "correct" in k:
            assert check(c, k, k["correct"]) is True, it["id"]
            assert k["correct"] in {o["id"] for o in c["options"]}, it["id"]
        if c["kind"] == "sequence":
            assert check(c, k, k["sequence"]) is True
        if c["kind"] == "plan_route":
            assert check(c, k, k["best_order"]) is True
        if c["kind"] == "passage_questions":
            for q in c["questions"]:
                assert check(c, k, k["answers"][q["id"]], {"qid": q["id"]}) is True


def test_bilingual_items_share_structure(items):
    by_group = {}
    for it in items:
        if it["task_id"] == "T23":
            by_group.setdefault(it["variant_group"], []).append(it)
    for group in by_group.values():
        assert sorted(i["language"] for i in group) == ["en", "hi", "hinglish"]
        assert len({i["answer_key"]["correct"] for i in group}) == 1


def test_bundles_fit_the_budget(lookup):
    import json

    seen_t2, group = None, None
    for number in range(1, 8):
        for band in ("11-14", "15-18"):
            for lang in ("en", "hi", "hinglish"):
                b = build_bundle(number, band, lang, 99, lookup, {"t2_item": seen_t2, "t2_group": group})
                size = len(json.dumps(b, ensure_ascii=False).encode())
                assert size < 15 * 1024 * 1024  # PRD: under 15 MB per session
                assert all(t["items"] or t.get("pools") for t in b["tasks"]), (number, band, lang)
                if number == 4 and band == "11-14" and lang == "en":
                    first = next(t for t in b["tasks"] if t["task_id"] == "T2")["items"][0]
                    seen_t2, group = first["id"], first["variant_group"]
    s7 = build_bundle(7, "11-14", "en", 5, lookup, {"t2_item": seen_t2})
    t2 = next(t for t in s7["tasks"] if t["task_id"] == "T2")
    assert t2["items"][0]["id"] == seen_t2 and t2["settings"]["phase"] == "delayed"
    s7_hi = build_bundle(7, "11-14", "hi", 5, lookup, {"t2_item": seen_t2, "t2_group": group})
    t2_hi = next(t for t in s7_hi["tasks"] if t["task_id"] == "T2")
    assert t2_hi["items"][0]["variant_group"] == group and t2_hi["items"][0]["language"] == "hi"
    missed = build_bundle(7, "11-14", "en", 5, lookup, {})
    assert next(t for t in missed["tasks"] if t["task_id"] == "T2")["settings"]["phase"] == "immediate"


def test_t23_probe_mixes_languages(lookup):
    b = build_bundle(2, "11-14", "en", 3, lookup)
    t23 = next(t for t in b["tasks"] if t["task_id"] == "T23")
    langs = Counter(i["language"] for i in t23["items"])
    assert langs["en"] == langs["hi"] == 6
