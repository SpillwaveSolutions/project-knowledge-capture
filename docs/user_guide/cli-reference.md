---
wiki_key: guide/cli-reference
doc_type: guide
title: CLI Reference
slug: cli-reference
truth_state: current
---

# CLI Reference

Every script under `scripts/`. Flags below were extracted from each script's own `--help` at tag `v0.4.1`, not written from memory.

## Shared conventions

Almost every script accepts:

| Flag | Default | Meaning |
|---|---|---|
| `--repo REPO` | `.` | Repository root |
| `--bundle BUNDLE` | resolved | Bundle name or path |
| `--json` | off | Machine-readable output — use this in scripts and CI |

**Bundle resolution order:** explicit `--bundle` → `.pkc/config.yml` `knowledge_root` → the first of `knowledge/`, `sample-knowledge/`, `.okf/` containing an `index.md`. Pass `--bundle` when you want certainty.

Inside a plugin host, invoke as `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/<name>.py"`.

---

## Capture

### `pkc_capture.py`

```
pkc_capture.py [--repo REPO] [--bundle BUNDLE]
               {meeting,experiment,discovery,decision,assumption,question,risk,acceptance} ...
```

| Subcommand | Required | Optional |
|---|---|---|
| `meeting` | `--title`, `--date` | `--attendees`, `--notes`, `--notes-file`, `--decision` (repeatable) |
| `experiment` | `--title`, `--hypothesis`, `--result`, `--conclusion` | `--informs` (repeatable) |
| `discovery` | `--title` | `--source`, `--notes`, `--notes-file`, `--confidence`, `--links-to` (repeatable), `--stale-after` |
| `decision` | `--title`, `--decision` | `--context`, `--consequences`, `--status`, `--originates-from`, `--decides` (repeatable) |
| `assumption` | `--title`, `--statement` | `--rationale`, `--status`, `--for` (repeatable) |
| `question` | `--title`, `--question` | `--context`, `--status`, `--blocks` (repeatable) |
| `risk` | `--title`, `--statement` | `--severity` (low/medium/high/critical), `--exposes`, `--mitigated-by` (repeatable) |
| `acceptance` | `--title`, `--criterion` | `--for` (Feature), `--verified-by` (repeatable) |

```bash
python3 scripts/pkc_capture.py meeting --repo . \
  --title "Auth design discussion" --date 2026-08-03 \
  --attendees "rick,alice" --notes-file /tmp/notes.md \
  --decision "Use JWT for session management"
```

Paths are derived from the title slug (plus date, for meetings), so re-running with the same title updates in place.

`--repo` and `--bundle` are **top-level** flags: they go before the subcommand, not after.

Flags that take a concept reference (`--exposes`, `--for`, `--decides`, `--verified-by`, …) accept an absolute path, a relative path, or a bare title that gets slugified into the default directory for that relation.

---

## Ingestion

### `pkc_transcript.py`

```
pkc_transcript.py [--file FILE] [--title TITLE] [--date DATE] [--json]
                  [--capture] [--repo REPO] [--bundle BUNDLE]
```

Normalizes plain text, Fireflies, Otter, and Granola-style JSON into notes. Reads stdin when `--file` is absent. Without `--capture` it only prints the normalized result — inspect before writing.

### `pkc_thread.py`

```
pkc_thread.py [--file FILE] [--title TITLE] [--as {meeting,discovery}]
              [--source SOURCE] [--repo REPO] [--bundle BUNDLE] [--capture] [--json]
```

Slack or Discord paste. `--as` decides whether it lands as a Meeting or a Discovery.

### `pkc_pr_capture.py`

```
pkc_pr_capture.py [pr] [--json-file JSON_FILE] [--repo REPO]
                  [--gh-repo GH_REPO] [--bundle BUNDLE] [--implements IMPLEMENTS]
```

A PR number (via `gh`) or `--json-file` for offline use. `--implements` links the resulting CodeChange to a Feature.

### `pkc_adr_import.py`

```
pkc_adr_import.py --from SOURCE [--repo REPO] [--bundle BUNDLE] [--dry-run]
```

MADR or adr-tools directory → DecisionRecords. **Always `--dry-run` first** on a directory you did not create.

---

## Query and reporting

### `pkc_pack.py`

```
pkc_pack.py concept [--repo REPO] [--bundle BUNDLE] [--hops HOPS]
            [--max-nodes MAX_NODES] [--tiny] [--mermaid] [--write WRITE] [--json]
```

| Flag | Default |
|---|---|
| `--hops` | 2 |
| `--max-nodes` | 20 |
| `--tiny` | 1 hop, max 8 nodes |
| `--mermaid` | print the diagram only |

```bash
python3 scripts/pkc_pack.py features/user-authentication.md --bundle sample-knowledge --hops 2
python3 scripts/pkc_pack.py features/user-authentication.md --bundle sample-knowledge --tiny --json
```

### `pkc_search.py`

```
pkc_search.py query [--repo REPO] [--bundle BUNDLE] [--type TYPES]
              [--limit LIMIT] [--prefix PREFIX] [--json]
```

Full-text AND search with ranked hits. `--type` filters by concept type; `--prefix` by path prefix.

### `pkc_digest.py`

```
pkc_digest.py [--repo REPO] [--bundle BUNDLE] [--days DAYS] [--write WRITE] [--json]
```

Weekly brief plus the needs-verification queue. `--write` saves to a path instead of printing.

### `pkc_release_notes.py`

```
pkc_release_notes.py [release] [--repo REPO] [--bundle BUNDLE] [--write WRITE] [--json]
```

