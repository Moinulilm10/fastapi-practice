"""Pydantic schemas used by the API."""

from pydantic import BaseModel


class PostCreate(BaseModel):
    title: str
    content: str


class PostResponse(BaseModel):
    title: str
    content: str


class ApiResponse(BaseModel):
    status_code: int
    message: str
    data: PostResponse | dict[int, PostResponse] | list[PostResponse] | None = None
