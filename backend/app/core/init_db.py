"""Schema bootstrap used by tests and the demo. Production uses Alembic migrations."""

from datetime import date

from sqlalchemy import Engine, text

from app.models import ASSESSMENT, IDENTITY, Base


def create_schemas(engine: Engine) -> None:
    with engine.begin() as conn:
        for schema in (IDENTITY, ASSESSMENT):
            conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))


def create_all(engine: Engine) -> None:
    create_schemas(engine)
    Base.metadata.create_all(engine)


def drop_all(engine: Engine) -> None:
    with engine.begin() as conn:
        for schema in (IDENTITY, ASSESSMENT):
            conn.execute(text(f"DROP SCHEMA IF EXISTS {schema} CASCADE"))


def ensure_event_partitions(engine: Engine, start: date, months: int = 3) -> list[str]:
    """Create monthly partitions of the item event log ahead of time (run from a periodic job)."""
    created = []
    with engine.begin() as conn:
        year, month = start.year, start.month
        for _ in range(months):
            nxt_year, nxt_month = (year + 1, 1) if month == 12 else (year, month + 1)
            name = f"item_events_{year}{month:02d}"
            exists = conn.execute(
                text("SELECT 1 FROM pg_tables WHERE schemaname = :s AND tablename = :t"),
                {"s": ASSESSMENT, "t": name},
            ).first()
            if not exists:
                # Rows already in the default partition for this range would block creation, so move them.
                conn.execute(
                    text(f"CREATE TABLE {ASSESSMENT}.{name} (LIKE {ASSESSMENT}.item_events INCLUDING DEFAULTS)")
                )
                lo, hi = f"{year}-{month:02d}-01", f"{nxt_year}-{nxt_month:02d}-01"
                bounds = f"FOR VALUES FROM ('{lo}') TO ('{hi}')"
                in_range = f"WHERE recorded_at >= '{lo}' AND recorded_at < '{hi}'"
                conn.execute(
                    text(f"INSERT INTO {ASSESSMENT}.{name} SELECT * FROM {ASSESSMENT}.item_events_default {in_range}")
                )
                conn.execute(text(f"DELETE FROM {ASSESSMENT}.item_events_default {in_range}"))
                conn.execute(
                    text(f"ALTER TABLE {ASSESSMENT}.item_events ATTACH PARTITION {ASSESSMENT}.{name} {bounds}")
                )
                created.append(name)
            year, month = nxt_year, nxt_month
    return created
