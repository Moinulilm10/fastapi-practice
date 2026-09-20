"""Pydantic schemas used by the API."""

import uuid

from fastapi_users import schemas
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


class UserRead(schemas.BaseUser[uuid.UUID]):
    """Public user fields returned by the authentication API."""


class UserCreate(schemas.BaseUserCreate):
    """Fields accepted when registering a new user."""


class UserUpdate(schemas.BaseUserUpdate):
    """Fields accepted when updating an existing user."""
