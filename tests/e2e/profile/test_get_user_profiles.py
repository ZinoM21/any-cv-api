import pytest
from src.deps import get_current_user

from tests.conftest import test_app


@pytest.mark.anyio
async def test_get_user_profiles_success(async_client, profile_linked_to_user):
    mock_profile, mock_user = profile_linked_to_user

    test_app.dependency_overrides[get_current_user] = lambda: mock_user

    try:
        response = await async_client.get("/v1/profile/user/list")

        assert response.status_code == 200
        profiles = response.json()

        # Verify response is a list
        assert isinstance(profiles, list)

        # Verify we got at least one profile
        assert len(profiles) >= 1

        # Verify the profile we linked to the user is in the response
        found = False
        for profile in profiles:
            if profile["username"] == mock_profile.username:
                found = True
                # Verify profile data matches
                assert profile["firstName"] == mock_profile.firstName
                assert profile["lastName"] == mock_profile.lastName
                assert profile["headline"] == mock_profile.headline
                assert profile["about"] == mock_profile.about
                break

        assert found, "User's profile not found in the response"

    finally:
        mock_profile.delete()
        mock_user.delete()
        test_app.dependency_overrides = {}


@pytest.mark.anyio
async def test_get_user_profiles_multiple(
    async_client, published_profiles_linked_to_user
):
    profiles, mock_user = published_profiles_linked_to_user

    test_app.dependency_overrides[get_current_user] = lambda: mock_user

    try:
        response = await async_client.get("/v1/profile/user/list")

        assert response.status_code == 200
        returned_profiles = response.json()

        # Should have same number of profiles
        assert len(returned_profiles) == len(profiles)

        # All created profiles should be present
        for profile in profiles:
            found = False
            for returned_profile in returned_profiles:
                if returned_profile["username"] == profile.username:
                    found = True
                    break
            assert found, f"Profile {profile.username} not found in response"

    finally:
        for profile in profiles:
            profile.delete()
        mock_user.delete()
        test_app.dependency_overrides = {}


@pytest.mark.anyio
async def test_get_user_profiles_no_profiles(async_client, mock_user):
    # Use a user with no profiles
    mock_user.profiles = []
    mock_user.save()

    test_app.dependency_overrides[get_current_user] = lambda: mock_user

    try:
        response = await async_client.get("/v1/profile/user/list")

        assert response.status_code == 200
        profiles = response.json()

        assert isinstance(profiles, list)
        assert len(profiles) == 0

    finally:
        mock_user.delete()
        test_app.dependency_overrides = {}


@pytest.mark.anyio
async def test_get_user_profiles_no_auth(async_client):
    response = await async_client.get("/v1/profile/user/list")

    assert response.status_code == 401
