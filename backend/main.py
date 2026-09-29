"""FastAPI application — REST + SSE API described in CONTRACT §4–§5.

Run from the repo root: ``uvicorn backend.main:app --reload``.
"""
from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator
from datetime import datetime
from typing import Annotated, Any, Literal

from fastapi import Body, FastAPI, File, Query, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from starlette.concurrency import iterate_in_threadpool, run_in_threadpool
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend import aggregates, assistant, config, data, detect_runner, llm, regulations, report, uploads
from backend.frame_utils import VIDEO_EXTENSIONS, parse_clip_filename
from backend.models import (
    DATE_PATTERN,
    AggregateRow,
    ChatRequest,
    ClipInfo,
    ContextSources,
    Deleted,
    DetectStatus,
    ErrorEnvelope,
    Event,
    Health,
    LlmTestResult,
    ModelInfo,
    Paginated,
    RegulationDoc,
    Report,
    ReportMeta,
    ReportRequest,
    Settings,
    Stats,
    Suggestions,
    SuggestionsRequest,
    UploadResult,
    ZoneSummary,
)

if not logging.getLogger().handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("backend.api")

REGULATION_MAX_BYTES = 20 * 1024 * 1024
FRAME_MEDIA_TYPES = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png"}

DateFrom = Annotated[str | None, Query(alias="from", pattern=DATE_PATTERN, description="YYYY-MM-DD (inclusive)")]
DateTo = Annotated[str | None, Query(alias="to", pattern=DATE_PATTERN, description="YYYY-MM-DD (inclusive)")]


# --- errors ---------------------------------------------------------------------

class ApiError(Exception):
    """Error rendered as the contract error envelope."""

    def __init__(self, status: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status, self.code, self.message = status, code, message


def not_found(message: str = "ไม่พบข้อมูลที่ร้องขอ") -> ApiError:
    return ApiError(404, "NOT_FOUND", message)


def bad_request(message: str) -> ApiError:
    return ApiError(400, "BAD_REQUEST", message)


def error_response(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message}})


app = FastAPI(
    title="Helmet Safety Assistant API",
    version=config.APP_VERSION,
    description="ระบบผู้ช่วย AI ติดตามการสวมหมวกนิรภัยในไซต์ก่อสร้าง",
    responses={400: {"model": ErrorEnvelope}, 404: {"model": ErrorEnvelope}, 422: {"model": ErrorEnvelope}},
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.exception_handler(ApiError)
async def _api_error(_: Request, exc: ApiError) -> JSONResponse:
    return error_response(exc.status, exc.code, exc.message)


@app.exception_handler(llm.LLMNotConfigured)
async def _llm_not_configured(_: Request, exc: llm.LLMNotConfigured) -> JSONResponse:
    return error_response(503, exc.code, exc.message)


@app.exception_handler(llm.LLMError)
async def _llm_error(_: Request, exc: llm.LLMError) -> JSONResponse:
    return error_response(502, exc.code, exc.message)


@app.exception_handler(report.ReportInputError)
async def _report_input(_: Request, exc: report.ReportInputError) -> JSONResponse:
    return error_response(400, "BAD_REQUEST", str(exc))


@app.exception_handler(detect_runner.DetectionRunning)
async def _detect_running(_: Request, __: detect_runner.DetectionRunning) -> JSONResponse:
    return error_response(409, "DETECTION_RUNNING", "กำลังรันการตรวจจับอยู่ — กรุณารอให้เสร็จก่อนเริ่มใหม่")


@app.exception_handler(RequestValidationError)
async def _validation(_: Request, exc: RequestValidationError) -> JSONResponse:
    details = "; ".join(
        f"{'.'.join(str(p) for p in err.get('loc', ()))}: {err.get('msg', '')}" for err in exc.errors()[:5]
    )
    return error_response(422, "VALIDATION_ERROR", f"ข้อมูลที่ส่งมาไม่ถูกต้อง — {details}")


@app.exception_handler(StarletteHTTPException)
async def _http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
    if exc.status_code == 404:
        return error_response(404, "NOT_FOUND", "ไม่พบข้อมูลหรือเส้นทาง API ที่ร้องขอ")
    if exc.status_code == 405:
        return error_response(405, "BAD_REQUEST", "ไม่รองรับเมธอดนี้สำหรับเส้นทางดังกล่าว")
    code = "INTERNAL_ERROR" if exc.status_code >= 500 else "BAD_REQUEST"
    return error_response(exc.status_code, code, "คำขอไม่ถูกต้อง" if exc.status_code < 500 else "เกิดข้อผิดพลาดภายในระบบ")


@app.exception_handler(Exception)
async def _unhandled(_: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error", exc_info=exc)
    return error_response(500, "INTERNAL_ERROR", "เกิดข้อผิดพลาดภายในระบบ กรุณาลองใหม่อีกครั้ง")


# --- health & settings ------------------------------------------------------------

@app.get("/api/health", response_model=Health, tags=["system"])
def health() -> dict[str, Any]:
    log = data.load_events()
    settings = config.get_settings()
    return {
        "status": "ok",
        "data_source": log.source,
        "events_count": len(log.df),
        "date_range": {"min": log.date_min, "max": log.date_max},
        "llm_configured": llm.is_configured(),
        "llm_model": settings.llm_model,
        "llm_base_url": settings.llm_base_url,
        "llm_provider": llm.active_provider(),
        "llm_fallback_configured": llm.fallback_configured(),
        "llm_rpm": settings.llm_rpm,
        "conf_threshold": settings.conf_threshold,
        "model_repo": settings.hf_model_repo,
        "site_name": config.site_name(),
        "version": config.APP_VERSION,
    }


@app.get("/api/settings", response_model=Settings, tags=["system"])
def get_settings() -> dict[str, str]:
    return {"site_name": config.site_name()}


@app.put("/api/settings", response_model=Settings, tags=["system"])
def put_settings(body: Settings) -> dict[str, str]:
    name = body.site_name.strip()
    if not name:
        raise bad_request("กรุณาระบุชื่อโครงการ")
    return {"site_name": config.save_site_name(name)}


@app.post("/api/llm/test", response_model=LlmTestResult, tags=["system"])
def llm_test(_: Annotated[dict[str, Any] | None, Body()] = None) -> dict[str, Any]:
    return llm.test_connection()


# --- events & aggregates ----------------------------------------------------------

@app.get("/api/stats", response_model=Stats, tags=["events"])
def stats(date_from: DateFrom = None, date_to: DateTo = None, zone: str | None = None, camera: str | None = None) -> dict[str, Any]:
    log = data.load_events()
    df = data.filter_events(log.df, zone=zone, camera=camera)
    return aggregates.compute_stats(df, log.source, date_from, date_to)


@app.get("/api/events", response_model=Paginated[Event], tags=["events"])
def list_events(
    date_from: DateFrom = None,
    date_to: DateTo = None,
    zone: str | None = None,
    camera: str | None = None,
    violation: bool | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=200)] = 20,
    sort: str = "datetime",
    order: Literal["asc", "desc"] = "desc",
) -> dict[str, Any]:
    if sort not in data.SORTABLE_COLUMNS:
        raise bad_request(f"ไม่สามารถเรียงตามคอลัมน์ '{sort}' ได้")
    df = data.filter_events(data.load_events().df, date_from, date_to, zone, camera, violation)
    return data.paginate(data.sort_events(df, sort, order), page, size)


