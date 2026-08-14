from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic.alias_generators import to_camel


class ApiModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class ParticipantRead(ApiModel):
    id: str
    name: str
    email: str | None
    avatar_color: str
    is_host: bool = False


class AccountRead(ApiModel):
    id: str
    display_name: str
    email: str
    avatar_url: str | None
    is_demo: bool


class TranscriptSegmentRead(ApiModel):
    id: str
    sequence_number: int
    start_in_seconds: float
    end_in_seconds: float
    text: str
    speaker: ParticipantRead | None


class TranscriptSegmentUpdate(ApiModel):
    text: str = Field(min_length=1, max_length=10_000)


class MeetingMomentRead(ApiModel):
    id: str
    segment_id: str
    kind: str
    note: str | None
    author_name: str
    created_at_utc: datetime


class MeetingMomentCreate(ApiModel):
    segment_id: str
    kind: str = Field(default="important", pattern="^(important|positive|concern)$")
    note: str | None = Field(default=None, max_length=500)


class MeetingSummaryRead(ApiModel):
    overview: str
    key_points: list[str]


class ChapterRead(ApiModel):
    id: str
    title: str
    start_in_seconds: float


class ActionItemRead(ApiModel):
    id: str
    description: str
    is_completed: bool
    due_at_utc: datetime | None
    assignee: ParticipantRead | None
    created_at_utc: datetime
    updated_at_utc: datetime


class MeetingListItem(ApiModel):
    id: str
    title: str
    meeting_at_utc: datetime
    duration_in_seconds: int
    source_type: str
    participants: list[ParticipantRead]
    summary_preview: str | None
    action_item_count: int
    completed_action_item_count: int


class MeetingDetail(MeetingListItem):
    media_url: str | None
    transcript_segments: list[TranscriptSegmentRead]
    summary: MeetingSummaryRead | None
    chapters: list[ChapterRead]
    action_items: list[ActionItemRead]
    moments: list[MeetingMomentRead]


class DashboardActionItem(ActionItemRead):
    meeting_id: str
    meeting_title: str


class DashboardRead(ApiModel):
    meetings: list[MeetingListItem]
    open_action_items: list[DashboardActionItem]


class MeetingCreate(ApiModel):
    title: str = Field(min_length=2, max_length=200)
    meeting_at_utc: datetime
    participant_names: list[str] = Field(min_length=1, max_length=20)
    transcript: str = Field(min_length=10, max_length=200_000)
    duration_in_seconds: int | None = Field(default=None, ge=0, le=86_400)

    @field_validator("participant_names")
    @classmethod
    def validate_participants(cls, values: list[str]) -> list[str]:
        cleaned = [value.strip() for value in values if value.strip()]
        if not cleaned:
            raise ValueError("At least one participant is required")
        return list(dict.fromkeys(cleaned))


class MeetingUpdate(ApiModel):
    title: str | None = Field(default=None, min_length=2, max_length=200)
    meeting_at_utc: datetime | None = None
    participant_names: list[str] | None = Field(default=None, min_length=1, max_length=20)


class ActionItemCreate(ApiModel):
    description: str = Field(min_length=2, max_length=500)
    assignee_participant_id: str | None = None
    due_at_utc: datetime | None = None


class ActionItemUpdate(ApiModel):
    description: str | None = Field(default=None, min_length=2, max_length=500)
    assignee_participant_id: str | None = None
    due_at_utc: datetime | None = None
    is_completed: bool | None = None


class SearchResult(ApiModel):
    meeting_id: str
    meeting_title: str
    meeting_at_utc: datetime
    segment_id: str | None = None
    start_in_seconds: float | None = None
    snippet: str
    result_type: str


class AskRequest(ApiModel):
    question: str = Field(min_length=2, max_length=500)


class AskAnswer(ApiModel):
    answer: str
    sources: list[SearchResult]
    used_ai: bool
