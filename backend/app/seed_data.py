# ruff: noqa: E501

from datetime import UTC, datetime

from sqlalchemy import func, select

from app.common.database import async_session_factory
from app.modules.meetings.meeting_models import Account, Meeting
from app.modules.meetings.meeting_repository import MeetingRepository
from app.modules.meetings.meeting_schemas import ActionItemCreate, MeetingCreate
from app.modules.meetings.meeting_service import MeetingService

SEED_MEETINGS = [
    {
        "title": "Q3 Product Roadmap Review",
        "meeting_at_utc": datetime(2026, 8, 12, 10, 30, tzinfo=UTC),
        "participants": ["Maya Chen", "Arjun Mehta", "Sofia Reed"],
        "transcript": """Maya Chen: Thanks for joining. Today we need to lock the Q3 roadmap and resolve the onboarding priority.
Arjun Mehta: Activation is still our biggest gap. Only forty-two percent of new workspaces invite a teammate in their first week.
Sofia Reed: The interviews point to uncertainty, not lack of intent. People do not understand what the invited teammate will see.
Maya Chen: Let us make the invitation preview part of the onboarding checklist and measure completion separately.
Arjun Mehta: Engineering can ship the preview behind a flag by next Thursday if design is final on Monday.
Sofia Reed: I will deliver the empty, pending, and accepted invitation states before Monday afternoon.
Maya Chen: Good. The analytics dashboard moves to the following sprint, but event instrumentation stays in this one.
Arjun Mehta: I will add activation events and a migration for the new invitation status.
Sofia Reed: We should test the copy with five recent trial users before the full rollout.
Maya Chen: Agreed. We will review the flag data in the August twenty-first product sync.""",
        "actions": [
            ("Deliver invitation preview states", "Sofia Reed"),
            ("Add activation events and invitation migration", "Arjun Mehta"),
            ("Schedule five onboarding copy tests", "Maya Chen"),
        ],
    },
    {
        "title": "Northstar Customer Onboarding",
        "meeting_at_utc": datetime(2026, 8, 11, 8, 0, tzinfo=UTC),
        "participants": ["Leah Morgan", "Daniel Kim", "Priya Nair"],
        "transcript": """Leah Morgan: Welcome to the kickoff. We will confirm goals, owners, and the first integration milestone.
Daniel Kim: Our main goal is to reduce the manual handoff between sales and implementation.
Priya Nair: The CRM export contains the required account fields, but contact roles are currently free text.
Leah Morgan: We can normalize those roles during import and show unmatched values for review.
Daniel Kim: Security also needs a data retention statement before production access is approved.
Priya Nair: I will share our standard retention policy and the subprocessors list this afternoon.
Leah Morgan: For the pilot, we will import one hundred historical accounts into a sandbox workspace.
Daniel Kim: I can provide the anonymized export by Wednesday morning.
Priya Nair: Once the import passes, we will schedule admin training with the operations team.
Leah Morgan: Perfect. Our checkpoint is Friday at the same time with import results and open mapping questions.""",
        "actions": [
            ("Send retention policy and subprocessors list", "Priya Nair"),
            ("Provide anonymized CRM export", "Daniel Kim"),
            ("Prepare role-mapping review", "Leah Morgan"),
        ],
    },
    {
        "title": "Mobile Experience Design Critique",
        "meeting_at_utc": datetime(2026, 8, 8, 12, 15, tzinfo=UTC),
        "participants": ["Sofia Reed", "Noah Williams", "Isha Kapoor"],
        "transcript": """Sofia Reed: The goal today is to decide how the meeting summary behaves on small screens.
Noah Williams: The current tabs hide too much context when someone jumps from a task into the transcript.
Isha Kapoor: A bottom sheet would preserve context, but it becomes crowded once the keyboard opens.
Sofia Reed: What if summary sections stay in the page and transcript search opens as a full-height sheet?
Noah Williams: That works if the playback bar remains pinned and does not cover the final transcript line.
Isha Kapoor: I can prototype the safe-area behavior and test it on iOS and Android viewport sizes.
Sofia Reed: Let us also reduce the metadata header after the first scroll so the transcript gets more space.
Noah Williams: Keep the title visible. Losing the meeting identity while searching feels disorienting.
Isha Kapoor: I will include a compact title and collapse participants into a count after scroll.
Sofia Reed: Great. We will compare both versions in Thursday's usability session.""",
        "actions": [
            ("Prototype transcript search bottom sheet", "Isha Kapoor"),
            ("Define compact meeting header behavior", "Sofia Reed"),
            ("Prepare mobile usability script", "Noah Williams"),
        ],
    },
    {
        "title": "Senior Backend Engineer Debrief",
        "meeting_at_utc": datetime(2026, 8, 7, 6, 45, tzinfo=UTC),
        "participants": ["Riya Shah", "Owen Brooks", "Arjun Mehta"],
        "transcript": """Riya Shah: Let us review the evidence against the role scorecard before making a recommendation.
Owen Brooks: The candidate decomposed the billing problem well and asked useful questions about failure recovery.
Arjun Mehta: I agreed with the architecture, especially starting with a modular monolith instead of services.
Riya Shah: How did the implementation portion go once the requirements changed?
Owen Brooks: They adapted quickly, but the first version missed idempotency on the retry endpoint.
Arjun Mehta: They caught that during review and added both the key constraint and a concurrency test.
Riya Shah: Communication was strong in my values interview, with concrete examples of handling disagreement.
Owen Brooks: My only concern is limited experience operating systems at our current traffic level.
Arjun Mehta: That is coachable. The debugging fundamentals were stronger than most candidates at this level.
Riya Shah: We have a clear hire recommendation. I will consolidate feedback and send the packet today.""",
        "actions": [
            ("Consolidate interview feedback packet", "Riya Shah"),
            ("Add operating-scale context to final feedback", "Owen Brooks"),
        ],
    },
    {
        "title": "Engineering Weekly Sync",
        "meeting_at_utc": datetime(2026, 8, 5, 9, 30, tzinfo=UTC),
        "participants": ["Arjun Mehta", "Elena Rossi", "Marcus Lee"],
        "transcript": """Arjun Mehta: We will start with release health, then blockers, then the database migration plan.
Elena Rossi: Error rate is back below baseline after yesterday's cache configuration change.
Marcus Lee: The worker backlog is stable, but the oldest job age still spikes during the morning import window.
Arjun Mehta: Can we split imports by workspace so one large customer cannot occupy every worker?
Marcus Lee: Yes. I have a partition-key change ready and need a production-like load test before merging.
Elena Rossi: I can add the worker age metric to the release dashboard and alert at ten minutes.
Arjun Mehta: The profile migration is the remaining release blocker. We need rollback timings before approval.
Marcus Lee: I will run the migration against the staging snapshot and record forward and rollback duration.
Elena Rossi: Support has been briefed on the visible changes and has the rollback communication template.
Arjun Mehta: We will make the release decision tomorrow after the load test and migration rehearsal.""",
        "actions": [
            ("Run partitioned import load test", "Marcus Lee"),
            ("Add worker age alert to release dashboard", "Elena Rossi"),
            ("Review migration rehearsal results", "Arjun Mehta"),
        ],
    },
    {
        "title": "Launch Campaign Planning",
        "meeting_at_utc": datetime(2026, 8, 1, 11, 0, tzinfo=UTC),
        "participants": ["Ava Thompson", "Kabir Singh", "Maya Chen"],
        "transcript": """Ava Thompson: We need one launch narrative that works across the announcement, demo, and customer email.
Kabir Singh: The strongest angle from beta feedback is getting decisions and follow-ups without replaying a call.
Maya Chen: Keep the message concrete. Faster review is believable; promising perfect memory is not.
Ava Thompson: The landing page will lead with exact moments, summaries, and assigned work in one workspace.
Kabir Singh: I will cut the demo around a customer handoff and show search jumping to the objection.
Maya Chen: Product can provide three anonymized meetings with realistic summaries by Tuesday.
Ava Thompson: We also need a launch checklist covering analytics, support readiness, and rollback ownership.
Kabir Singh: The video can be ready Thursday if the final interface is deployed by Wednesday morning.
Maya Chen: I will confirm the release candidate with engineering and share a stable demo URL.
Ava Thompson: Great. Final copy review is Wednesday afternoon and launch remains next Monday.""",
        "actions": [
            ("Produce customer handoff demo video", "Kabir Singh"),
            ("Provide anonymized demo meetings", "Maya Chen"),
            ("Complete launch readiness checklist", "Ava Thompson"),
        ],
    },
]


async def seed_database() -> None:
    async with async_session_factory() as session:
        if (await session.scalar(select(func.count(Meeting.id)))) or 0:
            return

        account = Account(
            display_name="Anusha",
            email="anusha@echonote.local",
            avatar_url=None,
        )
        session.add(account)
        await session.commit()

        service = MeetingService(MeetingRepository(session))
        for seed in SEED_MEETINGS:
            detail = await service.create_meeting(
                MeetingCreate(
                    title=seed["title"],
                    meeting_at_utc=seed["meeting_at_utc"],
                    participant_names=seed["participants"],
                    transcript=seed["transcript"],
                )
            )
            participant_ids = {
                participant.name: participant.id for participant in detail.participants
            }
            for description, assignee_name in seed["actions"]:
                await service.create_action_item(
                    detail.id,
                    ActionItemCreate(
                        description=description,
                        assignee_participant_id=participant_ids[assignee_name],
                    ),
                )
