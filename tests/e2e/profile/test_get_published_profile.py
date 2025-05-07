import pytest


@pytest.mark.anyio
async def test_get_published_profile_success(async_client, published_profile):
    try:
        response = await async_client.get(
            f"/v1/profile/published/{published_profile.publishingOptions.slug}"
        )

        assert response.status_code == 200
        profile_data = response.json()

        # Check that the returned profile matches what we created
        assert profile_data["username"] == published_profile.username
        assert profile_data["firstName"] == published_profile.firstName
        assert profile_data["lastName"] == published_profile.lastName
        assert profile_data["headline"] == published_profile.headline
        assert profile_data["about"] == published_profile.about

        # Check publishing options
        assert (
            profile_data["publishingOptions"]["slug"]
            == published_profile.publishingOptions.slug
        )
        assert (
            profile_data["publishingOptions"]["appearance"]
            == published_profile.publishingOptions.appearance
        )
        assert (
            profile_data["publishingOptions"]["templateId"]
            == published_profile.publishingOptions.templateId
        )

    finally:
        published_profile.delete()


@pytest.mark.anyio
async def test_get_published_profile_nonexistent(async_client):
    response = await async_client.get("/v1/profile/published/non-existent-slug")

    assert response.status_code == 404


@pytest.mark.anyio
async def test_get_published_profile_unpublished(async_client, mock_profile):
    unpublished_profile = mock_profile.save()

    try:
        response = await async_client.get(
            f"/v1/profile/published/{unpublished_profile.username}"
        )

        assert response.status_code == 404

    finally:
        unpublished_profile.delete()
