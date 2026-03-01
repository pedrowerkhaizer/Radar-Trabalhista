import sys
import os

# Ensure apps/api is on sys.path so flat imports resolve correctly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient

from main import app
from db import get_db, get_redis


@pytest.fixture
def mock_db():
    session = AsyncMock()
    session.execute = AsyncMock()
    return session


@pytest.fixture
def mock_redis():
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.setex = AsyncMock()
    redis.keys = AsyncMock(return_value=[])
    redis.delete = AsyncMock(return_value=0)
    return redis


@pytest.fixture
def client(mock_db, mock_redis):
    async def override_db():
        yield mock_db

    async def override_redis():
        return mock_redis

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_redis] = override_redis
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
