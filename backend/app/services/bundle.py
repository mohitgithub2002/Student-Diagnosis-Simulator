"""Session bundles: everything a device needs to run one session offline (preloaded at session start).

Item selection is deterministic from the session seed. Pure functions over an item lookup so the API and
the persona simulator build identical sessions.
"""

import random
from collections import defaultdict
from collections.abc import Callable
from typing import Any

from app.content.tasks import LANGUAGE_DEPENDENT, SESSION_PLAN, TASKS_BY_ID

ItemLookup = Callable[[str, str, str], list[dict]]  # (task_id, band, language) -> active items


def public_item(item: dict) -> dict:
    return {
        k: item[k] for k in ("id", "task_id", "level", "language", "content", "answer_key", "tags", "variant_group")
    }


def _pools(items: list[dict]) -> dict[int, list[dict]]:
    pools: dict[int, list[dict]] = defaultdict(list)
    for it in items:
        pools[it["level"]].append(public_item(it))
    return {lvl: sorted(v, key=lambda x: x["id"]) for lvl, v in sorted(pools.items())}


def _pick(rng: random.Random, items: list[dict], n: int) -> list[dict]:
    items = sorted(items, key=lambda x: x["id"])
    rng.shuffle(items)
    return [public_item(i) for i in items[:n]]


def task_language(task_id: str, student_lang: str) -> str:
    return student_lang if task_id in LANGUAGE_DEPENDENT else "xx"


