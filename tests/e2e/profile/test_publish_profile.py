import pytest
from src.core.domain.models import Profile
from src.deps import get_current_user

from tests.conftest import test_app


@pytest.mark.anyio
async def test_publish_profile_success(async_client, profile_linked_to_user):
    mock_profile, mock_user = profile_linked_to_user

    test_app.dependency_overrides[get_current_user] = lambda: mock_user

    publish_data = {
        "appearance": "light",
        "templateId": "classic",
        "slug": "test-profile-slug",
    }

    try:
        response = await async_client.patch(
            f"/v1/profile/{mock_profile.username}/publish", json=publish_data
        )

        assert response.status_code == 200
        profile_data = response.json()

        # Check that the publishingOptions was set correctly
        assert profile_data["publishingOptions"]["slug"] == publish_data["slug"]
        assert (
            profile_data["publishingOptions"]["appearance"]
            == publish_data["appearance"]
        )
        assert (
            profile_data["publishingOptions"]["templateId"]
            == publish_data["templateId"]
        )

    finally:
        mock_profile.delete()
        mock_user.delete()
        test_app.dependency_overrides = {}


@pytest.mark.anyio
async def test_publish_profile_duplicate_slug(async_client, profile_linked_to_user):
    mock_profile, mock_user = profile_linked_to_user

    duplicate_slug = "existing-slug"

    publish_data = {
        "appearance": "light",
        "templateId": "classic",
        "slug": duplicate_slug,
    }

    existing_profile = Profile(
        username="existing_user",
        firstName="Existing",
        lastName="User",
        headline="Existing Profile",
    )

    from src.core.domain.models import PublishingOptions

    existing_profile.publishingOptions = PublishingOptions(
        appearance="dark", templateId="modern", slug=duplicate_slug
    )
    existing_profile.save()

    test_app.dependency_overrides[get_current_user] = lambda: mock_user

    try:
        response = await async_client.patch(
            f"/v1/profile/{mock_profile.username}/publish", json=publish_data
        )

        assert response.status_code == 409

    finally:
        mock_profile.delete()
        mock_user.delete()
        existing_profile.delete()
        test_app.dependency_overrides = {}


@pytest.mark.anyio
async def test_publish_profile_nonexistent(async_client, mock_user):
    test_app.dependency_overrides[get_current_user] = lambda: mock_user

    publish_data = {
        "appearance": "light",
        "templateId": "classic",
        "slug": "nonexistent-profile-slug",
    }

    try:
        response = await async_client.patch(
            "/v1/profile/nonexistent/publish", json=publish_data
        )

        assert response.status_code == 404

    finally:
        test_app.dependency_overrides = {}


@pytest.mark.anyio
async def test_publish_profile_no_auth(async_client, mock_profile):
    mock_profile.save()

    publish_data = {
        "appearance": "light",
        "templateId": "classic",
        "slug": "no-auth-slug",
    }

    try:
        response = await async_client.patch(
            f"/v1/profile/{mock_profile.username}/publish", json=publish_data
        )

        assert response.status_code == 401

    finally:
        mock_profile.delete()


@pytest.mark.anyio
async def test_publish_profile_not_owned(async_client, mock_user, mock_profile):
    # Create a profile that is not linked to the user
    mock_profile.save()
    mock_user.save()

    test_app.dependency_overrides[get_current_user] = lambda: mock_user

    publish_data = {
        "appearance": "light",
        "templateId": "classic",
        "slug": "not-owned-slug",
    }

    try:
        response = await async_client.patch(
            f"/v1/profile/{mock_profile.username}/publish", json=publish_data
        )

        assert response.status_code == 404

    finally:
        mock_profile.delete()
        mock_user.delete()
        test_app.dependency_overrides = {}
