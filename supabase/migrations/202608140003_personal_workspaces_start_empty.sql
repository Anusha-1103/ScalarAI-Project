-- Personal accounts start empty. Only remove generated samples, never user-created meetings.

delete from public."Meeting" meeting
using public."Account" account
where meeting."ownerAccountId" = account.id
  and meeting."sourceType" = 'demo'
  and lower(account.email) <> 'demo@echonote.app';

delete from public."Participant" participant
where not exists (
  select 1
  from public."MeetingParticipant" membership
  where membership."participantId" = participant.id
);
