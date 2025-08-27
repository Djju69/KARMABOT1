import os
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
import pytest
import httpx
from httpx import ASGITransport

from web.main import app
from core.services.webapp_auth import issue_jwt
from core.services.cache import cache_service


def _auth_headers(user_id: int = 12345) -> dict:
    token = issue_jwt(user_id, ttl_sec=300)
    return {"Authorization": f"Bearer {token}"}


def setup_function():
    # изоляция состояния между тестами: очищаем ключи кулдауна
    # в memory-режиме cache_service поддерживает удаление по маске
    try:
        import asyncio
        asyncio.get_event_loop().run_until_complete(cache_service.delete_by_mask("actv:cd:*"))
    except Exception:
        pass


@pytest.mark.asyncio
async def test_missing_token_unauthorized(monkeypatch):
    monkeypatch.setenv("ACTIVITY_ENABLED", "true")
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        r = await client.post("/api/loyalty/activity/claim", json={"rule_code": "checkin"})
        assert r.status_code == 401


@pytest.mark.asyncio
async def test_feature_disabled_returns_rule_disabled(monkeypatch):
    monkeypatch.setenv("ACTIVITY_ENABLED", "false")
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        r = await client.post("/api/loyalty/activity/claim", headers=_auth_headers(), json={"rule_code": "checkin"})
        assert r.status_code == 200
        data = r.json()
        assert data["ok"] is False
        assert data["code"] == "rule_disabled"


@pytest.mark.asyncio
async def test_checkin_ok_and_cooldown(monkeypatch):
    monkeypatch.setenv("ACTIVITY_ENABLED", "true")
    monkeypatch.setenv("ACTIVITY_CHECKIN_COOLDOWN_SEC", "3600")

    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        r1 = await client.post("/api/loyalty/activity/claim", headers=_auth_headers(111), json={"rule_code": "checkin"})
        assert r1.status_code == 200
        d1 = r1.json()
        assert d1["ok"] is True
        assert d1.get("points_awarded", 0) >= 0

        r2 = await client.post("/api/loyalty/activity/claim", headers=_auth_headers(111), json={"rule_code": "checkin"})
        assert r2.status_code == 200
        d2 = r2.json()
        assert d2["ok"] is False
        assert d2["code"] == "cooldown_active"


@pytest.mark.asyncio
async def test_geocheckin_requires_geo(monkeypatch):
    monkeypatch.setenv("ACTIVITY_ENABLED", "true")
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        r = await client.post("/api/loyalty/activity/claim", headers=_auth_headers(222), json={"rule_code": "geocheckin"})
        assert r.status_code == 200
        d = r.json()
        assert d["ok"] is False
        assert d["code"] == "geo_required"


@pytest.mark.asyncio
async def test_geocheckin_with_geo_ok(monkeypatch):
    monkeypatch.setenv("ACTIVITY_ENABLED", "true")
    monkeypatch.setenv("ACTIVITY_GEO_COOLDOWN_SEC", "86400")

    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        r = await client.post(
            "/api/loyalty/activity/claim",
            headers=_auth_headers(333),
            json={"rule_code": "geocheckin", "lat": 12.34, "lng": 56.78},
        )
        assert r.status_code == 200
        d = r.json()
        assert d["ok"] is True
        assert d.get("points_awarded", 0) >= 0


@pytest.mark.asyncio
async def test_geocheckin_out_of_coverage_mock(monkeypatch):
    """When ACTIVITY_GEO_MOCK_OUT=true and coords=(0,0), expect out_of_coverage"""
    monkeypatch.setenv("ACTIVITY_ENABLED", "true")
    monkeypatch.setenv("ACTIVITY_GEO_MOCK_OUT", "true")

    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        r = await client.post(
            "/api/loyalty/activity/claim",
            headers=_auth_headers(444),
            json={"rule_code": "geocheckin", "lat": 0.0, "lng": 0.0},
        )
        assert r.status_code == 200
        d = r.json()
        assert d["ok"] is False
        assert d["code"] == "out_of_coverage"


@pytest.mark.asyncio
async def test_invalid_rule_code_returns_400(monkeypatch):
    monkeypatch.setenv("ACTIVITY_ENABLED", "true")
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        r = await client.post(
            "/api/loyalty/activity/claim",
            headers=_auth_headers(555),
            json={"rule_code": "unknown"},
        )
        assert r.status_code == 400
