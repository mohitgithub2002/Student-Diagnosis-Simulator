from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, EmailStr, Field, field_validator

Lang = Literal["en", "hi"]
StudentLang = Literal["en", "hi", "hinglish"]
AgeBand = Literal["11-14", "15-18"]


class TokenOut(BaseModel):
    token: str
    role: str
    name: str = ""
    school_id: int | None = None


class StaffLogin(BaseModel):
    email: str
    password: str


class SchoolSignup(BaseModel):
    school_name: str = Field(min_length=2, max_length=200)
    city: str = ""
    contract_start: date | None = None
    contract_end: date | None = None
    admin_name: str = Field(min_length=1, max_length=120)
    admin_email: EmailStr
    admin_password: str = Field(min_length=8)


class StudentLogin(BaseModel):
    class_code: str
    pin: str = Field(pattern=r"^\d{4}$")


class OtpRequest(BaseModel):
    phone: str = Field(min_length=10, max_length=20)


class OtpVerify(BaseModel):
    phone: str
    code: str = Field(pattern=r"^\d{6}$")


class ClassIn(BaseModel):
    grade: str = Field(min_length=1, max_length=20)
    section: str = ""
    age_band: AgeBand


class TeacherIn(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(min_length=8)


class ScheduleIn(BaseModel):
    start_date: date
    mode: Literal["lab", "home", "both"] = "lab"


class ConsentChoices(BaseModel):
    participate: bool
    voice: bool = False
    share_with_school: bool = False
    language: Lang = "en"


class ConsentSubmit(ConsentChoices):
    code: str = Field(pattern=r"^\d{6}$")


class StartSession(BaseModel):
    device_type: str = Field(default="web", max_length=20)
    language: StudentLang | None = None


class WarmupIn(BaseModel):
    language: StudentLang
    mic_ok: bool = False
    audio_ok: bool = False
    noise_level: float | None = None


class ChangeIn(BaseModel):
    model_config = {"populate_by_name": True}
    from_: Any = Field(default=None, alias="from")
    to: Any = None
    at_ms: int | None = None


class EventIn(BaseModel):
    client_event_id: str = Field(min_length=8, max_length=64)
    item_id: str = Field(max_length=40)
    task_id: str = Field(max_length=4)
    seq: int = 0
    shown_at_ms: float | None = None  # epoch milliseconds on the device clock
    response_ms: int | None = Field(default=None, ge=0, le=3_600_000)
    first_click_ms: int | None = Field(default=None, ge=0, le=3_600_000)
    answer: Any = None
    client_correct: bool | None = None
    changes: int = Field(default=0, ge=0)
    change_log: list[dict[str, Any]] = Field(default_factory=list, max_length=50)
    skipped: bool = False
    retries: int = Field(default=0, ge=0)
    confidence: int | None = Field(default=None, ge=1, le=4)
    idle_ms: int = Field(default=0, ge=0)
    max_idle_ms: int = Field(default=0, ge=0)
    switches: int = Field(default=0, ge=0)
    language: str = Field(default="xx", max_length=10)
    condition: str = Field(default="", max_length=30)
    extra: dict[str, Any] = Field(default_factory=dict)


class EventBatch(BaseModel):
    events: list[EventIn] = Field(max_length=500)


class FeatureIn(BaseModel):
    name: str = Field(max_length=60)
    value: float
    channel: Literal["voice", "voice_vad", "text", "device"]
    task_id: str = Field(default="", max_length=4)
    item_id: str = Field(default="", max_length=40)

    @field_validator("value")
    @classmethod
    def finite(cls, v: float) -> float:
        if v != v or v in (float("inf"), float("-inf")):
            raise ValueError("value must be finite")
        return v


class FeatureBatch(BaseModel):
    features: list[FeatureIn] = Field(max_length=200)


class ResumeState(BaseModel):
    state: dict[str, Any]


class ItemIn(BaseModel):
    id: str = Field(max_length=40)
    task_id: str
    age_band: AgeBand
    level: int = Field(ge=1, le=10)
    language: Literal["en", "hi", "hinglish", "xx"]
    content: dict[str, Any]
    answer_key: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    variant_group: str = ""
    status: Literal["draft", "active", "retired"] = "draft"


class ItemPatch(BaseModel):
    tags: list[str] | None = None
    status: Literal["draft", "active", "retired"] | None = None
    content: dict[str, Any] | None = None
    answer_key: dict[str, Any] | None = None
    level: int | None = Field(default=None, ge=1, le=10)


class ReportEdit(BaseModel):
    content: dict[str, Any]


class ScoringConfigIn(BaseModel):
    version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    config: dict[str, Any]
    notes: str = ""
