"""Safe handling of uploaded files (clips and regulation documents)."""
from __future__ import annotations

import logging
import re
import shutil
from collections.abc import Iterable
from pathlib import Path

from fastapi import UploadFile

logger = logging.getLogger(__name__)

MAX_NAME_LENGTH = 200
_UNSAFE_CHARS = re.compile(r'[\x00-\x1f\x7f<>:"|?*]')


class UnsafeName(ValueError):
    """Filename rejected; ``args[0]`` is a Thai reason."""


def safe_filename(raw: str | None) -> str:
    """Return a sanitized basename or raise :class:`UnsafeName` (path traversal, hidden, empty…)."""
    name = (raw or "").strip()
    if not name:
        raise UnsafeName("ไม่มีชื่อไฟล์")
    if "/" in name or "\\" in name or name in {".", ".."} or ".." in Path(name).parts:
        raise UnsafeName("ชื่อไฟล์ไม่ปลอดภัย (มีการระบุเส้นทางโฟลเดอร์)")
    if name.startswith("."):
        raise UnsafeName("ไม่อนุญาตไฟล์ที่ขึ้นต้นด้วยจุด")
    name = _UNSAFE_CHARS.sub("_", name)
    if len(name) > MAX_NAME_LENGTH:
        raise UnsafeName(f"ชื่อไฟล์ยาวเกิน {MAX_NAME_LENGTH} ตัวอักษร")
    return name


def resolve_inside(folder: Path, name: str) -> Path | None:
    """``folder / name`` if it stays inside ``folder`` and ``name`` is already a safe basename."""
    try:
        if safe_filename(name) != name:
            return None
    except UnsafeName:
        return None
    base = folder.resolve()
    target = (base / name).resolve()
    return target if target.parent == base else None


def save_uploads(
    files: Iterable[UploadFile],
    folder: Path,
    extensions: tuple[str, ...],
    max_bytes: int | None = None,
    reserved: frozenset[str] = frozenset(),
) -> dict[str, list]:
    """Persist uploads into ``folder``; returns an ``UploadResult`` payload."""
    folder.mkdir(parents=True, exist_ok=True)
    saved: list[str] = []
    rejected: list[dict[str, str]] = []
    allowed = ", ".join(extensions)
    for upload in files:
        original = upload.filename or ""
        try:
            name = safe_filename(original)
        except UnsafeName as exc:
            rejected.append({"name": original, "reason": str(exc)})
            continue
        if name.lower() in reserved:
            rejected.append({"name": original, "reason": "ชื่อไฟล์นี้สงวนไว้สำหรับระบบ"})
            continue
        if Path(name).suffix.lower() not in extensions:
            rejected.append({"name": original, "reason": f"นามสกุลไฟล์ไม่รองรับ (รองรับเฉพาะ {allowed})"})
            continue
        target = folder / name
        tmp = folder / f".{name}.part"
        with tmp.open("wb") as out:
            shutil.copyfileobj(upload.file, out, length=1024 * 1024)
        if max_bytes is not None and tmp.stat().st_size > max_bytes:
            tmp.unlink(missing_ok=True)
            rejected.append({"name": original, "reason": f"ไฟล์มีขนาดเกิน {max_bytes // (1024 * 1024)} MB"})
            continue
        tmp.replace(target)
        saved.append(name)
        logger.info("Saved upload %s", target)
    return {"saved": saved, "rejected": rejected}
