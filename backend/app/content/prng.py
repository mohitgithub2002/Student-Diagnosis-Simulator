"""mulberry32, bit-for-bit identical to packages/task-library/src/prng.ts.

The Focus Stream (T3) is generated on the device from a seed; the server regenerates the same stream to
score taps, so both implementations must agree (see tests/fixtures/prng_vectors.json).
"""

from collections.abc import Callable
from typing import Any

MASK = 0xFFFFFFFF


def _imul(a: int, b: int) -> int:
    return (a * b) & MASK


def mulberry32(seed: int) -> Callable[[], float]:
    state = seed & MASK

    def rnd() -> float:
        nonlocal state
        state = (state + 0x6D2B79F5) & MASK
        t = _imul(state ^ (state >> 15), 1 | state)
        t = ((t + _imul(t ^ (t >> 7), 61 | t)) & MASK) ^ t
        return ((t ^ (t >> 14)) & MASK) / 4294967296

    return rnd


def stream_sequence(content: dict[str, Any]) -> list[dict[str, Any]]:
    """Expand a Focus Stream block into its stimuli. Mirrors streamSequence() in the task library."""
    rnd = mulberry32(int(content["seed"]))
    count = int(content["duration_ms"]) // int(content["isi_ms"])
    distractors = content["distractors"]
    out = []
    for i in range(count):
        if rnd() < float(content["target_rate"]):
            out.append({"i": i, "target": True, "figure": content["target"]})
        else:
            pick = min(int(rnd() * len(distractors)), len(distractors) - 1)
            out.append({"i": i, "target": False, "figure": distractors[pick]})
    return out
