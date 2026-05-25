"""Tests for authentication: password hashing, JWT tokens, and auth API endpoints."""


class TestPasswordHashing:
    def test_hash_and_verify(self):
        from src.auth.security import hash_password, verify_password

        pw = "mysecretpassword"
        hashed = hash_password(pw)
        assert ":" in hashed
        assert verify_password(pw, hashed)
        assert not verify_password("wrongpassword", hashed)

    def test_unique_salts(self):
        from src.auth.security import hash_password

        h1 = hash_password("same")
        h2 = hash_password("same")
        assert h1 != h2  # Different salts each time


class TestJWTTokens:
    def test_create_and_decode(self):
        from src.auth.security import create_access_token, decode_token

        token = create_access_token({"sub": "user123"})
        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == "user123"
        assert "exp" in payload

    def test_invalid_token(self):
        from src.auth.security import decode_token

        assert decode_token("invalid.token.string") is None
        assert decode_token("") is None


class TestAuthAPI:
    def test_register_and_login(self, client):
        # Register
        r = client.post("/api/v1/auth/register", json={
            "email": "new@test.com",
            "username": "newuser",
            "password": "secret123",
        })
        assert r.status_code == 201
        data = r.json()
        assert data["email"] == "new@test.com"
        assert data["username"] == "newuser"
        assert "id" in data

        # Login
        r = client.post("/api/v1/auth/login", json={
            "email": "new@test.com",
            "password": "secret123",
        })
        assert r.status_code == 200
        assert "access_token" in r.json()

    def test_register_duplicate_email(self, client):
        client.post("/api/v1/auth/register", json={
            "email": "dup@test.com", "username": "user1", "password": "pass123",
        })
        r = client.post("/api/v1/auth/register", json={
            "email": "dup@test.com", "username": "user2", "password": "pass123",
        })
        assert r.status_code == 400

    def test_login_wrong_password(self, client):
        client.post("/api/v1/auth/register", json={
            "email": "user@test.com", "username": "user1", "password": "correct",
        })
        r = client.post("/api/v1/auth/login", json={
            "email": "user@test.com", "password": "wrong",
        })
        assert r.status_code == 401

    def test_get_me(self, client, auth_headers):
        r = client.get("/api/v1/auth/me", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["email"] == "test@example.com"

    def test_get_me_no_token(self, client):
        r = client.get("/api/v1/auth/me")
        assert r.status_code == 401

    def test_short_password_rejected(self, client):
        r = client.post("/api/v1/auth/register", json={
            "email": "short@test.com", "username": "short", "password": "abc",
        })
        assert r.status_code == 400

    def test_password_without_digits_rejected(self, client):
        r = client.post("/api/v1/auth/register", json={
            "email": "nodigits@test.com", "username": "nodigits", "password": "password!",
        })
        assert r.status_code == 400
