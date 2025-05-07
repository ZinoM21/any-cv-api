import pytest
from src.deps import get_current_user, get_profile_service

from tests.conftest import test_app


@pytest.mark.anyio
async def test_transfer_guest_profile_success(
    async_client, mock_profile_service, mock_user
):
    test_app.dependency_overrides[get_profile_service] = lambda: mock_profile_service
    test_app.dependency_overrides[get_current_user] = lambda: mock_user

    response = await async_client.get(
        "/v1/profile/johndoe/transfer",
    )

    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "johndoe"

    test_app.dependency_overrides = {}


# no username
@pytest.mark.anyio
async def test_transfer_guest_profile_no_username(
    async_client, mock_profile_service, mock_user
):
    test_app.dependency_overrides[get_profile_service] = lambda: mock_profile_service
    test_app.dependency_overrides[get_current_user] = lambda: mock_user

    response = await async_client.get(
        "/v1/profile//transfer",
    )

    assert response.status_code == 404

    test_app.dependency_overrides = {}


@pytest.mark.anyio
async def test_transfer_guest_profile_no_user(async_client, mock_profile_service):
    test_app.dependency_overrides[get_profile_service] = lambda: mock_profile_service

    response = await async_client.get(
        "/v1/profile/johndoe/transfer",
    )

    assert response.status_code == 401

    test_app.dependency_overrides = {}


@pytest.mark.anyio
async def test_transfer_guest_profile_invalid_user(async_client, mock_profile_service):
    test_app.dependency_overrides[get_profile_service] = lambda: mock_profile_service

    response = await async_client.get(
        "/v1/profile/johndoe",
        headers={"Authorization": "Bearer invalid_token"},
    )

    assert response.status_code == 401

    test_app.dependency_overrides = {}
