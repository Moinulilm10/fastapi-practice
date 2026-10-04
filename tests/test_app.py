"""Tests for the database-backed FastAPI endpoints."""

import asyncio
import importlib
import uuid
from collections.abc import Iterator
from typing import cast

import httpx
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import text

from app.db.db import engine
from app.schemas import PostCreate, PostResponse

app_module = importlib.import_module("app.app")


@pytest.fixture(name="test_client")
def create_test_client_fixture() -> Iterator[httpx.Client]:
    """Create a test client and run the application lifespan."""
    with TestClient(app_module.app) as active_client:
        yield cast(httpx.Client, active_client)
    asyncio.run(engine.dispose())


def register_and_login(test_client: httpx.Client, email: str, password: str) -> str:
    """Create a user and return a valid JWT for authenticated API calls."""
    register_response = test_client.post(
        "/auth/register", json={"email": email, "password": password}
    )
    assert register_response.status_code == 201

    login_response = test_client.post(
        "/auth/jwt/login",
        data={"username": email, "password": password},
    )
    assert login_response.status_code == 200
    return login_response.json()["access_token"]


def test_upload_file_returns_saved_metadata(
    test_client: httpx.Client,
):
    """Save an uploaded file and return its metadata."""
    email = f"upload-{uuid.uuid4()}@example.com"
    token = register_and_login(test_client, email, "Password123!")

    response = test_client.post(
        "/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("photo.jpg", b"file contents", "image/jpeg")},
        data={"caption": "A test photo"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["caption"] == "A test photo"
    assert body["file_name"].endswith(".jpg")
    assert body["file_type"] == "image"


def test_feed_returns_saved_posts(test_client: httpx.Client):
    """Return saved post metadata from the feed endpoint."""
    email = f"feed-{uuid.uuid4()}@example.com"
    token = register_and_login(test_client, email, "Password123!")
    test_client.post(
        "/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("feed.txt", b"feed contents", "text/plain")},
        data={"caption": "Feed item"},
    )

    response = test_client.get("/feed", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert any(post["caption"] == "Feed item" for post in response.json()["posts"])


def test_post_create_schema_accepts_valid_data():
    """Accept valid post creation data."""
    post = PostCreate(title="Title", content="Content")

    assert post.title == "Title"
    assert post.content == "Content"


def test_post_response_schema_rejects_missing_fields():
    """Reject post response data with required fields missing."""
    with pytest.raises(ValidationError):
        PostResponse.model_validate({"title": "Only title"})


def test_database_connection_succeeds():
    """Verify that the configured PostgreSQL database accepts a query."""

    async def check_connection() -> int:
        async with engine.connect() as connection:
            result = await connection.execute(text("SELECT 1"))
            return int(result.scalar_one())

    assert asyncio.run(check_connection()) == 1
