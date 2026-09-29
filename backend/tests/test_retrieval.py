"""Question-aware context selection, event line format, token budget and report trend labels."""
from __future__ import annotations

import pandas as pd
import pytest

from backend import assistant, data, evaluate, report, retrieval
from backend.models import ChatMessage


@pytest.fixture(scope="module")
def df() -> pd.DataFrame:
    return data.normalize(pd.read_csv(data.config.REPO_ROOT / "data" / "events_sample.csv", dtype=str, keep_default_na=False))


def test_parse_query_understands_thai_and_iso_dates_zones_cameras_ids() -> None:
    q = retrieval.parse_query(["กล้อง 4 วันที่ 27 ก.ย. 2569 ที่นั่งร้าน ไม่สวมหมวก", "แล้ว EVT-2 กับ 2026-09-21 ล่ะ"], 2026)
    assert q.dates == {"2026-09-27", "2026-09-21"} and q.zones == {"scaffold"}
    assert q.cameras == {"cam4"} and q.event_ids == {"EVT-0002"} and q.violation


def test_select_rows_filters_caps_and_falls_back(df: pd.DataFrame) -> None:
    crane = retrieval.select_rows(df, retrieval.parse_query(["โซนเครนมีการละเมิดกี่ครั้ง"]))
    assert not crane.fallback and crane.matched == 8 and set(crane.rows["zone"]) == {"crane"} and crane.rows["violation"].all()

    many = retrieval.select_rows(df, retrieval.parse_query(["cam1 เป็นอย่างไรบ้าง"]))
    assert many.matched == 25 and len(many.rows) == retrieval.MAX_ROWS

    only_id = retrieval.select_rows(df, retrieval.parse_query(["EVT-0002 เกิดอะไรขึ้น"]))
    assert list(only_id.rows["event_id"]) == ["EVT-0002"]

    general = retrieval.select_rows(df, retrieval.parse_query(["มีเหตุการณ์ทั้งหมดกี่รายการ"]))
    assert general.fallback and len(general.rows) == retrieval.FALLBACK_ROWS and general.rows["violation"].all()
    assert list(general.rows["datetime"]) == sorted(general.rows["datetime"], reverse=True)


def test_tables_stay_with_their_rule_and_rule_numbers_are_retrieved() -> None:
    text = "# หมวด\n\n**ข้อ 4:** โซนเสี่ยงสูง\n\n| โซน |\n|---|\n| crane |\n| entrance |\n\n**ข้อ 5:** อื่น ๆ"
    paras = retrieval.split_paragraphs("r.md", text)
    assert [p.title for p in paras] == ["ข้อ 4", "ข้อ 5"] and "| entrance |" in paras[0].text
    filler = [retrieval.Paragraph("r.md", f"ข้อ {n}", f"เนื้อหาทั่วไป {n}") for n in range(6, 20)]
    top = retrieval.top_paragraphs("ข้อ 4 ระบุอะไร", k=2, paragraphs=paras + filler)
    assert top[0].title == "ข้อ 4"


def test_event_line_format() -> None:
    row = {"event_id": "EVT-0002", "date": "2026-09-16", "time": "13:25", "camera": "cam2", "zone": "crane",
           "hardhat": 0, "no_hardhat": 3, "violation": True}
    assert assistant.event_line(row) == (
        "EVT-0002 | วันที่ 2026-09-16 | เวลา 13:25 | กล้อง cam2 | โซน crane (เครน) | สวมหมวก 0 | ไม่สวมหมวก 3 | ฝ่าฝืน: ใช่"
    )


# With len/2.1 (calibrated against Groq prompt_tokens), 15 rows + 5 paragraphs + aggregates peak near
# 3,000 tokens; typical questions are ~2,000–2,500.
CONTEXT_TOKEN_CEILING = 3000


def test_every_eval_question_fits_the_token_ceiling(df: pd.DataFrame) -> None:
    for case in evaluate.generate_cases(df):
        _, sources = assistant.build_messages([ChatMessage(role="user", content=case.question)], df, "sample")
        assert sources["token_estimate"] < CONTEXT_TOKEN_CEILING, case.question


@pytest.mark.parametrize(
    ("cur", "prev", "rate", "expected"),
    [
        (2, 2, False, "คงที่ (2 → 2, ±0)"),
        (3, 5, False, "ลดลง (5 → 3, -2)"),
        (0.5, 0.4, True, "เพิ่มขึ้น (40.0% → 50.0%, +10.0 จุดร้อยละ)"),
    ],
)
def test_trend_label(cur: float, prev: float, rate: bool, expected: str) -> None:
    assert report.trend_label(cur, prev, rate=rate) == expected


def test_trend_lines_without_previous_period(df: pd.DataFrame) -> None:
    assert "ห้ามกล่าวถึงแนวโน้ม" in report.trend_lines(df, "2026-09-16", "2026-09-16")


def test_report_quality_warnings() -> None:
    clean = {"บทสรุปผู้บริหาร": "จำนวนเหตุการณ์ลดลงเมื่อเทียบกับวันก่อนหน้า ในโซนเครนไม่พบการฝ่าฝืน"}
    assert report.quality_warnings(clean) == []
    bad = {"บทสรุปผู้บริหาร": "อัตราเพิ่มขึ้นตามป้ายกำกับแนวโน้ม", "ข้อเสนอแนะ": "ตรวจตราโซน โซนเครน ตาม Prompt"}
    warnings = report.quality_warnings(bad)
    assert len(warnings) == 3 and any("โซน โซน" in w for w in warnings)


def test_zone_names_are_prefixed_once() -> None:
    from backend.textfmt import zone_display, zone_name

    assert zone_name("crane") == "โซนเครน" and zone_display("floor3") == "โซนชั้น 3 (floor3)"
    assert zone_name("mystery") == "mystery"
    assert "โซนโซน" not in assistant.zone_names_text() and "crane=โซนเครน" in assistant.zone_names_text()
