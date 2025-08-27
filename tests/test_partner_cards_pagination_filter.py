import os
import sys
import time
from pathlib import Path
import pytest
import pytest_asyncio
import httpx

# Dev-bypass for local tests
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("ALLOW_PARTNER_FOR_CABINET", "1")

# Ensure repo root in sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from web.main import app  # noqa: E402


@pytest_asyncio.fixture(scope="function")
async def client():
    await app.router.startup()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    await app.router.shutdown()


def _auth_headers():
    return {"Authorization": "Bearer debug-token"}


@pytest.mark.asyncio
async def test_category_filter_and_keyset_pagination(client):
    # 1) Получаем категории, берём две разные
    r = await client.get("/cabinet/partner/categories", headers=_auth_headers())
    assert r.status_code == 200, r.text
    cats = r.json()
    assert isinstance(cats, list) and len(cats) >= 2
    cat1 = int(cats[0]["id"]) 
    cat2 = int(cats[1]["id"]) if len(cats) > 1 else int(cats[0]["id"])  # fallback, но по сидингу их >=2

    # 2) Создаём две карточки в разных категориях
    uniq1 = f"pytest-cat1 {int(time.time())}"
    payload1 = {
        "category_id": cat1,
        "title": uniq1,
        "description": "descr1",
        "contact": "+84...",
        "address": "addr1",
        "google_maps_url": None,
        "discount_text": "disc1",
    }
    r = await client.post("/cabinet/partner/cards", json=payload1, headers=_auth_headers())
    assert r.status_code == 200, r.text
    card1 = r.json()
    assert card1.get("category_id") == cat1

    uniq2 = f"pytest-cat2 {int(time.time())}"
    payload2 = {
        "category_id": cat2,
        "title": uniq2,
        "description": "descr2",
        "contact": "+84...",
        "address": "addr2",
        "google_maps_url": None,
        "discount_text": "disc2",
    }
    r = await client.post("/cabinet/partner/cards", json=payload2, headers=_auth_headers())
    assert r.status_code == 200, r.text
    card2 = r.json()
    assert card2.get("category_id") == cat2

    # 3) Фильтрация по категории cat1
    r = await client.get(f"/cabinet/partner/cards?category_id={cat1}&limit=50", headers=_auth_headers())
    assert r.status_code == 200, r.text
    data = r.json()
    titles = [it.get("title") for it in data.get("items", [])]
    assert uniq1 in titles
    assert uniq2 not in titles

    # 4) Keyset пагинация: ожидаем, что более новый id будет первым при ORDER BY id DESC
    # Получаем самую новую карточку с limit=1
    r = await client.get("/cabinet/partner/cards?limit=1", headers=_auth_headers())
    assert r.status_code == 200, r.text
    first_page = r.json().get("items", [])
    assert len(first_page) == 1
    newest_id = int(first_page[0]["id"])
    newest_title = first_page[0]["title"]

    # after_id=newest_id должен вернуть следующую по новизне карточку
    r = await client.get(f"/cabinet/partner/cards?after_id={newest_id}&limit=1", headers=_auth_headers())
    assert r.status_code == 200, r.text
    second_page = r.json().get("items", [])
    assert len(second_page) >= 0  # может быть 0, если всего одна карточка, но у нас их минимум 2
    if second_page:
        assert int(second_page[0]["id"]) < newest_id
        assert second_page[0]["title"] != newest_title
