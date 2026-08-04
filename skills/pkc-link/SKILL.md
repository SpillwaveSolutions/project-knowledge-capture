---
name: pkc-link
description: Add a typed edge between two OKF concepts (satisfies, implements, designed_by, decides, informs, originates_from, tracks, maps_to, etc.). Use when connecting meetings to decisions, features to requirements, or tickets to work concepts.
---

# PKC Link

Add reviewable, typed relations so impact analysis and progressive disclosure work across formal and informal knowledge.

## Recommended relations (PKC + OKF)

| rel | Typical direction | Meaning |
|-----|-------------------|---------|
| `satisfies` | Feature → Requirement | Feature meets requirement |
| `implements` | CodeChange/Ticket → Feature/Design | Implementation |
| `designed_by` | Feature → Design | Design shapes feature |
| `decides` | DecisionRecord → Feature/Design/Requirement | Decision governs target |
| `informs` | Experiment/Discovery → Feature/Design/Requirement | Evidence influences |
| `discovered_in` | Finding → Discovery | Nested finding |
| `originates_from` | DecisionRecord → Meeting/Experiment | Provenance |
| `lands_in` / `released_in` | CodeChange/Feature → Release | Shipping |
| `tracks` | TicketLink → work concept | Work tracking |
| `maps_to` | TicketLink → external | External id map |
| `depends_on` | any → any | Hard dependency |
| `related_to` | any → any | Soft link |
| `supersedes` | newer → older | Replacement |
| `verified_by` | Test → Feature | Verification |

## Process

1. Confirm both concept paths (absolute in-bundle preferred: `/features/….md`).
2. Add edge:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/pkc_link.py" \
     decisions/use-jwt-for-session.md \
     /features/user-authentication.md \
     --rel decides \
     --repo .
   ```
3. Always keep a human-readable Markdown body link in addition to `links[].rel`.
4. Never invent edges — only record real relationships the user affirmed or that are evident in the source material.
5. Unknown `rel` values are allowed (OKF flags as info).

## Done when

- Frontmatter `links` entry exists on the source
- Body contains a Markdown link to the target
- Log updated when a new edge is created
