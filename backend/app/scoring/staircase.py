"""Adaptive difficulty (FR-06): 10 levels, up one after 2 correct in a row, down one after a wrong answer.
The skill level is the mean of the last 6 turning points. Mirrors packages/task-library/src/staircase.ts;
tests/fixtures/staircase_vectors.json keeps the two in step."""

from dataclasses import dataclass, field

MIN_LEVEL, MAX_LEVEL = 1, 10


@dataclass
class Staircase:
    level: int
    streak: int = 0
    last_dir: int = 0
    reversals: list[int] = field(default_factory=list)
    history: list[int] = field(default_factory=list)

    def record(self, correct: bool) -> int:
        """Record an answer at the current level; returns the next level."""
        self.history.append(self.level)
        move = 0
        if correct:
            self.streak += 1
            if self.streak >= 2:
                move, self.streak = 1, 0
        else:
            self.streak, move = 0, -1
        if move:
            new = max(MIN_LEVEL, min(MAX_LEVEL, self.level + move))
            if new != self.level:
                if self.last_dir and move != self.last_dir:
                    self.reversals.append(self.level)
                self.last_dir = move
                self.level = new
        return self.level

    def estimate(self) -> float | None:
        if len(self.reversals) >= 2:
            last = self.reversals[-6:]
            return round(sum(last) / len(last), 3)
        if not self.history:
            return None
        tail = self.history[len(self.history) // 2 :]
        return round(sum(tail) / len(tail), 3)


def replay(start: int, answers: list[bool]) -> Staircase:
    sc = Staircase(level=start)
    for correct in answers:
        sc.record(correct)
    return sc


def estimate_from_trials(trials: list[tuple[int, bool]]) -> float | None:
    """Estimate from (level shown, correct) pairs as logged. When the log follows the staircase rules (the
    normal case) this equals the device's own estimate, including a turning point on the final answer."""
    if not trials:
        return None
    replayed = replay(trials[0][0], [ok for _, ok in trials])
    if replayed.history == [lvl for lvl, _ in trials]:
        return replayed.estimate()
    reversals: list[int] = []
    last_dir = 0
    for (lvl, _), (nxt, _) in zip(trials, trials[1:], strict=False):
        if nxt == lvl:
            continue
        direction = 1 if nxt > lvl else -1
        if last_dir and direction != last_dir:
            reversals.append(lvl)
        last_dir = direction
    if len(reversals) >= 2:
        last = reversals[-6:]
        return round(sum(last) / len(last), 3)
    levels = [lvl for lvl, _ in trials]
    tail = levels[len(levels) // 2 :]
    return round(sum(tail) / len(tail), 3)
