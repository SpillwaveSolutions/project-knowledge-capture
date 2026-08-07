---
type: Acceptance
title: Session expires within 15 minutes
description: An access token issued at T is rejected by the API at T plus 15 minutes.
status: unverified
tags: [acceptance]
timestamp: "2026-08-07T04:11:37Z"
verified: false
generated: true
wiki_key: acceptance-session-expires-within-15-minutes
truth_state: current
links:
  - target: /features/user-authentication.md
    rel: satisfies
  - target: /code/pr-12-jwt-middleware.md
    rel: verified_by
---

# Session expires within 15 minutes

## Criterion

An access token issued at T is rejected by the API at T plus 15 minutes.

## How it is verified

_Test, review, or observation that settles this._

## Related

- [/features/user-authentication.md](/features/user-authentication.md) (`satisfies`)
- [/code/pr-12-jwt-middleware.md](/code/pr-12-jwt-middleware.md) (`verified_by`)
