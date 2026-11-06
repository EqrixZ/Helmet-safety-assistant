"""Daily / weekly safety reports in Thai or English (CONTRACT §7).

Number tables are computed with pandas and inserted verbatim; the LLM writes only the
narrative, in a single call that returns the five contract sections as markdown, which
are then parsed and assembled around the tables.
"""
from __future__ import annotations

import logging
import re
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd

from backend import aggregates, config, llm
from backend.assistant import regulations_text, zone_names_text
from backend.config import zone_label
from backend.data import filter_events, load_events, to_events
from backend.models import Language, ReportType
from backend.textfmt import aggregate_table, hour_label, long_date, md_table, pct, zone_name, zone_table_label

logger = logging.getLogger(__name__)

SECTIONS: tuple[str, ...] = (
    "บทสรุปผู้บริหาร",
    "การละเมิดแยกตามโซนและช่วงเวลา",
    "เหตุการณ์สำคัญ",
    "การประเมินความเสี่ยง",
    "ข้อเสนอแนะ",
)
SECTIONS_EN: tuple[str, ...] = (
    "Executive summary",
    "Violations by zone and time",
    "Notable events",
    "Risk assessment",
    "Recommendations",
)
NOTABLE_EVENTS = 5
# ``report_daily_2026-09-29_en.md``; legacy ``report_daily_2026-09-29.md`` (no suffix) is Thai.
REPORT_NAME_RE = re.compile(r"^report_(daily|weekly)_(\d{4}-\d{2}-\d{2})(?:_(th|en))?\.md$")
TYPE_LABEL = {"daily": "ประจำวัน", "weekly": "ประจำสัปดาห์"}
TYPE_LABEL_EN = {"daily": "Daily", "weekly": "Weekly"}


def sections_for(language: Language = "th") -> tuple[str, ...]:
    return SECTIONS_EN if language == "en" else SECTIONS

