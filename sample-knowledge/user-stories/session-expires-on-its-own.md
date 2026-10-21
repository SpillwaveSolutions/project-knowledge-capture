---
type: UserStory
title: Session expires on its own
description: a stolen token stops working
persona: Operator
capability: have the session expire
outcome: a stolen token stops working
priority: must
acceptance_criteria:
  - An access token is rejected after the limit
requirement_ids:
  - FR-001
tags: [user-story, must]
timestamp: "2026-08-03T20:00:00Z"
status: active
verified: false
wiki_key: user-story-session-expires-on-its-own
truth_state: current
links:
  - target: /personas/operator.md
    rel: for_persona
  - target: /journey-stages/establish-a-session.md
    rel: implements_step
  - target: /requirements/secure-session-tokens.md
    rel: traces_to
  - target: /stories/session-expires-on-its-own.md
    rel: maps_to
---

# Session expires on its own

As a Operator, I want have the session expire, so that a stolen token stops working.

## Acceptance

- An access token is rejected after the limit.

## Requirement ids

FR-001
