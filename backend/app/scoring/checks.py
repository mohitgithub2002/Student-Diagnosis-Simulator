"""Server-side answer checking. The device decides correctness for the adaptive staircase, but the stored
`correct` value always comes from the server's own answer key so scores cannot be skewed by a client."""

from typing import Any


def route_cost(start: list[int], places: list[dict], order: list[str]) -> int | None:
    pos = {p["id"]: p["pos"] for p in places}
    if sorted(order) != sorted(pos):
        return None
    cost, cur = 0, start
    for pid in order:
        nxt = pos[pid]
        cost += abs(nxt[0] - cur[0]) + abs(nxt[1] - cur[1])
        cur = nxt
    return cost


def check(
    content: dict[str, Any],
    key: dict[str, Any],
    answer: Any,
    extra: dict[str, Any] | None = None,
    skipped: bool = False,
) -> bool | None:
    """Return True/False for scored responses and None when the response has no right answer."""
    extra = extra or {}
    kind = content.get("kind")
    if kind == "passage_questions":
        qid = extra.get("qid")
        if not qid:
            return None  # study / recap screens
        expected = key.get("answers", {}).get(qid)
        if expected is None:
            return None
        return False if skipped else answer == expected
    if kind == "sequence":
        if skipped or not isinstance(answer, list):
            return False
        return [str(a) for a in answer] == [str(k) for k in key.get("sequence", [])]
    if kind == "choice":
        if "correct" not in key:
            return None
        return False if skipped or answer is None else str(answer) == str(key["correct"])
    if kind == "estimate":
        if skipped or answer is None:
            return False
        try:
            value = float(answer)
        except (TypeError, ValueError):
            return False
        span = float(content.get("max", 1)) - float(content.get("min", 0))
        return abs(value - float(key["value"])) <= float(key.get("tolerance", 0.05)) * span
    if kind == "plan_route":
        if skipped or not isinstance(answer, list):
            return False
        cost = route_cost(content["start"], content["places"], [str(a) for a in answer])
        if cost is None:
            return False
        return cost <= key["best_cost"] * (1 + float(key.get("tolerance", 0.1)))
    return None
