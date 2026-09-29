"""Pydantic v2 models mirroring the shared types in CONTRACT §4 (names match exactly)."""
from __future__ import annotations

from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")

DataSource = Literal["real", "sample"]
ReportType = Literal["daily", "weekly"]
DetectState = Literal["idle", "running", "done", "error"]

DATE_PATTERN = r"^\d{4}-\d{2}-\d{2}$"


class Event(BaseModel):
    event_id: str
    datetime: str
    date: str
    time: str
    camera: str
    zone: str
    clip: str
    hardhat: int
    no_hardhat: int
    total_person: int
    violation: bool
    max_conf: float
    frame_path: str
    frame_url: str | None
    no_hardhat_max: int = 0             # raw max Head count before temporal voting
    no_hardhat_ratio: float | None = None  # share of sampled frames with >=1 Head; None for legacy logs


class Paginated(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    size: int
    pages: int


class AggregateRow(BaseModel):
    key: str
    events: int
    violations: int
    rate: float


class ZoneSummary(AggregateRow):
    sparkline: list[int]


class Trend(BaseModel):
    current: int | float
    previous: int | float
    change_pct: float | None


class TopItem(BaseModel):
    key: str
    violations: int


class StatsTrend(BaseModel):
    events: Trend
    violations: Trend
    violation_rate: Trend


class Stats(BaseModel):
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    from_: str | None = Field(alias="from")
    to: str | None
    total_events: int
    total_violations: int
    violation_rate: float
    total_persons: int
    total_no_hardhat: int
    top_zone: TopItem | None
    top_hour: TopItem | None
    trend: StatsTrend
    data_source: DataSource


class DateRange(BaseModel):
    min: str | None
    max: str | None


class LlmProvider(BaseModel):
    name: Literal["primary", "fallback"]
    model: str
    base_url: str


class Health(BaseModel):
    status: Literal["ok"] = "ok"
    data_source: DataSource
    events_count: int
    date_range: DateRange
    llm_configured: bool
    llm_model: str
    llm_base_url: str
    llm_provider: LlmProvider | None = None   # provider that answered last (or will be tried first)
    llm_fallback_configured: bool = False
    llm_rpm: float = 0.0
    conf_threshold: float
    model_repo: str
    site_name: str
    version: str


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=8000)


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1)


class SuggestionsRequest(BaseModel):
    """Body of ``POST /api/chat/suggestions``; ``event_id`` is an optional extension."""

    event_id: str | None = None


class Suggestions(BaseModel):
    questions: list[str]


class ReportRequest(BaseModel):
    type: ReportType
    date: str = Field(pattern=DATE_PATTERN)


class Report(BaseModel):
    name: str
    type: ReportType
    date: str
    created_at: str
    markdown: str


class ReportMeta(BaseModel):
    name: str
    type: ReportType
    date: str
    created_at: str
    size: int


class DetectStatus(BaseModel):
    state: DetectState = "idle"
    progress: float = 0.0
    processed: int = 0
    total: int = 0
    current_clip: str | None = None
    message: str = "ยังไม่ได้เริ่มการตรวจจับ"
    started_at: str | None = None
    finished_at: str | None = None
    events_written: int = 0


class ModelInfo(BaseModel):
    path: str
    source: Literal["local", "downloaded"]
    family: str | None                  # e.g. "yolo26s"
    class_names: list[str]              # model.names ordered by class id
    class_mapping: dict[str, str]       # class name -> "hardhat" | "no_hardhat"
    fallback_repo: str                  # HF repo used only when backend/models/best.pt is missing
    fallback_file: str
    thresholds: dict[str, float]        # {"hardhat": CONF_THRESHOLD, "no_hardhat": HEAD_CONF_THRESHOLD}
    violation_frame_ratio: float        # VIOLATION_FRAME_RATIO


class ParsedClip(BaseModel):
    camera: str
    zone: str
    datetime: str
    matched: bool


class ClipInfo(BaseModel):
    name: str
    size: int
    parsed: ParsedClip


class RejectedFile(BaseModel):
    name: str
    reason: str


class UploadResult(BaseModel):
    saved: list[str]
    rejected: list[RejectedFile]


class RegulationDoc(BaseModel):
    name: str
    size: int
    type: Literal["md", "txt", "pdf"]
    chars: int
    modified: str


class Settings(BaseModel):
    site_name: str = Field(min_length=1, max_length=200)


class LlmTestResult(BaseModel):
    ok: bool
    model: str
    base_url: str
    latency_ms: int | None
    message: str


class ContextSources(BaseModel):
    regulation_files: list[str]                 # files of the paragraphs in context
    log_range: DateRange
    events_count: int
    data_source: DataSource
    log_included_full: bool
    regulation_paragraphs: list[str] = []       # "file · rule title" of each included paragraph
    regulation_paragraphs_total: int = 0
    log_rows: int = 0                           # event lines included in context
    log_filter: str = ""                        # Thai description of how they were chosen
    token_estimate: int = 0                     # len(prompt) / 3.5


class Deleted(BaseModel):
    deleted: str


class ErrorBody(BaseModel):
    code: str
    message: str


class ErrorEnvelope(BaseModel):
    error: ErrorBody
