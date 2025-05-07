import pytest
from src.core.domain.models import PublishingOptions
from src.deps import get_current_user

from tests.conftest import test_app


@pytest.mark.anyio
async def test_unpublish_profile_success(
    async_client, published_profile_linked_to_user
):
    mock_profile, mock_user = published_profile_linked_to_user

    test_app.dependency_overrides[get_current_user] = lambda: mock_user

    try:
        response = await async_client.get(
            f"/v1/profile/{mock_profile.username}/unpublish"
        )

        assert response.status_code == 200
        profile_data = response.json()
        assert (
            "publishingOptions" not in profile_data
            or profile_data["publishingOptions"] == {}
        )

    finally:
        mock_profile.delete()
        mock_user.delete()
        test_app.dependency_overrides = {}


@pytest.mark.anyio
async def test_unpublish_nonexistent_profile(async_client, mock_user):
    test_app.dependency_overrides[get_current_user] = lambda: mock_user

    try:
        response = await async_client.get("/v1/profile/nonexistent/unpublish")

        assert response.status_code == 404

    finally:
        test_app.dependency_overrides = {}


@pytest.mark.anyio
async def test_unpublish_profile_no_auth(async_client, mock_profile):
    publishing_options = PublishingOptions(
        appearance="light", templateId="classic", slug="published-no-auth"
    )

    mock_profile.publishingOptions = publishing_options
    mock_profile.save()

    try:
        response = await async_client.get(
            f"/v1/profile/{mock_profile.username}/unpublish"
        )

        assert response.status_code == 401

    finally:
        mock_profile.delete()


@pytest.mark.anyio
async def test_unpublish_profile_not_owned(async_client, mock_user, mock_profile):
    # Create a published profile not linked to the user
    publishing_options = PublishingOptions(
        appearance="light", templateId="classic", slug="published-not-owned"
    )

    mock_profile.publishingOptions = publishing_options
    mock_profile.save()
    mock_user.save()

    test_app.dependency_overrides[get_current_user] = lambda: mock_user

    try:
        response = await async_client.get(
            f"/v1/profile/{mock_profile.username}/unpublish"
        )

        assert response.status_code == 404

    finally:
        mock_profile.delete()
        mock_user.delete()
        test_app.dependency_overrides = {}


@pytest.mark.anyio
async def test_unpublish_already_unpublished_profile(
    async_client, published_profile_linked_to_user
):
    mock_profile, mock_user = published_profile_linked_to_user

    test_app.dependency_overrides[get_current_user] = lambda: mock_user

    try:
        second_response = await async_client.get(
            f"/v1/profile/{mock_profile.username}/unpublish"
        )

        # Should still be successful
        assert second_response.status_code == 200
        profile_data = second_response.json()

        # Check that publishingOptions is still empty
        assert (
            "publishingOptions" not in profile_data
            or profile_data["publishingOptions"] == {}
        )

    finally:
        mock_profile.delete()
        mock_user.delete()
        test_app.dependency_overrides = {}