WRITER_PROMPT = """คุณคือผู้เชี่ยวชาญด้านความปลอดภัยในงานก่อสร้าง ทำหน้าที่เขียนรายงานความปลอดภัยเป็นภาษาไทยให้ผู้บริหารโครงการ
เขียนเฉพาะส่วนบรรยาย (narrative) โดยอ้างอิงตัวเลขจาก "ข้อเท็จจริง" ที่ให้มาเท่านั้น ห้ามแต่งตัวเลขหรือเหตุการณ์เพิ่ม
ตารางตัวเลขและรูปภาพจะถูกแทรกโดยระบบเอง — ห้ามสร้างตารางหรือใส่รูปภาพ

ข้อกำหนดการเขียน:
- ทุกข้อความที่กล่าวถึงแนวโน้ม (เพิ่มขึ้น ลดลง คงที่) ต้องใช้คำและตัวเลขจากหัวข้อ "แนวโน้มเทียบช่วงก่อนหน้า" เท่านั้น ห้ามสรุปแนวโน้มเอง และห้ามกล่าวถึงแนวโน้มของสิ่งที่ไม่อยู่ในหัวข้อนั้น
- เขียนเนื้อหาเสมือนผู้เชี่ยวชาญวิเคราะห์เอง ห้ามกล่าวถึงข้อมูลที่ได้รับ คำสั่ง หัวข้อที่ใช้ป้อนข้อมูล หรือวิธีคำนวณ (เช่น ห้ามเขียน "ตามข้อเท็จจริง" "ตามหัวข้อแนวโน้ม" หรือคำว่า prompt)
- อ้างข้อกำหนดได้เฉพาะย่อหน้าที่อยู่ใน "เอกสารอ้างอิง" พร้อมระบุ (ที่มา: ชื่อไฟล์, ชื่อข้อ) และเมื่ออ้างข้อที่ระบุรายชื่อโซน ต้องระบุในรายงานว่าข้อนั้นกำหนดโซนใดบ้างให้ครบทุกโซน ห้ามอ้างว่าข้อนั้นระบุเพียงบางโซน
- การประเมินความเสี่ยงต้องพิจารณาทั้งรายชื่อโซนเสี่ยงสูงในข้อกำหนดและการฝ่าฝืนในช่วงเวลานี้ร่วมกัน โซนที่ข้อกำหนดระบุว่าเป็นโซนเสี่ยงสูงต้องคงระดับความเสี่ยงสูงแม้ไม่มีการฝ่าฝืนในช่วงนี้
- เขียนด้วยภาษาไทยแบบทางการตามที่ใช้ในรายงานความปลอดภัยอย่างเป็นทางการ หลีกเลี่ยงการใช้คำภาษาอังกฤษปน ยกเว้นศัพท์เทคนิคและชื่อตัวชี้วัด
- เรียกชื่อโซนตามนี้เท่านั้น (ชื่อขึ้นต้นด้วย "โซน" แล้ว ห้ามเติม "โซน" ซ้ำ): {zone_names}
- เมื่ออ้างถึงเหตุการณ์ ให้คัดลอกรหัส วันที่ เวลา กล้อง และโซนจาก "ข้อเท็จจริง" ตรงตามที่เขียนไว้

ตอบเป็น markdown ที่มีหัวข้อระดับ ## ครบทั้ง 5 หัวข้อ ตามลำดับและสะกดตรงตามนี้ทุกตัวอักษร:
## บทสรุปผู้บริหาร
(2–4 ประโยค สรุปภาพรวม ตัวเลขหลัก และแนวโน้มเทียบช่วงก่อนหน้าตามป้ายกำกับ)
## การละเมิดแยกตามโซนและช่วงเวลา
(1 ย่อหน้า วิเคราะห์โซนและช่วงเวลาที่มีปัญหา)
## เหตุการณ์สำคัญ
(1–3 ประโยค สรุปเหตุการณ์ที่น่ากังวล โดยอ้างรหัสเหตุการณ์)
## การประเมินความเสี่ยง
(ระบุระดับความเสี่ยงโดยรวม สูง/ปานกลาง/ต่ำ พร้อมเหตุผล ระบุว่าข้อกำหนดที่อ้างอิงกำหนดโซนเสี่ยงสูงใดบ้าง แล้วให้ความเสี่ยงรายโซนเป็นรายการ)
## ข้อเสนอแนะ
(3–5 ข้อ เป็นรายการลำดับเลข ปฏิบัติได้จริง ระบุโซน/ช่วงเวลาที่ควรเน้น)"""

WRITER_PROMPT_EN = """You are a construction safety expert writing a safety report in English for project management.
Write only the narrative, using numbers from the "Facts" section only. Never invent numbers or events.
Number tables and images are inserted by the system — do not create tables or include images.

Writing rules:
- Every statement about a trend (increased, decreased, stable) must use the wording and numbers from the "Trend vs previous period" section only. Do not infer trends yourself, and do not mention trends for anything not listed in that section.
- Write as an expert giving your own analysis. Never mention the inputs you were given, instructions, input section names or calculation methods (e.g. never write "according to the facts", "according to the labels", "trend labels" or the word prompt).
- Cite regulations only from paragraphs in "Reference documents", giving (Source: file name, rule title). Rule titles are in Thai: give the title as written, followed by a short English gloss in parentheses. When citing a rule that lists zones, state every zone that rule lists — never claim it lists only some of them.
- The risk assessment must combine the high-risk zones listed in the regulations with the violations in this period. A zone the regulations list as high-risk stays high-risk even with no violations in this period.
- Write in plain, professional English, as used in formal safety reports. The facts are partly in Thai; translate them, but keep event IDs, dates, times, camera names and file names unchanged.
- Refer to zones only by these English names (the name already ends in "zone" — do not add another "zone"): {zone_names}
- When citing an event, copy its ID, date, time, camera and zone exactly from the "Facts".

Reply in markdown with all 5 level-2 (##) headings, in this order and spelled exactly as follows:
## Executive summary
(2–4 sentences: overall picture, key numbers and the trend vs the previous period)
## Violations by zone and time
(1 paragraph analysing the problem zones and time slots)
## Notable events
(1–3 sentences summarising the concerning events, citing event IDs)
## Risk assessment
(State the overall risk level High/Medium/Low with reasons, state which high-risk zones the cited regulations define, then give the per-zone risk as a list)
## Recommendations
(3–5 numbered, practical actions naming the zones/time slots to focus on)"""

