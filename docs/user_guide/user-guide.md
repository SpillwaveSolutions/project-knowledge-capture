---
wiki_key: guide/user-guide
doc_type: guide
truth_state: current
title: User Guide
slug: user-guide
---

# User Guide

Project Knowledge Capture turns the reasoning behind your work — meetings, spikes, research, decisions — into a knowledge graph made of ordinary Markdown files in your repo. No server, no database, no account. Git is the storage.

This guide covers PKC **v0.4.1**.

## Install

### Claude Code

```bash
claude plugin marketplace add SpillwaveSolutions/project-knowledge-capture
claude plugin install project-knowledge-capture@pkc-plugin-marketplace
```

### Grok Build

Nothing extra. Grok Build reads Claude-compatible plugins natively.

### Recommended companion

okf-plugin adds graph algorithms (impact analysis, traversal). PKC works without it, but degrades to writing files without validation:

```bash
claude plugin marketplace add SpillwaveSolutions/okf-plugin
claude plugin install okf-graph-eng@okf-plugin-marketplace
```

## First five minutes

```
/pkc-init
```

Scaffolds `knowledge/` with an index, a change log, and a catalog directory per concept type. Safe to re-run.

Then paste some meeting notes and run:

```
/pkc-capture-meeting
```

You get a `Meeting` concept, a separate `DecisionRecord` for each decision found, typed links between them, refreshed catalog indexes, and one line in `log.md`. Review the diff before committing — it is meant to be read.

## The commands

### Capture

| Command | Use when |
|---|---|
| `/pkc-capture-meeting` | You have meeting or standup notes |
| `/pkc-capture-experiment` | A spike or experiment finished; you have a hypothesis, result, conclusion |
| `/pkc-capture-discovery` | Research or a competitive scan produced findings |
| `/pkc-capture-decision` | You want a lightweight ADR without a meeting behind it |
| `/pkc-capture-assumption` | A working hypothesis you are proceeding on but have not proven |
| `/pkc-capture-question` | An open question that blocks a feature until answered |
| `pkc_capture.py risk` | Something that could go wrong, and what holds it back |
| `pkc_capture.py acceptance` | One checkable condition for calling a feature done |

Assumptions and questions matter more than they look. They are the two things teams carry in their heads and lose when someone leaves.

### Ingest

| Command | Accepts |
|---|---|
| `/pkc-capture-transcript` | Fireflies, Otter, Granola exports, or plain text with speaker labels |
| `/pkc-capture-thread` | A pasted Slack or Discord thread |
| `/pkc-capture-pr` | A GitHub PR → `CodeChange` concept |
| `/pkc-import-adr` | An existing MADR or adr-tools directory |

