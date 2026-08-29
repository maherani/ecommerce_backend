import asyncio
import uuid
from unittest.mock import patch

from app.core.config import settings
from app.core.config import validate_security_settings
from main import unhandled_exception_handler

@patch("app.modules.user.router.send_welcome_email_task.delay")
def test_create_user_queues_welcome_email(mock_delay, client):
    """Registration persists the user and enqueues its non-blocking welcome task."""
    unique_email = f"user_{uuid.uuid4().hex[:6]}@example.com"

    response = client.post(
        "/users/",
        json={"email": unique_email, "password": "password123"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == unique_email
    assert "id" in data
    mock_delay.assert_called_once_with(unique_email, unique_email)


@patch("app.modules.user.router.send_welcome_email_task.delay")
def test_create_user_rejects_short_password(mock_delay, client):
    unique_email = f"short_{uuid.uuid4().hex[:6]}@example.com"

    response = client.post(
        "/users/",
        json={
            "email": unique_email,
            "password": "short",
        },
    )

    assert response.status_code == 422
    mock_delay.assert_not_called()


def test_login_user(client, test_user):
    # Use the prepared test user fixture.
    response = client.post(
        "/users/login",
        data={"username": test_user["email"], "password": test_user["password"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_get_current_user_profile(client, auth_token):
    # A valid JWT returns the current user's profile.
    response = client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 200


def test_security_headers(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert (
        response.headers["Referrer-Policy"]
        == "strict-origin-when-cross-origin"
    )
    assert (
        response.headers["Permissions-Policy"]
        == "geolocation=(), microphone=(), camera=()"
    )


def test_cors_allows_configured_origin(client):
    response = client.options(
        "/",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert (
        response.headers["access-control-allow-origin"]
        == "http://localhost:3000"
    )


def test_cors_rejects_unconfigured_origin(client):
    response = client.options(
        "/",
        headers={
            "Origin": "http://evil.example.com",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers


def test_security_settings_validation_rejects_empty_values():
    original_secret = settings.SECRET_KEY
    original_webhook_secret = settings.PAYMENT_WEBHOOK_SECRET

    try:
        settings.SECRET_KEY = ""
        settings.PAYMENT_WEBHOOK_SECRET = ""

        try:
            validate_security_settings()
            assert False, "Expected ValueError"
        except ValueError as exc:
            assert "SECRET_KEY" in str(exc)
    finally:
        settings.SECRET_KEY = original_secret
        settings.PAYMENT_WEBHOOK_SECRET = original_webhook_secret


def test_security_settings_are_configured():
    assert settings.SECRET_KEY.strip()
    assert settings.PAYMENT_WEBHOOK_SECRET.strip()

def test_unhandled_exception_handler_returns_safe_error():
    response = asyncio.run(
        unhandled_exception_handler(
            None,
            RuntimeError("sensitive internal error"),
        )
    )

    assert response.status_code == 500
    assert response.body == b'{"detail":"Internal server error"}'
