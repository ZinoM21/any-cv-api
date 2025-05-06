import json
from unittest.mock import AsyncMock, MagicMock

import mongomock
import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from mongoengine import connect, disconnect
from src.core.domain.models import User
from src.core.interfaces import IRemoteDataSource
from src.main import app


# AnyIO uses both asyncio and trio by default (running all tests twice)
# This fixture is used to specify the backend to use for the tests
@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
def mock_user():
    return User(
        email="johndoe@example.com",
        pw_hash="1234567890",
        firstName="John",
        lastName="Doe",
    )


@pytest.fixture
def remote_data():
    with open("tests/demo_data.json", "r") as f:
        return json.load(f)


@pytest.fixture
def mock_remote_data_source(remote_data):
    mock = MagicMock(spec=IRemoteDataSource)
    mock.get_profile_data_by_username = AsyncMock(return_value=remote_data)
    return mock


# @pytest.fixture
# def mock_profile_service(mock_remote_data_source):
#     app.dependency_overrides[get_linkedin_api] = lambda: mock_remote_data_source

#     mock = MagicMock(spec=IProfileService)
#     # mock.get_profile = AsyncMock(return_value=mock_profile)

#     return mock


# @pytest.fixture
# def mock_auth_service():
#     mock = MagicMock(spec=IAuthService)
#     mock.verify_turnstile = AsyncMock(return_value=True)
#     return mock


@pytest.fixture
async def async_client():
    connect(
        db="testdb",
        host="mongodb://localhost:27017",
        alias="testdb",
        mongo_client_class=mongomock.MongoClient,
        uuidRepresentation="standard",
    )

    async with LifespanManager(app):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test/api"
        ) as client:
            yield client

    disconnect()
