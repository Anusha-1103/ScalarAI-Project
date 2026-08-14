-- Protect persisted meeting tags with the same tenant boundary as meetings.

alter table public."Tag" enable row level security;
alter table public."MeetingTag" enable row level security;

grant select on public."Tag", public."MeetingTag" to authenticated;
grant all on public."Tag", public."MeetingTag" to service_role;

create policy "tags_read_owned" on public."Tag"
for select to authenticated
using (
  exists (
    select 1 from public."Account" account
    where account.id = "ownerAccountId"
      and account."authUserId" = (select auth.uid())::text
  )
);

create policy "meeting_tags_read_owned" on public."MeetingTag"
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
