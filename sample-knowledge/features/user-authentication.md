---
type: Feature
title: User authentication
description: Sign-in, session, and refresh for end users
tags: [feature, auth]
timestamp: "2026-08-03T20:00:00Z"
status: active
verified: false
priority: high
level: story
wiki_key: feature-user-authentication
truth_state: current
worklog_id: 01KEXAMPLE0000000000000001
links:
  - target: /decisions/use-jwt-for-session.md
    rel: designed_by
  - target: /requirements/secure-session-tokens.md
    rel: satisfies
  - target: /designs/auth-middleware.md
    rel: designed_by
  - target: /meetings/2026-08-03-auth-design.md
    rel: related_to
  - target: /experiments/jwt-vs-cookie.md
    rel: related_to
  - target: /tickets/ticket-01kexample0000000000000001.md
    rel: tracks
  - target: /assumptions/short-ttl-ok-for-ux.md
    rel: related_to
  - target: /questions/need-revoke-denylist-v1.md
    rel: related_to
---

# User authentication

Shaped by [Use JWT for session management](/decisions/use-jwt-for-session.md).

- Assumption: [Short access TTL is OK for UX](/assumptions/short-ttl-ok-for-ux.md)
- Open question: [Need distributed revoke denylist in v1?](/questions/need-revoke-denylist-v1.md)
