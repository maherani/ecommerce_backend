import pytest
from app.core.rate_limit import limiter
from fastapi.testclient import TestClient
from main import app
from app.core.database import SessionLocal
from app.modules.user.models import User
import uuid

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

@pytest.fixture(autouse=True)
def cleanup_test_users():
    """پاکسازی کاربران تستی بعد از هر تست"""
    yield
    db = SessionLocal()
    try:
        db.query(User).filter(User.email.like("%@example.com")).delete()
        db.commit()
    finally:
        db.close()

@pytest.fixture(autouse=True)
def reset_rate_limit():
    limiter.reset()
    yield
    limiter.reset()

@pytest.fixture
def test_user(client):
    email = f"user_{uuid.uuid4().hex[:6]}@example.com"
    password = "password123"
    client.post("/users/", json={"email": email, "password": password})
    return {"email": email, "password": password}

@pytest.fixture
def auth_token(client, test_user):
    response = client.post(
        "/users/login",
        data={"username": test_user["email"], "password": test_user["password"]}
    )
    return response.json()["access_token"]
