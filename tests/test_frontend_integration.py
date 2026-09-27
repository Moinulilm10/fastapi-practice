"""Integration tests for frontend requests against the FastAPI application."""

import importlib
from collections.abc import AsyncGenerator, Iterator
from contextlib import asynccontextmanager
from types import SimpleNamespace
from typing import Any, cast
from urllib.parse import urlparse

import httpx
import pytest
import requests
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import frontend
from app.db.db import Base, get_async_session

api_module = importlib.import_module("app.app")


@pytest.fixture(name="isolated_api_client")
def create_isolated_api_client_fixture(
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[httpx.Client]:
    """Run the API against a fresh in-memory database for integration tests."""
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    test_session_factory = async_sessionmaker(test_engine, expire_on_commit=False)

    async def get_test_session():
        async with test_session_factory() as session:
            yield session

    @asynccontextmanager
    async def test_lifespan(_application: FastAPI) -> AsyncGenerator[None, None]:
        async with test_engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        yield
        await test_engine.dispose()

    monkeypatch.setattr(api_module.app.router, "lifespan_context", test_lifespan)
    api_module.app.dependency_overrides[get_async_session] = get_test_session
    with TestClient(api_module.app) as client:
        yield cast(httpx.Client, client)
    api_module.app.dependency_overrides.clear()


def test_register_login_upload_feed_and_delete(
    isolated_api_client: httpx.Client,
    monkeypatch: pytest.MonkeyPatch,
):
    """Exercise frontend API calls through real auth and post routes."""
    email = "frontend-integration@example.com"
    password = "integration-password-123"

    def fake_image_upload(**_kwargs: Any) -> Any:
        return SimpleNamespace(
            url="https://images.example.test/integration.jpg",
            name="integration.jpg",
        )

    monkeypatch.setattr(api_module.image_kit.files, "upload", fake_image_upload)

    def api_call(method: str, url: str, **kwargs: Any) -> requests.Response:
        kwargs.pop("timeout", None)
        client = cast(Any, isolated_api_client)
        response: httpx.Response = client.request(method, urlparse(url).path, **kwargs)
        return cast(requests.Response, response)

    monkeypatch.setattr(frontend.requests, "request", api_call)

    registered = frontend.api_request(
        "POST", "/auth/register", json={"email": email, "password": password}
    )
    assert registered is not None and registered.status_code == 201

    logged_in = frontend.api_request(
        "POST",
        "/auth/jwt/login",
        data={"username": email, "password": password},
    )
    assert logged_in is not None and logged_in.status_code == 200
    token = logged_in.json()["access_token"]

    empty_feed = frontend.api_request("GET", "/feed", token=token)
    assert empty_feed is not None and empty_feed.json() == {"posts": []}

    uploaded = frontend.api_request(
        "POST",
        "/upload",
        token=token,
        data={"caption": "Integration test post"},
        files={"file": ("integration.jpg", b"image-bytes", "image/jpeg")},
    )
    assert uploaded is not None and uploaded.status_code == 200
    post_id = uploaded.json()["id"]

    populated_feed = frontend.api_request("GET", "/feed", token=token)
    assert populated_feed is not None and populated_feed.status_code == 200
    post = populated_feed.json()["posts"][0]
    assert post["id"] == post_id
    assert post["caption"] == "Integration test post"
    assert post["is_owner"] is True

    deleted = frontend.api_request("DELETE", f"/posts/{post_id}", token=token)
    assert deleted is not None and deleted.status_code == 200
    assert deleted.json()["success"] is True

    final_feed = frontend.api_request("GET", "/feed", token=token)
    assert final_feed is not None and final_feed.json() == {"posts": []}
