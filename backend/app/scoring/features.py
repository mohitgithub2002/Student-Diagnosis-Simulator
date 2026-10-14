"""Feature extraction: per-session raw features from item events, on-device voice/text features and
session logs. Pure functions over plain dicts so the same inputs always give the same features."""

import statistics
from collections import defaultdict
from collections.abc import Iterable
from datetime import date, datetime
from typing import Any

from app.content.prng import stream_sequence
from app.scoring.checks import check
from app.scoring.staircase import estimate_from_trials

Event = dict[str, Any]
FeatureRow = dict[str, Any]  # {"session", "name", "value", "channel", "task"}


def mean(values: Iterable[float]) -> float | None:
    vals = [v for v in values if v is not None]
    return sum(vals) / len(vals) if vals else None


def median(values: Iterable[float]) -> float | None:
    vals = [v for v in values if v is not None]
    return float(statistics.median(vals)) if vals else None


def acc(events: list[Event]) -> float | None:
    scored = [e for e in events if e.get("correct") is not None]
    return sum(1 for e in scored if e["correct"]) / len(scored) if scored else None


def cv(values: list[float]) -> float | None:
    vals = [v for v in values if v is not None]
    if len(vals) < 3:
        return None
    m = statistics.mean(vals)
    return statistics.pstdev(vals) / m if m else None


def is_distraction(e: Event, th: dict) -> bool:
    if e.get("kind") in ("stream", "allocate", "choice_menu", "bonus_offer", "survey", "text_response"):
        return False
    rt = e.get("response_ms")
    if (
        rt is not None
        and not e.get("skipped")
        and rt < th["noise_min_response_ms"]
        and e["task"] not in th["noise_exempt_tasks"]
    ):
        return True
    return (e.get("max_idle_ms") or 0) > th["noise_max_idle_ms"]


def change_dirs(e: Event) -> dict[str, int]:
    """Count answer changes by direction (wrong-to-right, right-to-wrong) using the server answer key."""
    out = {"wr": 0, "rw": 0, "ww": 0, "rr": 0}
    for ch in e.get("change_log") or []:
        before = check(e["content"], e["key"], ch.get("from"), e.get("extra"))
        after = check(e["content"], e["key"], ch.get("to"), e.get("extra"))
        if before is None or after is None:
            continue
        out[("r" if before else "w") + ("r" if after else "w")] += 1
    return out


class Collector:
    def __init__(self) -> None:
        self.rows: list[FeatureRow] = []

    def add(self, session: int, name: str, value: float | None, channel: str = "timing", task: str = "") -> None:
        if value is None:
            return
        self.rows.append(
            {"session": session, "name": name, "value": round(float(value), 4), "channel": channel, "task": task}
        )


def _span(events: list[Event], threshold: float) -> float | None:
    by_len: dict[int, list[bool]] = defaultdict(list)
    for e in events:
        if e.get("correct") is None:
            continue
        by_len[len(e["content"].get("sequence", []))].append(bool(e["correct"]))
    if not by_len:
        return None
    good = [length for length, results in by_len.items() if sum(results) / len(results) >= threshold]
    return float(max(good)) if good else float(min(by_len) - 1)


def t1_features(c: Collector, s: int, events: list[Event], th: dict) -> None:
    fwd = [e for e in events if e["content"].get("direction") == "forward"]
    bwd = [e for e in events if e["content"].get("direction") == "backward"]
    c.add(s, "t1.forward_span", _span(fwd, th["span_accuracy"]), task="T1")
    c.add(s, "t1.backward_span", _span(bwd, th["span_accuracy"]), task="T1")
    c.add(s, "t1.accuracy", acc(events), task="T1")
    wrong = [e for e in events if e.get("correct") is False and isinstance(e.get("answer"), list)]
    if wrong:
        order_errors = sum(1 for e in wrong if sorted(map(str, e["answer"])) == sorted(e["key"]["sequence"]))
        c.add(s, "t1.order_error_share", order_errors / len(wrong), task="T1")