@app.get("/api/events/{event_id}", response_model=Event, tags=["events"])
def get_event(event_id: str) -> dict[str, Any]:
    event = data.get_event(data.load_events().df, event_id)
    if event is None:
        raise not_found(f"ไม่พบเหตุการณ์ {event_id}")
    return event


@app.get("/api/aggregates", response_model=list[AggregateRow], tags=["events"])
def get_aggregates(
    group_by: Literal["zone", "camera", "hour", "day"], date_from: DateFrom = None, date_to: DateTo = None
) -> list[dict[str, Any]]:
    return aggregates.group_by(data.load_events().df, group_by, date_from, date_to)


@app.get("/api/zones", response_model=list[ZoneSummary], tags=["events"])
def zones() -> list[dict[str, Any]]:
    return aggregates.zone_summaries(data.load_events().df)


@app.get("/api/cameras", response_model=list[AggregateRow], tags=["events"])
def cameras() -> list[dict[str, Any]]:
    return aggregates.group_by(data.load_events().df, "camera")


@app.get("/api/frames/{filename}", tags=["events"], response_class=FileResponse)
def frame(filename: str) -> FileResponse:
    path = uploads.resolve_inside(config.frames_dir(), filename)
    media_type = FRAME_MEDIA_TYPES.get(path.suffix.lower()) if path else None
    if path is None or media_type is None or not path.is_file():
        raise not_found(f"ไม่พบภาพเฟรม {filename}")
    return FileResponse(path, media_type=media_type)


# --- chat -------------------------------------------------------------------------

def _sse(payload: dict[str, Any]) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


@app.post("/api/chat", tags=["assistant"], response_class=StreamingResponse)
async def chat(body: ChatRequest) -> StreamingResponse:
    if not llm.is_configured():
        raise llm.LLMNotConfigured()
    if body.messages[-1].role != "user":
        raise bad_request("ข้อความล่าสุดต้องเป็นคำถามจากผู้ใช้")
    log = data.load_events()
    messages, sources = await run_in_threadpool(assistant.build_messages, body.messages, log.df, log.source)

    async def events() -> AsyncIterator[str]:
        yield _sse({"type": "sources", "sources": sources})
        try:
            async for token in iterate_in_threadpool(llm.stream_chat(messages)):
                yield _sse({"type": "token", "content": token})
        except (llm.LLMError, llm.LLMNotConfigured) as exc:
            yield _sse({"type": "error", "message": exc.message})
        except Exception:  # noqa: BLE001 — must terminate the stream cleanly
            logger.exception("Chat stream failed")
            yield _sse({"type": "error", "message": "เกิดข้อผิดพลาดระหว่างสร้างคำตอบ กรุณาลองใหม่อีกครั้ง"})
        yield _sse({"type": "done"})

    headers = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    return StreamingResponse(events(), media_type="text/event-stream", headers=headers)


