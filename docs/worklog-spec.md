---
wiki_key: guide/worklog-spec
doc_type: guide
title: Worklog Spec
slug: worklog-spec
truth_state: current
---

# Worklog Spec

How this repo runs WikiTicket SDD.

PKC ships a WikiTicket bridge, so it runs WikiTicket on itself. This page is the contract for contributors and agents working in this repository.

This is **not** the upstream WORKLOG-SPEC — that lives in [wiki_ticket_sdd](https://github.com/SpillwaveSolutions/wiki_ticket_sdd) and governs the tool. This page describes how *this repo* uses it, and where the two interact with PKC's own conventions.

Adopted at v0.4.1. Installed worklog version is recorded in `.work/config.yml` as `installed:`.

## The short version

1. Never commit on `main`.
2. Every commit message carries a 26-character ULID or a `#123` issue reference.
3. Never hand-edit `.work/*.jsonl` or `docs/roadmap.md`.
4. Work not in the plan gets filed *before* you do it.

All four are enforced by git hooks **and** by CI, so `--no-verify` does not get around them.

## Layout

| Path | What it is |
|---|---|
| `.work/todo.jsonl`, `.work/done.jsonl` | The append-only event log. The source of truth for work. |
| `.work/config.yml` | Machine-readable settings: project key, ticketing, wiki, paths |
| `.work/published.json` | Wiki publish ledger — what was published, at what hash |
| `bin/` | worklog scripts, committed so they work without the plugin installed |
| `hooks/` | git hooks, active via `core.hooksPath` |
| `adapters/github/adapter` | Pushes work items to GitHub Issues |
| `docs/roadmap.md` | **Generated.** Do not edit. |
| `docs/roadmap/` | Frozen release snapshots |
| `docs/plans/` | Plan documents from `worklog plan-capture` |
| `docs/.index/` | Generated IA layer: inventory, rendered wiki pages, publish manifest |

`.work/sync-state.json`, `.work/wiki-checkout/`, and friends are local-only and gitignored.

## Work taxonomy

Four independent axes. The validator enforces these; apply them when proposing items.

| Axis | Field | Values |
|---|---|---|
| Level | `level` | epic / story / task / subtask |
| Kind | `kind` | feature / bug / ops / triage |
| Milestone | `milestone` | free string (`v0.5.0`) or null |
| Planned | `unplanned` + `discovered_during` | bool + ULID |

Rules:

1. Kind is free at story level and below.
2. Epics are `feature` or `ops` only — a bug is never epic-sized.
3. `kind` defaults to `triage` when omitted. Never silently default to `feature`.
4. `bug.parent` is optional; bugs may float free of any epic.
5. `milestone` lives on leaves. An epic's milestone derives from its children — setting one directly is rejected.
6. `triage` and `ops` both trend down: triage shrinks by classifying, ops by automating.

The full block is in `CLAUDE.md` between the `worklog:taxonomy` markers.

## Daily flow

### Filing work

```bash
bin/worklog add --level story --kind feature --milestone v0.5.0 \
  --parent <epic-ulid> --body "What and why, readable by a junior dev." "Title"
```

The body is prose for a human, capped at 2048 bytes. Longer reasoning belongs in a plan doc under `docs/plans/`, not the log.

> **zsh trap.** `bin/worklog add $FLAGS ...` does not work in zsh — unquoted variables are not word-split, so the whole string arrives as one argument. Write flags literally, use `${=FLAGS}`, or run the script under `bash`.

### Discovering work mid-flight

File it before you do it:

```bash
bin/worklog add --unplanned --discovered-during <current-item-ulid> ...
```

This is the rule that keeps the log honest. Work that only exists in a commit message is work nobody can plan around.

### Working an item

```bash
git checkout -b feat/<slug>
bin/worklog update <ulid> --status in_progress
# ... work, test-first ...
bin/worklog close <ulid>
bin/worklog roadmap-render
```

Commit, push, open a PR, and let it merge on green. Never merge with `--admin`, never skip a gate.

## The gates

### `hooks/pre-commit`

- **Branch guard** — refuses a commit authored on `main` or `master`. Merges are exempt.
- **Trailing newline** on both `.jsonl` files. Without it, a union merge fuses two events into one unparseable line and loses both.
- **Event schema** — required fields, valid `level` and `kind`, taxonomy rules 2 and 5.
- **Roadmap freshness** — regenerates `docs/roadmap.md` and diffs. Any hand edit fails the commit.
- **IA checks** — inventory, rendered pages, and metadata drift.

### `hooks/commit-msg`

Requires a 26-character ULID or `#123` somewhere in the message. Merge commits are exempt.

### `.github/workflows/worklog.yml`

Runs `hooks/pre-commit` in CI, and on pull requests checks every non-merge commit message in the range. This is why bypassing the local hook does not help.

## Ticket sync

`ticketing.system: github` in `.work/config.yml`, with the adapter at `adapters/github/adapter`.

```bash
bin/worklog adapter check      # validate the adapter
bin/worklog sync --dry-run     # see what would happen
bin/worklog sync               # push
```

The dispatcher owns every invariant — scope, canonical hashing, create-vs-update, echo suppression, conflict detection. The adapter only translates to `gh` calls.

Known, expected drift on GitHub:

- GitHub has no epic type, so epics map to plain issues.
- `depends_on` has no GitHub equivalent and stays local.

Items are matched by a `worklog:<ULID>` marker in the issue body, so a retried push updates rather than duplicating.

> **Note:** `worklog init` scaffolds `bin/` and `hooks/` but **not** `adapters/`. A fresh install has no adapter and `sync` silently runs local-only. The adapter is committed here so that does not happen again.

## Wiki publishing

`wiki.system: github-wiki`. Pages are driven by `docs/.index/publish-manifest.json`, generated by `worklog ia-index`.

```bash
bin/worklog ia-index           # refresh inventory, rendered pages, manifest
# then publish per the wiki-publish skill
```

Two rules that are easy to get backwards:

- **Skip on `render_hash`, not `source_hash`.** A frozen page's source never changes, but its banner can — a superseded plan needs its new banner on the wiki even though the source is untouched.
- **`frozen: true` guards the source.** If a frozen source's own hash changed, that is a frozen-doc edit. Stop and report it; do not publish.

Frontmatter is stripped in the wiki copy only. Gollum renders YAML as raw text, so the page would otherwise open with a `---` block. Sources under `docs/` keep their frontmatter.

The ledger is `.work/published.json`, committed alongside the docs it describes.

## Releases

1. File a release item.
2. Stamp `CHANGELOG.md`: `## X.Y.Z — unreleased` becomes the release date.
3. Bump the version in **six** places: `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `.grok-plugin/marketplace.json`, `marketplace.json`, `package.json`, and the README table.
4. `bin/worklog roadmap-snapshot --name vX.Y.Z-release` — frozen, never regenerated.
5. `bin/worklog ia-index` — sidecar the snapshot, refresh the inventory, re-render the wiki pages.
6. Land it as a PR. The branch guard means the release cannot be committed on `main`.
7. Tag the merge commit, push the tag, create the GitHub release with the changelog section as notes.
8. Publish the wiki; close the release item.

Released changelog sections are frozen. Corrections go in the next release.

Version choice: this repo treats a new command, a new concept type, or an API change as a minor bump. Internal optimizations and additive frontmatter are patches — v0.4.1 shipped incremental materialize as a patch for exactly that reason, and because calling it 0.5.0 would have shown a version whose milestone was 2/12 done.

## PKC-specific interactions

Three places where worklog and PKC touch, and the rule for each:

| Interaction | Rule |
|---|---|
| `bin/worklog fold` → `pkc_materialize.py` | Epics and stories become Features; every item gets a TicketLink. PKC mirrors status, never writes it back. |
| Meeting action items → work items | `pkc_action_items.py --apply --worklog` shells out to `bin/worklog add`. Dry-run by default. |
| `hooks/` holds two hook systems | `hooks.json` is PKC's Claude plugin manifest; the rest are git hooks. Do not "tidy" the directory. |

## Recovering from common states

**"docs/roadmap.md is stale or hand-edited."** Run `bin/worklog roadmap-render` and commit. If you edited it by hand, your edit is gone — that is intended. Change the work items instead.

**Commit rejected for a missing ULID.** Add the item's ULID to the message, or `#123` if the work is tracked as an issue. If neither exists, the work is not filed; file it.

**Commit rejected on `main`.** Branch, then cherry-pick or re-commit there. `main` is pull-only.

**A sync reported 0 pushes and "no adapter configured."** `adapters/<system>/adapter` is missing. It is committed in this repo; check it did not get lost in a merge.