# Language-dependent report strings (Thai values are exactly the original literals).
TEXT: dict[str, dict[str, str]] = {
    "th": {
        "no_compare": "ไม่มีข้อมูลเปรียบเทียบ",
        "increased": "เพิ่มขึ้น", "decreased": "ลดลง", "stable": "คงที่", "pp": " จุดร้อยละ",
        "no_prev": "ไม่มีข้อมูลช่วงก่อนหน้า ({lo} ถึง {hi}) — ห้ามกล่าวถึงแนวโน้ม",
        "compare_period": "ช่วงเปรียบเทียบ: {lo} ถึง {hi}",
        "t_events": "จำนวนเหตุการณ์", "t_violations": "จำนวนเหตุการณ์ที่ฝ่าฝืน", "t_rate": "อัตราการฝ่าฝืน",
        "t_zone": "การฝ่าฝืนใน{zone}",
        "m_headers": "ตัวชี้วัด|ช่วงนี้|ช่วงก่อนหน้า (เปลี่ยนแปลง)",
        "m_events": "จำนวนเหตุการณ์ (คลิป)", "m_violations": "เหตุการณ์ที่มีการละเมิด", "m_rate": "อัตราการละเมิด",
        "m_persons": "จำนวนคนที่ตรวจพบรวม", "m_no_hardhat": "จำนวนคนไม่สวมหมวกนิรภัยรวม",
        "no_violations": "ไม่พบเหตุการณ์ละเมิดในช่วงเวลานี้",
        "event_head": "### {id} — {date} {time} น. · {camera} · {zone}",
        "event_body": "- ไม่สวมหมวกนิรภัย **{nh}** คน จากที่ตรวจพบ {tp} คน (ความมั่นใจสูงสุด {conf:.2f}) · คลิป `{clip}`",
        "no_events": "ไม่มีเหตุการณ์ในช่วงเวลานี้",
        "by_zone": "### แยกตามโซน", "zone": "โซน", "by_hour": "### แยกตามช่วงเวลา", "hour": "ช่วงเวลา",
        "by_day": "### แยกตามวัน", "day": "วันที่",
        "f_period": "ช่วงเวลา: {lo} ถึง {hi}", "f_metrics": "## ตัวชี้วัดหลัก", "f_trend": "## แนวโน้มเทียบช่วงก่อนหน้า",
        "f_details": "## รายละเอียด", "f_events": "## เหตุการณ์ละเมิดเด่น",
        "u_facts": "# ข้อเท็จจริง", "u_refs": "# เอกสารอ้างอิง",
        "no_narrative": "_(ไม่มีคำบรรยาย)_",
        "src_real": "บันทึกจริงจากระบบตรวจจับ", "src_sample": "ข้อมูลตัวอย่าง (sample)",
        "title": "# รายงานความปลอดภัย{type} — การสวมหมวกนิรภัย",
        "h_project": "**โครงการ:** {site}  ", "h_period": "**ช่วงเวลา:** {period} ({lo}{to})  ", "to": " ถึง {hi}",
        "h_generated": "**จัดทำเมื่อ:** {created:%Y-%m-%d %H:%M} น.  ", "h_source": "**แหล่งข้อมูล:** {source}",
        "footer": "_รายงานนี้สร้างโดย Helmet Safety Assistant — ตัวเลขคำนวณจากบันทึกเหตุการณ์โดยตรง ส่วนคำบรรยายเขียนโดย AI_",
    },
    "en": {
        "no_compare": "no comparison data",
        "increased": "increased", "decreased": "decreased", "stable": "stable", "pp": " percentage points",
        "no_prev": "No data for the previous period ({lo} to {hi}) — do not mention any trend",
        "compare_period": "Comparison period: {lo} to {hi}",
        "t_events": "Events", "t_violations": "Violating events", "t_rate": "Violation rate",
        "t_zone": "Violations in the {zone}",
        "m_headers": "Metric|This period|Previous period (change)",
        "m_events": "Events (clips)", "m_violations": "Events with violations", "m_rate": "Violation rate",
        "m_persons": "Total people detected", "m_no_hardhat": "Total people without hard hats",
        "no_violations": "No violations were found in this period.",
        "event_head": "### {id} — {date} {time} · {camera} · {zone}",
        "event_body": "- **{nh}** without a hard hat out of {tp} people detected (max confidence {conf:.2f}) · clip `{clip}`",
        "no_events": "No events in this period.",
        "by_zone": "### By zone", "zone": "Zone", "by_hour": "### By time of day", "hour": "Time",
        "by_day": "### By day", "day": "Date",
        "f_period": "Period: {lo} to {hi}", "f_metrics": "## Key metrics", "f_trend": "## Trend vs previous period",
        "f_details": "## Details", "f_events": "## Notable violations",
        "u_facts": "# Facts", "u_refs": "# Reference documents",
        "no_narrative": "_(no narrative)_",
        "src_real": "Live detection log", "src_sample": "Sample data",
        "title": "# {type} Safety Report — Hard-Hat Compliance",
        "h_project": "**Project:** {site}  ", "h_period": "**Period:** {period} ({lo}{to})  ", "to": " to {hi}",
        "h_generated": "**Generated:** {created:%Y-%m-%d %H:%M}  ", "h_source": "**Data source:** {source}",
        "footer": "_This report was generated by Helmet Safety Assistant — figures are computed directly from the event log; "
        "the narrative is written by AI._",
    },
}


