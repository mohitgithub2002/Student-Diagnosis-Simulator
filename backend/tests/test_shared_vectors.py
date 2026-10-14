"""The device and the server must agree on the Focus Stream PRNG and the adaptive staircase."""

import json

from app.content.prng import mulberry32, stream_sequence
from app.scoring.staircase import Staircase, estimate_from_trials, replay
from tests.conftest import VECTORS


def test_mulberry32_vectors():
    data = json.loads((VECTORS / "prng.json").read_text())
    for case in data["mulberry32"]:
        rnd = mulberry32(case["seed"])
        assert [rnd() for _ in case["values"]] == case["values"]


def test_stream_vectors():
    data = json.loads((VECTORS / "prng.json").read_text())
    for case in data["stream"]:
        got = [[s["target"], s["figure"]["shape"]] for s in stream_sequence(case["content"])]
        assert got == case["expected"]


def test_staircase_vectors():
    data = json.loads((VECTORS / "staircase.json").read_text())
    for case in data["cases"]:
        sc = replay(case["start"], case["answers"])
        assert sc.history == case["levels"]
        assert sc.level == case["final"]
        assert sc.reversals == case["reversals"]
        assert sc.estimate() == case["estimate"]


def test_staircase_rules():
    sc = Staircase(level=5)
    assert sc.record(True) == 5  # one correct: stay
    assert sc.record(True) == 6  # two in a row: up
    assert sc.record(False) == 5  # one wrong: down
    assert sc.reversals == [6]
    top = Staircase(level=10)
    top.record(True)
    assert top.record(True) == 10  # bounded


def test_estimate_from_logged_trials_matches_replay():
    answers = [True, True, True, True, False, True, True, False, False, True, True, True, True, False]
    sc = replay(4, answers)
    trials = list(zip(sc.history, answers, strict=True))
    assert estimate_from_trials(trials) == sc.estimate()
