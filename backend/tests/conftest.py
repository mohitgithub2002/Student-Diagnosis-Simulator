import os
from collections import defaultdict
from pathlib import Path

os.environ.setdefault("SDS_DATABASE_URL", "postgresql+psycopg://sds:sds@localhost:5432/sds_test")
os.environ["SDS_ENVIRONMENT"] = "test"
os.environ["SDS_CELERY_EAGER"] = "true"
os.environ.setdefault("SDS_SECRET_KEY", "test-secret-key-that-is-at-least-32-bytes")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.content.seed import all_items  # noqa: E402
from app.core.db import get_engine  # noqa: E402
from app.core.init_db import drop_all  # noqa: E402

VECTORS = Path(__file__).resolve().parents[2] / "shared" / "test-vectors"


@pytest.fixture(scope="session")
def items():
    return all_items()


@pytest.fixture(scope="session")
def items_by_id(items):
    return {i["id"]: i for i in items}


@pytest.fixture(scope="session")
def lookup(items):
    index = defaultdict(list)
    for i in items:
        index[(i["task_id"], i["age_band"], i["language"])].append(i)
    return lambda task, band, lang: index[(task, band, lang)]


@pytest.fixture(scope="session")
def client():
    drop_all(get_engine())
    from app.main import app

    with TestClient(app) as c:  # lifespan creates tables and seeds the item bank
        yield c


@pytest.fixture
def relaxed_schedule(monkeypatch):
    monkeypatch.setenv("SDS_RELAX_SCHEDULE", "1")
