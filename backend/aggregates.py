"""Pure pandas aggregations over a normalized events frame (see ``backend.data``).

Every function takes a DataFrame and returns plain Python data, so they are easy to
unit-test and reuse from the API, the assistant context, reports and evaluation.
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Literal

import pandas as pd

from backend.data import HOUR_COL, filter_events

GroupBy = Literal["zone", "camera", "hour", "day"]
SPARKLINE_DAYS = 14


def _rate(violations: int, events: int) -> float:
    return round(violations / events, 4) if events else 0.0


def _row(key: str, events: int, violations: int) -> dict[str, Any]:
    return {"key": key, "events": int(events), "violations": int(violations), "rate": _rate(violations, events)}


def _parse(d: str) -> date:
    return date.fromisoformat(d)


def date_span(start: str, end: str) -> list[str]:
    """Inclusive list of ISO dates from ``start`` to ``end`` (empty if start > end)."""
    first, last = _parse(start), _parse(end)
    return [(first + timedelta(days=i)).isoformat() for i in range((last - first).days + 1)]


def effective_range(df: pd.DataFrame, date_from: str | None, date_to: str | None) -> tuple[str | None, str | None]:
    """Fill missing bounds from the log's own min/max date."""
    lo = date_from or (str(df["date"].min()) if len(df) else None)
    hi = date_to or (str(df["date"].max()) if len(df) else None)
    return lo, hi


def group_by(
    df: pd.DataFrame, by: GroupBy, date_from: str | None = None, date_to: str | None = None
) -> list[dict[str, Any]]:
    """``AggregateRow`` list, ordered per CONTRACT §4 (``day`` includes zero days)."""
    df = filter_events(df, date_from, date_to)
    column = {"zone": "zone", "camera": "camera", "hour": HOUR_COL, "day": "date"}[by]
    grouped = df.groupby(column)["violation"].agg(["count", "sum"]) if len(df) else None
    counts: dict[str, tuple[int, int]] = (
        {str(k): (int(r["count"]), int(r["sum"])) for k, r in grouped.iterrows()} if grouped is not None else {}
    )

    if by == "day":
        lo, hi = effective_range(df, date_from, date_to)
        if lo is None or hi is None:
            return []
        return [_row(d, *counts.get(d, (0, 0))) for d in date_span(lo, hi)]
    rows = [_row(k, ev, vi) for k, (ev, vi) in counts.items()]
    if by == "hour":
        return sorted(rows, key=lambda r: r["key"])
    return sorted(rows, key=lambda r: (-r["violations"], -r["events"], r["key"]))


def top_n(df: pd.DataFrame, by: GroupBy, n: int = 3) -> list[dict[str, Any]]:
    """Top-``n`` keys by violations (ties → more events, then key); only keys with violations."""
    rows = [r for r in group_by(df, by) if r["violations"] > 0]
    rows.sort(key=lambda r: (-r["violations"], -r["events"], r["key"]))
    return rows[:n]


def _trend(current: float, previous: float) -> dict[str, Any]:
    change = round((current - previous) / previous * 100, 1) if previous else None
    return {"current": current, "previous": previous, "change_pct": change}


def _totals(df: pd.DataFrame) -> dict[str, Any]:
    events = len(df)
    violations = int(df["violation"].sum()) if events else 0
    return {"events": events, "violations": violations, "rate": _rate(violations, events)}


def previous_period(date_from: str, date_to: str) -> tuple[str, str]:
    """The period of equal length (in days) immediately preceding ``[date_from, date_to]``."""
    start, end = _parse(date_from), _parse(date_to)
    length = (end - start).days + 1
    return (start - timedelta(days=length)).isoformat(), (start - timedelta(days=1)).isoformat()


def compute_stats(
    df: pd.DataFrame,
    data_source: str,
    date_from: str | None = None,
    date_to: str | None = None,
) -> dict[str, Any]:
    """``Stats`` payload. ``df`` may be pre-filtered by zone/camera but not by date."""
    lo, hi = effective_range(df, date_from, date_to)
    current = filter_events(df, lo, hi)
    cur = _totals(current)
    if lo and hi:
        prev_lo, prev_hi = previous_period(lo, hi)
        prev = _totals(filter_events(df, prev_lo, prev_hi))
    else:
        prev = _totals(current.iloc[0:0])
    top_zone = top_n(current, "zone", 1)
    top_hour = top_n(current, "hour", 1)
    return {
        "from": lo,
        "to": hi,
        "total_events": cur["events"],
        "total_violations": cur["violations"],
        "violation_rate": cur["rate"],
        "total_persons": int(current["total_person"].sum()) if len(current) else 0,
        "total_no_hardhat": int(current["no_hardhat"].sum()) if len(current) else 0,
        "top_zone": {"key": top_zone[0]["key"], "violations": top_zone[0]["violations"]} if top_zone else None,
        "top_hour": {"key": top_hour[0]["key"], "violations": top_hour[0]["violations"]} if top_hour else None,
        "trend": {
            "events": _trend(cur["events"], prev["events"]),
            "violations": _trend(cur["violations"], prev["violations"]),
            "violation_rate": _trend(cur["rate"], prev["rate"]),
        },
        "data_source": data_source,
    }


def zone_summaries(df: pd.DataFrame, days: int = SPARKLINE_DAYS) -> list[dict[str, Any]]:
    """Zone rows (violations desc) with a per-day violation sparkline for the log's last ``days`` days."""
    rows = group_by(df, "zone")
    if not rows:
        return []
    end = _parse(str(df["date"].max()))
    span = [(end - timedelta(days=days - 1 - i)).isoformat() for i in range(days)]
    per_day = df[df["violation"]].groupby(["zone", "date"]).size()
    for row in rows:
        row["sparkline"] = [int(per_day.get((row["key"], d), 0)) for d in span]
    return rows
