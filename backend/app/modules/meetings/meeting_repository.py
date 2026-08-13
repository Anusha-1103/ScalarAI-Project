from datetime import datetime

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.meetings.meeting_models import (
    Account,
    ActionItem,
    Meeting,
    MeetingParticipant,
    Participant,
    TranscriptSegment,
)


class MeetingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def _with_detail() -> tuple:
        return (
            selectinload(Meeting.participants).selectinload(MeetingParticipant.participant),
            selectinload(Meeting.transcript_segments),
            selectinload(Meeting.summary),
            selectinload(Meeting.chapters),
            selectinload(Meeting.action_items),
        )

    async def list_meetings(
        self,
        *,
        search: str | None,
        participant: str | None,
        date_from: datetime | None,
        date_to: datetime | None,
        sort_order: str,
        page: int,
        limit: int,
    ) -> tuple[list[Meeting], int]:
        query: Select[tuple[Meeting]] = select(Meeting).where(Meeting.deleted_at_utc.is_(None))

        if search or participant:
            query = (
                query.join(MeetingParticipant, MeetingParticipant.meeting_id == Meeting.id)
                .join(Participant, Participant.id == MeetingParticipant.participant_id)
                .distinct()
            )
        if search:
            pattern = f"%{search.strip()}%"
            query = query.where(or_(Meeting.title.ilike(pattern), Participant.name.ilike(pattern)))
        if participant:
            query = query.where(Participant.name.ilike(f"%{participant.strip()}%"))
        if date_from:
            query = query.where(Meeting.meeting_at_utc >= date_from)
        if date_to:
            query = query.where(Meeting.meeting_at_utc <= date_to)

        count_query = select(func.count()).select_from(query.order_by(None).subquery())
        total = int((await self.session.scalar(count_query)) or 0)
        ordering = (
            Meeting.meeting_at_utc.asc() if sort_order == "asc" else Meeting.meeting_at_utc.desc()
        )
        result = await self.session.scalars(
            query.options(*self._with_detail())
            .order_by(ordering)
            .offset((page - 1) * limit)
            .limit(limit)
        )
        return list(result.unique().all()), total

    async def get_meeting(self, meeting_id: str) -> Meeting | None:
        return await self.session.scalar(
            select(Meeting)
            .where(Meeting.id == meeting_id, Meeting.deleted_at_utc.is_(None))
            .options(*self._with_detail())
        )

    async def find_participant(self, name: str) -> Participant | None:
        return await self.session.scalar(
            select(Participant).where(func.lower(Participant.name) == name.strip().lower())
        )

    async def get_default_account(self) -> Account | None:
        return await self.session.scalar(select(Account).order_by(Account.created_at_utc).limit(1))

    async def search_transcripts(
        self, query_text: str, limit: int
    ) -> list[tuple[Meeting, TranscriptSegment]]:
        pattern = f"%{query_text.strip()}%"
        result = await self.session.execute(
            select(Meeting, TranscriptSegment)
            .join(TranscriptSegment, TranscriptSegment.meeting_id == Meeting.id)
            .where(Meeting.deleted_at_utc.is_(None), TranscriptSegment.text.ilike(pattern))
            .order_by(Meeting.meeting_at_utc.desc(), TranscriptSegment.sequence_number)
            .limit(limit)
        )
        return list(result.all())

    async def get_action_item(self, action_item_id: str) -> ActionItem | None:
        return await self.session.get(ActionItem, action_item_id)

    def add(self, entity: object) -> None:
        self.session.add(entity)

    async def flush(self) -> None:
        await self.session.flush()

    async def commit(self) -> None:
        await self.session.commit()

    async def delete(self, entity: object) -> None:
        await self.session.delete(entity)
