import pytest
from src.deps import get_current_user, get_profile_service

from tests.conftest import test_app


@pytest.mark.anyio
async def test_get_profiles_success(async_client, mock_profile_service, mock_user):
    test_app.dependency_overrides[get_profile_service] = lambda: mock_profile_service
    test_app.dependency_overrides[get_current_user] = lambda: mock_user

    response = await async_client.get(
        "/v1/profile/user/list",
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

    test_app.dependency_overrides = {}


@pytest.mark.anyio
async def test_get_profiles_no_user(async_client, mock_profile_service):
    test_app.dependency_overrides[get_profile_service] = lambda: mock_profile_service

    response = await async_client.get(
        "/v1/profile/user/list",
    )

    assert response.status_code == 401

    test_app.dependency_overrides = {}


@pytest.mark.anyio
async def test_get_profiles_invalid_user(async_client, mock_profile_service):
    test_app.dependency_overrides[get_profile_service] = lambda: mock_profile_service

    response = await async_client.get(
        "/v1/profile/user/list",
        headers={"Authorization": "Bearer invalid_token"},
    )

    assert response.status_code == 401

    test_app.dependency_overrides = {}
