import pytest
from src.deps import get_profile_service

from tests.conftest import test_app


@pytest.mark.anyio
async def test_create_profile_success(async_client, mock_profile_service):
    test_app.dependency_overrides[get_profile_service] = lambda: mock_profile_service

    response = await async_client.post(
        "/v1/profile/johndoe",
        json={"turnstileToken": "XXXX.DUMMY.TOKEN.XXXX"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "johndoe"

    test_app.dependency_overrides = {}


@pytest.mark.anyio
async def test_create_profile_invalid_body(async_client):
    response = await async_client.post(
        "/v1/profile/johndoe",
        json={},
    )

    assert response.status_code == 400


@pytest.mark.anyio
async def test_create_profile_without_body(async_client):

    response = await async_client.post(
        "/v1/profile/johndoe",
    )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_create_profile_with_invalid_user(async_client, mock_profile_service):
    test_app.dependency_overrides[get_profile_service] = lambda: mock_profile_service

    response = await async_client.post(
        "/v1/profile/johndoe",
        headers={"Authorization": "Bearer invalid_token"},
        json={"turnstileToken": "XXXX.DUMMY.TOKEN.XXXX"},
    )

    assert response.status_code == 401

    test_app.dependency_overrides = {}


@pytest.mark.anyio
async def test_create_profile_with_no_username(async_client, mock_profile_service):
    test_app.dependency_overrides[get_profile_service] = lambda: mock_profile_service

    response = await async_client.post(
        "/v1/profile/",
        json={"turnstileToken": "XXXX.DUMMY.TOKEN.XXXX"},
    )

    assert response.status_code == 404

    test_app.dependency_overrides = {}
