---
type: Assumption
title: Short access TTL is OK for UX
description: 15-minute JWT access tokens will not harm user experience
status: unvalidated
tags: [assumption, auth, ux]
timestamp: "2026-08-03T17:00:00Z"
verified: false
wiki_key: assumption-short-ttl-ok
truth_state: current
links:
  - target: /features/user-authentication.md
    rel: assumes
  - target: /experiments/jwt-vs-cookie.md
    rel: related_to
---

# Short access TTL is OK for UX

## Statement

15-minute JWT access tokens will not harm user experience if silent refresh works.

## Rationale

Peers use similar TTLs; refresh cookies hide rotation from users.

## Validation path

Instrument refresh failure rate in production for 2 weeks.
