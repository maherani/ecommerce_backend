import os
import uuid

import psycopg2
import pytest
from alembic import command
from alembic.config import Config
from dotenv import load_dotenv
from fastapi.testclient import TestClient

load_dotenv()

POSTGRES_USER = os.environ["POSTGRES_USER"]
POSTGRES_PASSWORD = os.environ["POSTGRES_PASSWORD"]
POSTGRES_HOST = os.environ["POSTGRES_HOST"]
POSTGRES_PORT = os.environ["POSTGRES_PORT"]
POSTGRES_DB = os.environ["POSTGRES_DB"]

TEST_DATABASE_NAME = f"{POSTGRES_DB}_test"

admin_connection = psycopg2.connect(
    host=POSTGRES_HOST,
    port=POSTGRES_PORT,
    user=POSTGRES_USER,
    password=POSTGRES_PASSWORD,
    dbname=POSTGRES_DB,
)

admin_connection.autocommit = True

try:
    with admin_connection.cursor() as cursor:
        cursor.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            (TEST_DATABASE_NAME,),
        )

        database_exists = cursor.fetchone() is not None

        if not database_exists:
            cursor.execute(
                f'CREATE DATABASE "{TEST_DATABASE_NAME}"'
            )
finally:
    admin_connection.close()

TEST_DATABASE_URL = (
    f"postgresql://"
    f"{POSTGRES_USER}:"
    f"{POSTGRES_PASSWORD}@"
    f"{POSTGRES_HOST}:"
    f"{POSTGRES_PORT}/"
    f"{TEST_DATABASE_NAME}"
)

os.environ["TEST_DATABASE_URL"] = TEST_DATABASE_URL

alembic_config = Config("alembic.ini")
command.upgrade(alembic_config, "head")

from app.core.database import SessionLocal
from app.core.rate_limit import limiter
from app.modules.user.models import User
from main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(
        app,
        raise_server_exceptions=False,
    ) as c:
        yield c


@pytest.fixture(autouse=True)
def cleanup_test_users():
    """پاکسازی کاربران تستی بعد از هر تست."""
    yield

    db = SessionLocal()

    try:
        db.query(User).filter(
            User.email.like("%@example.com")
        ).delete()
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

    client.post(
        "/users/",
        json={
            "email": email,
            "password": password,
        },
    )

    return {
        "email": email,
        "password": password,
    }


@pytest.fixture
def auth_token(client, test_user):
    response = client.post(
        "/users/login",
        data={
            "username": test_user["email"],
            "password": test_user["password"],
        },
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
            "password": password,
        },
    )

    assert response.status_code == 201

    db = SessionLocal()

    try:
        user = db.query(User).filter(
            User.email == email
        ).first()

        assert user is not None

        user.is_superuser = True
        db.commit()
    finally:
        db.close()

    return {
        "email": email,
        "password": password,
    }


@pytest.fixture
def admin_token(client, admin_user):
    response = client.post(
        "/users/login",
        data={
            "username": admin_user["email"],
            "password": admin_user["password"],
        },
    )

    assert response.status_code == 200

    return response.json()["access_token"]