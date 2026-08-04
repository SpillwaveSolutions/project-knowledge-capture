Project Knowledge Capture (PKC)
Full Product Requirements Document, Specification & Design
Status: Draft for implementation handoff Audience: Grok Build / Claude Code agents, human implementers Date: 2026-08-03 Related repositories:
	•	SpillwaveSolutions/okf-plugin — OKF Graph Engineering plugin (knowledge + agent graph substrate)
	•	SpillwaveSolutions/wiki_ticket_sdd — WikiTicket SDD (event-sourced worklog + wiki publishing)
	•	New repository to create: SpillwaveSolutions/project-knowledge-capture (or pkc-plugin)

1. Vision
Software projects generate large amounts of reasoning that currently disappears: meeting notes, experiment results, discovery findings, ad-hoc decisions, and the rationale behind designs and features. Later, when agents or humans need to change something, they lack the institutional memory that produced the current state.
Project Knowledge Capture (PKC) is the continuous capture and materialization layer that turns both informal knowledge and structured work data into a durable, queryable OKF knowledge graph.
It sits between two existing systems:
System
Role
Repository
OKF Plugin
Format + tooling for knowledge & agent graphs (impact analysis, progressive disclosure, validation, typed edges)
okf-plugin
WikiTicket SDD
Event-sourced work execution, plans, tickets, releases, wiki publishing
wiki_ticket_sdd
Project Knowledge Capture (PKC)
Ingestion + materialization layer that uses OKF format and can pull from WikiTicket
New
Core principle: PKC uses the OKF format as its native storage. It can ingest data from WikiTicket (and from meetings, experiments, discovery sessions) and store everything as first-class OKF concepts. The resulting knowledge base becomes the project’s long-term institutional memory.

2. Goals
	1	Make every important decision, experiment, meeting, and discovery durable and linkable.
	2	Materialize WikiTicket work data (tickets, plans, designs, ADRs, releases) into the same OKF knowledge graph so it is impact-analyzable and progressively disclosable.
	3	Provide simple capture skills that turn messy real-world inputs into structured OKF concepts.
	4	Keep the three systems loosely coupled but deeply interoperable.
	5	Enable agents to automatically receive relevant historical context (meetings that decided X, experiments that informed Y, designs that shaped Z) when working on a Feature or code change.
	6	Remain fully Git-native, dual-host (Claude Code + Grok Build), and reviewable via ordinary PRs.
Non-Goals
	•	Replacing WikiTicket as the system of record for work status and event history.
	•	Replacing OKF as the graph tooling substrate.
	•	Building a full CRM, note-taking app, or general knowledge management system.
	•	Hard-coding per-wiki or per-tracker adapters (follow WikiTicket’s skill-based, system-agnostic pattern).

3. Product Requirements
3.1 Functional Requirements
FR1 – Capture from informal sources
	•	Support capture of Meeting notes → Meeting concept + extracted DecisionRecords + optional action items.
	•	Support capture of Experiment / spike results → Experiment concept.
	•	Support capture of Discovery / research / scanning → Discovery concept.
	•	Support lightweight Decision capture that links into existing Features, Designs, or Requirements.
FR2 – Materialize WikiTicket data
	•	Read from a WikiTicket worklog fold (.work/todo.jsonl + derived state) and/or from docs/ artifacts.
	•	Emit or update corresponding OKF concepts under a configurable knowledge root (knowledge/ or .okf/).
	•	Map:
	◦	Work items → Feature / Requirement / TicketLink
	◦	Plans → Specification or linked Features
	◦	Design docs & code walkthroughs → Design
	◦	ADRs → DecisionRecord
	◦	Releases → Release
	◦	Significant PRs / changes → CodeChange
FR3 – Use OKF format exclusively
	•	All stored knowledge is valid OKF concept Markdown (YAML frontmatter + body + absolute Markdown links + optional typed links array).
	•	Compatible with existing okf-graph.py, okf-impact, okf-query, okf-validate from okf-plugin.
