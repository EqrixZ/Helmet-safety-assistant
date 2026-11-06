"""Runtime configuration (CONTRACT §1).

`.env` at the repo root is loaded once at import time (without overriding real
environment variables). Settings are then read from ``os.environ`` on every call
so tests and long-running processes pick up changes (e.g. a temporary DATA_DIR).
"""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
APP_VERSION = "1.0.0"

DEFAULT_LLM_BASE_URL = "https://api.openai.com/v1"
DEFAULT_LLM_MODEL = "gpt-4o-mini"
DEFAULT_LLM_RPM = 4.0  # free tiers (e.g. Gemini: 5 RPM) — stay just under the limit
DEFAULT_CONF_THRESHOLD = 0.35
DEFAULT_HF_MODEL_REPO = "keremberke/yolov8n-hard-hat-detection"
DEFAULT_HF_MODEL_FILE = "best.pt"
DEFAULT_SITE_NAME = "โครงการก่อสร้างอาคาร A"

# Bare Thai names; sentences add the "โซน" prefix via textfmt.zone_name().
ZONE_LABELS: dict[str, str] = {
    "entrance": "ทางเข้า",
    "crane": "เครน",
    "scaffold": "นั่งร้าน",
    "floor3": "ชั้น 3",
    "warehouse": "คลังวัสดุ",
}

# English names; sentences add the " zone" suffix via textfmt.zone_name(..., "en").
ZONE_LABELS_EN: dict[str, str] = {
    "entrance": "Entrance",
    "crane": "Crane",
    "scaffold": "Scaffold",
    "floor3": "Floor 3",
    "warehouse": "Warehouse",
}

load_dotenv(REPO_ROOT / ".env", override=False)
logger = logging.getLogger(__name__)


def _env(name: str, default: str) -> str:
    value = os.environ.get(name, "").strip()
    return value or default


def _env_float(name: str, default: float) -> float:
    try:
        return float(_env(name, str(default)))
    except ValueError:
        logger.warning("Invalid %s=%r, using default %s", name, os.environ.get(name), default)
        return default


@dataclass(frozen=True)
class Settings:
    """Snapshot of environment-driven settings."""

    llm_api_key: str
    llm_base_url: str
    llm_model: str
    llm_rpm: float                 # client-side requests/minute per provider; <= 0 disables the throttle
    llm_fallback_api_key: str
    llm_fallback_base_url: str
    llm_fallback_model: str
    conf_threshold: float
    hf_model_repo: str
    hf_model_file: str
    site_name_default: str
    data_dir: Path


def get_settings() -> Settings:
    """Read settings from the current environment."""
    return Settings(
        llm_api_key=os.environ.get("LLM_API_KEY", "").strip(),
        llm_base_url=_env("LLM_BASE_URL", DEFAULT_LLM_BASE_URL),
        llm_model=_env("LLM_MODEL", DEFAULT_LLM_MODEL),
        llm_rpm=_env_float("LLM_RPM", DEFAULT_LLM_RPM),
        llm_fallback_api_key=os.environ.get("LLM_FALLBACK_API_KEY", "").strip(),
        llm_fallback_base_url=os.environ.get("LLM_FALLBACK_BASE_URL", "").strip(),
        llm_fallback_model=os.environ.get("LLM_FALLBACK_MODEL", "").strip(),
        conf_threshold=_env_float("CONF_THRESHOLD", DEFAULT_CONF_THRESHOLD),
        hf_model_repo=_env("HF_MODEL_REPO", DEFAULT_HF_MODEL_REPO),
        hf_model_file=_env("HF_MODEL_FILE", DEFAULT_HF_MODEL_FILE),
        site_name_default=_env("SITE_NAME", DEFAULT_SITE_NAME),
        data_dir=Path(_env("DATA_DIR", str(REPO_ROOT / "data"))).expanduser().resolve(),
    )


# --- path helpers -------------------------------------------------------------

def data_dir() -> Path:
    return get_settings().data_dir


def clips_dir() -> Path:
    return data_dir() / "clips"


def frames_dir() -> Path:
    return data_dir() / "frames"


def regulations_dir() -> Path:
    return data_dir() / "regulations"


def reports_dir() -> Path:
    return data_dir() / "reports"


def events_csv() -> Path:
    return data_dir() / "events.csv"


def sample_events_csv() -> Path:
    return data_dir() / "events_sample.csv"


def settings_json() -> Path:
    return data_dir() / "settings.json"


def eval_results_csv() -> Path:
    return data_dir() / "eval_results.csv"


# --- site settings (data/settings.json) ----------------------------------------

def site_name() -> str:
    """Site name from ``settings.json``, falling back to the ``SITE_NAME`` env var."""
    path = settings_json()
    if path.is_file():
        try:
            name = str(json.loads(path.read_text(encoding="utf-8")).get("site_name", "")).strip()
            if name:
                return name
        except (OSError, ValueError, AttributeError):
            logger.warning("Could not read %s; using SITE_NAME", path)
    return get_settings().site_name_default


def save_site_name(name: str) -> str:
    """Persist the site name to ``settings.json`` and return it."""
    path = settings_json()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"site_name": name}, ensure_ascii=False, indent=2), encoding="utf-8")
    return name


def zone_label(zone: str) -> str:
    """Thai display label for a zone key (raw key for unknown zones)."""
    return ZONE_LABELS.get(zone, zone)
