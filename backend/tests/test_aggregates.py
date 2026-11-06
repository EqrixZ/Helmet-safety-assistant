"""Tests for aggregations, data loading and the HTTP API."""
from __future__ import annotations

import json
import os
import sys
import threading
import time
import types
from pathlib import Path

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from backend import aggregates, data, evaluate, llm
from backend.frame_utils import EVENT_COLUMNS


def make_df(rows: list[tuple[str, str, str, int, int]]) -> pd.DataFrame:
    """rows: (datetime, camera, zone, hardhat, no_hardhat)."""
    records = []
    for i, (dt, cam, zone, hh, nh) in enumerate(rows, 1):
        records.append(
            {
                "event_id": f"EVT-{i:04d}", "datetime": dt, "date": dt[:10], "time": dt[11:16],
                "camera": cam, "zone": zone, "clip": f"{cam}_{zone}.mp4", "hardhat": hh, "no_hardhat": nh,
                "total_person": hh + nh, "violation": "true" if nh else "false", "max_conf": 0.8,
                "frame_path": f"f{i}.jpg" if nh else "",
            }
        )
    return data.normalize(pd.DataFrame(records))


@pytest.fixture()
def small_df() -> pd.DataFrame:
    return make_df(
        [
            ("2026-01-01T08:10:00", "cam1", "crane", 1, 1),
            ("2026-01-02T09:00:00", "cam1", "crane", 2, 0),
            ("2026-01-03T08:30:00", "cam2", "entrance", 0, 2),
            ("2026-01-03T14:00:00", "cam2", "crane", 1, 1),
            ("2026-01-04T14:45:00", "cam1", "entrance", 3, 0),
            ("2026-01-06T08:00:00", "cam2", "crane", 0, 1),
        ]
    )


# --- pure aggregates ----------------------------------------------------------------

def test_stats_totals(small_df: pd.DataFrame) -> None:
    s = aggregates.compute_stats(small_df, "sample")
    assert (s["from"], s["to"]) == ("2026-01-01", "2026-01-06")
    assert s["total_events"] == 6
    assert s["total_violations"] == 4
    assert s["violation_rate"] == pytest.approx(0.6667)
    assert s["total_persons"] == 12 and s["total_no_hardhat"] == 5
    assert s["top_zone"] == {"key": "crane", "violations": 3}
    assert s["top_hour"] == {"key": "08", "violations": 3}


def test_trend_vs_previous_equal_period(small_df: pd.DataFrame) -> None:
    s = aggregates.compute_stats(small_df, "sample", "2026-01-03", "2026-01-04")
    # previous period = 2026-01-01..2026-01-02: 2 events, 1 violation
    assert s["trend"]["events"] == {"current": 3, "previous": 2, "change_pct": 50.0}
    assert s["trend"]["violations"] == {"current": 2, "previous": 1, "change_pct": 100.0}
    assert s["trend"]["violation_rate"]["previous"] == 0.5


def test_trend_previous_zero_is_null(small_df: pd.DataFrame) -> None:
    s = aggregates.compute_stats(small_df, "sample", "2026-01-01", "2026-01-02")
    assert s["trend"]["events"]["change_pct"] is None


def test_previous_period() -> None:
    assert aggregates.previous_period("2026-01-08", "2026-01-14") == ("2026-01-01", "2026-01-07")


def test_group_by_day_includes_zero_days(small_df: pd.DataFrame) -> None:
    rows = aggregates.group_by(small_df, "day")
    assert [r["key"] for r in rows] == [f"2026-01-0{d}" for d in range(1, 7)]
    assert rows[4] == {"key": "2026-01-05", "events": 0, "violations": 0, "rate": 0.0}
    extended = aggregates.group_by(small_df, "day", "2026-01-05", "2026-01-08")
    assert [r["events"] for r in extended] == [0, 1, 0, 0]


