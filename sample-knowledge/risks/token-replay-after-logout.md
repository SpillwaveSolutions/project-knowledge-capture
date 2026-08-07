---
type: Risk
title: Token replay after logout
description: A stolen access token stays valid until it expires, so logout does not actually end the session. Anyone holding the token keeps access for up to the full TTL.
severity: high
status: open
tags: [risk, high]
timestamp: "2026-08-07T04:11:37Z"
verified: false
generated: true
wiki_key: risk-token-replay-after-logout
truth_state: current
links:
  - target: /features/user-authentication.md
    rel: exposes
---

# Token replay after logout

## Risk

A stolen access token stays valid until it expires, so logout does not actually end the session. Anyone holding the token keeps access for up to the full TTL.

## Severity

`high`

## Mitigation

_What reduces the likelihood or blast radius?_

## Related

- [/features/user-authentication.md](/features/user-authentication.md) (`exposes`)
