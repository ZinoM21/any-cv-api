import pytest


@pytest.mark.anyio
async def test_get_published_profiles_endpoint_access(async_client):
    response = await async_client.get("/v1/profile/published")

    # Should return list even if empty
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.anyio
async def test_get_published_profiles_success(async_client, published_profiles):
    try:
        response = await async_client.get("/v1/profile/published")

        assert response.status_code == 200
        returned_profiles = response.json()

        assert isinstance(returned_profiles, list)

        # Number we created equals response length
        assert len(returned_profiles) == len(published_profiles)

        # Check that all our created profiles in the response correctly match
        for profile in published_profiles:
            returned_profile = next(
                (p for p in returned_profiles if p["username"] == profile.username),
                None,
            )
            assert returned_profile is not None
            assert (
                returned_profile["publishingOptions"]["slug"]
                == profile.publishingOptions.slug
            )
            assert (
                returned_profile["publishingOptions"]["appearance"]
                == profile.publishingOptions.appearance
            )
            assert (
                returned_profile["publishingOptions"]["templateId"]
                == profile.publishingOptions.templateId
            )

    finally:
        for profile in published_profiles:
            profile.delete()


@pytest.mark.anyio
async def test_get_published_profiles_with_no_published_profiles(
    async_client, mock_profile
):
    unpublished_profile = mock_profile.save()

    try:
        response = await async_client.get("/v1/profile/published")

        assert response.status_code == 200
        data = response.json()

        # List, but can be empty
        assert isinstance(data, list)

        # Unpublished profile is not in the response
        response_usernames = [profile.get("username") for profile in data]
        assert unpublished_profile.username not in response_usernames

    finally:
        unpublished_profile.delete()
