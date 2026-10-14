"""Operational commands.

uv run python -m app.cli create-staff --role reviewer --email r@example.org --name "Reviewer" --password ...
uv run python -m app.cli seed
uv run python -m app.cli partitions
uv run python -m app.cli sweep-withdrawals
"""

import argparse
from datetime import UTC, datetime

from sqlalchemy import select

from app.core.db import get_engine, get_sessionmaker
from app.core.init_db import create_all, ensure_event_partitions
from app.core.security import hash_password
from app.models import StaffUser


def main() -> None:
    parser = argparse.ArgumentParser(prog="app.cli")
    sub = parser.add_subparsers(dest="cmd", required=True)
    staff = sub.add_parser("create-staff")
    staff.add_argument("--role", choices=["reviewer", "superadmin", "school_admin", "teacher"], required=True)
    staff.add_argument("--email", required=True)
    staff.add_argument("--name", required=True)
    staff.add_argument("--password", required=True)
    staff.add_argument("--school-id", type=int)
    sub.add_parser("seed")
    sub.add_parser("partitions")
    sub.add_parser("sweep-withdrawals")
    demo = sub.add_parser("demo")
    demo.add_argument("--students", type=int, default=6)
    args = parser.parse_args()

    if args.cmd == "create-staff":
        with get_sessionmaker()() as db:
            if db.scalars(select(StaffUser).where(StaffUser.email == args.email.lower())).first():
                raise SystemExit("A user with that email exists")
            db.add(
                StaffUser(
                    email=args.email.lower(),
                    name=args.name,
                    password_hash=hash_password(args.password),
                    role=args.role,
                    school_id=args.school_id,
                )
            )
            db.commit()
            print(f"Created {args.role} {args.email}")
    elif args.cmd == "seed":
        from app.content.seed import seed_all

        create_all(get_engine())
        with get_sessionmaker()() as db:
            print(f"Seeded {seed_all(db)} new items")
    elif args.cmd == "partitions":
        print(ensure_event_partitions(get_engine(), datetime.now(UTC).date().replace(day=1), months=3))
    elif args.cmd == "sweep-withdrawals":
        from app.workers.jobs import sweep_withdrawals

        print(f"Completed {sweep_withdrawals()} pending deletions")
    elif args.cmd == "demo":
        import json

        from app.sim.demo import build_demo

        print(json.dumps(build_demo(args.students), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