def test_group_by_hour_zone_camera(small_df: pd.DataFrame) -> None:
    assert [r["key"] for r in aggregates.group_by(small_df, "hour")] == ["08", "09", "14"]
    zones = aggregates.group_by(small_df, "zone")
    assert [(r["key"], r["violations"]) for r in zones] == [("crane", 3), ("entrance", 1)]
    assert aggregates.group_by(small_df, "camera")[0] == {"key": "cam2", "events": 3, "violations": 3, "rate": 1.0}


def test_top_n_and_zone_sparklines(small_df: pd.DataFrame) -> None:
    assert [r["key"] for r in aggregates.top_n(small_df, "hour")] == ["08", "14"]
    zones = aggregates.zone_summaries(small_df)
    crane = next(z for z in zones if z["key"] == "crane")
    assert len(crane["sparkline"]) == 14
    assert crane["sparkline"][-6:] == [1, 0, 1, 0, 0, 1]


def test_empty_frame_is_safe() -> None:
    empty = data.empty_frame()
    s = aggregates.compute_stats(empty, "real")
    assert s["total_events"] == 0 and s["top_zone"] is None and s["from"] is None
    assert s["trend"]["events"]["change_pct"] is None
    assert aggregates.group_by(empty, "day") == []
    assert aggregates.zone_summaries(empty) == []


# --- data loading, filters, pagination ---------------------------------------------------

def test_filters_and_pagination(small_df: pd.DataFrame) -> None:
    f = data.filter_events(small_df, "2026-01-02", "2026-01-04", zone="CRANE", violation=True)
    assert f["event_id"].tolist() == ["EVT-0004"]
    page = data.paginate(data.sort_events(small_df, "datetime", "desc"), page=2, size=4)
    assert (page["total"], page["pages"], page["page"]) == (6, 2, 2)
    assert [e["event_id"] for e in page["items"]] == ["EVT-0002", "EVT-0001"]
    assert page["items"][0]["frame_url"] is None
    assert page["items"][1]["frame_url"] == "/api/frames/f1.jpg"
    assert list(page["items"][0])[: len(EVENT_COLUMNS)] == EVENT_COLUMNS


def test_real_log_preferred_and_reloaded_on_change(data_dir: Path) -> None:
    assert data.load_events().source == "sample"
    real = data_dir / "events.csv"
    sample = (data_dir / "events_sample.csv").read_text().splitlines()
    real.write_text("\n".join(sample[:2]) + "\n")
    log = data.load_events()
    assert log.source == "real" and len(log.df) == 1
    real.write_text("\n".join(sample[:3]) + "\n")
    os.utime(real, ns=(time.time_ns(), time.time_ns() + 1_000_000_000))
    assert len(data.load_events().df) == 2


def test_empty_csv_falls_back_to_sample(data_dir: Path) -> None:
    (data_dir / "events.csv").write_text("")
    log = data.load_events()
    assert log.source == "sample"
    (data_dir / "events.csv").write_text(",".join(data.EVENT_COLUMNS) + "\n")
    data.invalidate_cache()
    assert data.load_events().source == "sample"


# --- evaluation helpers -----------------------------------------------------------------

def test_eval_answer_checking() -> None:
    case = evaluate.EvalCase("q", "1234", "number")
    assert evaluate.is_correct(case, "มีทั้งหมด ๑,๒๓๔ ครั้ง")
    day = evaluate.EvalCase("q", "2", "number")
    assert not evaluate.is_correct(day, "วันที่ 2026-09-02 เวลา 02:00 ไม่มีข้อมูล")
    assert evaluate.is_correct(evaluate.EvalCase("q", "crane", "label", ["crane", "พื้นที่เครน"]), "คือพื้นที่เครน")
    assert evaluate.is_correct(evaluate.EvalCase("q", "11:00", "hour", ["11"]), "ช่วง 11:00–11:59 น.")


def test_mock_evaluation_runs(data_dir: Path) -> None:
    results = evaluate.run(15, use_mock=True)
    assert len(results) == 15
    assert results["correct"].mean() >= 0.8


# --- API ------------------------------------------------------------------------------

