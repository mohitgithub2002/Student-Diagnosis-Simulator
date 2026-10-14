"""Automated wording check (FR-19). Any hit sends the report to the internal review queue."""

import re
from typing import Any

from app.reports.wording import DISCLAIMER

BANNED_EN = [
    r"\bweak\w*",
    r"\bslow learner",
    r"\bdisorder\w*",
    r"\badhd\b",
    r"\bdyslexi\w*",
    r"\bdyscalculi\w*",
    r"\bdysgraphi\w*",
    r"\bautis\w*",
    r"\basperger\w*",
    r"\banxiety disorder",
    r"\bdepress\w*",
    r"\blearning disabilit\w*",
    r"\bdisabilit\w*",
    r"\bocd\b",
    r"\brank(s|ed|ing)?\b",
    r"\btopper\w*",
    r"\bpercentile\w*",
    r"\bbelow average\b",
    r"\blazy\b",
    r"\bstupid\b",
    r"\bdull\b",
    r"\bfailure\b",
    r"\babnormal\w*",
    r"\bdiagnos\w*",
    r"\bclassmates? (scored|did) better",
]
BANNED_HI = [
    "कमज़ोर",
    "कमजोर",
    "मंदबुद्धि",
    "धीमा सीखने वाला",
    "धीमी सीखने वाली",
    "रैंक",
    "टॉपर",
    "विकार",
    "बीमारी",
    "मानसिक रोग",
    "पिछड़ा",
    "नालायक",
    "आलसी",
]
_EN = [re.compile(p, re.IGNORECASE) for p in BANNED_EN]


def iter_text(value: Any, path: str = ""):
    if isinstance(value, str):
        yield path, value
    elif isinstance(value, dict):
        for k, v in value.items():
            yield from iter_text(v, f"{path}.{k}" if path else str(k))
    elif isinstance(value, list):
        for i, v in enumerate(value):
            yield from iter_text(v, f"{path}[{i}]")


def check_report(content: dict[str, Any]) -> list[dict[str, str]]:
    flags: list[dict[str, str]] = []
    for path, text in iter_text(content):
        if path.endswith(
            (
                "skill_id",
                "type",
                "tag",
                "evidence_level",
                "audience",
                "language",
                "scoring_version",
                "generated_at",
                "direction",
                "layer",
                "band",
            )
        ):
            continue
        for pattern in _EN:
            m = pattern.search(text)
            if m:
                flags.append({"rule": "banned_word", "path": path, "match": m.group(0)})
        for word in BANNED_HI:
            if word in text:
                flags.append({"rule": "banned_word", "path": path, "match": word})
    lang = content.get("language", "en")
    if content.get("disclaimer") != DISCLAIMER.get(lang, DISCLAIMER["en"]):
        flags.append({"rule": "missing_disclaimer", "path": "disclaimer", "match": ""})
    for key in ("overall_score", "total_score", "overall"):
        if key in content:
            flags.append({"rule": "single_overall_number", "path": key, "match": key})
    for section in ("strengths", "areas_to_grow", "patterns"):
        for i, finding in enumerate(content.get(section, [])):
            if content.get("audience") == "parent" and (
                not finding.get("evidence_line") or finding.get("evidence_level") not in ("High", "Medium")
            ):
                flags.append({"rule": "finding_without_evidence", "path": f"{section}[{i}]", "match": ""})
    return flags
