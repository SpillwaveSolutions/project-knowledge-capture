# 1. Use JWT for sessions

## Status

Accepted

## Context

We need session state that works across multiple app instances.

## Decision

Use short-lived JWT access tokens with refresh cookies.

## Consequences

No shared session store required; need revoke strategy later.