def test_health(client: TestClient) -> None:
    body = client.get("/api/health").json()
    assert body["status"] == "ok" and body["data_source"] == "sample"
    assert body["events_count"] == 60 and body["llm_configured"] is False
    assert body["version"] == "1.0.0"


def test_stats_endpoint(client: TestClient) -> None:
    body = client.get("/api/stats", params={"from": "2026-09-23", "to": "2026-09-29", "zone": "crane"}).json()
    assert body["from"] == "2026-09-23" and body["total_events"] > 0
    assert set(body["trend"]) == {"events", "violations", "violation_rate"}


def test_events_endpoint(client: TestClient) -> None:
    body = client.get("/api/events", params={"violation": "true", "size": 5, "sort": "no_hardhat", "order": "desc"}).json()
    assert body["size"] == 5 and body["total"] == 21 and body["pages"] == 5
    assert all(e["violation"] for e in body["items"])
    assert body["items"][0]["no_hardhat"] >= body["items"][-1]["no_hardhat"]
    assert client.get("/api/events/EVT-0001").json()["zone"] == "entrance"
    missing = client.get("/api/events/EVT-9999")
    assert missing.status_code == 404 and missing.json()["error"]["code"] == "NOT_FOUND"
    assert client.get("/api/events", params={"sort": "bogus"}).json()["error"]["code"] == "BAD_REQUEST"


def test_validation_error_envelope(client: TestClient) -> None:
    r = client.get("/api/events", params={"size": 500})
    assert r.status_code == 422 and r.json()["error"]["code"] == "VALIDATION_ERROR"
    assert client.get("/api/aggregates").status_code == 422


def test_aggregates_and_zones(client: TestClient) -> None:
    days = client.get("/api/aggregates", params={"group_by": "day", "from": "2026-09-28", "to": "2026-10-02"}).json()
    assert len(days) == 5 and days[-1]["events"] == 0
    zones = client.get("/api/zones").json()
    assert zones[0]["key"] == "crane" and len(zones[0]["sparkline"]) == 14
    assert [z["violations"] for z in zones] == sorted((z["violations"] for z in zones), reverse=True)
    assert client.get("/api/cameras").json()[0]["key"] == "cam2"


def test_frames_rejects_traversal(client: TestClient, data_dir: Path) -> None:
    (data_dir / "frames" / "ok.jpg").write_bytes(b"\xff\xd8\xff")
    ok = client.get("/api/frames/ok.jpg")
    assert ok.status_code == 200 and ok.headers["content-type"] == "image/jpeg"
    for bad in ("..%2Fevents_sample.csv", "..", ".hidden.jpg", "missing.jpg"):
        assert client.get(f"/api/frames/{bad}").status_code == 404


def test_chat_requires_llm(client: TestClient) -> None:
    r = client.post("/api/chat", json={"messages": [{"role": "user", "content": "สวัสดี"}]})
    assert r.status_code == 503
    assert r.json()["error"]["code"] == "LLM_NOT_CONFIGURED"
    assert client.post("/api/reports", json={"type": "daily", "date": "2026-09-29"}).status_code == 503


def _sse_events(text: str) -> list[dict]:
    assert text.endswith("\n\n")
    return [json.loads(chunk.removeprefix("data: ")) for chunk in text.strip().split("\n\n")]


