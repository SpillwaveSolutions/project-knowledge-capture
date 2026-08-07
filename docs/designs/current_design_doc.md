---
wiki_key: design/current-design-doc
doc_type: design
truth_state: current
generated_at: 2026-08-06T18:42:39Z
tag: v0.4.1
git_hash: ddcf3c4b71829a6db0742c24a2f742f1d476fe82
branch: docs/user-guide-design-spec
roadmap: docs/roadmap.md
---

# Design Document — Project Knowledge Capture

## 1. Document overview

Generated from the repository at `ddcf3c4` (tag `v0.4.1`). Every code claim below cites a path and symbol. Sections of the standard template that do not apply to this system are listed in §14 with reasons, rather than filled with invented content.

## 2. Executive summary

PKC is a **plugin, not an application**. It ships agent procedures (skills), slash commands, an agent definition, hooks, and ~4,200 lines of dependency-free Python that turn project reasoning — meetings, experiments, discoveries, decisions — into an [OKF](https://github.com/SpillwaveSolutions/okf-plugin) knowledge graph stored as ordinary Markdown with YAML frontmatter.

There is no server, no database, and no build step. Git is the database. The unit of output is a Markdown file that a human can read in a PR diff.

Two hosts run the same tree: Claude Code (via `.claude-plugin/`) and Grok Build (via `.grok-plugin/`, which reads Claude-compatible plugins natively).

## 3. Requirements summary

From `docs/prd.md` and `docs/vision.md`, the system must:

1. Capture informal knowledge (meetings, spikes, research, decisions) without a separate app.
2. Materialize WikiTicket work items into the same graph, without owning their status.
3. Maintain typed edges so impact analysis and progressive disclosure work.
4. Stay Git-native and PR-reviewable.
5. Degrade gracefully when okf-plugin or WikiTicket is absent.

Explicit non-goals (`docs/vision.md`): a general notes app, owning work *status*, reimplementing OKF graph algorithms, realtime collaboration.

## 4. System context

```
 Human / agent activity
 (meetings, experiments, discovery, coding, planning)
        │
   ┌────┼────────────────┐
   ▼    ▼                ▼
WikiTicket   PKC capture   Direct OKF authoring
(bin/worklog) skills       (okf-author)
   │          │
   │ materialize
   └───►──────┤
              ▼
     OKF knowledge graph
     (Markdown + YAML, in Git)
              ▼
   Impact / query / progressive disclosure
   (okf-plugin)
```

Three plugins coexist. PKC is the capture and materialization layer; okf-plugin owns graph algorithms; WikiTicket owns work status and wiki publishing. Contracts are documented in `docs/integration-okf-wikiticket.md`.

## 5. High-level architecture

Four layers, each replaceable without touching the others:

| Layer | Location | Responsibility |
|---|---|---|
| Agent procedures | `skills/*/SKILL.md` (20) | Judgment: extract structure from free text, choose edge types |
| Command surface | `commands/*.md` (20) | Thin wrappers that invoke a skill with `$ARGUMENTS` |
| Deterministic core | `scripts/pkc_*.py` (18) | Paths, frontmatter, idempotency, catalogs, validation |
| Storage | A bundle directory of Markdown | The graph itself |

The split is deliberate and load-bearing: **anything deterministic belongs in Python**; the model is only trusted with judgment. A skill that writes Markdown directly instead of calling a script is a bug.

## 6. Architectural decisions

### 6.1 Zero runtime dependencies

`scripts/pkc_common.py` hand-rolls a YAML subset — `_parse_simple_yaml()` (lines 170–235) and `dump_frontmatter()` / `_dump_key()` (lines 303–339) — rather than importing PyYAML.

*Why:* the plugin must run on bare `python3` in any host, including sandboxes with no package installation. *Cost:* the parser handles the frontmatter subset only — nested maps, lists, inline `[a, b]` arrays, and scalar coercion. *Consequence:* a frontmatter construct the parser cannot express must be avoided, or the parser extended. Adding a dependency is not an option.

### 6.2 One write path

Every concept write funnels through `write_concept()` (`scripts/pkc_common.py`, lines 356–396). It owns four invariants the rest of the system assumes:

- **Merge** — existing frontmatter is preserved key-by-key, never clobbered.
- **`truth_state` barrier** — a file marked `snapshot`, `superseded`, or `archived` is skipped by a `current` write unless the caller passes `force`.
- **Three-way return** — `created` / `updated` / `skipped`. Identical content returns `skipped` without writing.
- **`stable_timestamp`** — preserves the original timestamp when the title is unchanged, so re-captures produce no diff churn.

Idempotency is not a feature bolted on top; it is this function's return value. CI asserts it directly (`.github/workflows/ci.yml`, "Materialize fixture idempotency" step, `grep -q "0 created"`).

### 6.3 Fingerprint-gated materialization *(new in v0.4.1)*

`item_fingerprint()` and `fingerprint_matches()` (`scripts/pkc_materialize.py`) hash only the worklog fields that reach rendered output — `FINGERPRINT_FIELDS`. A matching fingerprint short-circuits *before* the frontmatter dict and body string are constructed, so an unchanged item never reaches `write_concept()`.

*Tradeoff:* the fingerprint is stored in the concept's own frontmatter, so the check still reads the file. It avoids rendering and writing, not reading. A sidecar manifest would avoid the read too, at the cost of a second source of truth that can drift from the files.

*Sharp edge:* a field added to the rendered concept but not to `FINGERPRINT_FIELDS` will never trigger a re-render.

*Observability:* short-circuited items report `unchanged`; `write_concept()`'s byte-identical result reports `skipped`. Keeping them distinct is what makes the optimization verifiable from outside the process — an mtime check cannot tell them apart, because `write_concept()` declined to write in both cases even before fingerprints existed.

### 6.4 Bundle root resolution

`resolve_knowledge_root()` (`scripts/pkc_common.py`, lines 158–167) resolves in strict order: explicit `--bundle` → `.pkc/config.yml` `knowledge_root` → the first of `knowledge/`, `sample-knowledge/`, `.okf/` that contains an `index.md`.

*Consequence worth knowing:* creating a `knowledge/` directory in this repo would silently retarget every bare `--repo .` invocation away from `sample-knowledge/`. CI is insulated because every step passes `--bundle` explicitly.

## 7. Component inventory

| Script | Role |
|---|---|
| `pkc_common.py` | Frontmatter, catalogs, bundle init, scrubbing, fingerprints |
| `pkc_capture.py` | Meeting / experiment / discovery / decision / assumption / question |
| `pkc_materialize.py` | Worklog fold + docs → concepts |
| `pkc_link.py` / `pkc_promote.py` | Typed edges; informal → formal promotion |
| `pkc_pack.py` | Progressive-disclosure context packs |
| `pkc_validate.py` | Structure and link validation |
| `pkc_doctor.py` | One-screen bundle health check |
| `pkc_action_items.py` | Meeting actions → TicketLink / worklog |
| `pkc_scrub.py` | Secret and PII redaction |
| `pkc_transcript.py` / `pkc_thread.py` / `pkc_pr_capture.py` / `pkc_adr_import.py` | Ingestion |
| `pkc_search.py` / `pkc_digest.py` / `pkc_release_notes.py` / `pkc_federate.py` | Query and reporting |

Every script shares one CLI shape: `--repo <path>` (default `.`), optional `--bundle`, and usually `--json` for machine-readable output. CI asserts against the JSON, not the prose.

## 8. End-to-end workflows

### 8.1 Meeting capture

1. User pastes notes; `/pkc-capture-meeting` loads `skills/pkc-capture-meeting/SKILL.md`.
2. The agent extracts title, date, attendees, decisions, action items.
3. `pkc_capture.py meeting` writes `meetings/YYYY-MM-DD-<slug>.md` plus a `DecisionRecord` per decision, linked `decides` / `originates_from`.
4. Catalog indexes refresh; one line appends to `log.md`.
5. Optionally, action items become work items via `bin/worklog add` and `TicketLink` concepts.

Re-running on the same title and date **updates in place** — the path is derived from the slug, and `write_concept()` returns `skipped` when nothing changed.

### 8.2 Materialize

1. `bin/worklog fold` emits the work log as JSON.
2. `load_fold()` (`scripts/pkc_materialize.py`, lines 37–50) normalizes both a bare array and `{"items": [...]}`.
3. Epics and stories become `Feature` concepts; every item with a ULID also gets a `TicketLink`.
4. Unchanged items short-circuit on fingerprint (§6.3).
5. `truth_state` barriers are respected — a snapshot is never overwritten by a routine run.

### 8.3 Progressive disclosure

`pkc_pack.py` walks typed edges from a seed concept — 2 hops and ~20 nodes by default, 1 hop and ≤8 nodes with `--tiny`. The tiny bound exists for chat and mobile contexts and is asserted in CI.

## 9. Domain model

Concept types map to directories via `TYPE_TO_DIR` (`scripts/pkc_common.py`, lines 31–48); catalogs are enumerated in `CATALOGS`. Adding a type means touching, in order: `TYPE_TO_DIR` → `CATALOGS` → a template in `templates/` → the catalog case list in `scripts/pkc-curate.sh` → a sample under `sample-knowledge/`.

Edges are typed and stored twice on purpose: `links: [{target, rel}]` in frontmatter for machines, and a Markdown link under `## Related` for humans reading the file directly. `add_typed_link()` maintains both and dedupes. Targets are always absolute in-bundle paths. Permitted relations are listed in `DEFAULT_RELATIONS`; see `docs/typed-edges.md`.

## 10. Security design

`scrub_text()` (`scripts/pkc_common.py`, lines 123–142) runs over ingestion paths before anything is written. `SECRET_PATTERNS` covers OpenAI-style keys, GitHub tokens (`ghp_`, `gho_`), Slack tokens, AWS access keys, Google API keys, PEM private key blocks, and bearer tokens. `PII_PATTERNS` covers emails, phone numbers, and US SSNs.

Scrubbing is **on by default** for transcript, thread, and PR capture. CI asserts a transcript fixture is redacted. New ingestion paths must scrub; this is the one place where "add it later" is not acceptable, because the unscrubbed content lands in Git history.

## 11. Configuration

`.pkc/config.yml` (schema: `.pkc/config.schema.json`, example: `.pkc/config.example.yml`) controls the knowledge root, pack sizes, scrub toggles, materialize include list, capture defaults, the WikiTicket bridge, and federation remotes. It is read by `load_config()` and is optional — every value has a working default.

## 12. Testing strategy

`tests/test_pkc.py` — 27 tests, stdlib `unittest`, no pytest, no fixtures framework. Run the whole suite with `python3 tests/test_pkc.py`, or one class with `python3 tests/test_pkc.py TestIncrementalMaterialize`.

CI (`.github/workflows/ci.yml`) is the real specification. Beyond the unit tests it compiles every script, validates and doctors `sample-knowledge`, asserts the golden pack shape (≥5 nodes; tiny ≤8 nodes at 1 hop; mermaid emits `flowchart`), exercises search/digest/release-notes/thread/ADR fixtures, and asserts materialize idempotency. A second workflow, `worklog-invariants`, enforces the work-log rules described in `docs/worklog-spec.md`.

The `okf-interop` job is `continue-on-error` by design: PKC must not break when okf-plugin is unavailable.

## 13. Risks and technical debt

| Risk | Impact | Current position |
|---|---|---|
| Hand-rolled YAML parser | A frontmatter construct outside the subset fails silently | Accepted; the subset is sufficient and the zero-dep property is worth more |
| Fingerprint field list is manual | A new rendered field that is not in `FINGERPRINT_FIELDS` never re-renders | Documented in `CLAUDE.md`; a test asserting the two lists agree is the obvious next guard |
| `resolve_knowledge_root()` order is implicit | Creating `knowledge/` retargets bare commands | Documented; CI always passes `--bundle` |
| Version string in six manifest sites | A release can ship inconsistent metadata | Release checklist in `docs/worklog-spec.md`; a lockstep test is not yet written |

## 14. Sections omitted, with reasons

**Database design**, **Cache design**, **API design**, **Event-driven processing**, **Deployment architecture**, **Observability** — this system has no database, cache, network API, message bus, or deployed runtime. It is a set of files and CLI scripts invoked by an agent host.

**MCP server integration**, **AI endpoint design**, **Managed AI platform integration** — not built. MCP server mode is an open epic (GitHub #5); until it ships, documenting it here would be fiction.

**Performance and scalability** — the only performance-relevant decision is fingerprint-gated materialization, covered in §6.3. Bundle sizes are in the hundreds of files; no scaling work is warranted yet.

## 15. Open questions

Tracked as work items rather than prose — see `docs/roadmap.md` and the GitHub issues it links. The live v0.5.0 milestone covers agent auto-context injection, `Risk` and `Acceptance` concept types, and MCP server mode.
