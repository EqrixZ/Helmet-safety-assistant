"""Safety assistant context (CONTRACT §7) — no vector DB, sized for small free-tier token budgets.

The system message holds:
* the pandas aggregates, always, as compact labelled lines (the source for every count);
* at most ``retrieval.MAX_ROWS`` log rows relevant to the question (dates, zones, cameras,
  event ids, violation keywords from the question and the previous user turns), one
  labelled line each — or the latest violations when nothing matches;
* the ``retrieval.TOP_PARAGRAPHS`` regulation paragraphs most similar to the question,
  each tagged with its file name for citation.
Chat history is trimmed to the last ``MAX_HISTORY`` messages.
"""
from __future__ import annotations

import logging
import math
from collections.abc import Sequence
from datetime import datetime
from typing import Any

import pandas as pd

from backend import aggregates, config, retrieval
from backend.models import ChatMessage, DataSource
from backend.textfmt import hour_label, pct, thai_date, zone_display, zone_name

logger = logging.getLogger(__name__)

MAX_HISTORY = 10
DAILY_SERIES_DAYS = 14        # per-day counts in the context cover only the most recent days
QUERY_USER_TURNS = 3          # current question + the 2 previous user turns drive retrieval
CHARS_PER_TOKEN = 2.1         # Thai-heavy text; matched Groq prompt_tokens within a few % on the eval set

SYSTEM_PROMPT = """คุณคือ "ผู้ช่วยความปลอดภัย" ของเจ้าหน้าที่ความปลอดภัยในการทำงาน (จป.) ประจำไซต์ก่อสร้าง "{site}"
ระบบกล้องตรวจจับคนงานที่ไม่สวมหมวกนิรภัยจากคลิปวิดีโอ และบันทึกผลเป็นเหตุการณ์ (1 เหตุการณ์ = 1 คลิป)

กฎการตอบ:
1. ตอบจาก "ข้อมูลบริบท" ด้านล่างเท่านั้น ห้ามแต่งตัวเลข เหตุการณ์ หรือข้อกำหนด
2. คำถามเชิงนับหรือสถิติ ให้ใช้ตัวเลขจาก "สถิติสรุป" เท่านั้น รายการเหตุการณ์เป็นเพียงบางส่วนที่เกี่ยวข้อง ห้ามนับจากรายการนั้น
3. หากไม่มีข้อมูลในบริบท ให้ตอบว่า "ไม่พบข้อมูลนี้ในบันทึกหรือเอกสารที่มีอยู่"
4. เมื่ออ้างถึงเหตุการณ์ ให้คัดลอกวันที่ เวลา กล้อง และโซนจากบรรทัดของเหตุการณ์นั้นตรงตามที่เขียนไว้ ห้ามอนุมานเอง
5. อ้างข้อกำหนดได้เฉพาะย่อหน้าที่อยู่ใน "เอกสารกฎระเบียบที่เกี่ยวข้อง" พร้อมระบุ (ที่มา: ชื่อไฟล์, ชื่อข้อ) หากข้อกำหนดระบุรายชื่อโซน ให้ระบุโซนตามที่ข้อนั้นระบุไว้จริงทั้งหมด หากข้อที่ต้องการไม่อยู่ในบริบท ให้แจ้งว่าไม่พบในเอกสารที่ดึงมา
6. ตอบเป็นภาษาไทยเสมอ ใช้ markdown เมื่อช่วยให้อ่านง่าย
7. เขียนด้วยภาษาไทยแบบทางการตามที่ใช้ในรายงานความปลอดภัยอย่างเป็นทางการ หลีกเลี่ยงการใช้คำภาษาอังกฤษปน ยกเว้นศัพท์เทคนิคและชื่อตัวชี้วัด
8. เรียกชื่อโซนด้วยชื่อภาษาไทยตามนี้ (ขึ้นต้นด้วย "โซน" แล้ว ห้ามเติม "โซน" ซ้ำ): {zone_names}
9. เมื่อเหมาะสม ให้ข้อเสนอแนะเชิงปฏิบัติที่ช่วยลดการฝ่าฝืนได้จริง

ความหมาย: ฝ่าฝืน = พบคนไม่สวมหมวกนิรภัยอย่างน้อย 1 คนในคลิป; จำนวนคนคือค่าสูงสุดต่อเฟรมในคลิป; อัตราการฝ่าฝืน = เหตุการณ์ที่ฝ่าฝืน ÷ เหตุการณ์ทั้งหมด

==================== ข้อมูลบริบท ====================
{context}"""


def estimate_tokens(text: str) -> int:
    return math.ceil(len(text) / CHARS_PER_TOKEN)


def zone_names_text() -> str:
    return ", ".join(f"{key}={zone_name(key)}" for key in config.ZONE_LABELS)


def _ranked(rows: list[dict[str, Any]], fmt) -> str:
    if not rows:
        return "ไม่มี"
    return "; ".join(f"{i}. {fmt(r['key'])} {r['violations']} ครั้ง" for i, r in enumerate(rows, 1))


