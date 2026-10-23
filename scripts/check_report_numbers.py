"""Check every number in a generated report against the pandas aggregates for its period.

For each report in ``data/reports/`` (or the files given on the command line):
  1. the period comes from the file name (``report_daily_<date>_…`` = that day,
     ``report_weekly_<start>_…`` = 7 days from start);
  2. every line is tagged ``table`` (markdown table built by pandas), ``template`` (event blocks
     filled by code), ``header`` or ``narrative`` (text written by the LLM);
  3. dates, times, event IDs, camera/zone names, years, list markers and ordinals are removed, clause references
     ("ข้อปฏิบัติตัวอย่าง 4", "หมวด 2", "ข้อ 3") are recorded separately, and each remaining number
     is matched against the period's aggregates (totals, per zone/hour/day/camera, notable events,
     previous period and change). A number matches when it equals an aggregate of the same unit
     (percent, confidence or count) rounded to the decimals written in the report; signs are
     ignored, so "-5.7" matches a drop of 5.7.

The check is by value only: a match says the number exists among the aggregates, not that the
sentence uses it for the right quantity, so unmatched and narrative rows should still be read.

Writes ``data/report_check.csv``: report, section, source, number, context, matched, aggregate_key.

Usage: ``python scripts/check_report_numbers.py [REPORT.md ...]``
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from backend import aggregates, config, data  # noqa: E402
from backend.data import filter_events  # noqa: E402

THAI_DIGITS = str.maketrans("๐๑๒๓๔๕๖๗๘๙", "0123456789")
THAI_MONTHS = (
    "มกราคม|กุมภาพันธ์|มีนาคม|เมษายน|พฤษภาคม|มิถุนายน|กรกฎาคม|สิงหาคม|กันยายน|ตุลาคม|พฤศจิกายน|ธันวาคม|"
    r"ม\.ค\.|ก\.พ\.|มี\.ค\.|เม\.ย\.|พ\.ค\.|มิ\.ย\.|ก\.ค\.|ส\.ค\.|ก\.ย\.|ต\.ค\.|พ\.ย\.|ธ\.ค\."
)
# Removed before numbers are read: their digits are not quantities.
NON_QUANTITY = [
    r"^\s*\d+\.\s",                       # numbered-list marker
    r"ครั้งที่\s*\d+(\s*-\s*\d+)?",       # ordinal ("ครั้งที่ 2-4" quotes the regulation's steps)
    r"`[^`]*`",
    r"\d{4}-\d{2}-\d{2}",
    rf"\d{{1,2}}(\s*-\s*\d{{1,2}})?\s*({THAI_MONTHS})(\s*\d{{4}})?",
    r"\d{1,2}:\d{2}(\s*[–-]\s*\d{1,2}:\d{2})?(\s*น\.)?",
    r"\d{1,2}\.\d{2}(\s*[–-]\s*\d{1,2}\.\d{2})?\s*น\.",
    r"evt-\d+",
    r"\b[a-z]+\d+\b",
    r"ชั้น\s*\d+",
    r"\b(19|20)\d{2}\b|\b25\d{2}\b",
]
CLAUSE = re.compile(r"(ข้อปฏิบัติตัวอย่าง|ข้อ|หมวด)\s*(\d+)")
NUMBER = re.compile(r"(\d+(?:\.\d+)?)\s*(%|จุดร้อยละ|เปอร์เซ็นต์|percent)?")


def normalize(text: str) -> str:
    """Thai digits → Arabic, non-breaking/minus dashes → "-", no thousands separators, lowercase."""
    text = text.translate(THAI_DIGITS).replace("‑", "-").replace("−", "-")
    return re.sub(r"(?<=\d),(?=\d{3})", "", text).lower()


def strip_non_quantities(text: str) -> str:
    for pattern in NON_QUANTITY:
        text = re.sub(pattern, " ", text)
    return text


def clause_refs(text: str) -> list[tuple[str, int]]:
    return [(kind, int(n)) for kind, n in CLAUSE.findall(normalize(text))]


def extract_numbers(text: str) -> list[tuple[str, str]]:
    """``(number, unit)`` for each quantity in one line, as written (clause numbers excluded).
    unit is "pct" (followed by %, จุดร้อยละ, …), "conf" (a fraction like 0.73) or "count"."""
    text = CLAUSE.sub(" ", strip_non_quantities(normalize(text)))
    out = []
    for number, pct_word in NUMBER.findall(text):
        unit = "pct" if pct_word else "conf" if number.startswith("0.") else "count"
        out.append((number, unit))
    return out


def unit_of(key: str) -> str:
    if key.endswith("max_conf"):
        return "conf"
    return "pct" if "rate" in key or key.startswith("change_pct") else "count"


def matches(written: str, value: float) -> bool:
    """``written`` equals |value| rounded to the decimals shown in the report."""
    decimals = len(written.split(".")[1]) if "." in written else 0
    return round(abs(float(value)), decimals) == round(float(written), decimals)


def line_source(line: str) -> str:
    s = line.strip()
    if s.startswith("|"):
        return "table"
    if s.startswith("### ") or "![" in s or "· คลิป `" in s or "· clip `" in s:
        return "template"
    if s.startswith("# ") or s.startswith("**") or s == "---" or s.startswith("รายงานนี้"):
        return "header"
    return "narrative"


def period_of(path: Path) -> tuple[str, str]:
    m = re.match(r"report_(daily|weekly)_(\d{4}-\d{2}-\d{2})", path.name)
    if not m:
        raise ValueError(f"cannot read the period from {path.name}")
    start = date.fromisoformat(m.group(2))
    end = start + timedelta(days=6) if m.group(1) == "weekly" else start
    return start.isoformat(), end.isoformat()


def truth_values(df: pd.DataFrame, lo: str, hi: str) -> list[tuple[str, float]]:
    """Every aggregate a report for [lo, hi] can legitimately quote."""
    out: list[tuple[str, float]] = []
    changes: list[tuple[str, float]] = []  # previous period and change go last (key order = label shown)
    s = aggregates.compute_stats(df, "real", lo, hi)
    out += [
        ("total_events", s["total_events"]), ("total_violations", s["total_violations"]),
        ("violation_rate_pct", s["violation_rate"] * 100), ("total_persons", s["total_persons"]),
        ("total_no_hardhat", s["total_no_hardhat"]),
    ]
    for key, t in s["trend"].items():
        scale = 100 if key == "violation_rate" else 1
        changes += [(f"prev_{key}", t["previous"] * scale), (f"delta_{key}", (t["current"] - t["previous"]) * scale)]
        if t["change_pct"] is not None:
            changes.append((f"change_pct_{key}", t["change_pct"]))
    prev_lo, prev_hi = aggregates.previous_period(lo, hi)
    for by in ("zone", "hour", "day", "camera"):
        prev = {r["key"]: r for r in aggregates.group_by(df, by, prev_lo, prev_hi)}
        for r in aggregates.group_by(df, by, lo, hi):
            if not r["events"]:
                continue
            k = f"{by}:{r['key']}"
            out += [(f"{k}.events", r["events"]), (f"{k}.violations", r["violations"]), (f"{k}.rate_pct", r["rate"] * 100)]
            if by == "zone" and r["key"] in prev:
                changes += [(f"prev_{k}.violations", prev[r["key"]]["violations"]),
                            (f"delta_{k}.violations", r["violations"] - prev[r["key"]]["violations"])]
    period = filter_events(df, lo, hi)
    for e in period[period["violation"]].to_dict("records"):
        k = e["event_id"]
        out += [(f"{k}.no_hardhat", e["no_hardhat"]), (f"{k}.total_person", e["total_person"]),
                (f"{k}.hardhat", e["hardhat"]), (f"{k}.max_conf", e["max_conf"])]
    return out + changes


def regulation_clauses() -> set[tuple[str, int]]:
    found: set[tuple[str, int]] = set()
    for path in sorted(config.regulations_dir().glob("*.md")):
        for kind, n in clause_refs(path.read_text(encoding="utf-8")):
            found.add((kind, n))
            if kind == "ข้อปฏิบัติตัวอย่าง":
                found.add(("ข้อ", n))
    return found


def check_report(path: Path, df: pd.DataFrame, clauses: set[tuple[str, int]]) -> list[dict]:
    lo, hi = period_of(path)
    truth = truth_values(df, lo, hi)
    rows: list[dict] = []
    section = ""
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            section = line[3:].strip()
            continue
        if not line.strip() or line.startswith("![") or set(line.strip()) <= set("|-: "):
            continue
        source = line_source(line)
        context = " ".join(line.split())[:120]
        for kind, n in clause_refs(line):
            rows.append({"report": path.name, "section": section, "source": "clause", "number": f"{kind} {n}",
                         "context": context, "matched": (kind, n) in clauses, "aggregate_key": "regulations"})
        for written, unit in extract_numbers(line):
            key = next((k for k, v in truth if unit_of(k) == unit and matches(written, v)), "")
            rows.append({"report": path.name, "section": section, "source": source, "number": written,
                         "context": context, "matched": bool(key), "aggregate_key": key})
    return rows


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Compare the numbers in reports with the pandas aggregates.")
    ap.add_argument("reports", nargs="*", type=Path)
    ap.add_argument("--out", type=Path, default=None, help="output CSV (default DATA_DIR/report_check.csv)")
    args = ap.parse_args(argv)

    paths = args.reports or sorted(config.reports_dir().glob("report_*.md"))
    log = data.load_events()
    clauses = regulation_clauses()
    rows = [r for p in paths for r in check_report(p, log.df, clauses)]
    out = args.out or config.data_dir() / "report_check.csv"
    result = pd.DataFrame(rows, columns=["report", "section", "source", "number", "context", "matched", "aggregate_key"])
    result.to_csv(out, index=False, encoding="utf-8")

    if result.empty:
        print("ไม่พบตัวเลขในรายงาน")
        return 0
    summary = result.groupby(["report", "source"])["matched"].agg(matched="sum", total="count").astype(int)
    print(summary.to_string())
    for report, g in result[~result["matched"]].groupby("report"):
        print(f"\nไม่ตรง ({report}):")
        for r in g.itertuples():
            print(f"  [{r.source}] {r.number}  ← {r.context}")
    print(f"\nSaved: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
