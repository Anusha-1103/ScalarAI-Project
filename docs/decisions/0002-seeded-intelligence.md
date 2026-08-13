# Decision 0002: Seeded Meeting Intelligence

## Status

Accepted on 2026-08-13 by Anusha.

## Context

Real speech-to-text is explicitly outside the assignment scope. Calling an LLM
would add credentials, cost, nondeterminism, latency, and deployment risk without
improving the main evaluated interactions.

## Decision

Persist realistic seeded summaries, chapters, transcript segments, and action
items. New meetings accept pasted transcript text or a supported transcript
file and receive a deterministic extractive summary suitable for demonstration.

## Consequences

The application is immediately usable, works without external secrets, and can
be evaluated consistently. The summarization provider boundary remains small so
an LLM implementation could replace it later.