FR4 – Typed edges for traceability
	•	Maintain a rich set of relation types so impact analysis and progressive disclosure work across formal and informal knowledge.
	•	Required new or extended relations: satisfies, implements, designed_by, decides, informs, discovered_in, lands_in, released_in, originates_from, tracks, maps_to.
FR5 – Progressive disclosure & impact
	•	Concepts produced by PKC must participate in OKF impact analysis and context packs.
	•	An agent working on a Feature must be able to receive the relevant Meetings, Experiments, DecisionRecords, and Designs that shaped it.
FR6 – Optional WikiTicket bridge
	•	When action items are extracted from a Meeting, PKC may create WikiTicket work items (via worklog CLI or skill) and corresponding TicketLink concepts.
	•	PKC never becomes the source of truth for work status.
FR7 – Catalogs and directory layout
	•	Support (and preferably seed) these catalogs under the knowledge root:
	◦	meetings/
	◦	experiments/
	◦	discoveries/
	◦	decisions/
	◦	features/
	◦	requirements/
	◦	specs/
	◦	designs/
	◦	releases/
	◦	code/
	◦	packages/ (or modules/)
	◦	tickets/ (TicketLinks)
FR8 – Dual-host compatibility
	•	Ship as a Claude Code plugin that Grok Build can load with zero extra configuration (same pattern as okf-plugin).
3.2 Non-Functional Requirements
	•	All writes are ordinary Git files (Markdown). No hidden databases.
	•	Deterministic: same input + same fold produces the same concept files (modulo timestamps).
	•	Incremental: re-running materialization only updates changed concepts.
	•	Validation: concepts must pass okf-validate (or the Python fallback in okf-plugin).
	•	Frontmatter must remain compatible with both OKF conventions and, where useful, WikiTicket’s wiki_key / truth_state model.

4. Detailed Specification
4.1 Concept Type Catalog (PKC extensions to OKF)
PKC introduces or elevates the following types. All are free-form OKF type values (OKF has no central registry — see okf-plugin README and templates).
Type
Purpose
Typical directory
Meeting
Meeting notes, attendees, discussion, decisions extracted
meetings/
Experiment
Hypothesis, method, results, conclusion of a spike or experiment
experiments/
Discovery
Research, scanning, competitive analysis, user findings
discoveries/
DecisionRecord
ADR / decision (already exists in OKF; PKC strengthens usage)
decisions/
Requirement
Atomic need or constraint
requirements/
Specification
Grouped requirements or contracts
specs/
Feature
User- or system-facing capability
features/
Design
Design document or code walkthrough
designs/
Release
Version that ships a set of changes
releases/
CodeChange
PR, significant changeset
code/
Package / Module
Package or module documentation
packages/
TicketLink
Bridge to WikiTicket ULID or external tracker (already exists)
tickets/
4.2 Frontmatter Schema (common + type-specific)
Every concept must have at minimum:
---
type: 
title: Human readable title
description: One-line summary
tags: [tag1, tag2]
timestamp: 2026-08-03T20:00:00Z
status: active | proposed | accepted | shipped | deprecated | superseded
verified: true | false
# Optional but strongly recommended for interoperability
wiki_key: stable-key-for-this-concept
truth_state: current | snapshot | superseded | archived
# When originating from WikiTicket
worklog_id: 01J8X0M2QQ...          # ULID
external_id: "123"                 # GitHub issue/PR number etc.
external_system: github
links:
  - target: /features/auth.md
    rel: decides
  - target: /meetings/2026-07-15-auth-design.md
    rel: originates_from
---
Additional recommended fields by type:
	•	Meeting: date, attendees, duration_minutes
	•	Experiment: hypothesis, result, conclusion, related_code
	•	Discovery: source, confidence
	•	DecisionRecord: status (proposed|accepted|deprecated), classic ADR sections in body
	•	Feature / Requirement: priority, level (if mapped from WikiTicket taxonomy)
	•	Release: version, tag, date
	•	CodeChange: pr_number, branch, merged_at
	•	TicketLink: worklog_id (required), external_id, external_system
