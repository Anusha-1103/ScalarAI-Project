# ruff: noqa: B008

import json
import math
from datetime import datetime
from pathlib import Path
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, File, Form, Query, Response, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.api_schemas import ApiResponse, PaginatedData, Pagination
from app.common.auth import CurrentPrincipalDependency
from app.common.database import get_database_session
from app.common.exceptions import ApplicationError
from app.modules.meetings.meeting_repository import MeetingRepository
from app.modules.meetings.meeting_schemas import (
    AccountRead,
    ActionItemCreate,
    ActionItemRead,
    ActionItemUpdate,
    AskAnswer,
    AskRequest,
    MeetingCreate,
    MeetingDetail,
    MeetingListItem,
    MeetingMomentCreate,
    MeetingMomentRead,
    MeetingUpdate,
    SearchResult,
    TranscriptSegmentRead,
    TranscriptSegmentUpdate,
)
from app.modules.meetings.meeting_service import MeetingService

router = APIRouter(tags=["Meetings"])


def get_meeting_service(
    session: Annotated[AsyncSession, Depends(get_database_session)],
    principal: CurrentPrincipalDependency,
) -> MeetingService:
    return MeetingService(MeetingRepository(session, principal))


MeetingServiceDependency = Annotated[MeetingService, Depends(get_meeting_service)]


@router.get("/me", response_model=ApiResponse[AccountRead], tags=["Account"])
async def get_current_account(service: MeetingServiceDependency) -> ApiResponse[AccountRead]:
    return ApiResponse(data=await service.get_account())


@router.get("/meetings", response_model=ApiResponse[PaginatedData[MeetingListItem]])
async def list_meetings(
    service: MeetingServiceDependency,
    search: str | None = Query(default=None, max_length=100),
    participant: str | None = Query(default=None, max_length=100),
    date_from: datetime | None = Query(default=None, alias="dateFrom"),
    date_to: datetime | None = Query(default=None, alias="dateTo"),
    sort_order: Literal["asc", "desc"] = Query(default="desc", alias="sortOrder"),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
) -> ApiResponse[PaginatedData[MeetingListItem]]:
    items, total = await service.list_meetings(
        search=search,
        participant=participant,
        date_from=date_from,
        date_to=date_to,
        sort_order=sort_order,
        page=page,
        limit=limit,
    )
    return ApiResponse(
        data=PaginatedData(
            items=items,
            pagination=Pagination(
                page=page,
                limit=limit,
                total_items=total,
                total_pages=math.ceil(total / limit) if total else 0,
            ),
        )
    )


@router.post(
    "/meetings",
    response_model=ApiResponse[MeetingDetail],
    status_code=status.HTTP_201_CREATED,
)
async def create_meeting(
    payload: MeetingCreate,
    service: MeetingServiceDependency,
) -> ApiResponse[MeetingDetail]:
    return ApiResponse(data=await service.create_meeting(payload))


@router.post(
    "/meetings/import",
    response_model=ApiResponse[MeetingDetail],
    status_code=status.HTTP_201_CREATED,
)
async def import_meeting(
    service: MeetingServiceDependency,
    title: Annotated[str, Form(min_length=2, max_length=200)],
    meeting_at_utc: Annotated[datetime, Form(alias="meetingAtUtc")],
    participant_names: Annotated[str, Form(alias="participantNames")],
    transcript_file: Annotated[UploadFile, File(alias="transcriptFile")],
) -> ApiResponse[MeetingDetail]:
    extension = Path(transcript_file.filename or "transcript.txt").suffix.lower().lstrip(".")
    if extension not in {"txt", "vtt", "json"}:
        raise ApplicationError(
            "UNSUPPORTED_TRANSCRIPT_TYPE",
            "Transcript must be a TXT, VTT, or JSON file",
            422,
        )
    raw = await transcript_file.read()
    if len(raw) > 1_000_000:
        raise ApplicationError("TRANSCRIPT_TOO_LARGE", "Transcript must be smaller than 1 MB", 413)
    try:
        content = raw.decode("utf-8")
        names_payload = json.loads(participant_names)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ApplicationError(
            "INVALID_TRANSCRIPT_UPLOAD",
            "Transcript must be UTF-8 and participant names must be valid JSON",
            422,
        ) from error
    if not isinstance(names_payload, list):
        raise ApplicationError("INVALID_PARTICIPANTS", "Participant names must be an array", 422)
    payload = MeetingCreate(
        title=title,
        meeting_at_utc=meeting_at_utc,
        participant_names=[str(name) for name in names_payload],
        transcript=content,
    )
    return ApiResponse(data=await service.create_meeting(payload, file_type=extension))


