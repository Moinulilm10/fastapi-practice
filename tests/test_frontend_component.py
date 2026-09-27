"""Streamlit component tests for the frontend views and interactions."""

from pathlib import Path
from typing import Any, cast
from unittest.mock import Mock
from urllib.parse import urlparse

import pytest
import requests
from streamlit.testing.v1 import AppTest

FRONTEND_PATH = Path(__file__).parents[1] / "frontend.py"


def make_response(status_code: int, payload: Any) -> requests.Response:
    """Build a requests response mock for component interactions."""
    response = Mock(spec=requests.Response)
    response.status_code = status_code
    response.json.return_value = payload
    return cast(requests.Response, response)


def test_sign_in_renders_authenticated_feed(monkeypatch: pytest.MonkeyPatch):
    """Submit the sign-in form and render the authenticated feed state."""

    def fake_request(_method: str, url: str, **_kwargs: Any) -> requests.Response:
        if urlparse(url).path == "/auth/jwt/login":
            return make_response(200, {"access_token": "component-token"})
        return make_response(200, {"posts": []})

    monkeypatch.setattr(requests, "request", fake_request)
    app_test = AppTest.from_file(str(FRONTEND_PATH)).run()
    app_test.text_input[0].set_value("person@example.com")
    app_test.text_input[1].set_value("example-password")
    app_test.button[0].click().run()

    assert not app_test.exception
    assert app_test.session_state["access_token"] == "component-token"
    assert app_test.session_state["user_email"] == "person@example.com"
    assert "The feed" in [heading.value for heading in app_test.title]


def test_registration_signs_user_in(monkeypatch: pytest.MonkeyPatch):
    """Submit registration and verify the frontend automatically signs in."""

    def fake_request(_method: str, url: str, **_kwargs: Any) -> requests.Response:
        path = urlparse(url).path
        if path == "/auth/register":
            return make_response(201, {"id": "new-user"})
        if path == "/auth/jwt/login":
            return make_response(200, {"access_token": "registered-token"})
        return make_response(200, {"posts": []})

    monkeypatch.setattr(requests, "request", fake_request)
    app_test = AppTest.from_file(str(FRONTEND_PATH)).run()
    app_test.text_input[2].set_value("new-person@example.com")
    app_test.text_input[3].set_value("registration-password")
    app_test.button[1].click().run()

    assert not app_test.exception
    assert app_test.session_state["access_token"] == "registered-token"
    assert app_test.session_state["user_email"] == "new-person@example.com"


def test_create_post_page_renders_upload_controls(monkeypatch: pytest.MonkeyPatch):
    """Render the authenticated post composer and its expected controls."""

    def fake_request(_method: str, _url: str, **_kwargs: Any) -> requests.Response:
        return make_response(200, {"posts": []})

    monkeypatch.setattr(requests, "request", fake_request)
    app_test = AppTest.from_file(str(FRONTEND_PATH))
    app_test.session_state["access_token"] = "component-token"
    app_test.session_state["user_email"] = "person@example.com"
    app_test.session_state["page"] = "Create post"
    app_test.run()

    assert not app_test.exception
    assert "Share a moment" in [heading.value for heading in app_test.title]
    assert [uploader.label for uploader in app_test.file_uploader] == ["Photo or video"]
    assert [area.label for area in app_test.text_area] == ["Caption"]


def test_delete_button_removes_owned_post(monkeypatch: pytest.MonkeyPatch):
    """Render an owned post and verify deletion refreshes the feed."""
    post: dict[str, Any] = {
        "id": "post-123",
        "email": "person@example.com",
        "created_at": "2026-09-28T10:00:00+00:00",
        "file_type": "video",
        "url": "https://media.example.test/post.mp4",
        "file_name": "post.mp4",
        "caption": "A test post",
        "is_owner": True,
    }
    deleted = False

    def fake_request(method: str, url: str, **_kwargs: Any) -> requests.Response:
        nonlocal deleted
        path = urlparse(url).path
        if method == "DELETE" and path == "/posts/post-123":
            deleted = True
            return make_response(200, {"success": True, "message": "Deleted"})
        if path == "/feed":
            return make_response(200, {"posts": [] if deleted else [post]})
        return make_response(200, {})

    monkeypatch.setattr(requests, "request", fake_request)
    app_test = AppTest.from_file(str(FRONTEND_PATH))
    app_test.session_state["access_token"] = "component-token"
    app_test.session_state["user_email"] = "person@example.com"
    app_test.session_state["page"] = "Feed"
    app_test.run()
    delete_button = next(
        button for button in app_test.button if button.label == "Delete"
    )
    delete_button.click().run()

    assert not app_test.exception
    assert deleted
    assert any("Nothing here yet" in item.value for item in app_test.subheader)
