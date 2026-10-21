---
type: UserJourney
title: Finish a signed-in task
description: The task is done and the session can end
goal: The task is done and the session can end
trigger: The operator opens the product
end_state: The task is done and the session is closed
golden_thread: true
tags: [journey, golden-thread]
timestamp: "2026-08-03T20:00:00Z"
status: active
verified: false
wiki_key: journey-finish-a-signed-in-task
truth_state: current
links:
  - target: /personas/operator.md
    rel: for_persona
  - target: /journey-stages/establish-a-session.md
    rel: covers
  - target: /scenarios/session-reaches-its-limit.md
    rel: has_scenario
---

# Finish a signed-in task

## Goal

The task is done and the session can end.

## Trigger

The operator opens the product.

## End state

The task is done and the session is closed.

## Stages

- [Establish a session](/journey-stages/establish-a-session.md)
