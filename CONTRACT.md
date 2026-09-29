# API & Data Contract — Helmet Safety Assistant

**Single source of truth.** Every component must follow this file. Do not edit it.
If a deviation is unavoidable, append a bullet to `CONTRACT_CHANGES.md` explaining what and why.

---

## 1. Paths & environment

| Item | Value |
|---|---|
| Repo root | `helmet-safety-assistant/` |
| Data dir | env `DATA_DIR`, default `<repo>/data` |
| Clips | `data/clips/*.mp4` (also accept `.mov`, `.avi`, `.mkv`) |
| Annotated frames | `data/frames/*.jpg` |
| Regulations | `data/regulations/*.md|*.txt|*.pdf` (`README.md` in that folder is **excluded** from LLM context and from the list) |
| Reports | `data/reports/report_{type}_{date}.md` |
| Event log | `data/events.csv` (real) → falls back to `data/events_sample.csv` (sample) |
| Settings | `data/settings.json` → `{"site_name": "..."}` |
| Eval output | `data/eval_results.csv` |
| Env vars | `LLM_API_KEY`, `LLM_BASE_URL` (default `https://api.openai.com/v1`), `LLM_MODEL` (default `gpt-4o-mini`), `CONF_THRESHOLD` (default `0.35`), `HF_MODEL_REPO` (default `keremberke/yolov8n-hard-hat-detection`), `HF_MODEL_FILE` (default `best.pt`), `SITE_NAME` (default `โครงการก่อสร้างอาคาร A`), `DATA_DIR` |

Backend listens on `:8000`. Frontend dev server on `:5173` proxies `/api` → `http://localhost:8000`.
Python package is `backend` (run from repo root: `uvicorn backend.main:app`, `python -m backend.detector`, `python -m backend.evaluate`). `.env` at repo root is loaded with python-dotenv.

## 2. Clip filename convention

```
cam{ID}_{zone}_{YYYY-MM-DD}_{HHMM}.{ext}
regex (case-insensitive): ^cam(\d+)_([a-z0-9]+)_(\d{4}-\d{2}-\d{2})_(\d{2})(\d{2})\.(mp4|mov|avi|mkv)$
example: cam2_crane_2026-09-29_1405.mp4 → camera "cam2", zone "crane", 2026-09-29 14:05
```
Non-matching filename (or invalid date/time) → `camera = "unknown"`, `zone = "unknown"`, datetime = file mtime (local time).
`camera` is always the string `cam{ID}` (e.g. `"cam2"`); zone is lowercased.

Known zones (used for display labels): `entrance` (ทางเข้า), `crane` (พื้นที่เครน), `scaffold` (นั่งร้าน), `floor3` (ชั้น 3), `warehouse` (คลังวัสดุ). Unknown zones must still work (display raw key).

## 3. events.csv

One row per clip. Columns, in this order:

| column | type | notes |
|---|---|---|
| event_id | str | `EVT-0001`… sequential by datetime |
| datetime | str | ISO `YYYY-MM-DDTHH:MM:SS` (local, no tz) |
| date | str | `YYYY-MM-DD` |
| time | str | `HH:MM` |
| camera | str | `cam2` or `unknown` |
| zone | str | lowercased |
| clip | str | clip filename |
| hardhat | int | max count of `Hardhat` over sampled frames |
| no_hardhat | int | max count of `NO-Hardhat` over sampled frames |
| total_person | int | max over frames of (hardhat + no_hardhat) in the same frame |
| violation | bool | `true`/`false` (lowercase in CSV); true iff no_hardhat > 0 |
| max_conf | float | max detection confidence over all detections, 3 decimals; 0 if none |
| frame_path | str | **basename only** of the annotated frame in `data/frames/` (e.g. `cam2_crane_2026-09-29_1405.jpg`); empty string if no frame |

Annotated frame = the sampled frame with the most NO-Hardhat detections (ties → earliest; if no violation, the frame with the most detections; if no detections at all, the middle sampled frame).

## 4. REST API

All JSON. Base prefix `/api`. CORS allows all origins. OpenAPI docs at `/docs`.
Date params `from`/`to` are inclusive `YYYY-MM-DD`; both optional (default = entire log range).

### Error envelope (all non-2xx responses)
```json
{ "error": { "code": "LLM_NOT_CONFIGURED", "message": "ยังไม่ได้ตั้งค่า LLM_API_KEY — กรุณาใส่ค่าในไฟล์ .env แล้วรีสตาร์ต backend" } }
```
Codes: `NOT_FOUND` (404), `BAD_REQUEST` (400), `VALIDATION_ERROR` (422), `LLM_NOT_CONFIGURED` (503), `LLM_ERROR` (502), `DETECTION_RUNNING` (409), `INTERNAL_ERROR` (500). Messages are Thai.

