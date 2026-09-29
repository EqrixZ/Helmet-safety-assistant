"""Clip filename parsing and frame annotation helpers (CONTRACT §2, §3, §6).

Kept lightweight: cv2/numpy are imported lazily inside the drawing helpers so
that importing this module (e.g. from the API) never pulls heavy deps.
"""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

EVENT_COLUMNS: list[str] = [
    "event_id",
    "datetime",
    "date",
    "time",
    "camera",
    "zone",
    "clip",
    "hardhat",
    "no_hardhat",
    "total_person",
    "violation",
    "max_conf",
    "frame_path",
    # Temporal voting (appended so older logs stay readable): the raw max Head count over
    # sampled frames, and the share of sampled frames with >=1 Head. ``no_hardhat`` and
    # ``violation`` above only count once that share reaches VIOLATION_FRAME_RATIO.
    "no_hardhat_max",
    "no_hardhat_ratio",
]

VIDEO_EXTENSIONS: tuple[str, ...] = (".mp4", ".mov", ".avi", ".mkv")

CLIP_RE = re.compile(
    r"^cam(\d+)_([a-z0-9]+)_(\d{4}-\d{2}-\d{2})_(\d{2})(\d{2})\.(mp4|mov|avi|mkv)$",
    re.IGNORECASE,
)

# Detection kinds (= events.csv count columns). Model class names are mapped to these
# at runtime by backend.detector.CLASS_MAP; nothing here depends on a model's labels.
KIND_OK = "hardhat"
KIND_BAD = "no_hardhat"


def parse_clip_filename(name: str, mtime: float | None = None) -> dict[str, Any]:
    """Parse ``cam{ID}_{zone}_{YYYY-MM-DD}_{HHMM}.{ext}``.

    Returns ``{"camera", "zone", "datetime", "matched"}``. On a non-matching name
    or an invalid date/time, camera/zone are ``"unknown"`` and datetime is the
    file mtime (local time) or now.
    """
    base = Path(str(name)).name
    m = CLIP_RE.match(base)
    if m:
        cam_id, zone, date_s, hh, mm, _ext = m.groups()
        try:
            dt = datetime.strptime(f"{date_s} {hh}:{mm}", "%Y-%m-%d %H:%M")
        except ValueError:
            dt = None
        if dt is not None:
            return {
                "camera": f"cam{int(cam_id)}" if cam_id.isdigit() else f"cam{cam_id}",
                "zone": zone.lower(),
                "datetime": dt,
                "matched": True,
            }
    if mtime is not None:
        dt = datetime.fromtimestamp(mtime)
    else:
        dt = datetime.now()
    return {
        "camera": "unknown",
        "zone": "unknown",
        "datetime": dt.replace(microsecond=0),
        "matched": False,
    }


def is_video_file(path: Path | str) -> bool:
    return Path(path).suffix.lower() in VIDEO_EXTENSIONS


def frame_filename_for_clip(clip_name: str) -> str:
    """Annotated-frame basename for a clip: clip stem + ``.jpg``."""
    return Path(clip_name).stem + ".jpg"


# --------------------------------------------------------------------------- #
# Drawing
# --------------------------------------------------------------------------- #
# BGR colours
_GREEN = (80, 175, 76)       # #4CAF50
_ORANGE = (40, 140, 242)     # #F28C28
_RED = (48, 48, 220)
_WHITE = (255, 255, 255)
_DARK = (30, 30, 30)


def _color_for(kind: str) -> tuple[int, int, int]:
    return _GREEN if kind == KIND_OK else _ORANGE


def draw_detections(frame_bgr, detections: Iterable[dict[str, Any]], violation: bool | None = None):
    """Draw boxes, label chips and a count banner on a copy of ``frame_bgr``.

    ``detections``: iterable of ``{"kind": "hardhat"|"no_hardhat", "label": <model class
    name>, "conf": float, "box": (x1, y1, x2, y2)}``. ``violation`` sets the banner status
    (the clip-level decision); by default it is "any no_hardhat box in this frame".
    """
    import cv2  # lazy

    img = frame_bgr.copy()
    h, w = img.shape[:2]
    scale = max(0.45, min(1.2, w / 1280 * 0.8))
    thick = max(1, int(round(w / 640)))
    font = cv2.FONT_HERSHEY_SIMPLEX

    dets = list(detections or [])
    n_ok = sum(1 for d in dets if d.get("kind") == KIND_OK)
    n_bad = sum(1 for d in dets if d.get("kind") == KIND_BAD)

    for d in dets:
        kind = d.get("kind")
        if kind not in (KIND_OK, KIND_BAD):
            continue
        label = d.get("label") or kind
        x1, y1, x2, y2 = (int(round(v)) for v in d["box"])
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w - 1, x2), min(h - 1, y2)
        color = _color_for(kind)
        cv2.rectangle(img, (x1, y1), (x2, y2), color, thick + 1, cv2.LINE_AA)

        text = f"{label} {float(d.get('conf', 0.0)):.2f}"
        (tw, th), base = cv2.getTextSize(text, font, scale * 0.6, max(1, thick))
        pad = 4
        cy1 = y1 - th - base - 2 * pad
        if cy1 < 0:  # put chip inside the box when too close to the top
            cy1 = y1
        cy2 = cy1 + th + base + 2 * pad
        cx2 = min(w - 1, x1 + tw + 2 * pad)
        cv2.rectangle(img, (x1, cy1), (cx2, cy2), color, -1, cv2.LINE_AA)
        cv2.putText(img, text, (x1 + pad, cy2 - base - pad + 1), font, scale * 0.6,
                    _WHITE, max(1, thick), cv2.LINE_AA)

    # Top-left banner with counts (semi-transparent)
    banner = f"Helmet on: {n_ok}   No helmet: {n_bad}"
    status = "VIOLATION" if (n_bad > 0 if violation is None else violation) else "OK"
    fs = scale * 0.7
    (bw, bh), bb = cv2.getTextSize(banner, font, fs, max(1, thick))
    (sw, sh), _ = cv2.getTextSize(status, font, fs, max(1, thick) + 1)
    pad = 8
    box_w = bw + sw + 5 * pad
    box_h = bh + bb + 2 * pad
    overlay = img.copy()
    cv2.rectangle(overlay, (8, 8), (8 + box_w, 8 + box_h), _DARK, -1)
    img = cv2.addWeighted(overlay, 0.65, img, 0.35, 0)
    ty = 8 + pad + bh
    cv2.putText(img, banner, (8 + pad, ty), font, fs, _WHITE, max(1, thick), cv2.LINE_AA)
    sx = 8 + bw + 3 * pad
    scol = _RED if n_bad > 0 else _GREEN
    cv2.rectangle(img, (sx - pad // 2, 8 + pad // 2), (sx + sw + pad // 2, 8 + box_h - pad // 2), scol, -1)
    cv2.putText(img, status, (sx, ty), font, fs, _WHITE, max(1, thick) + 1, cv2.LINE_AA)
    return img
