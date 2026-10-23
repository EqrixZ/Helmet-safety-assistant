"""Ablation of the two false-violation filters (Head threshold, temporal voting) on data/clips/.

Runs the self-trained model on every clip under four configs (Helmet threshold 0.35 in all):
  a: Head 0.35, no voting   b: Head 0.35, voting 0.4   c: Head 0.55, no voting   d: Head 0.55, voting 0.4
"No voting" is vote_ratio 0, i.e. one sampled frame with a Head box flags the clip.

Writes ``data/ablation_results.csv`` (one row per clip × config) and, for config a, an annotated
frame per clip in ``data/ablation_frames/`` so every Head box can be checked by eye.
With ``--truth CLIP[,CLIP...]`` (clips that really show a bare head) the ``ground_truth``
column is filled and ``data/ablation_summary.csv`` (false alarms, detections and misses per config) is written.

Usage: ``python scripts/ablation.py [--truth cam2_crane_2026-09-27_0850.mp4,...]``
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from backend import detector  # noqa: E402
from backend.frame_utils import KIND_BAD, KIND_OK, frame_filename_for_clip  # noqa: E402

HELMET_CONF = 0.35
CONFIGS = [  # (name, head_conf, vote_ratio)
    ("a", 0.35, 0.0),
    ("b", 0.35, 0.4),
    ("c", 0.55, 0.0),
    ("d", 0.55, 0.4),
]
COLUMNS = [
    "clip", "config", "head_conf", "vote_ratio", "sampled_frames", "head_frames", "head_frame_ratio",
    "head_max", "violation", "frame_path", "ground_truth",
]


def run(clips_dir: Path, frames_dir: Path) -> pd.DataFrame:
    model = detector.load_model()
    cmap = detector._class_map(model)
    rows = []
    for clip in detector.list_clips(clips_dir):
        frame = ""
        for name, head_conf, vote_ratio in CONFIGS:
            thresholds = {KIND_OK: HELMET_CONF, KIND_BAD: head_conf}
            out_frames = frames_dir if name == "a" else None
            r = detector._process_clip(clip, model, thresholds, cmap, out_frames, vote_ratio)
            if r is None:
                continue
            if name == "a" and r["frame_path"]:
                frame = str((frames_dir / frame_filename_for_clip(clip.name)).relative_to(REPO_ROOT))
            rows.append({
                "clip": clip.name, "config": name, "head_conf": head_conf, "vote_ratio": vote_ratio,
                "sampled_frames": r["_samples"], "head_frames": round(r["no_hardhat_ratio"] * r["_samples"]),
                "head_frame_ratio": r["no_hardhat_ratio"], "head_max": r["no_hardhat_max"],
                "violation": r["violation"], "frame_path": frame, "ground_truth": "",
            })
    return pd.DataFrame(rows, columns=COLUMNS)


def summarize(df: pd.DataFrame) -> pd.DataFrame:
    """False alarms, detections and misses per config (needs ``ground_truth``)."""
    out = []
    for name, head_conf, vote_ratio in CONFIGS:
        g = df[df["config"] == name]
        truth = g["ground_truth"].astype(bool)
        flagged = g["violation"].astype(bool)
        out.append({
            "config": name, "head_conf": head_conf, "vote_ratio": vote_ratio, "clips": len(g),
            "flagged": int(flagged.sum()), "false_alarms": int((flagged & ~truth).sum()),
            "detected": int((flagged & truth).sum()), "misses": int((~flagged & truth).sum()),
            "true_total": int(truth.sum()),
        })
    return pd.DataFrame(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Head-threshold / voting ablation on data/clips/.")
    ap.add_argument("--clips", type=Path, default=REPO_ROOT / "data" / "clips")
    ap.add_argument("--out", type=Path, default=REPO_ROOT / "data" / "ablation_results.csv")
    ap.add_argument("--frames", type=Path, default=REPO_ROOT / "data" / "ablation_frames")
    ap.add_argument("--truth", default=None, help="comma-separated clip names that really show a bare head")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.WARNING, format="%(levelname)-7s %(message)s")

    df = run(args.clips, args.frames)
    if df.empty:
        print(f"ไม่พบคลิปใน {args.clips}")
        return 1
    if args.truth is not None:
        truth = {c.strip() for c in args.truth.split(",") if c.strip()}
        unknown = truth - set(df["clip"])
        if unknown:
            print(f"ไม่รู้จักคลิป: {', '.join(sorted(unknown))}")
            return 1
        df["ground_truth"] = df["clip"].isin(truth)
    df.to_csv(args.out, index=False, encoding="utf-8")

    wide = df.pivot(index="clip", columns="config", values="violation")
    wide["head_max(a)"] = df[df["config"] == "a"].set_index("clip")["head_max"]
    wide["frame (config a)"] = df[df["config"] == "a"].set_index("clip")["frame_path"]
    wide["frame (default)"] = ["data/frames/" + frame_filename_for_clip(c) for c in wide.index]
    print(wide.to_string())
    print(f"\nSaved: {args.out}")
    if args.truth is not None:
        summary = summarize(df)
        summary_csv = args.out.with_name("ablation_summary.csv")
        summary.to_csv(summary_csv, index=False, encoding="utf-8")
        print(summary.to_string(index=False))
        print(f"Saved: {summary_csv}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
