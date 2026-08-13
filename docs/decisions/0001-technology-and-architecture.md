# Decision 0001: Technology and Architecture

## Status

Accepted on 2026-08-13 by Anusha.

## Context

The assignment requires Next.js with TypeScript, a Python backend using FastAPI
or Django, and SQLite. The product has several related domains but only one
deployment unit per runtime and a short delivery window.

## Decision

Use Next.js for the web application and FastAPI with SQLAlchemy and Alembic for
the API. Keep both applications in one repository. Structure the backend as a
modular monolith with controller, service, schema, and repository boundaries.
Use REST under `/api/v1` and generate frontend types from OpenAPI where useful.

## Consequences

The solution directly satisfies the required stack, stays easy to deploy and
explain, and preserves clear domain boundaries. Python and Node dependencies
remain separate, so root scripts must coordinate both toolchains explicitly.
