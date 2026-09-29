"""Retry / backoff / throttle / fallback behaviour of backend.llm (no network)."""
from __future__ import annotations

from types import SimpleNamespace

import httpx
import openai
import pytest

from backend import llm


def _err(status: int, headers: dict[str, str] | None = None, message: str = "boom") -> openai.APIStatusError:
    response = httpx.Response(status, headers=headers or {}, request=httpx.Request("POST", "http://llm.test/v1/chat"))
    cls = {429: openai.RateLimitError, 401: openai.AuthenticationError}.get(status, openai.InternalServerError)
    return cls(message, response=response, body=None)


def _ok(text: str) -> SimpleNamespace:
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=text))])


class FakeClient:
    """Plays back ``script`` (exceptions are raised, anything else returned) on each create()."""

    def __init__(self, script: list[object]) -> None:
        self.script, self.calls = list(script), 0
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **_: object) -> object:
        self.calls += 1
        item = self.script.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


@pytest.fixture()
def fake(monkeypatch: pytest.MonkeyPatch):
    """Primary + optional fallback fake clients, a fake clock, and recorded sleeps."""
    now = [1000.0]
    sleeps: list[float] = []

    def sleep(s: float) -> None:
        sleeps.append(round(s, 2))
        now[0] += s

    monkeypatch.setattr(llm, "_limiter", llm.RateLimiter(clock=lambda: now[0], sleep=sleep))
    monkeypatch.setattr(llm, "_sleep", sleep)
    monkeypatch.setattr(llm.time, "monotonic", lambda: now[0])
    monkeypatch.setattr(llm, "_primary_cooldown_until", 0.0)
    monkeypatch.setattr(llm, "_last_provider", None)
    monkeypatch.setenv("LLM_API_KEY", "k1")
    monkeypatch.setenv("LLM_BASE_URL", "http://primary.test/v1")
    monkeypatch.setenv("LLM_MODEL", "primary-model")
    monkeypatch.setenv("LLM_RPM", "0")
    for var in ("LLM_FALLBACK_API_KEY", "LLM_FALLBACK_BASE_URL", "LLM_FALLBACK_MODEL"):
        monkeypatch.delenv(var, raising=False)
    clients: dict[str, FakeClient] = {}
    monkeypatch.setattr(llm, "_client", lambda key, base_url: clients[base_url])

    def setup(primary: list[object], fallback: list[object] | None = None) -> dict[str, FakeClient]:
        clients["http://primary.test/v1"] = FakeClient(primary)
        if fallback is not None:
            monkeypatch.setenv("LLM_FALLBACK_API_KEY", "k2")
            monkeypatch.setenv("LLM_FALLBACK_BASE_URL", "http://fallback.test/v1")
            monkeypatch.setenv("LLM_FALLBACK_MODEL", "fallback-model")
            clients["http://fallback.test/v1"] = FakeClient(fallback)
        return clients

    return SimpleNamespace(setup=setup, sleeps=sleeps, now=now)


def _ask() -> tuple[str, llm.CallInfo]:
    return llm.complete_with_info([{"role": "user", "content": "q"}])


def test_retry_after_header_is_honoured(fake) -> None:
    fake.setup([_err(429, {"retry-after": "3"}), _ok("hi")])
    text, info = _ask()
    assert (text, info.provider, info.retries) == ("hi", "primary", 1)
    assert fake.sleeps == [3.0]


def test_exponential_backoff_on_503(fake) -> None:
    clients = fake.setup([_err(503), _err(503), _err(503), _ok("ok")])
    assert _ask()[0] == "ok"
    assert fake.sleeps == [2.0, 4.0, 8.0] and clients["http://primary.test/v1"].calls == 4


def test_gemini_retry_delay_in_body_is_used() -> None:
    exc = _err(429, message="Quota exceeded ... Please retry in 31.1s.")
    assert llm.retry_after_seconds(exc) == pytest.approx(31.1)


def test_gives_up_after_five_attempts_without_fallback(fake) -> None:
    clients = fake.setup([_err(429)] * 5)
    with pytest.raises(llm.LLMError) as err:
        _ask()
    assert clients["http://primary.test/v1"].calls == 5 and fake.sleeps == [2.0, 4.0, 8.0, 16.0]
    assert "โควตา" in err.value.message


def test_falls_back_then_skips_primary_during_cooldown(fake) -> None:
    clients = fake.setup([_err(429)] * 5, fallback=[_ok("from fallback"), _ok("again")])
    text, info = _ask()
    assert (text, info.provider, info.fell_back, info.retries) == ("from fallback", "fallback", True, 4)
    assert llm.active_provider() == {"name": "fallback", "model": "fallback-model", "base_url": "http://fallback.test/v1"}

    assert _ask()[1].provider == "fallback"          # cooling down: primary not tried
    assert clients["http://primary.test/v1"].calls == 5


def test_primary_is_retried_after_cooldown(fake) -> None:
    clients = fake.setup([_err(429)] * 5 + [_ok("primary back")], fallback=[_ok("fb")])
    _ask()
    fake.now[0] += llm.PRIMARY_COOLDOWN_S + 1
    text, info = _ask()
    assert (text, info.provider) == ("primary back", "primary")
    assert llm.active_provider()["name"] == "primary" and clients["http://primary.test/v1"].calls == 6


def test_auth_error_does_not_fall_back(fake) -> None:
    clients = fake.setup([_err(401)], fallback=[_ok("never")])
    with pytest.raises(llm.LLMError):
        _ask()
    assert clients["http://fallback.test/v1"].calls == 0 and fake.sleeps == []


def test_throttle_limits_requests_per_minute(fake, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_RPM", "2")
    fake.setup([_ok("1"), _ok("2"), _ok("3")])
    infos = [_ask()[1] for _ in range(3)]
    assert [round(i.waited_s) for i in infos] == [0, 0, 60]   # third request waits for the window
    assert len(fake.sleeps) == 1


def test_stream_retries_before_first_token(fake) -> None:
    chunk = SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content="tok"))])
    fake.setup([_err(503), iter([chunk, chunk])])
    assert list(llm.stream_chat([{"role": "user", "content": "q"}])) == ["tok", "tok"]
    assert fake.sleeps == [2.0]


DAILY = "Quota exceeded ... quotaId': 'GenerateRequestsPerDayPerProjectPerModel-FreeTier' ... retry in 59s"


def test_daily_quota_fails_fast_without_backoff(fake) -> None:
    clients = fake.setup([_err(429, message=DAILY)])
    with pytest.raises(llm.LLMError) as err:
        _ask()
    assert clients["http://primary.test/v1"].calls == 1 and fake.sleeps == []
    assert "รายวัน" in err.value.message


def test_daily_quota_goes_straight_to_fallback(fake) -> None:
    fake.setup([_err(429, message=DAILY)], fallback=[_ok("fb")])
    text, info = _ask()
    assert (text, info.provider, info.retries) == ("fb", "fallback", 0) and fake.sleeps == []


def test_error_carries_retry_info(fake) -> None:
    fake.setup([_err(503)] * 5)
    with pytest.raises(llm.LLMError) as err:
        _ask()
    assert err.value.info is not None
    assert (err.value.info.provider, err.value.info.retries, err.value.info.waited_s) == ("primary", 4, 30.0)
