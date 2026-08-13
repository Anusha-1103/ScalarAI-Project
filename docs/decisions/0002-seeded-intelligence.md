# Decision 0002: Resilient Meeting Intelligence

## Status

Accepted on 2026-08-13 by Anusha.

## Context

Generated meeting intelligence improves review speed, but provider credentials,
quotas, latency, and structured-output variation must not make transcript
ingestion unavailable.

## Decision

Use Groq from the backend to generate grounded summaries, chapters, action
items, and answers. Normalize and validate provider output before persistence.
Keep deterministic local analysis as the fallback for missing credentials,
timeouts, quota exhaustion, invalid output, and local development.

## Consequences

The application gains useful synthesis without coupling core meeting ingestion
to one provider. Generated output may differ between requests, while validated
schemas, source evidence, tenant scoping, and fallback behavior remain stable.
