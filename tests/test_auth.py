import uuid
from unittest.mock import patch


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
