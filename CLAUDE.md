# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

**PKC** is a *plugin*, not an app. It ships skills, slash commands, an agent, hooks, and Python scripts that capture meetings/experiments/discoveries/decisions and materialize WikiTicket work into an [OKF](https://github.com/SpillwaveSolutions/okf-plugin) knowledge graph (plain Markdown + YAML frontmatter).

One tree, two hosts: Claude Code (`.claude-plugin/`) and Grok Build (`.grok-plugin/`, zero-config Claude compatibility). **Never diverge the packaging.**

## Commands

```bash
python3 tests/test_pkc.py                    # full suite (stdlib unittest, no pytest)
python3 tests/test_pkc.py TestSlugify        # one test class
python3 tests/test_pkc.py TestSlugify.test_basic
npm test                                     # same as tests/test_pkc.py
npm run typecheck                            # py_compile over every script
npm run validate                             # pkc_validate on sample-knowledge
npm run doctor                               # pkc_doctor on sample-knowledge
npm run dev                                  # docs preview server on :8080
```

There is no build step and no lint config. `npm run typecheck` and CI both hard-code the script list — **add new `scripts/pkc_*.py` to `package.json` and `.github/workflows/ci.yml`** or they go unchecked.

CI (`.github/workflows/ci.yml`) is the real spec: it runs the suite, compiles scripts, validates + doctors `sample-knowledge`, asserts the golden pack shape (`node_count>=5`, tiny `<=8` nodes / 1 hop, mermaid emits `flowchart`), exercises search/digest/release-notes/thread/ADR fixtures, and asserts re-running `pkc_materialize.py` on the same fold reports **`0 created`**. Reproduce a CI failure by running that step's command verbatim.

## Architecture

### Zero dependencies, on purpose

`scripts/pkc_common.py` hand-rolls `_parse_simple_yaml` / `dump_frontmatter` so the plugin runs on bare `python3` in any host. **Do not add PyYAML or any pip dependency.** If frontmatter needs a construct the mini-parser can't handle, extend the parser — or avoid the construct.

### Every script shares the same shape

`--repo <path>` (default `.`) plus optional `--bundle <name-or-path>`, resolved by `resolve_knowledge_root()`:

1. explicit `--bundle` (absolute, or relative to repo)
2. `.pkc/config.yml` → `pkc.knowledge_root` (also read from `.work/config.yml`)
3. first of `knowledge/`, `sample-knowledge/`, `.okf/` that contains `index.md`

Most scripts also take `--json` for machine-readable output — that's how CI asserts on them. Prefer adding `--json` to new scripts over parsing prose.

### One write path

All concept writes go through `write_concept()` in `pkc_common.py`. It owns the invariants that everything else assumes:

- **Merge** — existing frontmatter is preserved and updated key-by-key, never clobbered.
- **`truth_state` barrier** — a file marked `snapshot` / `superseded` / `archived` is *refused* by a `current` write unless `force: true` is passed in the frontmatter dict. It returns `refused`, not `skipped`: a rejected write must be distinguishable from a no-op.
- **Return code** — `"created" | "updated" | "skipped" | "exists" | "refused"`. Identical content returns `skipped`, which is what makes re-running capture/materialize idempotent (and what CI's `0 created` check depends on). `exists` means `create_only=True` found the file already there; `refused` means the `truth_state` barrier blocked the write.
- `stable_timestamp: true` keeps the original `timestamp` when title is unchanged, so re-captures don't churn diffs.

Materialized concepts additionally carry `source_fingerprint` — a hash of the worklog fields that reach the rendered output (`FINGERPRINT_FIELDS` in `pkc_materialize.py`). On the next run a matching fingerprint short-circuits *before* the frontmatter and body are built, so unchanged items never reach `write_concept()`. Adding a field to the rendered concept means adding it to `FINGERPRINT_FIELDS`, or that field will never trigger a re-render.

`pkc_materialize.py` reports these as **`unchanged`**, distinct from `write_concept()`'s **`skipped`**. The split is load-bearing: `skipped` means rendered, compared, and discarded — which was already happening before fingerprints existed. Only `unchanged` proves nothing was rendered, and CI asserts on exactly that.

Bypassing this function (writing Markdown directly) breaks idempotency and the truth-state contract.

### Concept types → directories

`CATALOGS`, `TYPE_TO_DIR`, and `DEFAULT_RELATIONS` in `pkc_common.py` are the source of truth. Adding a concept type means touching, in this order: `TYPE_TO_DIR` (+ `CATALOGS` if it gets its own directory) → a skeleton in `templates/` → the catalog `case` list in `scripts/pkc-curate.sh` → a sample under `sample-knowledge/`.

### Graph edges

Edges are typed and live in two places at once: `links: [{target, rel}]` in frontmatter *and* a Markdown link in the body's `## Related` section. `add_typed_link()` maintains both and dedupes. Targets are always **absolute in-bundle paths** (`/decisions/foo.md`). See `docs/typed-edges.md` for which `rel` to use; never invent an edge the source material doesn't state.

### Adding a capability = 4 files in lockstep

1. `skills/<name>/SKILL.md` — the agent procedure (frontmatter `name` + `description`; the description is what triggers it)
2. `commands/<name>.md` — thin wrapper that says "run the `<name>` skill", passing `$ARGUMENTS`
3. `scripts/pkc_<name>.py` — the deterministic part
4. CI step + `package.json` `typecheck` list + README/AGENTS.md tables

Skills reference scripts as `"${CLAUDE_PLUGIN_ROOT}/scripts/…"` — never a relative path, since the plugin runs from an install directory, not the repo.

### `hooks/` holds two unrelated hook systems

Do not "tidy" this directory — it is deliberately dual-purpose:

- `hooks/hooks.json` — the **Claude plugin** manifest. Fires `scripts/pkc-curate.sh` on `Write|Edit|MultiEdit`. It walks up from the edited file looking for an `index.md` containing `okf_version` (or `.okf/`, `knowledge/`), refreshes that catalog's `index.md`, and runs a non-fatal validate. Silent no-op outside a bundle — keep it that way; a hook that errors blocks edits.
- `hooks/pre-commit`, `hooks/pre-merge-commit`, `hooks/commit-msg` — **git** hooks installed by worklog, active via `git config core.hooksPath hooks`.

They don't shadow each other: `hooks.json` is not a valid git hook name, so git ignores it.

### Split of labor

Deterministic Python owns paths, frontmatter, idempotency, catalogs, and the log. The agent/skill owns judgment: extracting decisions from prose, choosing edge types, writing bodies. When in doubt, push work into a script.

## Rules

1. Valid OKF Markdown only — frontmatter with at least `type` and `title`, absolute links, typed `rel`.
2. Use `scripts/pkc_*.py` for anything deterministic; don't hand-roll file writes.
3. Never invent edges. Never hand-edit `.work/*.jsonl` — WikiTicket owns work status, use repo-local `bin/worklog`.
4. Default context pack: 2 hops / ~20 nodes; tiny pack: 1 hop / ≤8 nodes.
5. After any capture: refresh catalogs + append one line to `log.md`.
6. Releases bump the version in **six** places: `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `.grok-plugin/marketplace.json`, `marketplace.json`, `package.json`, and the README table — plus a `CHANGELOG.md` entry.
7. After script changes: `python3 tests/test_pkc.py` **and** `npm run validate`.
8. Secrets/PII: capture paths run through `scrub_text()`; keep new ingestion paths (transcripts, PRs, threads) scrubbed by default.

## Reference

- `sample-knowledge/` is the golden fixture and CI's test subject — the full Discovery → Experiment → Meeting → Decision → Feature → Design → CodeChange → Release chain. Keep it valid.
- Config: `.pkc/config.example.yml`, schema in `.pkc/config.schema.json`.
- Docs: `docs/design.md` (module boundaries, data flows) · `docs/typed-edges.md` · `docs/prd.md`.
- `docs/vision.md` is hand-written (themes, brainstorm, non-goals). `docs/roadmap.md` is **generated** from `.work/` — see the policy block below.
- `AGENTS.md` mirrors this file for Grok Build / Codex-style hosts — update both together. It is a real file, not a symlink, because the two hosts get deliberately different content.

<!-- worklog:policy:start -->
## Work tracking policy

- Every plan MUST end by running `worklog plan-capture` — it writes
  `docs/plans/<date>-<slug>.md` and appends the plan's steps as work items.
- Work discovered mid-flight that wasn't in the plan: run
  `worklog add --unplanned --discovered-during <item>` BEFORE doing the work.
- Never hand-edit `.work/*.jsonl` (use `worklog`) or `docs/roadmap.md`
  (it is generated; change the work items instead).
- After changing work items, run `worklog roadmap-render` and commit the log
  and roadmap together.
<!-- worklog:policy:end -->

<!-- worklog:taxonomy:start -->
## Work taxonomy

Every work item sits on four independent axes:

| Axis | Field | Values | Answers |
|---|---|---|---|
| Level | `level` | epic / story / task / subtask | size & place in the parent tree |
| Kind | `kind` | feature / bug / ops / triage | nature of the work |
| Milestone | `milestone` | free string (e.g. v0.6.0) or null | what ships together |
| Planned | `unplanned` + `discovered_during` | bool + ULID | deliberate vs discovered |

Rules (the validator enforces these; apply them when proposing items):
1. Kind is free at story/task/subtask.
2. Epics are `feature` or `ops` only — a bug is never epic-sized.
3. `kind` defaults to `triage` when omitted — never silently default to feature.
4. `bug.parent` is optional; bugs may float free of any epic.
5. `milestone` lives on leaves (story and below); an epic's milestone derives from its children.
6. `triage` and `ops` both trend down: triage shrinks by classifying, ops by automating.

When trackable work surfaces in conversation, propose an item inline as part of
the normal response — "want me to file this? `level:story kind:feature
parent:<ulid> milestone:v0.6.0`" — and create it only on assent, via the
work-track or plan-capture skill. When unsure of the kind, propose `kind:triage`
with the open question stated — triage is the honest default, never a confident
guess. This inline path is the default; the flag-gated classifier (`classifier:`
in `.work/config.yml`, off by default) is the escape hatch for teams where work
keeps escaping the log.
<!-- worklog:taxonomy:end -->
