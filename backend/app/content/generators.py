"""Deterministic item generators for the procedural tasks.

Everything is seeded from the item id, so reseeding produces the same item bank. Language-neutral items
use language "xx" and carry `prompt_key`s that the apps translate.
"""

import itertools
import random
from typing import Any

from app.content.authored.logic_props import OPTIONS as LOGIC_OPTIONS
from app.content.authored.logic_props import PROPS, phrase

BANDS = ("11-14", "15-18")
LANGS = ("en", "hi", "hinglish")


def band_code(band: str) -> str:
    return band.replace("-", "")


def make_id(task: str, band: str, level: int, lang: str, n: int, extra: str = "") -> str:
    return f"{task}-{band_code(band)}-L{level:02d}-{lang}{('-' + extra) if extra else ''}-{n:03d}"


def item(
    task: str,
    band: str,
    level: int,
    lang: str,
    n: int,
    content: dict[str, Any],
    answer_key: dict[str, Any] | None = None,
    tags: list[str] | None = None,
    variant_group: str = "",
    extra: str = "",
) -> dict[str, Any]:
    return {
        "id": make_id(task, band, level, lang, n, extra),
        "task_id": task,
        "age_band": band,
        "level": level,
        "language": lang,
        "content": content,
        "answer_key": answer_key or {},
        "tags": tags or [],
        "variant_group": variant_group,
    }


# --------------------------------------------------------------------------------------------- T1
SYMBOLS = ["star", "circle", "triangle", "square", "diamond", "cross", "heart", "moon"]
COLORS = ["red", "blue", "green", "yellow", "purple", "orange"]
DIGITS = [str(d) for d in range(10)]


def seq_length(level: int) -> int:
    return level + 2


def gen_t1(band: str, per_level: int = 6) -> list[dict]:
    out = []
    for direction in ("forward", "backward"):
        for level in range(1, 11):
            for n in range(1, per_level + 1):
                rng = random.Random(f"T1:{band}:{direction}:{level}:{n}")
                mode = ("digits", "symbols", "colors")[(n - 1) % 3]
                pool = {"digits": DIGITS, "symbols": SYMBOLS, "colors": COLORS}[mode]
                length = seq_length(level)
                seq: list[str] = []
                while len(seq) < length:
                    tok = rng.choice(pool)
                    if not seq or seq[-1] != tok:
                        seq.append(tok)
                key = list(reversed(seq)) if direction == "backward" else list(seq)
                out.append(
                    item(
                        "T1",
                        band,
                        level,
                        "xx",
                        n,
                        {
                            "kind": "sequence",
                            "mode": mode,
                            "direction": direction,
                            "sequence": seq,
                            "choices": pool,
                            "show_ms": 800,
                            "gap_ms": 250,
                            "prompt_key": f"t1.{direction}",
                        },
                        {"sequence": key},
                        tags=[direction, mode],
                        extra=direction[0],
                    )
                )
    return out


# --------------------------------------------------------------------------------------------- figures
FILLS = ["solid", "empty", "striped", "dotted"]


def figure(shape: str, rotation: int = 0, count: int = 1, fill: str = "solid", **extra: Any) -> dict:
    return {"shape": shape, "rotation": rotation % 360, "count": count, "fill": fill, **extra}


