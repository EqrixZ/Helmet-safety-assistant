"""Background detection runs for ``POST /api/detect/run`` (one at a time).

``backend.detector`` is imported lazily inside the worker so the API keeps working
even when the heavy ML stack (ultralytics/torch/opencv) is unavailable.
"""
from __future__ import annotations

import logging
import threading
from datetime import datetime

from backend import config, data
from backend.models import DetectStatus

logger = logging.getLogger(__name__)

_status = DetectStatus()
_lock = threading.Lock()


class DetectionRunning(RuntimeError):
    """A detection run is already in progress."""


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _update(**fields: object) -> None:
    global _status
    with _lock:
        _status = _status.model_copy(update=fields)


def get_status() -> DetectStatus:
    with _lock:
        return _status.model_copy()


def _on_progress(processed: int, total: int, current_clip: str) -> None:
    _update(
        processed=processed,
        total=total,
        current_clip=current_clip or None,
        progress=round(processed / total, 4) if total else 0.0,
        message=f"กำลังประมวลผล {current_clip} ({processed}/{total})" if current_clip else f"ประมวลผลแล้ว {processed}/{total} คลิป",
    )


def _worker() -> None:
    try:
        from backend.detector import run_detection  # lazy: heavy ML deps

        df = run_detection(
            clips_dir=config.clips_dir(),
            out_csv=config.events_csv(),
            frames_dir=config.frames_dir(),
            conf=config.get_settings().conf_threshold,
            progress_cb=_on_progress,
        )
    except Exception as exc:  # noqa: BLE001 — surfaced to the UI via status
        logger.exception("Detection run failed")
        _update(state="error", finished_at=_now(), current_clip=None, message=f"การตรวจจับล้มเหลว: {exc}")
        return
    data.invalidate_cache()
    written = len(df)
    message = (
        f"ตรวจจับเสร็จสิ้น — บันทึก {written} เหตุการณ์ลงใน events.csv"
        if written
        else "ไม่พบคลิปวิดีโอในโฟลเดอร์ data/clips — กรุณาอัปโหลดคลิปก่อนเริ่มตรวจจับ"
    )
    with _lock:
        total = _status.total or written
    _update(
        state="done",
        progress=1.0,
        processed=total,
        total=total,
        current_clip=None,
        events_written=written,
        finished_at=_now(),
        message=message,
    )
    logger.info("Detection finished: %d events", written)


def start() -> DetectStatus:
    """Start a background run; raises :class:`DetectionRunning` if one is active."""
    global _status
    with _lock:
        if _status.state == "running":
            raise DetectionRunning()
        _status = DetectStatus(state="running", started_at=_now(), message="กำลังเตรียมโมเดลตรวจจับ…")
        snapshot = _status.model_copy()
    threading.Thread(target=_worker, name="detection", daemon=True).start()
    return snapshot
