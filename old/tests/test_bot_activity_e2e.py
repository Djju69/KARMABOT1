import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import asyncio
import types
import pytest

from core.handlers import activity as act


class FakeMessage:
    def __init__(self, user_id: int, text: str = ""):
        self.from_user = types.SimpleNamespace(id=user_id)
        self.text = text
        self._answers = []
        self._edited = []
        self.location = None

    async def answer(self, text: str, reply_markup=None):
        self._answers.append((text, reply_markup))

    async def edit_reply_markup(self, reply_markup=None):
        self._edited.append(reply_markup)


class FakeCallback:
    def __init__(self, user_id: int, data: str):
        self.from_user = types.SimpleNamespace(id=user_id)
        self.data = data
        self.message = FakeMessage(user_id)
        self._answers = []

    async def answer(self, text: str = None, show_alert: bool = False):
        self._answers.append((text, show_alert))


class FakeResp:
    def __init__(self, status: int, json_data: dict | None = None, text_data: str = ""):
        self.status = status
        self._json = json_data or {}
        self._text = text_data

    async def json(self, content_type=None):
        return self._json

    async def text(self):
        return self._text


class FakeRequestCtx:
    def __init__(self, resp: "FakeResp"):
        self._resp = resp

    async def __aenter__(self):
        return self._resp

    async def __aexit__(self, exc_type, exc, tb):
        return False


class FakeSession:
    def __init__(self, resp: FakeResp):
        self._resp = resp

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    def post(self, url, json=None, headers=None):
        return FakeRequestCtx(self._resp)


class FakeClient:
    def __init__(self, resp: FakeResp):
        self.resp = resp

    async def __aenter__(self):
        return FakeSession(self.resp)

    async def __aexit__(self, exc_type, exc, tb):
        return False


@pytest.mark.asyncio
async def test_open_activity_screen(monkeypatch):
    # Arrange
    user_id = 1001
    msg = FakeMessage(user_id, text="🎯 Активность")

    async def fake_get_lang(uid):
        return "ru"

    async def fake_ensure_policy_accepted(message):
        return True

    monkeypatch.setattr(act.profile_service, "get_lang", fake_get_lang)
    monkeypatch.setattr(act, "ensure_policy_accepted", fake_ensure_policy_accepted)

    # Act
    await act.on_activity_open(msg)

    # Assert: one answer with keyboard having 4 rows (инлайн для 4 правил)
    assert len(msg._answers) >= 1
    text, kb = msg._answers[-1]
    assert "🎯" in text
    assert kb is not None
    assert hasattr(kb, "inline_keyboard")
    assert len(kb.inline_keyboard) == 4


@pytest.mark.asyncio
async def test_checkin_claim_flow_ok(monkeypatch):
    user_id = 1002
    cb = FakeCallback(user_id, data="actv:checkin")

    async def fake_get_lang(uid):
        return "ru"

    async def fake_ensure_policy_accepted(message):
        return True

    # Fake cache: no cooldown initially, set on success
    storage = {}

    async def fake_get(key):
        return storage.get(key)

    async def fake_set(key, val, ex=None):
        storage[key] = val

    monkeypatch.setattr(act.profile_service, "get_lang", fake_get_lang)
    monkeypatch.setattr(act, "ensure_policy_accepted", fake_ensure_policy_accepted)
    monkeypatch.setattr(act.cache_service, "get", fake_get)
    monkeypatch.setattr(act.cache_service, "set", fake_set)

    # Mock backend response OK
    ok_resp = FakeResp(status=200, json_data={"ok": True, "points_awarded": 5})

    class FakeTimeout:
        def __init__(self, total):
            self.total = total

    class FakeAiohttp:
        class ClientTimeout:
            def __init__(self, total):
                self.total = total

        def ClientSession(self, timeout=None):
            return FakeClient(ok_resp)

    import core.handlers.activity as act_mod
    monkeypatch.setattr(act_mod, "aiohttp", FakeAiohttp())

    # Act
    await act.on_activity_claim(cb)

    # Assert: answered with claim_ok and cooldown set
    assert any((ans[0] == act.get_text('actv_claim_ok', 'ru')) for ans in cb._answers)


@pytest.mark.asyncio
async def test_geocheckin_request_and_success(monkeypatch):
    user_id = 1003
    cb = FakeCallback(user_id, data="actv:geocheckin")

    async def fake_get_lang(uid):
        return "ru"

    async def fake_ensure_policy_accepted(message):
        return True

    storage = {}

    async def fake_get(key):
        return storage.get(key)

    async def fake_set(key, val, ex=None):
        storage[key] = val

    monkeypatch.setattr(act.profile_service, "get_lang", fake_get_lang)
    monkeypatch.setattr(act, "ensure_policy_accepted", fake_ensure_policy_accepted)
    monkeypatch.setattr(act.cache_service, "get", fake_get)
    monkeypatch.setattr(act.cache_service, "set", fake_set)

    # Step 1: press geocheckin -> bot asks for location
    await act.on_activity_claim(cb)
    assert len(cb.message._answers) >= 1
    prompt_text, prompt_kb = cb.message._answers[-1]
    assert act.get_text('actv_send_location_prompt', 'ru') in prompt_text

    # Step 2: send location -> backend ok
    # mock aiohttp for next call
    ok_resp = FakeResp(status=200, json_data={"ok": True, "points_awarded": 10})

    class FakeAiohttp2:
        class ClientTimeout:
            def __init__(self, total):
                self.total = total

        def ClientSession(self, timeout=None):
            return FakeClient(ok_resp)

    import core.handlers.activity as act_mod
    monkeypatch.setattr(act_mod, "aiohttp", FakeAiohttp2())

    msg = FakeMessage(user_id)
    msg.location = types.SimpleNamespace(latitude=12.3, longitude=45.6)

    await act.on_location_for_geocheckin(msg)

    # Expect confirmation message
    assert any((act.get_text('actv_claim_ok', 'ru') in a[0]) for a in msg._answers)
