"""Database models and asynchronous database helpers."""

import os
import uuid
from collections.abc import AsyncGenerator
from datetime import datetime, timezone

from dotenv import load_dotenv
from sqlalchemy import Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL must be set to a PostgreSQL connection URL")


# SQLAlchemy declarative classes do not need public methods.
# pylint: disable=too-few-public-methods
class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""


class Post(Base):
    """Database model for uploaded posts."""

    __tablename__ = "posts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    caption = Column(Text)
    url = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    file_name = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


engine = create_async_engine(DATABASE_URL)
async_session_maker = async_sessionmaker(
    engine,
    expire_on_commit=False,
)


async def create_db_and_tables():
    """Create all database tables if they do not already exist."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an asynchronous database session."""
    async with async_session_maker() as session:
        yield session