def test_chat_sse_format(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_API_KEY", "test")
    captured: dict = {}

    def fake_stream(messages):
        captured["messages"] = messages
        yield "สวัส"
        yield "ดีครับ"

    monkeypatch.setattr(llm, "stream_chat", fake_stream)
    r = client.post("/api/chat", json={"messages": [{"role": "user", "content": "สรุปให้หน่อย"}]})
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/event-stream")
    assert r.headers["cache-control"] == "no-cache" and r.headers["x-accel-buffering"] == "no"
    events = _sse_events(r.text)
    assert events[0]["type"] == "sources" and events[0]["sources"]["events_count"] == 60
    assert events[1:] == [{"type": "token", "content": "สวัส"}, {"type": "token", "content": "ดีครับ"}, {"type": "done"}]
    system = captured["messages"][0]["content"]
    assert captured["messages"][0]["role"] == "system" and "ภาษาไทย" in system and "EVT-0060" in system


def test_chat_sse_error_mid_stream(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_API_KEY", "test")

    def failing_stream(_messages):
        yield "เริ่ม"
        raise llm.LLMError("เชื่อมต่อ LLM ไม่สำเร็จ")

    monkeypatch.setattr(llm, "stream_chat", failing_stream)
    events = _sse_events(client.post("/api/chat", json={"messages": [{"role": "user", "content": "x"}]}).text)
    assert [e["type"] for e in events] == ["sources", "token", "error", "done"]
    assert events[2]["message"] == "เชื่อมต่อ LLM ไม่สำเร็จ"


def test_context_and_suggestions(client: TestClient, data_dir: Path) -> None:
    (data_dir / "regulations" / "README.md").write_text("ignored")
    (data_dir / "regulations" / "rules.md").write_text("# กฎ\nต้องสวมหมวกนิรภัย")
    ctx = client.get("/api/chat/context").json()
    assert ctx["regulation_files"] == ["rules.md"] and ctx["regulation_paragraphs"] == ["rules.md · กฎ"]
    assert ctx["log_included_full"] is False and ctx["log_rows"] == 10 and 0 < ctx["token_estimate"] < 3000
    questions = client.post("/api/chat/suggestions", json={}).json()["questions"]
    assert len(questions) == 5 and "2026-09-29" in questions[0]
    with_event = client.post("/api/chat/suggestions", json={"event_id": "EVT-0002"}).json()["questions"]
    assert len(with_event) == 5 and "EVT-0002" in with_event[0]


def test_report_generation(client: TestClient, data_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_API_KEY", "test")
    narrative = "\n".join(f"## {s}\nข้อความ {s}" for s in ("บทสรุปผู้บริหาร", "การละเมิดแยกตามโซนและช่วงเวลา", "เหตุการณ์สำคัญ", "การประเมินความเสี่ยง", "ข้อเสนอแนะ"))
    monkeypatch.setattr(llm, "complete", lambda *a, **k: narrative)
    r = client.post("/api/reports", json={"type": "weekly", "date": "2026-09-23"})
    assert r.status_code == 200
    report = r.json()
    assert report["name"] == "report_weekly_2026-09-23_th.md" and report["language"] == "th"
    md = report["markdown"]
    positions = [md.index(f"## {s}") for s in ("บทสรุปผู้บริหาร", "การละเมิดแยกตามโซนและช่วงเวลา", "เหตุการณ์สำคัญ", "การประเมินความเสี่ยง", "ข้อเสนอแนะ")]
    assert positions == sorted(positions)
    assert "![EVT-" in md and "(/api/frames/" in md and "ข้อความ ข้อเสนอแนะ" in md
    assert (data_dir / "reports" / report["name"]).is_file()
    assert client.get("/api/reports").json()[0]["name"] == report["name"]
    assert client.get(f"/api/reports/{report['name']}").json()["markdown"] == md
    empty = client.post("/api/reports", json={"type": "daily", "date": "2030-01-01"}).json()
    assert "ไม่พบเหตุการณ์" in empty["markdown"]
    assert client.get("/api/reports/..%2Fsettings.json").status_code == 404


def test_uploads_and_regulations(client: TestClient, data_dir: Path) -> None:
    files = [
        ("files", ("cam1_crane_2026-09-29_0800.mp4", b"x", "video/mp4")),
        ("files", ("notes.exe", b"x", "application/octet-stream")),
        ("files", ("../evil.mp4", b"x", "video/mp4")),
    ]
    result = client.post("/api/clips/upload", files=files).json()
    assert result["saved"] == ["cam1_crane_2026-09-29_0800.mp4"]
    assert {r["name"] for r in result["rejected"]} == {"notes.exe", "../evil.mp4"}
    assert not (data_dir / "evil.mp4").exists()
    clip = client.get("/api/clips").json()[0]
    assert clip["parsed"] == {"camera": "cam1", "zone": "crane", "datetime": "2026-09-29T08:00:00", "matched": True}

    docs = [("files", ("กฎความปลอดภัย.md", "สวมหมวกนิรภัย".encode(), "text/markdown")), ("files", ("README.md", b"x", "text/markdown"))]
    result = client.post("/api/regulations/upload", files=docs).json()
    assert result["saved"] == ["กฎความปลอดภัย.md"] and result["rejected"][0]["name"] == "README.md"
    listed = client.get("/api/regulations").json()
    assert listed[0]["type"] == "md" and listed[0]["chars"] == len("สวมหมวกนิรภัย")
    assert client.delete("/api/regulations/กฎความปลอดภัย.md").json() == {"deleted": "กฎความปลอดภัย.md"}
    assert client.delete("/api/regulations/README.md").status_code == 404


def test_settings_roundtrip(client: TestClient, data_dir: Path) -> None:
    assert client.get("/api/settings").json()["site_name"] == "โครงการก่อสร้างอาคาร A"
    assert client.put("/api/settings", json={"site_name": "ไซต์ B"}).json() == {"site_name": "ไซต์ B"}
    assert client.get("/api/health").json()["site_name"] == "ไซต์ B"
    assert json.loads((data_dir / "settings.json").read_text())["site_name"] == "ไซต์ B"
    assert client.put("/api/settings", json={"site_name": ""}).status_code == 422


def test_llm_test_not_configured(client: TestClient) -> None:
    body = client.post("/api/llm/test", json={}).json()
    assert body["ok"] is False and body["latency_ms"] is None


def test_detection_run_with_fake_detector(client: TestClient, data_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    sample = (data_dir / "events_sample.csv").read_text().splitlines()
    release = threading.Event()

    def fake_run_detection(clips_dir=None, out_csv=None, frames_dir=None, conf=None, progress_cb=None):
        release.wait(5)
        progress_cb(1, 2, "a.mp4")
        progress_cb(2, 2, "b.mp4")
        Path(out_csv).write_text("\n".join(sample[:3]) + "\n")
        return pd.read_csv(out_csv)

    monkeypatch.setitem(sys.modules, "backend.detector", types.SimpleNamespace(run_detection=fake_run_detection))
    started = client.post("/api/detect/run", json={})
    assert started.status_code == 200 and started.json()["state"] == "running"
    again = client.post("/api/detect/run", json={})
    assert again.status_code == 409 and again.json()["error"]["code"] == "DETECTION_RUNNING"
    release.set()
    for _ in range(100):
        status = client.get("/api/detect/status").json()
        if status["state"] != "running":
            break
        time.sleep(0.02)
    assert status["state"] == "done" and status["events_written"] == 2 and status["progress"] == 1.0
    health = client.get("/api/health").json()
    assert health["data_source"] == "real" and health["events_count"] == 2


def test_events_expose_vote_columns_and_accept_legacy_logs(client: TestClient, data_dir: Path) -> None:
    legacy = client.get("/api/events", params={"size": 1}).json()["items"][0]  # sample log: no vote columns
    assert legacy["no_hardhat_ratio"] is None and legacy["no_hardhat_max"] == legacy["no_hardhat"]

    header = ",".join(EVENT_COLUMNS)
    row = "EVT-0001,2026-09-29T10:20:00,2026-09-29,10:20,cam7,floor3,c.mp4,2,0,3,false,0.709,c.jpg,1,0.133"
    (data_dir / "events.csv").write_text(f"{header}\n{row}\n")
    data.invalidate_cache()
    ev = client.get("/api/events/EVT-0001").json()
    assert (ev["no_hardhat"], ev["no_hardhat_max"], ev["no_hardhat_ratio"], ev["violation"]) == (0, 1, 0.133, False)