4.3 Typed Edges (extended set)
Building on the existing recommended relations in okf-plugin typed-edges.md:
rel
Direction (typical)
Meaning
depends_on
any → any
Existing
routes_to
Agent/Workflow → target
Existing
implements
CodeChange / Ticket → Feature or Design
Existing + strengthened
documents
Package/Design → code or Feature
Existing
uses
any → Tool/Capability
Existing
owns
Agent → concept
Existing
supersedes
newer → older
Existing
related_to
soft
Existing
tracks
TicketLink → work concept
Existing
maps_to
TicketLink → external
Existing
satisfies
Feature → Requirement
New
designed_by
Feature → Design
New
decides
DecisionRecord → Feature/Design/Requirement
New
informs
Experiment/Discovery → Feature/Design/Requirement
New
discovered_in
Finding → Discovery
New
originates_from
DecisionRecord → Meeting or Experiment
New
lands_in / released_in
CodeChange/Feature → Release
New
verified_by
Test/Acceptance → Feature
New
4.4 Capture Skills (PKC plugin surface)
Skill / Command
Input
Output
/pkc-capture-meeting
Meeting notes (paste, file, or transcript)
Meeting concept + extracted DecisionRecords + optional WikiTicket items + TicketLinks
/pkc-capture-experiment
Experiment write-up
Experiment concept + optional DecisionRecord + links
/pkc-capture-discovery
Research / scan notes
Discovery concept + links into Features/Requirements
/pkc-capture-decision
Short decision statement + context
DecisionRecord linked to existing concepts
/pkc-materialize
WikiTicket fold or specific ULIDs / docs
Batch of OKF concepts under knowledge root
/pkc-promote
Existing Discovery/Experiment/Meeting
Promote into formal Requirement, Feature, or ADR
/pkc-link
Two concept paths + rel
Add typed edge
All skills must:
	•	Write valid OKF Markdown.
	•	Use absolute paths in links (/features/...).
	•	Update or create catalog index.md files where appropriate.
	•	Be idempotent where possible (re-running on the same meeting notes updates rather than duplicates).
4.5 Materialization Rules (WikiTicket → PKC/OKF)
When /pkc-materialize runs against a WikiTicket project:
	1	Read .work/config.yml and the current fold of .work/todo.jsonl (via bin/worklog fold or equivalent).
	2	For each relevant entity produce or update an OKF file.
	3	Preserve wiki_key and truth_state when present so dual publishing remains possible.
	4	Create TicketLink nodes that point back to the original ULID.
	5	Respect truth_state: do not overwrite a snapshot or superseded concept with current data unless explicitly requested.
	6	Emit a short report of created/updated/skipped concepts.