@router.get("/meetings/{meeting_id}", response_model=ApiResponse[MeetingDetail])
async def get_meeting(
    meeting_id: str, service: MeetingServiceDependency
) -> ApiResponse[MeetingDetail]:
    return ApiResponse(data=await service.get_meeting(meeting_id))


@router.patch("/meetings/{meeting_id}", response_model=ApiResponse[MeetingDetail])
async def update_meeting(
    meeting_id: str,
    payload: MeetingUpdate,
    service: MeetingServiceDependency,
) -> ApiResponse[MeetingDetail]:
    return ApiResponse(data=await service.update_meeting(meeting_id, payload))


@router.delete("/meetings/{meeting_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_meeting(meeting_id: str, service: MeetingServiceDependency) -> Response:
    await service.delete_meeting(meeting_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/meetings/{meeting_id}/action-items",
    response_model=ApiResponse[ActionItemRead],
    status_code=status.HTTP_201_CREATED,
)
async def create_action_item(
    meeting_id: str,
    payload: ActionItemCreate,
    service: MeetingServiceDependency,
) -> ApiResponse[ActionItemRead]:
    return ApiResponse(data=await service.create_action_item(meeting_id, payload))


@router.patch("/action-items/{action_item_id}", response_model=ApiResponse[ActionItemRead])
async def update_action_item(
    action_item_id: str,
    payload: ActionItemUpdate,
    service: MeetingServiceDependency,
) -> ApiResponse[ActionItemRead]:
    return ApiResponse(data=await service.update_action_item(action_item_id, payload))


@router.delete("/action-items/{action_item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_action_item(action_item_id: str, service: MeetingServiceDependency) -> Response:
    await service.delete_action_item(action_item_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch(
    "/transcript-segments/{segment_id}", response_model=ApiResponse[TranscriptSegmentRead]
)
async def update_transcript_segment(
    segment_id: str,
    payload: TranscriptSegmentUpdate,
    service: MeetingServiceDependency,
) -> ApiResponse[TranscriptSegmentRead]:
    return ApiResponse(data=await service.update_transcript_segment(segment_id, payload))


@router.post(
    "/meetings/{meeting_id}/moments",
    response_model=ApiResponse[MeetingMomentRead],
    status_code=status.HTTP_201_CREATED,
)
async def create_meeting_moment(
    meeting_id: str,
    payload: MeetingMomentCreate,
    service: MeetingServiceDependency,
) -> ApiResponse[MeetingMomentRead]:
    return ApiResponse(data=await service.create_moment(meeting_id, payload))


@router.delete("/moments/{moment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_meeting_moment(moment_id: str, service: MeetingServiceDependency) -> Response:
    await service.delete_moment(moment_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/search", response_model=ApiResponse[list[SearchResult]], tags=["Search"])
async def global_search(
    service: MeetingServiceDependency,
    query_text: str = Query(alias="q", min_length=1, max_length=100),
    limit: int = Query(default=20, ge=1, le=50),
) -> ApiResponse[list[SearchResult]]:
    return ApiResponse(data=await service.search(query_text, limit))


@router.post("/ask", response_model=ApiResponse[AskAnswer], tags=["Search"])
async def ask_meeting_memory(
    payload: AskRequest, service: MeetingServiceDependency
) -> ApiResponse[AskAnswer]:
    return ApiResponse(data=await service.ask(payload.question))
