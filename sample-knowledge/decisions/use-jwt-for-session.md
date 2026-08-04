---
type: DecisionRecord
title: Use JWT for session management
description: Adopt short-lived JWT access tokens with httpOnly refresh cookies
status: accepted
tags: [decision, adr, auth]
timestamp: "2026-08-03T19:00:00Z"
verified: true
wiki_key: adr-jwt-session
truth_state: current
links:
  - target: /meetings/2026-08-03-auth-design.md
    rel: originates_from
  - target: /features/user-authentication.md
    rel: decides
  - target: /experiments/jwt-vs-cookie.md
    rel: informs
---

# Use JWT for session management

## Decision

Use short-lived JWT access tokens + httpOnly refresh cookies.
