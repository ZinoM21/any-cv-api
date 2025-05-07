import pytest
from src.deps import (
    get_cf_secret,
    get_profile_data_provider,
)

from ..conftest import test_app


@pytest.mark.anyio
async def test_create_profile_without_token_without_user(async_client):
    response = await async_client.post(
        "/v1/profile/johndoe",
        json={},
    )

    assert response.status_code == 400


@pytest.mark.anyio
async def test_create_profile_without_body(async_client):

    response = await async_client.post(
        "/v1/profile/johndoe",
    )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_create_profile_without_user_with_valid_turnstile_token(
    async_client, mock_profile_data_provider, always_passes_cf_secret
):
    test_app.dependency_overrides[get_profile_data_provider] = (
        lambda: mock_profile_data_provider
    )
    test_app.dependency_overrides[get_cf_secret] = lambda: always_passes_cf_secret

    response = await async_client.post(
        "/v1/profile/johndoe",
        json={"turnstileToken": "XXXX.DUMMY.TOKEN.XXXX"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "johndoe"
    assert data["firstName"] == "John"
    assert data["lastName"] == "Doe"

    test_app.dependency_overrides = {}


@pytest.mark.anyio
async def test_create_profile_without_user_with_invalid_turnstile_token(
    async_client, mock_profile_data_provider, always_blocks_cf_secret
):
    test_app.dependency_overrides[get_profile_data_provider] = (
        lambda: mock_profile_data_provider
    )
    test_app.dependency_overrides[get_cf_secret] = lambda: always_blocks_cf_secret

    response = await async_client.post(
        "/v1/profile/johndoe",
        json={"turnstileToken": "XXXX.INVALID.TOKEN.XXXX"},
    )

    assert response.status_code == 500

    test_app.dependency_overrides = {}


@pytest.mark.anyio
async def test_create_profile_without_turnstile_token(
    async_client, mock_profile_data_provider
):

    test_app.dependency_overrides[get_profile_data_provider] = (
        lambda: mock_profile_data_provider
    )

    response = await async_client.post(
        "/v1/profile/johndoe",
        json={},
    )

    assert response.status_code == 400
