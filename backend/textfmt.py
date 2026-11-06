"""Small Thai/markdown formatting helpers shared by the assistant, reports and evaluation."""
from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Any

from backend.config import ZONE_LABELS_EN, zone_label

THAI_MONTHS = (
    "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
    "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม",
)
EN_MONTHS = (
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
)


def pct(rate: float) -> str:
    """0.4167 → "41.7%"."""
    return f"{rate * 100:.1f}%"


def hour_label(hour_key: str) -> str:
    """"14" → "14:00–14:59"."""
    return f"{hour_key}:00–{hour_key}:59"


def zone_name(zone: str, language: str = "th") -> str:
    """"crane" → "โซนเครน" / "Crane zone", "floor3" → "โซนชั้น 3" / "Floor 3 zone"; unknown zones stay raw."""
    if language == "en":
        label = ZONE_LABELS_EN.get(zone)
        return f"{label} zone" if label else zone
    label = zone_label(zone)
    return zone if label == zone else f"โซน{label}"


def zone_display(zone: str, language: str = "th") -> str:
    """"crane" → "โซนเครน (crane)" / "Crane zone (crane)"; unknown zones stay raw."""
    name = zone_name(zone, language)
    return zone if name == zone else f"{name} ({zone})"


def zone_table_label(zone: str, language: str = "th") -> str:
    """Bare zone label for table cells: "เครน" / "Crane"; unknown zones stay raw."""
    return ZONE_LABELS_EN.get(zone, zone) if language == "en" else zone_label(zone)


def thai_date(iso: str) -> str:
    """"2026-09-29" → "29 กันยายน 2569" (Buddhist era)."""
    year, month, day = (int(p) for p in iso.split("-"))
    return f"{day} {THAI_MONTHS[month - 1]} {year + 543}"


def en_date(iso: str) -> str:
    """"2026-09-29" → "29 September 2026" (Gregorian)."""
    year, month, day = (int(p) for p in iso.split("-"))
    return f"{day} {EN_MONTHS[month - 1]} {year}"


def long_date(iso: str, language: str = "th") -> str:
    return en_date(iso) if language == "en" else thai_date(iso)


def md_table(headers: Sequence[str], rows: Iterable[Sequence[Any]]) -> str:
    """Render a GitHub-flavoured markdown table."""
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    lines += ["| " + " | ".join(str(c) for c in row) + " |" for row in rows]
    return "\n".join(lines)


def aggregate_table(rows: list[dict[str, Any]], key_header: str, key_fmt=str, language: str = "th") -> str:
    """Markdown table for ``AggregateRow`` dicts."""
    columns = ["Events", "Violations", "Violation rate"] if language == "en" else ["เหตุการณ์", "ละเมิด", "อัตราละเมิด"]
    return md_table(
        [key_header, *columns],
        ([key_fmt(r["key"]), r["events"], r["violations"], pct(r["rate"])] for r in rows),
    )
