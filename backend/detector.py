"""Helmet (hard-hat) detection over CCTV clips -> data/events.csv (CONTRACT §3, §6).

Usage:
    python -m backend.detector [--clips DIR] [--conf 0.35] [--out PATH]

Heavy dependencies (ultralytics, cv2, huggingface_hub) are imported lazily so that
``import backend.detector`` is cheap and safe for the API process.
"""
from __future__ import annotations

import argparse
import logging
import os
import shutil
import sys
import threading
import time
from pathlib import Path
from typing import Any, Callable

import pandas as pd

from backend.frame_utils import (
    EVENT_COLUMNS,
    KIND_BAD,
    KIND_OK,
    draw_detections,
    frame_filename_for_clip,
    is_video_file,
    parse_clip_filename,
)

logger = logging.getLogger("backend.detector")

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_HF_REPO = "keremberke/yolov8n-hard-hat-detection"
DEFAULT_HF_FILE = "best.pt"
DEFAULT_CONF = 0.35            # Helmet (and base) threshold
DEFAULT_HEAD_CONF = 0.55       # stricter: false Head boxes are what creates false violations
DEFAULT_VIOLATION_FRAME_RATIO = 0.4
FALLBACK_FPS = 25.0

MODELS_DIR = Path(__file__).resolve().parent / "models"
LOCAL_WEIGHTS = MODELS_DIR / "best.pt"

# Model class name -> events.csv count column. Covers the self-trained YOLO26s model
# (Head/Helmet) and the Hugging Face fallback (Hardhat/NO-Hardhat). Other classes are ignored.
CLASS_MAP: dict[str, str] = {
    "Helmet": KIND_OK,
    "Hardhat": KIND_OK,
    "Head": KIND_BAD,
    "NO-Hardhat": KIND_BAD,
}

_MODEL: Any = None
_MODEL_INFO: dict[str, Any] | None = None
_MODEL_LOCK = threading.Lock()


# --------------------------------------------------------------------------- #
# Config helpers (read env at call time)
# --------------------------------------------------------------------------- #
def data_dir() -> Path:
    d = os.getenv("DATA_DIR", "").strip()
    return Path(d).expanduser() if d else REPO_ROOT / "data"


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, "").strip() or default)
    except ValueError:
        logger.warning("Invalid %s=%r; using %s", name, os.getenv(name), default)
        return default


def default_conf() -> float:
    """Helmet / base threshold (CONF_THRESHOLD)."""
    return _env_float("CONF_THRESHOLD", DEFAULT_CONF)


def head_conf() -> float:
    return _env_float("HEAD_CONF_THRESHOLD", DEFAULT_HEAD_CONF)


def violation_frame_ratio() -> float:
    return _env_float("VIOLATION_FRAME_RATIO", DEFAULT_VIOLATION_FRAME_RATIO)


def class_thresholds(conf: float | None = None, head: float | None = None) -> dict[str, float]:
    """Per-kind confidence thresholds: hardhat <- CONF_THRESHOLD, no_hardhat <- HEAD_CONF_THRESHOLD."""
    return {
        KIND_OK: float(conf) if conf is not None else default_conf(),
        KIND_BAD: float(head) if head is not None else head_conf(),
    }


def model_repo() -> str:
    return os.getenv("HF_MODEL_REPO", "").strip() or DEFAULT_HF_REPO


def model_file() -> str:
    return os.getenv("HF_MODEL_FILE", "").strip() or DEFAULT_HF_FILE


