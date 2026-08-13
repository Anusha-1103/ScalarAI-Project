# Architecture Overview

EchoNote uses a mixed-language monorepo with two independently deployable
applications and one relational database.

```text
Browser
  -> Next.js frontend
       -> typed HTTP client
            -> FastAPI /api/v1
                 -> application services
                      -> repositories
                           -> SQLite
```

## Frontend

The Next.js App Router owns navigation, rendering, local interaction state, and
accessible UI. TanStack Query owns server state and cache invalidation. The
media element remains the playback clock; transcript components derive their
active segment from its current time instead of maintaining a second clock.

## Backend

FastAPI is organized as a modular monolith. HTTP controllers validate requests
and delegate to services. Services implement use cases and transaction
boundaries. Repositories are the only layer that queries SQLAlchemy models.
Pydantic schemas define every external request and response contract.

Initial modules are meetings, transcripts, summaries, action items, and search.
They share database and error infrastructure but do not reach into each other's
persistence implementation.

## Persistence

SQLite stores meetings, participants, transcript segments, summaries, chapters,
and action items. Alembic owns schema changes. Foreign keys and frequently used
filter fields are indexed. Transcript sequence and timestamps are constrained so
playback order remains deterministic.

## Search

Meeting metadata filtering is performed through indexed relational queries.
Transcript search uses SQLite FTS5 when available, with a deterministic LIKE
fallback for compatible hosted environments. Results include segment and start
time so the frontend can navigate directly to context.

## Deployment

The frontend is designed for Vercel. The FastAPI application and persistent
SQLite volume are designed for Render. Environment-specific API origins and
CORS allowlists are configured through environment variables.

## Quality Strategy

- Pytest covers services, repositories, validation, and API behavior.
- Vitest and Testing Library cover frontend logic and components.
- Playwright covers the library, transcript synchronization, and CRUD workflows.
- CI runs formatting, linting, type checking, unit tests, and production builds.