def t2_features(c: Collector, s: int, events: list[Event]) -> dict:
    qs = [e for e in events if e.get("extra", {}).get("qid")]
    detail = [e for e in qs if e["extra"].get("qtype") == "detail"]
    recog = [e for e in qs if e["extra"].get("qtype") == "recognition"]
    phase = "delayed" if any(e.get("condition") == "delayed" for e in events) else "immediate"
    c.add(s, f"t2.{phase}_acc", acc(detail), task="T2")
    lures = [e for e in recog if e["extra"]["qid"] in e["key"].get("lures", [])]
    if lures:
        c.add(s, "t2.false_alarm_rate", sum(1 for e in lures if e.get("answer") == "yes") / len(lures), task="T2")
    c.add(s, "t2.recognition_acc", acc(recog), task="T2")
    return {"phase": phase, "acc": acc(detail)}


def t3_block(e: Event) -> dict | None:
    stimuli = stream_sequence(e["content"])
    taps = (e.get("answer") or {}).get("taps", []) if isinstance(e.get("answer"), dict) else []
    tapped: dict[int, float] = {}
    for tap in taps:
        i = int(tap.get("i", -1))
        if 0 <= i < len(stimuli) and i not in tapped:
            tapped[i] = float(tap.get("rt", 0))
    targets = [st["i"] for st in stimuli if st["target"]]
    nontargets = [st["i"] for st in stimuli if not st["target"]]
    if not targets or not nontargets:
        return None
    hits = [i for i in targets if i in tapped]
    fas = [i for i in nontargets if i in tapped]
    return {
        "hit_rate": len(hits) / len(targets),
        "fa_rate": len(fas) / len(nontargets),
        "rts": [tapped[i] for i in hits],
    }


def t3_features(c: Collector, s: int, events: list[Event]) -> None:
    blocks = [b for b in (t3_block(e) for e in sorted(events, key=lambda e: e["seq"])) if b]
    if not blocks:
        return
    scores = [b["hit_rate"] - b["fa_rate"] for b in blocks]
    c.add(s, "t3.hit_minus_fa", mean(scores), task="T3")
    c.add(s, "t3.rt_cv", cv([rt for b in blocks for rt in b["rts"]]), task="T3")
    if len(scores) >= 2:
        c.add(s, "t3.decline", scores[0] - scores[-1], task="T3")
    if len(scores) >= 3:
        c.add(s, "t3.decline_after_2", mean(scores[:2]) - mean(scores[2:]), task="T3")


def _rt_correct(events: list[Event]) -> float | None:
    return median(e["response_ms"] for e in events if e.get("correct") and e.get("response_ms") is not None)


def speed_features(c: Collector, s: int, task: str, events: list[Event], th: dict, flags: dict) -> None:
    a = acc(events)
    c.add(s, f"{task.lower()}.accuracy", a, task=task)
    rt = _rt_correct(events)
    if a is not None and a >= th["speed_min_accuracy"]:
        c.add(s, f"{task.lower()}.median_rt_correct", rt, task=task)
    elif a is not None and rt is not None:
        # Withheld from the speed score; the engine decides whether it was fast enough to call impulsive.
        c.add(s, f"{task.lower()}.median_rt_inaccurate", rt, task=task)
        flags.setdefault("speed_withheld", []).append({"task": task, "accuracy": round(a, 3), "median_rt": rt})


def staircase_level(events: list[Event]) -> float | None:
    trials = [
        (int(e["level"]), bool(e["correct"]))
        for e in sorted(events, key=lambda e: e["seq"])
        if e.get("correct") is not None and e.get("level") is not None
    ]
    return estimate_from_trials(trials)


def t5_features(c: Collector, s: int, events: list[Event]) -> None:
    c.add(s, "t5.level", staircase_level(events), task="T5")
    c.add(s, "t5.accuracy", acc(events), task="T5")
    long_chain = [e for e in events if (e["content"].get("steps") or 0) >= 4]
    short_chain = [e for e in events if (e["content"].get("steps") or 0) == 3]
    c.add(s, "t5.long_chain_acc", acc(long_chain), task="T5")
    c.add(s, "t5.short_chain_acc", acc(short_chain), task="T5")
    per_step = [
        e["response_ms"] / max(1, e["content"].get("steps", 3))
        for e in events
        if e.get("correct") and e.get("response_ms")
    ]
    c.add(s, "t5.time_per_step", median(per_step), task="T5")
    ratios = [
        e["first_click_ms"] / e["response_ms"]
        for e in events
        if e.get("first_click_ms") is not None and e.get("response_ms")
    ]
    c.add(s, "t5.first_click_ratio", median(ratios), task="T5")


