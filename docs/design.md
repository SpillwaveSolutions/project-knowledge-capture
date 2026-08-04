# PKC Design

## Architecture

```text
 Human / Agent Activity
 (meetings, experiments, discovery, coding, planning)
              │
   ┌──────────┼──────────┐
   ▼          ▼          ▼
WikiTicket   PKC Capture  Direct OKF authoring
(worklog)    skills       (okf-author)
   │          │
   │ materialize
   └────►─────┤
              ▼
       OKF Knowledge Graph
       (Markdown + YAML)
              │
              ▼
   Impact / Query / Progressive Disclosure
   (okf-plugin)
```

## Design principles

1. **Git-native** — ordinary Markdown files; PR-reviewable diffs.
2. **OKF-native storage** — no parallel schema; free-form `type` values OKF already allows.
3. **Loose coupling** — optional WikiTicket bridge; optional okf CLI.
4. **Deterministic helpers** — scripts for materialize/link; agents for extraction judgment.
5. **Idempotent writes** — re-capture and re-materialize update in place.
6. **Dual-host packaging** — one Claude plugin tree for Claude Code + Grok Build.

## Module boundaries

| Module | Responsibility |
|--------|----------------|
| Skills | Agent procedures for capture/materialize/promote/link |
| `scripts/pkc_common.py` | Frontmatter, catalogs, bundle init |
| `scripts/pkc_capture.py` | Structured capture skeletons |
| `scripts/pkc_materialize.py` | Worklog fold + docs → concepts |
| `scripts/pkc_link.py` / `pkc_promote.py` | Graph edges and promotion |
| `templates/` | Normative skeletons |
| `sample-knowledge/` | Golden demo chain |

## Data flow: meeting capture

1. User pastes notes → `/pkc-capture-meeting`
2. Agent extracts title, date, attendees, decisions, actions
3. Writes `meetings/…` + `decisions/…` with typed edges
4. Optionally creates WikiTicket tasks via `bin/worklog` + TicketLinks
5. Updates catalogs + log

## Data flow: materialize

1. `bin/worklog fold` → JSON
2. `pkc_materialize.py` maps levels → Feature / TicketLink
3. Docs globs → Design / DecisionRecord / Specification / Release
4. Report created/updated/skipped
5. Respect `truth_state` barriers

## Non-goals (design)

- PKC does not publish wiki pages (WikiTicket plane)
- PKC does not own impact/query algorithms (OKF plane)
- No embedded database or network service required for core capture

## Evolution

See roadmap in [prd.md](./prd.md) §6. v0.1.0 delivers Phase 0–3 scaffolding + capture + materialize + promote/link + sample chain.
