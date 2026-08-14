"""add persisted meeting tags

Revision ID: e4a3d91c72be
Revises: c24e8b31f570
Create Date: 2026-08-14 11:45:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e4a3d91c72be"
down_revision: str | Sequence[str] | None = "c24e8b31f570"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "Tag",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("ownerAccountId", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("normalizedName", sa.String(length=50), nullable=False),
        sa.Column("createdAtUtc", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updatedAtUtc", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["ownerAccountId"], ["Account.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ownerAccountId", "normalizedName"),
    )
    op.create_index("idx_Tag_ownerAccountId", "Tag", ["ownerAccountId"])
    op.create_index("idx_tag_owner_name", "Tag", ["ownerAccountId", "normalizedName"])
    op.create_table(
        "MeetingTag",
        sa.Column("meetingId", sa.String(length=36), nullable=False),
        sa.Column("tagId", sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(["meetingId"], ["Meeting.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tagId"], ["Tag.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("meetingId", "tagId"),
    )
    op.create_index("idx_MeetingTag_tagId", "MeetingTag", ["tagId"])


def downgrade() -> None:
    op.drop_table("MeetingTag")
    op.drop_table("Tag")