def t6_features(c: Collector, s: int, events: list[Event]) -> None:
    c.add(s, "t6.level", staircase_level(events), task="T6")
    c.add(s, "t6.accuracy", acc(events), task="T6")
    c.add(s, "t6.sequence_acc", acc([e for e in events if e["content"].get("concept") == "sequence"]), task="T6")
    c.add(s, "t6.rotation_acc", acc([e for e in events if e["content"].get("concept") == "rotation"]), task="T6")
    wrong = [e for e in events if e.get("correct") is False and e.get("answer") is not None]
    if wrong:
        near = sum(1 for e in wrong if e["answer"] in e["key"].get("near_miss", []))
        c.add(s, "t6.near_miss_share", near / len(wrong), task="T6")


def t8_features(c: Collector, s: int, events: list[Event]) -> None:
    qs = [e for e in events if e.get("extra", {}).get("qid")]
    direct = acc([e for e in qs if e["extra"].get("qtype") == "direct"])
    inference = acc([e for e in qs if e["extra"].get("qtype") == "inference"])
    c.add(s, "t8.direct_acc", direct, task="T8")
    c.add(s, "t8.inference_acc", inference, task="T8")
    if direct is not None and inference is not None:
        c.add(s, "t8.comprehension", 0.6 * inference + 0.4 * direct, task="T8")
    c.add(s, "t8.reread_rate", mean(e["extra"].get("rereads", 0) for e in qs), task="T8")
    per100 = []
    for e in events:
        if e.get("extra", {}).get("phase") == "study" and e.get("response_ms"):
            words = e["content"].get("passage", {}).get("word_count") or 0
            if words:
                per100.append(e["response_ms"] / 1000 / words * 100)
    c.add(s, "t8.silent_time_per_100w", median(per100), task="T8")


def t9_features(c: Collector, s: int, events: list[Event]) -> None:
    scored = [e for e in events if e.get("correct") is not None]
    if not scored:
        return
    c.add(s, "t9.accuracy", acc(scored), task="T9")
    total = sum(e["level"] for e in scored)
    c.add(s, "t9.weighted_acc", sum(e["level"] for e in scored if e["correct"]) / total if total else None, task="T9")
    med = median(e["response_ms"] for e in scored if e.get("response_ms"))
    if med:
        slow_correct = sum(1 for e in scored if e["correct"] and (e.get("response_ms") or 0) > med)
        fast_wrong = sum(1 for e in scored if not e["correct"] and (e.get("response_ms") or 0) < med * 0.5)
        c.add(s, "t9.clue_use", slow_correct / len(scored), task="T9")
        c.add(s, "t9.guess_rate", fast_wrong / len(scored), task="T9")


def t10_features(c: Collector, s: int, events: list[Event], th: dict, flags: dict) -> None:
    speed_features(c, s, "T10", events, th, flags)
    c.add(s, "t10.compare_acc", acc([e for e in events if e["content"].get("concept") == "compare"]), task="T10")
    errors = []
    for e in events:
        if e["content"].get("kind") == "estimate" and e.get("answer") is not None and not e.get("skipped"):
            try:
                span = float(e["content"]["max"]) - float(e["content"]["min"])
                errors.append(abs(float(e["answer"]) - float(e["key"]["value"])) / span)
            except (TypeError, ValueError, KeyError):
                continue
    if errors:
        c.add(s, "t10.estimation_error", mean(errors), task="T10")
        c.add(s, "t10.estimate_acc", 1 - mean(errors), task="T10")


