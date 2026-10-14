from datetime import date, timedelta

from app.models import Cycle, Session
from app.services.scheduler import session_status

START = date(2026, 11, 2)


def make_cycle(done: set[int] = frozenset()) -> Cycle:
    cycle = Cycle(student_id="x", number=1, age_band="11-14", start_date=START, end_date=START + timedelta(days=15))
    for n in range(1, 8):
        day = START + timedelta(days=2 * (n - 1))
        cycle.sessions.append(
            Session(
                number=n,
                scheduled_for=day,
                window_end=day + timedelta(days=3),
                status="completed" if n in done else "scheduled",
            )
        )
    return cycle


def state(cycle: Cycle, n: int, offset: int) -> str:
    return session_status(cycle.sessions[n - 1], cycle, START + timedelta(days=offset))["state"]


def test_seven_sessions_every_second_day_with_makeup_window():
    c = make_cycle()
    assert state(c, 1, 0) == "available"
    assert state(c, 2, 0) == "locked"  # must finish session 1 first
    assert state(c, 1, 3) == "available"  # make-up window: 3 days
    assert session_status(c.sessions[0], c, START + timedelta(days=3))["makeup"] is True
    assert state(c, 1, 4) == "missed"
    assert state(c, 2, 4) == "available"  # a missed session no longer blocks the next one


def test_upcoming_and_completed():
    c = make_cycle(done={1})
    assert state(c, 1, 1) == "completed"
    assert state(c, 2, 1) == "upcoming"
    assert state(c, 2, 2) == "available"
    assert session_status(c.sessions[1], c, START + timedelta(days=1))["opens_on"] == "2026-11-04"