class ReportInputError(ValueError):
    """Invalid report request (message is Thai)."""


def _parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ReportInputError(f"รูปแบบวันที่ไม่ถูกต้อง: {value} (ต้องเป็น YYYY-MM-DD)") from exc


def _trend_text(trend: dict[str, Any], fmt=str, language: Language = "th") -> str:
    if trend["change_pct"] is None:
        return f"{fmt(trend['previous'])} ({TEXT[language]['no_compare']})"
    sign = "+" if trend["change_pct"] > 0 else ""
    return f"{fmt(trend['previous'])} ({sign}{trend['change_pct']}%)"


def trend_label(current: float, previous: float, *, rate: bool = False, language: Language = "th") -> str:
    """"เพิ่มขึ้น (2 → 3, +1)" / "คงที่ (2 → 2, ±0)" / "ลดลง (40.0% → 30.0%, -10.0 จุดร้อยละ)".

    English: "increased (2 → 3, +1)" / "decreased (40.0% → 30.0%, -10.0 percentage points)".
    """
    tx = TEXT[language]
    if rate:
        delta = round((current - previous) * 100, 1)
        shown, unit = f"{pct(previous)} → {pct(current)}", tx["pp"]
        delta_s = f"{delta:+.1f}" if delta else "±0.0"
    else:
        delta = int(round(current - previous))
        shown, unit = f"{int(previous)} → {int(current)}", ""
        delta_s = f"{delta:+d}" if delta else "±0"
    word = tx["increased"] if delta > 0 else tx["decreased"] if delta < 0 else tx["stable"]
    return f"{word} ({shown}, {delta_s}{unit})"


def trend_lines(df: pd.DataFrame, lo: str, hi: str, language: Language = "th") -> str:
    """Trend labels vs the preceding period of equal length, computed in pandas."""
    tx = TEXT[language]
    prev_lo, prev_hi = aggregates.previous_period(lo, hi)
    if not len(filter_events(df, prev_lo, prev_hi)):
        return tx["no_prev"].format(lo=prev_lo, hi=prev_hi)
    stats = aggregates.compute_stats(df, "real", lo, hi)
    t = stats["trend"]

    def label(key: str, rate: bool = False) -> str:
        return trend_label(t[key]["current"], t[key]["previous"], rate=rate, language=language)

    lines = [
        tx["compare_period"].format(lo=prev_lo, hi=prev_hi),
        f"- {tx['t_events']}: {label('events')}",
        f"- {tx['t_violations']}: {label('violations')}",
        f"- {tx['t_rate']}: {label('violation_rate', rate=True)}",
    ]
    cur = {r["key"]: r["violations"] for r in aggregates.group_by(df, "zone", lo, hi)}
    prev = {r["key"]: r["violations"] for r in aggregates.group_by(df, "zone", prev_lo, prev_hi)}
    for zone in sorted(cur.keys() | prev.keys(), key=lambda z: (-cur.get(z, 0), z)):
        zone_text = tx["t_zone"].format(zone=zone_name(zone, language))
        lines.append(f"- {zone_text}: {trend_label(cur.get(zone, 0), prev.get(zone, 0), language=language)}")
    return "\n".join(lines)


