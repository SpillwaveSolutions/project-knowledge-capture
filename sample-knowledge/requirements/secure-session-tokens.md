---
type: Requirement
title: Secure session tokens
description: Access tokens must be short-lived; refresh tokens httpOnly
tags: [requirement, auth, security]
timestamp: "2026-08-03T16:00:00Z"
status: active
verified: true
priority: high
wiki_key: req-secure-session-tokens
truth_state: current
links:
  - target: /features/user-authentication.md
    rel: related_to
---

# Secure session tokens

Access tokens MUST expire within 15 minutes.
