"""Persona simulator: plays all 7 sessions the way a device would and emits the same event and feature
payloads the apps send. Used by tests (does the engine find the planted pattern?) and the demo seed.

Personas are synthetic and deliberately exaggerated; they are test fixtures, not norms.
"""

import math
import random
import uuid
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from typing import Any

from app.content.prng import stream_sequence
from app.scoring.checks import check, route_cost
from app.scoring.staircase import Staircase
from app.services.bundle import ItemLookup, build_bundle


@dataclass
class Persona:
    name: str
    language: str = "en"
    ability: dict[str, float] = field(default_factory=dict)  # 0..1 per domain
    confidence_bias: float = 0.0  # negative = underconfident
    pressure_drop: float = 0.0
    english_penalty: float = 0.0
    carelessness: float = 0.03
    attention_decline: float = 0.03
    persistence: float = 0.5
    retry: float = 0.6
    challenge: float = 0.5
    avoid_after_error: bool = False
    speed: float = 0.5
    voice: bool = True
    wpm: float = 110
    read_errors: float = 0.03
    returns: int = 2
    study_days: float = 3.5
    on_schedule: float = 0.85

    def a(self, domain: str) -> float:
        return self.ability.get(domain, 0.6)


BASE = {
    d: 0.62
    for d in (
        "memory",
        "recall",
        "attention",
        "reasoning",
        "spatial",
        "reading",
        "vocab",
        "number",
        "transfer",
        "expression",
        "planning",
        "detection",
    )
}

PERSONAS: dict[str, Persona] = {
    "balanced": Persona("balanced", ability=dict(BASE)),
    "pressure_sensitive": Persona("pressure_sensitive", ability=dict(BASE), pressure_drop=0.4),
    "language_gap": Persona("language_gap", language="en", ability={**BASE, "reasoning": 0.7}, english_penalty=0.35),
    "underconfident": Persona(
        "underconfident",
        ability={**BASE, "reasoning": 0.75, "spatial": 0.75, "memory": 0.75, "number": 0.75},
        confidence_bias=-0.45,
    ),
    "strong_memory": Persona(
        "strong_memory", ability={**BASE, "memory": 0.95, "recall": 0.9, "number": 0.45, "planning": 0.4}
    ),
    "careless": Persona("careless", ability=dict(BASE), carelessness=0.25, speed=0.9),
}


def _logistic(x: float) -> float:
    return 1 / (1 + math.exp(-x))


def p_level(ability: float, level: int, slope: float = 1.1) -> float:
    """Chance of a correct answer at a staircase level for an ability (0..1 maps to level 1..10)."""
    return _logistic(slope * (ability * 10 + 0.5 - level))


