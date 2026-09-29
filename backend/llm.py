"""Thin wrapper around the ``openai`` client for any OpenAI-compatible endpoint (CONTRACT §7).

Works with OpenAI, Typhoon (https://api.opentyphoon.ai/v1), Gemini's OpenAI-compatible
endpoint and Ollama (http://localhost:11434/v1) — only ``LLM_BASE_URL``/``LLM_MODEL`` change.

Rate-limit handling (chat, reports and evaluation all go through ``_run``):

* **Throttle** — at most ``LLM_RPM`` requests per rolling minute per provider (every
  attempt counts, including retries); callers block until a slot frees up.
* **Retry** — HTTP 429/503 are retried up to ``MAX_ATTEMPTS`` times with exponential
  backoff (2, 4, 8, 16 s), or the server's ``Retry-After`` when it sends one.
* **Fallback** — if ``LLM_FALLBACK_*`` is set and the primary still fails after retries
  (or is unreachable / 5xx), the request goes to the fallback, and the primary is skipped
  for ``PRIMARY_COOLDOWN_S`` so later requests don't each pay the full retry cost.
"""
from __future__ import annotations

import logging
import re
import threading
import time
from collections import deque
from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass
from email.utils import parsedate_to_datetime
from functools import lru_cache
from typing import Any, Literal, TypeVar
from urllib.parse import urlparse

import openai
from openai import OpenAI

from backend.config import get_settings

logger = logging.getLogger(__name__)

NOT_CONFIGURED_MESSAGE = "ยังไม่ได้ตั้งค่า LLM_API_KEY — กรุณาใส่ค่าในไฟล์ .env แล้วรีสตาร์ต backend"
TEMPERATURE = 0.2
TIMEOUT_S = 90.0

RETRY_STATUSES = frozenset({429, 503})
MAX_ATTEMPTS = 5
BACKOFF_BASE_S = 2.0
MAX_WAIT_S = 60.0            # cap on a single backoff / Retry-After wait
PRIMARY_COOLDOWN_S = 60.0    # after the primary gives up, go straight to the fallback for this long

Message = dict[str, str]
ProviderName = Literal["primary", "fallback"]
T = TypeVar("T")


class LLMNotConfigured(RuntimeError):
    """Raised when ``LLM_API_KEY`` is empty."""

    code = "LLM_NOT_CONFIGURED"

    def __init__(self) -> None:
        super().__init__(NOT_CONFIGURED_MESSAGE)
        self.message = NOT_CONFIGURED_MESSAGE


