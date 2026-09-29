"""Factual-accuracy evaluation of the safety assistant.

Generates questions with pandas ground truth from the loaded event log, asks the
assistant through the same context path as chat (non-streaming), and checks whether the
expected number/label appears in the answer.

Usage: ``python -m backend.evaluate [--mock] [--n 15]``. The mock LLM is used when
``--mock`` is passed or ``LLM_API_KEY`` is not set; it answers by pattern-matching the
question against the precomputed aggregates, so the pipeline always runs end-to-end.
"""
from __future__ import annotations

import argparse
import logging
import re
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Literal

import pandas as pd

from backend import aggregates, assistant, config, data, llm
from backend.config import ZONE_LABELS, zone_label
from backend.models import ChatMessage
from backend.textfmt import hour_label, pct

logger = logging.getLogger(__name__)

CheckKind = Literal["number", "percent", "hour", "label"]
THAI_DIGITS = str.maketrans("๐๑๒๓๔๕๖๗๘๙", "0123456789")
NOT_FOUND_ANSWER = "ขออภัย ไม่พบข้อมูลนี้ในบันทึกหรือเอกสารที่มีอยู่"


@dataclass
class EvalCase:
    question: str
    expected: str
    kind: CheckKind
    accept: list[str] = field(default_factory=list)  # alternatives for label/hour checks


# --- question generation -------------------------------------------------------------

def _tied_top(rows: list[dict]) -> list[dict]:
    """All rows sharing the maximum violation count."""
    best = max((r["violations"] for r in rows), default=0)
    return [r for r in rows if r["violations"] == best and best > 0]


def _zone_phrase(key: str) -> str:
    """"crane" → "โซนเครน (crane)", "scaffold" → "โซนนั่งร้าน (scaffold)" (no doubled "โซน")."""
    label = zone_label(key)
    return f"{label if label.startswith('โซน') else 'โซน' + label} ({key})"


def generate_cases(df: pd.DataFrame) -> list[EvalCase]:
    """Deterministic questions + ground truth from the log, ordered for variety."""
    if not len(df):
        return []
    stats = aggregates.compute_stats(df, "real")
    zones = aggregates.group_by(df, "zone")
    cams = aggregates.group_by(df, "camera")
    days = [r for r in aggregates.group_by(df, "day") if r["events"]]
    cases = [
        EvalCase("ในบันทึกมีเหตุการณ์ (คลิป) ทั้งหมดกี่รายการ?", str(stats["total_events"]), "number"),
        EvalCase("มีเหตุการณ์ที่ละเมิดการสวมหมวกนิรภัยทั้งหมดกี่ครั้ง?", str(stats["total_violations"]), "number"),
        EvalCase("อัตราการละเมิดการสวมหมวกนิรภัยโดยรวมคิดเป็นกี่เปอร์เซ็นต์?", f"{stats['violation_rate'] * 100:.1f}", "percent"),
    ]
    if top_zones := _tied_top(zones):
        accept = [a for r in top_zones for a in (r["key"], zone_label(r["key"]))]
        cases.append(EvalCase("โซนไหนมีการละเมิดมากที่สุด?", " / ".join(r["key"] for r in top_zones), "label", accept))
    if top_hours := _tied_top(aggregates.group_by(df, "hour")):
        expected = " / ".join(hour_label(r["key"]) for r in top_hours)
        cases.append(EvalCase("ช่วงชั่วโมงไหนของวันที่มีการละเมิดมากที่สุด?", expected, "hour", [r["key"] for r in top_hours]))
    if top_cams := _tied_top(cams):
        cases.append(EvalCase("กล้องตัวไหนตรวจพบการละเมิดมากที่สุด?", " / ".join(r["key"] for r in top_cams), "label", [r["key"] for r in top_cams]))
    cases.append(EvalCase("รวมแล้วตรวจพบคนที่ไม่สวมหมวกนิรภัยกี่คน?", str(stats["total_no_hardhat"]), "number"))
    busiest_day = max(days, key=lambda r: (r["violations"], r["key"]))
    for day in dict.fromkeys([days[-1]["key"], busiest_day["key"], days[0]["key"]]):
        row = next(r for r in days if r["key"] == day)
        cases.append(EvalCase(f"วันที่ {day} มีการละเมิดการสวมหมวกนิรภัยกี่ครั้ง?", str(row["violations"]), "number"))
    for row in sorted(zones, key=lambda r: r["key"]):
        cases.append(EvalCase(f"{_zone_phrase(row['key'])} มีการละเมิดกี่ครั้ง?", str(row["violations"]), "number"))
    if zones:
        busiest_zone = max(zones, key=lambda r: (r["events"], r["key"]))
        cases.append(EvalCase(f"{_zone_phrase(busiest_zone['key'])} มีเหตุการณ์ทั้งหมดกี่รายการ?", str(busiest_zone["events"]), "number"))
    for row in sorted(cams, key=lambda r: r["key"])[:2]:
        cases.append(EvalCase(f"กล้อง {row['key']} ตรวจพบการละเมิดกี่ครั้ง?", str(row["violations"]), "number"))
    return cases


