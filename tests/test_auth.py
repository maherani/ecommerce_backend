import asyncio
import uuid
from unittest.mock import patch
from starlette.requests import Request

from app.core.config import settings
from app.core.config import validate_security_settings
from main import MetricsMiddleware, app, unhandled_exception_handler

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
            Request(
                {
                    "type": "http",
                    "method": "GET",
                    "path": "/test",
                    "headers": [],
                    "query_string": b"",
                    "scheme": "http",
                    "server": ("testserver", 80),
                    "client": ("testclient", 123),
                }
            ),
            RuntimeError("sensitive internal error"),
        )
    )

    assert response.status_code == 500
    assert response.body == b'{"detail":"Internal server error"}'

def test_metrics_endpoint_exposes_http_metrics(client):
    response = client.get("/")

    assert response.status_code == 200

    metrics_response = client.get("/metrics")

    assert metrics_response.status_code == 200
    body = metrics_response.text

    assert "# HELP http_requests_total" in body
    assert "# TYPE http_requests_total counter" in body
    assert 'http_requests_total{endpoint="/",method="GET",status="200"}' in body

    assert "# HELP http_request_duration_seconds" in body
    assert "# TYPE http_request_duration_seconds histogram" in body
    assert 'http_request_duration_seconds_count{endpoint="/",method="GET"}' in body

def test_request_id_is_returned_and_preserved(client):
    request_id = "test-request-id-123"

    response = client.get(
        "/",
        headers={"X-Request-ID": request_id},
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == request_id

def test_request_id_is_generated_when_missing(client):
    response = client.get("/")

    assert response.status_code == 200
    request_id = response.headers.get("X-Request-ID")

    assert request_id is not None
    assert len(request_id) == 36
    assert request_id.count("-") == 4

def test_client_error_is_recorded_in_metrics(client):
    response = client.get(
        "/users/999999999",
        headers={"X-Request-ID": "test-404-request"},
    )

    assert response.status_code in (404, 405)

    metrics_response = client.get("/metrics")

    assert metrics_response.status_code == 200
    body = metrics_response.text

    assert 'status="404"' in body or 'status="405"' in body

def test_metrics_middleware_records_500_on_exception(client):
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/test-500",
            "headers": [],
            "query_string": b"",
            "scheme": "http",
            "server": ("testserver", 80),
            "client": ("testclient", 123),
        }
    )

    middleware = MetricsMiddleware(app)

    async def call_next(request):
        raise RuntimeError("test failure")

    try:
        asyncio.run(middleware.dispatch(request, call_next))
    except RuntimeError:
        pass
    else:
        assert False, "Expected RuntimeError"

    metrics_response = client.get("/metrics")

    assert metrics_response.status_code == 200
    body = metrics_response.text

    assert (
        'http_requests_total{endpoint="/test-500",method="GET",status="500"}'
        in body
    )
def test_unhandled_exception_logs_request_id(caplog):
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/test-error",
            "headers": [],
            "query_string": b"",
            "scheme": "http",
            "server": ("testserver", 80),
            "client": ("testclient", 123),
        }
    )

    request.state.request_id = "test-error-request-789"

    with caplog.at_level("ERROR", logger="app.request"):
        response = asyncio.run(
            unhandled_exception_handler(
                request,
                RuntimeError("sensitive internal error"),
            )
        )

    assert response.status_code == 500
    assert "Unhandled application exception" in caplog.text
    assert any(
        record.request_id == "test-error-request-789"
        for record in caplog.records
    )