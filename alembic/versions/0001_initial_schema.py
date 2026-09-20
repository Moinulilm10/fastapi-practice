# pyright: reportAttributeAccessIssue=false
# pylint: disable=invalid-name

"""Create users and posts tables."""

from collections.abc import Sequence
from typing import Any, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0001_initial_schema"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None
create_table: Any = getattr(op, "create_table")
create_index: Any = getattr(op, "create_index")
drop_table: Any = getattr(op, "drop_table")
drop_index: Any = getattr(op, "drop_index")


def upgrade() -> None:
    """Create the initial application tables."""
    create_table(
        "user",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("hashed_password", sa.String(length=1024), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_superuser", sa.Boolean(), nullable=False),
        sa.Column("is_verified", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    create_index("ix_user_email", "user", ["email"], unique=True)
    create_table(
        "posts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("caption", sa.Text(), nullable=True),
        sa.Column("url", sa.String(), nullable=False),
        sa.Column("file_type", sa.String(), nullable=False),
        sa.Column("file_name", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Drop the initial application tables."""
    drop_table("posts")
    drop_index("ix_user_email", table_name="user")
    drop_table("user")
