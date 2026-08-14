"""remove automatic samples from personal accounts

Revision ID: c24e8b31f570
Revises: b781c6f4a2d9
Create Date: 2026-08-14 13:00:00
"""

from collections.abc import Sequence

from alembic import op

revision: str = "c24e8b31f570"
down_revision: str | Sequence[str] | None = "b781c6f4a2d9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        DELETE FROM "Meeting"
        WHERE "sourceType" = 'demo'
          AND "ownerAccountId" IN (
            SELECT id FROM "Account" WHERE lower(email) <> 'demo@echonote.app'
          )
        """
    )
    op.execute(
        """
        DELETE FROM "Participant"
        WHERE NOT EXISTS (
          SELECT 1 FROM "MeetingParticipant"
          WHERE "MeetingParticipant"."participantId" = "Participant".id
        )
        """
    )


def downgrade() -> None:
    # Removed sample records can be restored explicitly from the product empty state.
    pass
