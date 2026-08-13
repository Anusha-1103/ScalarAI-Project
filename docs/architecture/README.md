# EchoNote Architecture

EchoNote is a mixed-language system with independently deployable web and API
runtimes, managed identity, relational persistence, and a resilient AI provider
boundary.

## Interactive Map

[Open the interactive Archify architecture](echonote-architecture.html) or
inspect its [typed source](echonote.architecture.json).

[![EchoNote runtime architecture](../assets/echonote-architecture.png)](echonote-architecture.html)

The artifact is generated with
[Archify](https://github.com/tt-a1i/archify). Its showcase validation checks
schema correctness, SVG integrity, route geometry, label clearance, crossings,
corridors, border runs, route rhythm, and legend placement.

## Runtime Boundaries

### Web

Next.js and React run on Vercel. The web application owns routing, responsive
rendering, local interaction state, Supabase session refresh, and TanStack Query
cache invalidation. Authenticated API calls include the Supabase access token as
a bearer credential.

### API

FastAPI runs on Render as a modular monolith. Controllers validate HTTP
contracts, application services coordinate use cases and transactions, and
repositories exclusively own SQL access. Pydantic models define request,
response, and provider-output contracts.

### Identity and Tenancy

Supabase Auth owns credentials and sessions. FastAPI verifies issuer, audience,
signature, and expiry using the project's JWKS, then maps the JWT subject to an
application account. Repositories scope meeting, transcript, action, moment,
and search operations to that account. PostgreSQL row-level security adds a
second boundary for Data API reads.

### Persistence

Supabase PostgreSQL stores accounts, meetings, participants, transcript
segments, summaries, chapters, actions, and saved moments. Alembic owns schema
evolution. SQLite uses the same SQLAlchemy domain model for local development
and automated tests.

### Intelligence

Groq generates evidence-grounded summaries, key points, chapters, assigned
actions, and Ask Echo answers. Provider output is normalized and validated
before persistence. Deterministic local analysis protects meeting ingestion and
search when the provider is unavailable or not configured.

## Primary Request Path

```text
Browser
  -> Next.js on Vercel
    -> Supabase Auth
    -> FastAPI on Render
      -> application service
        -> owner-scoped repository
          -> Supabase PostgreSQL
      -> Groq inference or local fallback
```

## Deployment

| Runtime | Platform | Responsibility |
| --- | --- | --- |
| Web | Vercel | Next.js delivery and authenticated product UI |
| API | Render | FastAPI, authorization, use cases, AI orchestration |
| Identity | Supabase Auth | Credentials, sessions, JWT issuance |
| Data | Supabase PostgreSQL | Durable tenant-scoped relational state |
| AI | Groq | Grounded generation and synthesis |
| Monitoring | GitHub Actions + Render | Scheduled readiness probe and service recovery |

The API exposes `/api/v1/health` for deployment checks. AI provider failures do
not make the core transcript workflow unavailable.