### Shared types (TypeScript notation; Python pydantic mirrors these names exactly)

```ts
type Event = {
  event_id: string; datetime: string; date: string; time: string;
  camera: string; zone: string; clip: string;
  hardhat: number; no_hardhat: number; total_person: number;
  violation: boolean; max_conf: number;
  frame_path: string;          // basename or ""
  frame_url: string | null;    // "/api/frames/{frame_path}" or null when frame_path empty
};

type Paginated<T> = { items: T[]; total: number; page: number; size: number; pages: number };

type AggregateRow = { key: string; events: number; violations: number; rate: number }; // rate 0..1

type Trend = { current: number; previous: number; change_pct: number | null }; // null when previous == 0

type Stats = {
  from: string | null; to: string | null;           // effective range used
  total_events: number;
  total_violations: number;
  violation_rate: number;                            // 0..1
  total_persons: number;
  total_no_hardhat: number;
  top_zone: { key: string; violations: number } | null;
  top_hour: { key: string; violations: number } | null;   // key "14" = 14:00–14:59
  trend: { events: Trend; violations: Trend; violation_rate: Trend };
  data_source: "real" | "sample";
};

type Health = {
  status: "ok";
  data_source: "real" | "sample";
  events_count: number;
  date_range: { min: string | null; max: string | null };
  llm_configured: boolean;
  llm_model: string;
  llm_base_url: string;
  conf_threshold: number;
  model_repo: string;             // HF repo id
  site_name: string;
  version: string;                // "1.0.0"
};

type ChatMessage = { role: "user" | "assistant"; content: string };
type ChatRequest = { messages: ChatMessage[] };     // last message is the user's new question

type Suggestions = { questions: string[] };          // exactly 5 Thai questions

type ReportType = "daily" | "weekly";
type ReportRequest = { type: ReportType; date: string };   // daily: that day; weekly: start date (7 days inclusive)
type Report = { name: string; type: ReportType; date: string; created_at: string; markdown: string };
type ReportMeta = { name: string; type: ReportType; date: string; created_at: string; size: number };

type DetectState = "idle" | "running" | "done" | "error";
type DetectStatus = {
  state: DetectState;
  progress: number;            // 0..1
  processed: number; total: number;
  current_clip: string | null;
  message: string;             // Thai human-readable status
  started_at: string | null; finished_at: string | null;
  events_written: number;
};

type ClipInfo = { name: string; size: number; parsed: { camera: string; zone: string; datetime: string; matched: boolean } };
type UploadResult = { saved: string[]; rejected: { name: string; reason: string }[] };

type RegulationDoc = { name: string; size: number; type: "md" | "txt" | "pdf"; chars: number; modified: string };

type Settings = { site_name: string };
type LlmTestResult = { ok: boolean; model: string; base_url: string; latency_ms: number | null; message: string };
type ContextSources = { regulation_files: string[]; log_range: { min: string | null; max: string | null }; events_count: number; data_source: "real" | "sample"; log_included_full: boolean };
```

### Endpoints

| Method & path | Query / body | Response |
|---|---|---|
| `GET /api/health` | — | `Health` |
| `GET /api/stats` | `from`, `to`, `zone?`, `camera?` | `Stats` — trend compares with the immediately preceding period of equal length (in days) |
| `GET /api/events` | `from`, `to`, `zone`, `camera`, `violation` (`true`/`false`), `page` (default 1), `size` (default 20, max 200), `sort` (column name, default `datetime`), `order` (`asc`/`desc`, default `desc`) | `Paginated<Event>` |
| `GET /api/events/{event_id}` | — | `Event` (404 `NOT_FOUND`) |
| `GET /api/aggregates` | `group_by` = `zone`\|`camera`\|`hour`\|`day` (required), `from`, `to` | `AggregateRow[]` — `day` sorted by date asc and **includes zero days** in the range; `hour` keys `"00"`…`"23"` only for hours present, sorted asc; `zone`/`camera` sorted by violations desc |
| `GET /api/frames/{filename}` | — | image/jpeg (404 if missing; reject path traversal) |
| `GET /api/zones` | — | `ZoneSummary[]` over whole log (see below) |
| `GET /api/cameras` | — | `AggregateRow[]` over whole log |
| `POST /api/chat` | `ChatRequest` | `text/event-stream` (see §5). If LLM not configured → HTTP 503 JSON error envelope `LLM_NOT_CONFIGURED` (NOT an SSE stream) |
| `GET /api/chat/context` | — | `ContextSources` |
| `POST /api/chat/suggestions` | `{}` | `Suggestions` — deterministic from the data (no LLM needed) |
| `POST /api/reports` | `ReportRequest` | `Report` (saved to `data/reports/`). 503 if LLM not configured |
| `GET /api/reports` | — | `ReportMeta[]` newest first |
| `GET /api/reports/{name}` | `name` = file name without path, e.g. `report_daily_2026-09-29.md` | `Report` |
| `POST /api/detect/run` | `{}` | `DetectStatus` (409 `DETECTION_RUNNING` if already running) |
| `GET /api/detect/status` | — | `DetectStatus` |
| `GET /api/clips` | — | `ClipInfo[]` |
| `POST /api/clips/upload` | multipart, field `files` (multiple) | `UploadResult` — only video extensions accepted |
| `GET /api/regulations` | — | `RegulationDoc[]` |
| `POST /api/regulations/upload` | multipart, field `files` (multiple) | `UploadResult` — only `.md`, `.txt`, `.pdf` |
| `DELETE /api/regulations/{name}` | — | `{ "deleted": string }` |
| `GET /api/settings` | — | `Settings` |
| `PUT /api/settings` | `Settings` | `Settings` |
| `POST /api/llm/test` | `{}` | `LlmTestResult` (always 200; `ok:false` + Thai message when not configured or failing) |