@app.get("/api/chat/context", response_model=ContextSources, tags=["assistant"])
def chat_context() -> dict[str, Any]:
    log = data.load_events()
    return assistant.build_context(log.df, log.source)[1]


@app.post("/api/chat/suggestions", response_model=Suggestions, tags=["assistant"])
def chat_suggestions(body: SuggestionsRequest | None = None) -> dict[str, list[str]]:
    df = data.load_events().df
    event = None
    if body is not None and body.event_id:
        event = data.get_event(df, body.event_id)
        if event is None:
            raise not_found(f"ไม่พบเหตุการณ์ {body.event_id}")
    return {"questions": assistant.suggestions(df, event)}


# --- reports ----------------------------------------------------------------------

@app.post("/api/reports", response_model=Report, tags=["reports"])
def create_report(body: ReportRequest) -> dict[str, Any]:
    if not llm.is_configured():
        raise llm.LLMNotConfigured()
    return report.daily_report(body.date) if body.type == "daily" else report.weekly_report(body.date)


@app.get("/api/reports", response_model=list[ReportMeta], tags=["reports"])
def list_reports() -> list[dict[str, Any]]:
    return report.list_reports()


@app.get("/api/reports/{name}", response_model=Report, tags=["reports"])
def get_report(name: str) -> dict[str, Any]:
    found = report.get_report(name)
    if found is None:
        raise not_found(f"ไม่พบรายงาน {name}")
    return found


# --- detection & clips ------------------------------------------------------------

@app.post("/api/detect/run", response_model=DetectStatus, tags=["detection"])
def detect_run(_: Annotated[dict[str, Any] | None, Body()] = None) -> DetectStatus:
    return detect_runner.start()


@app.get("/api/detect/model-info", response_model=ModelInfo, tags=["detection"])
def detect_model_info() -> ModelInfo:
    """Weights path, class names and whether they were found locally or downloaded.
    Loads (and on first use downloads) the model."""
    from backend.detector import model_info  # lazy: keeps ultralytics out of API startup

    try:
        return ModelInfo(**model_info())
    except Exception as exc:  # noqa: BLE001 - surface download/load failures as a clean envelope
        logger.exception("Model load failed")
        raise ApiError(500, "INTERNAL_ERROR", f"โหลดโมเดลตรวจจับไม่สำเร็จ: {exc}") from exc


@app.get("/api/detect/status", response_model=DetectStatus, tags=["detection"])
def detect_status() -> DetectStatus:
    return detect_runner.get_status()


@app.get("/api/clips", response_model=list[ClipInfo], tags=["detection"])
def clips() -> list[dict[str, Any]]:
    folder = config.clips_dir()
    if not folder.is_dir():
        return []
    result = []
    for path in sorted(folder.iterdir(), key=lambda p: p.name):
        if not path.is_file() or path.suffix.lower() not in VIDEO_EXTENSIONS:
            continue
        stat = path.stat()
        parsed = parse_clip_filename(path.name, stat.st_mtime)
        dt: datetime = parsed["datetime"]
        result.append(
            {
                "name": path.name,
                "size": stat.st_size,
                "parsed": {
                    "camera": parsed["camera"],
                    "zone": parsed["zone"],
                    "datetime": dt.isoformat(timespec="seconds"),
                    "matched": parsed["matched"],
                },
            }
        )
    return result


@app.post("/api/clips/upload", response_model=UploadResult, tags=["detection"])
def upload_clips(files: Annotated[list[UploadFile], File()]) -> dict[str, list]:
    return uploads.save_uploads(files, config.clips_dir(), VIDEO_EXTENSIONS)


# --- regulations ------------------------------------------------------------------

@app.get("/api/regulations", response_model=list[RegulationDoc], tags=["regulations"])
def list_regulations() -> list[dict[str, Any]]:
    return [regulations.describe(p) for p in regulations.list_paths()]


@app.post("/api/regulations/upload", response_model=UploadResult, tags=["regulations"])
def upload_regulations(files: Annotated[list[UploadFile], File()]) -> dict[str, list]:
    return uploads.save_uploads(
        files, config.regulations_dir(), regulations.ALLOWED_EXTENSIONS, REGULATION_MAX_BYTES, regulations.EXCLUDED_NAMES
    )


@app.delete("/api/regulations/{name}", response_model=Deleted, tags=["regulations"])
def delete_regulation(name: str) -> dict[str, str]:
    path = regulations.find(name)
    if path is None:
        raise not_found(f"ไม่พบเอกสาร {name}")
    path.unlink()
    logger.info("Deleted regulation %s", name)
    return {"deleted": name}
