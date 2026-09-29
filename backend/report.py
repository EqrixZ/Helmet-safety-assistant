"""Daily / weekly Thai safety reports (CONTRACT §7).

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
from backend.models import ReportType
from backend.textfmt import aggregate_table, hour_label, md_table, pct, thai_date, zone_name

logger = logging.getLogger(__name__)

SECTIONS: tuple[str, ...] = (
    "บทสรุปผู้บริหาร",
    "การละเมิดแยกตามโซนและช่วงเวลา",
    "เหตุการณ์สำคัญ",
    "การประเมินความเสี่ยง",
    "ข้อเสนอแนะ",
)
NOTABLE_EVENTS = 5
REPORT_NAME_RE = re.compile(r"^report_(daily|weekly)_(\d{4}-\d{2}-\d{2})\.md$")
TYPE_LABEL = {"daily": "ประจำวัน", "weekly": "ประจำสัปดาห์"}

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


class ReportInputError(ValueError):
    """Invalid report request (message is Thai)."""


def _parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ReportInputError(f"รูปแบบวันที่ไม่ถูกต้อง: {value} (ต้องเป็น YYYY-MM-DD)") from exc


def _trend_text(trend: dict[str, Any], fmt=str) -> str:
    if trend["change_pct"] is None:
        return f"{fmt(trend['previous'])} (ไม่มีข้อมูลเปรียบเทียบ)"
    sign = "+" if trend["change_pct"] > 0 else ""
    return f"{fmt(trend['previous'])} ({sign}{trend['change_pct']}%)"


def trend_label(current: float, previous: float, *, rate: bool = False) -> str:
    """"เพิ่มขึ้น (2 → 3, +1)" / "คงที่ (2 → 2, ±0)" / "ลดลง (40.0% → 30.0%, -10.0 จุดร้อยละ)"."""
    if rate:
        delta = round((current - previous) * 100, 1)
        shown, unit = f"{pct(previous)} → {pct(current)}", " จุดร้อยละ"
        delta_s = f"{delta:+.1f}" if delta else "±0.0"
    else:
        delta = int(round(current - previous))
        shown, unit = f"{int(previous)} → {int(current)}", ""
        delta_s = f"{delta:+d}" if delta else "±0"
    word = "เพิ่มขึ้น" if delta > 0 else "ลดลง" if delta < 0 else "คงที่"
    return f"{word} ({shown}, {delta_s}{unit})"


def trend_lines(df: pd.DataFrame, lo: str, hi: str) -> str:
    """Trend labels vs the preceding period of equal length, computed in pandas."""
    prev_lo, prev_hi = aggregates.previous_period(lo, hi)
    if not len(filter_events(df, prev_lo, prev_hi)):
        return f"ไม่มีข้อมูลช่วงก่อนหน้า ({prev_lo} ถึง {prev_hi}) — ห้ามกล่าวถึงแนวโน้ม"
    stats = aggregates.compute_stats(df, "real", lo, hi)
    t = stats["trend"]
    lines = [
        f"ช่วงเปรียบเทียบ: {prev_lo} ถึง {prev_hi}",
        f"- จำนวนเหตุการณ์: {trend_label(t['events']['current'], t['events']['previous'])}",
        f"- จำนวนเหตุการณ์ที่ฝ่าฝืน: {trend_label(t['violations']['current'], t['violations']['previous'])}",
        f"- อัตราการฝ่าฝืน: {trend_label(t['violation_rate']['current'], t['violation_rate']['previous'], rate=True)}",
    ]
    cur = {r["key"]: r["violations"] for r in aggregates.group_by(df, "zone", lo, hi)}
    prev = {r["key"]: r["violations"] for r in aggregates.group_by(df, "zone", prev_lo, prev_hi)}
    for zone in sorted(cur.keys() | prev.keys(), key=lambda z: (-cur.get(z, 0), z)):
        lines.append(f"- การฝ่าฝืนใน{zone_name(zone)}: {trend_label(cur.get(zone, 0), prev.get(zone, 0))}")
    return "\n".join(lines)


def _metrics_table(stats: dict[str, Any]) -> str:
    t = stats["trend"]
    return md_table(
        ["ตัวชี้วัด", "ช่วงนี้", "ช่วงก่อนหน้า (เปลี่ยนแปลง)"],
        [
            ["จำนวนเหตุการณ์ (คลิป)", stats["total_events"], _trend_text(t["events"])],
            ["เหตุการณ์ที่มีการละเมิด", stats["total_violations"], _trend_text(t["violations"])],
            ["อัตราการละเมิด", pct(stats["violation_rate"]), _trend_text(t["violation_rate"], pct)],
            ["จำนวนคนที่ตรวจพบรวม", stats["total_persons"], "—"],
            ["จำนวนคนไม่สวมหมวกนิรภัยรวม", stats["total_no_hardhat"], "—"],
        ],
    )


def _notable_events(period: pd.DataFrame) -> list[dict[str, Any]]:
    violations = period[period["violation"]].sort_values(
        ["no_hardhat", "max_conf", "datetime"], ascending=[False, False, True]
    )
    return to_events(violations.head(NOTABLE_EVENTS))


def _events_markdown(events: list[dict[str, Any]]) -> str:
    if not events:
        return "ไม่พบเหตุการณ์ละเมิดในช่วงเวลานี้"
    blocks = []
    for e in events:
        lines = [
            f"### {e['event_id']} — {e['date']} {e['time']} น. · {e['camera']} · {zone_name(e['zone'])}",
            f"- ไม่สวมหมวกนิรภัย **{e['no_hardhat']}** คน จากที่ตรวจพบ {e['total_person']} คน "
            f"(ความมั่นใจสูงสุด {e['max_conf']:.2f}) · คลิป `{e['clip']}`",
        ]
        if e["frame_url"]:
            lines.append(f"\n![{e['event_id']}]({e['frame_url']})")
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def _breakdown_markdown(df: pd.DataFrame, start: str, end: str, weekly: bool) -> str:
    if not len(filter_events(df, start, end)):
        return "ไม่มีเหตุการณ์ในช่วงเวลานี้"
    parts = [
        "### แยกตามโซน",
        aggregate_table(aggregates.group_by(df, "zone", start, end), "โซน", zone_label),
        "",
        "### แยกตามช่วงเวลา",
        aggregate_table(aggregates.group_by(df, "hour", start, end), "ช่วงเวลา", hour_label),
    ]
    if weekly:
        parts += ["", "### แยกตามวัน", aggregate_table(aggregates.group_by(df, "day", start, end), "วันที่")]
    return "\n".join(parts)


def parse_sections(markdown: str) -> dict[str, str]:
    """Split LLM output on ``## heading`` lines, keeping only the contract sections."""
    found: dict[str, str] = {}
    matches = list(re.finditer(r"^##\s+(.+?)\s*$", markdown, flags=re.MULTILINE))
    for i, m in enumerate(matches):
        heading = m.group(1).strip().strip("*# ")
        section = next((s for s in SECTIONS if s in heading), None)
        if section and section not in found:
            end = matches[i + 1].start() if i + 1 < len(matches) else len(markdown)
            found[section] = markdown[m.end() : end].strip()
    return found


