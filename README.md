# EchoNote

EchoNote is a full-stack meeting notes and transcription workspace inspired by
the post-meeting experience of Fireflies.ai. It turns persisted meeting
transcripts into a searchable library, synchronized playback, concise summaries,
and actionable follow-ups.

> Project setup and local development instructions will be completed alongside
> the first runnable release.

## Planned Stack

- Next.js and TypeScript
- FastAPI and SQLAlchemy
- SQLite with Alembic migrations
- Tailwind CSS and accessible headless UI primitives
- Vitest, Pytest, and Playwright

## Repository Layout

```text
frontend/   Next.js web application
backend/    FastAPI application, migrations, and tests
docs/       Product, architecture, and API documentation
```

## Scope

The first release includes a meetings library, transcript search, synchronized
media playback, AI-style summaries, topics, and persistent action-item CRUD.
Authentication, live meeting bots, speech-to-text, and third-party integrations
are represented as product placeholders and are outside the implementation
scope.
