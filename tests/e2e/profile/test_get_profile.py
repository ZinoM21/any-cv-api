import pytest
from src.deps import get_optional_current_user

from tests.conftest import test_app


@pytest.mark.anyio
async def test_get_profile_with_user_success(
    async_client,
    profile_linked_to_user,
):
    mock_profile, mock_user = profile_linked_to_user

    test_app.dependency_overrides[get_optional_current_user] = lambda: mock_user

    try:
        response = await async_client.get(f"/v1/profile/{mock_profile.username}")

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == mock_profile.username
        assert data["firstName"] == mock_profile.firstName
        assert data["lastName"] == mock_profile.lastName
        assert data["headline"] == mock_profile.headline
        assert data["about"] == mock_profile.about

    finally:
        mock_profile.delete()
        mock_user.delete()
        test_app.dependency_overrides = {}


@pytest.mark.anyio
async def test_get_profile_without_user_success(async_client, mock_guest_profile):
    mock_guest_profile.save()

    try:
        response = await async_client.get(f"/v1/profile/{mock_guest_profile.username}")

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == mock_guest_profile.username
        assert data["firstName"] == mock_guest_profile.firstName
        assert data["lastName"] == mock_guest_profile.lastName
        assert data["headline"] == mock_guest_profile.headline
        assert data["about"] == mock_guest_profile.about

    finally:
        mock_guest_profile.delete()
        test_app.dependency_overrides = {}


@pytest.mark.anyio
async def test_get_profile_with_user_not_linked_to_profile(
    async_client, mock_user, mock_profile
):
    test_app.dependency_overrides[get_optional_current_user] = lambda: mock_user

    mock_user.save()
    mock_profile.save()

    try:
        response = await async_client.get(f"/v1/profile/{mock_profile.username}")

        assert response.status_code == 404

    finally:
        mock_profile.delete()
        mock_user.delete()
        test_app.dependency_overrides = {}


@pytest.mark.anyio
async def test_get_nonexistent_profile_with_user(async_client, mock_user):
    test_app.dependency_overrides[get_optional_current_user] = lambda: mock_user

    try:
        response = await async_client.get("/v1/profile/nonexistentuser")

        assert response.status_code == 404

    finally:
        test_app.dependency_overrides = {}


@pytest.mark.anyio
async def test_get_nonexistent_profile_without_user(async_client):
    response = await async_client.get("/v1/profile/nonexistentuser")

    assert response.status_code == 404