def _empty_narrative() -> dict[str, str]:
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


def _llm_narrative(facts: str, regulation_query: str) -> dict[str, str]:
    regs, _, _ = regulations_text(regulation_query)
    reply = llm.complete(
        [
            {"role": "system", "content": WRITER_PROMPT.format(zone_names=zone_names_text())},
            {"role": "user", "content": f"# ข้อเท็จจริง\n\n{facts}\n\n# เอกสารอ้างอิง\n\n{regs}"},
        ],
        temperature=0.3,
    )
    sections = parse_sections(reply)
    if not sections and reply.strip():
        # The model ignored the heading format; keep its text rather than dropping it.
        sections = {SECTIONS[0]: reply.strip()}
    missing = [s for s in SECTIONS if s not in sections]
    if missing:
        logger.warning("LLM report narrative missing sections: %s", missing)
    return sections


def _build(report_type: ReportType, start: date, end: date) -> dict[str, Any]:
    log = load_events()
    lo, hi = start.isoformat(), end.isoformat()
    period = filter_events(log.df, lo, hi)
    stats = aggregates.compute_stats(log.df, log.source, lo, hi)
    notable = _notable_events(period)
    breakdown = _breakdown_markdown(log.df, lo, hi, report_type == "weekly")
    events_md = _events_markdown(notable)
    metrics = _metrics_table(stats)

    if len(period):
        facts = "\n\n".join(
            [
                f"ช่วงเวลา: {lo} ถึง {hi}",
                "## ตัวชี้วัดหลัก", metrics,
                "## แนวโน้มเทียบช่วงก่อนหน้า", trend_lines(log.df, lo, hi),
                "## รายละเอียด", breakdown,
                "## เหตุการณ์ละเมิดเด่น", events_md,
            ]
        )
        narrative = _llm_narrative(facts, _regulation_query(period))
    else:
        narrative = _empty_narrative()

    for warning in quality_warnings(narrative):
        logger.warning("Report %s %s quality check: %s", report_type, lo, warning)

    def text(section: str) -> str:
        return narrative.get(section) or "_(ไม่มีคำบรรยาย)_"

    created = datetime.now()
    period_text = thai_date(lo) if report_type == "daily" else f"{thai_date(lo)} – {thai_date(hi)}"
    source = "บันทึกจริงจากระบบตรวจจับ" if log.source == "real" else "ข้อมูลตัวอย่าง (sample)"
    markdown = "\n".join(
        [
            f"# รายงานความปลอดภัย{TYPE_LABEL[report_type]} — การสวมหมวกนิรภัย",
            "",
            f"**โครงการ:** {config.site_name()}  ",
            f"**ช่วงเวลา:** {period_text} ({lo}{'' if lo == hi else f' ถึง {hi}'})  ",
            f"**จัดทำเมื่อ:** {created:%Y-%m-%d %H:%M} น.  ",
            f"**แหล่งข้อมูล:** {source}",
            "",
            f"## {SECTIONS[0]}",
            text(SECTIONS[0]),
            "",
            metrics,
            "",
            f"## {SECTIONS[1]}",
            text(SECTIONS[1]),
            "",
            breakdown,
            "",
            f"## {SECTIONS[2]}",
            text(SECTIONS[2]),
            "",
            events_md,
            "",
            f"## {SECTIONS[3]}",
            text(SECTIONS[3]),
            "",
            f"## {SECTIONS[4]}",
            text(SECTIONS[4]),
            "",
            "---",
            "_รายงานนี้สร้างโดย Helmet Safety Assistant — ตัวเลขคำนวณจากบันทึกเหตุการณ์โดยตรง ส่วนคำบรรยายเขียนโดย AI_",
            "",
        ]
    )
    name = f"report_{report_type}_{lo}.md"
    folder = config.reports_dir()
    folder.mkdir(parents=True, exist_ok=True)
    (folder / name).write_text(markdown, encoding="utf-8")
    logger.info("Saved report %s", name)
    return {"name": name, "type": report_type, "date": lo, "created_at": created.isoformat(timespec="seconds"), "markdown": markdown}


def daily_report(date_str: str) -> dict[str, Any]:
    """Report for a single day."""
    day = _parse_date(date_str)
    return _build("daily", day, day)


def weekly_report(start_date: str) -> dict[str, Any]:
    """Report for 7 days starting at ``start_date`` (inclusive)."""
    start = _parse_date(start_date)
    return _build("weekly", start, start + timedelta(days=6))


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
    return {k: meta[k] for k in ("name", "type", "date", "created_at")} | {"markdown": path.read_text(encoding="utf-8")}
