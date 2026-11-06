"""Turn raw stock videos into CCTV-style clips the detector can read.

For every video in ``data/raw_clips/``:
  1. check it is real footage with OpenCV (> 1 distinct frame and duration > 3 s);
  2. cut to the first 15 s and re-encode with ffmpeg (1280 px wide, libx264, CRF 28, no
     audio) to mimic CCTV compression;
  3. save to ``data/clips/cam{ID}_{zone}_{YYYY-MM-DD}_{HHMM}.mp4``, spreading the clips over
     4 cameras, 5 zones and the last 10 days (deterministic: same inputs → same names).
It also deletes clips already in ``data/clips/`` that are a still image turned into video,
and rewrites ``data/clips/SOURCES.md`` (output file ← original file, Pexels licence).

Usage: ``python scripts/prepare_clips.py [--raw DIR] [--out DIR] [--end-date YYYY-MM-DD] [--dry-run]``
ffmpeg: a system ``ffmpeg`` if present, else the one bundled with ``imageio-ffmpeg``
(``pip install -r scripts/requirements.txt``).
"""
from __future__ import annotations

import argparse
import logging
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

import cv2  # noqa: E402
import numpy as np  # noqa: E402

from backend.frame_utils import is_video_file, parse_clip_filename  # noqa: E402

logger = logging.getLogger("prepare_clips")

CLIP_SECONDS = 15
MIN_SECONDS = 3.0
OUT_WIDTH = 1280
CRF = 28
SAMPLE_FRAMES = 10
DISTINCT_DIFF = 2.0          # mean abs grey-level difference (0–255) that counts as a new frame
DAYS_WINDOW = 10
SOURCE_LABEL = "Pexels (Pexels License)"

ZONES = ["entrance", "crane", "scaffold", "floor3", "warehouse"]
ZONE_CAMERA = {"entrance": 1, "warehouse": 1, "crane": 2, "scaffold": 3, "floor3": 4}  # same as the sample data
WORK_START_MIN, WORK_END_MIN = 7 * 60, 17 * 60


@dataclass
class Probe:
    readable: bool
    fps: float = 0.0
    frames: int = 0
    width: int = 0
    height: int = 0
    distinct: int = 0

    @property
    def duration(self) -> float:
        return self.frames / self.fps if self.fps > 0 else 0.0

    @property
    def is_real_video(self) -> bool:
        return self.readable and self.distinct > 1 and self.duration > MIN_SECONDS

    def reason(self) -> str:
        if not self.readable:
            return "อ่านไฟล์ไม่ได้ / unreadable"
        if self.distinct <= 1:
            return "มีเฟรมเดียว (ภาพนิ่ง) / still image"
        if self.duration <= MIN_SECONDS:
            return f"สั้นเกินไป {self.duration:.1f}s / too short"
        return "ok"


def probe(path: Path, window_s: float = CLIP_SECONDS) -> Probe:
    """Duration and number of distinct frames among up to SAMPLE_FRAMES spread over the first ``window_s``."""
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        return Probe(False)
    try:
        fps = cap.get(cv2.CAP_PROP_FPS) or 0.0
        n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        p = Probe(True, fps, n, int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
        if fps <= 0 or n <= 0:
            return Probe(False)
        last = min(n, int(window_s * fps)) - 1
        kept: list[np.ndarray] = []
        for idx in np.linspace(0, max(last, 0), SAMPLE_FRAMES).astype(int):
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(idx))
            ok, frame = cap.read()
            if not ok or frame is None:
                continue
            small = cv2.resize(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), (64, 36)).astype(np.float32)
            if all(np.abs(small - k).mean() > DISTINCT_DIFF for k in kept):
                kept.append(small)
        p.distinct = len(kept)
        return p
    finally:
        cap.release()


def plan_names(count: int, end: date) -> list[str]:
    """``count`` clip names cycling through the 5 zones (4 cameras) over the last DAYS_WINDOW days."""
    names: list[str] = []
    span = WORK_END_MIN - WORK_START_MIN
    for i in range(count):
        zone = ZONES[i % len(ZONES)]
        day = end - timedelta(days=(3 * i) % DAYS_WINDOW)
        minute = WORK_START_MIN + ((i * 97 + 15) % span) // 5 * 5
        while True:
            name = f"cam{ZONE_CAMERA[zone]}_{zone}_{day:%Y-%m-%d}_{minute // 60:02d}{minute % 60:02d}.mp4"
            if name not in names:
                break
            minute = WORK_START_MIN + (minute - WORK_START_MIN + 5) % span
        assert parse_clip_filename(name)["matched"], name
        names.append(name)
    return names


def ffmpeg_exe() -> str:
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    try:
        import imageio_ffmpeg
    except ImportError as exc:
        raise SystemExit("ไม่พบ ffmpeg — ติดตั้งด้วย `pip install -r scripts/requirements.txt` หรือ `brew install ffmpeg`") from exc
    return imageio_ffmpeg.get_ffmpeg_exe()


