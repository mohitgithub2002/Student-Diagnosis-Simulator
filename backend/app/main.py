from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import admin, auth, consent, dev, parent, schools, student
from app.core.config import get_settings


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    settings.check_production()
    if settings.is_dev:
        # Local convenience: create tables and load the item bank. Production runs Alembic migrations.
        from app.content.seed import seed_all
        from app.core.db import get_engine, get_sessionmaker
        from app.core.init_db import create_all

        create_all(get_engine())
        with get_sessionmaker()() as db:
            seed_all(db)
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Student Diagnostic Simulator API", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    for router in (auth.router, schools.router, consent.router, parent.router, student.router, admin.router):
        app.include_router(router, prefix="/api")
    if settings.is_dev:
        app.include_router(dev.router, prefix="/api")
    app.mount("/api/static/fonts", StaticFiles(directory=Path(__file__).parent / "reports" / "fonts"), name="fonts")

    @app.get("/api/health")
    def health() -> dict:
        return {"ok": True, "environment": settings.environment}

    return app


app = create_app()