# --------------------------------------------------------------------------- #
# Model
# --------------------------------------------------------------------------- #
def resolve_weights() -> tuple[Path, str]:
    """Return (weights path, source).

    The self-trained model at ``backend/models/best.pt`` is always used when present
    ("local"); Hugging Face is never contacted in that case. Fallback only: download
    ``HF_MODEL_REPO``/``HF_MODEL_FILE``, copy it to ``backend/models/best.pt`` ("downloaded")."""
    if LOCAL_WEIGHTS.is_file():
        return LOCAL_WEIGHTS, "local"
    from dotenv import load_dotenv  # lazy; env may not be loaded when called outside the API
    from huggingface_hub import hf_hub_download  # lazy

    load_dotenv(REPO_ROOT / ".env", override=False)
    repo, filename = model_repo(), model_file()
    logger.info("Downloading weights %s/%s from Hugging Face ...", repo, filename)
    cached = Path(hf_hub_download(repo_id=repo, filename=filename))
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    tmp = LOCAL_WEIGHTS.with_suffix(".pt.tmp")
    shutil.copyfile(cached, tmp)  # copyfile: HF cache blobs are read-only, don't inherit that
    tmp.replace(LOCAL_WEIGHTS)
    logger.info("Saved weights to %s", LOCAL_WEIGHTS)
    return LOCAL_WEIGHTS, "downloaded"


def _names(model) -> dict[int, str]:
    names = getattr(model, "names", {}) or {}
    if isinstance(names, (list, tuple)):
        names = dict(enumerate(names))
    return {int(k): str(v) for k, v in names.items()}


def _map_class(name: str) -> str | None:
    """CLASS_MAP lookup, exact first, then case-insensitive."""
    if name in CLASS_MAP:
        return CLASS_MAP[name]
    folded = {k.casefold(): v for k, v in CLASS_MAP.items()}
    return folded.get(name.casefold())


def _class_map(model) -> dict[int, str]:
    """model.names -> {class_id: "hardhat"|"no_hardhat"}; unmapped classes are dropped."""
    return {idx: kind for idx, name in _names(model).items() if (kind := _map_class(name))}


def _model_family(model) -> str | None:
    """e.g. "yolo26s" from the architecture yaml, else from the checkpoint's train args."""
    yaml_file = (getattr(getattr(model, "model", None), "yaml", None) or {}).get("yaml_file")
    base = yaml_file or ((getattr(model, "ckpt", None) or {}).get("train_args") or {}).get("model")
    return Path(str(base)).stem if base else None


def load_model():
    """Load the detector once (thread-safe) and check its classes map onto helmet/no-helmet."""
    global _MODEL, _MODEL_INFO
    with _MODEL_LOCK:
        if _MODEL is not None:
            return _MODEL
        from ultralytics import YOLO  # lazy

        path, source = resolve_weights()
        model = YOLO(str(path))
        names = _names(model)
        cmap = _class_map(model)
        kinds = set(cmap.values())
        if not kinds:
            raise RuntimeError(f"Model at {path} has no classes in CLASS_MAP: {names}")
        if kinds != {KIND_OK, KIND_BAD}:
            logger.warning("Model classes %s only map to %s; the other count will stay 0", names, kinds)
        family = _model_family(model)
        logger.info("Model loaded from %s (%s, %s). classes=%s mapping=%s", path, source, family, names,
                    {names[i]: k for i, k in cmap.items()})
        _MODEL = model
        _MODEL_INFO = {
            "path": str(path),
            "source": source,
            "family": family,
            "class_names": [names[i] for i in sorted(names)],
            "class_mapping": {names[i]: k for i, k in sorted(cmap.items())},
        }
        return model


def model_info() -> dict[str, Any]:
    """Details of the loaded model (loads it on first call)."""
    load_model()
    assert _MODEL_INFO is not None
    return {
        **_MODEL_INFO,
        "fallback_repo": model_repo(),
        "fallback_file": model_file(),
        "thresholds": class_thresholds(),
        "violation_frame_ratio": violation_frame_ratio(),
    }


def load_hf_model():
    """The Hugging Face model, straight from the HF cache (for --compare).

    Unlike resolve_weights() this never copies to backend/models/, so it cannot
    overwrite the self-trained weights."""
    from dotenv import load_dotenv  # lazy
    from huggingface_hub import hf_hub_download  # lazy
    from ultralytics import YOLO  # lazy

    load_dotenv(REPO_ROOT / ".env", override=False)
    return YOLO(hf_hub_download(repo_id=model_repo(), filename=model_file()))