def _metrics_table(stats: dict[str, Any], language: Language = "th") -> str:
    t, tx = stats["trend"], TEXT[language]
    return md_table(
        tx["m_headers"].split("|"),
        [
            [tx["m_events"], stats["total_events"], _trend_text(t["events"], language=language)],
            [tx["m_violations"], stats["total_violations"], _trend_text(t["violations"], language=language)],
            [tx["m_rate"], pct(stats["violation_rate"]), _trend_text(t["violation_rate"], pct, language)],
            [tx["m_persons"], stats["total_persons"], "—"],
            [tx["m_no_hardhat"], stats["total_no_hardhat"], "—"],
        ],
    )


def _notable_events(period: pd.DataFrame) -> list[dict[str, Any]]:
    violations = period[period["violation"]].sort_values(
        ["no_hardhat", "max_conf", "datetime"], ascending=[False, False, True]
    )
    return to_events(violations.head(NOTABLE_EVENTS))


def _events_markdown(events: list[dict[str, Any]], language: Language = "th") -> str:
    tx = TEXT[language]
    if not events:
        return tx["no_violations"]
    blocks = []
    for e in events:
        lines = [
            tx["event_head"].format(
                id=e["event_id"], date=e["date"], time=e["time"], camera=e["camera"], zone=zone_name(e["zone"], language)
            ),
            tx["event_body"].format(nh=e["no_hardhat"], tp=e["total_person"], conf=e["max_conf"], clip=e["clip"]),
        ]
        if e["frame_url"]:
            lines.append(f"\n![{e['event_id']}]({e['frame_url']})")
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def _breakdown_markdown(df: pd.DataFrame, start: str, end: str, weekly: bool, language: Language = "th") -> str:
    tx = TEXT[language]
    if not len(filter_events(df, start, end)):
        return tx["no_events"]

    def zone_fmt(zone: str) -> str:
        return zone_table_label(zone, language)

    parts = [
        tx["by_zone"],
        aggregate_table(aggregates.group_by(df, "zone", start, end), tx["zone"], zone_fmt, language),
        "",
        tx["by_hour"],
        aggregate_table(aggregates.group_by(df, "hour", start, end), tx["hour"], hour_label, language),
    ]
    if weekly:
        parts += ["", tx["by_day"], aggregate_table(aggregates.group_by(df, "day", start, end), tx["day"], str, language)]
    return "\n".join(parts)


def parse_sections(markdown: str, language: Language = "th") -> dict[str, str]:
    """Split LLM output on ``## heading`` lines, keeping only the contract sections of ``language``."""
    sections = sections_for(language)
    found: dict[str, str] = {}
    matches = list(re.finditer(r"^##\s+(.+?)\s*$", markdown, flags=re.MULTILINE))
    for i, m in enumerate(matches):
        heading = m.group(1).strip().strip("*# ")
        section = next((s for s in sections if s.casefold() in heading.casefold()), None)
        if section and section not in found:
            end = matches[i + 1].start() if i + 1 < len(matches) else len(markdown)
            found[section] = markdown[m.end() : end].strip()
    return found


