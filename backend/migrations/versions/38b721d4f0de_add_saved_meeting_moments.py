"""add saved meeting moments

Revision ID: 38b721d4f0de
Revises: 9f44e3a918a1
Create Date: 2026-08-14 02:20:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "38b721d4f0de"
down_revision: str | Sequence[str] | None = "9f44e3a918a1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "MeetingMoment",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("meetingId", sa.String(length=36), nullable=False),
        sa.Column("segmentId", sa.String(length=36), nullable=False),
        sa.Column("authorAccountId", sa.String(length=36), nullable=False),
        sa.Column("kind", sa.String(length=20), nullable=False),
        sa.Column("note", sa.String(length=500), nullable=True),
        sa.Column("createdAtUtc", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updatedAtUtc", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "kind IN ('important', 'positive', 'concern')",
            name=op.f("ck_MeetingMoment_moment_kind_valid"),
        ),
        sa.ForeignKeyConstraint(["authorAccountId"], ["Account.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["meetingId"], ["Meeting.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["segmentId"], ["TranscriptSegment.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_MeetingMoment_meetingId", "MeetingMoment", ["meetingId"])
    op.create_index("idx_MeetingMoment_segmentId", "MeetingMoment", ["segmentId"])
    op.create_index("idx_MeetingMoment_authorAccountId", "MeetingMoment", ["authorAccountId"])


def downgrade() -> None:
    op.drop_table("MeetingMoment")