def t12_features(c: Collector, s: int, events: list[Event]) -> None:
    qs = [e for e in events if e.get("extra", {}).get("qid")]
    by_type = {t: acc([e for e in qs if e["extra"].get("qtype") == t]) for t in ("recall", "near", "far")}
    for t, v in by_type.items():
        c.add(s, f"t12.{t}_acc", v, task="T12")
    a = acc([e for e in qs if e["extra"].get("set") == "A"])
    b = acc([e for e in qs if e["extra"].get("set") == "B"])
    if a is not None and b is not None:
        c.add(s, "t12.gain", b - a, task="T12")


def confidence_features(c: Collector, s: int, events: list[Event]) -> int:
    rated = [e for e in events if e.get("confidence") and e.get("correct") is not None]
    if not rated:
        return 0
    conf01 = [(e["confidence"] - 1) / 3 for e in rated]
    accuracy = sum(1 for e in rated if e["correct"]) / len(rated)
    c.add(s, "conf.mean", mean(conf01), channel="timing", task="T13")
    c.add(s, "conf.n", len(rated), task="T13")
    c.add(s, "conf.gap", mean(conf01) - accuracy, task="T13")
    right = [(e["confidence"] - 1) / 3 for e in rated if e["correct"]]
    wrong = [(e["confidence"] - 1) / 3 for e in rated if not e["correct"]]
    if right and wrong:
        c.add(s, "conf.resolution", mean(right) - mean(wrong), task="T13")
    c.add(s, "conf.right_n", len(right), task="T13")
    c.add(s, "conf.wrong_n", len(wrong), task="T13")
    c.add(s, "conf.unsure_correct", sum(1 for e in rated if e["correct"] and e["confidence"] <= 2), task="T13")
    c.add(s, "conf.sure_wrong", sum(1 for e in rated if not e["correct"] and e["confidence"] >= 3), task="T13")
    hes_r = median(e["first_click_ms"] for e in rated if e["correct"] and e.get("first_click_ms") is not None)
    hes_w = median(e["first_click_ms"] for e in rated if not e["correct"] and e.get("first_click_ms") is not None)
    if hes_r is not None and hes_w is not None:
        c.add(s, "conf.hesitation_link", hes_w - hes_r, task="T13")
    return len(rated)


def t14_features(c: Collector, s: int, events: list[Event]) -> None:
    from app.scoring.checks import route_cost

    effs, plan, restarts = [], [], []
    for e in events:
        if not isinstance(e.get("answer"), list):
            continue
        cost = route_cost(e["content"]["start"], e["content"]["places"], [str(a) for a in e["answer"]])
        if cost:
            effs.append(min(1.0, e["key"]["best_cost"] / cost))
        if e.get("response_ms") and e.get("extra", {}).get("plan_ms") is not None:
            plan.append(e["extra"]["plan_ms"] / e["response_ms"])
        restarts.append(e.get("extra", {}).get("restarts", 0))
    c.add(s, "t14.efficiency", mean(effs), task="T14")
    c.add(s, "t14.accuracy", acc(events), task="T14")
    c.add(s, "t14.plan_ratio", median(plan), task="T14")
    c.add(s, "t14.restarts", mean(restarts), task="T14")


def t15_features(c: Collector, s: int, events: list[Event]) -> None:
    first = [e for e in events if e.get("condition") != "review"]
    review = [e for e in events if e.get("condition") == "review"]
    c.add(s, "t15.detection_rate", acc(first), task="T15")
    if review:
        dirs = [change_dirs(e) for e in review]
        net = sum(d["wr"] - d["rw"] for d in dirs)
        c.add(s, "t15.review_net", net / max(1, len(first)), task="T15")


