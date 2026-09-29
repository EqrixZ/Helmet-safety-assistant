from datetime import datetime

import pandas as pd

from backend.frame_utils import (
    EVENT_COLUMNS,
    frame_filename_for_clip,
    parse_clip_filename,
)

MTIME = datetime(2025, 1, 2, 3, 4, 5).timestamp()


def test_valid_example():
    r = parse_clip_filename("cam2_crane_2026-09-29_1405.mp4")
    assert r == {"camera": "cam2", "zone": "crane", "datetime": datetime(2026, 9, 29, 14, 5), "matched": True}


def test_uppercase_extension_and_zone():
    r = parse_clip_filename("CAM3_Scaffold_2026-09-28_0830.MP4")
    assert r["matched"] is True
    assert r["camera"] == "cam3"
    assert r["zone"] == "scaffold"
    assert r["datetime"] == datetime(2026, 9, 28, 8, 30)


def test_mov_extension():
    r = parse_clip_filename("cam1_entrance_2026-09-29_0900.mov")
    assert r["matched"] and r["zone"] == "entrance"
    assert r["datetime"] == datetime(2026, 9, 29, 9, 0)


def test_non_matching_uses_mtime():
    r = parse_clip_filename("random_video.mp4", mtime=MTIME)
    assert r == {"camera": "unknown", "zone": "unknown", "datetime": datetime(2025, 1, 2, 3, 4, 5), "matched": False}


def test_non_matching_without_mtime_uses_now():
    r = parse_clip_filename("whatever.mp4")
    assert not r["matched"]
    assert abs((datetime.now() - r["datetime"]).total_seconds()) < 5


def test_invalid_date_falls_back():
    r = parse_clip_filename("cam2_crane_2026-13-45_1405.mp4", mtime=MTIME)
    assert r["matched"] is False
    assert r["camera"] == "unknown" and r["zone"] == "unknown"
    assert r["datetime"] == datetime(2025, 1, 2, 3, 4, 5)


def test_invalid_time_falls_back():
    r = parse_clip_filename("cam2_crane_2026-09-29_2575.mp4", mtime=MTIME)
    assert r["matched"] is False
    assert r["datetime"] == datetime(2025, 1, 2, 3, 4, 5)


def test_unsupported_extension_not_matched():
    assert parse_clip_filename("cam2_crane_2026-09-29_1405.webm", mtime=MTIME)["matched"] is False


def test_frame_filename():
    assert frame_filename_for_clip("cam2_crane_2026-09-29_1405.mp4") == "cam2_crane_2026-09-29_1405.jpg"


class _FakeModel:
    def __init__(self, names):
        self.names = names


def test_class_map_self_trained_model():
    from backend.detector import _class_map

    assert _class_map(_FakeModel({0: "Head", 1: "Helmet"})) == {0: "no_hardhat", 1: "hardhat"}


def test_class_map_hf_fallback_model_and_unknown_classes():
    from backend.detector import _class_map

    assert _class_map(_FakeModel({0: "Hardhat", 1: "NO-Hardhat"})) == {0: "hardhat", 1: "no_hardhat"}
    assert _class_map(_FakeModel(["helmet", "person", "HEAD"])) == {0: "hardhat", 2: "no_hardhat"}


def test_run_detection_empty_dir(tmp_path):
    from backend.detector import run_detection

    clips = tmp_path / "clips"
    clips.mkdir()
    (clips / ".gitkeep").touch()
    out_csv = tmp_path / "events.csv"
    df = run_detection(clips_dir=clips, out_csv=out_csv, frames_dir=tmp_path / "frames")
    assert isinstance(df, pd.DataFrame)
    assert df.empty
    assert list(df.columns) == EVENT_COLUMNS
    assert not out_csv.exists()


# --- weight resolution ------------------------------------------------------------------

def test_resolve_weights_prefers_local(tmp_path, monkeypatch):
    from backend import detector

    local = tmp_path / "best.pt"
    local.write_bytes(b"x")
    monkeypatch.setattr(detector, "LOCAL_WEIGHTS", local)
    assert detector.resolve_weights() == (local, "local")


