---
type: Meeting
title: Auth design discussion
description: Decided on JWT session approach for horizontal scaling
date: 2026-08-03
attendees: [rick, alice]
duration_minutes: 45
tags: [meeting, auth]
timestamp: "2026-08-03T18:00:00Z"
status: active
verified: true
wiki_key: meeting-2026-08-03-auth
truth_state: current
links:
  - target: /decisions/use-jwt-for-session.md
    rel: decides
  - target: /features/user-authentication.md
    rel: related_to
---

# Auth design discussion

## Meta

- Date: 2026-08-03
- Attendees: rick, alice
- Duration: 45 minutes

## Agenda

1. Review session strategies for multi-instance deploy
2. Compare JWT vs sticky session cookies
3. Agree on refresh/revoke approach

## Notes

We need auth that survives horizontal scale-out without shared session stores.
Alice walked through the cookie-session prototype; Rick shared JWT spike results
from [JWT vs session-cookie spike](/experiments/jwt-vs-cookie.md).

Concerns raised:
- Token size on every request
- Revocation for compromised tokens
- Refresh UX on mobile

## Decisions extracted

- [Use JWT for session management](/decisions/use-jwt-for-session.md)

## Action items

- Implement JWT middleware (owner: alice)
- Document refresh cookie scheme in design doc (owner: rick)
- Investigate token revoke denylist options (owner: rick)