Mapping table (normative):
WikiTicket source
OKF type(s) written
Work item (level=epic/story)
Feature + TicketLink
Work item (task/subtask)
TicketLink (and optionally linked to parent Feature)
Plan (docs/plans/*.md)
Specification or set of Features
Design / code walkthrough
Design
ADR
DecisionRecord
Release
Release
PR page / significant change
CodeChange
4.6 Directory Layout (recommended)
knowledge/                    # or .okf/ — configurable
├── index.md                  # OKF bundle root (okf_version, catalogs)
├── log.md
├── meetings/
│   ├── index.md
│   └── 2026-07-15-auth-design.md
├── experiments/
├── discoveries/
├── decisions/
├── features/
├── requirements/
├── specs/
├── designs/
├── releases/
├── code/
├── packages/
├── tickets/                  # TicketLink concepts
├── agents/                   # optional — can stay in main OKF bundle
├── workflows/
└── shared/
PKC may live inside an existing OKF bundle or own a dedicated knowledge root that the OKF tools can still operate on.
4.7 Configuration
Suggested section in a project-level config (can live in .work/config.yml or a new .pkc/config.yml):
pkc:
  enabled: true
  knowledge_root: knowledge          # or .okf
  okf_bundle: true                   # treat knowledge_root as full OKF bundle
  materialize:
    from_worklog: true
    from_docs: true
    include:
      - features
      - decisions
      - designs
      - releases
      - tickets
  capture:
    auto_create_ticketlinks: true
    default_meeting_dir: meetings
    default_experiment_dir: experiments
  bridge:
    wikiticket: true                 # allow creating work items
    worklog_bin: bin/worklog

5. Design
5.1 High-level Architecture
┌─────────────────────────────────────────────────────────────┐
│                     Human / Agent Activity                   │
│  (meetings, experiments, discovery, coding, planning)        │
└────────────────────────────┬────────────────────────────────┘
                             │
          ┌──────────────────┼──────────────────┐
          ▼                  ▼                  ▼
┌─────────────────┐  ┌──────────────┐  ┌─────────────────────┐
│ WikiTicket SDD  │  │ PKC Capture  │  │ Direct OKF authoring│
│ (worklog + docs)│  │ skills       │  │ (okf-author etc.)   │
└────────┬────────┘  └──────┬───────┘  └──────────┬──────────┘
         │                  │                     │
         │    materialize   │                     │
         └──────────►───────┼─────────────────────┘
                            ▼
                 ┌─────────────────────┐
                 │  OKF Knowledge Graph │
                 │  (Markdown + YAML)   │
                 │  managed by PKC +    │
                 │  okf-plugin tools    │
                 └─────────────────────┘
                            │
                            ▼
                 Impact / Query / Progressive
                 Disclosure / Validation
                 (okf-plugin)
5.2 Plugin Structure (new repository)
Recommended layout for SpillwaveSolutions/project-knowledge-capture:
project-knowledge-capture/
├── .claude-plugin/
│   └── plugin.json / marketplace.json
├── .grok-plugin/                  # optional identity pin
├── skills/
│   ├── pkc-capture-meeting/
│   ├── pkc-capture-experiment/
│   ├── pkc-capture-discovery/
│   ├── pkc-capture-decision/
│   ├── pkc-materialize/
│   ├── pkc-promote/
│   └── pkc-link/
├── commands/                      # thin slash wrappers
├── templates/                     # Meeting, Experiment, Discovery, Feature, …
├── scripts/                       # optional deterministic helpers
├── agents/                        # optional specialist “knowledge-capturer”
├── docs/
│   ├── design.md
│   ├── prd.md                     # this document or a rendered version
│   └── integration-okf-wikiticket.md
├── sample-knowledge/              # self-describing example bundle
├── AGENTS.md
├── CLAUDE.md
└── README.md
Follow the same dual-host packaging conventions used by okf-plugin.
5.3 Integration Contracts
With OKF Plugin
	•	PKC writes files that are valid OKF concepts.
	•	PKC may call or assume the presence of okf-graph.py, okf-validate, okf-impact, okf-query.
	•	New templates should be compatible with okf-author style.
	•	Typed edges must be understood by existing edge and impact tooling (unknown rel values are already allowed and only flagged as info).
With WikiTicket SDD
	•	Read-only consumption of the worklog fold and docs/ tree is the primary path.
	•	Optional write path: create work items for action items extracted from meetings (using bin/worklog or the ticket-sync skill patterns already present in WikiTicket).
	•	Respect WikiTicket’s wiki_key, truth_state, and four-axis taxonomy when materializing.
	•	Do not mutate .work/todo.jsonl except through the official CLI.
Publishing
	•	PKC itself does not publish to the wiki. WikiTicket’s existing wiki-publish skill and publish-manifest remain the publishing plane. Once concepts exist in the knowledge tree, WikiTicket (or a future extension) can choose to surface them.
5.4 Example End-to-End Flow
	1	Team holds a design meeting about authentication.
	2	Agent or human runs /pkc-capture-meeting with the notes.
	3	PKC writes:
	◦	knowledge/meetings/2026-08-03-auth-design.md (type: Meeting)
	◦	knowledge/decisions/use-jwt-for-session.md (type: DecisionRecord, originates_from the Meeting)
	◦	Optionally creates WikiTicket tasks for “Implement JWT middleware” and corresponding TicketLinks.
	4	Later a Feature is created or materialized: knowledge/features/user-authentication.md.
	5	The DecisionRecord and Meeting are linked via decides / originates_from.
	6	When an agent later works on the Feature, okf-query pack (or equivalent) can include the Meeting and DecisionRecord automatically.
	7	Impact analysis on the DecisionRecord surfaces the Feature and any CodeChanges that implemented it.
5.5 Template Skeletons (normative starting points)
Meeting
---
type: Meeting
title: Auth design discussion
description: Decided on JWT session approach
date: 2026-08-03
attendees: [rick, alice]
tags: [meeting, auth]
timestamp: 2026-08-03T18:00:00Z
status: active
verified: true
wiki_key: meeting-2026-08-03-auth
truth_state: current
links:
  - target: /decisions/use-jwt-for-session.md
    rel: decides
---
Experiment
---
type: Experiment
title: JWT vs session-cookie spike
hypothesis: JWT will simplify horizontal scaling
result: Both workable; JWT chosen for statelessness
conclusion: Proceed with JWT
tags: [experiment, auth]
timestamp: 2026-08-01T12:00:00Z
status: completed
verified: true
links:
  - target: /features/user-authentication.md
    rel: informs
  - target: /decisions/use-jwt-for-session.md
    rel: originates_from
---
DecisionRecord (extends existing OKF template)
---
type: DecisionRecord
title: Use JWT for session management
status: accepted
tags: [decision, adr, auth]
timestamp: 2026-08-03T19:00:00Z
verified: true
wiki_key: adr-jwt-session
truth_state: current
links:
  - target: /meetings/2026-08-03-auth-design.md
    rel: originates_from
  - target: /features/user-authentication.md
    rel: decides
  - target: /experiments/jwt-vs-cookie.md
    rel: informs
---

6. Implementation Roadmap (suggested)
Phase 0 – Repository & scaffolding
	•	Create SpillwaveSolutions/project-knowledge-capture.
	•	Dual-host plugin metadata (.claude-plugin, .grok-plugin).
	•	Basic README, AGENTS.md, CLAUDE.md.
	•	Sample knowledge bundle demonstrating Meeting → Decision → Feature chain.
Phase 1 – Core capture skills
	•	Implement /pkc-capture-meeting, /pkc-capture-experiment, /pkc-capture-discovery, /pkc-capture-decision.
	•	Ship templates for the new types.
	•	Write concepts into a configurable knowledge_root.
Phase 2 – Materialization from WikiTicket
	•	/pkc-materialize that reads worklog fold + key docs and emits OKF concepts.
	•	TicketLink generation.
	•	Idempotent update logic + report.
Phase 3 – Graph quality & promotion
	•	/pkc-promote and /pkc-link.
	•	Catalog index maintenance.
	•	Validation against OKF tools.
	•	Example progressive-disclosure packs that include Meetings/Experiments.
Phase 4 – Hardening & docs
	•	Integration guide referencing both upstream repos.
	•	End-to-end tests / golden knowledge bundles.
	•	Optional hooks (post-capture curation).

7. Success Criteria
	•	A Meeting can be captured and produces valid OKF concepts that appear in impact analysis.
	•	WikiTicket work items and designs can be materialized into the knowledge graph without manual rewriting.
	•	An agent requesting a context pack for a Feature receives related DecisionRecords, Meetings, and Experiments.
	•	All three plugins can be installed side-by-side in a Claude Code or Grok Build environment and interoperate.
	•	The knowledge tree remains ordinary Git-diffable Markdown.

8. References
	•	OKF Plugin: https://github.com/SpillwaveSolutions/okf-plugin (skills: okf-init-graph, okf-author, okf-impact, okf-query, okf-validate; sample-okf; typed-edges.md; DecisionRecord template)
	•	WikiTicket SDD: https://github.com/SpillwaveSolutions/wiki_ticket_sdd (worklog, four-axis taxonomy, schema/doc.schema.json, schema/entity.schema.json, wiki-publish skill, IA rendering, design docs & ADR handling)
	•	OKF concept model and progressive disclosure patterns as implemented in the okf-plugin sample and scripts.

End of PRD / Spec / Design
This document is intentionally detailed so it can be handed directly to Grok Build (or Claude Code) as the authoritative specification for implementing the Project Knowledge Capture plugin and its integration with the two existing systems.
