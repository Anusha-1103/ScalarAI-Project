-- Make every Data API policy verify workspace ownership without relying on nested RLS behavior.

revoke all on all tables in schema public from anon;

drop policy if exists "meeting_participants_read_owned" on public."MeetingParticipant";
drop policy if exists "segments_read_owned" on public."TranscriptSegment";
drop policy if exists "summaries_read_owned" on public."MeetingSummary";
drop policy if exists "key_points_read_owned" on public."SummaryKeyPoint";
drop policy if exists "chapters_read_owned" on public."Chapter";
drop policy if exists "actions_read_owned" on public."ActionItem";
drop policy if exists "moments_read_owned" on public."MeetingMoment";

create policy "meeting_participants_read_owned" on public."MeetingParticipant"
for select to authenticated
using (
  exists (
    select 1
    from public."Meeting" meeting
    join public."Account" account on account.id = meeting."ownerAccountId"
    where meeting.id = "meetingId"
      and account."authUserId" = (select auth.uid())::text
  )
);

create policy "segments_read_owned" on public."TranscriptSegment"
for select to authenticated
using (
  exists (
    select 1
    from public."Meeting" meeting
    join public."Account" account on account.id = meeting."ownerAccountId"
    where meeting.id = "meetingId"
      and account."authUserId" = (select auth.uid())::text
  )
);

create policy "summaries_read_owned" on public."MeetingSummary"
for select to authenticated
using (
  exists (
    select 1
    from public."Meeting" meeting
    join public."Account" account on account.id = meeting."ownerAccountId"
    where meeting.id = "meetingId"
      and account."authUserId" = (select auth.uid())::text
  )
);

create policy "key_points_read_owned" on public."SummaryKeyPoint"
for select to authenticated
using (
  exists (
    select 1
    from public."MeetingSummary" summary
    join public."Meeting" meeting on meeting.id = summary."meetingId"
    join public."Account" account on account.id = meeting."ownerAccountId"
    where summary.id = "summaryId"
      and account."authUserId" = (select auth.uid())::text
  )
);

create policy "chapters_read_owned" on public."Chapter"
for select to authenticated
using (
  exists (
    select 1
    from public."Meeting" meeting
    join public."Account" account on account.id = meeting."ownerAccountId"
    where meeting.id = "meetingId"
      and account."authUserId" = (select auth.uid())::text
  )
);

create policy "actions_read_owned" on public."ActionItem"
for select to authenticated
using (
  exists (
    select 1
    from public."Meeting" meeting
    join public."Account" account on account.id = meeting."ownerAccountId"
    where meeting.id = "meetingId"
      and account."authUserId" = (select auth.uid())::text
  )
);

create policy "moments_read_owned" on public."MeetingMoment"
for select to authenticated
using (
  exists (
    select 1
    from public."Meeting" meeting
    join public."Account" account on account.id = meeting."ownerAccountId"
    where meeting.id = "meetingId"
      and account."authUserId" = (select auth.uid())::text
  )
);

create index if not exists idx_meeting_owner_active_date
on public."Meeting" ("ownerAccountId", "deletedAtUtc", "meetingAtUtc");

create index if not exists idx_action_item_meeting_completion
on public."ActionItem" ("meetingId", "isCompleted");
