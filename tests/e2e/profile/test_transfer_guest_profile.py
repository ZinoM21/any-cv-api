import pytest
from src.deps import get_current_user

from tests.conftest import test_app


@pytest.mark.anyio
async def test_transfer_guest_profile_success(
    async_client, mock_guest_profile, mock_user
):
    guest_profile = mock_guest_profile.save()
    mock_user = mock_user.save()

    guest_username = guest_profile.username

    test_app.dependency_overrides[get_current_user] = lambda: mock_user

    try:
        response = await async_client.get(f"/v1/profile/{guest_username}/transfer")

        assert response.status_code == 200
        profile_data = response.json()

        assert profile_data["username"] == guest_username
        assert profile_data["firstName"] == guest_profile.firstName
        assert profile_data["lastName"] == guest_profile.lastName
        assert profile_data["headline"] == guest_profile.headline
        assert profile_data["about"] == guest_profile.about

    finally:
        from src.core.domain.models import Profile

        Profile.objects.get(username=guest_username).delete()  # type: ignore
        mock_user.delete()

        test_app.dependency_overrides = {}


@pytest.mark.anyio
async def test_transfer_nonexistent_guest_profile(async_client, mock_user):
    test_app.dependency_overrides[get_current_user] = lambda: mock_user

    try:
        response = await async_client.get("/v1/profile/nonexistent/transfer")

        assert response.status_code == 404

    finally:
        test_app.dependency_overrides = {}


@pytest.mark.anyio
async def test_transfer_guest_profile_no_auth(async_client, mock_guest_profile):

    mock_guest_profile.save()

    try:
        response = await async_client.get(
            f"/v1/profile/{mock_guest_profile.username}/transfer"
        )

        assert response.status_code == 401

    finally:
        mock_guest_profile.delete()
        pass


@pytest.mark.anyio
async def test_transfer_guest_profile_already_exists(
    async_client,
    profile_linked_to_user,
    mock_guest_profile,
):
    # Save guest profile & profile linked to user (assert same usernames)
    mock_guest_profile.save()
    mock_profile, mock_user = profile_linked_to_user
    assert mock_profile.username == mock_guest_profile.username

    test_app.dependency_overrides[get_current_user] = lambda: mock_user

    try:
        response = await async_client.get(
            f"/v1/profile/{mock_guest_profile.username}/transfer"
        )

        assert response.status_code == 200
        profile_data = response.json()
        assert profile_data["username"] == mock_profile.username

    finally:
        mock_profile.delete()
        mock_user.delete()
        test_app.dependency_overrides = {}