def t16_features(c: Collector, s: int, events: list[Event]) -> None:
    summary = [e for e in events if e["content"].get("kind") == "allocate"]
    if not summary:
        return
    ex = summary[-1].get("extra", {})
    planned, actual = ex.get("planned", {}), ex.get("actual", {})
    total = float(summary[-1]["content"].get("total_s", 180))
    if planned and actual:
        diff = sum(abs(float(planned.get(k, 0)) - float(actual.get(k, 0))) for k in set(planned) | set(actual))
        c.add(s, "t16.fit", max(0.0, 1 - diff / (2 * total)), task="T16")
        blocks = summary[-1]["content"].get("blocks", [])
        if blocks:
            first_id = blocks[0]["id"]
            spent = sum(float(v) for v in actual.values()) or 1.0
            c.add(s, "t16.front_load", float(actual.get(first_id, 0)) / spent, task="T16")
    n_items = sum(len(b.get("item_ids", [])) for b in summary[-1]["content"].get("blocks", []))
    if n_items:
        c.add(s, "t16.unfinished_share", float(ex.get("unfinished", 0)) / n_items, task="T16")
    c.add(s, "t16.unused_share", float(ex.get("unused_s", 0)) / total, task="T16")


def t17_features(c: Collector, s: int, events: list[Event]) -> dict | None:
    relaxed = [e for e in events if e["content"].get("condition") == "relaxed"]
    pressure = [e for e in events if e["content"].get("condition") == "pressure"]
    ra, pa = acc(relaxed), acc(pressure)
    if ra is None or pa is None:
        return None
    c.add(s, "t17.relaxed_acc", ra, task="T17")
    c.add(s, "t17.pressure_acc", pa, task="T17")
    c.add(s, "t17.drop", ra - pa, task="T17")

    def churn(evs: list[Event]) -> float:
        return sum(1 for e in evs if e.get("skipped") or (e.get("changes") or 0) > 0) / len(evs)

    c.add(s, "t17.change_skip_increase", churn(pressure) - churn(relaxed), task="T17")
    cv_r = cv([e["response_ms"] for e in relaxed if e.get("response_ms")])
    cv_p = cv([e["response_ms"] for e in pressure if e.get("response_ms")])
    if cv_r is not None and cv_p is not None:
        c.add(s, "t17.rt_cv_change", cv_p - cv_r, task="T17")
    c.add(
        s,
        "t17.timeout_share",
        sum(1 for e in pressure if e.get("extra", {}).get("timeout")) / len(pressure),
        task="T17",
    )
    return {"drop": ra - pa, "relaxed": ra, "pressure": pa, "n": len(pressure)}


def t18_features(c: Collector, s: int, events: list[Event]) -> int:
    menu = sorted([e for e in events if e["content"].get("kind") == "choice_menu"], key=lambda e: e["seq"])
    solved = sorted([e for e in events if e.get("condition") in ("t18_easy", "t18_hard")], key=lambda e: e["seq"])
    if menu:
        c.add(s, "t18.hard_share", sum(1 for e in menu if e.get("answer") == "hard") / len(menu), task="T18")
        after_error = []
        for m in menu:
            prev = [x for x in solved if x["seq"] < m["seq"]]
            if prev and prev[-1].get("correct") is False:
                after_error.append(1 if m.get("answer") == "easy" else 0)
        if after_error:
            c.add(s, "t18.after_error_easy", mean(after_error), task="T18")
    bonus = [e for e in events if e["content"].get("kind") == "bonus_offer"]
    if bonus:
        c.add(s, "t18.bonus", 1.0 if bonus[-1].get("answer") in (True, "yes", "accept") else 0.0, task="T18")
    return len(menu)


def t19_features(c: Collector, s: int, events: list[Event]) -> None:
    if not events:
        return
    persist = [min(90.0, (e.get("response_ms") or 0) / 1000) for e in events]
    c.add(s, "t19.persist_s", mean(persist), task="T19")
    c.add(s, "t19.attempts", mean(e.get("extra", {}).get("attempts", 1) for e in events), task="T19")
    c.add(s, "t19.solved", acc(events), task="T19")


def t20_features(c: Collector, s: int, events: list[Event]) -> int:
    offered = [e for e in events if e.get("correct") is False and e.get("extra", {}).get("retry_offered")]
    if not offered:
        return 0
    c.add(s, "t20.retry_rate", mean(1 if e["extra"].get("retried") else 0 for e in offered), task="T20")
    for variant in ("effort", "ability"):
        sub = [e for e in offered if e["extra"].get("feedback_variant") == variant]
        if sub:
            c.add(s, f"t20.retry_after_{variant}", mean(1 if e["extra"].get("retried") else 0 for e in sub), task="T20")
    retried = [e for e in offered if e["extra"].get("retried")]
    if retried:
        c.add(s, "t20.retry_success", mean(1 if e["extra"].get("retry_correct") else 0 for e in retried), task="T20")
    return len(offered)


