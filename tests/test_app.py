"""Tests for the FastAPI post endpoints."""

import asyncio
import importlib
from copy import deepcopy
from typing import Any, cast

import httpx
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import text

from app.db.db import engine
from app.schemas import ApiResponse, PostCreate, PostResponse

app_module = importlib.import_module("app.app")
client = cast(httpx.Client, TestClient(app_module.app))


@pytest.fixture(autouse=True)
def reset_posts():
    """Restore the in-memory posts after each test."""
    original_posts = deepcopy(app_module.text_posts)
    yield
    app_module.text_posts.clear()
    app_module.text_posts.update(original_posts)


def test_get_all_posts_returns_all_posts():
    """Return all available posts from the collection endpoint."""
    response = client.get("/posts")

    assert response.status_code == 200
    body = response.json()
    assert body["status_code"] == 200
    assert body["message"] == "Posts retrieved successfully"
    assert len(body["data"]) == 10
    assert body["data"]["1"]["title"] == "Getting Started with FastAPI"


def test_get_all_posts_with_limit():
    """Limit the number of posts returned by the collection endpoint."""
    response = client.get("/posts", params={"limit": 2})

    assert response.status_code == 200
    assert len(response.json()["data"]) == 2


def test_get_all_posts_with_zero_limit_returns_empty_data():
    """Return an empty collection when the limit is zero."""
    response = client.get("/posts", params={"limit": 0})

    assert response.status_code == 200
    assert response.json()["data"] == []


def test_get_all_posts_rejects_negative_limit():
    """Reject negative collection limits."""
    response = client.get("/posts", params={"limit": -1})

    assert response.status_code == 422


def test_get_all_posts_rejects_non_integer_limit():
    """Reject non-integer collection limits."""
    response = client.get("/posts", params={"limit": "invalid"})

    assert response.status_code == 422


def test_get_post_by_id_returns_post():
    """Return the requested post when its identifier exists."""
    response = client.get("/posts/2")

    assert response.status_code == 200
    assert response.json() == {
        "status_code": 200,
        "message": "Post retrieved successfully",
        "data": {
            "title": "Why Type Hints Matter",
            "content": "Type hints make Python code easier to understand, validate, and maintain.",
        },
    }


def test_get_post_by_id_returns_not_found():
    """Return not found for an unknown post identifier."""
    response = client.get("/posts/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Post not found"}


def test_get_post_by_id_rejects_non_integer_id():
    """Reject a non-integer post identifier."""
    response = client.get("/posts/not-an-id")

    assert response.status_code == 422


def test_create_post_returns_created_post():
    """Create a post and return its data."""
    response = client.post(
        "/posts",
        json={"title": "New title", "content": "New content"},
    )

    assert response.status_code == 201
    assert response.json() == {
        "status_code": 201,
        "message": "Post created successfully",
        "data": {"title": "New title", "content": "New content"},
    }
    assert app_module.text_posts[11] == {
        "title": "New title",
        "content": "New content",
    }


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"title": "Only title"},
        {"content": "Only content"},
        {"title": None, "content": "Content"},
        {"title": "Title", "content": None},
    ],
)
def test_create_post_validates_request_body(payload: dict[str, Any]):
    """Reject invalid create-post request bodies."""
    response = client.post("/posts", json=payload)

    assert response.status_code == 422


def test_update_post_replaces_post_data():
    """Replace an existing post with the submitted data."""
    response = client.put(
        "/posts/2",
        json={"title": "Updated title", "content": "Updated content"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "status_code": 200,
        "message": "Post updated successfully",
        "data": {"title": "Updated title", "content": "Updated content"},
    }
    assert app_module.text_posts[2] == {
        "title": "Updated title",
        "content": "Updated content",
    }


def test_update_post_returns_not_found():
    """Return not found when updating an unknown post."""
    response = client.put(
        "/posts/999",
        json={"title": "Updated title", "content": "Updated content"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Post not found"}


def test_update_post_validates_request_body():
    """Reject an incomplete update-post request body."""
    response = client.put("/posts/2", json={"title": "Only title"})

    assert response.status_code == 422


def test_delete_post_removes_post():
    """Delete an existing post from the collection."""
    response = client.delete("/posts/2")

    assert response.status_code == 200
    assert response.json() == {
        "status_code": 200,
        "message": "Post deleted successfully",
        "data": None,
    }
    assert 2 not in app_module.text_posts


def test_delete_post_returns_not_found():
    """Return not found when deleting an unknown post."""
    response = client.delete("/posts/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Post not found"}


def test_partial_update_post_changes_both_fields():
    """Update both fields of an existing post."""
    response = client.patch(
        "/posts/2",
        json={"title": "Patched title", "content": "Patched content"},
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Post partially updated successfully"
    assert response.json()["data"] == {
        "title": "Patched title",
        "content": "Patched content",
    }


@pytest.mark.parametrize(
    "payload",
    [{}, {"title": "Only title"}, {"content": "Only content"}],
)
def test_partial_update_requires_both_fields_with_current_schema(
    payload: dict[str, str],
):
    """Reject partial updates missing fields required by the schema."""
    response = client.patch("/posts/2", json=payload)

    assert response.status_code == 422


def test_partial_update_returns_not_found():
    """Return not found when partially updating an unknown post."""
    response = client.patch(
        "/posts/999",
        json={"title": "Patched title", "content": "Patched content"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Post not found"}


def test_post_create_schema_accepts_valid_data():
    """Accept a valid post creation schema."""
    post = PostCreate(title="Title", content="Content")

    assert post.title == "Title"
    assert post.content == "Content"


@pytest.mark.parametrize(
    "model",
    [PostCreate, PostResponse],
)
def test_post_schemas_reject_missing_fields(
    model: type[PostCreate] | type[PostResponse],
):
    """Reject schema instances with required fields missing."""
    with pytest.raises(ValidationError):
        model.model_validate({"title": "Only title"})


def test_api_response_accepts_single_post_object():
    """Accept an API response containing one post object."""
    response = ApiResponse(
        status_code=200,
        message="Success",
        data=PostResponse(title="Title", content="Content"),
    )

    assert isinstance(response.data, PostResponse)
    assert response.data.title == "Title"


def test_api_response_accepts_post_dictionary_with_integer_ids():
    """Accept an API response containing posts keyed by integer IDs."""
    response = ApiResponse(
        status_code=200,
        message="Success",
        data={1: PostResponse(title="Title", content="Content")},
    )

    assert isinstance(response.data, dict)
    post = response.data.get(1)
    assert isinstance(post, PostResponse)
    assert post.content == "Content"


def test_api_response_accepts_null_data():
    """Accept an API response with no data payload."""
    response = ApiResponse(status_code=200, message="Deleted", data=None)

    assert response.data is None


def test_database_connection_succeeds():
    """Verify that the configured PostgreSQL database accepts a query."""

    async def check_connection() -> int:
        async with engine.connect() as connection:
            result = await connection.execute(text("SELECT 1"))
            return int(result.scalar_one())

    assert asyncio.run(check_connection()) == 1
