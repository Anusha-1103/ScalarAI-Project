# EchoNote

EchoNote is a full-stack meeting notes and transcription workspace inspired by
the post-meeting experience of Fireflies.ai. It provides a searchable meeting
library, synchronized transcript playback, concise summaries, chapters, and
persistent action items.

## Highlights

- Six seeded meetings with speakers, timestamps, summaries, chapters, and tasks
- Meeting search, participant and date filters, and recency sorting
- TXT, VTT, and JSON transcript import, plus pasted-transcript creation
- Playback seek bar synchronized in both directions with transcript segments
- In-transcript highlighting and global search with timestamp deep links
- Supabase email/password and magic-link authentication with isolated accounts
- Editable transcript lines, saved moments, and Smart Search filters
- Speaker talk time, recurring topics, meeting tone, and conversation metrics
- Meeting metadata and action-item CRUD with toast feedback
- Responsive desktop and mobile workspaces and Markdown export
- Dashboard, Ask Echo, calendar, people, integrations, and settings workspaces
- Interactive OpenAPI documentation at `/docs`

Real speech-to-text, live call bots, authentication, integrations, and actual
LLM inference are intentionally out of scope. The API generates deterministic
summary content from imported text so the project is immediately usable without
external services or credentials.

## Tech Stack

- **Frontend:** Next.js 15, React 19, TypeScript, TanStack Query, Tailwind CSS,
  Lucide icons, Vitest
- **Backend:** Python 3.12+, FastAPI, SQLAlchemy async, Pydantic, Alembic, Pytest
- **Platform:** Supabase Auth and PostgreSQL with row-level security
- **Local adapter:** SQLite with the same domain models and API behavior

## Local Setup

Prerequisites: Node.js 22+, pnpm 10+, Python 3.12+, and
[uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/Anusha-1103/ScalarAI-Project.git
cd ScalarAI-Project

# Terminal 1: API
cd backend
cp .env.example .env
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --port 8000

# Terminal 2: web app
cd frontend
cp .env.example .env.local
corepack enable
pnpm install
pnpm dev
```

Open `http://localhost:3000`. The database and sample records are created on
the API's first startup. API documentation is at `http://localhost:8000/docs`.

## Architecture

```text
Next.js App Router
  -> typed fetch client + TanStack Query cache
    -> FastAPI controllers
      -> meeting application service
        -> SQLAlchemy repository
          -> SQLite
```

The frontend owns interaction state and derives the active transcript segment
from one playback timestamp. TanStack Query owns remote state and invalidation.
The backend is a modular monolith: controllers validate HTTP contracts,
services implement use cases and transactions, and repositories exclusively own
database queries. Supabase Auth supplies production identities, and PostgreSQL
RLS provides a second ownership boundary behind the API. See
[the Supabase setup guide](docs/SUPABASE.md), [the architecture notes](docs/architecture/README.md), and
[decisions](docs/decisions/) for the reasoning behind these boundaries.

## Database Schema

| Table | Purpose | Important relationships |
| --- | --- | --- |
| `Account` | Supabase identity profile or local demo owner | Owns meetings |
| `Meeting` | Metadata, duration, source, and soft-delete state | Parent for all meeting content |
| `Participant` | Reusable speaker identity | Many-to-many with meetings |
| `MeetingParticipant` | Meeting attendance and host role | Joins meetings and participants |
| `TranscriptSegment` | Ordered text with start/end timestamps | Meeting and optional speaker |
| `MeetingSummary` | One overview per meeting | Owns ordered key points |
| `SummaryKeyPoint` | Ordered summary bullets | Belongs to a summary |
| `Chapter` | Timestamped meeting outline | Belongs to a meeting |
| `ActionItem` | Persistent tasks, completion, assignee, due date | Meeting and optional participant |
| `MeetingMoment` | Saved transcript bookmarks and reactions | Meeting, segment, and author account |

Foreign keys cascade owned content, sequence uniqueness preserves deterministic
ordering, timestamp checks reject invalid transcript ranges, and indexes support
the library filters and transcript search.

## API Overview

All JSON responses use `{ success, data, error }`.

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET/POST` | `/api/v1/meetings` | Filter/list or create meetings |
| `POST` | `/api/v1/meetings/import` | Import TXT, VTT, or JSON transcript |
| `GET/PATCH/DELETE` | `/api/v1/meetings/{id}` | Read, edit, or soft-delete a meeting |
| `POST` | `/api/v1/meetings/{id}/action-items` | Add an action item |
| `PATCH/DELETE` | `/api/v1/action-items/{id}` | Edit, complete, or remove a task |
| `PATCH` | `/api/v1/transcript-segments/{id}` | Correct transcript text |
| `POST` | `/api/v1/meetings/{id}/moments` | Save a transcript moment |
| `DELETE` | `/api/v1/moments/{id}` | Remove a saved moment |
| `GET` | `/api/v1/search?q=...` | Search all transcript segments |
| `GET` | `/api/v1/me` | Resolve the authenticated application profile |
| `GET` | `/api/v1/health` | Deployment health check |

## Verification

```bash
# Frontend
pnpm --dir frontend lint
pnpm --dir frontend exec tsc --noEmit
pnpm --dir frontend test
pnpm --dir frontend build

# Backend
cd backend
uv run ruff check .
uv run ruff format --check .
uv run pytest
```

## Deployment

The frontend is ready for Vercel with `frontend` as the project root. Set
`NEXT_PUBLIC_API_URL` to the deployed API URL ending in `/api/v1`.

The included `render.yaml` provisions FastAPI on Render. Supply the Supabase
session-pooler URL through `ECHONOTE_DATABASE_URL`, set
`ECHONOTE_SUPABASE_URL`, and allow the Vercel origin through
`ECHONOTE_CORS_ORIGINS`. Dockerfiles are included for container deployment.

## Assumptions

- A default seeded account represents the logged-in user.
- Imported transcripts are UTF-8 and at most 1 MB.
- Playback uses a deterministic recording clock because real media and
  transcription are outside the assignment scope.
- Summary generation is deterministic and local; no transcript leaves the API.