def _series(rows: list[dict[str, Any]], fmt=str, rate: bool = True) -> str:
    return "; ".join(
        f"{fmt(r['key'])} = {r['events']}/{r['violations']}" + (f" ({pct(r['rate'])})" if rate else "") for r in rows
    )


def aggregates_text(df: pd.DataFrame, data_source: DataSource) -> str:
    """Precomputed aggregates as compact, labelled Thai lines."""
    stats = aggregates.compute_stats(df, data_source)
    if not len(df):
        return "## สถิติสรุป\nยังไม่มีเหตุการณ์ในบันทึก (0 เหตุการณ์)"
    return "\n".join(
        [
            "## สถิติสรุป (คำนวณจากบันทึกทั้งหมด — ใช้ตอบคำถามเชิงนับ)",
            f"ช่วงข้อมูล: {stats['from']} ถึง {stats['to']} | เหตุการณ์ทั้งหมด: {stats['total_events']} | "
            f"เหตุการณ์ที่ฝ่าฝืน: {stats['total_violations']} | อัตราการฝ่าฝืน: {pct(stats['violation_rate'])} | "
            f"คนที่ตรวจพบรวม: {stats['total_persons']} | คนไม่สวมหมวกรวม: {stats['total_no_hardhat']}",
            f"โซนที่ฝ่าฝืนมากที่สุด 3 อันดับ: {_ranked(aggregates.top_n(df, 'zone'), zone_display)}",
            f"ช่วงเวลาที่ฝ่าฝืนมากที่สุด 3 อันดับ: {_ranked(aggregates.top_n(df, 'hour'), hour_label)}",
            f"กล้องที่ฝ่าฝืนมากที่สุด: {_ranked(aggregates.top_n(df, 'camera', 1), str)}",
            "รูปแบบรายการต่อไปนี้: ชื่อ = เหตุการณ์/ฝ่าฝืน (อัตราการฝ่าฝืน)",
            f"รายวัน {DAILY_SERIES_DAYS} วันล่าสุด (รวมวันที่ไม่มีเหตุการณ์): "
            f"{_series(aggregates.group_by(df, 'day')[-DAILY_SERIES_DAYS:], rate=False)}",
            f"รายโซน: {_series(aggregates.group_by(df, 'zone'), zone_display)}",
            f"รายกล้อง: {_series(aggregates.group_by(df, 'camera'))}",
            f"รายช่วงชั่วโมง: {_series(aggregates.group_by(df, 'hour'), hour_label)}",
        ]
    )


def event_line(row: dict[str, Any]) -> str:
    """One labelled line per event — the model is told to copy fields from here verbatim."""
    zone = row["zone"]
    label = config.zone_label(zone)
    zone_text = zone if label == zone else f"{zone} ({label})"
    return (
        f"{row['event_id']} | วันที่ {row['date']} | เวลา {row['time']} | กล้อง {row['camera']} | โซน {zone_text} | "
        f"สวมหมวก {int(row['hardhat'])} | ไม่สวมหมวก {int(row['no_hardhat'])} | ฝ่าฝืน: {'ใช่' if row['violation'] else 'ไม่'}"
    )


def log_text(df: pd.DataFrame, query: retrieval.Query) -> tuple[str, retrieval.RowSelection]:
    sel = retrieval.select_rows(df, query)
    if sel.fallback:
        header = f"## เหตุการณ์ที่เกี่ยวข้อง ({sel.description})"
    else:
        shown = f"{len(sel.rows)} จาก {sel.matched} รายการ" if sel.matched > len(sel.rows) else f"{len(sel.rows)} รายการ"
        header = f"## เหตุการณ์ที่เกี่ยวข้องกับคำถาม ({shown} ที่ตรงเงื่อนไข: {sel.description})"
    lines = [event_line(r) for r in sel.rows.to_dict("records")] or ["(ไม่มี)"]
    return "\n".join([header, "ใช้สำหรับอ้างรายละเอียดเหตุการณ์ ห้ามใช้นับจำนวน", *lines]), sel


def regulations_text(query_text: str) -> tuple[str, list[retrieval.Paragraph], int]:
    """Top regulation paragraphs for the query, each tagged ``[filename] title``."""
    paras = retrieval.all_paragraphs()
    if not paras:
        return "## เอกสารกฎระเบียบที่เกี่ยวข้อง\nยังไม่มีเอกสารกฎระเบียบในระบบ", [], 0
    top = retrieval.top_paragraphs(query_text, paragraphs=paras)
    body = "\n\n".join(f"### [{p.file}] {p.title}\n{p.text}" for p in top)
    return f"## เอกสารกฎระเบียบที่เกี่ยวข้อง (ตัดตอน {len(top)} จาก {len(paras)} ย่อหน้า)\n\n{body}", top, len(paras)


