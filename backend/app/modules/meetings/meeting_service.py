import math
from datetime import UTC, datetime

from app.common.exceptions import ApplicationError
from app.modules.meetings.meeting_models import (
    ActionItem,
    Chapter,
    Meeting,
    MeetingParticipant,
    MeetingSummary,
    Participant,
    SummaryKeyPoint,
    TranscriptSegment,
)
from app.modules.meetings.meeting_repository import MeetingRepository
from app.modules.meetings.meeting_schemas import (
    ActionItemCreate,
    ActionItemRead,
    ActionItemUpdate,
    ChapterRead,
    MeetingCreate,
    MeetingDetail,
    MeetingListItem,
    MeetingSummaryRead,
    MeetingUpdate,
    ParticipantRead,
    SearchResult,
    TranscriptSegmentRead,
)
from app.modules.meetings.transcript_helper import build_summary, parse_transcript


class MeetingService:
    def __init__(self, repository: MeetingRepository) -> None:
        self.repository = repository

    @staticmethod
    def _participant_read(participant: Participant, *, is_host: bool = False) -> ParticipantRead:
        return ParticipantRead(
            id=participant.id,
            name=participant.name,
            email=participant.email,
            avatar_color=participant.avatar_color,
            is_host=is_host,
        )

    def _list_item(self, meeting: Meeting) -> MeetingListItem:
        participants = [
            self._participant_read(link.participant, is_host=link.is_host)
            for link in meeting.participants
        ]
        return MeetingListItem(
            id=meeting.id,
            title=meeting.title,
            meeting_at_utc=meeting.meeting_at_utc,
            duration_in_seconds=meeting.duration_in_seconds,
            source_type=meeting.source_type,
            participants=participants,
            summary_preview=meeting.summary.overview if meeting.summary else None,
            action_item_count=len(meeting.action_items),
            completed_action_item_count=sum(item.is_completed for item in meeting.action_items),
        )

    def _detail(self, meeting: Meeting) -> MeetingDetail:
        base = self._list_item(meeting)
        summary = None
        if meeting.summary:
            summary = MeetingSummaryRead(
                overview=meeting.summary.overview,
                key_points=[point.text for point in meeting.summary.key_points],
            )
        return MeetingDetail(
            **base.model_dump(),
            media_url=meeting.media_url,
            transcript_segments=[
                TranscriptSegmentRead(
                    id=segment.id,
                    sequence_number=segment.sequence_number,
                    start_in_seconds=segment.start_in_seconds,
                    end_in_seconds=segment.end_in_seconds,
                    text=segment.text,
                    speaker=(self._participant_read(segment.speaker) if segment.speaker else None),
                )
                for segment in meeting.transcript_segments
            ],
            summary=summary,
            chapters=[
                ChapterRead(
                    id=chapter.id, title=chapter.title, start_in_seconds=chapter.start_in_seconds
                )
                for chapter in meeting.chapters
            ],
            action_items=[self._action_item_read(item) for item in meeting.action_items],
        )

    def _action_item_read(self, item: ActionItem) -> ActionItemRead:
        return ActionItemRead(
            id=item.id,
            description=item.description,
            is_completed=item.is_completed,
            due_at_utc=item.due_at_utc,
            assignee=self._participant_read(item.assignee) if item.assignee else None,
            created_at_utc=item.created_at_utc,
            updated_at_utc=item.updated_at_utc,
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
    ) -> tuple[list[MeetingListItem], int]:
        meetings, total = await self.repository.list_meetings(
            search=search,
            participant=participant,
            date_from=date_from,
            date_to=date_to,
            sort_order=sort_order,
            page=page,
            limit=limit,
        )
        return [self._list_item(meeting) for meeting in meetings], total

    async def get_meeting(self, meeting_id: str) -> MeetingDetail:
        meeting = await self.repository.get_meeting(meeting_id)
        if not meeting:
            raise ApplicationError("MEETING_NOT_FOUND", "Meeting does not exist", 404)
        return self._detail(meeting)

    async def _get_or_create_participant(self, name: str, color_index: int) -> Participant:
        existing = await self.repository.find_participant(name)
        if existing:
            return existing
        colors = ["#5B61DC", "#0F9D78", "#D97706", "#D14D72", "#147D92", "#7C3AED"]
        participant = Participant(name=name.strip(), avatar_color=colors[color_index % len(colors)])
        self.repository.add(participant)
        await self.repository.flush()
        return participant

    async def create_meeting(
        self, payload: MeetingCreate, *, file_type: str = "txt"
    ) -> MeetingDetail:
        account = await self.repository.get_default_account()
        if not account:
            raise ApplicationError(
                "ACCOUNT_NOT_CONFIGURED", "Default account is not configured", 500
            )

        try:
            parsed = parse_transcript(payload.transcript, payload.participant_names, file_type)
        except ValueError as error:
            raise ApplicationError("INVALID_TRANSCRIPT", str(error), 422) from error

        speaker_names = list(
            dict.fromkeys([*payload.participant_names, *(item.speaker_name for item in parsed)])
        )
        participants = {
            name: await self._get_or_create_participant(name, index)
            for index, name in enumerate(speaker_names)
        }
        duration = payload.duration_in_seconds or math.ceil(parsed[-1].end_in_seconds)
        meeting = Meeting(
            owner_account_id=account.id,
            title=payload.title.strip(),
            meeting_at_utc=payload.meeting_at_utc,
            duration_in_seconds=duration,
            source_type="uploaded",
        )
        meeting.participants = [
            MeetingParticipant(participant=participants[name], is_host=index == 0)
            for index, name in enumerate(payload.participant_names)
        ]
        meeting.transcript_segments = [
            TranscriptSegment(
                speaker=participants[item.speaker_name],
                sequence_number=index,
                start_in_seconds=item.start_in_seconds,
                end_in_seconds=item.end_in_seconds,
                text=item.text,
            )
            for index, item in enumerate(parsed)
        ]
        overview, points = build_summary(parsed)
        meeting.summary = MeetingSummary(
            overview=overview,
            key_points=[
                SummaryKeyPoint(sequence_number=index, text=text)
                for index, text in enumerate(points)
            ],
        )
        chapter_indexes = sorted({0, len(parsed) // 3, (len(parsed) * 2) // 3})
        meeting.chapters = [
            Chapter(
                title=(
                    "Opening and context"
                    if index == 0
                    else f"Discussion: {parsed[index].text[:52].rstrip('.')}"
                ),
                start_in_seconds=parsed[index].start_in_seconds,
            )
            for index in chapter_indexes
        ]
        self.repository.add(meeting)
        await self.repository.commit()
        created = await self.repository.get_meeting(meeting.id)
        if not created:
            raise ApplicationError("MEETING_CREATE_FAILED", "Meeting could not be loaded", 500)
        return self._detail(created)

    async def update_meeting(self, meeting_id: str, payload: MeetingUpdate) -> MeetingDetail:
        meeting = await self.repository.get_meeting(meeting_id)
        if not meeting:
            raise ApplicationError("MEETING_NOT_FOUND", "Meeting does not exist", 404)
        updates = payload.model_dump(exclude_unset=True)
        if "title" in updates:
            meeting.title = updates["title"].strip()
        if "meeting_at_utc" in updates:
            meeting.meeting_at_utc = updates["meeting_at_utc"]
        if "participant_names" in updates:
            names = list(
                dict.fromkeys(name.strip() for name in updates["participant_names"] if name.strip())
            )
            meeting.participants = [
                MeetingParticipant(
                    participant=await self._get_or_create_participant(name, index),
                    is_host=index == 0,
                )
                for index, name in enumerate(names)
            ]
        await self.repository.commit()
        updated = await self.repository.get_meeting(meeting_id)
        return self._detail(updated)  # type: ignore[arg-type]

    async def delete_meeting(self, meeting_id: str) -> None:
        meeting = await self.repository.get_meeting(meeting_id)
        if not meeting:
            raise ApplicationError("MEETING_NOT_FOUND", "Meeting does not exist", 404)
        meeting.deleted_at_utc = datetime.now(UTC)
        await self.repository.commit()

    async def create_action_item(
        self, meeting_id: str, payload: ActionItemCreate
    ) -> ActionItemRead:
        meeting = await self.repository.get_meeting(meeting_id)
        if not meeting:
            raise ApplicationError("MEETING_NOT_FOUND", "Meeting does not exist", 404)
        participant_ids = {link.participant_id for link in meeting.participants}
        if (
            payload.assignee_participant_id
            and payload.assignee_participant_id not in participant_ids
        ):
            raise ApplicationError("INVALID_ASSIGNEE", "Assignee is not a meeting participant", 422)
        item = ActionItem(
            meeting_id=meeting_id,
            description=payload.description.strip(),
            assignee_participant_id=payload.assignee_participant_id,
            due_at_utc=payload.due_at_utc,
        )
        self.repository.add(item)
        await self.repository.commit()
        saved = await self.repository.get_action_item(item.id)
        return self._action_item_read(saved)  # type: ignore[arg-type]

    async def update_action_item(
        self, action_item_id: str, payload: ActionItemUpdate
    ) -> ActionItemRead:
        item = await self.repository.get_action_item(action_item_id)
        if not item:
            raise ApplicationError("ACTION_ITEM_NOT_FOUND", "Action item does not exist", 404)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(item, field, value.strip() if field == "description" and value else value)
        await self.repository.commit()
        saved = await self.repository.get_action_item(action_item_id)
        return self._action_item_read(saved)  # type: ignore[arg-type]

    async def delete_action_item(self, action_item_id: str) -> None:
        item = await self.repository.get_action_item(action_item_id)
        if not item:
            raise ApplicationError("ACTION_ITEM_NOT_FOUND", "Action item does not exist", 404)
        await self.repository.delete(item)
        await self.repository.commit()

    async def search(self, query_text: str, limit: int) -> list[SearchResult]:
        if not query_text.strip():
            return []
        matches = await self.repository.search_transcripts(query_text, limit)
        return [
            SearchResult(
                meeting_id=meeting.id,
                meeting_title=meeting.title,
                meeting_at_utc=meeting.meeting_at_utc,
                segment_id=segment.id,
                start_in_seconds=segment.start_in_seconds,
                snippet=segment.text,
                result_type="transcript",
            )
            for meeting, segment in matches
        ]
