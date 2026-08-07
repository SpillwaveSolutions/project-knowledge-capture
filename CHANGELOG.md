# Changelog

## 0.5.0 — 2026-08-06

Two new concept types. Minor bump: the plugin tree gains types, templates, and capture subcommands.

### Added
- **`Risk` concept type** (`risks/`) — what could go wrong, with a `severity` of low/medium/high/critical. New relations `exposes` (Risk → Feature) and `mitigates` (Decision → Risk).
- **`Acceptance` concept type** (`acceptance/`) — one atomic, checkable condition for calling a Feature done, linked by `satisfies` to the Feature and `verified_by` to whatever proves it.
- `pkc_capture.py risk` and `pkc_capture.py acceptance`, plus `templates/risk.md` and `templates/acceptance.md`.
- Both types on the sample auth chain, so they are covered by validate, doctor, search, and the golden pack like every other type.
- `concept_ref()` in `pkc_common.py` — normalizes a concept reference that may be an absolute path, a relative path, or a bare title.
- **Incremental materialize is now verifiable.** Fingerprint short-circuits report a distinct `unchanged` action, separate from `write_concept()`'s `skipped`. CI asserts every action is `unchanged` on a second run.
- `tools/ci-local.sh` and `npm run ci` — 19 steps mirroring both CI workflows.

### Fixed
- **Relative concept paths were mangled.** Ten call sites did `t if t.startswith("/") else f"/{dir}/{slugify(t)}.md"`; `slugify` strips `/` and `.`, so `--decides features/user-auth.md` produced `/features/featuresuser-authmd.md`. All sites now use `concept_ref()`. Affects `--decides`, `--informs`, `--links-to`, `--for`, `--originates-from`, `--blocks`, and `pkc_pr_capture`'s `--implements`.
- Capture warns on stderr when an inverse-edge target does not exist, instead of dropping the edge silently.

### Notes
- **Edge direction is not symmetric.** `Decision --mitigates--> Risk`, never the reverse. `--mitigated-by` therefore writes its edge on the decision.
- **`pack()` walks outbound edges only**, so a concept pointing at a Feature does not appear in that Feature's pack unless the Feature points back. `capture_acceptance` writes the inverse `Feature --verified_by--> Acceptance` for this reason. The general fix — a reverse index in `pack()` — is tracked, not shipped.
- The golden auth pack grows from 9 to 12 nodes. The tiny pack now sits exactly on its 8-node ceiling.
- Stories still open under the v0.5.0 milestone (agent auto-context injection, MCP server mode) were re-milestoned to **v0.6.0** rather than left claiming a shipped version.
- GitHub Actions resumed producing runs during this release, after the blackout recorded in 0.4.2. This release is verified by both CI and `npm run ci`.

## 0.4.2 — 2026-08-06

Documentation release. No plugin code changed.

### Added
- **Six wiki pages**, each with a source of truth in `docs/`:
  - `User-Guide` — install, the 20 commands grouped by intent, context packs, concept types, typed edges, privacy, troubleshooting
  - `CLI-Reference` — every script's flags, extracted from each script's own `--help`
  - `Plugin-Guide` — packaging and extension: the skill/command/script split, `${CLAUDE_PLUGIN_ROOT}`, hook rules, adding a capability or concept type
  - `Design-Doc` — architecture and the four decisions that shape it
  - `Code-Walkthrough` — a read-the-code tour with line citations computed against the tree
  - `Worklog-Spec` — how this repo runs WikiTicket SDD
- `tools/wiki-publish.py` — the wiki publisher. The wiki-publish skill describes the ledger rules but ships no implementation. Placed in `tools/` rather than `scripts/` deliberately: `scripts/` ships inside the plugin, and a wiki publisher is repo tooling.

### Fixed
- `docs/worklog-spec.md` used `doc_type: spec`, which is not in the IA schema (valid: plan, roadmap, roadmap-snapshot, status, design, adr, guide). Re-keyed as `guide/worklog-spec`.

### Known gap
- **GitHub Actions produced no workflow runs for this release, or for v0.4.1.** The last run was 2026-08-05 18:59 UTC; PRs #21, #22, and #23 each have zero check-runs despite Actions being enabled and both workflows `active`. The cause appears to be org-level and is not visible from this repository.

  Both releases were verified by running the CI suite locally instead — unit tests, `py_compile` over every script, validate and doctor on `sample-knowledge`, the golden pack assertions, materialize idempotency, and `commit-msg` over every commit in each PR. All passed. This is self-reported rather than independently verified, and is recorded here rather than left in a terminal.

  Related: `merge-when-green.sh` treats *no checks* as *all checks green*. PR #22 merged that way. Worth a guard.

## 0.4.1 — 2026-08-06

### Added
- **Incremental materialize** — materialized concepts carry `source_fingerprint`, a hash of only the worklog fields that reach the rendered output. A matching fingerprint short-circuits before the frontmatter and body are built, so unchanged items never reach `write_concept()`. Re-materialize is now O(changed work) instead of O(all work).
- `adapters/github/adapter` — the GitHub ticket adapter, so `worklog sync` can push work items to GitHub Issues. worklog's own `init.sh` scaffolds `bin/` and `hooks/` but not `adapters/`.
- `docs/vision.md` — themes, brainstorm, non-goals, and how to contribute an idea.

### Changed
- **This repo now runs WikiTicket SDD on itself.** `bin/`, git hooks via `core.hooksPath`, a `.work/` event log, and CI invariants. `pkc_materialize.py` is exercised against a real fold instead of only a four-item fixture.
- **`docs/roadmap.md` is generated** from `.work/` by `bin/worklog roadmap-render` and is read-only for humans. Its narrative half moved to `docs/vision.md`; the shipped table was dropped as a duplicate of this changelog.
- `CLAUDE.md` rewritten for accuracy: the zero-dependency mini-YAML parser, the `write_concept()` merge and `truth_state` contract, `--repo`/`--bundle` resolution order, and the `source_fingerprint` contract.
- `AGENTS.md` carries the work-tracking policy as a real file, not a symlink — the Claude and Grok hosts get deliberately different content.

### Notes
- Upgrade path is one migration pass: a bundle written before this release has no fingerprint, so the first materialize updates each concept once and every run after that skips.
- Contributors: commits no longer land on `main`, and every commit message must reference a 26-char ULID or `#123`. Both enforced by git hooks and by CI on pull requests.

## 0.4.0 — 2026-08-04

### Added
- `pkc_search.py` / `/pkc-search` — full-text AND search with ranked hits
- `pkc_digest.py` / `/pkc-digest` — weekly/daily brief + needs-verification queue
- `pkc_release_notes.py` / `/pkc-release-notes` — notes from Release/Feature/CodeChange edges
- `pkc_thread.py` / `/pkc-capture-thread` — Slack/Discord paste → Meeting/Discovery
- `pkc_federate.py` / `/pkc-federate` — multi-repo read-only roots + cross-search
- `pkc_adr_import.py` / `/pkc-import-adr` — MADR/adr-tools → DecisionRecords
- Preview: Search + Digest views
- Federation config schema + example
- Sample digest + release-notes packs
- 24 unit tests

## 0.3.0 — 2026-08-04

### Added
- Doctor, Assumption/Question, scrub, transcript, PR capture, tiny packs, mermaid, config schema

## 0.2.0 — 2026-08-04

### Added
- Context packs, validate, action-item bridge, curate hook, CI, golden pack, roadmap

## 0.1.0 — 2026-08-03

### Added
- Dual-host plugin, core capture/materialize skills, sample chain, templates
