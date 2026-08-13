# Supabase Production Setup

EchoNote uses Supabase for production authentication and PostgreSQL. The web
application stores the user session in secure cookies; FastAPI verifies the
Supabase JWT and scopes every query to the matching application account.

## 1. Create the project

Create a Supabase project and record these values from **Project Settings**:

- Project URL
- Publishable key
- Session pooler connection string on port `5432`

Use the session pooler for a long-running FastAPI service. Replace the connection
scheme with `postgresql+asyncpg://` for SQLAlchemy.

## 2. Configure the API

```env
ECHONOTE_ENVIRONMENT=production
ECHONOTE_DATABASE_URL=postgresql+asyncpg://postgres.PROJECT_REF:PASSWORD@POOLER_HOST:5432/postgres
ECHONOTE_CORS_ORIGINS=https://your-frontend.example
ECHONOTE_AUTH_REQUIRED=true
ECHONOTE_SUPABASE_URL=https://PROJECT_REF.supabase.co
```

`ECHONOTE_SUPABASE_JWT_SECRET` is only needed for projects still using legacy
HS256 tokens. New projects use asymmetric signing keys and the API reads the
project JWKS automatically.

## 3. Create and secure the schema

From `backend/`, run Alembic against the Supabase connection:

```bash
uv sync
uv run alembic upgrade head
```

Then run `supabase/migrations/202608140001_enable_rls.sql` in the Supabase SQL
Editor. It enables RLS on every Data API table and limits authenticated reads to
meetings owned by the current Supabase identity. FastAPI remains the write API
and applies the same ownership boundary in its repository layer.

## 4. Configure the web app

```env
NEXT_PUBLIC_API_URL=https://your-api.example/api/v1
NEXT_PUBLIC_SUPABASE_URL=https://PROJECT_REF.supabase.co
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=sb_publishable_...
NEXT_PUBLIC_DEMO_MODE=false
```

In Supabase **Authentication > URL Configuration**, add the deployed frontend
origin and its `/meetings` redirect URL. Enable email/password and magic-link
authentication. Google or Microsoft OAuth can be enabled later without changing
the application account model.

## Security Model

- The browser receives only the publishable key; secret/service keys never enter
  the frontend bundle.
- Next.js middleware refreshes cookie sessions and protects workspace routes.
- FastAPI verifies issuer, audience, signature, and expiry on bearer JWTs.
- The JWT subject maps to `Account.authUserId` on first API request.
- Repository queries always include the resolved account owner.
- PostgreSQL RLS adds defense in depth if tables are queried through Supabase's
  Data API.

## Local Demo Mode

Leave Supabase variables empty and set `ECHONOTE_AUTH_REQUIRED=false`. The app
uses the seeded account and SQLite, which keeps evaluator setup one-command and
does not weaken production behavior.
