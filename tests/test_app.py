"""Tests for the FastAPI post endpoints."""

import importlib
from copy import deepcopy

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.schemas import ApiResponse, PostCreate, PostResponse

app_module = importlib.import_module("app.app")
client = TestClient(app_module.app)


@pytest.fixture(autouse=True)
def reset_posts():
    original_posts = deepcopy(app_module.text_posts)
    yield
    app_module.text_posts.clear()
    app_module.text_posts.update(original_posts)


def test_get_all_posts_returns_all_posts():
    response = client.get("/posts")

    assert response.status_code == 200
    body = response.json()
    assert body["status_code"] == 200
    assert body["message"] == "Posts retrieved successfully"
    assert len(body["data"]) == 10
    assert body["data"]["1"]["title"] == "Getting Started with FastAPI"


def test_get_all_posts_with_limit():
    response = client.get("/posts", params={"limit": 2})

    assert response.status_code == 200
    assert len(response.json()["data"]) == 2


def test_get_all_posts_with_zero_limit_returns_empty_data():
    response = client.get("/posts", params={"limit": 0})

    assert response.status_code == 200
    assert response.json()["data"] == []


def test_get_all_posts_rejects_negative_limit():
    response = client.get("/posts", params={"limit": -1})

    assert response.status_code == 422


def test_get_all_posts_rejects_non_integer_limit():
    response = client.get("/posts", params={"limit": "invalid"})

    assert response.status_code == 422


def test_get_post_by_id_returns_post():
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
    response = client.get("/posts/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Post not found"}


def test_get_post_by_id_rejects_non_integer_id():
    response = client.get("/posts/not-an-id")

    assert response.status_code == 422


def test_create_post_returns_created_post():
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
def test_create_post_validates_request_body(payload):
    response = client.post("/posts", json=payload)

    assert response.status_code == 422


def test_update_post_replaces_post_data():
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
    response = client.put(
        "/posts/999",
        json={"title": "Updated title", "content": "Updated content"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Post not found"}


def test_update_post_validates_request_body():
    response = client.put("/posts/2", json={"title": "Only title"})

    assert response.status_code == 422


def test_delete_post_removes_post():
    response = client.delete("/posts/2")

    assert response.status_code == 200
    assert response.json() == {
        "status_code": 200,
        "message": "Post deleted successfully",
        "data": None,
    }
    assert 2 not in app_module.text_posts


def test_delete_post_returns_not_found():
    response = client.delete("/posts/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Post not found"}


def test_partial_update_post_changes_both_fields():
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
def test_partial_update_requires_both_fields_with_current_schema(payload):
    response = client.patch("/posts/2", json=payload)

    assert response.status_code == 422


def test_partial_update_returns_not_found():
    response = client.patch(
        "/posts/999",
        json={"title": "Patched title", "content": "Patched content"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Post not found"}


def test_post_create_schema_accepts_valid_data():
    post = PostCreate(title="Title", content="Content")

    assert post.title == "Title"
    assert post.content == "Content"


@pytest.mark.parametrize(
    "model",
    [PostCreate, PostResponse],
)
def test_post_schemas_reject_missing_fields(model):
    with pytest.raises(ValidationError):
        model(title="Only title")


def test_api_response_accepts_single_post_object():
    response = ApiResponse(
        status_code=200,
        message="Success",
        data=PostResponse(title="Title", content="Content"),
    )

    assert response.data.title == "Title"


def test_api_response_accepts_post_dictionary_with_integer_ids():
    response = ApiResponse(
        status_code=200,
        message="Success",
        data={1: PostResponse(title="Title", content="Content")},
    )

    assert response.data[1].content == "Content"


def test_api_response_accepts_null_data():
    response = ApiResponse(status_code=200, message="Deleted", data=None)

    assert response.data is None
