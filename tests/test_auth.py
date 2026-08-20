import uuid

def test_create_user(client):
    unique_email = f"user_{uuid.uuid4().hex[:6]}@example.com"
    response = client.post(
        "/users/",
        json={"email": unique_email, "password": "password123"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == unique_email
    assert "id" in data

def test_login_user(client, test_user):
    # از test_user که فیکسچر آماده کرده استفاده می‌کنیم
    response = client.post(
        "/users/login",
        data={"username": test_user["email"], "password": test_user["password"]}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_get_current_user_profile(client, auth_token):
    # اینجا تست می‌کنیم که توکن ساخته شده معتبر است و پروفایل را برمی‌گرداند
    response = client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
