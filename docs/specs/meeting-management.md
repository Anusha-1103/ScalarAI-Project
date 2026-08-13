---
slug: meeting-management
title: Meeting Management
status: draft
saved: 2026-08-13T18:30:00Z
---

# Meeting Management

## Why

The assignment requires persisted CRUD rather than a read-only visual prototype.
Users need to bring meeting knowledge into the workspace and keep it accurate.

## Behaviour

A user can create a meeting by pasting transcript text or uploading a TXT, VTT,
or JSON transcript. The create flow validates metadata and previews parser
errors. Existing meeting titles and participants can be edited, and deletion
requires explicit confirmation. Action items can be created, edited, assigned,
completed, reopened, and deleted. Successful and failed mutations surface concise
toasts and correctly invalidate cached views.

## Acceptance criteria

- Creating a valid meeting persists metadata and at least one transcript segment.
- TXT, VTT, and documented JSON transcript shapes are accepted.
- Invalid files return a field-level or file-level explanation without partial data.
- Editing metadata is visible after reload in both detail and library views.
- Meeting deletion requires confirmation and removes it from normal queries.
- Every action-item mutation persists and updates without a full page reload.