def build_task(
    task_id: str, variant: str, band: str, student_lang: str, seed: int, lookup: ItemLookup, context: dict[str, Any]
) -> tuple[dict, dict[str, dict]]:
    tdef = TASKS_BY_ID[task_id]
    rng = random.Random(f"{seed}:{task_id}:{variant}")
    lang = task_language(task_id, student_lang)
    items = lookup(task_id, band, lang)
    aux: dict[str, dict] = {}
    entry: dict[str, Any] = {
        "task_id": task_id,
        "variant": variant,
        "name": tdef["name"],
        "title": tdef["title"].get(student_lang, tdef["title"]["en"]),
        "instructions": tdef["instructions"].get(student_lang, tdef["instructions"]["en"]),
        "instructions_all": tdef["instructions"],
        "primitive": tdef["primitive"],
        "minutes": tdef["minutes"],
        "adaptive": tdef.get("adaptive", False),
        "confidence": tdef.get("confidence", False),
        "language": lang,
        "settings": {},
        "items": [],
    }
    session_number = context.get("session_number", 0)

    if task_id == "T1":
        entry["start_level"] = tdef["start_level"][band]
        entry["items_per_run"] = {"forward": 8, "backward": 8}
        entry["pools"] = {
            d: _pools([i for i in items if i["content"]["direction"] == d]) for d in ("forward", "backward")
        }
        # Different sessions draw from different halves of each level so the retest is not a repeat.
        half = 0 if session_number < 7 else 1
        for d in entry["pools"]:
            entry["pools"][d] = {
                lvl: [x for k, x in enumerate(v) if k % 2 == half] or v for lvl, v in entry["pools"][d].items()
            }
    elif tdef.get("adaptive"):
        entry["start_level"] = tdef["start_level"][band]
        entry["items_per_run"] = tdef.get("items_per_run", 14)
        entry["pools"] = _pools(items)
    elif task_id == "T2":
        phase = variant or "immediate"
        chosen = []
        if phase == "delayed":
            chosen = [i for i in items if i["id"] == context.get("t2_item")]
            if not chosen and context.get("t2_group"):  # language changed since session 4: same card, new language
                chosen = [i for i in items if i["variant_group"] == context["t2_group"]]
            if not chosen:  # session 4 was missed, so there is nothing to recall: run a fresh card instead
                phase = "immediate"
        entry["items"] = [public_item(i) for i in chosen[:1]] or _pick(rng, items, 1)
        entry["settings"] = {"phase": phase, "distractor_s": 60 if phase == "immediate" else 0}
        if phase == "immediate":
            distractors = _pick(rng, lookup("T4", band, "xx"), 8)
            entry["settings"]["distractor_ids"] = [d["id"] for d in distractors]
            aux.update({d["id"]: d for d in distractors})
    elif task_id == "T3":
        ordered = sorted(items, key=lambda x: x["id"])
        block = ordered[:4] if session_number < 7 else ordered[4:8]
        entry["items"] = [public_item(i) for i in block]
    elif task_id == "T4":
        entry["items"] = _pick(rng, items, tdef["items_per_run"])
    elif task_id in ("T7", "T12"):
        entry["items"] = _pick(rng, items, 1)
    elif task_id == "T8":
        entry["items"] = [public_item(i) for i in sorted(items, key=lambda x: x["id"])[:2]]
    elif task_id == "T9":
        entry["items"] = [public_item(i) for i in sorted(items, key=lambda x: (x["level"], x["id"]))[:10]]
    elif task_id == "T10":
        # Fixed mixed set across the band's range so accuracy (and speed on correct items) is comparable.
        levels = range(2, 8) if band == "11-14" else range(3, 9)
        chosen: list[dict] = []
        for lvl in levels:
            by_kind: dict[str, list[dict]] = defaultdict(list)  # dots, baskets, number line
            for i in items:
                if i["level"] == lvl:
                    by_kind[i["content"]["prompt_key"]].append(i)
            for kind in sorted(by_kind):
                chosen += _pick(rng, by_kind[kind], 1)
        entry["items"] = chosen[: tdef["items_per_run"]]
    elif task_id == "T11":
        entry["items"] = _pick(rng, items, 2)
    elif task_id == "T14":
        levels = [2, 3, 4, 5, 6] if band == "11-14" else [3, 4, 5, 6, 7]
        for lvl in levels:
            pool = [i for i in items if i["level"] == lvl]
            entry["items"] += _pick(rng, pool, 1)
    elif task_id == "T15":
        entry["items"] = [public_item(i) for i in sorted(items, key=lambda x: (x["level"], x["id"]))]
        entry["settings"] = {"review": True}
    elif task_id == "T16":
        chosen = _pick(rng, items, 1)
        entry["items"] = chosen
        for block in chosen[0]["content"]["blocks"] if chosen else []:
            for ref in block["item_ids"]:
                src_task = ref.split("-")[0]
                found = next((i for i in lookup(src_task, band, "xx") if i["id"] == ref), None)
                if found:
                    aux[ref] = public_item(found)
    elif task_id == "T17":
        wanted_set = "A" if session_number < 7 else "B"
        pairs: dict[int, dict[str, dict]] = defaultdict(dict)
        for i in items:
            if i["content"].get("set") == wanted_set:
                pairs[i["content"]["pair"]][i["content"]["condition"]] = i
        order = sorted(pairs)
        rng.shuffle(order)
        relaxed = [public_item(pairs[p]["relaxed"]) for p in order if "relaxed" in pairs[p]]
        rng.shuffle(order)
        pressure = [public_item(pairs[p]["pressure"]) for p in order if "pressure" in pairs[p]]
        entry["items"] = relaxed + pressure
        entry["settings"] = {"pressure_seconds": 10 if band == "15-18" else 12}
    elif task_id == "T18":
        menus = sorted([i for i in items if i["content"]["kind"] == "choice_menu"], key=lambda x: x["id"])
        bonus = [i for i in items if i["content"]["kind"] == "bonus_offer"]
        entry["items"] = [public_item(i) for i in menus[: tdef["items_per_run"]]] + [public_item(i) for i in bonus[:1]]
        by_id = {i["id"]: i for i in items}
        for it in entry["items"]:
            refs = [it["content"].get("easy_ref"), it["content"].get("hard_ref"), *it["content"].get("refs", [])]
            for ref in refs:
                if ref and ref in by_id:
                    aux[ref] = public_item(by_id[ref])
    elif task_id == "T19":
        entry["items"] = _pick(rng, items, tdef["items_per_run"])
        entry["settings"] = {"max_seconds": 90}
    elif task_id == "T20":
        entry["items"] = _pick(rng, items, tdef["items_per_run"])
        entry["settings"] = {"feedback_variants": ["effort", "ability", "neutral"]}
    elif task_id == "T21":
        entry["items"] = [public_item(i) for i in sorted(items, key=lambda x: x["id"])]
    elif task_id == "T22":
        entry["items"] = [public_item(i) for i in sorted(items, key=lambda x: x["id"])]
    elif task_id == "T23":
        native = student_lang if student_lang in ("hi", "hinglish") else "hi"
        en_items = {i["variant_group"]: i for i in lookup("T23", band, "en")}
        nat_items = {i["variant_group"]: i for i in lookup("T23", band, native)}
        groups = sorted(set(en_items) & set(nat_items))
        rng.shuffle(groups)
        groups = groups[:6]
        first = [en_items[g] if k % 2 == 0 else nat_items[g] for k, g in enumerate(groups)]
        second = [nat_items[g] if k % 2 == 0 else en_items[g] for k, g in enumerate(groups)]
        entry["items"] = [public_item(i) for i in first + second]
        entry["settings"] = {"probe_language": native}
        entry["language"] = "mixed"
    return entry, aux


def build_bundle(
    session_number: int,
    band: str,
    student_lang: str,
    seed: int,
    lookup: ItemLookup,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    context = {**(context or {}), "session_number": session_number}
    plan = SESSION_PLAN[session_number]
    tasks, aux = [], {}
    for task_id, variant in plan["tasks"]:
        entry, extra = build_task(task_id, variant, band, student_lang, seed, lookup, context)
        tasks.append(entry)
        aux.update(extra)
    return {
        "session_number": session_number,
        "focus": plan["focus"],
        "age_band": band,
        "language": student_lang,
        "seed": seed,
        "confidence_scale": 4,
        "tasks": tasks,
        "aux_items": aux,
    }
