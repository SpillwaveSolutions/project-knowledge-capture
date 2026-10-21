---
type: Scenario
title: Session reaches its limit
description: The next action is refused
preconditions: A session was issued
steps:
  - Wait past the limit
  - Try the next action
success_outcome: The next action is refused
tags: [scenario]
timestamp: "2026-08-03T20:00:00Z"
status: active
verified: false
wiki_key: scenario-session-reaches-its-limit
truth_state: current
links:
  - target: /journey-stages/establish-a-session.md
    rel: illustrates
  - target: /user-stories/session-expires-on-its-own.md
    rel: realized_by
---

# Session reaches its limit

## Preconditions

A session was issued.

## Steps

1. Wait past the limit.
2. Try the next action.

## Success outcome

The next action is refused.