class Player:
    def __init__(self, persona: Persona, band: str, lookup: ItemLookup, start: date, seed: int = 7) -> None:
        self.p = persona
        self.band = band
        self.lookup = lookup
        self.start = start
        self.rng = random.Random(f"{persona.name}:{band}:{seed}")
        self.seq = 0
        self.t2_item: str | None = None
        self.t2_group: str | None = None

    # ------------------------------------------------------------------ helpers
    def _rt(self, base_ms: float, spread: float = 0.25) -> int:
        speed_factor = 1.4 - 0.8 * self.p.speed
        return max(250, int(self.rng.gauss(base_ms * speed_factor, base_ms * spread)))

    def _conf(self, prob: float, correct: bool) -> int:
        est = prob + (0.15 if correct else -0.15) + self.p.confidence_bias + self.rng.gauss(0, 0.12)
        return max(1, min(4, int(round(1 + 3 * max(0.0, min(1.0, est))))))

    def _event(
        self,
        item: dict,
        task: str,
        answer: Any,
        correct: bool | None,
        rt: int | None,
        *,
        confidence: int | None = None,
        condition: str = "",
        extra: dict | None = None,
        skipped: bool = False,
        changes: list | None = None,
        first_click: int | None = None,
        idle: int = 0,
        switches: int = 0,
    ) -> dict:
        self.seq += 1
        return {
            "client_event_id": str(uuid.UUID(int=self.rng.getrandbits(128))),
            "item_id": item["id"],
            "task_id": task,
            "seq": self.seq,
            "shown_at_ms": self.seq * 1000,
            "response_ms": rt,
            "first_click_ms": first_click if first_click is not None else (int(rt * 0.45) if rt else None),
            "answer": answer,
            "client_correct": correct,
            "changes": len(changes or []),
            "change_log": changes or [],
            "skipped": skipped,
            "retries": 0,
            "confidence": confidence,
            "idle_ms": idle,
            "max_idle_ms": idle,
            "switches": switches,
            "language": item.get("language", "xx"),
            "condition": condition,
            "extra": extra or {},
        }

    def _wrong_option(self, item: dict, near_bias: float = 0.6) -> str:
        key = item["answer_key"].get("correct")
        options = [o["id"] for o in item["content"].get("options", []) if o["id"] != key]
        near = [o for o in item["answer_key"].get("near_miss", []) if o != key]
        if near and self.rng.random() < near_bias:
            return self.rng.choice(near)
        return self.rng.choice(options) if options else key

    def _lang_penalty(self, item: dict) -> float:
        return self.p.english_penalty if item.get("language") == "en" else 0.0

    def _choice(
        self,
        item: dict,
        task: str,
        prob: float,
        base_rt: float,
        condition: str = "",
        confidence: bool = True,
        extra: dict | None = None,
        careless_ok: bool = True,
    ) -> tuple[dict, bool]:
        prob = max(0.02, min(0.98, prob - self._lang_penalty(item)))
        correct = self.rng.random() < prob
        rt = self._rt(base_ms=base_rt)
        if correct and careless_ok and self.rng.random() < self.p.carelessness:
            correct, rt = False, int(rt * 0.35)
        answer = item["answer_key"].get("correct") if correct else self._wrong_option(item)
        changes = []
        if self.rng.random() < 0.08:
            other = self._wrong_option(item, 0.0)
            changes = [{"from": other, "to": answer, "at_ms": int(rt * 0.6)}]
        actual = check(item["content"], item["answer_key"], answer)
        ev = self._event(
            item,
            task,
            answer,
            actual,
            rt,
            condition=condition,
            extra=extra,
            changes=changes,
            confidence=self._conf(prob, bool(actual)) if confidence else None,
        )
        return ev, bool(actual)

    # ------------------------------------------------------------------ tasks
    def play_task(self, entry: dict, aux: dict, session: int, out: list, feats: list) -> None:
        tid = entry["task_id"]
        getattr(self, f"_t{tid[1:]}")(entry, aux, session, out, feats)

    def _staircase(
        self, pools: dict, start: int, n: int, prob_fn, task: str, out: list, base_rt: float, used: set
    ) -> None:
        sc = Staircase(level=start)
        for _ in range(n):
            pool = [i for i in pools.get(str(sc.level), pools.get(sc.level, [])) if i["id"] not in used]
            if not pool:
                pool = pools.get(str(sc.level), pools.get(sc.level, []))
            if not pool:
                break
            item = pool[0]
            used.add(item["id"])
            ev, ok = self._choice_or_kind(item, task, prob_fn(item), base_rt)
            out.append(ev)
            sc.record(ok)

    def _choice_or_kind(self, item: dict, task: str, prob: float, base_rt: float) -> tuple[dict, bool]:
        kind = item["content"]["kind"]
        if kind == "sequence":
            prob = max(0.02, min(0.98, prob))
            ok = self.rng.random() < prob
            seq = list(item["answer_key"]["sequence"])
            answer = list(seq)
            if not ok:
                if len(seq) > 1 and self.rng.random() < 0.5:
                    i = self.rng.randrange(len(seq) - 1)
                    answer[i], answer[i + 1] = answer[i + 1], answer[i]
                else:
                    choices = [c for c in item["content"]["choices"] if c != answer[-1]]
                    answer[-1] = self.rng.choice(choices)
            actual = check(item["content"], item["answer_key"], answer)
            rt = self._rt(1200 + 450 * len(seq))
            return self._event(item, task, answer, actual, rt, confidence=self._conf(prob, bool(actual))), bool(actual)
        if kind == "estimate":
            span = item["content"]["max"] - item["content"]["min"]
            err = abs(self.rng.gauss(0, 0.11 * (1.1 - self.p.a("number")))) * span
            value = item["answer_key"]["value"] + (err if self.rng.random() < 0.5 else -err)
            value = max(item["content"]["min"], min(item["content"]["max"], value))
            actual = check(item["content"], item["answer_key"], value)
            rt = self._rt(3500)
            return self._event(
                item, task, round(value, 1), actual, rt, confidence=self._conf(prob, bool(actual))
            ), bool(actual)
        return self._choice(item, task, prob, base_rt)

    def _t1(self, entry, aux, s, out, feats):
        used: set = set()
        for direction, penalty in (("forward", 0.0), ("backward", 0.12)):
            pools = entry["pools"][direction]
            self._staircase(
                pools,
                entry["start_level"],
                8,
                lambda it, pen=penalty: p_level(self.p.a("memory") - pen, it["level"]),
                "T1",
                out,
                3000,
                used,
            )

    def _t2(self, entry, aux, s, out, feats):
        item = entry["items"][0]
        phase = entry["settings"]["phase"]
        if phase == "immediate":
            self.t2_item, self.t2_group = item["id"], item["variant_group"]
            out.append(self._event(item, "T2", None, None, 40000, condition=phase, extra={"phase": "study"}))
            for ref in entry["settings"].get("distractor_ids", []):
                ev, _ = self._choice(aux[ref], "T2", 0.9, 1100, condition="t2_distractor", confidence=False)
                out.append(ev)
        recall = self.p.a("recall") if phase == "immediate" else self.p.a("recall") * 0.82
        for q in item["content"]["questions"]:
            expected = item["answer_key"]["answers"][q["id"]]
            if q["qtype"] == "recognition":
                lure = q["id"] in item["answer_key"].get("lures", [])
                prob = 0.92 - (0.35 * (1 - recall) if lure else 0.2 * (1 - recall))
            else:
                prob = 0.25 + 0.75 * recall
            prob -= self._lang_penalty(item)
            ok = self.rng.random() < prob
            answer = expected if ok else next(o["id"] for o in q["options"] if o["id"] != expected)
            actual = check(item["content"], item["answer_key"], answer, {"qid": q["id"]})
            out.append(
                self._event(
                    item,
                    "T2",
                    answer,
                    actual,
                    self._rt(4000),
                    condition=phase,
                    confidence=self._conf(prob, bool(actual)),
                    extra={"qid": q["id"], "qtype": q["qtype"]},
                )
            )

    def _t3(self, entry, aux, s, out, feats):
        for b, item in enumerate(entry["items"]):
            stim = stream_sequence(item["content"])
            hit_p = 0.55 + 0.42 * self.p.a("attention") - self.p.attention_decline * b
            fa_p = 0.02 + 0.12 * (1 - self.p.a("attention"))
            taps = []
            for st in stim:
                if (st["target"] and self.rng.random() < hit_p) or (not st["target"] and self.rng.random() < fa_p):
                    taps.append(
                        {"i": st["i"], "rt": max(200, int(self.rng.gauss(480, 60 + 120 * (1 - self.p.a("attention")))))}
                    )
            out.append(self._event(item, "T3", {"taps": taps}, None, 60000, extra={"block": b + 1}))

    def _t4(self, entry, aux, s, out, feats):
        for item in entry["items"]:
            ev, _ = self._choice(item, "T4", 0.94, 1100, confidence=False)
            out.append(ev)

    def _t5(self, entry, aux, s, out, feats):
        self._staircase(
            entry["pools"],
            entry["start_level"],
            entry["items_per_run"],
            lambda it: p_level(self.p.a("reasoning"), it["level"]),
            "T5",
            out,
            14000,
            set(),
        )

    def _t6(self, entry, aux, s, out, feats):
        self._staircase(
            entry["pools"],
            entry["start_level"],
            entry["items_per_run"],
            lambda it: p_level(self.p.a("spatial"), it["level"]),
            "T6",
            out,
            9000,
            set(),
        )

    def _t7(self, entry, aux, s, out, feats):
        item = entry["items"][0]
        words = item["content"]["word_count"]
        wpm = self.p.wpm * (1 - self._lang_penalty(item) * 0.6)
        out.append(
            self._event(
                item, "T7", None, None, int(words / wpm * 60000), extra={"mode": "voice" if self.p.voice else "typed"}
            )
        )
        if self.p.voice:
            err = self.p.read_errors + self._lang_penalty(item) * 0.2
            for name, value in (
                ("wpm", wpm),
                ("error_rate", err),
                ("pause_rate", 6 + 30 * err),
                ("self_corrections", 1.0 + self.p.a("detection")),
                ("speech_start_ms", 900),
            ):
                feats.append(
                    {
                        "name": f"t7.{name}",
                        "value": round(value, 3),
                        "channel": "voice",
                        "task_id": "T7",
                        "item_id": item["id"],
                    }
                )

    def _t8(self, entry, aux, s, out, feats):
        reading = self.p.a("reading")
        for item in entry["items"]:
            words = item["content"]["passage"]["word_count"]
            out.append(
                self._event(item, "T8", None, None, int(words / (self.p.wpm * 1.4) * 60000), extra={"phase": "study"})
            )
            for q in item["content"]["questions"]:
                prob = 0.3 + 0.65 * reading - (0.1 if q["qtype"] == "inference" else 0) - self._lang_penalty(item)
                expected = item["answer_key"]["answers"][q["id"]]
                ok = self.rng.random() < prob
                answer = expected if ok else next(o["id"] for o in q["options"] if o["id"] != expected)
                rereads = self.rng.choice([0, 0, 1]) + (2 if self._lang_penalty(item) else 0)
                actual = check(item["content"], item["answer_key"], answer, {"qid": q["id"]})
                out.append(
                    self._event(
                        item,
                        "T8",
                        answer,
                        actual,
                        self._rt(9000),
                        confidence=self._conf(prob, bool(actual)),
                        extra={"qid": q["id"], "qtype": q["qtype"], "rereads": rereads},
                    )
                )

    def _t9(self, entry, aux, s, out, feats):
        for item in entry["items"]:
            ev, _ = self._choice(item, "T9", p_level(self.p.a("vocab"), item["level"], 0.8), 7000)
            out.append(ev)

    def _t10(self, entry, aux, s, out, feats):
        for item in entry["items"]:
            ev, _ = self._choice_or_kind(item, "T10", p_level(self.p.a("number") + 0.15, item["level"]), 2600)
            out.append(ev)

    def _text_item(self, item: dict, task: str, out: list, feats: list, quality: float, skip_p: float = 0.0) -> None:
        if self.rng.random() < skip_p:
            out.append(self._event(item, task, None, None, 3000, skipped=True, extra={"mode": "skipped"}))
            return
        mode = "voice" if self.p.voice else "typed"
        out.append(self._event(item, task, None, None, 55000, extra={"mode": mode}))
        words = 10 + 45 * quality + self.rng.gauss(0, 5)
        values = {
            "word_count": max(3, round(words)),
            "unique_ratio": 0.4 + 0.35 * quality,
            "connectors": round(4 * quality),
            "avg_sentence_words": 8 + 6 * quality,
            "filler_rate": 0.1 * (1 - quality),
        }
        if task == "T11":
            values["keyword_share"] = 0.15 + 0.5 * quality
        if mode == "voice":
            values["pause_rate"] = 18 - 12 * quality
            values["speech_start_ms"] = 3500 - 2500 * quality
        channel = "voice" if mode == "voice" else "text"
        for name, value in values.items():
            feats.append(
                {
                    "name": f"{task.lower()}.{name}",
                    "value": round(value, 3),
                    "channel": channel,
                    "task_id": task,
                    "item_id": item["id"],
                }
            )

    def _t11(self, entry, aux, s, out, feats):
        for item in entry["items"]:
            self._text_item(item, "T11", out, feats, self.p.a("expression") - self._lang_penalty(item) * 0.5)

    def _t12(self, entry, aux, s, out, feats):
        item = entry["items"][0]
        out.append(self._event(item, "T12", None, None, 120000, extra={"phase": "study"}))
        transfer = self.p.a("transfer")
        for qset in ("A", "B"):
            if qset == "B":
                out.append(self._event(item, "T12", None, None, 30000, extra={"phase": "recap"}))
            for q in [q for q in item["content"]["questions"] if q["set"] == qset]:
                base = {
                    "recall": 0.35 + 0.6 * self.p.a("recall"),
                    "near": 0.3 + 0.6 * transfer,
                    "far": 0.2 + 0.65 * transfer,
                }[q["qtype"]] + (0.05 if qset == "B" else 0)
                prob = base - self._lang_penalty(item)
                expected = item["answer_key"]["answers"][q["id"]]
                ok = self.rng.random() < prob
                answer = expected if ok else next(o["id"] for o in q["options"] if o["id"] != expected)
                actual = check(item["content"], item["answer_key"], answer, {"qid": q["id"]})
                out.append(
                    self._event(
                        item,
                        "T12",
                        answer,
                        actual,
                        self._rt(8000),
                        confidence=self._conf(prob, bool(actual)),
                        extra={"qid": q["id"], "qtype": q["qtype"], "set": qset},
                    )
                )

    def _t14(self, entry, aux, s, out, feats):
        plan = self.p.a("planning")
        for item in entry["items"]:
            places = [p["id"] for p in item["content"]["places"]]
            if self.rng.random() < 0.3 + 0.65 * plan:
                order = list(item["answer_key"]["best_order"])
            else:
                order = list(places)
                self.rng.shuffle(order)
            rt = self._rt(20000)
            plan_ms = int(rt * (0.08 + 0.4 * plan))
            restarts = 0 if self.rng.random() < plan else self.rng.choice([1, 2, 3])
            actual = check(item["content"], item["answer_key"], order)
            cost = route_cost(item["content"]["start"], item["content"]["places"], order)
            out.append(
                self._event(
                    item,
                    "T14",
                    order,
                    actual,
                    rt,
                    first_click=plan_ms,
                    confidence=self._conf(0.3 + 0.6 * plan, bool(actual)),
                    extra={"plan_ms": plan_ms, "restarts": restarts, "cost": cost},
                )
            )

    def _t15(self, entry, aux, s, out, feats):
        first = []
        for item in entry["items"]:
            ev, ok = self._choice(item, "T15", 0.3 + 0.65 * self.p.a("detection") - self._lang_penalty(item), 15000)
            out.append(ev)
            first.append((item, ev, ok))
        for item, ev, _ok in first:
            if self.rng.random() < 0.2:
                new = (
                    item["answer_key"]["correct"]
                    if self.rng.random() < self.p.a("detection")
                    else self._wrong_option(item, 0)
                )
                if new != ev["answer"]:
                    actual = check(item["content"], item["answer_key"], new)
                    out.append(
                        self._event(
                            item,
                            "T15",
                            new,
                            actual,
                            4000,
                            condition="review",
                            changes=[{"from": ev["answer"], "to": new, "at_ms": 2000}],
                        )
                    )

    def _t16(self, entry, aux, s, out, feats):
        item = entry["items"][0]
        blocks = item["content"]["blocks"]
        total = item["content"]["total_s"]
        plan_skill = self.p.a("planning")
        weights = {"easy": 1, "medium": 1.5, "hard": 2.2}
        planned_raw = {b["id"]: weights[b["difficulty"]] * (0.5 + plan_skill) + self.rng.random() for b in blocks}
        scale = total / sum(planned_raw.values())
        planned = {k: round(v * scale) for k, v in planned_raw.items()}
        actual, unfinished, used_s = {}, 0, 0.0
        for b in blocks:
            budget = planned[b["id"]] * (1.0 + self.rng.gauss(0, 0.35 * (1 - plan_skill)))
            spent = 0.0
            for ref in b["item_ids"]:
                sub = aux[ref]
                cost = 8 if b["difficulty"] == "easy" else 14 if b["difficulty"] == "medium" else 25
                if spent + cost > budget or used_s + spent + cost > total:
                    unfinished += 1
                    continue
                spent += cost
                ev, _ = self._choice_or_kind(sub, "T16", 0.75, cost * 1000)
                ev["condition"] = f"t16:{b['id']}"
                out.append(ev)
            actual[b["id"]] = round(spent)
            used_s += spent
        out.append(
            self._event(
                item,
                "T16",
                None,
                None,
                int(used_s * 1000),
                extra={
                    "planned": planned,
                    "actual": actual,
                    "unfinished": unfinished,
                    "unused_s": round(max(0.0, total - used_s)),
                },
            )
        )

    def _t17(self, entry, aux, s, out, feats):
        base = 0.85
        for item in entry["items"]:
            pressure = item["content"]["condition"] == "pressure"
            prob = base - (self.p.pressure_drop if pressure else 0) + self.rng.gauss(0, 0.03)
            timeout = pressure and self.rng.random() < self.p.pressure_drop * 0.3
            if timeout:
                out.append(
                    self._event(
                        item,
                        "T17",
                        None,
                        False,
                        entry["settings"]["pressure_seconds"] * 1000,
                        skipped=True,
                        extra={"timeout": True},
                    )
                )
                continue
            ev, _ = self._choice(item, "T17", prob, 3000 if pressure else 4500, careless_ok=False)
            if pressure and self.p.pressure_drop > 0.2 and self.rng.random() < 0.4:
                key = item["answer_key"]["correct"]
                if ev["answer"] != key:
                    ev["change_log"] = [{"from": key, "to": ev["answer"], "at_ms": 1500}]
                    ev["changes"] = 1
                    ev["max_idle_ms"] = ev["idle_ms"] = 3500
            out.append(ev)

    def _t18(self, entry, aux, s, out, feats):
        last_wrong = False
        for item in entry["items"]:
            c = item["content"]
            if c["kind"] == "bonus_offer":
                accept = self.rng.random() < self.p.challenge
                out.append(self._event(item, "T18", "accept" if accept else "decline", None, 2500))
                if accept:
                    for ref in c["refs"]:
                        ev, _ = self._choice(aux[ref], "T18", 0.9, 2500, condition="bonus")
                        out.append(ev)
                continue
            p_hard = self.p.challenge * (0.15 if (last_wrong and self.p.avoid_after_error) else 1.0)
            pick = "hard" if self.rng.random() < p_hard else "easy"
            out.append(self._event(item, "T18", pick, None, 2000))
            target = aux[c["hard_ref"] if pick == "hard" else c["easy_ref"]]
            prob = 0.45 + 0.3 * self.p.a("reasoning") if pick == "hard" else 0.92
            ev, ok = self._choice(target, "T18", prob, 6000 if pick == "hard" else 2500, condition=f"t18_{pick}")
            out.append(ev)
            last_wrong = not ok

    def _t19(self, entry, aux, s, out, feats):
        for item in entry["items"]:
            seconds = max(4.0, min(90.0, self.rng.gauss(10 + 70 * self.p.persistence, 8)))
            attempts = max(1, int(round(1 + 3.5 * self.p.persistence + self.rng.gauss(0, 0.6))))
            solved = self.rng.random() < 0.15 + 0.2 * self.p.persistence
            answer = item["answer_key"]["correct"] if solved else self._wrong_option(item)
            out.append(
                self._event(
                    item,
                    "T19",
                    answer,
                    check(item["content"], item["answer_key"], answer),
                    int(seconds * 1000),
                    confidence=self._conf(0.2, solved),
                    extra={"attempts": attempts, "gave_up": not solved},
                )
            )

    def _t20(self, entry, aux, s, out, feats):
        variants = entry["settings"]["feedback_variants"]
        k = 0
        for item in entry["items"]:
            ev, ok = self._choice(item, "T20", 0.62, 6000)
            if not ok:
                variant = variants[k % len(variants)]
                k += 1
                retried = self.rng.random() < self.p.retry
                ev["extra"] = {
                    "retry_offered": True,
                    "feedback_variant": variant,
                    "retried": retried,
                    "retry_correct": retried and self.rng.random() < 0.55,
                }
                ev["retries"] = 1 if retried else 0
            out.append(ev)

    def _t21(self, entry, aux, s, out, feats):
        for item in entry["items"]:
            options = item["content"]["options"]
            target = {
                "study_days": self.p.study_days,
                "self_start": self.p.study_days * 0.7,
                "plan_days": self.p.study_days * 0.6,
                "review_days": self.p.study_days * 0.5,
                "stuck": 2,
                "focus_span": 15,
            }.get(item["content"]["qid"], 2)
            best = min(options, key=lambda o: abs(o["value"] - target))
            out.append(self._event(item, "T21", best["id"], None, self._rt(5000)))

    def _t22(self, entry, aux, s, out, feats):
        for item in entry["items"]:
            self._text_item(item, "T22", out, feats, self.p.a("expression"), skip_p=0.1)

    def _t23(self, entry, aux, s, out, feats):
        for item in entry["items"]:
            ev, _ = self._choice(item, "T23", p_level(self.p.a("reasoning"), item["level"]), 12000)
            out.append(ev)

    # ------------------------------------------------------------------ sessions
    def play_bundle(self, bundle: dict) -> tuple[list[dict], list[dict]]:
        """Play a session bundle (as built locally or downloaded from the API)."""
        events: list[dict] = []
        feats: list[dict] = []
        for entry in bundle["tasks"]:
            self.play_task(entry, bundle["aux_items"], bundle["session_number"], events, feats)
        return events, feats

    def play_session(self, number: int, seed: int) -> dict:
        context = {"t2_item": self.t2_item, "t2_group": self.t2_group}
        bundle = build_bundle(number, self.band, self.p.language, seed, self.lookup, context)
        events, feats = self.play_bundle(bundle)
        scheduled = self.start + timedelta(days=2 * (number - 1))
        on_time = self.rng.random() < self.p.on_schedule
        done_day = scheduled if on_time else scheduled + timedelta(days=1)
        return {
            "number": number,
            "bundle": bundle,
            "events": events,
            "features": feats,
            "scheduled_for": scheduled,
            "completed_on": done_day,
        }

    def play_cycle(self, seeds: list[int] | None = None) -> dict:
        seeds = seeds or [1000 + n for n in range(1, 8)]
        sessions = [self.play_session(n, seeds[n - 1]) for n in range(1, 8)]
        visits = []
        for k in range(self.p.returns):
            day = self.start + timedelta(days=1 + 2 * k)
            visits.append(datetime.combine(day, datetime.min.time(), tzinfo=UTC) + timedelta(hours=18))
        return {"sessions": sessions, "visits": visits}


