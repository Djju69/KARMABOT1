"""Smoke tests to verify deployment health."""
import pytest
from httpx import AsyncClient
from web.main import app

@pytest.mark.asyncio
async def test_health_endpoint():
    """Test health check endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

@pytest.mark.asyncio
async def test_ready_endpoint():
    """Test readiness check endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/ready")
        assert response.status_code == 200
        assert "database" in response.json()
        assert response.json()["database"] == "ok"

@pytest.mark.asyncio
async def test_loyalty_endpoints():
    """Test basic loyalty endpoints."""
    test_user_id = 9999
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Test getting balance for non-existent user (should return 0 or 404)
        response = await client.get(f"/api/v1/loyalty/balance/{test_user_id}")
        assert response.status_code in [200, 404]
        
        # Test adding points
        response = await client.post(
            "/api/v1/loyalty/adjust",
            json={
                "user_id": test_user_id,
                "delta_pts": 10,
                "note": "Smoke test"
            }
        )
        assert response.status_code == 200
        assert response.json()["balance_after"] == 10

        # Verify balance was updated
        response = await client.get(f"/api/v1/loyalty/balance/{test_user_id}")
        assert response.status_code == 200
        assert response.json()["balance"] == 10