def encode(src: Path, dst: Path, ffmpeg: str) -> None:
    tmp = dst.with_name(dst.stem + ".tmp.mp4")
    cmd = [
        ffmpeg, "-y", "-hide_banner", "-loglevel", "error", "-i", str(src), "-t", str(CLIP_SECONDS), "-an",
        "-vf", f"scale={OUT_WIDTH}:-2", "-c:v", "libx264", "-crf", str(CRF), "-preset", "medium",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(tmp),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        tmp.unlink(missing_ok=True)
        raise RuntimeError(f"ffmpeg failed for {src.name}: {exc.stderr.strip()[-300:]}") from exc
    tmp.replace(dst)


def delete_stills(clips_dir: Path, dry_run: bool) -> list[str]:
    removed = []
    for path in sorted(p for p in clips_dir.iterdir() if p.is_file() and is_video_file(p)):
        info = probe(path)
        if info.readable and info.distinct <= 1:
            removed.append(path.name)
            logger.info("%s ภาพนิ่งที่ถูกแปลงเป็นวิดีโอ: %s", "จะลบ" if dry_run else "ลบ", path.name)
            if not dry_run:
                path.unlink()
    return removed


def write_sources(clips_dir: Path, rows: list[tuple[str, str, float]]) -> Path:
    lines = [
        "# แหล่งที่มาของคลิปวิดีโอ",
        "",
        "คลิปใน `data/clips/` สร้างโดย `scripts/prepare_clips.py` จากไฟล์ต้นฉบับใน `data/raw_clips/`: "
        f"ตัดเหลือ {CLIP_SECONDS} วินาทีแรก และเข้ารหัสใหม่เป็น H.264 กว้าง {OUT_WIDTH} px (CRF {CRF}, ไม่มีเสียง) "
        "เพื่อจำลองภาพกล้องวงจรปิด ชื่อกล้อง โซน วันที่ และเวลาในชื่อไฟล์เป็นค่าสมมติสำหรับการสาธิต",
        "",
        "| ไฟล์ในระบบ | ไฟล์ต้นฉบับ | ความยาว (วินาที) | แหล่งที่มา / สัญญาอนุญาต |",
        "|---|---|---|---|",
        *(f"| `{out}` | `{orig}` | {dur:.1f} | {SOURCE_LABEL} |" for out, orig, dur in rows),
        "",
    ]
    path = clips_dir / "SOURCES.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Prepare CCTV-style clips from raw stock videos.")
    ap.add_argument("--raw", type=Path, default=REPO_ROOT / "data" / "raw_clips")
    ap.add_argument("--out", type=Path, default=REPO_ROOT / "data" / "clips")
    ap.add_argument("--end-date", type=date.fromisoformat, default=date.today(), help="last day of the 10-day window")
    ap.add_argument("--dry-run", action="store_true", help="only report what would be deleted/written")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)-7s %(message)s")

    args.out.mkdir(parents=True, exist_ok=True)
    delete_stills(args.out, args.dry_run)

    raws = sorted(p for p in args.raw.iterdir() if p.is_file() and is_video_file(p)) if args.raw.is_dir() else []
    if not raws:
        logger.error("ไม่พบวิดีโอใน %s", args.raw)
        return 1
    good: list[tuple[Path, Probe]] = []
    for raw in raws:
        info = probe(raw)
        if info.is_real_video:
            good.append((raw, info))
        else:
            logger.warning("ข้าม %s: %s", raw.name, info.reason())

    names = plan_names(len(good), args.end_date)
    ffmpeg = None if args.dry_run else ffmpeg_exe()
    rows: list[tuple[str, str, float]] = []
    print(f"\n{'output':<40} {'original':<36} {'src':>11} {'out':>11} {'dur':>5} {'distinct':>8}")
    for (raw, info), name in zip(good, names):
        dst = args.out / name
        if args.dry_run:
            print(f"{name:<40} {raw.name:<36} {info.width}x{info.height:<5} {'-':>11} {min(info.duration, CLIP_SECONDS):5.1f} {info.distinct:>8}")
            continue
        encode(raw, dst, ffmpeg)
        out = probe(dst)
        if not out.is_real_video or out.duration > CLIP_SECONDS + 0.5 or out.width != OUT_WIDTH:
            logger.error("ผลลัพธ์ไม่ผ่านการตรวจ %s: %s, %dx%d, %.1fs", name, out.reason(), out.width, out.height, out.duration)
            dst.unlink(missing_ok=True)
            continue
        rows.append((name, raw.name, out.duration))
        print(f"{name:<40} {raw.name:<36} {info.width}x{info.height:<5} {out.width}x{out.height:<5} {out.duration:5.1f} {out.distinct:>8}")

    if args.dry_run:
        return 0
    if not rows:
        logger.error("ไม่มีคลิปที่สร้างสำเร็จ")
        return 1
    sources = write_sources(args.out, rows)
    print(f"\n{len(rows)} clip(s) written to {args.out} · sources: {sources}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
