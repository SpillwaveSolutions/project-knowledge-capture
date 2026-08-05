# PKC Vision & Idea Backlog

Themes, unscheduled ideas, and the lines we refuse to cross.

> **Scheduled work is not here.** Planned items live in [`docs/roadmap.md`](./roadmap.md), which is **generated** from `.work/*.jsonl` by `bin/worklog roadmap-render`. To change the schedule, change the work items — never edit the roadmap or this file's ideas into dates.
>
> Shipped history lives in [`CHANGELOG.md`](../CHANGELOG.md).

## Open themes

Candidates that have earned a name but not yet a milestone. Promoting one means filing it via `bin/worklog add`, not editing this list into a plan.

### Quality & agent ergonomics

- **Incremental materialize** — fingerprint worklog ULIDs; skip unchanged items without rewriting the file
- **Confidence decay** — Discoveries auto-flag for re-verification after N days
- **Decision supersession wizard** — guided `supersedes` + `truth_state` archive
- **Agent auto-inject** — pack the graph into agent context when a Feature path or ULID is detected
- **Daily brief** — "decisions that touch files I changed this week"
- **Golden pack stable-node assert** — the pack exists in CI; the node set is not pinned

### Capture & delivery

- **Email → Discovery**
- **Sprint / iteration nodes** — lightweight timeboxes linking Features, without replacing WikiTicket milestones
- **Risk register** — `Risk` type with `mitigates` / `exposes` edges
- **Acceptance criteria as concepts** — atomic nodes with `verified_by`
- **Code intelligence** — map `CodeChange` to file globs and packages via import-graph hints

### Interop

- **GitHub Projects / Linear adapters** — as skills, following WikiTicket's adapter pattern, never hard-coded
- **Notion / Docs export** — one-way publish *from* OKF (WikiTicket remains the wiki plane)
- **MCP server mode** — expose pack / validate / capture as tools for any MCP host

### Trust & compliance

- **Provenance chain export** for audits (Feature ← Decision ← Meeting + Experiment)
- **Signed knowledge** — optional git notes / sigstore for `verified: true`
- **i18n** — locale-neutral frontmatter; body language tag

## Brainstorm

Unscheduled and unowned. Shipped ideas are struck from this list as they land — check `CHANGELOG.md` for what made it.

**Capture & cognition** — confidence decay · decision supersession wizard · richer conflict detection

**Work & delivery** — sprint nodes · risk register · acceptance criteria

**Agent / focus-friendly** — one-screen daily brief · skill checklists that complete · "why is this here?" (packs always lead with the originating Meeting or Decision)

**Interop** — Linear / GitHub Projects · Notion export · MCP server mode

**Trust** — provenance chain export · signed knowledge

## Non-goals

Things PKC must not become, however reasonable each step looks in isolation:

- **A general notes app.** PKC captures project *reasoning*, not everything a person types.
- **The source of truth for work status.** WikiTicket owns status. PKC mirrors it into `TicketLink` nodes and never writes back.
- **A reimplementation of OKF graph algorithms.** Impact, query, and traversal belong to okf-plugin. PKC produces valid concepts and calls out.
- **A multiplayer realtime collaboration server.** Git is the database. Merge conflicts are a feature.

## How to add an idea

Open an issue with four lines:

- **Problem** — one sentence
- **Who hurts** — human, agent, or both
- **Smallest wedge** — a skill? a script? a template?
- **Non-goal** — what we must not become while solving it

Accepted ideas become work items (`bin/worklog add`) and appear in the generated roadmap. Ideas that are interesting but not next land in the brainstorm list above.
