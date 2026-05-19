import pytest
from fastapi.testclient import TestClient

from langsmith_simple.main import app


@pytest.fixture
def client():
    return TestClient(app)
