"""FastAPI routes and application setup."""

import os
import shutil
import tempfile
import uuid
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db import Post, create_db_and_tables, get_async_session
from app.images import image_kit
from app.schemas import DeleteResponse


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Create database tables when the application starts."""
    await create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)


@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    caption: str = Form(""),
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, object]:
    """Upload a file to ImageKit and save its metadata."""
    original_file_name = file.filename or "uploaded-file"

    temp_file_path: str | None = None

    try:
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=os.path.splitext(original_file_name)[1]
        ) as temp_file:
            temp_file_path = temp_file.name
            shutil.copyfileobj(file.file, temp_file)

        with open(temp_file_path, "rb") as upload_file_handle:
            upload_result = image_kit.files.upload(
                file=upload_file_handle,
                file_name=original_file_name,
                use_unique_file_name=True,
                tags=["backend-upload"],
            )

        url = upload_result.url
        file_name = upload_result.name
        if not url or not file_name:
            raise HTTPException(
                status_code=502,
                detail="ImageKit returned incomplete upload metadata",
            )

        file_type = (
            "video"
            if file.content_type and file.content_type.startswith("video/")
            else "image"
        )
        post = Post(
            caption=caption,
            url=url,
            file_type=file_type,
            file_name=file_name,
        )
        session.add(post)
        await session.commit()
        await session.refresh(post)
        return {
            "id": str(post.id),
            "caption": post.caption,
            "url": post.url,
            "file_type": post.file_type,
            "file_name": post.file_name,
            "created_at": str(post.created_at),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"File upload failed: {str(e)}",
        ) from e
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        file.file.close()


@app.get("/feed")
async def get_feed(
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, list[dict[str, Any]]]:
    """Retrieve all posts from the database."""
    result = await session.execute(select(Post).order_by(Post.created_at.desc()))
    posts = result.scalars().all()

    post_data: list[dict[str, Any]] = []

    for post in posts:
        post_data.append(
            {
                "id": str(post.id),
                "caption": post.caption,
                "url": post.url,
                "file_type": post.file_type,
                "file_name": post.file_name,
                "created_at": post.created_at.isoformat(),
            }
        )

    return {"posts": post_data}


@app.delete("/posts/{post_id}")
async def delete_post(
    post_id: str, session: AsyncSession = Depends(get_async_session)
) -> DeleteResponse:
    """Delete a post by its ID."""
    try:
        post_uuid = uuid.UUID(post_id)

        result = await session.execute(select(Post).where(Post.id == post_uuid))
        post = result.scalars().first()

        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        await session.delete(post)
        await session.commit()

        return DeleteResponse(success=True, message="Post deleted successfully")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