# --- answer checking -----------------------------------------------------------------

def normalize(text: str) -> str:
    """Thai digits → Arabic, drop thousands separators, lowercase."""
    text = text.translate(THAI_DIGITS)
    return re.sub(r"(?<=\d),(?=\d{3})", "", text).lower()


def _strip_non_answer_numbers(text: str) -> str:
    """Remove dates, times, IDs and zone/camera names whose digits are not answers."""
    patterns = [
        r"\d{4}-\d{2}-\d{2}",
        r"\d{1,2}[:.]\d{2}(\s*[–-]\s*\d{1,2}[:.]\d{2})?",
        r"evt-\d+",
        r"[a-z]+\d+",
        r"ชั้น\s*\d+",
        r"\d{1,2}\s+(มกราคม|กุมภาพันธ์|มีนาคม|เมษายน|พฤษภาคม|มิถุนายน|กรกฎาคม|สิงหาคม|กันยายน|ตุลาคม|พฤศจิกายน|ธันวาคม)\s+\d{4}",
    ]
    for p in patterns:
        text = re.sub(p, " ", text)
    return text


def _numbers(text: str) -> list[float]:
    return [float(n) for n in re.findall(r"\d+(?:\.\d+)?", text)]


def is_correct(case: EvalCase, answer: str) -> bool:
    text = normalize(answer)
    if case.kind == "label":
        return any(a.lower() in text for a in case.accept)
    if case.kind == "hour":
        hours = {int(h) for h in re.findall(r"(?<!\d)(\d{1,2})(?:[:.]\d{2}|\s*น\.)", text)}
        return any(int(h) in hours for h in case.accept)
    nums = _numbers(_strip_non_answer_numbers(text))
    expected = float(case.expected)
    tolerance = 0.1 if case.kind == "percent" else 0.0
    return any(abs(n - expected) <= tolerance for n in nums)


# --- mock LLM ------------------------------------------------------------------------

class MockLLM:
    """Answers factual questions by pattern-matching against precomputed aggregates."""

    def __init__(self, df: pd.DataFrame) -> None:
        self.df = df
        self.stats = aggregates.compute_stats(df, "real")

    def complete(self, messages: list[dict[str, str]]) -> str:
        question = messages[-1]["content"]
        for handler in (self._by_date, self._by_zone, self._by_camera, self._top, self._totals):
            if (answer := handler(question)) is not None:
                return answer
        return NOT_FOUND_ANSWER

    def _by_date(self, q: str) -> str | None:
        m = re.search(r"\d{4}-\d{2}-\d{2}", q)
        if not m:
            return None
        day = data.filter_events(self.df, m.group(), m.group())
        return f"วันที่ {m.group()} มีการละเมิด {int(day['violation'].sum())} ครั้ง จากทั้งหมด {len(day)} เหตุการณ์"

    def _by_zone(self, q: str) -> str | None:
        zone = next((z for z in sorted(self.df["zone"].unique()) if z in q or ZONE_LABELS.get(z, "\0") in q), None)
        if zone is None:
            return None
        rows = data.filter_events(self.df, zone=zone)
        if "เหตุการณ์ทั้งหมด" in q:
            return f"โซน{zone_label(zone)} มีเหตุการณ์ทั้งหมด {len(rows)} รายการ"
        return f"โซน{zone_label(zone)} มีการละเมิด {int(rows['violation'].sum())} ครั้ง"

    def _by_camera(self, q: str) -> str | None:
        m = re.search(r"cam\d+", q)
        if not m:
            return None
        rows = data.filter_events(self.df, camera=m.group())
        return f"กล้อง {m.group()} ตรวจพบการละเมิด {int(rows['violation'].sum())} ครั้ง"

    def _top(self, q: str) -> str | None:
        if "โซนไหน" in q and (top := aggregates.top_n(self.df, "zone", 1)):
            return f"โซนที่มีการละเมิดมากที่สุดคือ โซน{zone_label(top[0]['key'])} ({top[0]['violations']} ครั้ง)"
        if "กล้อง" in q and "ไหน" in q and (top := aggregates.top_n(self.df, "camera", 1)):
            return f"กล้อง {top[0]['key']} ตรวจพบการละเมิดมากที่สุด ({top[0]['violations']} ครั้ง)"
        if ("ชั่วโมงไหน" in q or "ช่วงเวลาไหน" in q) and (top := aggregates.top_n(self.df, "hour", 1)):
            return f"ช่วงเวลา {hour_label(top[0]['key'])} มีการละเมิดมากที่สุด ({top[0]['violations']} ครั้ง)"
        return None

    def _totals(self, q: str) -> str | None:
        if "อัตรา" in q or "เปอร์เซ็นต์" in q:
            return f"อัตราการละเมิดโดยรวมคือ {pct(self.stats['violation_rate'])}"
        if "ละเมิด" in q and "ทั้งหมด" in q:
            return f"มีเหตุการณ์ละเมิดทั้งหมด {self.stats['total_violations']} ครั้ง"
        if "เหตุการณ์" in q and "ทั้งหมด" in q:
            return f"มีเหตุการณ์ทั้งหมด {self.stats['total_events']} รายการ"
        return None