def build_context(
    df: pd.DataFrame, data_source: DataSource = "sample", query_texts: Sequence[str] = ()
) -> tuple[str, dict[str, Any]]:
    """Return ``(context_text, ContextSources)`` for the given log and question text(s)."""
    default_year = int(str(df["date"].max())[:4]) if len(df) else None
    query = retrieval.parse_query(list(query_texts), default_year)
    log, sel = log_text(df, query)
    regs, paras, total_paras = regulations_text(" ".join(query_texts))
    source_label = "บันทึกจริงจากระบบตรวจจับ" if data_source == "real" else "ข้อมูลตัวอย่าง (sample)"
    header = f"วันที่ปัจจุบัน: {datetime.now():%Y-%m-%d} | โครงการ: {config.site_name()} | แหล่งข้อมูล: {source_label}"
    text = "\n\n".join([header, aggregates_text(df, data_source), log, regs])
    lo, hi = aggregates.effective_range(df, None, None)
    sources = {
        "regulation_files": list(dict.fromkeys(p.file for p in paras)),
        "regulation_paragraphs": [f"{p.file} · {p.title}" for p in paras],
        "regulation_paragraphs_total": total_paras,
        "log_range": {"min": lo, "max": hi},
        "events_count": len(df),
        "data_source": data_source,
        "log_included_full": len(sel.rows) == len(df),
        "log_rows": len(sel.rows),
        "log_filter": sel.description,
        "token_estimate": estimate_tokens(text),
    }
    return text, sources


def build_messages(
    history: Sequence[ChatMessage], df: pd.DataFrame, data_source: DataSource
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    """OpenAI-style message list: system prompt + context, then the last ``MAX_HISTORY`` turns."""
    user_turns = [m.content for m in history if m.role == "user"][-QUERY_USER_TURNS:]
    context, sources = build_context(df, data_source, user_turns)
    system = SYSTEM_PROMPT.format(site=config.site_name(), zone_names=zone_names_text(), context=context)
    turns = [{"role": m.role, "content": m.content} for m in history[-MAX_HISTORY:]]
    messages = [{"role": "system", "content": system}, *turns]
    sources["token_estimate"] = estimate_tokens("".join(m["content"] for m in messages))
    logger.info(
        "Chat context: %d log rows (%s), %d regulation paragraphs, ~%d tokens",
        sources["log_rows"], sources["log_filter"], len(sources["regulation_paragraphs"]), sources["token_estimate"],
    )
    return messages, sources


def event_question(event: dict[str, Any]) -> str:
    """Pre-filled question asking the assistant about one event."""
    return (
        f"ช่วยวิเคราะห์เหตุการณ์ {event['event_id']} (กล้อง {event['camera']} {zone_display(event['zone'])} "
        f"วันที่ {event['date']} เวลา {event['time']} น. พบคนไม่สวมหมวก {event['no_hardhat']} คน "
        f"จากทั้งหมด {event['total_person']} คน) ว่ามีความเสี่ยงอย่างไร และควรดำเนินการอย่างไรตามข้อกำหนด"
    )


def suggestions(df: pd.DataFrame, event: dict[str, Any] | None = None) -> list[str]:
    """Exactly 5 deterministic Thai questions derived from the data."""
    if not len(df):
        questions = [
            "ตอนนี้มีข้อมูลเหตุการณ์ในระบบแล้วหรือยัง?",
            "ตามกฎหมาย นายจ้างมีหน้าที่อย่างไรเกี่ยวกับการสวมหมวกนิรภัยในไซต์ก่อสร้าง?",
            "หมวกนิรภัยที่ใช้ในงานก่อสร้างต้องมีมาตรฐานอะไรบ้าง?",
            "ควรจัดการอย่างไรเมื่อพบคนงานไม่สวมหมวกนิรภัย?",
            "มีแนวทางลดการละเมิดการสวมหมวกนิรภัยอย่างไรบ้าง?",
        ]
    else:
        latest = str(df["date"].max())
        top_zone = aggregates.top_n(df, "zone", 1)
        top_hour = aggregates.top_n(df, "hour", 1)
        zone_q = (
            f"ทำไม{zone_display(top_zone[0]['key'])} ถึงมีการละเมิดมากที่สุด และควรแก้ไขอย่างไร?"
            if top_zone
            else "โซนไหนมีความเสี่ยงสูงที่สุดจากข้อมูลที่มี?"
        )
        hour_q = (
            f"ช่วงเวลา {hour_label(top_hour[0]['key'])} มีการละเมิดบ่อยเพราะอะไร และควรเพิ่มการตรวจตราอย่างไร?"
            if top_hour
            else "ช่วงเวลาไหนของวันที่มีการละเมิดบ่อยที่สุด?"
        )
        questions = [
            f"วันที่ {latest} ({thai_date(latest)}) มีการละเมิดการสวมหมวกนิรภัยกี่ครั้ง และเกิดที่โซนไหนบ้าง?",
            zone_q,
            hour_q,
            f"สรุปแนวโน้มการละเมิดตั้งแต่ {df['date'].min()} ถึง {latest} ให้หน่อย",
            "ตามข้อกำหนด นายจ้างต้องทำอย่างไรเมื่อพบลูกจ้างไม่สวมหมวกนิรภัย?",
        ]
    if event is not None:
        questions = [event_question(event), *questions[:4]]
    return questions
