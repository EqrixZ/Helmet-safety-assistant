"""Small Thai/markdown formatting helpers shared by the assistant, reports and evaluation."""
from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Any

from backend.config import zone_label

THAI_MONTHS = (
    "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
    "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม",
)


def pct(rate: float) -> str:
    """0.4167 → "41.7%"."""
    return f"{rate * 100:.1f}%"


def hour_label(hour_key: str) -> str:
    """"14" → "14:00–14:59"."""
    return f"{hour_key}:00–{hour_key}:59"


def zone_name(zone: str) -> str:
    """"crane" → "โซนเครน", "floor3" → "โซนชั้น 3"; unknown zones stay raw."""
    label = zone_label(zone)
    return zone if label == zone else f"โซน{label}"


def zone_display(zone: str) -> str:
    """"crane" → "โซนเครน (crane)"; unknown zones stay raw."""
    name = zone_name(zone)
    return zone if name == zone else f"{name} ({zone})"


def thai_date(iso: str) -> str:
    """"2026-09-29" → "29 กันยายน 2569" (Buddhist era)."""
    year, month, day = (int(p) for p in iso.split("-"))
    return f"{day} {THAI_MONTHS[month - 1]} {year + 543}"


def md_table(headers: Sequence[str], rows: Iterable[Sequence[Any]]) -> str:
    """Render a GitHub-flavoured markdown table."""
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    lines += ["| " + " | ".join(str(c) for c in row) + " |" for row in rows]
    return "\n".join(lines)


def aggregate_table(rows: list[dict[str, Any]], key_header: str, key_fmt=str) -> str:
    """Markdown table for ``AggregateRow`` dicts."""
    return md_table(
        [key_header, "เหตุการณ์", "ละเมิด", "อัตราละเมิด"],
        ([key_fmt(r["key"]), r["events"], r["violations"], pct(r["rate"])] for r in rows),
    )
