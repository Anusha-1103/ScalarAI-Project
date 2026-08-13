import json
from unittest.mock import AsyncMock

import pytest

from app.common.settings_config import Settings
from app.modules.meetings.ai_service import MeetingAIService
from app.modules.meetings.transcript_helper import ParsedSegment


@pytest.mark.asyncio
async def test_groq_analysis_contract_is_validated_and_mapped() -> None:
    service = MeetingAIService(Settings(groq_api_key="test-key"))
    service._complete = AsyncMock(  # type: ignore[method-assign]
        return_value=json.dumps(
            {
                "overview": "The team approved the onboarding launch after accessibility review.",
                "key_points": ["Launch is scheduled for Friday."],
                "chapters": [{"title": "Launch decision", "start_in_seconds": 4.2}],
                "action_items": [
                    {"description": "Complete accessibility review", "assignee_name": "Anusha"}
                ],
            }
        )
    )
    segments = [
        ParsedSegment(
            speaker_name="Anusha",
            text="I will complete the accessibility review before Friday.",
            start_in_seconds=4.2,
            end_in_seconds=9.0,
        )
    ]

    analysis = await service.analyze(segments)

    assert analysis.overview.startswith("The team approved")
    assert analysis.chapters[0].start_in_seconds == 4.2
    assert analysis.action_items[0].assignee_name == "Anusha"
    service._complete.assert_awaited_once()