def test_resolve_weights_downloads_and_copies(tmp_path, monkeypatch):
    import huggingface_hub

    from backend import detector

    cached = tmp_path / "hf-cache" / "best.pt"
    cached.parent.mkdir()
    cached.write_bytes(b"weights")
    calls = []
    monkeypatch.setattr(huggingface_hub, "hf_hub_download", lambda **kw: calls.append(kw) or str(cached))
    monkeypatch.setattr(detector, "MODELS_DIR", tmp_path / "models")
    monkeypatch.setattr(detector, "LOCAL_WEIGHTS", tmp_path / "models" / "best.pt")
    monkeypatch.setenv("HF_MODEL_REPO", "some/repo")

    path, source = detector.resolve_weights()
    assert source == "downloaded" and path.read_bytes() == b"weights"
    assert calls == [{"repo_id": "some/repo", "filename": "best.pt"}]


# --- per-class thresholds & temporal voting --------------------------------------------

class _Arr:
    def __init__(self, values):
        import numpy as np

        self._a = np.asarray(values, dtype=float)

    def cpu(self):
        return self

    def numpy(self):
        return self._a


class _Boxes:
    def __init__(self, dets):  # dets: [(cls, conf)]
        self.cls = _Arr([c for c, _ in dets])
        self.conf = _Arr([p for _, p in dets])
        self.xyxy = _Arr([[10, 10, 40, 40] for _ in dets])

    def __len__(self):
        return len(self.cls.numpy())


class _ScriptedModel:
    """Head/Helmet model whose i-th predict() call returns ``script[i]`` (list of (cls, conf))."""

    names = {0: "Head", 1: "Helmet"}

    def __init__(self, script):
        self.script, self.calls, self.min_confs = list(script), 0, []

    def predict(self, frame, conf, verbose=False):
        self.min_confs.append(conf)
        dets = [d for d in self.script[self.calls] if d[1] >= conf]
        self.calls += 1
        return [type("R", (), {"boxes": _Boxes(dets)})()]


def _write_clip(path, seconds, fps=5):
    import cv2
    import numpy as np

    out = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (64, 48))
    for _ in range(seconds * fps):
        out.write(np.full((48, 64, 3), 128, np.uint8))
    out.release()


def _run(tmp_path, script, vote_ratio=0.4):
    from backend import detector

    clip = tmp_path / "cam1_crane_2026-09-29_1000.mp4"
    _write_clip(clip, len(script))
    model = _ScriptedModel(script)
    th = {"hardhat": 0.35, "no_hardhat": 0.55}
    row = detector._process_clip(clip, model, th, detector._class_map(model), tmp_path / "frames", vote_ratio)
    assert model.calls == len(script)  # one sampled frame per second
    return row, model


def test_sporadic_head_is_voted_out(tmp_path):
    head, helmet = (0, 0.9), (1, 0.8)
    row, _ = _run(tmp_path, [[helmet]] * 4 + [[head, helmet]])  # Head in 1/5 frames = 20%
    assert row["violation"] is False and row["no_hardhat"] == 0
    assert row["no_hardhat_max"] == 1 and row["no_hardhat_ratio"] == 0.2


def test_persistent_head_is_a_violation(tmp_path):
    head = (0, 0.9)
    row, _ = _run(tmp_path, [[head]] * 2 + [[]] * 3)  # 2/5 = 40% -> meets the ratio
    assert row["violation"] is True and row["no_hardhat"] == 1 and row["no_hardhat_ratio"] == 0.4


def test_head_uses_its_own_higher_threshold(tmp_path):
    weak_head, weak_helmet = (0, 0.5), (1, 0.4)  # head below 0.55, helmet above 0.35
    row, model = _run(tmp_path, [[weak_head, weak_helmet]] * 3)
    assert row["no_hardhat_max"] == 0 and row["hardhat"] == 1 and row["violation"] is False
    assert set(model.min_confs) == {0.35}  # predict at the lowest threshold, then filter per class