def _empty_narrative(language: Language = "th") -> dict[str, str]:
    if language == "en":
        return {
            "Executive summary": "No events were detected by the system in this period, so there is no violation data "
            "to analyse yet.",
            "Violations by zone and time": "There is no violation data by zone or time of day for this period.",
            "Notable events": "There are no notable events to follow up.",
            "Risk assessment": "The risk cannot be assessed from camera data because there were no events in this "
            "period. Check that the cameras and the detection system are working normally.",
            "Recommendations": "1. Check that the cameras are working and that daily clips are being uploaded.\n"
            "2. Re-run detection once new clips arrive.\n"
            "3. Continue routine site inspections and hard-hat reminders.",
        }
    return {
        "บทสรุปผู้บริหาร": "ไม่พบเหตุการณ์ที่ระบบตรวจจับได้ในช่วงเวลานี้ จึงยังไม่มีข้อมูลการละเมิดสำหรับการวิเคราะห์",
        "การละเมิดแยกตามโซนและช่วงเวลา": "ไม่มีข้อมูลการละเมิดแยกตามโซนหรือช่วงเวลาในช่วงนี้",
        "เหตุการณ์สำคัญ": "ไม่มีเหตุการณ์สำคัญที่ต้องติดตาม",
        "การประเมินความเสี่ยง": "ไม่สามารถประเมินความเสี่ยงจากข้อมูลกล้องได้ เนื่องจากไม่มีเหตุการณ์ในช่วงนี้ "
        "ควรตรวจสอบว่ากล้องและระบบตรวจจับทำงานตามปกติ",
        "ข้อเสนอแนะ": "1. ตรวจสอบการทำงานของกล้องและการอัปโหลดคลิปประจำวัน\n"
        "2. รันการตรวจจับใหม่หลังมีคลิปเข้ามา\n"
        "3. คงการตรวจตราหน้างานและการย้ำเตือนเรื่องการสวมหมวกนิรภัยตามปกติ",
    }


QUALITY_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"ป้ายกำกับ", 'mentions "ป้ายกำกับ" (prompt wording)'),
    (r"(?i)prompt", 'mentions "prompt"'),
    (r"โซน\s*โซน", 'doubled "โซน โซน"'),
    (r"(?i)according to the (?:labels?|facts|trend section|input)", "meta phrase about the inputs"),
    (r"(?i)trend labels?", 'mentions "trend label" (prompt wording)'),
    (r"(?i)\bzone\s+zone\b", 'doubled "zone zone"'),
)


def quality_warnings(narrative: dict[str, str]) -> list[str]:
    """Problems in the LLM-written sections that should not reach a report; logged, not fixed."""
    found = []
    for section, text in narrative.items():
        for pattern, what in QUALITY_PATTERNS:
            if m := re.search(pattern, text):
                snippet = text[max(0, m.start() - 20) : m.end() + 20].replace("\n", " ")
                found.append(f"{section}: {what} … {snippet} …")
    return found


def _regulation_query(period: pd.DataFrame) -> str:
    """Retrieval query for a report: violated zones (key + Thai name) plus the usual topics."""
    zones = period.loc[period["violation"], "zone"].unique().tolist() or period["zone"].unique().tolist()
    names = " ".join(f"{z} {zone_label(z)}" for z in zones)
    return f"โซนเสี่ยงสูง {names} การสวมหมวกนิรภัย หัวหน้างาน ตักเตือน ผู้ฝ่าฝืนซ้ำ กล้อง CCTV"


def _llm_narrative(facts: str, regulation_query: str, language: Language = "th") -> dict[str, str]:
    regs, _, _ = regulations_text(regulation_query)
    tx = TEXT[language]
    prompt = WRITER_PROMPT_EN if language == "en" else WRITER_PROMPT
    reply = llm.complete(
        [
            {"role": "system", "content": prompt.format(zone_names=zone_names_text(language))},
            {"role": "user", "content": f"{tx['u_facts']}\n\n{facts}\n\n{tx['u_refs']}\n\n{regs}"},
        ],
        temperature=0.3,
    )
    sections = parse_sections(reply, language)
    all_sections = sections_for(language)
    if not sections and reply.strip():
        # The model ignored the heading format; keep its text rather than dropping it.
        sections = {all_sections[0]: reply.strip()}
    missing = [s for s in all_sections if s not in sections]
    if missing:
        logger.warning("LLM report narrative missing sections: %s", missing)
    return sections


