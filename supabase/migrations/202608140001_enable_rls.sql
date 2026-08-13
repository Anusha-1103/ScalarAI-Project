-- Run after Alembic creates the application schema in Supabase Postgres.
-- The FastAPI service owns writes; these policies defend Data API reads.

alter table public."Account" enable row level security;
alter table public."Meeting" enable row level security;
alter table public."Participant" enable row level security;
alter table public."MeetingParticipant" enable row level security;
alter table public."TranscriptSegment" enable row level security;
alter table public."MeetingSummary" enable row level security;
alter table public."SummaryKeyPoint" enable row level security;
alter table public."Chapter" enable row level security;
alter table public."ActionItem" enable row level security;
alter table public."MeetingMoment" enable row level security;

grant select on all tables in schema public to authenticated;
grant all on all tables in schema public to service_role;

create policy "accounts_read_self" on public."Account"
for select to authenticated
using ("authUserId" = (select auth.uid())::text);

create policy "meetings_read_owned" on public."Meeting"
for select to authenticated
using (
  exists (
    select 1 from public."Account" account
    where account.id = "ownerAccountId"
      and account."authUserId" = (select auth.uid())::text
  )
);

create policy "participants_read_from_owned_meetings" on public."Participant"
for select to authenticated
using (
  exists (
    select 1
    from public."MeetingParticipant" membership
    join public."Meeting" meeting on meeting.id = membership."meetingId"
    join public."Account" account on account.id = meeting."ownerAccountId"
    where membership."participantId" = "Participant".id
      and account."authUserId" = (select auth.uid())::text
  )
);

create policy "meeting_participants_read_owned" on public."MeetingParticipant"
for select to authenticated
using (exists (select 1 from public."Meeting" meeting where meeting.id = "meetingId"));

create policy "segments_read_owned" on public."TranscriptSegment"
for select to authenticated
using (exists (select 1 from public."Meeting" meeting where meeting.id = "meetingId"));

create policy "summaries_read_owned" on public."MeetingSummary"
for select to authenticated
using (exists (select 1 from public."Meeting" meeting where meeting.id = "meetingId"));

create policy "key_points_read_owned" on public."SummaryKeyPoint"
for select to authenticated
using (
  exists (
    select 1 from public."MeetingSummary" summary
    where summary.id = "summaryId"
  )
);

create policy "chapters_read_owned" on public."Chapter"
for select to authenticated
using (exists (select 1 from public."Meeting" meeting where meeting.id = "meetingId"));

create policy "actions_read_owned" on public."ActionItem"
for select to authenticated
using (exists (select 1 from public."Meeting" meeting where meeting.id = "meetingId"));

create policy "moments_read_owned" on public."MeetingMoment"
for select to authenticated
using (exists (select 1 from public."Meeting" meeting where meeting.id = "meetingId"));
