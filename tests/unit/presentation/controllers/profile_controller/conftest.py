from unittest.mock import AsyncMock, MagicMock

import pytest
from src.core.interfaces import IProfileService


@pytest.fixture
def mock_profile():
    return {
        "username": "johndoe",
        "firstName": "John",
        "lastName": "Doe",
        "headline": "Software Engineer",
    }


@pytest.fixture
def mock_profiles(mock_profile):
    return [mock_profile, mock_profile]


@pytest.fixture
def mock_profile_service(mock_profile, mock_profiles):

    mock = MagicMock(spec=IProfileService)
    mock.get_profile = AsyncMock(return_value=mock_profile)
    mock.create_profile = AsyncMock(return_value=mock_profile)
    mock.get_published_profile = AsyncMock(return_value=mock_profile)
    mock.get_published_profiles = AsyncMock(return_value=mock_profiles)
    mock.update_profile = AsyncMock(return_value=mock_profile)
    mock.delete_profile = AsyncMock(return_value=None)
    mock.delete_profiles_from_user = AsyncMock(return_value=None)
    mock.publish_profile = AsyncMock(return_value=mock_profile)
    mock.unpublish_profile = AsyncMock(return_value=mock_profile)
    mock.transfer_guest_profile_to_user = AsyncMock(return_value=mock_profile)
    mock.get_user_profiles = AsyncMock(return_value=mock_profiles)

    return mock
