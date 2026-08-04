---
type: Design
title: Auth middleware
description: Request middleware that validates JWT and attaches principal
tags: [design, auth]
timestamp: "2026-08-03T21:00:00Z"
status: active
verified: false
wiki_key: design-auth-middleware
truth_state: current
links:
  - target: /features/user-authentication.md
    rel: documents
  - target: /decisions/use-jwt-for-session.md
    rel: implements
---

# Auth middleware

Validates Bearer JWT and attaches principal.
