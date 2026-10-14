"""Turn the authored content into item-bank rows (T2, T7, T8, T9, T11, T12, T15, T21, T22)."""

import random

from app.content.authored import everyday, lesson, passages, recall_cards, words
from app.content.generators import BANDS, LANGS, item, make_id

LETTERS = "abcd"


def _choice_options(rng: random.Random, texts: list[str]) -> tuple[list[dict], str]:
    """First text is correct. Returns shuffled options and the correct option id."""
    order = list(range(len(texts)))
    rng.shuffle(order)
    options = [{"id": LETTERS[pos], "text": texts[idx]} for pos, idx in enumerate(order)]
    correct = LETTERS[order.index(0)]
    return options, correct


def build_t2() -> list[dict]:
    out = []
    counters = {b: 0 for b in BANDS}
    for card_index, card in enumerate(recall_cards.CARDS):
        band = card["band"]
        counters[band] += 1
        n = counters[band]
        group = f"T2-{band.replace('-', '')}-c{card_index + 1}"
        for lang in LANGS:
            data = card[lang]
            rng = random.Random(f"T2:{group}:{lang}")
            questions, answers, lures = [], {}, []
            for qi, (prompt, opts) in enumerate(data["detail"]):
                options, correct = _choice_options(rng, opts)
                qid = f"d{qi + 1}"
                questions.append({"id": qid, "qtype": "detail", "prompt": prompt, "options": options})
                answers[qid] = correct
            yes, no = recall_cards.YES_NO[lang]
            for ri, (thing, present) in enumerate(card[lang]["recognition"]):
                qid = f"r{ri + 1}"
                questions.append(
                    {
                        "id": qid,
                        "qtype": "recognition",
                        "prompt": recall_cards.RECOGNITION_PROMPT[lang].format(x=thing),
                        "options": [{"id": "yes", "text": yes}, {"id": "no", "text": no}],
                    }
                )
                answers[qid] = "yes" if present else "no"
                if not present:
                    lures.append(qid)
            out.append(
                item(
                    "T2",
                    band,
                    5,
                    lang,
                    n,
                    {
                        "kind": "passage_questions",
                        "mode": "card",
                        "card": {"title": data["title"], "lines": data["lines"]},
                        "study_s": 40,
                        "questions": questions,
                    },
                    {"answers": answers, "lures": lures},
                    tags=["card"],
                    variant_group=group,
                )
            )
    return out


def build_t7() -> list[dict]:
    out = []
    counters = {b: 0 for b in BANDS}
    for idx, p in enumerate(passages.READ_ALOUD):
        band = p["band"]
        counters[band] += 1
        group = f"T7-{band.replace('-', '')}-p{idx + 1}"
        for lang in LANGS:
            title, text = p[lang]
            out.append(
                item(
                    "T7",
                    band,
                    p["level"],
                    lang,
                    counters[band],
                    {
                        "kind": "text_response",
                        "mode": "read_aloud",
                        "title": title,
                        "passage": text,
                        "word_count": len(text.split()),
                        "time_limit_s": 150,
                    },
                    {},
                    tags=["read_aloud"],
                    variant_group=group,
                )
            )
    return out


def build_t8() -> list[dict]:
    out = []
    counters = {b: 0 for b in BANDS}
    for idx, p in enumerate(passages.COMPREHENSION):
        band = p["band"]
        counters[band] += 1
        group = f"T8-{band.replace('-', '')}-p{idx + 1}"
        for lang in LANGS:
            data = p[lang]
            rng = random.Random(f"T8:{group}:{lang}")
            questions, answers = [], {}
            for qi, q in enumerate(data["questions"]):
                options, correct = _choice_options(rng, q["options"])
                qid = f"q{qi + 1}"
                questions.append({"id": qid, "qtype": q["qtype"], "prompt": q["prompt"], "options": options})
                answers[qid] = correct
            out.append(
                item(
                    "T8",
                    band,
                    p["level"],
                    lang,
                    counters[band],
                    {
                        "kind": "passage_questions",
                        "mode": "passage",
                        "passage": {
                            "title": data["title"],
                            "text": data["text"],
                            "word_count": len(data["text"].split()),
                        },
                        "questions": questions,
                    },
                    {"answers": answers},
                    tags=["passage"],
                    variant_group=group,
                )
            )
    return out


