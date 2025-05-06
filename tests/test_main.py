import pytest


@pytest.mark.anyio
async def test_healthz(async_client):
    response = await async_client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

