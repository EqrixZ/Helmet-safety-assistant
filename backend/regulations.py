"""Regulation documents in ``data/regulations`` (``README.md`` there is always excluded)."""
from __future__ import annotations

import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Any

from pypdf import PdfReader

from backend import config

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS: tuple[str, ...] = (".md", ".txt", ".pdf")
EXCLUDED_NAMES = frozenset({"readme.md"})

_text_cache: dict[tuple[str, int, int], str] = {}
_lock = threading.Lock()


def list_paths() -> list[Path]:
    """Regulation files sorted by name."""
    folder = config.regulations_dir()
    if not folder.is_dir():
        return []
    return sorted(
        (
            p
            for p in folder.iterdir()
            if p.is_file() and p.suffix.lower() in ALLOWED_EXTENSIONS and p.name.lower() not in EXCLUDED_NAMES
        ),
        key=lambda p: p.name.lower(),
    )


def _extract(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        reader = PdfReader(str(path))
        return "\n".join((page.extract_text() or "") for page in reader.pages).strip()
    return path.read_text(encoding="utf-8", errors="replace").strip()


def read_text(path: Path) -> str:
    """Plain text of a document (cached by mtime/size; unreadable files yield "")."""
    stat = path.stat()
    key = (str(path), stat.st_mtime_ns, stat.st_size)
    with _lock:
        if key in _text_cache:
            return _text_cache[key]
    try:
        text = _extract(path)
    except Exception:  # noqa: BLE001 — a broken PDF must not break chat
        logger.exception("Could not extract text from %s", path)
        text = ""
    with _lock:
        _text_cache[key] = text
    return text


def describe(path: Path) -> dict[str, Any]:
    """``RegulationDoc`` payload."""
    stat = path.stat()
    return {
        "name": path.name,
        "size": stat.st_size,
        "type": path.suffix.lower().lstrip("."),
        "chars": len(read_text(path)),
        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
    }


def find(name: str) -> Path | None:
    """Listed document with exactly this file name, if any."""
    return next((p for p in list_paths() if p.name == name), None)
