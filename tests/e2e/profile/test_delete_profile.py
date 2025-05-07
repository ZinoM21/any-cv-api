import pytest
from src.deps import get_current_user

from tests.conftest import test_app




@pytest.mark.anyio
async def test_delete_profile_success(async_client, profile_linked_to_user):
    mock_profile, mock_user = profile_linked_to_user

    test_app.dependency_overrides[get_current_user] = lambda: mock_user

    try:
        response = await async_client.delete(f"/v1/profile/{mock_profile.username}")

        assert response.status_code == 204
        assert response.content == b""

        # Verify the profile is deleted from the database directly
        from mongoengine import DoesNotExist
        from src.core.domain.models import Profile

        with pytest.raises(DoesNotExist):
            Profile.objects.get(username=mock_profile.username)  # type: ignore

    finally:
        mock_user.delete()
        test_app.dependency_overrides = {}


@pytest.mark.anyio
async def test_delete_nonexistent_profile(async_client, mock_user):
    test_app.dependency_overrides[get_current_user] = lambda: mock_user

    try:
        response = await async_client.delete("/v1/profile/nonexistent")

        assert response.status_code == 404

    finally:
        test_app.dependency_overrides = {}


@pytest.mark.anyio
async def test_delete_profile_no_user(async_client, mock_profile):
    mock_profile.save()

    try:
        response = await async_client.delete(f"/v1/profile/{mock_profile.username}")

        assert response.status_code == 401

    finally:
        mock_profile.delete()


@pytest.mark.anyio
async def test_delete_profile_not_linked_to_user(async_client, mock_user, mock_profile):
    mock_profile.save()
    mock_user.save()

    test_app.dependency_overrides[get_current_user] = lambda: mock_user

    try:
        response = await async_client.delete(f"/v1/profile/{mock_profile.username}")

        assert response.status_code == 404

    finally:
        mock_profile.delete()
        mock_user.delete()
        test_app.dependency_overrides = {}
