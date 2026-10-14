"""Assessment schema: behavioural data, scores and reports. No names or phone numbers live here."""

from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    DDL,
    JSON,
    BigInteger,
    Boolean,
    Date,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    event,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import ASSESSMENT, Base, utcnow


class ScoringConfig(Base):
    """Versioned weights and thresholds (FR-27). Every score and report records the version used."""

    __tablename__ = "scoring_configs"
    __table_args__ = {"schema": ASSESSMENT}

    version: Mapped[str] = mapped_column(String(20), primary_key=True)
    config: Mapped[dict[str, Any]] = mapped_column(JSON)
    active: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str] = mapped_column(String(500), default="")
    created_by: Mapped[str] = mapped_column(String(80), default="system")
    created_at: Mapped[datetime] = mapped_column(default=utcnow)


class Task(Base):
    __tablename__ = "tasks"
    __table_args__ = {"schema": ASSESSMENT}

    id: Mapped[str] = mapped_column(String(4), primary_key=True)  # T1..T23
    name: Mapped[str] = mapped_column(String(80))
    layer: Mapped[str] = mapped_column(String(30))
    primitive: Mapped[str] = mapped_column(String(30))
    version: Mapped[int] = mapped_column(Integer, default=1)
    definition: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class Item(Base):
    __tablename__ = "items"
    __table_args__ = (
        Index("ix_items_lookup", "task_id", "age_band", "language", "level", "status"),
        {"schema": ASSESSMENT},
    )

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    task_id: Mapped[str] = mapped_column(ForeignKey(f"{ASSESSMENT}.tasks.id"))
    age_band: Mapped[str] = mapped_column(String(5))
    level: Mapped[int] = mapped_column(Integer)
    language: Mapped[str] = mapped_column(String(10))  # en | hi | hinglish | xx (language-neutral)
    content: Mapped[dict[str, Any]] = mapped_column(JSON)
    answer_key: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    # Items that are the same content in different languages or forms share a group.
    variant_group: Mapped[str] = mapped_column(String(40), default="")
    status: Mapped[str] = mapped_column(String(10), default="active")  # draft | active | retired
    created_at: Mapped[datetime] = mapped_column(default=utcnow)


class Cycle(Base):
    __tablename__ = "cycles"
    __table_args__ = (UniqueConstraint("student_id", "number"), {"schema": ASSESSMENT})

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[str] = mapped_column(String(36), index=True)
    number: Mapped[int] = mapped_column(Integer, default=1)
    age_band: Mapped[str] = mapped_column(String(5))
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(12), default="active")  # active | completed | scored
    completed_at: Mapped[datetime | None]
    scored_at: Mapped[datetime | None]
    scoring_version: Mapped[str | None] = mapped_column(String(20))
    # Engine output that is not a per-skill score: patterns, root-cause summary, flags, language gap.
    summary: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    sessions: Mapped[list["Session"]] = relationship(
        back_populates="cycle", order_by="Session.number", cascade="all, delete-orphan"
    )


class Session(Base):
    __tablename__ = "sessions"
    __table_args__ = (UniqueConstraint("cycle_id", "number"), {"schema": ASSESSMENT})

    id: Mapped[int] = mapped_column(primary_key=True)
    cycle_id: Mapped[int] = mapped_column(ForeignKey(f"{ASSESSMENT}.cycles.id", ondelete="CASCADE"), index=True)
    number: Mapped[int] = mapped_column(Integer)
    scheduled_for: Mapped[date] = mapped_column(Date)
    window_end: Mapped[date] = mapped_column(Date)
    started_at: Mapped[datetime | None]
    completed_at: Mapped[datetime | None]
    device_type: Mapped[str] = mapped_column(String(20), default="")
    language: Mapped[str] = mapped_column(String(10), default="")
    status: Mapped[str] = mapped_column(String(12), default="scheduled")  # scheduled|in_progress|completed|missed
    seed: Mapped[int] = mapped_column(BigInteger, default=0)
    resume_state: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    cycle: Mapped[Cycle] = relationship(back_populates="sessions")


class EventReceipt(Base):
    """Idempotency ledger for client event ids (item events are partitioned, so they cannot carry a
    global unique constraint on the client id)."""

    __tablename__ = "event_receipts"
    __table_args__ = {"schema": ASSESSMENT}

    client_event_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    session_id: Mapped[int] = mapped_column(Integer, index=True)
    received_at: Mapped[datetime] = mapped_column(default=utcnow)


