"""scripts/prepare_clips.py: clip naming and the real-video (distinct frame) check."""
from __future__ import annotations

import importlib.util
import sys
from datetime import date

import cv2
import numpy as np
import pytest

from backend.config import REPO_ROOT
from backend.frame_utils import parse_clip_filename

_spec = importlib.util.spec_from_file_location("prepare_clips", REPO_ROOT / "scripts" / "prepare_clips.py")
prepare_clips = importlib.util.module_from_spec(_spec)
sys.modules["prepare_clips"] = prepare_clips  # dataclasses resolve their module via sys.modules
_spec.loader.exec_module(prepare_clips)


def test_names_parse_and_spread_over_cameras_zones_and_10_days() -> None:
    end = date(2026, 9, 30)
    names = prepare_clips.plan_names(12, end)
    parsed = [parse_clip_filename(n) for n in names]
    assert all(p["matched"] for p in parsed) and len(set(names)) == 12
    assert {p["zone"] for p in parsed} == set(prepare_clips.ZONES)
    assert {p["camera"] for p in parsed} == {"cam1", "cam2", "cam3", "cam4"}
    days = {p["datetime"].date() for p in parsed}
    assert all(0 <= (end - d).days < 10 for d in days) and len(days) >= 5
    assert all(7 <= p["datetime"].hour < 17 for p in parsed)
    assert prepare_clips.plan_names(12, end) == names  # deterministic


def _video(path, seconds: int, moving: bool, fps: int = 10) -> None:
    out = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (160, 120))
    for i in range(seconds * fps):
        frame = np.full((120, 160, 3), 90, np.uint8)
        x = (i * 3) % 140 if moving else 40
        cv2.rectangle(frame, (x, 40), (x + 20, 80), (255, 255, 255), -1)
        out.write(frame)
    out.release()


@pytest.mark.parametrize(("seconds", "moving", "real"), [(5, True, True), (5, False, False), (2, True, False)])
def test_probe_detects_stills_and_short_clips(tmp_path, seconds: int, moving: bool, real: bool) -> None:
    path = tmp_path / "clip.mp4"
    _video(path, seconds, moving)
    info = prepare_clips.probe(path)
    assert info.is_real_video is real
    if not moving:
        assert info.distinct == 1 and "ภาพนิ่ง" in info.reason()


def test_delete_stills_only_removes_single_frame_videos(tmp_path) -> None:
    _video(tmp_path / "still.mp4", 5, moving=False)
    _video(tmp_path / "moving.mp4", 5, moving=True)
    assert prepare_clips.delete_stills(tmp_path, dry_run=False) == ["still.mp4"]
    assert sorted(p.name for p in tmp_path.iterdir()) == ["moving.mp4"]