def build_t9() -> list[dict]:
    out = []
    for band, (lo, hi) in (("11-14", (1, 7)), ("15-18", (4, 10))):
        for lang in LANGS:
            n = 0
            for wi, (level, word, sentence, opts) in enumerate(words.WORDS[lang]):
                if not lo <= level <= hi:
                    continue
                n += 1
                rng = random.Random(f"T9:{band}:{lang}:{wi}")
                options, correct = _choice_options(rng, opts)
                out.append(
                    item(
                        "T9",
                        band,
                        level,
                        lang,
                        n,
                        {
                            "kind": "choice",
                            "layout": "list",
                            "stem": {"sentence": sentence, "word": word},
                            "prompt": words.PROMPT[lang].format(w=word),
                            "options": options,
                            "concept": "word_meaning",
                        },
                        {"correct": correct},
                        tags=["vocabulary"],
                        variant_group=f"T9-w{wi + 1}",
                    )
                )
    return out


def build_t11() -> list[dict]:
    out = []
    for band in BANDS:
        for lang in LANGS:
            for n, (prompt, keywords) in enumerate(everyday.SITUATIONS[lang], start=1):
                out.append(
                    item(
                        "T11",
                        band,
                        5,
                        lang,
                        n,
                        {
                            "kind": "text_response",
                            "mode": "explain",
                            "prompt": prompt,
                            "keywords": keywords,
                            "time_limit_s": 60,
                        },
                        {},
                        tags=["explain"],
                        variant_group=f"T11-s{n}",
                    )
                )
    return out


def build_t12() -> list[dict]:
    out = []
    for band in BANDS:
        for lang in LANGS:
            data = lesson.LESSON[lang]
            rng = random.Random(f"T12:{band}:{lang}")
            questions, answers = [], {}
            for qi, (qset, qtype, prompt, opts) in enumerate(data["questions"]):
                options, correct = _choice_options(rng, opts)
                qid = f"{qset.lower()}{qi + 1}"
                questions.append({"id": qid, "set": qset, "qtype": qtype, "prompt": prompt, "options": options})
                answers[qid] = correct
            out.append(
                item(
                    "T12",
                    band,
                    5,
                    lang,
                    1,
                    {
                        "kind": "passage_questions",
                        "mode": "lesson",
                        "lesson": {"title": data["title"], "sections": data["sections"]},
                        "study_s": 120,
                        "recap": {"text": data["recap"], "study_s": 30},
                        "questions": questions,
                    },
                    {"answers": answers},
                    tags=["lesson"],
                    variant_group="T12-glimmers",
                )
            )
    return out


def build_t15() -> list[dict]:
    out = []
    for band in BANDS:
        for lang in LANGS:
            for n, (level, setup, steps, wrong) in enumerate(everyday.WORKED[lang], start=1):
                label = everyday.STEP_LABEL[lang]
                out.append(
                    item(
                        "T15",
                        band,
                        level,
                        lang,
                        n,
                        {
                            "kind": "choice",
                            "layout": "steps",
                            "stem": {"setup": setup, "steps": steps},
                            "prompt": everyday.WORKED_PROMPT[lang],
                            "options": [{"id": f"s{i + 1}", "text": label.format(n=i + 1)} for i in range(len(steps))],
                            "concept": "error_spotting",
                        },
                        {"correct": f"s{wrong + 1}"},
                        tags=["worked"],
                        variant_group=f"T15-w{n}",
                    )
                )
    return out


def build_t21() -> list[dict]:
    out = []
    for band in BANDS:
        for lang in LANGS:
            for n, (qid, prompt, options) in enumerate(everyday.HABITS[lang], start=1):
                out.append(
                    item(
                        "T21",
                        band,
                        5,
                        lang,
                        n,
                        {
                            "kind": "survey",
                            "qid": qid,
                            "prompt": prompt,
                            "options": [
                                {"id": f"o{i}", "text": text, "value": value} for i, (text, value) in enumerate(options)
                            ],
                        },
                        {},
                        tags=["habits", qid],
                        variant_group=f"T21-{qid}",
                    )
                )
    return out


def build_t22() -> list[dict]:
    out = []
    for band in BANDS:
        for lang in LANGS:
            for n, prompt in enumerate(everyday.CONVERSATION[lang], start=1):
                out.append(
                    item(
                        "T22",
                        band,
                        5,
                        lang,
                        n,
                        {"kind": "text_response", "mode": "converse", "prompt": prompt, "time_limit_s": 60},
                        {},
                        tags=["conversation"],
                        variant_group=f"T22-c{n}",
                    )
                )
    return out


def build_all() -> list[dict]:
    out: list[dict] = []
    for builder in (build_t2, build_t7, build_t8, build_t9, build_t11, build_t12, build_t15, build_t21, build_t22):
        out.extend(builder())
    return out


__all__ = ["build_all", "make_id"]
