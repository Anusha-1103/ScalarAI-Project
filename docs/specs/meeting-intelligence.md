---
slug: meeting-intelligence
title: Meeting Intelligence and Search
status: draft
saved: 2026-08-13T18:30:00Z
---

# Meeting Intelligence and Search

## Why

Users should be able to understand a meeting quickly and recover details even
when they remember only a phrase from the conversation.

## Behaviour

Every seeded meeting includes a persisted general summary, key points, chapters,
and action items. New meetings receive deterministic extractive notes from their
transcript. Global search matches meeting metadata and transcript content and
returns contextual snippets linked to the meeting and transcript timestamp.

## Acceptance criteria

- Each seeded meeting has a summary, at least two chapters, and action items.
- Chapters include start positions that seek to the relevant transcript context.
- New meeting summaries are deterministic for the same transcript input.
- Global search returns meeting-level and transcript-level matches.
- A transcript result opens the correct meeting and seeks to the matching segment.
- Empty queries and no-result queries are handled without backend errors.
