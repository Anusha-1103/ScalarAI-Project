"""add Supabase identity mapping

Revision ID: 9f44e3a918a1
Revises: da26b8757ff7
Create Date: 2026-08-14 02:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "9f44e3a918a1"
down_revision: str | Sequence[str] | None = "da26b8757ff7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("Account", sa.Column("authUserId", sa.String(length=36), nullable=True))
    op.create_index("idx_Account_authUserId", "Account", ["authUserId"], unique=True)


def downgrade() -> None:
    op.drop_index("idx_Account_authUserId", table_name="Account")
    op.drop_column("Account", "authUserId")