def _normalize(cells: list[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    mx = min(x for x, _ in cells)
    my = min(y for _, y in cells)
    return tuple(sorted((x - mx, y - my) for x, y in cells))


def _rotate(cells, times: int):
    out = list(cells)
    for _ in range(times % 4):
        out = [(y, -x) for x, y in out]
    return _normalize(out)


def _mirror(cells):
    return _normalize([(-x, y) for x, y in cells])


def _canonical(cells):
    return min(_rotate(cells, k) for k in range(4))


def polyomino(rng: random.Random, size: int) -> tuple[tuple[int, int], ...]:
    while True:
        cells = {(0, 0)}
        while len(cells) < size:
            x, y = rng.choice(sorted(cells))
            dx, dy = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
            cells.add((x + dx, y + dy))
        shape = _normalize(list(cells))
        # Reject shapes that look the same when mirrored: the mirror distractor would also be correct.
        if _canonical(shape) != _canonical(_mirror(shape)):
            return shape


def poly_figure(cells, fill: str = "solid") -> dict:
    return {"shape": "poly", "cells": [list(c) for c in cells], "rotation": 0, "count": 1, "fill": fill}


def _options(rng: random.Random, correct: dict, distractors: list[tuple[dict, str]]) -> tuple[list, dict]:
    opts = [("c", correct, "correct")] + [(f"d{i}", d, kind) for i, (d, kind) in enumerate(distractors)]
    rng.shuffle(opts)
    letters = "abcdef"
    options, key, near = [], {}, []
    for idx, (_, fig, kind) in enumerate(opts):
        oid = letters[idx]
        options.append({"id": oid, "figure": fig})
        if kind == "correct":
            key["correct"] = oid
        elif kind == "near":
            near.append(oid)
    key["near_miss"] = near
    return options, key


def rotation_item(rng: random.Random, level: int, n_options: int = 4) -> tuple[dict, dict]:
    size = 4 + (level - 1) // 3  # 4..7 cells (every tromino is mirror-symmetric)
    shape = polyomino(rng, size)
    turn = rng.choice([1, 2, 3])
    correct = poly_figure(_rotate(shape, turn))
    mirrors = [poly_figure(_rotate(_mirror(shape), k)) for k in rng.sample([0, 1, 2, 3], 2 if n_options <= 4 else 3)]
    other = shape
    while _canonical(other) in (_canonical(shape), _canonical(_mirror(shape))):
        other = polyomino(rng, size)
    distractors = [(m, "near") for m in mirrors] + [(poly_figure(_rotate(other, rng.randrange(4))), "far")]
    if n_options > 4:
        other2 = polyomino(rng, size)
        distractors.append((poly_figure(other2), "far"))
    options, key = _options(rng, correct, distractors)
    content = {
        "kind": "choice",
        "layout": "grid",
        "prompt_key": "t6.same_turned",
        "stem": {"figures": [poly_figure(shape)]},
        "options": options,
        "concept": "rotation",
    }
    return content, key


ARROWLIKE = ["arrow", "triangle", "flag"]


def sequence_item(rng: random.Random, level: int) -> tuple[dict, dict]:
    shape = rng.choice(ARROWLIKE)
    step_rot = 90 if level <= 3 else rng.choice([45, 90, 135])
    use_count = level >= 4
    use_fill = level >= 7
    length = 3 if level <= 6 else 4
    start_rot = rng.choice([0, 90, 180, 270])
    start_count = rng.choice([1, 2]) if use_count else 1
    fill_cycle = rng.sample(FILLS[:3], 3) if use_fill else ["solid"]
    count_step = 1 if use_count else 0

    def fig_at(i: int) -> dict:
        count = start_count + count_step * i
        if count > 4:  # wrap counts so figures stay drawable
            count = (count - 1) % 4 + 1
        return figure(shape, start_rot + step_rot * i, count, fill_cycle[i % len(fill_cycle)])

    stem = [fig_at(i) for i in range(length)]
    answer = fig_at(length)
    near = [
        {**answer, "rotation": (answer["rotation"] + step_rot) % 360},
        {**answer, "rotation": (answer["rotation"] - step_rot) % 360},
    ]
    if use_count:
        near.append({**answer, "count": answer["count"] % 4 + 1})
    if use_fill:
        near.append({**answer, "fill": fill_cycle[(length + 1) % len(fill_cycle)]})
    rng.shuffle(near)
    distractors = [(d, "near") for d in near[:2]]
    far = figure(
        rng.choice([s for s in ARROWLIKE if s != shape]),
        rng.choice([0, 90, 180, 270]),
        rng.randint(1, 3),
        rng.choice(FILLS[:3]),
    )
    distractors.append((far, "far"))
    options, key = _options(rng, answer, distractors)
    content = {
        "kind": "choice",
        "layout": "grid",
        "prompt_key": "t6.what_next",
        "stem": {"figures": stem, "blank": True},
        "options": options,
        "concept": "sequence",
    }
    return content, key


def gen_t6(band: str, per_level: int = 6) -> list[dict]:
    out = []
    for level in range(1, 11):
        for n in range(1, per_level + 1):
            rng = random.Random(f"T6:{band}:{level}:{n}")
            content, key = (rotation_item if n % 2 else sequence_item)(rng, level)
            out.append(item("T6", band, level, "xx", n, content, key, tags=[content["concept"]]))
    return out


# --------------------------------------------------------------------------------------------- T4
LETTERS = "BCDFGHJKLMNPRSTVWXZ"


def gen_t4(band: str, count: int = 40) -> list[dict]:
    out = []
    for n in range(1, count + 1):
        rng = random.Random(f"T4:{band}:{n}")
        same = n % 2 == 0
        if n % 3 == 0:
            length = 4 if band == "11-14" else 5
            left = "".join(rng.sample(LETTERS, length))
            right = left
            if not same:
                i = rng.randrange(length - 1)
                chars = list(left)
                chars[i], chars[i + 1] = chars[i + 1], chars[i]
                right = "".join(chars)
            pair = {"left": {"text": left}, "right": {"text": right}}
            tags = ["letters"]
        else:
            fig = figure(
                rng.choice(["arrow", "triangle", "flag", "star"]),
                rng.choice([0, 90, 180, 270]),
                rng.randint(1, 3),
                rng.choice(FILLS),
            )
            other = dict(fig)
            if not same:
                change = rng.choice(["rotation", "count", "fill"])
                if change == "rotation":
                    other["rotation"] = (fig["rotation"] + 90) % 360
                elif change == "count":
                    other["count"] = fig["count"] % 3 + 1
                else:
                    other["fill"] = rng.choice([f for f in FILLS if f != fig["fill"]])
            pair = {"left": {"figure": fig}, "right": {"figure": other}}
            tags = ["shapes"]
        out.append(
            item(
                "T4",
                band,
                5,
                "xx",
                n,
                {
                    "kind": "choice",
                    "layout": "pair",
                    "prompt_key": "t4.same_or_different",
                    "stem": pair,
                    "options": [{"id": "same", "label_key": "same"}, {"id": "different", "label_key": "different"}],
                },
                {"correct": "same" if same else "different"},
                tags=tags,
            )
        )
    return out


# --------------------------------------------------------------------------------------------- T10
def dots_compare(rng: random.Random, level: int) -> tuple[dict, dict]:
    ratio = 2.0 - (level - 1) * 0.1  # 2.0 .. 1.1
    small = rng.randint(8, 18 + level * 2)
    big = max(small + 1, round(small * ratio))
    left_big = rng.random() < 0.5
    left, right = (big, small) if left_big else (small, big)
    content = {
        "kind": "choice",
        "layout": "pair",
        "prompt_key": "t10.more_dots",
        "stem": {
            "left": {"dots": left, "seed": rng.randrange(1, 10**6)},
            "right": {"dots": right, "seed": rng.randrange(1, 10**6)},
        },
        "options": [{"id": "left", "label_key": "left"}, {"id": "right", "label_key": "right"}],
        "concept": "compare",
        "show_ms": 1500,
    }
    return content, {"correct": "left" if left_big else "right"}


def basket_compare(rng: random.Random, level: int) -> tuple[dict, dict]:
    k = 2 if level <= 3 else (3 if level <= 7 else 4)
    while True:
        a = [rng.randint(5, 99) for _ in range(k)]
        b = [rng.randint(5, 99) for _ in range(k)]
        diff = abs(sum(a) - sum(b)) / max(sum(a), sum(b))
        target = 0.3 - level * 0.025  # closer totals at higher levels
        if target * 0.6 <= diff <= target * 1.4 or (level >= 9 and 0.02 <= diff <= 0.08):
            break
    content = {
        "kind": "choice",
        "layout": "pair",
        "prompt_key": "t10.basket_more",
        "stem": {"left": {"prices": a}, "right": {"prices": b}},
        "options": [{"id": "left", "label_key": "left"}, {"id": "right", "label_key": "right"}],
        "concept": "compare",
    }
    return content, {"correct": "left" if sum(a) > sum(b) else "right"}


def number_line(rng: random.Random, level: int) -> tuple[dict, dict]:
    hi = 100 if level <= 3 else (1000 if level <= 7 else 10000)
    step = {100: 1, 1000: 10, 10000: 100}[hi]
    grain = 10 if level in (1, 4, 8) else 1
    value = rng.randrange(1, hi // (step * grain)) * step * grain
    content = {
        "kind": "estimate",
        "prompt_key": "t10.number_line",
        "min": 0,
        "max": hi,
        "step": step,
        "target": value,
        "concept": "estimate",
    }
    return content, {"value": value, "tolerance": 0.05}


def gen_t10(band: str, per_level: int = 6) -> list[dict]:
    out = []
    makers = [dots_compare, basket_compare, number_line]
    for level in range(1, 11):
        for n in range(1, per_level + 1):
            rng = random.Random(f"T10:{band}:{level}:{n}")
            content, key = makers[(n - 1) % 3](rng, level)
            out.append(item("T10", band, level, "xx", n, content, key, tags=[content["concept"]]))
    return out


# --------------------------------------------------------------------------------------------- T3
def gen_t3(band: str, count: int = 8) -> list[dict]:
    out = []
    target = figure("star", 0, 1, "solid")
    if band == "11-14":
        distractors = [figure("star", 0, 1, "empty"), figure("circle"), figure("triangle"), figure("diamond")]
        isi, stim = 1200, 650
    else:
        distractors = [
            figure("star", 0, 1, "empty"),
            figure("star", 0, 1, "striped"),
            figure("diamond"),
            figure("triangle", 180),
            figure("circle", 0, 1, "striped"),
        ]
        isi, stim = 1050, 550
    for n in range(1, count + 1):
        rng = random.Random(f"T3:{band}:{n}")
        out.append(
            item(
                "T3",
                band,
                5,
                "xx",
                n,
                {
                    "kind": "stream",
                    "prompt_key": "t3.tap_target",
                    "target": target,
                    "distractors": distractors,
                    "duration_ms": 60000,
                    "isi_ms": isi,
                    "stim_ms": stim,
                    "target_rate": 0.22,
                    "seed": rng.randrange(1, 2**31 - 1),
                },
                {},
                tags=["block"],
            )
        )
    return out


# --------------------------------------------------------------------------------------------- T5 / T23
def logic_item(rng: random.Random, level: int) -> dict:
    """Language-independent structure of an if-then puzzle; rendered per language by logic_render()."""
    steps = 3 if level <= 3 else (4 if level <= 6 else 5)
    props = rng.sample(range(len(PROPS)), steps + 2)
    chain = props[: steps + 1]
    spare = props[steps + 1]
    # polarity: True = positive state. Negated rule parts appear from level 5.
    pol = [True if level < 5 else rng.random() < 0.7 for _ in chain]
    rules = [((chain[i], pol[i]), (chain[i + 1], pol[i + 1])) for i in range(steps)]
    kinds = ["forward", "forward_neg"]
    if level >= 3:
        kinds.append("converse_trap")
    if level >= 5:
        kinds.append("broken")
    if level >= 7:
        kinds.append("tollens")
    kind = rng.choice(kinds)
    first, last = (chain[0], pol[0]), (chain[-1], pol[-1])
    if kind == "forward":
        fact, question, answer = first, last, "yes"
    elif kind == "forward_neg":
        fact, question, answer = first, (last[0], not last[1]), "no"
    elif kind == "converse_trap":
        fact, question, answer = last, first, "cannot"
    elif kind == "tollens":
        fact, question, answer = (last[0], not last[1]), first, "no"
    else:  # broken: one link is missing, so nothing follows
        drop = rng.randrange(1, steps)
        rules = [r for i, r in enumerate(rules) if i != drop]
        fact, question, answer = first, last, "cannot"
    if level >= 6:
        rules.append(((spare, True), (chain[rng.randrange(1, len(chain))], rng.random() < 0.5)))
    if level >= 4:
        rng.shuffle(rules)
    return {"rules": rules, "fact": fact, "question": question, "answer": answer, "kind": kind, "steps": steps}


def logic_render(structure: dict, lang: str) -> dict:
    t = {
        "en": ("If {a}, then {b}.", "{a}.", "Is it true that {q}?"),
        "hi": ("अगर {a}, तो {b}।", "{a}।", "क्या यह सच है कि {q}?"),
        "hinglish": ("Agar {a}, toh {b}.", "{a}.", "Kya yeh sach hai ki {q}?"),
    }[lang]

    def cap(s: str) -> str:
        return s[0].upper() + s[1:] if lang != "hi" else s

    rules = [cap(t[0].format(a=phrase(a[0], a[1], lang), b=phrase(b[0], b[1], lang))) for a, b in structure["rules"]]
    fact = cap(t[1].format(a=phrase(*structure["fact"], lang)))
    question = t[2].format(q=phrase(*structure["question"], lang))
    options = [{"id": oid, "text": LOGIC_OPTIONS[lang][oid]} for oid in ("yes", "no", "cannot")]
    return {
        "kind": "choice",
        "layout": "list",
        "stem": {"rules": rules, "fact": fact},
        "prompt": question,
        "options": options,
        "concept": structure["kind"],
        "steps": structure["steps"],
    }


def gen_t5(band: str, per_level: int = 6) -> list[dict]:
    out = []
    for level in range(1, 11):
        for n in range(1, per_level + 1):
            structure = logic_item(random.Random(f"T5:{band}:{level}:{n}"), level)
            group = make_id("T5", band, level, "all", n)
            for lang in LANGS:
                out.append(
                    item(
                        "T5",
                        band,
                        level,
                        lang,
                        n,
                        logic_render(structure, lang),
                        {"correct": structure["answer"]},
                        tags=[structure["kind"], f"steps{structure['steps']}"],
                        variant_group=group,
                    )
                )
    return out


def gen_t23(band: str, count: int = 12) -> list[dict]:
    """Bilingual probe: the same reasoning item rendered in English, Hindi and Hinglish."""
    out = []
    base = 3 if band == "11-14" else 4
    for n in range(1, count + 1):
        level = base + (n % 3)
        structure = logic_item(random.Random(f"T23:{band}:{n}"), level)
        group = make_id("T23", band, level, "all", n)
        for lang in LANGS:
            out.append(
                item(
                    "T23",
                    band,
                    level,
                    lang,
                    n,
                    logic_render(structure, lang),
                    {"correct": structure["answer"]},
                    tags=["bilingual", structure["kind"]],
                    variant_group=group,
                )
            )
    return out


# --------------------------------------------------------------------------------------------- T14
PLACES = ["shop", "school", "park", "bank", "temple", "library", "post_office", "clinic", "market", "station"]


def route_cost(start: tuple[int, int], points: list[tuple[int, int]]) -> int:
    cost, cur = 0, start
    for p in points:
        cost += abs(p[0] - cur[0]) + abs(p[1] - cur[1])
        cur = p
    return cost


def gen_t14(band: str, per_level: int = 4) -> list[dict]:
    out = []
    for level in range(1, 11):
        for n in range(1, per_level + 1):
            rng = random.Random(f"T14:{band}:{level}:{n}")
            k = min(3 + level // 2, 7)
            size = 6 if k <= 4 else 8
            cells = rng.sample([(x, y) for x in range(size) for y in range(size)], k + 1)
            start, spots = cells[0], cells[1:]
            labels = rng.sample(PLACES, k)
            places = [
                {"id": lab, "label_key": f"place.{lab}", "pos": list(pos)}
                for lab, pos in zip(labels, spots, strict=True)
            ]
            best = min(itertools.permutations(range(k)), key=lambda order: route_cost(start, [spots[i] for i in order]))
            best_cost = route_cost(start, [spots[i] for i in best])
            out.append(
                item(
                    "T14",
                    band,
                    level,
                    "xx",
                    n,
                    {
                        "kind": "plan_route",
                        "prompt_key": "t14.plan",
                        "grid": size,
                        "start": list(start),
                        "places": places,
                    },
                    {"best_cost": best_cost, "best_order": [labels[i] for i in best], "tolerance": 0.1},
                    tags=[f"places{k}"],
                )
            )
    return out


# --------------------------------------------------------------------------------------------- T17 / T19 / T20 / T18
def gen_t17(band: str, pairs: int = 16) -> list[dict]:
    """Pressure Round: matched pairs. Pair k's relaxed and pressure items share difficulty and variant group."""
    out = []
    level = 4 if band == "11-14" else 5
    for k in range(1, pairs + 1):
        for cond_n, cond in enumerate(("relaxed", "pressure")):
            n = (k - 1) * 2 + cond_n + 1
            rng = random.Random(f"T17:{band}:{k}:{cond}")
            maker = [dots_compare, basket_compare, sequence_item][(k - 1) % 3]
            content, key = maker(rng, level)
            content["pair"] = k
            content["set"] = "A" if k <= pairs // 2 else "B"
            content["condition"] = cond
            out.append(
                item(
                    "T17",
                    band,
                    level,
                    "xx",
                    n,
                    content,
                    key,
                    tags=[cond, content["concept"]],
                    variant_group=f"T17-{band_code(band)}-p{k:02d}",
                )
            )
    return out


def symbol_code(rng: random.Random, level: int) -> tuple[dict, dict]:
    """Novel puzzle type used as the 'unfamiliar hard' choice in T18 and as a very hard puzzle in T19."""
    symbols = rng.sample(["star", "circle", "triangle", "square", "diamond"], 3 if level >= 8 else 2)
    values = {s: rng.randint(2, 9) for s in symbols}
    eqs = []
    if len(symbols) == 2:
        a, b = symbols
        eqs.append({"terms": [a, a], "total": values[a] * 2})
        eqs.append({"terms": [a, b], "total": values[a] + values[b]})
        ask = b
    else:
        a, b, c = symbols
        eqs.append({"terms": [a, a, b], "total": values[a] * 2 + values[b]})
        eqs.append({"terms": [a, b], "total": values[a] + values[b]})
        eqs.append({"terms": [b, c, c], "total": values[b] + values[c] * 2})
        ask = c
    answer = values[ask]
    choices = {answer}
    while len(choices) < 4:
        choices.add(max(1, answer + rng.choice([-3, -2, -1, 1, 2, 3])))
    ordered = sorted(choices)
    options = [{"id": f"o{v}", "text": str(v)} for v in ordered]
    content = {
        "kind": "choice",
        "layout": "list",
        "prompt_key": "t18.symbol_code",
        "stem": {"equations": eqs, "ask": ask},
        "options": options,
        "concept": "symbol_code",
    }
    return content, {"correct": f"o{answer}"}


def gen_t18(band: str, count: int = 8) -> list[dict]:
    out = []
    hard_level = 8 if band == "11-14" else 9
    for n in range(1, count + 1):
        rng = random.Random(f"T18:{band}:hard:{n}")
        content, key = symbol_code(rng, hard_level)
        out.append(item("T18", band, hard_level, "xx", n, content, key, tags=["novel", "hard"], extra="h"))
        rng = random.Random(f"T18:{band}:easy:{n}")
        content, key = (dots_compare if n % 2 else basket_compare)(rng, 2)
        out.append(item("T18", band, 2, "xx", n, content, key, tags=["familiar", "easy"], extra="e"))
    for n in range(1, count + 1):
        out.append(
            item(
                "T18",
                band,
                5,
                "xx",
                n,
                {
                    "kind": "choice_menu",
                    "prompt_key": "t18.pick",
                    "easy_ref": make_id("T18", band, 2, "xx", n, "e"),
                    "hard_ref": make_id("T18", band, hard_level, "xx", n, "h"),
                    "easy_points": 1,
                    "hard_points": 3,
                },
                {},
                tags=["menu"],
                extra="m",
            )
        )
    out.append(
        item(
            "T18",
            band,
            5,
            "xx",
            1,
            {
                "kind": "bonus_offer",
                "prompt_key": "t18.bonus",
                "refs": [make_id("T18", band, 2, "xx", n, "e") for n in (6, 7, 8)],
            },
            {},
            tags=["bonus"],
            extra="b",
        )
    )
    return out


def gen_t19(band: str, count: int = 6) -> list[dict]:
    out = []
    for n in range(1, count + 1):
        rng = random.Random(f"T19:{band}:{n}")
        if n % 2:
            content, key = rotation_item(rng, 10, n_options=5)
        else:
            content, key = symbol_code(rng, 10)
        out.append(item("T19", band, 10, "xx", n, content, key, tags=["very_hard", content["concept"]]))
    return out


def gen_t20(band: str, count: int = 12) -> list[dict]:
    out = []
    level = 5 if band == "11-14" else 6
    for n in range(1, count + 1):
        rng = random.Random(f"T20:{band}:{n}")
        content, key = [sequence_item, basket_compare, rotation_item][(n - 1) % 3](rng, level)
        out.append(item("T20", band, level, "xx", n, content, key, tags=[content["concept"]]))
    return out


# --------------------------------------------------------------------------------------------- T16
def gen_t16(band: str, count: int = 3) -> list[dict]:
    out = []
    for n in range(1, count + 1):
        rng = random.Random(f"T16:{band}:{n}")
        t4 = [make_id("T4", band, 5, "xx", i) for i in rng.sample(range(1, 41), 6)]
        t10 = [make_id("T10", band, 4, "xx", i) for i in rng.sample(range(1, 7), 4)]
        t6 = [make_id("T6", band, 7, "xx", i) for i in rng.sample(range(1, 7), 3)]
        out.append(
            item(
                "T16",
                band,
                5,
                "xx",
                n,
                {
                    "kind": "allocate",
                    "prompt_key": "t16.plan",
                    "total_s": 180,
                    "blocks": [
                        {"id": "quick", "label_key": "t16.pack_quick", "difficulty": "easy", "item_ids": t4},
                        {"id": "number", "label_key": "t16.pack_number", "difficulty": "medium", "item_ids": t10},
                        {"id": "shape", "label_key": "t16.pack_shape", "difficulty": "hard", "item_ids": t6},
                    ],
                },
                {},
                tags=["budget"],
            )
        )
    return out


GENERATORS = [
    gen_t1,
    gen_t3,
    gen_t4,
    gen_t5,
    gen_t6,
    gen_t10,
    gen_t14,
    gen_t16,
    gen_t17,
    gen_t18,
    gen_t19,
    gen_t20,
    gen_t23,
]


def generate_all() -> list[dict]:
    out: list[dict] = []
    for band in BANDS:
        for gen in GENERATORS:
            out.extend(gen(band))
    return out
