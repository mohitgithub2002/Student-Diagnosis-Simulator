"""Root-cause tagging (FR-16). Every wrong answer gets at most one of 6 tags, applied only when both the
trigger pattern and its confirming signal appear; otherwise it stays untagged (Blueprint table)."""

import statistics
from collections import defaultdict
from typing import Any

from app.scoring.features import change_dirs

TAGS = ("pressure_error", "language_barrier", "guess", "careless_slip", "attention_lapse", "concept_gap")
RULE_IDS = {
    "concept_gap": "CG1",
    "careless_slip": "CS1",
    "pressure_error": "PE1",
    "language_barrier": "LB1",
    "attention_lapse": "AL1",
    "guess": "GU1",
}


def _median(values: list[float]) -> float | None:
    vals = [v for v in values if v is not None]
    return float(statistics.median(vals)) if vals else None


def tag_errors(
    events: list[dict[str, Any]], th: dict, levels: dict[str, float], t7_error_rate: float | None = None
) -> list[dict[str, Any]]:
    scored = sorted([e for e in events if e.get("correct") is not None], key=lambda e: (e["session"], e["seq"]))
    task_rt: dict[str, float | None] = {}
    task_fc: dict[str, float | None] = {}
    by_task: dict[str, list[dict]] = defaultdict(list)
    for e in scored:
        by_task[e["task"]].append(e)
    for task, evs in by_task.items():
        task_rt[task] = _median([e.get("response_ms") for e in evs if not e.get("skipped")])
        task_fc[task] = _median([e.get("first_click_ms") for e in evs])

    def n_options(e: dict) -> int:
        return max(2, len(e["content"].get("options", [])) or 2)

    def is_hard(e: dict) -> bool:
        if e["task"] == "T19" or "hard" in e.get("tags", []):
            return True
        ref = levels.get(e["task"])
        return ref is not None and (e.get("level") or 0) >= ref + th["guess_level_margin"]

    def fast(e: dict, ratio: float) -> bool:
        med = task_rt.get(e["task"])
        return bool(med and e.get("response_ms") is not None and e["response_ms"] < ratio * med)

    fast_hard = [e for e in scored if is_hard(e) and fast(e, th["guess_rt_ratio"])]
    fast_hard_acc = (sum(1 for e in fast_hard if e["correct"]) / len(fast_hard)) if fast_hard else None

    concept_wrong: dict[tuple, list[dict]] = defaultdict(list)
    concept_all: dict[tuple, list[dict]] = defaultdict(list)
    for e in scored:
        concept = e["content"].get("concept")
        if concept:
            concept_all[(e["task"], concept)].append(e)
            if not e["correct"]:
                concept_wrong[(e["task"], concept)].append(e)

    native_correct_groups = {
        (e["session"], e["variant_group"])
        for e in scored
        if e.get("language") in ("hi", "hinglish") and e["correct"] and e.get("variant_group")
    }
    native_rt = _median(
        [e.get("response_ms") for e in scored if e.get("language") in ("hi", "hinglish") and e["task"] == "T23"]
    )
    relaxed_by_pair = {
        (e["session"], e["content"].get("pair")): e
        for e in scored
        if e["task"] == "T17" and e["content"].get("condition") == "relaxed"
    }

    out = []
    for e in scored:
        if e["correct"]:
            continue
        tag = None
        # Pressure-driven error: right in the relaxed round, wrong under the timer.
        if e["task"] == "T17" and e["content"].get("condition") == "pressure":
            twin = relaxed_by_pair.get((e["session"], e["content"].get("pair")))
            if twin and twin["correct"]:
                dirs = change_dirs(e)
                relaxed_fc = task_fc.get("T17")
                hesitated = (e.get("max_idle_ms") or 0) >= th["pressure_idle_ms"] or (
                    relaxed_fc and (e.get("first_click_ms") or 0) > 1.5 * relaxed_fc
                )
                if dirs["rw"] > 0 or hesitated:
                    tag = "pressure_error"
        # Reading or language barrier: wrong in English, right on the Hindi/Hinglish version.
        if (
            tag is None
            and e.get("language") == "en"
            and (e["session"], e.get("variant_group")) in native_correct_groups
        ):
            rereads = (e.get("extra") or {}).get("rereads", 0)
            slow = native_rt and (e.get("response_ms") or 0) > th["language_rt_ratio"] * native_rt
            if rereads >= 2 or slow or (t7_error_rate is not None and t7_error_rate > 0.08):
                tag = "language_barrier"
        # Guess: fast answer on a hard item, low confidence, near-chance accuracy on such items.
        if tag is None and is_hard(e) and fast(e, th["guess_rt_ratio"]):
            chance = 1 / n_options(e)
            if (
                (e.get("confidence") or 4) <= 2
                and fast_hard_acc is not None
                and fast_hard_acc <= chance + th["guess_chance_margin"]
            ):
                tag = "guess"
        # Careless slip: a similar item was right in the same session; answered very fast.
        if tag is None and fast(e, th["careless_rt_ratio"]):
            similar_right = any(
                o["correct"]
                and o["id"] != e["id"]
                and o["session"] == e["session"]
                and o["task"] == e["task"]
                and abs((o.get("level") or 0) - (e.get("level") or 0)) <= 1
                and o["content"].get("concept") == e["content"].get("concept")
                for o in by_task[e["task"]]
            )
            extra = e.get("extra") or {}
            retry_ok = (not extra.get("retried")) or extra.get("retry_correct")
            if similar_right and retry_ok:
                tag = "careless_slip"
        # Attention lapse: errors cluster late in the task, with idle gaps or app switches nearby.
        if tag is None:
            run = [o for o in by_task[e["task"]] if o["session"] == e["session"]]
            if len(run) >= 6:
                third = len(run) // 3
                pos = run.index(e)
                early = run[:third]
                late = run[-third:]
                early_err = sum(1 for o in early if not o["correct"]) / len(early)
                late_err = sum(1 for o in late if not o["correct"]) / len(late)
                if pos >= len(run) - third and late_err >= 0.3 and late_err >= 2 * early_err:
                    nearby = run[max(0, pos - 2) : pos + 1]
                    if any(
                        (o.get("max_idle_ms") or 0) >= th["attention_idle_ms"] or (o.get("switches") or 0) > 0
                        for o in nearby
                    ):
                        tag = "attention_lapse"
        # Concept gap: same idea wrong in 3+ forms, including an easier version; not rushed; retry didn't fix it.
        if tag is None:
            concept = e["content"].get("concept")
            wrongs = concept_wrong.get((e["task"], concept), []) if concept else []
            if len({o["item_id"] for o in wrongs}) >= th["concept_min_errors"]:
                easier_failed = any((o.get("level") or 0) < (e.get("level") or 0) for o in wrongs) or (
                    min(o.get("level") or 0 for o in concept_all[(e["task"], concept)]) == (e.get("level") or 0)
                    and not any(
                        o["correct"]
                        for o in concept_all[(e["task"], concept)]
                        if (o.get("level") or 0) == (e.get("level") or 0)
                    )
                )
                med = task_rt.get(e["task"])
                not_rushed = med is None or (e.get("response_ms") or 0) >= th["concept_rt_ratio"] * med
                extra = e.get("extra") or {}
                if easier_failed and not_rushed and not extra.get("retry_correct"):
                    tag = "concept_gap"
        if tag:
            out.append(
                {
                    "event_id": e["id"],
                    "item_id": e["item_id"],
                    "tag": tag,
                    "rule_id": RULE_IDS[tag],
                    "session": e["session"],
                    "task": e["task"],
                }
            )
    return out
