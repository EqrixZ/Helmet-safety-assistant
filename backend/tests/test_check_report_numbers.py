"""scripts/check_report_numbers.py: number extraction and matching against the aggregates."""
from __future__ import annotations

import importlib.util
import shutil
import sys
from pathlib import Path

from backend.config import REPO_ROOT

from .conftest import REPO_DATA

_spec = importlib.util.spec_from_file_location("check_report_numbers", REPO_ROOT / "scripts" / "check_report_numbers.py")
check = importlib.util.module_from_spec(_spec)
sys.modules["check_report_numbers"] = check
_spec.loader.exec_module(check)


def test_dates_times_ids_and_clip_names_are_not_quantities() -> None:
    line = "EVT-0051 — 2026‑09‑27 13:05 น. · cam4 · โซนชั้น 3 : ไม่สวมหมวก 3 คนจาก 5 คน · คลิป `cam4_floor3_2026-09-27_1305.mp4`"
    assert check.extract_numbers(line) == [("3", "count"), ("5", "count")]
    assert check.extract_numbers("ช่วง 23‑29 ก.ย. 2026 มี 31 รายการ (11:00–11:59)") == [("31", "count")]


def test_units_and_clauses() -> None:
    line = "อัตรา 32.3 % ลดลง ‑5.7 จุดร้อยละ ความมั่นใจ 0.73 ตามข้อปฏิบัติตัวอย่าง 4"
    assert check.extract_numbers(line) == [("32.3", "pct"), ("5.7", "pct"), ("0.73", "conf")]
    assert check.clause_refs(line) == [("ข้อปฏิบัติตัวอย่าง", 4)]


def test_matches_rounds_to_written_precision() -> None:
    assert check.matches("32.3", 32.258) and check.matches("5.7", -5.67)
    assert not check.matches("32", 32.258 + 1) and not check.matches("33", 32.258)


def test_sample_report_tables_all_match(data_dir: Path) -> None:
    shutil.copy(REPO_DATA / "regulations" / "safety_rules_example.md", data_dir / "regulations")
    report = data_dir / "reports" / "report_weekly_2026-09-23.md"
    shutil.copy(REPO_DATA / "reports" / "report_weekly_2026-09-23.md", report)
    assert check.main([str(report)]) == 0
    import pandas as pd

    rows = pd.read_csv(data_dir / "report_check.csv")
    tables = rows[rows["source"] == "table"]
    assert len(tables) > 50 and tables["matched"].all()
