"""Thai/English language support for chat, suggestions and reports."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend import assistant, data, llm, report
from backend.models import ChatMessage, ChatRequest, ReportRequest, SuggestionsRequest

# sha256 of the Thai SYSTEM_PROMPT before English support was added — evaluate.py relies on it.
THAI_SYSTEM_PROMPT_SHA256 = "07d7ed245b77f1625d703aa936e4e63541773d635913942c15eb978927d4dda0"
EN_NARRATIVE = "\n".join(f"## {s}\nEnglish text for {s}." for s in report.SECTIONS_EN)


def _no_thai(text: str) -> bool:
    return not any("\u0e00" <= ch <= "\u0e7f" for ch in text)


def _sse_events(text: str) -> list[dict]:
    return [json.loads(chunk.removeprefix("data: ")) for chunk in text.strip().split("\n\n")]


def test_language_defaults_to_thai() -> None:
    assert ChatRequest(messages=[{"role": "user", "content": "x"}]).language == "th"
    assert SuggestionsRequest().language == "th"
    assert ReportRequest(type="daily", date="2026-09-29").language == "th"
    assert ReportRequest(type="daily", date="2026-09-29", language="en").language == "en"


def test_thai_system_prompt_unchanged(data_dir: Path) -> None:
    assert hashlib.sha256(assistant.SYSTEM_PROMPT.encode()).hexdigest() == THAI_SYSTEM_PROMPT_SHA256
    log = data.load_events()
    history = [ChatMessage(role="user", content="โซนเครนเป็นอย่างไร")]
    default, _ = assistant.build_messages(history, log.df, log.source)
    thai, _ = assistant.build_messages(history, log.df, log.source, "th")
    assert default == thai
    assert default[0]["content"].startswith('คุณคือ "ผู้ช่วยความปลอดภัย"')
    assert "crane=โซนเครน" in default[0]["content"] and "answer in English" not in default[0]["content"]


def test_english_system_prompt(data_dir: Path) -> None:
    log = data.load_events()
    history = [ChatMessage(role="user", content="How is the crane zone?")]
    th, th_sources = assistant.build_messages(history, log.df, log.source, "th")
    en, en_sources = assistant.build_messages(history, log.df, log.source, "en")
    system = en[0]["content"]
    assert system.startswith('You are the "Safety Assistant"')
    assert "plain, professional English" in system and "crane=Crane zone" in system and "floor3=Floor 3 zone" in system
    assert "not found in the available logs or documents" in system
    # Same data context below the separator.
    assert system.split("====================\n", 1)[1] == th[0]["content"].split("====================\n", 1)[1]
    assert en_sources["log_rows"] == th_sources["log_rows"]
    assert en_sources["regulation_paragraphs"] == th_sources["regulation_paragraphs"]


def test_english_suggestions(client: TestClient) -> None:
    questions = client.post("/api/chat/suggestions", json={"language": "en"}).json()["questions"]
    assert len(questions) == 5 and "29 September 2026" in questions[0]
    assert all(_no_thai(q) for q in questions) and "Crane zone (crane)" in questions[1]
    with_event = client.post("/api/chat/suggestions", json={"event_id": "EVT-0002", "language": "en"}).json()["questions"]
    assert len(with_event) == 5 and with_event[0].startswith("Please analyse event EVT-0002")
    thai = client.post("/api/chat/suggestions", json={}).json()["questions"]
    assert "ครั้ง" in thai[0]
    empty = assistant.suggestions(data.load_events().df.iloc[:0], language="en")
    assert len(empty) == 5 and all(_no_thai(q) for q in empty)


def test_chat_passes_language(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_API_KEY", "test")
    captured: dict = {}

    def fake_stream(messages, *a, **k):
        captured["messages"] = messages
        yield "Hello"

    monkeypatch.setattr(llm, "stream_chat", fake_stream)
    body = {"messages": [{"role": "user", "content": "How many violations?"}], "language": "en"}
    events = _sse_events(client.post("/api/chat", json=body).text)
    assert [e["type"] for e in events] == ["sources", "token", "done"]
    assert captured["messages"][0]["content"].startswith('You are the "Safety Assistant"')
    client.post("/api/chat", json={"messages": body["messages"]})
    assert captured["messages"][0]["content"].startswith("คุณคือ")
    assert client.post("/api/chat", json={**body, "language": "fr"}).status_code == 422


def test_english_report(client: TestClient, data_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_API_KEY", "test")
    captured: list = []
    monkeypatch.setattr(llm, "complete", lambda messages, **k: captured.append(messages) or EN_NARRATIVE)
    r = client.post("/api/reports", json={"type": "weekly", "date": "2026-09-23", "language": "en"})
    assert r.status_code == 200
    rep = r.json()
    assert rep["name"] == "report_weekly_2026-09-23_en.md" and rep["language"] == "en"
    md = rep["markdown"]
    assert md.startswith("# Weekly Safety Report — Hard-Hat Compliance")
    assert "**Period:** 23 September 2026 – 29 September 2026" in md and "**Data source:** Sample data" in md
    positions = [md.index(f"## {s}\nEnglish text for {s}.") for s in report.SECTIONS_EN]
    assert positions == sorted(positions)
    assert "| Metric | This period | Previous period (change) |" in md
    assert "| Zone | Events | Violations | Violation rate |" in md and "| Crane | 8 |" in md
    body = md.split("\n", 3)[3]  # skip title + site-name line (the site name is user data, Thai by default)
    assert _no_thai(body) and "· Crane zone" in md and "ข้อเสนอแนะ" not in md
    # English writer prompt and English facts (trend labels in English).
    system, user = captured[0][0]["content"], captured[0][1]["content"]
    assert "plain, professional English" in system and "## Recommendations" in system
    assert user.startswith("# Facts") and "percentage points" in user and "Violations in the Crane zone" in user
    assert report.parse_sections(EN_NARRATIVE, "en").keys() == set(report.SECTIONS_EN)
    assert report.parse_sections(EN_NARRATIVE) == {}
    # Listing and fetching by name.
    listed = {m["name"]: m for m in client.get("/api/reports").json()}
    assert listed[rep["name"]]["language"] == "en"
    assert client.get(f"/api/reports/{rep['name']}").json() == rep | {"created_at": listed[rep["name"]]["created_at"]}
    # Thai and English reports for the same date coexist.
    monkeypatch.setattr(llm, "complete", lambda *a, **k: "")
    th = client.post("/api/reports", json={"type": "weekly", "date": "2026-09-23"}).json()
    assert th["name"] == "report_weekly_2026-09-23_th.md" and (data_dir / "reports" / rep["name"]).is_file()


def test_english_empty_report(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_API_KEY", "test")
    md = client.post("/api/reports", json={"type": "daily", "date": "2030-01-01", "language": "en"}).json()["markdown"]
    assert md.startswith("# Daily Safety Report") and "**Period:** 1 January 2030 (2030-01-01)" in md
    assert "No events were detected" in md and "No events in this period." in md


def test_legacy_report_names(client: TestClient, data_dir: Path) -> None:
    (data_dir / "reports" / "report_daily_2026-09-29.md").write_text("# legacy", encoding="utf-8")
    (data_dir / "reports" / "report_daily_2026-09-29_fr.md").write_text("x", encoding="utf-8")
    listed = client.get("/api/reports").json()
    assert [(m["name"], m["language"]) for m in listed] == [("report_daily_2026-09-29.md", "th")]
    got = client.get("/api/reports/report_daily_2026-09-29.md").json()
    assert got["language"] == "th" and got["markdown"] == "# legacy" and got["date"] == "2026-09-29"
    assert client.get("/api/reports/report_daily_2026-09-29_fr.md").status_code == 404


def test_trend_labels_and_quality_warnings_in_english() -> None:
    assert report.trend_label(3, 2, language="en") == "increased (2 → 3, +1)"
    assert report.trend_label(2, 2, language="en") == "stable (2 → 2, ±0)"
    assert report.trend_label(0.3, 0.4, rate=True, language="en") == "decreased (40.0% → 30.0%, -10.0 percentage points)"
    assert report.trend_label(3, 2) == "เพิ่มขึ้น (2 → 3, +1)"
    assert report.quality_warnings({"Executive summary": "Violations decreased in the Crane zone."}) == []
    bad = {"Executive summary": "According to the labels, violations rose.", "Risk assessment": "The trend labels show a prompt"}
    assert len(report.quality_warnings(bad)) == 3


def test_sources_log_filter_follows_language(client) -> None:
    th = client.get("/api/chat/context").json()["log_filter"]
    en = client.get("/api/chat/context", params={"language": "en"}).json()["log_filter"]
    assert th.startswith("ไม่พบเงื่อนไขเฉพาะ") and en.startswith("No specific filter")
