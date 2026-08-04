---
type: Experiment
title: JWT vs session-cookie spike
description: Both workable; JWT chosen for statelessness
hypothesis: JWT will simplify horizontal scaling
result: Both workable; JWT slightly simpler ops without Redis session store
conclusion: Proceed with JWT + httpOnly refresh cookie
tags: [experiment, auth]
timestamp: "2026-08-01T12:00:00Z"
status: completed
verified: true
wiki_key: experiment-jwt-vs-cookie
truth_state: current
links:
  - target: /features/user-authentication.md
    rel: informs
  - target: /decisions/use-jwt-for-session.md
    rel: related_to
---

# JWT vs session-cookie spike

## Conclusion

Proceed with JWT.