Derives notes from `lands_in` and `released_in` edges. Omit the positional to use the latest Release concept.

### `pkc_federate.py`

```
pkc_federate.py [--repo REPO] [--bundle BUNDLE] {list,search,index} ...
```

| Subcommand | Flags |
|---|---|
| `list` | — |
| `search` | `query`, `--limit`, `--json` |
| `index` | `--write` |

Remotes are read-only and configured under `federation:` in `.pkc/config.yml`.

---

## Health

### `pkc_validate.py`

```
pkc_validate.py [--repo REPO] [--bundle BUNDLE] [--strict] [--json]
```

Structure and links. Exit 0 with warnings allowed; exit 1 on errors. `--strict` promotes broken links from warning to error.

Errors: missing `index.md`, missing `okf_version`, absent frontmatter, missing `type` or `title`, malformed `links`.

### `pkc_doctor.py`

```
pkc_doctor.py [--repo REPO] [--bundle BUNDLE] [--stale-days STALE_DAYS] [--strict] [--json]
```

One-screen health: conflicting decisions, thin features, stale discoveries, unvalidated assumptions, open questions blocking features.

### `pkc_scrub.py`

```
pkc_scrub.py [--file FILE] [--text TEXT] [--no-pii] [--out OUT] [--report]
```

Reads stdin when neither `--file` nor `--text` is given. `--no-pii` keeps emails and phone numbers while still redacting secrets. `--report` lists what was redacted.

---

## Graph editing

### `pkc_link.py`

```
pkc_link.py source target --rel REL [--repo REPO] [--bundle BUNDLE]
            [--bidirectional] [--reverse-rel REVERSE_REL]
```

`--bidirectional` also writes the inverse edge; `--reverse-rel` names it when the inverse differs (e.g. `decides` ↔ `originates_from`).

### `pkc_promote.py`

```
pkc_promote.py source --to {Feature,Requirement,DecisionRecord,Specification,Design}
               [--title TITLE] [--repo REPO] [--bundle BUNDLE] [--slug SLUG]
```

Informal concept → formal one, preserving provenance edges back to the source.

### `pkc_action_items.py`

```
pkc_action_items.py meeting [--repo REPO] [--bundle BUNDLE] [--apply]
                    [--worklog] [--parent PARENT]
```

**Dry-run by default.** `--apply` creates TicketLinks; `--apply --worklog` also runs `bin/worklog add`. `--parent` sets the parent ULID for created tasks.

### `pkc_materialize.py`

```
pkc_materialize.py [--repo REPO] [--bundle BUNDLE] [--fold FOLD] [--include INCLUDE]
                   [--from-docs] [--no-worklog] [--force] [--dry-run] [--json]
```

| Flag | Meaning |
|---|---|
| `--fold` | Path to fold JSON; reads stdin when absent |
| `--include` | Comma-separated: `features,tickets,designs,decisions,specs,releases` |
| `--from-docs` | Also materialize from `docs/**` |
| `--no-worklog` | Docs only, skip the fold |
| `--force` | Override `truth_state` barriers **and** the fingerprint skip |

```bash
bin/worklog fold | python3 scripts/pkc_materialize.py --repo . --bundle knowledge
```

Since v0.4.1, unchanged items are skipped by fingerprint before rendering. `--force` bypasses that — use it after changing the concept template, when output would change even though inputs did not.

---

## Utilities

### `pkc_common.py`

```
pkc_common.py {init-bundle,slugify,resolve-root,scrub} ...
```

| Subcommand | Flags |
|---|---|
| `init-bundle` | `--bundle`, `--title`, `--repo` |
| `slugify` | `text` |
| `resolve-root` | `--repo`, `--override` |
| `scrub` | `--text`, `--file`, `--no-pii` |

`resolve-root` is the fastest way to answer "which bundle would this command write to?"

```bash
python3 scripts/pkc_common.py resolve-root --repo .
```

### `pkc-curate.sh`

Post-edit hook helper. Takes a file path as `$1` or reads `tool_input.file_path` from JSON on stdin. Refreshes the catalog index and runs a non-fatal validate. Silent no-op outside a bundle.

### `pkc_auto_context.py`

`UserPromptSubmit` hook. Reads the hook payload from stdin (`prompt` or `user_prompt`, plus `cwd`) and prints `hookSpecificOutput.additionalContext` containing the tiny pack for a Feature the prompt named — or prints nothing.

| Flag | Purpose |
|---|---|
| `--repo` | repo root; defaults to the payload's `cwd`, then `.` |
| `--bundle` | bundle override, as everywhere else |
| `--prompt` | supply the prompt directly instead of reading stdin (debugging) |

Detection: a `features/<slug>` path whose file exists and is `type: Feature`, else a ULID matching a Feature's `worklog_id`, else nothing. Gated by `pkc.pack.auto_inject_on_feature` (default true) and `pkc.enabled`. Always exits 0, even on malformed input — a hook that fails would fail the turn it decorates.

```bash
python3 scripts/pkc_auto_context.py --bundle sample-knowledge \
  --prompt "recap features/user-authentication.md"
```

---

## npm shortcuts

| Command | Runs |
|---|---|
| `npm test` | `python3 tests/test_pkc.py` |
| `npm run typecheck` | `py_compile` over every script |
| `npm run validate` | validate `sample-knowledge` |
| `npm run doctor` | doctor `sample-knowledge` |
| `npm run digest` | digest `sample-knowledge` |
| `npm run dev` | docs preview server on :8080 |

Run a single test class: `python3 tests/test_pkc.py TestIncrementalMaterialize`.
