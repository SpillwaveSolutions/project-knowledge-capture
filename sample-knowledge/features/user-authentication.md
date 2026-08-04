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
---

# User authentication

Shaped by [Use JWT for session management](/decisions/use-jwt-for-session.md).
