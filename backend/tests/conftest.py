import os

os.environ["ECHONOTE_DATABASE_URL"] = "sqlite+aiosqlite:///./test_echonote_moments.db"

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session")
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client