class ItemEvent(Base):
    """Append-only per-item log (FR-10). Range-partitioned by recorded_at."""

    __tablename__ = "item_events"
    __table_args__ = (
        Index("ix_item_events_session", "session_id"),
        {"schema": ASSESSMENT, "postgresql_partition_by": "RANGE (recorded_at)"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    recorded_at: Mapped[datetime] = mapped_column(primary_key=True, default=utcnow)
    client_event_id: Mapped[str] = mapped_column(String(64))
    session_id: Mapped[int] = mapped_column(Integer)
    item_id: Mapped[str] = mapped_column(String(40))
    task_id: Mapped[str] = mapped_column(String(4))
    seq: Mapped[int] = mapped_column(Integer, default=0)  # order within the session
    shown_at: Mapped[datetime]
    response_ms: Mapped[int | None] = mapped_column(Integer)
    first_click_ms: Mapped[int | None] = mapped_column(Integer)
    answer: Mapped[Any] = mapped_column(JSON, nullable=True)
    correct: Mapped[bool | None] = mapped_column(Boolean)
    changes: Mapped[int] = mapped_column(Integer, default=0)
    change_log: Mapped[list[Any]] = mapped_column(JSON, default=list)
    skipped: Mapped[bool] = mapped_column(Boolean, default=False)
    retries: Mapped[int] = mapped_column(Integer, default=0)
    confidence: Mapped[int | None] = mapped_column(Integer)
    idle_ms: Mapped[int] = mapped_column(Integer, default=0)
    max_idle_ms: Mapped[int] = mapped_column(Integer, default=0)
    switches: Mapped[int] = mapped_column(Integer, default=0)
    level: Mapped[int | None] = mapped_column(Integer)
    language: Mapped[str] = mapped_column(String(10), default="xx")
    condition: Mapped[str] = mapped_column(String(30), default="")
    extra: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


# A default partition catches every row; ensure_event_partitions() adds monthly partitions ahead of time.
event.listen(
    ItemEvent.__table__,
    "after_create",
    DDL(f"CREATE TABLE IF NOT EXISTS {ASSESSMENT}.item_events_default PARTITION OF {ASSESSMENT}.item_events DEFAULT"),
)


class Feature(Base):
    """Derived values per session: server-extracted timing features and on-device voice/text features."""

    __tablename__ = "features"
    __table_args__ = (Index("ix_features_session_name", "session_id", "name"), {"schema": ASSESSMENT})

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey(f"{ASSESSMENT}.sessions.id", ondelete="CASCADE"))
    skill_id: Mapped[str | None] = mapped_column(String(40))
    name: Mapped[str] = mapped_column(String(60))
    value: Mapped[float] = mapped_column(Float)
    source_channel: Mapped[str] = mapped_column(String(20))  # timing | voice | voice_vad | text | selfreport
    task_id: Mapped[str] = mapped_column(String(4), default="")
    item_id: Mapped[str] = mapped_column(String(40), default="")
    # False for features computed on the device; True for features the scoring engine derived.
    derived: Mapped[bool] = mapped_column(Boolean, default=False)
    recorded_at: Mapped[datetime] = mapped_column(default=utcnow)


class StudentVisit(Base):
    """App opens, used for 'returns between sessions' (motivation, study consistency)."""

    __tablename__ = "student_visits"
    __table_args__ = {"schema": ASSESSMENT}

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[str] = mapped_column(String(36), index=True)
    at: Mapped[datetime] = mapped_column(default=utcnow)


class SkillScore(Base):
    __tablename__ = "skill_scores"
    __table_args__ = (
        UniqueConstraint("cycle_id", "skill_id", "scoring_version"),
        {"schema": ASSESSMENT},
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    cycle_id: Mapped[int] = mapped_column(ForeignKey(f"{ASSESSMENT}.cycles.id", ondelete="CASCADE"), index=True)
    skill_id: Mapped[str] = mapped_column(String(40))
    score: Mapped[float | None] = mapped_column(Float)
    raw_score: Mapped[float | None] = mapped_column(Float)
    evidence_level: Mapped[str] = mapped_column(String(8))  # High | Medium | Low
    relative_band: Mapped[str] = mapped_column(String(14))  # strength | typical | grow | insufficient
    language_adjusted: Mapped[bool] = mapped_column(Boolean, default=False)
    scoring_version: Mapped[str] = mapped_column(String(20))
    detail: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class ErrorTag(Base):
    __tablename__ = "error_tags"
    __table_args__ = {"schema": ASSESSMENT}

    id: Mapped[int] = mapped_column(primary_key=True)
    cycle_id: Mapped[int] = mapped_column(ForeignKey(f"{ASSESSMENT}.cycles.id", ondelete="CASCADE"), index=True)
    item_event_id: Mapped[int] = mapped_column(BigInteger, index=True)
    item_id: Mapped[str] = mapped_column(String(40))
    tag: Mapped[str] = mapped_column(String(30))
    rule_id: Mapped[str] = mapped_column(String(10))
    scoring_version: Mapped[str] = mapped_column(String(20))


class Report(Base):
    __tablename__ = "reports"
    __table_args__ = {"schema": ASSESSMENT}

    id: Mapped[int] = mapped_column(primary_key=True)
    cycle_id: Mapped[int] = mapped_column(ForeignKey(f"{ASSESSMENT}.cycles.id", ondelete="CASCADE"), index=True)
    audience: Mapped[str] = mapped_column(String(10))  # parent | student
    language: Mapped[str] = mapped_column(String(5))
    status: Mapped[str] = mapped_column(String(12), default="draft")  # draft | in_review | released
    scoring_version: Mapped[str] = mapped_column(String(20))
    content: Mapped[dict[str, Any]] = mapped_column(JSON)
    wording_flags: Mapped[list[Any]] = mapped_column(JSON, default=list)
    reviewed_by: Mapped[str | None] = mapped_column(String(80))
    reviewed_at: Mapped[datetime | None]
    released_at: Mapped[datetime | None]
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
