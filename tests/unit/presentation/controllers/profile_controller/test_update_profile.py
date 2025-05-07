import pytest
from src.deps import get_profile_service

from tests.conftest import test_app


@pytest.mark.anyio
async def test_update_profile_success(async_client, mock_profile_service):
    test_app.dependency_overrides[get_profile_service] = lambda: mock_profile_service

    response = await async_client.patch(
        "/v1/profile/johndoe",
        json={"firstName": "John", "lastName": "Doe"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "johndoe"

    test_app.dependency_overrides = {}


@pytest.mark.anyio
async def test_update_profile_without_body(async_client, mock_profile_service):
    test_app.dependency_overrides[get_profile_service] = lambda: mock_profile_service

    response = await async_client.patch(
        "/v1/profile/johndoe",
    )

    assert response.status_code == 422

    test_app.dependency_overrides = {}


@pytest.mark.anyio
async def test_update_profile_with_invalid_update_data(
    async_client, mock_profile_service
):
    test_app.dependency_overrides[get_profile_service] = lambda: mock_profile_service

    response = await async_client.patch(
        "/v1/profile/johndoe",
        json={"firstName": 123},
    )

    assert response.status_code == 422

    test_app.dependency_overrides = {}


@pytest.mark.anyio
async def test_update_profile_with_invalid_user(async_client, mock_profile_service):
    test_app.dependency_overrides[get_profile_service] = lambda: mock_profile_service

    response = await async_client.patch(
        "/v1/profile/johndoe",
        headers={"Authorization": "Bearer invalid_token"},
    )

    assert response.status_code == 401

    test_app.dependency_overrides = {}


@pytest.mark.anyio
async def test_update_profile_with_no_username(async_client, mock_profile_service):
    test_app.dependency_overrides[get_profile_service] = lambda: mock_profile_service

    response = await async_client.patch(
        "/v1/profile/",
    )

    assert response.status_code == 404

    test_app.dependency_overrides = {}
