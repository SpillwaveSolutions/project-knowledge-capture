# Integration: PKC ↔ OKF ↔ WikiTicket

## With OKF Plugin

| Contract | Detail |
|----------|--------|
| Storage | PKC writes valid OKF concept Markdown |
| Types | Free-form; PKC elevates Meeting, Experiment, Discovery, Feature, … |
| Edges | Extended `rel` values; unknown rels allowed (info in validate) |
| Tools | May call `okf-graph.py` / `okf validate` / impact / pack when present |
| Bundle root | `knowledge/`, `.okf/`, or any dir with `okf_version` in `index.md` |

Install side-by-side:

```bash
claude plugin install okf-graph-eng@okf-plugin-marketplace
claude plugin install project-knowledge-capture@pkc-plugin-marketplace
```

Typical agent loop on a Feature:

```bash
python3 <okf-plugin>/scripts/okf-graph.py pack knowledge features/user-authentication.md --hops 2
python3 <okf-plugin>/scripts/okf-graph.py impact knowledge decisions/use-jwt-for-session.md
```

## With WikiTicket SDD

| Contract | Detail |
|----------|--------|
| Read path | `bin/worklog fold` + `docs/**` |
| Write path (optional) | Action items → `bin/worklog add` (never hand-edit jsonl) |
| Identity | Preserve `wiki_key`, `truth_state`, `worklog_id` |
| TicketLink | Bridge nodes under `tickets/` with `tracks` / `maps_to` |
| Publishing | Remains WikiTicket wiki-publish; PKC does not publish |

### Mapping table

| WikiTicket | OKF / PKC |
|------------|-----------|
| epic / story | Feature + TicketLink |
| task / subtask | TicketLink |
| plan docs | Specification |
| design / walkthrough | Design |
| ADR | DecisionRecord |
| release | Release |
| PR page | CodeChange |

### Materialize command

```bash
bin/worklog fold | python3 ${CLAUDE_PLUGIN_ROOT}/scripts/pkc_materialize.py \
  --repo . --bundle knowledge --from-docs
```

## Three-plugin coexistence

```text
.claude-plugin installs:
  okf-graph-eng          → graph ops
  project-knowledge-capture → capture + materialize
  (wiki_ticket_sdd)      → worklog + wiki
```

Shared conventions:

- Absolute Markdown links
- YAML frontmatter
- Git as the database
- `${CLAUDE_PLUGIN_ROOT}` for plugin-local scripts

## Failure modes & degradation

| Missing dependency | Behavior |
|--------------------|----------|
| No okf-plugin | Capture still works; skip validate/impact or crawl links manually |
| No WikiTicket | Capture skills work; materialize needs fold JSON or `--from-docs` only |
| No network | Fully offline; all local files |

## Sample interoperability demo

See `sample-knowledge/` in this repo — a complete Meeting → Decision → Feature chain ready for okf impact/pack once okf-plugin is available.
