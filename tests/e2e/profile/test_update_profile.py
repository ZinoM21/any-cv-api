import pytest
from src.deps import get_optional_current_user

from tests.conftest import test_app


@pytest.mark.anyio
async def test_update_profile_with_user_success(async_client, profile_linked_to_user):
    mock_profile, mock_user = profile_linked_to_user
    test_app.dependency_overrides[get_optional_current_user] = lambda: mock_user

    update_data = {
        "firstName": "Updated John",
        "lastName": "Updated Doe",
        "headline": "Senior Software Developer",
        "about": "Updated professional bio with more experience",
    }

    try:
        response = await async_client.patch(
            f"/v1/profile/{mock_profile.username}", json=update_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["firstName"] == update_data["firstName"]
        assert data["lastName"] == update_data["lastName"]
        assert data["headline"] == update_data["headline"]
        assert data["about"] == update_data["about"]

        # Verify other fields remain unchanged
        assert data["username"] == mock_profile.username

    finally:
        mock_profile.delete()
        mock_user.delete()
        test_app.dependency_overrides = {}


@pytest.mark.anyio
async def test_update_profile_without_user_success(async_client, mock_guest_profile):
    mock_guest_profile.save()

    update_data = {
        "firstName": "Updated Guest",
        "lastName": "Updated User",
        "headline": "Guest Developer",
        "about": "Updated guest profile description",
    }

    try:
        response = await async_client.patch(
            f"/v1/profile/{mock_guest_profile.username}", json=update_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["firstName"] == update_data["firstName"]
        assert data["lastName"] == update_data["lastName"]
        assert data["headline"] == update_data["headline"]
        assert data["about"] == update_data["about"]

        # Verify other fields remain unchanged
        assert data["username"] == mock_guest_profile.username

    finally:
        mock_guest_profile.delete()
        test_app.dependency_overrides = {}


@pytest.mark.anyio
async def test_update_profile_complex_fields(async_client, profile_linked_to_user):
    mock_profile, mock_user = profile_linked_to_user

    test_app.dependency_overrides[get_optional_current_user] = lambda: mock_user

    update_data = {
        "languages": ["English", "Spanish", "French"],
        "skills": ["Python", "FastAPI", "MongoDB", "React"],
    }

    try:
        response = await async_client.patch(
            f"/v1/profile/{mock_profile.username}", json=update_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["languages"] == update_data["languages"]
        assert data["skills"] == update_data["skills"]

        # Verify other fields remain unchanged
        assert data["username"] == mock_profile.username
        assert data["firstName"] == mock_profile.firstName
        assert data["lastName"] == mock_profile.lastName

    finally:
        mock_profile.delete()
        mock_user.delete()
        test_app.dependency_overrides = {}


@pytest.mark.anyio
async def test_update_profile_with_user_not_linked_to_profile(
    async_client, mock_user, mock_profile
):
    test_app.dependency_overrides[get_optional_current_user] = lambda: mock_user

    mock_user.save()
    mock_profile.save()

    update_data = {"firstName": "Updated Name"}

    try:
        response = await async_client.patch(
            f"/v1/profile/{mock_profile.username}", json=update_data
        )

        assert response.status_code == 404

    finally:
        mock_profile.delete()
        mock_user.delete()
        test_app.dependency_overrides = {}


@pytest.mark.anyio
async def test_update_nonexistent_profile_with_user(async_client, mock_user):
    test_app.dependency_overrides[get_optional_current_user] = lambda: mock_user

    update_data = {"firstName": "New Name"}

    try:
        response = await async_client.patch(
            "/v1/profile/nonexistentuser", json=update_data
        )

        assert response.status_code == 404

    finally:
        test_app.dependency_overrides = {}


@pytest.mark.anyio
async def test_update_nonexistent_profile_without_user(async_client):
    update_data = {"firstName": "New Name"}

    response = await async_client.patch("/v1/profile/nonexistentuser", json=update_data)

    assert response.status_code == 404


@pytest.mark.anyio
async def test_update_profile_with_empty_payload(async_client, profile_linked_to_user):
    mock_profile, mock_user = profile_linked_to_user

    test_app.dependency_overrides[get_optional_current_user] = lambda: mock_user

    update_data = {}

    try:
        response = await async_client.patch(
            f"/v1/profile/{mock_profile.username}", json=update_data
        )

        assert response.status_code == 200
        data = response.json()

        # Verify fields remain unchanged
        assert data["username"] == mock_profile.username
        assert data["firstName"] == mock_profile.firstName
        assert data["lastName"] == mock_profile.lastName
        assert data["headline"] == mock_profile.headline
        assert data["about"] == mock_profile.about

    finally:
        mock_profile.delete()
        mock_user.delete()
        test_app.dependency_overrides = {}
