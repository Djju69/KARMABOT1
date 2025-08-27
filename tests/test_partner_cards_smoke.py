import os
import sys
import time
from pathlib import Path
import pytest
import pytest_asyncio
import httpx

# В этом тесте используем dev-байпас: ENVIRONMENT=development и ALLOW_PARTNER_FOR_CABINET=1,
# чтобы не требовался реальный JWT. Это соответствует нашему техплану для локальной проверки.

os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("ALLOW_PARTNER_FOR_CABINET", "1")

# Гарантируем, что корень репозитория в sys.path (для import web.main)
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from web.main import app  # noqa: E402


@pytest_asyncio.fixture(scope="function")
async def client():
    # Явно вызываем startup/shutdown на каждый тест, чтобы избежать конфликтов скопов с anyio
    await app.router.startup()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    await app.router.shutdown()


def _auth_headers():
    # Передаём любой bearer — бэкенд включит дев-байпас и примет роль partner
    return {"Authorization": "Bearer debug-token"}


@pytest.mark.asyncio
async def test_profile_partner_role(client):
    r = await client.get("/cabinet/profile?token=debug")
    assert r.status_code == 200
    data = r.json()
    assert data.get("role") in ("partner", "admin", "superadmin"), data


@pytest.mark.asyncio
async def test_create_card_and_list_with_status_filter(client):
    # 1) Получаем категории (должны быть посеяны на бэкенде)
    r = await client.get("/cabinet/partner/categories", headers=_auth_headers())
    assert r.status_code == 200
    cats = r.json()
    assert isinstance(cats, list) and len(cats) > 0
    category_id = int(cats[0]["id"])  # берем первую доступную

    # 2) Создаём карточку в статусе pending (черновик/на модерации)
    uniq = f"pytest {int(time.time())}"
    payload = {
        "category_id": category_id,
        "title": uniq,
        "description": "описание",
        "contact": "+84...",
        "address": "адрес",
        "google_maps_url": None,
        "discount_text": "скидка",
    }
    r = await client.post("/cabinet/partner/cards", json=payload, headers=_auth_headers())
    assert r.status_code == 200, r.text
    created = r.json()
    assert created.get("id")
    assert created.get("category_id") == category_id
    assert created.get("title") == uniq
    assert created.get("status") in ("pending", "draft", "moderation"), created

    # 3) Список карточек партнёра, фильтр по статусу pending
    r = await client.get("/cabinet/partner/cards?status=pending&limit=50", headers=_auth_headers())
    assert r.status_code == 200, r.text
    data = r.json()
    assert isinstance(data, dict) and isinstance(data.get("items"), list)
    titles = [it.get("title") for it in data.get("items")]
    assert uniq in titles, f"Card '{uniq}' not found in pending list"
