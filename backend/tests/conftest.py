import os

os.environ["ECHONOTE_DATABASE_URL"] = "sqlite+aiosqlite:///./test_echonote_moments.db"
os.environ["ECHONOTE_ENVIRONMENT"] = "test"
os.environ["ECHONOTE_AUTH_REQUIRED"] = "false"
os.environ["ECHONOTE_SUPABASE_URL"] = ""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session")
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client
