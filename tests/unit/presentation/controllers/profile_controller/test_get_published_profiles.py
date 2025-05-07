import pytest
from src.deps import get_profile_service

from tests.conftest import test_app


@pytest.mark.anyio
async def test_get_published_profiles_success(async_client, mock_profile_service):
    test_app.dependency_overrides[get_profile_service] = lambda: mock_profile_service

    response = await async_client.get(
        "/v1/profile/published",
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

    test_app.dependency_overrides = {}
