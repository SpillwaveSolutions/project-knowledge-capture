# PKC Typed Edges Reference

Plain Markdown links remain the universal edge form:

```markdown
[User authentication](/features/user-authentication.md)
```

Optional frontmatter enriches the same targets:

```yaml
links:
  - target: /features/user-authentication.md
    rel: decides
```

## Full relation set

### Inherited from OKF

| rel | Meaning |
|-----|---------|
| `depends_on` | Hard dependency |
| `routes_to` | Agent/workflow handoff |
| `implements` | Fulfills decision/ticket/interface |
| `documents` | Narrative about target |
| `uses` | Runtime/tool dependency |
| `owns` | Accountability |
| `supersedes` | Replaces older concept |
| `related_to` | Soft association |
| `tracks` | TicketLink tracks work/concept |
| `maps_to` | Ticket/external id maps to concept |

### PKC extensions

| rel | Direction (typical) | Meaning |
|-----|---------------------|---------|
| `satisfies` | Feature → Requirement | Feature meets requirement |
| `designed_by` | Feature → Design | Design shapes feature |
| `decides` | DecisionRecord → Feature/Design/Requirement | Decision governs |
| `informs` | Experiment/Discovery → Feature/Design/Requirement | Evidence influences |
| `discovered_in` | Finding → Discovery | Nested finding |
| `originates_from` | DecisionRecord → Meeting/Experiment | Provenance |
| `lands_in` | CodeChange/Feature → Release | Ships in release |
| `released_in` | CodeChange/Feature → Release | Alias of lands_in |
| `verified_by` | Test/Acceptance → Feature | Verification |

## Rules

1. Keep a body Markdown link for humans.
2. `target` is absolute in-bundle (`/features/…`).
3. Unknown `rel` values allowed (OKF validate → info).
4. Never invent edges.

## Helper

```bash
python3 scripts/pkc_link.py decisions/use-jwt-for-session.md \
  /features/user-authentication.md --rel decides --repo .
```
