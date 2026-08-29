import pytest
from app.core.rate_limit import limiter
from fastapi.testclient import TestClient
from main import app
from app.core.database import SessionLocal
from app.modules.user.models import User
import uuid

@pytest.fixture(scope="module")
def client():
    with TestClient(
        app,
        raise_server_exceptions=False,
    ) as c:
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

@pytest.fixture
def admin_user(client):
    email = f"admin_{uuid.uuid4().hex[:6]}@example.com"
    password = "password123"

    response = client.post(
        "/users/",
        json={
            "email": email,
            "password": password
        }
    )

    assert response.status_code == 201

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        assert user is not None

        user.is_superuser = True
        db.commit()
    finally:
        db.close()

    return {
        "email": email,
        "password": password
    }


@pytest.fixture
def admin_token(client, admin_user):
    response = client.post(
        "/users/login",
        data={
            "username": admin_user["email"],
            "password": admin_user["password"]
        }
    )

    assert response.status_code == 200

    return response.json()["access_token"]
