# Project Knowledge Capture (PKC)

**Continuous capture and materialization** of meetings, experiments, discoveries, decisions, and WikiTicket work into a durable [OKF](https://github.com/SpillwaveSolutions/okf-plugin) knowledge graph.

Works in **Claude Code** and **Grok Build** (zero-config: Grok Build reads Claude plugins natively).

| | |
|---|---|
| **Plugin name** | `project-knowledge-capture` |
| **Repo** | [SpillwaveSolutions/project-knowledge-capture](https://github.com/SpillwaveSolutions/project-knowledge-capture) |
| **Version** | 0.5.0 |
| **License** | MIT |

## Why PKC

Software projects generate reasoning that disappears: meeting notes, spike results, discovery findings, and the *why* behind designs. PKC turns that into **Git-native OKF concepts** so agents and humans get institutional memory with impact analysis and progressive disclosure.

| System | Role | Repository |
|--------|------|------------|
| **OKF Plugin** | Graph format + impact / query / validate | [okf-plugin](https://github.com/SpillwaveSolutions/okf-plugin) |
| **WikiTicket SDD** | Event-sourced work + wiki publishing | [wiki_ticket_sdd](https://github.com/SpillwaveSolutions/wiki_ticket_sdd) |
| **PKC (this plugin)** | Capture + materialization layer | this repo |

## Install

### Claude Code

```bash
claude plugin marketplace add SpillwaveSolutions/project-knowledge-capture
claude plugin install project-knowledge-capture@pkc-plugin-marketplace
```

### Grok Build

Grok Build discovers Claude-compatible plugins automatically — **no separate Grok-only config required**.

### Recommended companions

```bash
claude plugin marketplace add SpillwaveSolutions/okf-plugin
claude plugin install okf-graph-eng@okf-plugin-marketplace
```

## Quick start

1. `/pkc-init` — scaffold `knowledge/`
2. `/pkc-capture-meeting` — paste notes → Meeting + DecisionRecords
3. `/pkc-context features/…` — progressive disclosure pack for a Feature
4. `/pkc-materialize` — sync WikiTicket fold into OKF
5. Run tests: `python3 tests/test_pkc.py`

```bash
python3 scripts/pkc_validate.py --bundle sample-knowledge
python3 scripts/pkc_pack.py features/user-authentication.md --bundle sample-knowledge --hops 2
python3 scripts/pkc_action_items.py meetings/2026-08-03-auth-design.md --bundle sample-knowledge
```

## Skills & commands

| Skill / command | Purpose |
|-----------------|---------|
| `pkc-init` | Scaffold knowledge catalogs |
| `pkc-capture-meeting` | Meeting → decisions (+ action items) |
| `pkc-capture-experiment` | Spike / experiment write-up |
| `pkc-capture-discovery` | Research / scan findings |
| `pkc-capture-decision` | Lightweight ADR |
| `pkc-materialize` | WikiTicket fold + docs → OKF |
| `pkc-promote` | Informal → Feature / Requirement / ADR |
| `pkc-link` | Typed edges |
| `pkc-context` | Progressive disclosure pack (`--tiny`, mermaid) |
| `pkc-doctor` | Bundle health: conflicts, thin features, stale |
| `pkc-capture-assumption` | Working hypothesis (weaker than ADR) |
| `pkc-capture-question` | Open question that may block a Feature |
| `pkc-capture-transcript` | Fireflies/Otter/Granola/plain → Meeting |
| `pkc-capture-pr` | GitHub PR → CodeChange |
| `pkc-import-adr` | Import MADR/adr-tools ADRs |
| `pkc-federate` | Multi-repo federation |
| `pkc-capture-thread` | Slack/Discord paste capture |
| `pkc-release-notes` | Release notes from graph edges |
| `pkc-digest` | Weekly brief + verification queue |
| `pkc-search` | Full-text search over concepts |

### Agent

- **knowledge-capturer** — capture, materialization, provenance

### Hooks

Post-edit curation refreshes catalog indexes and runs a light validate when you edit knowledge Markdown.

## Scripts

| Script | Role |
|--------|------|
| `pkc_common.py` | Frontmatter, catalogs, bundle init |
| `pkc_capture.py` | Meeting / experiment / discovery / decision |
| `pkc_materialize.py` | Worklog fold + docs |
| `pkc_link.py` / `pkc_promote.py` | Edges + promotion |
| `pkc_pack.py` | Context packs (2-hop default) |
| `pkc_validate.py` | Structure + links |
| `pkc_action_items.py` | Meeting actions → TicketLink / worklog |
| `pkc-curate.sh` | Post-edit hook helper |
| `pkc_doctor.py` | One-screen health check |
| `pkc_scrub.py` | Secret/PII redaction |
| `pkc_transcript.py` | Transcript normalizer |
| `pkc_pr_capture.py` | PR → CodeChange |

## Sample knowledge

[`sample-knowledge/`](./sample-knowledge/) — auth chain:

**Discovery → Experiment → Meeting → Decision → Feature → Design → CodeChange → Release**

Plus a `Risk` the decision mitigates and an `Acceptance` criterion the PR verifies.

Golden pack: [`sample-knowledge/packs/user-authentication-pack.md`](./sample-knowledge/packs/user-authentication-pack.md)

## Docs

- [PRD](./docs/prd.md) · [Design](./docs/design.md) · [Integration](./docs/integration-okf-wikiticket.md)
- [Typed edges](./docs/typed-edges.md) · [Vision & brainstorm](./docs/vision.md)
- [Roadmap](./docs/roadmap.md) — generated from `.work/` by `bin/worklog roadmap-render`; edit work items, not the file

## Config

See [`.pkc/config.example.yml`](./.pkc/config.example.yml).

## License

MIT — see [LICENSE](./LICENSE).