class LLMError(RuntimeError):
    """Raised when the upstream LLM call fails; ``message`` is Thai and user-facing.
    ``info`` records the providers/retries tried before giving up (None for mid-stream errors)."""

    code = "LLM_ERROR"

    def __init__(self, message: str, info: CallInfo | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.info = info


# --- providers ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Provider:
    name: ProviderName
    api_key: str
    base_url: str
    model: str

    @property
    def label(self) -> str:
        return f"{self.name} ({self.model} @ {urlparse(self.base_url).netloc or self.base_url})"

    def public(self) -> dict[str, str]:
        return {"name": self.name, "model": self.model, "base_url": self.base_url}


def providers() -> list[Provider]:
    """Configured providers in preference order: primary, then the optional fallback."""
    s = get_settings()
    out: list[Provider] = []
    if s.llm_api_key:
        out.append(Provider("primary", s.llm_api_key, s.llm_base_url, s.llm_model))
    if s.llm_fallback_api_key and s.llm_fallback_base_url and s.llm_fallback_model:
        out.append(Provider("fallback", s.llm_fallback_api_key, s.llm_fallback_base_url, s.llm_fallback_model))
    return out


def is_configured() -> bool:
    return bool(get_settings().llm_api_key)


def fallback_configured() -> bool:
    return any(p.name == "fallback" for p in providers())


@lru_cache(maxsize=4)
def _client(api_key: str, base_url: str) -> OpenAI:
    # max_retries=0: retries/backoff are handled here so they are counted and throttled.
    return OpenAI(api_key=api_key, base_url=base_url, timeout=TIMEOUT_S, max_retries=0)


def get_client() -> OpenAI:
    """OpenAI client for the primary provider (cached per key/base_url)."""
    settings = get_settings()
    if not settings.llm_api_key:
        raise LLMNotConfigured()
    return _client(settings.llm_api_key, settings.llm_base_url)


# --- throttle ----------------------------------------------------------------------------

class RateLimiter:
    """Blocking sliding-window limiter: at most ``rpm`` acquisitions per 60 s per key."""

    WINDOW_S = 60.0

    def __init__(self, clock: Callable[[], float] = time.monotonic, sleep: Callable[[float], None] = time.sleep) -> None:
        self._clock, self._sleep = clock, sleep
        self._lock = threading.Lock()
        self._stamps: dict[str, deque[float]] = {}

    def acquire(self, key: str, rpm: float) -> float:
        """Take a slot, sleeping until one is free; returns the seconds waited."""
        if rpm <= 0:
            return 0.0
        limit = max(1, int(rpm))
        waited = 0.0
        while True:
            with self._lock:
                now = self._clock()
                stamps = self._stamps.setdefault(key, deque())
                while stamps and now - stamps[0] >= self.WINDOW_S:
                    stamps.popleft()
                if len(stamps) < limit:
                    stamps.append(now)
                    return waited
                delay = self.WINDOW_S - (now - stamps[0]) + 0.05
            logger.info("LLM throttle (%s): %d requests in the last minute, waiting %.1fs", key, limit, delay)
            self._sleep(delay)
            waited += delay


_limiter = RateLimiter()
_sleep = time.sleep  # backoff sleep; patched in tests


# --- retry / fallback --------------------------------------------------------------------

@dataclass
class CallInfo:
    """What happened on one logical LLM call (for logs and eval_results.csv)."""

    provider: ProviderName | None = None
    model: str | None = None
    retries: int = 0          # extra attempts after failures, across providers
    waited_s: float = 0.0     # time spent in throttle + backoff
    fell_back: bool = False
    prompt_tokens: int | None = None  # provider-reported usage (non-streaming calls)


_state_lock = threading.Lock()
_primary_cooldown_until = 0.0
_last_provider: ProviderName | None = None


def active_provider() -> dict[str, Any] | None:
    """Provider that answered most recently, or the one the next call will try first."""
    provs = {p.name: p for p in providers()}
    if not provs:
        return None
    with _state_lock:
        cooling = time.monotonic() < _primary_cooldown_until
        name = _last_provider if _last_provider in provs else None
    if name is None:
        name = "fallback" if cooling and "fallback" in provs else next(iter(provs))
    return provs[name].public()


def _status(exc: Exception) -> int | None:
    return getattr(exc, "status_code", None)


def _is_daily_quota(exc: Exception) -> bool:
    """A per-day quota (e.g. Gemini free tier "...PerDay...") will not recover within any backoff."""
    return _status(exc) == 429 and "perday" in str(exc).replace("_", "").replace("-", "").lower()


def _is_retryable(exc: Exception) -> bool:
    return _status(exc) in RETRY_STATUSES and not _is_daily_quota(exc)


def _should_fall_back(exc: Exception) -> bool:
    """Transient/provider-side failures move on to the fallback; config errors (400/401/404) do not."""
    status = _status(exc)
    return (
        status in RETRY_STATUSES
        or (status is not None and status >= 500)
        or isinstance(exc, (openai.APIConnectionError, openai.APITimeoutError))
    )


_BODY_RETRY_RE = re.compile(r"retry in ([0-9.]+)\s*s|\"retryDelay\":\s*\"([0-9.]+)s\"", re.IGNORECASE)


def retry_after_seconds(exc: Exception) -> float | None:
    """Server-requested wait: ``Retry-After`` (seconds or HTTP date), ``retry-after-ms``, or the
    ``retryDelay`` hint Gemini puts in its error body."""
    response = getattr(exc, "response", None)
    headers = getattr(response, "headers", None) or {}
    if (ms := headers.get("retry-after-ms")) is not None:
        try:
            return max(0.0, float(ms) / 1000)
        except ValueError:
            pass
    if (value := headers.get("retry-after")) is not None:
        try:
            return max(0.0, float(value))
        except ValueError:
            try:
                return max(0.0, parsedate_to_datetime(value).timestamp() - time.time())
            except (TypeError, ValueError):
                pass
    if m := _BODY_RETRY_RE.search(str(exc)):
        return float(m.group(1) or m.group(2))
    return None


def _backoff(attempt: int, exc: Exception) -> float:
    hinted = retry_after_seconds(exc)
    delay = hinted if hinted is not None else BACKOFF_BASE_S * 2 ** (attempt - 1)
    return min(delay, MAX_WAIT_S)


def _call_with_retries(provider: Provider, fn: Callable[[OpenAI, Provider], T], info: CallInfo) -> T:
    client = _client(provider.api_key, provider.base_url)
    rpm = get_settings().llm_rpm
    for attempt in range(1, MAX_ATTEMPTS + 1):
        info.waited_s += _limiter.acquire(provider.name, rpm)
        try:
            return fn(client, provider)
        except openai.OpenAIError as exc:
            if not _is_retryable(exc) or attempt == MAX_ATTEMPTS:
                raise
            delay = _backoff(attempt, exc)
            logger.warning(
                "LLM %s returned %s (attempt %d/%d); retrying in %.1fs",
                provider.label, _status(exc), attempt, MAX_ATTEMPTS, delay,
            )
            info.retries += 1
            info.waited_s += delay
            _sleep(delay)
    raise AssertionError("unreachable")


def _run(fn: Callable[[OpenAI, Provider], T]) -> tuple[T, CallInfo]:
    """Call ``fn`` with retries, falling back to the secondary provider when configured."""
    global _primary_cooldown_until, _last_provider
    provs = providers()
    if not provs or provs[0].name != "primary":
        raise LLMNotConfigured()
    with _state_lock:
        cooling = time.monotonic() < _primary_cooldown_until
    order = list(reversed(provs)) if cooling and len(provs) > 1 else provs
    info = CallInfo()
    for i, provider in enumerate(order):
        try:
            result = _call_with_retries(provider, fn, info)
        except openai.OpenAIError as exc:
            if provider.name == "primary" and _should_fall_back(exc):
                with _state_lock:
                    _primary_cooldown_until = time.monotonic() + PRIMARY_COOLDOWN_S
            if i + 1 < len(order) and _should_fall_back(exc):
                logger.warning("LLM %s failed after retries (%r); switching to %s", provider.label, exc, order[i + 1].label)
                info.fell_back = True
                continue
            info.provider, info.model = provider.name, provider.model  # last provider tried
            error = _thai_error(exc, provider)
            error.info = info
            raise error from exc
        with _state_lock:
            if _last_provider != provider.name:
                logger.info("LLM active provider is now %s", provider.label)
            _last_provider = provider.name
            if provider.name == "primary":
                _primary_cooldown_until = 0.0
        info.provider, info.model = provider.name, provider.model
        logger.info("LLM answered by %s (retries=%d, waited=%.1fs)", provider.label, info.retries, info.waited_s)
        return result, info
    raise AssertionError("unreachable")


def _thai_error(exc: Exception, provider: Provider | None = None) -> LLMError:
    model = provider.model if provider else get_settings().llm_model
    if isinstance(exc, openai.AuthenticationError):
        msg = "API key ไม่ถูกต้องหรือไม่มีสิทธิ์ใช้งาน — กรุณาตรวจสอบ LLM_API_KEY"
    elif isinstance(exc, openai.NotFoundError):
        msg = f"ไม่พบโมเดลหรือ endpoint ที่ระบุ — กรุณาตรวจสอบ LLM_MODEL ({model}) และ LLM_BASE_URL"
    elif _is_daily_quota(exc):
        msg = f"โควตารายวันของ {model} หมดแล้ว — รอให้โควตารีเซ็ต (Gemini free tier รีเซ็ตทุกวัน) หรือตั้งค่าผู้ให้บริการสำรอง LLM_FALLBACK_*"
    elif isinstance(exc, openai.RateLimitError):
        msg = f"เรียกใช้ LLM เกินโควตาหรือถี่เกินไป (ลองใหม่แล้ว {MAX_ATTEMPTS} ครั้ง) — กรุณารอสักครู่แล้วลองใหม่"
    elif _status(exc) == 503:
        msg = "ผู้ให้บริการ LLM มีผู้ใช้งานหนาแน่นชั่วคราว (503) — กรุณาลองใหม่อีกครั้ง"
    elif isinstance(exc, openai.APITimeoutError):
        msg = "LLM ตอบกลับช้าเกินกำหนดเวลา — กรุณาลองใหม่อีกครั้ง"
    elif isinstance(exc, openai.APIConnectionError):
        msg = "เชื่อมต่อ LLM ไม่สำเร็จ — กรุณาตรวจสอบ LLM_BASE_URL และการเชื่อมต่ออินเทอร์เน็ต"
    else:
        msg = f"เกิดข้อผิดพลาดจาก LLM: {exc.__class__.__name__}"
    logger.warning("LLM call failed: %r", exc)
    return LLMError(msg)


# --- public calls ------------------------------------------------------------------------

def stream_chat(messages: Sequence[Message], temperature: float = TEMPERATURE) -> Iterator[str]:
    """Yield content deltas from a streaming chat completion.

    Retries and fallback apply to opening the stream (where 429/503 surface); an error after
    tokens have been sent cannot be retried and is raised as ``LLMError``."""
    stream, _ = _run(
        lambda client, p: client.chat.completions.create(
            model=p.model,
            messages=list(messages),  # type: ignore[arg-type]
            temperature=temperature,
            stream=True,
        )
    )
    try:
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    except openai.OpenAIError as exc:
        raise _thai_error(exc) from exc


def complete_with_info(messages: Sequence[Message], temperature: float = TEMPERATURE, **kwargs: Any) -> tuple[str, CallInfo]:
    """Non-streaming completion plus which provider answered and how many retries it took."""
    resp, info = _run(
        lambda client, p: client.chat.completions.create(
            model=p.model,
            messages=list(messages),  # type: ignore[arg-type]
            temperature=temperature,
            **kwargs,
        )
    )
    text = (resp.choices[0].message.content or "").strip() if resp.choices else ""
    usage = getattr(resp, "usage", None)
    info.prompt_tokens = getattr(usage, "prompt_tokens", None)
    return text, info


def complete(messages: Sequence[Message], temperature: float = TEMPERATURE, **kwargs: Any) -> str:
    """Return the full text of a non-streaming chat completion."""
    return complete_with_info(messages, temperature, **kwargs)[0]


def test_connection() -> dict[str, Any]:
    """``LlmTestResult`` payload; never raises."""
    settings = get_settings()
    result: dict[str, Any] = {"model": settings.llm_model, "base_url": settings.llm_base_url, "latency_ms": None}
    if not settings.llm_api_key:
        return {**result, "ok": False, "message": NOT_CONFIGURED_MESSAGE}
    started = time.perf_counter()
    try:
        reply, info = complete_with_info([{"role": "user", "content": "ตอบคำว่า OK เพียงคำเดียว"}], temperature=0, max_tokens=256)
    except LLMError as exc:
        return {**result, "ok": False, "message": exc.message}
    latency = int((time.perf_counter() - started) * 1000)
    via = " ผ่านผู้ให้บริการสำรอง" if info.provider == "fallback" else ""
    return {
        **result,
        "model": info.model or settings.llm_model,
        "ok": True,
        "latency_ms": latency,
        "message": f"เชื่อมต่อสำเร็จ{via} ({latency} ms, ลองใหม่ {info.retries} ครั้ง) — โมเดลตอบว่า: {reply[:40]}",
    }
