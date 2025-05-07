import pytest
from src.core.domain.models import Profile, PublishingOptions


@pytest.fixture
def profile_linked_to_user(mock_user, mock_profile):
    mock_profile.save()
    mock_user.profiles = [mock_profile]
    mock_user.save()

    return mock_profile, mock_user


@pytest.fixture
def published_profile(mock_profile):
    profile = mock_profile

    publishing_options = PublishingOptions(
        appearance="light", templateId="classic", slug="published-user"
    )

    profile.publishingOptions = publishing_options
    profile.save()

    return profile


@pytest.fixture
def published_profile_linked_to_user(mock_user, mock_profile):
    publishing_options = PublishingOptions(
        appearance="light", templateId="classic", slug="published-profile"
    )

    mock_profile.publishingOptions = publishing_options
    mock_profile.save()

    # Link profile to user
    mock_user.profiles = [mock_profile]
    mock_user.save()

    return mock_profile, mock_user


@pytest.fixture
def published_profiles():
    profiles = []
    for i in range(1, 4):
        profile = Profile(
            username=f"testuser{i}",
            firstName=f"Test{i}",
            lastName=f"User{i}",
            headline=f"Test Headline {i}",
            about=f"Test About {i}",
        )

        publishing_options = PublishingOptions(
            appearance="light" if i % 2 == 0 else "dark",
            templateId="classic" if i % 2 == 0 else "modern",
            slug=f"test-user-{i}",
        )

        profile.publishingOptions = publishing_options
        profile.save()
        profiles.append(profile)

    return profiles


@pytest.fixture
def published_profiles_linked_to_user(mock_user):
    profiles = []
    for i in range(1, 4):
        profile = Profile(
            username=f"testuser{i}",
            firstName=f"Test{i}",
            lastName=f"User{i}",
            headline=f"Test Headline {i}",
            about=f"Test About {i}",
        )

        profile.save()
        profiles.append(profile)

    # Link profiles to user
    mock_user.profiles = profiles
    mock_user.save()

    return profiles, mock_user


@pytest.fixture
def guest_profile_for_transfer(mock_guest_profile):
    """Creates a guest profile for testing the transfer functionality"""
    mock_guest_profile.save()
    return mock_guest_profile
