import os
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Use an isolated in-memory-per-test SQLite DB and a throwaway Chroma dir,
# set BEFORE importing the app, so nothing here touches real dev data.
os.environ["DATABASE_URL"] = "sqlite:///./test_flowmind.db"
os.environ["CHROMA_PERSIST_DIR"] = "./test_chroma_data"
os.environ["SECRET_KEY"] = "test-secret-key"

from app.core.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402

engine = create_engine("sqlite:///./test_flowmind.db", connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function", autouse=True)
def _fresh_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    client.post(
        "/api/auth/signup",
        json={"full_name": "Test User", "email": "test@example.com", "password": "password123"},
    )
    res = client.post("/api/auth/login", json={"email": "test@example.com", "password": "password123"})
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
