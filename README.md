# Project Knowledge Capture (PKC)

**Continuous capture and materialization** of meetings, experiments, discoveries, decisions, and WikiTicket work into a durable [OKF](https://github.com/SpillwaveSolutions/okf-plugin) knowledge graph.

Works in **Claude Code** and **Grok Build** (zero-config: Grok Build reads Claude plugins natively).

| | |
|---|---|
| **Plugin name** | `project-knowledge-capture` |
| **Repo** | [SpillwaveSolutions/project-knowledge-capture](https://github.com/SpillwaveSolutions/project-knowledge-capture) |
| **Version** | 0.1.0 |
| **License** | MIT |

## Why PKC

Software projects generate reasoning that disappears: meeting notes, spike results, discovery findings, and the *why* behind designs. PKC turns that into **Git-native OKF concepts** so agents and humans get institutional memory with impact analysis and progressive disclosure.

PKC sits between two systems it does **not** replace:

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

# Or local path
claude plugin marketplace add /path/to/project-knowledge-capture
claude plugin install project-knowledge-capture@pkc-plugin-marketplace
```

### Grok Build

Grok Build discovers Claude-compatible plugins automatically — **no separate Grok-only config required**. Optional identity pin: `.grok-plugin/marketplace.json`.

### Recommended companions

```bash
# Graph tooling (impact, pack, validate)
claude plugin marketplace add SpillwaveSolutions/okf-plugin
claude plugin install okf-graph-eng@okf-plugin-marketplace

# Work execution (optional bridge)
# install wiki_ticket_sdd per its README
```

## Quick start

1. **Init** a knowledge bundle in your project:
   - Slash: `/pkc-init`
   - Or: `python3 scripts/pkc_common.py init-bundle --repo . --bundle knowledge`
2. **Capture** a meeting: `/pkc-capture-meeting` (paste notes)
3. **Materialize** WikiTicket work: `/pkc-materialize`
4. **Link** concepts: `/pkc-link`
5. **Query context** with okf-plugin: pack a Feature at 2 hops

Try the included sample chain:

```bash
# Auth institutional-memory demo
ls sample-knowledge/features/user-authentication.md
python3 tests/test_pkc.py
```

## Skills & commands

| Skill / command | Purpose |
|-----------------|---------|
| `pkc-init` · `/pkc-init` | Scaffold knowledge catalogs |
| `pkc-capture-meeting` · `/pkc-capture-meeting` | Meeting → decisions (+ optional tickets) |
| `pkc-capture-experiment` · `/pkc-capture-experiment` | Spike / experiment write-up |
| `pkc-capture-discovery` · `/pkc-capture-discovery` | Research / scan findings |
| `pkc-capture-decision` · `/pkc-capture-decision` | Lightweight ADR |
| `pkc-materialize` · `/pkc-materialize` | WikiTicket fold + docs → OKF |
| `pkc-promote` · `/pkc-promote` | Informal → Feature / Requirement / ADR |
| `pkc-link` · `/pkc-link` | Typed edges |

### Agent

- **knowledge-capturer** — specialist for capture, materialization, and provenance

## Concept types

| Type | Directory |
|------|-----------|
| Meeting | `meetings/` |
| Experiment | `experiments/` |
| Discovery | `discoveries/` |
| DecisionRecord | `decisions/` |
| Feature | `features/` |
| Requirement | `requirements/` |
| Specification | `specs/` |
| Design | `designs/` |
| Release | `releases/` |
| CodeChange | `code/` |
| Package / Module | `packages/` |
| TicketLink | `tickets/` |

## Typed edges (PKC extensions)

`satisfies` · `implements` · `designed_by` · `decides` · `informs` · `discovered_in` · `originates_from` · `lands_in` · `released_in` · `tracks` · `maps_to` · `verified_by`  
(+ OKF standards: `depends_on`, `related_to`, `supersedes`, …)

## Deterministic scripts

```bash
python3 scripts/pkc_common.py init-bundle --repo . --bundle knowledge
python3 scripts/pkc_capture.py meeting --title "…" --date 2026-08-03 --notes-file notes.md --decision "…"
bin/worklog fold | python3 scripts/pkc_materialize.py --repo . --from-docs
python3 scripts/pkc_link.py decisions/x.md /features/y.md --rel decides
python3 scripts/pkc_promote.py discoveries/z.md --to Feature
python3 tests/test_pkc.py
```

## Configuration

See [`.pkc/config.example.yml`](./.pkc/config.example.yml). May also live under `pkc:` in `.work/config.yml`.

## Sample knowledge

[`sample-knowledge/`](./sample-knowledge/) is a self-describing OKF bundle:

**Discovery → Experiment → Meeting → Decision → Feature → Design → CodeChange → Release**

Open [`sample-knowledge/features/user-authentication.md`](./sample-knowledge/features/user-authentication.md) and walk the links.

## Docs

- [PRD / Spec](./docs/prd.md)
- [Design](./docs/design.md)
- [Integration with OKF + WikiTicket](./docs/integration-okf-wikiticket.md)
- [Typed edges reference](./docs/typed-edges.md)

## Dual-host packaging

Same pattern as okf-plugin:

- `.claude-plugin/plugin.json` + `marketplace.json` — Claude Code
- `.grok-plugin/marketplace.json` — optional Grok identity pin
- Skills, agents, commands load on both hosts with zero extra config

## Non-goals

- Not a replacement for WikiTicket work status
- Not a replacement for OKF graph tooling
- Not a general CRM / notes app
- No hard-coded per-wiki adapters

## License

MIT — see [LICENSE](./LICENSE).
