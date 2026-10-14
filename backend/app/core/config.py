from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration. Every value can be overridden with an SDS_* environment variable."""

    model_config = SettingsConfigDict(env_prefix="SDS_", env_file=".env", extra="ignore")

    environment: str = "dev"  # dev | test | prod
    database_url: str = "postgresql+psycopg://sds:sds@localhost:5432/sds"
    redis_url: str = "redis://localhost:6379/0"
    # Run background jobs inline instead of through Celery (tests, single-process demos).
    celery_eager: bool = True

    secret_key: str = "dev-only-secret-change-me-before-any-real-deployment"
    # Fernet key for identity fields (guardian phone). Derived from secret_key when empty.
    field_encryption_key: str = ""
    staff_token_ttl_minutes: int = 8 * 60
    parent_token_ttl_minutes: int = 60
    student_token_ttl_minutes: int = 90

    otp_ttl_seconds: int = 300
    otp_max_attempts: int = 5
    login_max_failures: int = 5
    login_lockout_minutes: int = 15

    messaging_provider: str = "console"  # console | (future) msg91 | twilio
    public_web_url: str = "http://localhost:5173"
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:4173"]

    notice_version: str = "2026-10-v1"
    withdrawal_deadline_days: int = 7
    # Session schedule (FR-09): 7 sessions, one every second day, 3-day make-up window.
    sessions_per_cycle: int = 7
    session_interval_days: int = 2
    makeup_window_days: int = 3

    @property
    def is_dev(self) -> bool:
        return self.environment in ("dev", "test")

    def check_production(self) -> None:
        if self.environment == "prod" and (self.secret_key.startswith("dev-only") or len(self.secret_key) < 32):
            raise RuntimeError("Set SDS_SECRET_KEY to a random value of at least 32 characters in production")


@lru_cache
def get_settings() -> Settings:
    return Settings()