Every ingest path scrubs secrets and PII **before** anything is written. See [Privacy](#privacy).

### Use what you captured

| Command | Gives you |
|---|---|
| `/pkc-context <concept>` | A progressive-disclosure pack: the concept plus its neighborhood |
| `/pkc-search <query>` | Full-text search across concepts |
| `/pkc-digest` | Weekly brief plus a needs-verification queue |
| `/pkc-doctor` | Bundle health: conflicts, thin features, stale concepts, broken links |
| `/pkc-release-notes` | Release notes derived from graph edges |

### Shape the graph

| Command | Does |
|---|---|
| `/pkc-link` | Adds a typed edge between two concepts |
| `/pkc-promote` | Turns an informal concept into a Feature, Requirement, or ADR |
| `/pkc-materialize` | Syncs WikiTicket work items into the graph |
| `/pkc-federate` | Adds a read-only knowledge root from another repo |

## Context packs

A pack is the answer to "what do I need to know about this thing?" It walks typed edges outward from a concept and stops before it floods your context.

```bash
python3 scripts/pkc_pack.py features/user-authentication.md --bundle knowledge --hops 2
```

Defaults: 2 hops, about 20 nodes. For chat or mobile, use `--tiny` — 1 hop, at most 8 nodes. Add `--mermaid` for a diagram, `--json` for machine-readable output.

Start tiny and escalate. A pack you actually read beats a complete one you skim.

## Concept types

| Type | Directory | Holds |
|---|---|---|
| Meeting | `meetings/` | What was discussed and who was there |
| Experiment | `experiments/` | Hypothesis, result, conclusion |
| Discovery | `discoveries/` | Research findings, with a confidence level |
| DecisionRecord | `decisions/` | A decision, its context, and its consequences |
| Assumption | `assumptions/` | A working hypothesis, weaker than a decision |
| Question | `questions/` | An open question that may block work |
| Feature / Requirement | `features/`, `requirements/` | Formalized work |
| Specification / Design | `specs/`, `designs/` | Plans and designs |
| CodeChange / Release | `code/`, `releases/` | What shipped |
| Risk | `risks/` | What could go wrong, with a severity |
| Acceptance | `acceptance/` | One atomic condition that decides whether a Feature is done |
| TicketLink | `tickets/` | A bridge to a work item; never the source of truth for status |

Every concept is Markdown with YAML frontmatter. Open one and read it — that is the whole format.

## Typed edges

Concepts connect with named relationships, not bare links. A decision `decides` a feature; it `originates_from` a meeting; an experiment `informs` a decision.

This is what makes packs and impact analysis work: `/pkc-context` on a feature can surface the meeting where it was decided, three hops back.

Rule: **never invent an edge.** If the source material does not state the relationship, do not record it. A wrong edge is worse than a missing one, because everything downstream trusts it.

See `docs/typed-edges.md` for the full vocabulary.

## Configuration

Optional. Copy `.pkc/config.example.yml` to `.pkc/config.yml` and edit:

```yaml
pkc:
  knowledge_root: knowledge      # where the bundle lives
  stale_days: 90                 # when a Discovery needs re-verification
  pack:
    default_hops: 2
    default_max_nodes: 20
    tiny_hops: 1
    tiny_max_nodes: 8
  scrub:
    secrets: true
    pii: true
  bridge:
    wikiticket: true
    worklog_bin: bin/worklog
```

Every value has a working default. The JSON Schema is at `.pkc/config.schema.json`.

## Privacy

`scrub_text()` runs over pasted content before it is written. It redacts OpenAI-style keys, GitHub tokens, Slack tokens, AWS access keys, Google API keys, PEM private key blocks, bearer tokens, email addresses, phone numbers, and US SSNs.

This matters because captured content goes into Git history, where removing it later means rewriting history. Scrubbing is on by default; leave it on.

To scrub something by hand:

```bash
python3 scripts/pkc_scrub.py --file notes.txt
```

## WikiTicket integration

If your repo uses [WikiTicket SDD](https://github.com/SpillwaveSolutions/wiki_ticket_sdd), PKC materializes work items into the graph:

```bash
bin/worklog fold | python3 scripts/pkc_materialize.py --repo . --bundle knowledge
```

Epics and stories become `Feature` concepts; every item gets a `TicketLink`. Re-running is cheap: since v0.4.1, unchanged items are skipped by fingerprint before anything is rendered.

**PKC never owns work status.** WikiTicket does. PKC mirrors it. Never hand-edit `.work/*.jsonl`.

## Health checks

```bash
python3 scripts/pkc_doctor.py --bundle knowledge      # one-screen health
python3 scripts/pkc_validate.py --bundle knowledge    # structure and links
```

Doctor reports conflicting decisions, features with no supporting concepts, stale discoveries, unvalidated assumptions, and open questions blocking features. Run it weekly; it is the difference between a graph and a pile of files.

## Troubleshooting

**Commands write to the wrong directory.** Resolution order is `--bundle` → `.pkc/config.yml` → the first of `knowledge/`, `sample-knowledge/`, `.okf/` that has an `index.md`. If you have both `knowledge/` and `sample-knowledge/`, the former wins. Pass `--bundle` to be certain.

**Re-capturing created a duplicate.** Paths derive from a slug of the title (plus date, for meetings). A changed title produces a new file. Rename the old one or edit the title to match.

**A concept will not update.** Check its `truth_state`. Files marked `snapshot`, `superseded`, or `archived` are protected from routine writes by design.

**Validation complains about a link.** Targets must be absolute in-bundle paths: `/decisions/foo.md`, not `../decisions/foo.md`.

## Learn by reading

`sample-knowledge/` is a complete worked example: Discovery → Experiment → Meeting → Decision → Feature → Design → CodeChange → Release, all linked. Start at `sample-knowledge/packs/user-authentication-pack.md` to see what a good pack looks like.
