import pytest
from src.deps import (
    get_cf_secret,
    get_optional_current_user,
    get_profile_data_provider,
)

from tests.conftest import test_app


@pytest.mark.anyio
async def test_create_profile_without_user_with_valid_turnstile_token(
    async_client, mock_profile_data_provider, always_passes_cf_secret
):
    test_app.dependency_overrides[get_profile_data_provider] = (
        lambda: mock_profile_data_provider
    )
    test_app.dependency_overrides[get_cf_secret] = lambda: always_passes_cf_secret

    try:
        response = await async_client.post(
            "/v1/profile/johndoe",
            json={"turnstileToken": "XXXX.DUMMY.TOKEN.XXXX"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "johndoe"
        assert data["firstName"] == "John"
        assert data["lastName"] == "Doe"
        assert (
            data["headline"] == "Backend Developer @Netflix | Python & FastAPI Expert"
        )
        assert "about" in data

    finally:
        from src.core.domain.models import GuestProfile

        GuestProfile.objects(username="johndoe").delete()  # type: ignore
        test_app.dependency_overrides = {}


@pytest.mark.anyio
async def test_create_profile_without_user_with_invalid_turnstile_token(
    async_client, mock_profile_data_provider, always_blocks_cf_secret
):
    test_app.dependency_overrides[get_profile_data_provider] = (
        lambda: mock_profile_data_provider
    )
    test_app.dependency_overrides[get_cf_secret] = lambda: always_blocks_cf_secret

    try:
        response = await async_client.post(
            "/v1/profile/johndoe",
            json={"turnstileToken": "XXXX.INVALID.TOKEN.XXXX"},
        )

        assert response.status_code == 422

    finally:
        test_app.dependency_overrides = {}


@pytest.mark.anyio
async def test_create_profile_with_user(
    async_client, mock_profile_data_provider, mock_user
):
    test_app.dependency_overrides[get_profile_data_provider] = (
        lambda: mock_profile_data_provider
    )
    test_app.dependency_overrides[get_optional_current_user] = lambda: mock_user

    mock_user.save()

    try:
        response = await async_client.post(
            "/v1/profile/johndoe",
            json={"turnstileToken": "not-needed-for-authenticated-users"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "johndoe"
        assert data["firstName"] == "John"
        assert data["lastName"] == "Doe"

    finally:
        from src.core.domain.models import Profile

        Profile.objects(username="johndoe").delete()  # type: ignore
        mock_user.delete()
        test_app.dependency_overrides = {}


@pytest.mark.anyio
async def test_create_profile_user_already_has_profile(
    async_client, mock_profile_data_provider, profile_linked_to_user
):
    test_app.dependency_overrides[get_profile_data_provider] = (
        lambda: mock_profile_data_provider
    )
    mock_profile, mock_user = profile_linked_to_user

    test_app.dependency_overrides[get_optional_current_user] = lambda: mock_user

    try:
        # Try to create the same profile again
        response = await async_client.post(
            f"/v1/profile/{mock_profile.username}",
            json={"turnstileToken": "not-needed"},
        )

        assert response.status_code == 409

    finally:
        mock_profile.delete()
        mock_user.delete()
        test_app.dependency_overrides = {}


@pytest.mark.anyio
async def test_create_profile_without_user_cache_hit(
    async_client, mock_profile_data_provider, always_passes_cf_secret
):
    """Test creating the same profile as guest twice - second should be a cache hit"""
    test_app.dependency_overrides[get_profile_data_provider] = (
        lambda: mock_profile_data_provider
    )
    test_app.dependency_overrides[get_cf_secret] = lambda: always_passes_cf_secret

    try:
        # First: create guest profile
        first_response = await async_client.post(
            "/v1/profile/johndoe",
            json={"turnstileToken": "XXXX.DUMMY.TOKEN.XXXX"},
        )
        assert first_response.status_code == 200
        first_data = first_response.json()

        # Track call count to profile_data_provider
        call_count = mock_profile_data_provider.get_profile_data_by_username.call_count

        # Second: hit cache
        second_response = await async_client.post(
            "/v1/profile/johndoe",
            json={"turnstileToken": "XXXX.DUMMY.TOKEN.XXXX"},
        )

        assert second_response.status_code == 200
        second_data = second_response.json()
        assert first_data["username"] == second_data["username"]
        assert first_data["firstName"] == second_data["firstName"]
        assert first_data["lastName"] == second_data["lastName"]

        assert (
            mock_profile_data_provider.get_profile_data_by_username.call_count
            == call_count
        )

    finally:
        from src.core.domain.models import GuestProfile

        GuestProfile.objects(username="johndoe").delete()  # type: ignore
        test_app.dependency_overrides = {}


@pytest.mark.anyio
async def test_create_profile_no_user_no_turnstile_token(async_client):
    """Test that guest requests without turnstile token are rejected"""
    try:
        response = await async_client.post(
            "/v1/profile/johndoe",
            json={},
        )

        assert response.status_code == 422

    finally:
        pass