# --- runner --------------------------------------------------------------------------

RESULT_COLUMNS = [
    "question", "expected", "answer", "correct", "provider", "model", "retries", "waited_s", "elapsed_s",
    "token_estimate", "prompt_tokens",
]


def run(n: int, use_mock: bool, on_result: Callable[[int, dict[str, Any]], None] | None = None) -> pd.DataFrame:
    """Ask the questions one at a time. Real LLM calls go through llm.py, so the LLM_RPM
    throttle, 429/503 retries and the fallback provider all apply."""
    log = data.load_events()
    cases = generate_cases(log.df)[:n]
    mock = MockLLM(log.df) if use_mock else None
    rows: list[dict[str, Any]] = []
    for i, case in enumerate(cases, 1):
        messages, sources = assistant.build_messages([ChatMessage(role="user", content=case.question)], log.df, log.source)
        started = time.perf_counter()
        info = llm.CallInfo(provider=None, model="mock" if mock else None)
        try:
            if mock:
                answer = mock.complete(messages)
            else:
                answer, info = llm.complete_with_info(messages)
        except llm.LLMError as exc:
            answer = f"ERROR: {exc.message}"
            info = exc.info or info
        row = {
            "question": case.question, "expected": case.expected, "answer": answer,
            "correct": is_correct(case, answer),
            "provider": "mock" if mock else (info.provider or "?") + (" (error)" if answer.startswith("ERROR:") else ""),
            "model": info.model or "",
            "retries": info.retries, "waited_s": round(info.waited_s, 1),
            "elapsed_s": round(time.perf_counter() - started, 1),
            "token_estimate": sources["token_estimate"], "prompt_tokens": info.prompt_tokens,
        }
        rows.append(row)
        if on_result:
            on_result(i, row)
    return pd.DataFrame(rows, columns=RESULT_COLUMNS)


def _short(text: str, width: int) -> str:
    text = " ".join(text.split())
    return text if len(text) <= width else text[: width - 1] + "…"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate the safety assistant's factual accuracy.")
    parser.add_argument("--mock", action="store_true", help="use the pattern-matching mock LLM")
    parser.add_argument("--n", type=int, default=15, help="number of questions (default 15)")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")

    use_mock = args.mock or not llm.is_configured()
    settings = config.get_settings()
    if use_mock:
        mode = "mock"
    else:
        rpm = f"{settings.llm_rpm:g} RPM" if settings.llm_rpm > 0 else "no throttle"
        fb = f", fallback {settings.llm_fallback_model}" if llm.fallback_configured() else ""
        mode = f"LLM {settings.llm_model}, {rpm}{fb}"
    print(f"\nประเมินผู้ช่วย ({mode}) — ถามทีละข้อ\n", flush=True)

    def show(i: int, r: dict[str, Any]) -> None:
        mark = "PASS" if r["correct"] else "FAIL"
        meta = f"{r['provider']}, retries {r['retries']}, {r['elapsed_s']:.1f}s"
        print(f"{i:>2}. [{mark}] {_short(r['question'], 60)}  ({meta})")
        print(f"      expected: {r['expected']} | answer: {_short(r['answer'], 90)}", flush=True)

    started = time.perf_counter()
    results = run(args.n, use_mock, on_result=show)
    if results.empty:
        print("ไม่มีข้อมูลเหตุการณ์สำหรับการประเมิน")
        return 0
    elapsed = time.perf_counter() - started
    correct = int(results["correct"].sum())
    errors = int(results["answer"].str.startswith("ERROR:").sum())
    print(f"\nAccuracy: {correct}/{len(results)} = {correct / len(results):.1%}"
          + (f"  ({errors} call(s) failed)" if errors else ""))
    print(f"Elapsed: {elapsed:.1f}s  (retries {int(results['retries'].sum())}, "
          f"waiting on throttle/backoff {results['waited_s'].sum():.1f}s)")

    out = config.eval_results_csv()
    out.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(out, index=False, encoding="utf-8")
    print(f"Saved: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