def t21_features(c: Collector, s: int, events: list[Event]) -> None:
    for e in events:
        qid = e["content"].get("qid")
        option = next((o for o in e["content"].get("options", []) if o["id"] == e.get("answer")), None)
        if qid and option is not None:
            c.add(s, f"t21.{qid}", option["value"], channel="selfreport", task="T21")


def t23_features(c: Collector, s: int, events: list[Event]) -> dict | None:
    en = [e for e in events if e.get("language") == "en"]
    native = [e for e in events if e.get("language") in ("hi", "hinglish")]
    groups_en = {e["variant_group"] for e in en}
    groups_nat = {e["variant_group"] for e in native}
    both = groups_en & groups_nat
    en_m = [e for e in en if e["variant_group"] in both]
    nat_m = [e for e in native if e["variant_group"] in both]
    a_en, a_nat = acc(en_m), acc(nat_m)
    if a_en is None or a_nat is None:
        return None
    gap = a_nat - a_en
    c.add(s, "t23.en_acc", a_en, task="T23")
    c.add(s, "t23.native_acc", a_nat, task="T23")
    c.add(s, "t23.gap", gap, task="T23")
    c.add(s, "t23.english_relative", 1 - max(0.0, gap), task="T23")
    rt_en = median(e["response_ms"] for e in en_m if e.get("response_ms"))
    rt_nat = median(e["response_ms"] for e in nat_m if e.get("response_ms"))
    if rt_en and rt_nat:
        c.add(s, "t23.rt_ratio_inv", rt_nat / rt_en, task="T23")
    return {"gap": gap, "en": a_en, "native": a_nat, "n": len(en_m)}


def rubric(
    word_count: float, keyword_share: float | None, connectors: float, avg_sentence: float, filler_rate: float
) -> float:
    if keyword_share is None:
        completeness = 4 if word_count >= 35 else 3 if word_count >= 20 else 2 if word_count >= 8 else 1
    else:
        completeness = (
            4
            if word_count >= 40 and keyword_share >= 0.375
            else 3
            if word_count >= 25 and keyword_share >= 0.25
            else 2
            if word_count >= 12
            else 1
        )
    order = 4 if connectors >= 3 else 3 if connectors >= 2 else 2 if connectors >= 1 else 1
    if word_count == 0:
        clarity = 1
    elif 6 <= avg_sentence <= 22 and filler_rate < 0.08:
        clarity = 4
    elif 4 <= avg_sentence <= 30:
        clarity = 3
    else:
        clarity = 2
    return (completeness + order + clarity) / 3


def text_task_features(c: Collector, s: int, task: str, events: list[Event], client: list[FeatureRow]) -> None:
    """T11 / T22 answers: features arrive per item from the device (raw text never leaves the device)."""
    per_item: dict[str, dict[str, float]] = defaultdict(dict)
    channel_of: dict[str, str] = {}
    for f in client:
        if f["task"] != task:
            continue
        per_item[f.get("item_id", "")][f["name"].split(".", 1)[1]] = f["value"]
        channel_of[f.get("item_id", "")] = f["channel"]
    prefix = task.lower()
    answered = [e for e in events if not e.get("skipped")]
    if events:
        c.add(s, f"{prefix}.answered_rate", len(answered) / len(events), task=task)
    rubrics, words, uniq, pauses, starts, voice = [], [], [], [], [], []
    for item_id, f in per_item.items():
        wc = f.get("word_count", 0)
        if wc <= 0:
            continue
        words.append(wc)
        if "unique_ratio" in f:
            uniq.append(f["unique_ratio"])
        kw = f.get("keyword_share") if task == "T11" else None
        rubrics.append(rubric(wc, kw, f.get("connectors", 0), f.get("avg_sentence_words", wc), f.get("filler_rate", 0)))
        if "pause_rate" in f:
            pauses.append(f["pause_rate"])
        if "speech_start_ms" in f:
            starts.append(f["speech_start_ms"])
        voice.append(1 if channel_of.get(item_id, "").startswith("voice") else 0)
    c.add(s, f"{prefix}.rubric", mean(rubrics), channel="text", task=task)
    c.add(s, f"{prefix}.word_count", mean(words), channel="text", task=task)
    c.add(s, f"{prefix}.mean_words", mean(words), channel="text", task=task)
    c.add(s, f"{prefix}.unique_ratio", mean(uniq), channel="text", task=task)
    c.add(s, f"{prefix}.pause_rate", mean(pauses), channel="voice", task=task)
    c.add(s, f"{prefix}.speech_start_ms", median(starts), channel="voice", task=task)
    c.add(s, f"{prefix}.voice_share", mean(voice), channel="text", task=task)


