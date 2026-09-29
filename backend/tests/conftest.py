"""Shared fixtures: an isolated DATA_DIR (copy of the sample log) and an API client."""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend import data

REPO_DATA = Path(__file__).resolve().parents[2] / "data"


@pytest.fixture()
def data_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Temporary data dir containing only ``events_sample.csv``; LLM unconfigured."""
    for sub in ("clips", "frames", "regulations", "reports"):
        (tmp_path / sub).mkdir()
    shutil.copy(REPO_DATA / "events_sample.csv", tmp_path / "events_sample.csv")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("LLM_API_KEY", "")
    monkeypatch.delenv("SITE_NAME", raising=False)
    data.invalidate_cache()
    yield tmp_path
    data.invalidate_cache()


@pytest.fixture()
def client(data_dir: Path) -> TestClient:
    from backend.main import app

    return TestClient(app)