def _build(report_type: ReportType, start: date, end: date, language: Language = "th") -> dict[str, Any]:
    tx = TEXT[language]
    sections = sections_for(language)
    log = load_events()
    lo, hi = start.isoformat(), end.isoformat()
    period = filter_events(log.df, lo, hi)
    stats = aggregates.compute_stats(log.df, log.source, lo, hi)
    notable = _notable_events(period)
    breakdown = _breakdown_markdown(log.df, lo, hi, report_type == "weekly", language)
    events_md = _events_markdown(notable, language)
    metrics = _metrics_table(stats, language)

    if len(period):
        facts = "\n\n".join(
            [
                tx["f_period"].format(lo=lo, hi=hi),
                tx["f_metrics"], metrics,
                tx["f_trend"], trend_lines(log.df, lo, hi, language),
                tx["f_details"], breakdown,
                tx["f_events"], events_md,
            ]
        )
        narrative = _llm_narrative(facts, _regulation_query(period), language)
    else:
        narrative = _empty_narrative(language)

    for warning in quality_warnings(narrative):
        logger.warning("Report %s %s %s quality check: %s", report_type, lo, language, warning)

    def text(section: str) -> str:
        return narrative.get(section) or tx["no_narrative"]

    created = datetime.now()
    period_text = long_date(lo, language) if report_type == "daily" else f"{long_date(lo, language)} – {long_date(hi, language)}"
    source = tx["src_real"] if log.source == "real" else tx["src_sample"]
    type_label = (TYPE_LABEL_EN if language == "en" else TYPE_LABEL)[report_type]
    markdown = "\n".join(
        [
            tx["title"].format(type=type_label),
            "",
            tx["h_project"].format(site=config.site_name()),
            tx["h_period"].format(period=period_text, lo=lo, to="" if lo == hi else tx["to"].format(hi=hi)),
            tx["h_generated"].format(created=created),
            tx["h_source"].format(source=source),
            "",
            f"## {sections[0]}",
            text(sections[0]),
            "",
            metrics,
            "",
            f"## {sections[1]}",
            text(sections[1]),
            "",
            breakdown,
            "",
            f"## {sections[2]}",
            text(sections[2]),
            "",
            events_md,
            "",
            f"## {sections[3]}",
            text(sections[3]),
            "",
            f"## {sections[4]}",
            text(sections[4]),
            "",
            "---",
            tx["footer"],
            "",
        ]
    )
    name = f"report_{report_type}_{lo}_{language}.md"
    folder = config.reports_dir()
    folder.mkdir(parents=True, exist_ok=True)
    (folder / name).write_text(markdown, encoding="utf-8")
    logger.info("Saved report %s", name)
    return {
        "name": name,
        "type": report_type,
        "date": lo,
        "created_at": created.isoformat(timespec="seconds"),
        "markdown": markdown,
        "language": language,
    }


def daily_report(date_str: str, language: Language = "th") -> dict[str, Any]:
    """Report for a single day."""
    day = _parse_date(date_str)
    return _build("daily", day, day, language)


def weekly_report(start_date: str, language: Language = "th") -> dict[str, Any]:
    """Report for 7 days starting at ``start_date`` (inclusive)."""
    start = _parse_date(start_date)
    return _build("weekly", start, start + timedelta(days=6), language)


def _meta(path: Path) -> dict[str, Any]:
    m = REPORT_NAME_RE.match(path.name)
    if m is None:
        raise ValueError(path.name)
    stat = path.stat()
    return {
        "name": path.name,
        "type": m.group(1),
        "date": m.group(2),
        "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
        "size": stat.st_size,
        "language": m.group(3) or "th",
    }


def list_reports() -> list[dict[str, Any]]:
    """``ReportMeta`` list, newest first."""
    folder = config.reports_dir()
    if not folder.is_dir():
        return []
    metas = [_meta(p) for p in folder.iterdir() if p.is_file() and REPORT_NAME_RE.match(p.name)]
    return sorted(metas, key=lambda m: (m["created_at"], m["name"]), reverse=True)


def get_report(name: str) -> dict[str, Any] | None:
    """Saved report by exact file name (names not matching the pattern are rejected)."""
    if not REPORT_NAME_RE.match(name):
        return None
    path = config.reports_dir() / name
    if not path.is_file():
        return None
    meta = _meta(path)
    keys = ("name", "type", "date", "created_at", "language")
    return {k: meta[k] for k in keys} | {"markdown": path.read_text(encoding="utf-8")}
