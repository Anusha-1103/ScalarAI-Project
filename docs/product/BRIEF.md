# EchoNote Product Brief

## Summary

EchoNote is a post-meeting workspace that helps users browse recorded meetings,
review timestamped conversations, understand concise meeting outcomes, and track
follow-up work. It recreates the focused library and two-panel meeting workflow
expected from a modern meeting assistant while using seeded transcript data in
place of speech-to-text.

## Users

- **Meeting participant** - revisits discussion context and completes assigned work.
- **Meeting host** - maintains meeting metadata, notes, participants, and tasks.
- **Knowledge seeker** - searches meetings and transcripts for a remembered detail.

## Target Outcome

A user can move from a broad meeting library to the exact spoken moment and its
resulting action item without replaying the full call or relying on separate notes.

## Key Flows

1. **Find a meeting** - Search, filter, and sort the meeting library, then open the relevant record.
2. **Review a meeting** - Scan the summary, topics, and tasks beside the timestamped transcript.
3. **Navigate playback** - Select a transcript segment to seek media, or follow the active segment as playback advances.
4. **Search a transcript** - Highlight every match, move between results, and seek directly to its timestamp.
5. **Manage meeting knowledge** - Create or import a meeting, edit metadata, and remove an obsolete meeting.
6. **Complete follow-ups** - Add, edit, assign, complete, and reopen action items with persistent state.

## Domain Concepts

- **Meeting** - a dated conversation with duration, media, participants, and generated notes.
- **Participant** - a person attached to one or more meetings and transcript segments.
- **Transcript segment** - an ordered speaker utterance with start and end positions.
- **Summary** - a persisted overview and structured set of key points.
- **Chapter** - a timestamped topic describing one portion of a meeting.
- **Action item** - a persistent follow-up task with assignee and completion state.

## Constraints

- Next.js and TypeScript frontend; FastAPI backend; SQLite database.
- REST endpoints are versioned under `/api/v1` and documented through OpenAPI.
- A default logged-in account is assumed; no authentication flow is required.
- The dedicated demo account includes realistic meetings; personal accounts opt into sample content explicitly.
- The experience is responsive and keyboard accessible.

## Out of Scope

- Live meeting bots and real-time transcription.
- Real speech-to-text or speaker diarization.
- Production authentication, teams, and sharing permissions.
- Zoom, Meet, calendar, CRM, and messaging integrations.
- Unbounded generative AI calls; summaries are deterministic and persisted.
