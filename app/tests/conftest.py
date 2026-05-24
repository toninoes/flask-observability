import os
import pytest
from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = (
    "postgresql://payments:payments@localhost:5432/paymentsdb_test"
)

from app import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c
