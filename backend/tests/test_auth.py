def test_signup_creates_user_and_returns_token(client):
    res = client.post(
        "/api/auth/signup",
        json={"full_name": "Ada Lovelace", "email": "ada@example.com", "password": "password123"},
    )
    assert res.status_code == 201
    body = res.json()
    assert body["user"]["email"] == "ada@example.com"
    assert body["access_token"]


def test_signup_rejects_duplicate_email(client):
    payload = {"full_name": "Ada", "email": "dupe@example.com", "password": "password123"}
    client.post("/api/auth/signup", json=payload)
    res = client.post("/api/auth/signup", json=payload)
    assert res.status_code == 400


def test_login_rejects_wrong_password(client):
    client.post(
        "/api/auth/signup",
        json={"full_name": "Grace", "email": "grace@example.com", "password": "correct-password"},
    )
    res = client.post("/api/auth/login", json={"email": "grace@example.com", "password": "wrong"})
    assert res.status_code == 401


def test_me_requires_auth(client):
    res = client.get("/api/auth/me")
    assert res.status_code == 401


def test_me_returns_current_user(client, auth_headers):
    res = client.get("/api/auth/me", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["email"] == "test@example.com"
