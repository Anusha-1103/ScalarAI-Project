"""add workspace query indexes

Revision ID: b781c6f4a2d9
Revises: 38b721d4f0de
Create Date: 2026-08-14 12:00:00
"""

from collections.abc import Sequence

from alembic import op

revision: str = "b781c6f4a2d9"
down_revision: str | Sequence[str] | None = "38b721d4f0de"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "idx_meeting_owner_active_date",
        "Meeting",
        ["ownerAccountId", "deletedAtUtc", "meetingAtUtc"],
    )
    op.create_index(
        "idx_action_item_meeting_completion",
        "ActionItem",
        ["meetingId", "isCompleted"],
    )


def downgrade() -> None:
    op.drop_index("idx_action_item_meeting_completion", table_name="ActionItem")
    op.drop_index("idx_meeting_owner_active_date", table_name="Meeting")
