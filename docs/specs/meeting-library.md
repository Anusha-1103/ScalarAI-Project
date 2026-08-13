---
slug: meeting-library
title: Meeting Library
status: draft
saved: 2026-08-13T18:30:00Z
---

# Meeting Library

## Why

Users need one dependable place to scan, find, and reopen prior conversations.
The library must be useful immediately, before a user learns any advanced feature.

## Behaviour

The library lists non-deleted meetings with title, date, duration, host, and
participants. Search matches meeting titles and participant names as the user
types. Date and participant filters can be combined, and recency sorting is the
default. Loading, empty, no-result, and request-failure states preserve the page
layout and offer a clear recovery action.

## Acceptance criteria

- At least six realistic seeded meetings are visible on first launch.
- Every row shows title, local date and time, duration, and participant avatars.
- Search is case-insensitive and combines correctly with date and participant filters.
- The user can sort newest-first or oldest-first.
- Selecting a row opens the corresponding meeting workspace.
- The layout remains usable from 360 px mobile width through wide desktop.
