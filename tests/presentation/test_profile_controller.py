import pytest
from src.deps import (
    get_linkedin_api,
    get_optional_current_user,
)
from src.main import app


@pytest.mark.anyio
async def test_create_profile_without_user_with_turnstile_token(
    async_client, mock_remote_data_source
):
    app.dependency_overrides[get_linkedin_api] = lambda: mock_remote_data_source

    response = await async_client.post(
        "/v1/profile/johndoe",
        json={"turnstileToken": "1234567890"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "johndoe"
    assert data["firstName"] == "John"
    assert data["lastName"] == "Doe"


@pytest.mark.anyio
async def test_create_profile_with_user_without_turnstile_token(
    async_client, mock_remote_data_source, mock_user
):
    app.dependency_overrides[get_linkedin_api] = lambda: mock_remote_data_source
    app.dependency_overrides[get_optional_current_user] = lambda: mock_user

    response = await async_client.post(
        "/v1/profile/johndoe",
        json={},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "johndoe"
    assert data["firstName"] == "John"
    assert data["lastName"] == "Doe"