def _detect_frame(model, frame, thresholds: dict[str, float], cmap: dict[int, str]) -> list[dict[str, Any]]:
    names = _names(model)
    results = model.predict(frame, conf=min(thresholds.values()), verbose=False)
    dets: list[dict[str, Any]] = []
    if not results:
        return dets
    boxes = getattr(results[0], "boxes", None)
    if boxes is None or len(boxes) == 0:
        return dets
    cls = boxes.cls.cpu().numpy().astype(int).tolist()
    confs = boxes.conf.cpu().numpy().tolist()
    xyxy = boxes.xyxy.cpu().numpy().tolist()
    for c, p, b in zip(cls, confs, xyxy):
        kind = cmap.get(c)
        if kind is None or p < thresholds[kind]:
            continue
        dets.append({"kind": kind, "label": names.get(c, kind), "conf": float(p),
                     "box": tuple(float(v) for v in b)})
    return dets


# --------------------------------------------------------------------------- #
# Per-clip processing
# --------------------------------------------------------------------------- #
def _process_clip(
    path: Path,
    model,
    thresholds: dict[str, float],
    cmap: dict[int, str],
    frames_dir: Path | None,
    vote_ratio: float,
) -> dict[str, Any] | None:
    """Return the per-clip metrics dict (without event_id) or None if unreadable.

    Temporal voting: the clip is a violation only if >=1 no_hardhat box appears in at least
    ``vote_ratio`` of the sampled frames. Keys starting with "_" are stats, not CSV columns.
    ``frames_dir=None`` skips writing the annotated frame (used by --compare)."""
    import cv2  # lazy

    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        logger.warning("Cannot open clip, skipping: %s", path.name)
        return None
    max_ok = max_bad = max_total = 0
    max_conf = 0.0
    n_sampled = 0
    bad_frames = 0            # sampled frames with >=1 no_hardhat box
    conf_sum, n_dets = 0.0, 0
    infer_s = 0.0
    # best violation frame: (no_hardhat count, frame, dets)
    best_bad: tuple[int, Any, list] | None = None
    best_any: tuple[int, Any, list] | None = None
    # JPEG-encoded sampled frames kept only until the first detection (for middle-frame fallback)
    plain_frames: list[bytes] | None = []
    try:
        fps = cap.get(cv2.CAP_PROP_FPS) or 0.0
        if not fps or fps != fps or fps <= 0 or fps > 1000:
            fps = FALLBACK_FPS
        step = max(1, int(round(fps)))


        idx = 0
        while True:
            if idx % step == 0:
                ok, frame = cap.read()
                if not ok or frame is None:
                    break
                n_sampled += 1
                t0 = time.perf_counter()
                dets = _detect_frame(model, frame, thresholds, cmap)
                infer_s += time.perf_counter() - t0
                n_ok = sum(1 for d in dets if d["kind"] == KIND_OK)
                n_bad = sum(1 for d in dets if d["kind"] == KIND_BAD)
                max_ok = max(max_ok, n_ok)
                max_bad = max(max_bad, n_bad)
                max_total = max(max_total, n_ok + n_bad)
                bad_frames += n_bad > 0
                conf_sum += sum(d["conf"] for d in dets)
                n_dets += len(dets)
                if dets:
                    max_conf = max(max_conf, max(d["conf"] for d in dets))
                    plain_frames = None
                    if n_bad > 0 and (best_bad is None or n_bad > best_bad[0]):
                        best_bad = (n_bad, frame.copy(), dets)
                    if best_any is None or len(dets) > best_any[0]:
                        best_any = (len(dets), frame.copy(), dets)
                elif plain_frames is not None:
                    enc_ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
                    if enc_ok:
                        plain_frames.append(buf.tobytes())
            else:
                if not cap.grab():
                    break
            idx += 1
    except Exception:  # corrupt stream mid-way
        logger.exception("Error while reading clip %s", path.name)
        if n_sampled == 0:
            return None
    finally:
        cap.release()

    if n_sampled == 0:
        logger.warning("No readable frames in clip, skipping: %s", path.name)
        return None

    bad_ratio = bad_frames / n_sampled
    violation = bad_frames > 0 and bad_ratio >= vote_ratio

    # Choose annotated frame (CONTRACT §3); the banner shows the clip-level (voted) decision.
    out_img = None
    if frames_dir is not None:
        if violation and best_bad is not None:
            out_img = draw_detections(best_bad[1], best_bad[2], violation=True)
        elif best_any is not None:
            out_img = draw_detections(best_any[1], best_any[2], violation=violation)
        elif plain_frames:
            import numpy as np  # lazy

            mid = plain_frames[(len(plain_frames) - 1) // 2]
            frame = cv2.imdecode(np.frombuffer(mid, dtype=np.uint8), cv2.IMREAD_COLOR)
            if frame is not None:
                out_img = draw_detections(frame, [])

    frame_path = ""
    if out_img is not None and frames_dir is not None:
        frames_dir.mkdir(parents=True, exist_ok=True)
        fname = frame_filename_for_clip(path.name)
        if cv2.imwrite(str(frames_dir / fname), out_img, [cv2.IMWRITE_JPEG_QUALITY, 88]):
            frame_path = fname
        else:
            logger.warning("Failed to write annotated frame for %s", path.name)

    meta = parse_clip_filename(path.name, mtime=path.stat().st_mtime)
    dt = meta["datetime"]
    return {
        "datetime": dt.strftime("%Y-%m-%dT%H:%M:%S"),
        "date": dt.strftime("%Y-%m-%d"),
        "time": dt.strftime("%H:%M"),
        "camera": meta["camera"],
        "zone": meta["zone"],
        "clip": path.name,
        "hardhat": int(max_ok),
        "no_hardhat": int(max_bad) if violation else 0,
        "total_person": int(max_total),
        "violation": bool(violation),
        "max_conf": round(float(max_conf), 3),
        "frame_path": frame_path,
        "no_hardhat_max": int(max_bad),
        "no_hardhat_ratio": round(bad_ratio, 3),
        "_samples": n_sampled,
        "_avg_conf": conf_sum / n_dets if n_dets else 0.0,
        "_infer_fps": n_sampled / infer_s if infer_s > 0 else 0.0,
    }


def list_clips(clips_dir: Path) -> list[Path]:
    if not clips_dir.is_dir():
        return []
    return sorted(p for p in clips_dir.iterdir() if p.is_file() and is_video_file(p))


def empty_events_df() -> pd.DataFrame:
    return pd.DataFrame(columns=EVENT_COLUMNS)


def write_events_csv(df: pd.DataFrame, out_csv: Path) -> None:
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    out = df[EVENT_COLUMNS].copy()
    out["violation"] = out["violation"].map(lambda v: "true" if bool(v) else "false")
    out["max_conf"] = out["max_conf"].map(lambda v: f"{float(v):.3f}")
    out["no_hardhat_ratio"] = out["no_hardhat_ratio"].map(lambda v: f"{float(v):.3f}")
    tmp = out_csv.with_suffix(out_csv.suffix + ".tmp")
    out.to_csv(tmp, index=False, encoding="utf-8")
    os.replace(tmp, out_csv)


# --------------------------------------------------------------------------- #
# Public API (CONTRACT §6)
# --------------------------------------------------------------------------- #
def run_detection(
    clips_dir: Path | None = None,
    out_csv: Path | None = None,
    frames_dir: Path | None = None,
    conf: float | None = None,
    progress_cb: Callable[[int, int, str], None] | None = None,
    head_conf: float | None = None,
    vote_ratio: float | None = None,
) -> pd.DataFrame:
    """Scan all clips, write events.csv (full overwrite) and annotated frames.

    Returns the rows written, or an empty DataFrame with EVENT_COLUMNS when there
    are no clips (events.csv is then left untouched).
    """
    base = data_dir()
    clips_dir = Path(clips_dir) if clips_dir is not None else base / "clips"
    out_csv = Path(out_csv) if out_csv is not None else base / "events.csv"
    frames_dir = Path(frames_dir) if frames_dir is not None else base / "frames"
    thresholds = class_thresholds(conf, head_conf)
    vote_ratio = float(vote_ratio) if vote_ratio is not None else violation_frame_ratio()

    clips = list_clips(clips_dir)
    total = len(clips)
    if total == 0:
        logger.info("ไม่พบคลิปวิดีโอใน %s — no clips found, events.csv not modified.", clips_dir)
        return empty_events_df()

    model = load_model()
    cmap = _class_map(model)
    logger.info(
        "Processing %d clip(s) from %s (helmet conf=%.2f, head conf=%.2f, violation frame ratio=%.2f)",
        total, clips_dir, thresholds[KIND_OK], thresholds[KIND_BAD], vote_ratio,
    )

    rows: list[dict[str, Any]] = []
    for i, clip in enumerate(clips):
        if progress_cb:
            _safe_cb(progress_cb, i, total, clip.name)
        try:
            row = _process_clip(clip, model, thresholds, cmap, frames_dir, vote_ratio)
        except Exception:
            logger.exception("Failed to process clip, skipping: %s", clip.name)
            row = None
        if row is not None:
            rows.append(row)
            logger.info(
                "%s: hardhat=%d no_hardhat=%d (max %d, in %.0f%% of frames) persons=%d violation=%s "
                "max_conf=%.3f samples=%d",
                clip.name, row["hardhat"], row["no_hardhat"], row["no_hardhat_max"],
                row["no_hardhat_ratio"] * 100, row["total_person"], row["violation"], row["max_conf"],
                row["_samples"],
            )
        if progress_cb:
            _safe_cb(progress_cb, i + 1, total, clip.name)

    if not rows:
        # Keep any existing log (or the sample fallback) rather than replacing it with nothing.
        logger.warning("ไม่สามารถประมวลผลคลิปใดได้ — ไม่เขียนทับ events.csv / No clip could be processed")
        return empty_events_df()
    df = pd.DataFrame(rows).drop(columns=[c for c in rows[0] if c.startswith("_")])
    df = df.sort_values(["datetime", "clip"], kind="stable").reset_index(drop=True)
    df.insert(0, "event_id", [f"EVT-{n:04d}" for n in range(1, len(df) + 1)])
    df = df[EVENT_COLUMNS]
    write_events_csv(df, out_csv)
    logger.info("Wrote %d event(s) to %s", len(df), out_csv)
    return df


COMPARISON_COLUMNS = [
    "clip", "model", "helmet", "head", "head_frame_ratio", "violation", "avg_conf", "infer_fps", "sampled_frames",
]


def compare_models(
    clips_dir: Path | None = None,
    out_csv: Path | None = None,
    conf: float | None = None,
    head_conf: float | None = None,
    vote_ratio: float | None = None,
) -> pd.DataFrame:
    """Run the self-trained model and the Hugging Face model on the same clips with the same
    thresholds and voting; write one row per (clip, model) to ``model_comparison.csv``.

    ``helmet``/``head`` are max per-frame counts; ``violation`` is the voted decision;
    ``avg_conf`` is the mean confidence of kept boxes; ``infer_fps`` counts model time only."""
    base = data_dir()
    clips = list_clips(Path(clips_dir) if clips_dir is not None else base / "clips")
    out_csv = Path(out_csv) if out_csv is not None else base / "model_comparison.csv"
    if not clips:
        logger.info("No clips to compare.")
        return pd.DataFrame(columns=COMPARISON_COLUMNS)
    thresholds = class_thresholds(conf, head_conf)
    vote_ratio = float(vote_ratio) if vote_ratio is not None else violation_frame_ratio()

    own = load_model()
    models = [(_MODEL_INFO["family"] if _MODEL_INFO and _MODEL_INFO["family"] else "self-trained", own)]
    hf = load_hf_model()
    models.append((f"{_model_family(hf) or 'hf'} (HF)", hf))

    rows: list[dict[str, Any]] = []
    for clip in clips:
        for label, model in models:
            r = _process_clip(clip, model, thresholds, _class_map(model), None, vote_ratio)
            if r is None:
                continue
            rows.append({
                "clip": clip.name, "model": label, "helmet": r["hardhat"], "head": r["no_hardhat_max"],
                "head_frame_ratio": r["no_hardhat_ratio"], "violation": r["violation"],
                "avg_conf": round(r["_avg_conf"], 3), "infer_fps": round(r["_infer_fps"], 1),
                "sampled_frames": r["_samples"],
            })
    df = pd.DataFrame(rows, columns=COMPARISON_COLUMNS)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_csv, index=False)
    logger.info("Wrote model comparison (%d rows) to %s", len(df), out_csv)
    return df


