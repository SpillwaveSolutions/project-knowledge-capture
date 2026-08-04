---
type: ContextPack
title: Context pack for /features/user-authentication.md
description: Progressive disclosure pack (1 hops, 8 nodes)
timestamp: 2026-08-04T04:29:31Z
generated: true
tags: [pack, pkc, progressive-disclosure]
---

# Context pack: `/features/user-authentication.md`

- Hops: **1**
- Nodes: **8** (max 8)
- Generated: 2026-08-04T04:29:31Z

## Graph

```mermaid
flowchart LR
  features_user_authentication_md["Feature: User authentication"]
  decisions_use_jwt_for_session_md{"DecisionRecord: Use JWT for session management"}
  meetings_2026_08_03_auth_design_md(["Meeting: Auth design discussion"])
  experiments_jwt_vs_cookie_md[("Experiment: JWT vs session-cookie spike")]
  assumptions_short_ttl_ok_for_ux_md["Assumption: Short access TTL is OK for UX"]
  designs_auth_middleware_md["Design: Auth middleware"]
  requirements_secure_session_tokens_md["Requirement: Secure session tokens"]
  tickets_ticket_01kexample0000000000000001_md["TicketLink: Implement user authentication"]
  features_user_authentication_md -- designed_by --> decisions_use_jwt_for_session_md
  features_user_authentication_md -- satisfies --> requirements_secure_session_tokens_md
  features_user_authentication_md -- designed_by --> designs_auth_middleware_md
  features_user_authentication_md -- related_to --> meetings_2026_08_03_auth_design_md
  features_user_authentication_md -- related_to --> experiments_jwt_vs_cookie_md
  features_user_authentication_md -- tracks --> tickets_ticket_01kexample0000000000000001_md
  features_user_authentication_md -- related_to --> assumptions_short_ttl_ok_for_ux_md
```

## Nodes (ranked)

### [User authentication](/features/user-authentication.md) · `Feature` · depth 0

Sign-in, session, and refresh for end users

> Shaped by [Use JWT for session management](/decisions/use-jwt-for-session.md). - Assumption: [Short access TTL is OK for UX](/assumptions/short-ttl-ok-for-ux.md) - Open question: [Need distributed revoke denylist in v1?](/questions/need-revoke-denylist-v1.md)

### [Use JWT for session management](/decisions/use-jwt-for-session.md) · `DecisionRecord` · depth 1

Adopt short-lived JWT access tokens with httpOnly refresh cookies

> Use short-lived JWT access tokens + httpOnly refresh cookies.

### [Auth design discussion](/meetings/2026-08-03-auth-design.md) · `Meeting` · depth 1

Decided on JWT session approach for horizontal scaling

> - Date: 2026-08-03 - Attendees: rick, alice - Duration: 45 minutes 1. Review session strategies for multi-instance deploy 2. Compare JWT vs sticky session cookies 3. Agree on refresh/revoke approach We need auth that survives horizontal scale-out without shared session stores. Alice walked through the cookie-session prototype; Rick shared JWT spike results from [JWT vs session-cookie spike](/exper…

### [JWT vs session-cookie spike](/experiments/jwt-vs-cookie.md) · `Experiment` · depth 1

Both workable; JWT chosen for statelessness

> Proceed with JWT.

### [Short access TTL is OK for UX](/assumptions/short-ttl-ok-for-ux.md) · `Assumption` · depth 1

15-minute JWT access tokens will not harm user experience

> 15-minute JWT access tokens will not harm user experience if silent refresh works. Peers use similar TTLs; refresh cookies hide rotation from users. Instrument refresh failure rate in production for 2 weeks.

### [Auth middleware](/designs/auth-middleware.md) · `Design` · depth 1

Request middleware that validates JWT and attaches principal

> Validates Bearer JWT and attaches principal.

### [Secure session tokens](/requirements/secure-session-tokens.md) · `Requirement` · depth 1

Access tokens must be short-lived; refresh tokens httpOnly

> Access tokens MUST expire within 15 minutes.

### [Implement user authentication](/tickets/ticket-01kexample0000000000000001.md) · `TicketLink` · depth 1

WikiTicket bridge for the user-authentication feature

> Worklog ULID `01KEXAMPLE0000000000000001`.

## Edges

- `/features/user-authentication.md` —[designed_by]→ `/decisions/use-jwt-for-session.md`
- `/features/user-authentication.md` —[satisfies]→ `/requirements/secure-session-tokens.md`
- `/features/user-authentication.md` —[designed_by]→ `/designs/auth-middleware.md`
- `/features/user-authentication.md` —[related_to]→ `/meetings/2026-08-03-auth-design.md`
- `/features/user-authentication.md` —[related_to]→ `/experiments/jwt-vs-cookie.md`
- `/features/user-authentication.md` —[tracks]→ `/tickets/ticket-01kexample0000000000000001.md`
- `/features/user-authentication.md` —[related_to]→ `/assumptions/short-ttl-ok-for-ux.md`
- `/features/user-authentication.md` —[related_to]→ `/questions/need-revoke-denylist-v1.md`

_Nodes beyond hops/max_nodes omitted for progressive disclosure._