def t7_features(c: Collector, s: int, client: list[FeatureRow]) -> None:
    f = {row["name"].split(".", 1)[1]: row for row in client if row["task"] == "T7"}
    if "wpm" not in f:
        return
    wpm = f["wpm"]["value"]
    channel = f["wpm"]["channel"]
    error_rate = f["error_rate"]["value"] if "error_rate" in f else None
    c.add(s, "t7.wpm", wpm, channel=channel, task="T7")
    c.add(s, "t7.wpm_acc", wpm * (1 - error_rate) if error_rate is not None else wpm, channel=channel, task="T7")
    for name in ("pause_rate", "self_corrections", "error_rate", "speech_start_ms"):
        if name in f:
            c.add(s, f"t7.{name}", f[name]["value"], channel=f[name]["channel"], task="T7")


def cross_task_features(c: Collector, s: int, events: list[Event], distraction_ids: set[int]) -> None:
    scored = [e for e in events if e.get("correct") is not None]
    countable = [e for e in events if e["content"].get("kind") not in ("stream", "allocate", "survey")]
    if countable:
        c.add(s, "all.distraction_rate", sum(1 for e in countable if e["id"] in distraction_ids) / len(countable))
    quick = [e for e in scored if e["task"] in ("T4", "T10", "T17", "T20") and e["id"] not in distraction_ids]
    if quick and (acc(quick) or 0) >= 0.6:
        c.add(s, "all.median_rt_correct", _rt_correct(quick))
    # Accuracy on the item right after an error, within the same task.
    after = []
    by_task: dict[str, list[Event]] = defaultdict(list)
    for e in sorted(scored, key=lambda e: e["seq"]):
        by_task[e["task"]].append(e)
    for evs in by_task.values():
        for prev, nxt in zip(evs, evs[1:], strict=False):
            if prev["correct"] is False:
                after.append(1 if nxt["correct"] else 0)
    c.add(s, "all.post_error_acc", mean(after) if len(after) >= 2 else None)
    dirs = [change_dirs(e) for e in scored if e.get("change_log")]
    total = sum(d["wr"] + d["rw"] for d in dirs)
    if total >= 2:
        c.add(s, "all.net_changes", sum(d["wr"] - d["rw"] for d in dirs) / total)
    c.add(s, "all.hesitation", median(e["first_click_ms"] for e in scored if e.get("first_click_ms") is not None))


def log_features(c: Collector, sessions: list[dict], visits: list[datetime]) -> None:
    done = [x for x in sessions if x.get("completed_at")]
    last = max((x["number"] for x in done), default=7)
    c.add(last, "log.completion_rate", len(done) / max(1, len(sessions)), channel="log")
    if done:
        on_time = sum(1 for x in done if _as_date(x["completed_at"]) == _as_date(x["scheduled_for"]))
        c.add(last, "log.on_schedule_rate", on_time / len(done), channel="log")
    session_days = {_as_date(x["started_at"]) for x in sessions if x.get("started_at")}
    session_days |= {_as_date(x["completed_at"]) for x in done}
    if len(done) >= 2:
        first_day = min(_as_date(x["scheduled_for"]) for x in sessions)
        last_day = max(_as_date(x["completed_at"]) for x in done)
        other_days = {_as_date(v) for v in visits if first_day <= _as_date(v) <= last_day} - session_days
        c.add(last, "log.return_rate", min(1.0, len(other_days) / max(1, len(done) - 1)), channel="log")


