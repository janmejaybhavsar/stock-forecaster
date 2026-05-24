"""
Shared test fixtures for the stock-forecaster test suite.
Uses an in-memory SQLite database and mocked data providers.
"""

import sqlite3
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.database.connection import SCHEMA


@pytest.fixture()
def db():
    """Create a fresh in-memory SQLite database with schema applied."""
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(SCHEMA)
    conn.commit()
    yield conn
    conn.close()


@pytest.fixture()
def patched_db(db):
    """Patch get_db() everywhere so all repos use the in-memory DB."""
    with patch("src.database.connection.get_db", return_value=db), \
         patch("src.database.repositories.get_db", return_value=db):
        yield db


@pytest.fixture()
def user_repo(patched_db):
    from src.database.repositories import UserRepository
    return UserRepository()


@pytest.fixture()
def sample_user(user_repo):
    """Create and return a sample user."""
    from src.auth.security import hash_password
    return user_repo.create("test@example.com", "testuser", hash_password("password123"))


@pytest.fixture()
def holdings_repo(patched_db):
    from src.database.repositories import HoldingsRepository
    return HoldingsRepository()


@pytest.fixture()
def app(patched_db):
    """Create a FastAPI test app with the in-memory DB."""
    from src.api.app import create_app
    return create_app()


@pytest.fixture()
def client(app):
    """FastAPI test client."""
    from fastapi.testclient import TestClient
    return TestClient(app)


@pytest.fixture()
def auth_headers(client):
    """Register a user and return auth headers."""
    client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "username": "testuser",
        "password": "password123",
    })
    r = client.post("/api/v1/auth/login", json={
        "email": "test@example.com",
        "password": "password123",
    })
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
