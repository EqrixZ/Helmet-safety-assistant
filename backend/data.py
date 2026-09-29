"""Event-log loading, filtering and pagination (CONTRACT §3).

``data/events.csv`` (real) is preferred; ``data/events_sample.csv`` (sample) is the
fallback. The parsed frame is cached and reloaded when the file's mtime/size changes,
so a fresh detection run is picked up automatically.
"""
from __future__ import annotations

import logging
import math
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from backend import config
from backend.frame_utils import EVENT_COLUMNS
from backend.models import DataSource

logger = logging.getLogger(__name__)

INT_COLUMNS = ("hardhat", "no_hardhat", "total_person")
SORTABLE_COLUMNS = frozenset(EVENT_COLUMNS)
# Internal helper columns added on load (never exposed through the API).
DT_COL = "_dt"
HOUR_COL = "_hour"


@dataclass(frozen=True)
class EventLog:
    df: pd.DataFrame
    source: DataSource
    path: Path | None

    @property
    def date_min(self) -> str | None:
        return str(self.df["date"].min()) if len(self.df) else None

    @property
    def date_max(self) -> str | None:
        return str(self.df["date"].max()) if len(self.df) else None


_cache: dict[tuple[str, int, int], EventLog] = {}
_cache_lock = threading.Lock()


def empty_frame() -> pd.DataFrame:
    """An empty, correctly-typed events frame."""
    return normalize(pd.DataFrame({c: pd.Series(dtype=object) for c in EVENT_COLUMNS}))


def normalize(raw: pd.DataFrame) -> pd.DataFrame:
    """Coerce CSV strings into contract types and add helper columns."""
    df = raw.copy()
    for col in EVENT_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    df = df[EVENT_COLUMNS]
    for col in ("event_id", "datetime", "date", "time", "camera", "zone", "clip", "frame_path"):
        df[col] = df[col].fillna("").astype(str).str.strip()
    df["zone"] = df["zone"].str.lower()
    for col in INT_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    df["max_conf"] = pd.to_numeric(df["max_conf"], errors="coerce").fillna(0.0).astype(float)
    df["violation"] = df["violation"].astype(str).str.strip().str.lower().isin(["true", "1", "yes"])
    # Logs written before temporal voting lack these: max = the stored count, ratio unknown.
    raw_max = pd.to_numeric(df["no_hardhat_max"], errors="coerce")
    df["no_hardhat_max"] = raw_max.fillna(df["no_hardhat"]).astype(int)
    df["no_hardhat_ratio"] = pd.to_numeric(df["no_hardhat_ratio"], errors="coerce")
    df[DT_COL] = pd.to_datetime(df["datetime"], errors="coerce")
    df = df[df[DT_COL].notna()].copy()
    df["date"] = df[DT_COL].dt.strftime("%Y-%m-%d")
    df["time"] = df[DT_COL].dt.strftime("%H:%M")
    df[HOUR_COL] = df[DT_COL].dt.strftime("%H")
    return df.sort_values([DT_COL, "event_id"]).reset_index(drop=True)


def _read_csv(path: Path) -> pd.DataFrame:
    try:
        raw = pd.read_csv(path, dtype=str, keep_default_na=False)
    except pd.errors.EmptyDataError:
        logger.warning("%s is empty", path)
        return empty_frame()
    return normalize(raw)


def _has_rows(path: Path) -> bool:
    """True if the CSV has at least one data row beyond the header."""
    with path.open(encoding="utf-8", errors="ignore") as f:
        return sum(1 for line, _ in zip(f, range(2)) if line.strip()) >= 2


def resolve_log_path() -> tuple[Path | None, DataSource]:
    real = config.events_csv()
    if real.is_file() and _has_rows(real):
        return real, "real"
    sample = config.sample_events_csv()
    return (sample if sample.is_file() else None), "sample"


def load_events() -> EventLog:
    """Return the current event log, re-reading the CSV only if it changed."""
    path, source = resolve_log_path()
    if path is None:
        return EventLog(empty_frame(), source, None)
    stat = path.stat()
    key = (str(path), stat.st_mtime_ns, stat.st_size)
    with _cache_lock:
        cached = _cache.get(key)
        if cached is not None:
            return cached
        log = EventLog(_read_csv(path), source, path)
        _cache.clear()
        _cache[key] = log
        logger.info("Loaded %d events from %s (%s)", len(log.df), path, source)
        return log


def invalidate_cache() -> None:
    with _cache_lock:
        _cache.clear()


def filter_events(
    df: pd.DataFrame,
    date_from: str | None = None,
    date_to: str | None = None,
    zone: str | None = None,
    camera: str | None = None,
    violation: bool | None = None,
) -> pd.DataFrame:
    """Apply inclusive date range and exact-match filters."""
    mask = pd.Series(True, index=df.index)
    if date_from:
        mask &= df["date"] >= date_from
    if date_to:
        mask &= df["date"] <= date_to
    if zone:
        mask &= df["zone"] == zone.lower()
    if camera:
        mask &= df["camera"] == camera
    if violation is not None:
        mask &= df["violation"] == violation
    return df[mask]


def sort_events(df: pd.DataFrame, sort: str = "datetime", order: str = "desc") -> pd.DataFrame:
    """Stable sort by a contract column (``datetime`` sorts chronologically)."""
    if sort not in SORTABLE_COLUMNS:
        raise ValueError(sort)
    key = DT_COL if sort == "datetime" else sort
    return df.sort_values([key, "event_id"], ascending=order == "asc", kind="mergesort")


def event_to_dict(row: dict[str, Any]) -> dict[str, Any]:
    """Project a frame row onto the ``Event`` contract type."""
    out = {c: row[c] for c in EVENT_COLUMNS}
    out["hardhat"] = int(out["hardhat"])
    out["no_hardhat"] = int(out["no_hardhat"])
    out["total_person"] = int(out["total_person"])
    out["violation"] = bool(out["violation"])
    out["max_conf"] = round(float(out["max_conf"]), 3)
    out["no_hardhat_max"] = int(out["no_hardhat_max"])
    ratio = out["no_hardhat_ratio"]
    out["no_hardhat_ratio"] = None if pd.isna(ratio) else round(float(ratio), 3)
    out["frame_url"] = f"/api/frames/{out['frame_path']}" if out["frame_path"] else None
    return out


def to_events(df: pd.DataFrame) -> list[dict[str, Any]]:
    return [event_to_dict(r) for r in df.to_dict(orient="records")]


def paginate(df: pd.DataFrame, page: int, size: int) -> dict[str, Any]:
    """Slice a frame into a ``Paginated<Event>`` payload (page is 1-based)."""
    total = len(df)
    pages = math.ceil(total / size) if total else 0
    start = (page - 1) * size
    return {
        "items": to_events(df.iloc[start : start + size]),
        "total": total,
        "page": page,
        "size": size,
        "pages": pages,
    }


def get_event(df: pd.DataFrame, event_id: str) -> dict[str, Any] | None:
    match = df[df["event_id"] == event_id]
    return event_to_dict(match.iloc[0].to_dict()) if len(match) else None
