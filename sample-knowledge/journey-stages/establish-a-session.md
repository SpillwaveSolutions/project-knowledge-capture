---
type: JourneyStage
title: Establish a session
description: The operator has a session that will expire
outcome: The operator has a session that will expire
success_metric: Time to a usable session
order: 1
tags: [journey-stage]
timestamp: "2026-08-03T20:00:00Z"
status: active
verified: false
wiki_key: stage-establish-a-session
truth_state: current
links:
  - target: /journeys/finish-a-signed-in-task.md
    rel: stage_of
  - target: /features/user-authentication.md
    rel: realized_by
  - target: /personas/operator.md
    rel: for_persona
---

# Establish a session

## Outcome

The operator has a session that will expire.

## Success metric

Time to a usable session.

## Feature

This stage is delivered by [User authentication](/features/user-authentication.md).