def _as_date(v: Any) -> date:
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    return datetime.fromisoformat(str(v)).date()


def extract(
    events: list[Event],
    client_features: list[FeatureRow],
    sessions: list[dict],
    visits: list[datetime],
    thresholds: dict,
) -> tuple[list[FeatureRow], dict]:
    """Return (features, context) where context holds intermediate facts the engine reuses."""
    c = Collector()
    for f in client_features:
        if f["task"] not in ("T7", "T11", "T22"):
            c.add(f["session"], f["name"], f["value"], channel=f["channel"], task=f["task"])
    distraction_ids = {e["id"] for e in events if is_distraction(e, thresholds)}
    clean = [e for e in events if e["id"] not in distraction_ids]
    context: dict[str, Any] = {
        "distraction_ids": distraction_ids,
        "flags": {},
        "t17": {},
        "t2": {},
        "t23": None,
        "rated_items": 0,
        "growth_events": 0,
    }
    by_session: dict[int, list[Event]] = defaultdict(list)
    for e in clean:
        by_session[e["session"]].append(e)
    client_by_session: dict[int, list[FeatureRow]] = defaultdict(list)
    for f in client_features:
        client_by_session[f["session"]].append(f)

    for s in sorted(set(by_session) | set(client_by_session)):
        evs = by_session.get(s, [])
        by_task: dict[str, list[Event]] = defaultdict(list)
        for e in evs:
            by_task[e["task"]].append(e)
        for task, tevs in sorted(by_task.items()):
            if task == "T1":
                t1_features(c, s, tevs, thresholds)
            elif task == "T2":
                context["t2"][s] = t2_features(c, s, tevs)
            elif task == "T3":
                t3_features(c, s, tevs)
            elif task == "T4":
                speed_features(c, s, "T4", tevs, thresholds, context["flags"])
            elif task == "T5":
                t5_features(c, s, tevs)
            elif task == "T6":
                t6_features(c, s, tevs)
            elif task == "T8":
                t8_features(c, s, tevs)
            elif task == "T9":
                t9_features(c, s, tevs)
            elif task == "T10":
                t10_features(c, s, tevs, thresholds, context["flags"])
            elif task == "T12":
                t12_features(c, s, tevs)
            elif task == "T14":
                t14_features(c, s, tevs)
            elif task == "T15":
                t15_features(c, s, tevs)
            elif task == "T16":
                t16_features(c, s, tevs)
            elif task == "T17":
                r = t17_features(c, s, tevs)
                if r:
                    context["t17"][s] = r
            elif task == "T18":
                context["growth_events"] += t18_features(c, s, tevs)
            elif task == "T19":
                t19_features(c, s, tevs)
            elif task == "T20":
                context["growth_events"] += t20_features(c, s, tevs)
            elif task == "T21":
                t21_features(c, s, tevs)
            elif task == "T23":
                context["t23"] = t23_features(c, s, tevs) or context["t23"]
        for task in ("T11", "T22"):
            if by_task.get(task) or any(f["task"] == task for f in client_by_session.get(s, [])):
                text_task_features(c, s, task, by_task.get(task, []), client_by_session.get(s, []))
        t7_features(c, s, client_by_session.get(s, []))
        context["rated_items"] += confidence_features(c, s, evs)
        cross_task_features(c, s, [e for e in events if e["session"] == s], distraction_ids)

    # Long-term recall needs both halves of Delayed Recall.
    imm = next((v["acc"] for v in context["t2"].values() if v["phase"] == "immediate"), None)
    dly_s = next((s for s, v in context["t2"].items() if v["phase"] == "delayed"), None)
    if imm and dly_s is not None and context["t2"][dly_s]["acc"] is not None:
        c.add(dly_s, "t2.retention", min(1.2, context["t2"][dly_s]["acc"] / imm), task="T2")

    log_features(c, sessions, visits)
    return c.rows, context