def engine_inputs(played: dict, band: str, items_by_id: dict[str, dict], text_language: str = "en") -> dict:
    """Convert a simulated cycle straight into scoring-engine inputs (no database)."""
    events, feats, sessions = [], [], []
    next_id = 1
    for s in played["sessions"]:
        for ev in s["events"]:
            item = items_by_id[ev["item_id"]]
            events.append(
                {
                    "id": next_id,
                    "session": s["number"],
                    "task": ev["task_id"],
                    "item_id": ev["item_id"],
                    "seq": ev["seq"],
                    "response_ms": ev["response_ms"],
                    "first_click_ms": ev["first_click_ms"],
                    "answer": ev["answer"],
                    "correct": check(item["content"], item["answer_key"], ev["answer"], ev["extra"], ev["skipped"]),
                    "changes": ev["changes"],
                    "change_log": ev["change_log"],
                    "skipped": ev["skipped"],
                    "retries": ev["retries"],
                    "confidence": ev["confidence"],
                    "idle_ms": ev["idle_ms"],
                    "max_idle_ms": ev["max_idle_ms"],
                    "switches": ev["switches"],
                    "level": item["level"],
                    "language": ev["language"],
                    "condition": ev["condition"],
                    "extra": ev["extra"],
                    "content": item["content"],
                    "key": item["answer_key"],
                    "tags": item["tags"],
                    "variant_group": item["variant_group"],
                    "kind": item["content"]["kind"],
                }
            )
            next_id += 1
        for f in s["features"]:
            feats.append(
                {
                    "session": s["number"],
                    "name": f["name"],
                    "value": f["value"],
                    "channel": f["channel"],
                    "task": f["task_id"],
                    "item_id": f["item_id"],
                }
            )
        sessions.append(
            {
                "number": s["number"],
                "scheduled_for": s["scheduled_for"],
                "started_at": datetime.combine(s["completed_on"], datetime.min.time(), tzinfo=UTC),
                "completed_at": datetime.combine(s["completed_on"], datetime.min.time(), tzinfo=UTC)
                + timedelta(minutes=25),
            }
        )
    return {
        "age_band": band,
        "events": events,
        "client_features": feats,
        "sessions": sessions,
        "visits": played["visits"],
        "text_language": text_language,
    }
