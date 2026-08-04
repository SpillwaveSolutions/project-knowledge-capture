# PKC Roadmap & Idea Backlog

Status legend: **done** · **now** · **next** · **later** · **idea**

## Shipped (v0.1 → v0.2)

| Item | Status |
|------|--------|
| Dual-host plugin packaging (Claude + Grok) | **done** |
| Capture skills (meeting / experiment / discovery / decision) | **done** |
| Materialize WikiTicket fold + docs | **done** |
| Promote + typed link | **done** |
| Sample auth institutional-memory chain | **done** |
| Deterministic Python helpers | **done** |
| Unit tests | **done** |
| Progressive disclosure packer (`pkc_pack`) | **done** (v0.2) |
| Bundle validate (`pkc_validate`) | **done** (v0.2) |
| Action-item → TicketLink bridge (dry-run / apply) | **done** (v0.2) |
| Post-edit curate hook | **done** (v0.2) |
| CI workflow | **done** (v0.2) |
| `/pkc-context` skill | **done** (v0.2) |
| Doctor + conflicts + thin features | **done** (v0.3) |
| Assumption + Question types | **done** (v0.3) |
| Stale / re-verify | **done** (v0.3) |
| Transcript + PR capture | **done** (v0.3) |
| Scrub secrets/PII | **done** (v0.3) |
| Tiny packs + mermaid | **done** (v0.3) |
| Config JSON Schema | **done** (v0.3) |
| okf-plugin CI interop job | **done** (v0.3) |
| Full-text search | **done** (v0.4) |
| Weekly digest + verify queue | **done** (v0.4) |
| Release notes generator | **done** (v0.4) |
| Slack/Discord thread capture | **done** (v0.4) |
| Multi-repo federation | **done** (v0.4) |
| ADR import | **done** (v0.4) |

## Next (v0.3)

1. **Golden pack committed** under `sample-knowledge/packs/` + assert stable node set in CI  
2. **okf-plugin optional job** in CI (checkout okf-plugin, run `okf-graph.py validate/pack/impact` when available)  
3. **Meeting transcript modes** — timestamps, speaker labels, auto-summarize sections  
4. **Config schema** — JSON Schema for `.pkc/config.yml` + `pkc_common load_config` validation  
5. **Incremental materialize** — fingerprint worklog items; skip unchanged ULIDs without rewrite  
6. **`pkc doctor`** — one command: bundle health + missing catalogs + orphan concepts + broken links  

## Later (v0.4+)

| Theme | Ideas |
|-------|--------|
| **Capture UX** | `/pkc-capture-thread` for Slack/Discord paste; email → Discovery; PR description → CodeChange |
| **Voice / meeting bots** | Ingest Granola / Fireflies / Otter export JSON |
| **Code intelligence** | Map `CodeChange` to file globs; link packages via import graph hints |
| **Agent runtime** | Auto-inject `pkc_pack` into agent system prompts when Feature ULID/path detected |
| **Quality** | Stale detection (`stale_after`), “needs verification” queue, weekly knowledge digest |
| **Search** | Full-text index over concepts (ripgrep wrapper or tiny SQLite FTS — still Git source of truth) |
| **Viz** | Mermaid export of Meeting→Decision→Feature chains; HTML graph page in preview |
| **Multi-repo** | Federated knowledge roots (read-only remotes) with `maps_to` across repos |
| **Security** | Redaction profiles for secrets in pasted meeting notes before write |
| **i18n** | Locale-neutral frontmatter; body language tag |

## Brainstorm — things the PRD may have under-specified

### Capture & cognition
- **Assumption log** — first-class `Assumption` type (weaker than Decision; promote when validated)
- **Open questions** — `Question` concepts that block Features until answered
- **Confidence decay** — Discoveries auto-flag after N days without re-verify
- **Conflict detection** — two DecisionRecords that `decides` the same Feature with incompatible status
- **Decision supersession wizard** — guided `supersedes` + truth_state archive

### Work & delivery
- **Sprint/iteration nodes** — lightweight timeboxes linking Features without replacing WikiTicket milestones
- **Release notes generator** — from `lands_in` / `released_in` edges
- **Risk register** — `Risk` type linked to Features (`mitigates` / `exposes`)
- **Acceptance criteria as concepts** — atomic `Acceptance` nodes with `verified_by`

### Agent ergonomics (ADHD / focus friendly)
- **One-screen daily brief** — “what decisions touch files I changed this week”
- **Tiny packs by default** — 1 hop + max 8 nodes for mobile/chat; escalate on demand
- **Checklists in skills** — numbered, completable, no walls of prose
- **“Why is this here?” button** — pack always leads with originating Meeting/Decision

### Interop
- **GitHub Projects / Linear adapters** as skills (not hard-coded) following WikiTicket’s pattern
- **ADR tools import** — MADR / adr-tools directory → DecisionRecords
- **Notion/Docs export** — one-way publish *from* OKF (WikiTicket remains wiki plane)
- **MCP server mode** — expose pack/validate/capture as tools for any MCP host

### Trust & compliance
- **Provenance chain export** for audits (Feature ← Decision ← Meeting + Experiment)
- **PII scrubber** on capture
- **Signed knowledge** — optional git notes / sigstore for verified:true

### Non-goals to keep resisting
- Becoming a general notes app
- Owning work *status* (WikiTicket stays SoT)
- Replacing OKF graph algorithms
- Multiplayer real-time collab server

## Suggested sequencing

```text
v0.2  pack + validate + action items + CI + hook     ← this release
v0.3  doctor + okf CI job + config schema + golden packs
v0.4  transcript/PR capture + conflict detection + mermaid viz
v0.5  agent auto-context injection + stale/digest + search
```

## How to contribute an idea

Open an issue with:
- **Problem** (one sentence)
- **Who hurts** (human / agent / both)
- **Smallest wedge** (skill? script? template?)
- **Non-goal** (what we must not become)
