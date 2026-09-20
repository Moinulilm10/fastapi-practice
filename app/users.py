"""Authentication configuration and user lifecycle hooks."""

import os
import uuid
from collections.abc import AsyncGenerator
from typing import Optional
from uuid import UUID

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase

from app.db import User, get_user_db

SECRET: str = os.getenv("SECRET") or ""
if not SECRET:
    raise RuntimeError("SECRET must be set for authentication")


class UserManager(UUIDIDMixin, BaseUserManager[User, UUID]):
    """Manage authentication lifecycle events for application users."""

    reset_password_token = SECRET
    verification_token_secret = SECRET

    async def on_after_register(self, user: User, request: Optional[Request] = None):
        """Log a user's successful registration."""
        print(f"User {user.id} has registered")

    async def on_after_forgot_password(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        """Log that a password reset was requested."""
        print(f"User {user.id} has forgot their password. Reset token: {token}")

    async def on_after_request_verify(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        """Log that email verification was requested."""
        print(f"Verification requested for user {user.id}. Verification token: {token}")


async def get_user_manager(
    user_db: SQLAlchemyUserDatabase[User, UUID] = Depends(get_user_db),
) -> AsyncGenerator[UserManager, None]:
    """Yield a user manager for the current database session."""
    yield UserManager(user_db)


bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")


def get_jwt_strategy() -> JWTStrategy[User, UUID]:
    """Create the JWT authentication strategy."""
    return JWTStrategy(secret=SECRET, lifetime_seconds=3600)


auth_backend: AuthenticationBackend[User, UUID] = AuthenticationBackend(
    name="jwt", transport=bearer_transport, get_strategy=get_jwt_strategy
)

fastapi_users = FastAPIUsers[User, uuid.UUID](get_user_manager, [auth_backend])
current_active_user = fastapi_users.current_user(active=True)
