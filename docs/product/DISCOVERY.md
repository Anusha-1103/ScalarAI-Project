# EchoNote Product Discovery

## Problem

Meeting recordings are difficult to review and handwritten notes lose context.
People need a fast way to locate a past conversation, understand its outcome,
verify the original wording, and complete follow-up work without replaying an
entire recording.

## Audience

- Individual contributors reviewing decisions and assigned follow-ups.
- Managers scanning summaries across recurring team meetings.
- Recruiters and customer-facing teams locating exact transcript moments.
- Evaluators assessing full-stack architecture, usability, and code quality.

## Product Principles

- Make the useful post-meeting information visible immediately.
- Keep transcript text and playback position synchronized in both directions.
- Preserve user edits and status changes across sessions.
- Favor clear, dense productivity UI over decorative dashboard design.
- Seed realistic data so every important workflow is demonstrable immediately.

## Success Signals

- A user can find and open a meeting in a few seconds.
- A transcript search result opens and seeks to the exact matching moment.
- Summary, topics, and action items are understandable without reading the full transcript.
- Meeting and task changes remain correct after a reload.
- The primary workflows remain usable on desktop and mobile viewports.

## Constraints

- The frontend uses Next.js with TypeScript.
- The backend uses Python with FastAPI.
- SQLite is the persistent database.
- Real speech-to-text, authentication, and live meeting capture are out of scope.
- The first release must remain practical to build, explain, and deploy within the assignment window.
