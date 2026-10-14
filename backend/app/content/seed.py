"""Load task definitions, the item bank and the default scoring configuration.

uv run python -m app.content.seed
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.content.authored.build import build_all
from app.content.generators import generate_all
from app.content.tasks import TASKS
from app.models import Item, ScoringConfig, Task


def all_items() -> list[dict]:
    return generate_all() + build_all()


def seed_tasks(db: Session) -> None:
    for t in TASKS:
        row = db.get(Task, t["id"]) or Task(id=t["id"])
        row.name = t["name"]
        row.layer = t["layer"]
        row.primitive = t["primitive"]
        row.version = 1
        row.definition = t
        db.merge(row)


def seed_items(db: Session) -> int:
    existing = set(db.scalars(select(Item.id)).all())
    added = 0
    for data in all_items():
        if data["id"] in existing:
            continue  # never overwrite: items may have been edited, tagged or retired in the admin console
        db.add(Item(**data, status="active"))
        added += 1
    return added


def seed_scoring_config(db: Session) -> None:
    from app.scoring.config import DEFAULT_CONFIG, DEFAULT_VERSION

    if db.get(ScoringConfig, DEFAULT_VERSION) is None:
        has_active = db.scalars(select(ScoringConfig).where(ScoringConfig.active.is_(True))).first() is not None
        db.add(
            ScoringConfig(
                version=DEFAULT_VERSION,
                config=DEFAULT_CONFIG,
                active=not has_active,
                notes="Blueprint defaults; thresholds marked 'pilot' are placeholders",
            )
        )


def seed_all(db: Session) -> int:
    seed_tasks(db)
    db.flush()
    added = seed_items(db)
    seed_scoring_config(db)
    db.commit()
    return added


if __name__ == "__main__":
    from app.core.db import get_engine, get_sessionmaker
    from app.core.init_db import create_all

    create_all(get_engine())
    with get_sessionmaker()() as session:
        print(f"Seeded {seed_all(session)} new items")