def comparison_table(df: pd.DataFrame) -> str:
    """Side-by-side text table: one line per clip, one column group per model."""
    if df.empty:
        return "(no rows)"
    wide = df.pivot(index="clip", columns="model", values=["helmet", "head", "violation", "avg_conf", "infer_fps"])
    wide = wide.swaplevel(axis=1).sort_index(axis=1, level=0, sort_remaining=False)
    order = ["helmet", "head", "violation", "avg_conf", "infer_fps"]
    wide = wide.reindex(columns=[(m, c) for m in df["model"].unique() for c in order])
    wide.columns = [f"{m}:{c}" for m, c in wide.columns]
    return wide.to_string()


def _safe_cb(cb: Callable[[int, int, str], None], processed: int, total: int, name: str) -> None:
    try:
        cb(processed, total, name)
    except Exception:
        logger.exception("progress_cb raised; ignoring")


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def main(argv: list[str] | None = None) -> int:
    try:
        from dotenv import load_dotenv

        load_dotenv(REPO_ROOT / ".env")
    except Exception:
        pass

    ap = argparse.ArgumentParser(prog="python -m backend.detector", description="Detect hard-hat violations in CCTV clips.")
    ap.add_argument("--clips", type=Path, default=None, help="clips folder (default DATA_DIR/clips)")
    ap.add_argument("--conf", type=float, default=None, help=f"Helmet confidence threshold (default CONF_THRESHOLD or {DEFAULT_CONF})")
    ap.add_argument("--head-conf", type=float, default=None,
                    help=f"Head / no-hardhat confidence threshold (default HEAD_CONF_THRESHOLD or {DEFAULT_HEAD_CONF})")
    ap.add_argument("--vote-ratio", type=float, default=None,
                    help=f"min share of sampled frames with a Head box to flag a violation "
                         f"(default VIOLATION_FRAME_RATIO or {DEFAULT_VIOLATION_FRAME_RATIO})")
    ap.add_argument("--compare", action="store_true",
                    help="run the self-trained and Hugging Face models side by side; writes "
                         "DATA_DIR/model_comparison.csv (or --out) and does not touch events.csv")
    ap.add_argument("--out", type=Path, default=None,
                    help="output CSV (default DATA_DIR/events.csv, or DATA_DIR/model_comparison.csv with --compare)")
    ap.add_argument("--frames", type=Path, default=None, help="annotated frames folder (default DATA_DIR/frames)")
    args = ap.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-7s %(message)s", datefmt="%H:%M:%S")
    started = time.time()

    if args.compare:
        try:
            cmp = compare_models(args.clips, args.out, args.conf, args.head_conf, args.vote_ratio)
        except Exception as exc:
            logger.exception("Comparison failed: %s", exc)
            return 1
        print()
        print(comparison_table(cmp))
        print(f"\nDone in {time.time() - started:.1f}s")
        return 0

    def progress(done: int, total: int, name: str) -> None:
        width = 28
        filled = int(width * done / total) if total else width
        bar = "#" * filled + "-" * (width - filled)
        verb = "done" if done > 0 and _last.get("name") == name else "processing"
        _last["name"] = name
        print(f"  [{bar}] {done}/{total}  {verb:<10} {name}", flush=True)

    _last: dict[str, str] = {}

    try:
        df = run_detection(clips_dir=args.clips, out_csv=args.out, frames_dir=args.frames, conf=args.conf,
                           progress_cb=progress, head_conf=args.head_conf, vote_ratio=args.vote_ratio)
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        return 130
    except Exception as exc:
        logger.exception("Detection failed: %s", exc)
        return 1

    if df.empty:
        print("No events written (no clips found or none readable).")
        return 0
    n_v = int(df["violation"].sum())
    print()
    print(f"Done in {time.time() - started:.1f}s — {len(df)} clip(s), {n_v} violation(s).")
    print(df[["event_id", "clip", "hardhat", "no_hardhat_max", "no_hardhat_ratio", "violation", "max_conf"]].to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
