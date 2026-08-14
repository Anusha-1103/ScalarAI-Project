from datetime import datetime

from sqlalchemy import Select, case, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import noload, selectinload

from app.common.auth import CurrentPrincipal
from app.common.settings_config import get_settings
from app.modules.meetings.meeting_models import (
    Account,
    ActionItem,
    Meeting,
    MeetingMoment,
    MeetingParticipant,
    MeetingSummary,
    Participant,
    TranscriptSegment,
)


class MeetingRepository:
    def __init__(self, session: AsyncSession, principal: CurrentPrincipal | None = None) -> None:
        self.session = session
        self.principal = principal
        self.account_id: str | None = None

    async def resolve_account(self) -> Account:
        if self.account_id:
            account = await self.session.get(Account, self.account_id)
            if account:
                return account
        account = None
        created = False
        if self.principal and self.principal.auth_user_id:
            account = await self.session.scalar(
                select(Account).where(Account.auth_user_id == self.principal.auth_user_id)
            )
            if not account:
                account = Account(
                    auth_user_id=self.principal.auth_user_id,
                    display_name=self.principal.display_name,
                    email=self.principal.email,
                )
                self.session.add(account)
                try:
                    await self.session.commit()
                    created = True
                except IntegrityError:
                    await self.session.rollback()
                    account = await self.session.scalar(
                        select(Account).where(Account.auth_user_id == self.principal.auth_user_id)
                    )
            if not account:
                raise RuntimeError("Authenticated account could not be resolved")
        if not account:
            account = await self.session.scalar(
                select(Account).order_by(Account.created_at_utc).limit(1)
            )
        if not account:
            raise RuntimeError("No application account is configured")
        self.account_id = account.id
        settings = get_settings()
        if (
            created
            and settings.seed_demo_account
            and account.email.casefold() == settings.demo_account_email.casefold()
        ):
            from app.seed_data import provision_account_workspace

            await provision_account_workspace(self.session, account)
        return account

    async def _owner_id(self) -> str:
        return (await self.resolve_account()).id

    @staticmethod
    def _with_detail() -> tuple:
        return (
            selectinload(Meeting.participants).selectinload(MeetingParticipant.participant),
            selectinload(Meeting.transcript_segments),
            selectinload(Meeting.summary),
            selectinload(Meeting.chapters),
            selectinload(Meeting.action_items),
            selectinload(Meeting.moments),
        )

    @staticmethod
    def _with_list() -> tuple:
        return (
            selectinload(Meeting.participants).selectinload(MeetingParticipant.participant),
            selectinload(Meeting.summary).noload(MeetingSummary.key_points),
            selectinload(Meeting.action_items),
            noload(Meeting.transcript_segments),
            noload(Meeting.chapters),
            noload(Meeting.moments),
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
        owner_id = await self._owner_id()
        query: Select[tuple[Meeting]] = select(Meeting).where(
            Meeting.deleted_at_utc.is_(None), Meeting.owner_account_id == owner_id
        )

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
            query.options(*self._with_list())
            .order_by(ordering)
            .offset((page - 1) * limit)
            .limit(limit)
        )
        return list(result.unique().all()), total

    async def get_dashboard_meetings(self, limit: int) -> list[Meeting]:
        owner_id = await self._owner_id()
        result = await self.session.scalars(
            select(Meeting)
            .where(Meeting.deleted_at_utc.is_(None), Meeting.owner_account_id == owner_id)
            .options(*self._with_list())
            .order_by(Meeting.meeting_at_utc.desc())
            .limit(limit)
        )
        return list(result.unique().all())

    async def get_meeting(self, meeting_id: str) -> Meeting | None:
        owner_id = await self._owner_id()
        return await self.session.scalar(
            select(Meeting)
            .where(
                Meeting.id == meeting_id,
                Meeting.deleted_at_utc.is_(None),
                Meeting.owner_account_id == owner_id,
            )
            .options(*self._with_detail())
        )

    async def find_participant(self, name: str) -> Participant | None:
        owner_id = await self._owner_id()
        return await self.session.scalar(
            select(Participant)
            .join(MeetingParticipant, MeetingParticipant.participant_id == Participant.id)
            .join(Meeting, Meeting.id == MeetingParticipant.meeting_id)
            .where(
                func.lower(Participant.name) == name.strip().lower(),
                Meeting.owner_account_id == owner_id,
            )
            .limit(1)
        )

    async def get_default_account(self) -> Account | None:
        return await self.resolve_account()

    async def search_transcripts(
        self, query_terms: list[str], limit: int
    ) -> list[tuple[Meeting, TranscriptSegment]]:
        patterns = [f"%{term}%" for term in query_terms]
        relevance = sum(
            (case((TranscriptSegment.text.ilike(pattern), 1), else_=0) for pattern in patterns),
            start=case((TranscriptSegment.id.is_not(None), 0), else_=0),
        )
        owner_id = await self._owner_id()
        result = await self.session.execute(
            select(Meeting, TranscriptSegment)
            .join(TranscriptSegment, TranscriptSegment.meeting_id == Meeting.id)
            .where(
                Meeting.deleted_at_utc.is_(None),
                Meeting.owner_account_id == owner_id,
                or_(*(TranscriptSegment.text.ilike(pattern) for pattern in patterns)),
            )
            .order_by(
                relevance.desc(),
                Meeting.meeting_at_utc.desc(),
                TranscriptSegment.sequence_number,
            )
            .limit(limit)
        )
        return list(result.all())

    async def get_action_item(self, action_item_id: str) -> ActionItem | None:
        owner_id = await self._owner_id()
        return await self.session.scalar(
            select(ActionItem)
            .join(Meeting, Meeting.id == ActionItem.meeting_id)
            .where(ActionItem.id == action_item_id, Meeting.owner_account_id == owner_id)
        )

    async def get_transcript_segment(self, segment_id: str) -> TranscriptSegment | None:
        owner_id = await self._owner_id()
        return await self.session.scalar(
            select(TranscriptSegment)
            .join(Meeting, Meeting.id == TranscriptSegment.meeting_id)
            .where(TranscriptSegment.id == segment_id, Meeting.owner_account_id == owner_id)
        )

    async def get_moment(self, moment_id: str) -> MeetingMoment | None:
        owner_id = await self._owner_id()
        return await self.session.scalar(
            select(MeetingMoment)
            .join(Meeting, Meeting.id == MeetingMoment.meeting_id)
            .where(MeetingMoment.id == moment_id, Meeting.owner_account_id == owner_id)
        )

    def add(self, entity: object) -> None:
        self.session.add(entity)

    async def flush(self) -> None:
        await self.session.flush()

    async def commit(self) -> None:
        await self.session.commit()

    async def delete(self, entity: object) -> None:
        await self.session.delete(entity)