```ts
type ZoneSummary = AggregateRow & { sparkline: number[] };  // violations per day for the last 14 days of the log, oldest→newest
```
`GET /api/zones` → `ZoneSummary[]`, sorted by violations desc.

## 5. SSE format — `POST /api/chat`

Response headers: `Content-Type: text/event-stream`, `Cache-Control: no-cache`, `X-Accel-Buffering: no`.
Each event is one line `data: <json>\n\n` (no `event:` field). Order:

```
data: {"type":"sources","sources":<ContextSources>}
data: {"type":"token","content":"สวัส"}
data: {"type":"token","content":"ดีครับ"}
...
data: {"type":"done"}
```
On failure mid-stream: `data: {"type":"error","message":"<Thai message>"}` then `data: {"type":"done"}`.
Frontend reads with `fetch` + `ReadableStream` (not EventSource, since it is a POST).

## 6. Detector module interface (`backend/detector.py`)

```python
def run_detection(
    clips_dir: Path | None = None,          # default DATA_DIR/clips
    out_csv: Path | None = None,            # default DATA_DIR/events.csv
    frames_dir: Path | None = None,         # default DATA_DIR/frames
    conf: float | None = None,              # default CONF_THRESHOLD
    progress_cb: Callable[[int, int, str], None] | None = None,  # (processed, total, current_clip)
) -> pandas.DataFrame                       # the rows written (empty DataFrame with contract columns if no clips)
```
- If no clips: log a Thai/English message, return empty DataFrame, **do not create or overwrite** events.csv. Exit code 0 for CLI.
- Otherwise overwrite `events.csv` with all clips (full re-scan).
- `backend/frame_utils.py` exposes `parse_clip_filename(name: str, mtime: float | None = None) -> dict` returning `{"camera","zone","datetime": datetime,"matched": bool}`, `EVENT_COLUMNS: list[str]`, and frame annotation helpers.
- CLI: `python -m backend.detector [--clips DIR] [--conf 0.35] [--out PATH]`.

## 7. LLM layer

- `backend/llm.py`: `get_client()`, `is_configured() -> bool` (true iff `LLM_API_KEY` non-empty), `stream_chat(messages) -> Iterator[str]`, `complete(messages) -> str`. Uses the `openai` package with `base_url=LLM_BASE_URL`.
- `backend/assistant.py`: `build_context(df) -> (context_text, ContextSources)`; aggregates: totals, per-day, per-zone, per-camera, per-hour violation counts, top-3 zones, top-3 time slots (hours), violation rate; full log as compact CSV if ≤ 300 rows; every regulation document prefixed with `### เอกสาร: {filename}`. Thai system prompt as specified in the product brief.
- `backend/report.py`: `daily_report(date: str) -> Report`, `weekly_report(start_date: str) -> Report`. Thai markdown sections, in order: `## บทสรุปผู้บริหาร`, `## การละเมิดแยกตามโซนและช่วงเวลา`, `## เหตุการณ์สำคัญ` (with frame refs like `![EVT-0012](/api/frames/xxx.jpg)`), `## การประเมินความเสี่ยง`, `## ข้อเสนอแนะ`. Number tables are computed by pandas and inserted directly; the LLM writes the narrative parts.
- `backend/evaluate.py`: when `LLM_API_KEY` is missing or `--mock` is passed, use a mock LLM that answers from the same aggregates (so the pipeline runs end-to-end).
