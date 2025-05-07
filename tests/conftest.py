import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from mongoengine import connect, disconnect
from pydantic_settings import SettingsConfigDict
from src.config import Settings
from src.core.domain.models import GuestProfile, Profile, User
from src.core.interfaces import ILogger, IProfileDataProvider
from src.deps import get_settings
from src.infrastructure.persistence.configuration.database import Database
from src.main import build_app


### ------------ SETUP ------------ ###
class TestSettings(Settings):
    model_config = SettingsConfigDict(env_file=".env.test")


def get_test_settings():
    return TestSettings()  # type: ignore


class MockDatabase(Database):
    """Mock implementation of the Database class for testing."""

    @classmethod
    def connect(cls, mongodb_url: str, logger: ILogger):
        try:
            connect(
                "testdb",
                host=mongodb_url,
                uuidRepresentation="standard",
                # mongo_client_class=mongomock.MongoClient,
                alias="default",
            )
        except Exception:
            raise

    @classmethod
    def disconnect(cls, logger: ILogger):
        disconnect()


# Create test app with test database connection
test_app = build_app(MockDatabase)


# AnyIO uses both asyncio and trio by default (running all tests twice)
# Specify which backend to use to only run tests once
@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def app():
    test_app.dependency_overrides[get_settings] = get_test_settings

    async with LifespanManager(test_app) as manager:
        print("We're in!")
        yield manager.app
        test_app.dependency_overrides = {}


@pytest.fixture
async def async_client(app):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test/api"
    ) as client:
        yield client


### ------------ MOCK FIXTURES ------------ ###
@pytest.fixture
def mock_user():
    return User(
        email="johndoe@example.com",
        pw_hash="1234567890",
        firstName="John",
        lastName="Doe",
    )


@pytest.fixture
def mock_profile():
    return Profile(
        username="johndoe",
        firstName="John",
        lastName="Doe",
        headline="Software Developer",
        about="Experienced software developer with a passion for building scalable applications",
    )


@pytest.fixture
def mock_guest_profile():
    return GuestProfile(
        username="johndoe",
        firstName="John",
        lastName="Doe",
        headline="Software Developer",
        about="Experienced software developer with a passion for building scalable applications",
    )


@pytest.fixture
def remote_data():
    with open("tests/mock_remote_data_return.json", "r") as f:
        return json.load(f)


@pytest.fixture
def mock_profile_data_provider(remote_data):
    mock = MagicMock(spec=IProfileDataProvider)
    mock.get_profile_data_by_username = AsyncMock(return_value=remote_data)
    return mock


@pytest.fixture
def always_passes_cf_secret():
    return "1x0000000000000000000000000000000AA"


@pytest.fixture
def always_blocks_cf_secret():
    return "2x0000000000000000000000000000000AA"
