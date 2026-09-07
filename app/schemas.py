"""Pydantic schemas used by the API."""

from pydantic import BaseModel


class PostCreate(BaseModel):
    """Schema for creating a new post."""

    title: str
    content: str


class PostResponse(BaseModel):
    """Schema for returning post data."""

    title: str
    content: str


class ApiResponse(BaseModel):
    """Generic API response schema."""

    status_code: int
    message: str
    data: PostResponse | dict[int, PostResponse] | list[PostResponse] | None = None


class DeleteResponse(BaseModel):
    """Response returned after deleting a post."""

    success: bool
    message: str
