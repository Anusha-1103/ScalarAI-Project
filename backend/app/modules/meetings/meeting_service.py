import math
import re
from datetime import UTC, datetime

from app.common.exceptions import ApplicationError
from app.common.settings_config import get_settings
from app.modules.meetings.ai_service import MeetingAIService
from app.modules.meetings.meeting_models import (
    ActionItem,
    Chapter,
    Meeting,
    MeetingMoment,
    MeetingParticipant,
    MeetingSummary,
    Participant,
    SummaryKeyPoint,
    TranscriptSegment,
)
from app.modules.meetings.meeting_repository import MeetingRepository
from app.modules.meetings.meeting_schemas import (
    AccountRead,
    ActionItemCreate,
    ActionItemRead,
    ActionItemUpdate,
    AskAnswer,
    ChapterRead,
    DashboardActionItem,
    DashboardRead,
    MeetingCreate,
    MeetingDetail,
    MeetingListItem,
    MeetingMomentCreate,
    MeetingMomentRead,
    MeetingSummaryRead,
    MeetingUpdate,
    ParticipantRead,
    SearchResult,
    TranscriptSegmentRead,
    TranscriptSegmentUpdate,
)
from app.modules.meetings.transcript_helper import parse_transcript


class MeetingService:
    def __init__(self, repository: MeetingRepository) -> None:
        self.repository = repository
        self.ai = MeetingAIService()

    async def get_account(self) -> AccountRead:
        account = await self.repository.resolve_account()
        settings = get_settings()
        return AccountRead(
            id=account.id,
            display_name=account.display_name,
            email=account.email,
            avatar_url=account.avatar_url,
            is_demo=(
                account.auth_user_id is None
                or account.email.casefold() == settings.demo_account_email.casefold()
            ),
        )

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
            moments=[
                MeetingMomentRead(
                    id=moment.id,
                    segment_id=moment.segment_id,
                    kind=moment.kind,
                    note=moment.note,
                    author_name=moment.author.display_name,
                    created_at_utc=moment.created_at_utc,
                )
                for moment in meeting.moments
            ],
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

    async def get_dashboard(self, limit: int) -> DashboardRead:
        meetings = await self.repository.get_dashboard_meetings(limit)
        open_actions = [
            DashboardActionItem(
                **self._action_item_read(item).model_dump(),
                meeting_id=meeting.id,
                meeting_title=meeting.title,
            )
            for meeting in meetings
            for item in meeting.action_items
            if not item.is_completed
        ]
        return DashboardRead(
            meetings=[self._list_item(meeting) for meeting in meetings],
            open_action_items=open_actions,
        )

    async def provision_sample_workspace(self) -> DashboardRead:
        from app.seed_data import provision_account_workspace

        account = await self.repository.resolve_account()
        await provision_account_workspace(self.repository.session, account)
        return await self.get_dashboard(50)

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
        self,
        payload: MeetingCreate,
        *,
        file_type: str = "txt",
        analyze_with_ai: bool = True,
        generate_actions: bool = True,
        source_type: str = "uploaded",
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
            source_type=source_type,
        )
        meeting.participants = [
            MeetingParticipant(participant=participants[name], is_host=index == 0)
            for index, name in enumerate(speaker_names)
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
        analysis = await self.ai.analyze(parsed, use_ai=analyze_with_ai)
        meeting.summary = MeetingSummary(
            overview=analysis.overview,
            key_points=[
                SummaryKeyPoint(sequence_number=index, text=text)
                for index, text in enumerate(analysis.key_points)
            ],
        )
        meeting.chapters = [
            Chapter(
                title=chapter.title,
                start_in_seconds=min(chapter.start_in_seconds, duration),
            )
            for chapter in analysis.chapters
        ]
        participant_lookup = {
            name.casefold(): participant for name, participant in participants.items()
        }
        if generate_actions:
            meeting.action_items = [
                ActionItem(
                    description=item.description,
                    assignee=participant_lookup.get(item.assignee_name.casefold())
                    if item.assignee_name
                    else None,
                )
                for item in analysis.action_items
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
        updates = payload.model_dump(exclude_unset=True)
        assignee_id = updates.get("assignee_participant_id")
        if assignee_id:
            meeting = await self.repository.get_meeting(item.meeting_id)
            participant_ids = {link.participant_id for link in meeting.participants}  # type: ignore[union-attr]
            if assignee_id not in participant_ids:
                raise ApplicationError(
                    "INVALID_ASSIGNEE", "Assignee is not a meeting participant", 422
                )
        for field, value in updates.items():
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

    async def update_transcript_segment(
        self, segment_id: str, payload: TranscriptSegmentUpdate
    ) -> TranscriptSegmentRead:
        segment = await self.repository.get_transcript_segment(segment_id)
        if not segment:
            raise ApplicationError("SEGMENT_NOT_FOUND", "Transcript segment does not exist", 404)
        segment.text = payload.text.strip()
        await self.repository.commit()
        saved = await self.repository.get_transcript_segment(segment_id)
        return TranscriptSegmentRead(
            id=saved.id,  # type: ignore[union-attr]
            sequence_number=saved.sequence_number,  # type: ignore[union-attr]
            start_in_seconds=saved.start_in_seconds,  # type: ignore[union-attr]
            end_in_seconds=saved.end_in_seconds,  # type: ignore[union-attr]
            text=saved.text,  # type: ignore[union-attr]
            speaker=(self._participant_read(saved.speaker) if saved and saved.speaker else None),
        )

    async def create_moment(
        self, meeting_id: str, payload: MeetingMomentCreate
    ) -> MeetingMomentRead:
        meeting = await self.repository.get_meeting(meeting_id)
        if not meeting:
            raise ApplicationError("MEETING_NOT_FOUND", "Meeting does not exist", 404)
        segment = await self.repository.get_transcript_segment(payload.segment_id)
        if not segment or segment.meeting_id != meeting_id:
            raise ApplicationError("INVALID_SEGMENT", "Segment is not part of this meeting", 422)
        account = await self.repository.resolve_account()
        moment = MeetingMoment(
            meeting_id=meeting_id,
            segment_id=payload.segment_id,
            author_account_id=account.id,
            kind=payload.kind,
            note=payload.note.strip() if payload.note else None,
        )
        self.repository.add(moment)
        await self.repository.commit()
        saved = await self.repository.get_moment(moment.id)
        return MeetingMomentRead(
            id=saved.id,  # type: ignore[union-attr]
            segment_id=saved.segment_id,  # type: ignore[union-attr]
            kind=saved.kind,  # type: ignore[union-attr]
            note=saved.note,  # type: ignore[union-attr]
            author_name=saved.author.display_name,  # type: ignore[union-attr]
            created_at_utc=saved.created_at_utc,  # type: ignore[union-attr]
        )

    async def delete_moment(self, moment_id: str) -> None:
        moment = await self.repository.get_moment(moment_id)
        if not moment:
            raise ApplicationError("MOMENT_NOT_FOUND", "Saved moment does not exist", 404)
        await self.repository.delete(moment)
        await self.repository.commit()

    async def search(self, query_text: str, limit: int) -> list[SearchResult]:
        if not query_text.strip():
            return []
        stop_words = {
            "about",
            "and",
            "did",
            "do",
            "for",
            "from",
            "mention",
            "the",
            "was",
            "were",
            "what",
            "when",
            "where",
            "which",
            "who",
            "with",
        }
        words = re.findall(r"[a-z0-9]+", query_text.lower())
        terms = list(
            dict.fromkeys(word for word in words if len(word) >= 3 and word not in stop_words)
        )
        terms.extend(
            word[:-1]
            for word in terms.copy()
            if word.endswith("s") and len(word) > 4 and word[:-1] not in terms
        )
        matches = await self.repository.search_transcripts(terms or words, limit)
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

    async def ask(self, question: str) -> AskAnswer:
        sources = await self.search(question, 8)
        result = await self.ai.answer(question, [source.snippet for source in sources])
        return AskAnswer(answer=result.answer, sources=sources[:5], used_ai=result.used_ai)
