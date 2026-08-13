# Decision 0001: Technology and Architecture

## Status

Accepted on 2026-08-13 by Anusha.

## Context

EchoNote needs independently deployable web and API runtimes, typed HTTP
contracts, relational persistence, and clear ownership boundaries without the
operational overhead of distributed services.

## Decision

Use Next.js for the web application and FastAPI with SQLAlchemy and Alembic for
the API. Keep both applications in one repository. Structure the backend as a
modular monolith with controller, service, schema, and repository boundaries.
Use REST under `/api/v1` and generate frontend types from OpenAPI where useful.

## Consequences

The system stays easy to deploy and explain while preserving clear domain
boundaries. Python and Node dependencies remain separate, so root scripts must
coordinate both toolchains explicitly.
