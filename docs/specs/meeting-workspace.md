---
slug: meeting-workspace
title: Meeting Workspace
status: draft
saved: 2026-08-13T18:30:00Z
---

# Meeting Workspace

## Why

The meeting page is the core evaluation surface. It must let users understand
the outcome quickly while retaining confidence that every note maps back to the
recorded conversation.

## Behaviour

The workspace presents summary, key points, chapters, and action items beside an
ordered transcript with speaker labels and timestamps. Selecting a transcript
segment seeks the media element. During playback, the active segment is visibly
selected and may follow the viewport until the user intentionally scrolls away.
Transcript search highlights all matches, supports next and previous navigation,
and seeks playback when a result is selected.

## Acceptance criteria

- Summary and transcript panels are simultaneously visible on desktop.
- Every transcript segment has a stable speaker identity and formatted timestamp.
- Clicking a segment updates playback to within 250 ms of its start time.
- Playback updates the active segment without causing layout movement.
- Search highlights all case-insensitive matches and reports the result count.
- Previous and next controls wrap safely through the result set.
- Missing media uses a functional simulated player rather than a broken element.
