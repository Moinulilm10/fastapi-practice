"""Unit tests for Streamlit frontend helpers."""

from typing import Any, cast
from unittest.mock import Mock

import pytest
import requests

import frontend


def make_response(status_code: int, payload: Any) -> requests.Response:
    """Build a requests response mock for frontend helper tests."""
    response = Mock(spec=requests.Response)
    response.status_code = status_code
    response.json.return_value = payload
    return cast(requests.Response, response)


def test_response_detail_handles_json_and_non_json_errors():
    """Format API JSON errors and non-JSON fallbacks."""
    json_response = make_response(400, {"detail": "LOGIN_BAD_CREDENTIALS"})
    text_response = Mock(spec=requests.Response)
    text_response.status_code = 502
    text_response.json.side_effect = ValueError("not JSON")

    assert frontend.response_detail(json_response) == "LOGIN_BAD_CREDENTIALS"
    assert frontend.response_detail(text_response) == "Request failed with HTTP 502."


def test_api_request_adds_bearer_token(monkeypatch: pytest.MonkeyPatch):
    """Attach bearer authorization and preserve request parameters."""
    captured: dict[str, Any] = {}

    def fake_request(method: str, url: str, **kwargs: Any) -> requests.Response:
        captured.update(method=method, url=url, **kwargs)
        return make_response(200, {"ok": True})

    monkeypatch.setattr(frontend.requests, "request", fake_request)
    response = frontend.api_request(
        "GET", "/feed", token="test-token", params={"limit": 5}
    )

    assert response is not None and response.status_code == 200
    assert captured["headers"]["Authorization"] == "Bearer test-token"
    assert captured["url"] == f"{frontend.API_BASE_URL}/feed"
    assert captured["params"] == {"limit": 5}