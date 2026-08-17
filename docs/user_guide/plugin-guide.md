---
wiki_key: guide/plugin-guide
doc_type: guide
title: Plugin Guide
slug: plugin-guide
truth_state: current
---

# Plugin Guide

How PKC is packaged, and how to extend it. For using the commands, see [[User-Guide]]. For the code itself, see [[Code-Walkthrough]].

## The tree

```
.claude-plugin/plugin.json      Claude Code manifest
.claude-plugin/marketplace.json
.grok-plugin/marketplace.json   Grok Build
marketplace.json                root marketplace entry
skills/<name>/SKILL.md          agent procedures (20)
commands/<name>.md              slash commands (20)
agents/knowledge-capturer.md    agent definition
hooks/hooks.json                PostToolUse hook manifest
scripts/pkc_*.py                deterministic core (18)
templates/*.md                  concept skeletons
sample-knowledge/               the golden worked example
```

One tree, two hosts. Grok Build reads Claude-compatible plugins natively, so there is no Grok-specific packaging beyond a marketplace entry. **Do not diverge the two.**

## Skills vs commands vs scripts

Three layers with a strict division of labor:

| Layer | Decides | Never does |
|---|---|---|
| **Skill** | Judgment — what is a decision, which edge type fits, how to word a body | Compute paths, write files directly |
| **Command** | Nothing. Routes to a skill with `$ARGUMENTS` | Contain procedure |
| **Script** | Paths, frontmatter, idempotency, catalogs, validation | Interpret prose |

The rule that keeps this honest: **if it can be deterministic, it belongs in Python.** A skill that writes Markdown itself has bypassed `write_concept()`, and with it the merge semantics, the `truth_state` barrier, and idempotency.

## Anatomy of a skill

```markdown
---
name: pkc-capture-meeting
description: Capture meeting notes into OKF Meeting concepts, extract
  DecisionRecords, and optionally create WikiTicket action items. Use when
  the user pastes meeting notes, transcripts, or asks to record a decision.
---

# PKC Capture Meeting

## When to use
## Inputs          (table: input | required | notes)
## Process         (numbered steps with real commands)
## Output report
## Done when       (checkable conditions)
```

The `description` is the trigger. It is what a host matches against user intent, so write it as *when to use this*, not *what this is*. A description that reads "Meeting capture skill" will never fire.

`## Done when` matters more than it looks — it is what stops a skill from being half-applied.

## Anatomy of a command

Thin on purpose:

```markdown
---
name: pkc-capture-meeting
description: Capture meeting notes → Meeting + DecisionRecords (+ optional tickets).
---

Run the **pkc-capture-meeting** skill.

User request: `$ARGUMENTS`

Follow `${CLAUDE_PLUGIN_ROOT}/skills/pkc-capture-meeting/SKILL.md` completely.
```

Procedure lives in the skill, never duplicated here. Two copies drift.

## `${CLAUDE_PLUGIN_ROOT}`

Always reference plugin files through it:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/pkc_common.py" resolve-root --repo .
```

The plugin runs from an install directory, not from a checkout of this repo. A relative path works in development and breaks for every installed user.

## Hooks

`hooks/hooks.json` registers two, and they run at opposite ends of a turn.

| Event | Script | Job |
|---|---|---|
| `UserPromptSubmit` | `scripts/pkc_auto_context.py` | inject a tiny pack when the prompt names a Feature |
| `PostToolUse` on `Write\|Edit\|MultiEdit` | `scripts/pkc-curate.sh` | refresh the catalog index and validate after a knowledge edit |

```json
{
  "hooks": {
    "UserPromptSubmit": [{
      "hooks": [{
        "type": "command",
        "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/scripts/pkc_auto_context.py\"",
        "timeout": 10
      }]
    }],
    "PostToolUse": [{
      "matcher": "Write|Edit|MultiEdit",
      "hooks": [{
        "type": "command",
        "command": "\"${CLAUDE_PLUGIN_ROOT}/scripts/pkc-curate.sh\"",
        "timeout": 45
      }]
    }]
  }
}
```

`UserPromptSubmit` takes no `matcher` — it has no tool to match on.

Three rules for hook scripts:

1. **Exit 0 outside your domain.** `pkc-curate.sh` returns immediately for non-Markdown files and for anything outside a bundle; `pkc_auto_context.py` swallows every exception. A hook that errors blocks the user's edit or fails their turn.
2. **Never assume argv.** The path arrives as `$1` or as `tool_input.file_path` in JSON on stdin, depending on the host. Handle both. `UserPromptSubmit` has the same problem one level down: the prompt is `prompt` in the hooks reference and `user_prompt` in the plugin-dev skill, so read both keys.
3. **Say nothing by default.** A `UserPromptSubmit` hook's stdout becomes model context on *every* turn. `pkc_auto_context.py` prints only when it resolved a real Feature; the silent path is covered by its own test and its own CI step, because that is the half a regression breaks invisibly.

### Auto-context injection

`UserPromptSubmit` is the only hook whose output reaches the model *before* the turn runs, which is why detection lives there and not in `PostToolUse` — by then Claude has already chosen what to read.

Detection is deliberately narrow. A path wins over a ULID, since it is what the human actually typed:

1. `features/<slug>` or `/features/<slug>.md` in the prompt, where that file exists **and** its `type` is `Feature`
2. a 26-char ULID matching some Feature's `worklog_id` (materialize writes it)
3. otherwise nothing

On a hit it emits the tiny pack (1 hop, ≤8 nodes — `pack.tiny_hops` / `pack.tiny_max_nodes`) as `hookSpecificOutput.additionalContext`, with no mermaid: a diagram costs tokens the model cannot act on better than the edge list it already gets.

Turn it off with `pkc.pack.auto_inject_on_feature: false`, or the whole plugin with `pkc.enabled: false`.

Debug it without a host:

```bash
python3 scripts/pkc_auto_context.py --bundle sample-knowledge \
  --prompt "why did we pick JWT in features/user-authentication.md?"
```

> `hooks/` also holds worklog's git hooks (`pre-commit`, `pre-merge-commit`, `commit-msg`) because `core.hooksPath` points there. They coexist — `hooks.json` is not a valid git hook name. Do not "tidy" this directory.

## Adding a capability

Four files move together. Miss one and the capability is invisible, untested, or undocumented.

**1. The skill** — `skills/<name>/SKILL.md`, with a trigger-shaped `description`.

**2. The command** — `commands/<name>.md`, thin wrapper.

**3. The script** — `scripts/pkc_<name>.py`:

```python
parser.add_argument("--repo", default=".")
parser.add_argument("--bundle", default=None)
parser.add_argument("--json", action="store_true")
```

Resolve the bundle with `resolve_knowledge_root()`. Write through `write_concept()`. Add `--json`; CI asserts against JSON, not prose.

**4. The wiring** — the `typecheck` list in `package.json`, a step in `.github/workflows/ci.yml`, and the tables in `README.md` and `AGENTS.md`.

Steps 1–3 are the fun part; step 4 is the one that gets skipped. A script missing from the typecheck list is never compiled by CI.

## Adding a concept type

In this order:

1. `TYPE_TO_DIR` in `scripts/pkc_common.py` — type name → directory
2. `CATALOGS` — if it gets its own directory
3. `DEFAULT_RELATIONS` — any new edge types it needs
4. A skeleton in `templates/`
5. The catalog `case` list in `scripts/pkc-curate.sh`
6. A worked example in `sample-knowledge/`

Skipping 5 means the post-edit hook silently stops refreshing that catalog. Skipping 6 means the type is never exercised by validate, doctor, or the golden pack.

If the type is materialized from worklog, also add its fields to `FINGERPRINT_FIELDS` in `pkc_materialize.py` — otherwise changes to it will never trigger a re-render.

If concepts of the new type point *at* an existing concept, decide whether the existing one needs an inverse edge. `pack()` reads both directions, so an inbound-only concept is reachable either way — add the inverse only when the target genuinely asserts it, not to make the traversal work. `Risk` and `Acceptance` (v0.5) are the worked examples.

## Frontmatter constraints

Frontmatter is parsed by a hand-written YAML subset (`_parse_simple_yaml()`), not PyYAML. **Do not add a dependency** — the zero-dep property is what lets the plugin run on bare `python3` in any sandbox.

Supported: scalars with type coercion, flat lists, inline `[a, b]` arrays, nested maps, and lists of single-level dicts (which is what `links:` is).

Not supported: multi-line strings, anchors, aliases, flow maps. If you need one of those, extend the parser rather than working around it.

## Testing

`tests/test_pkc.py`, stdlib `unittest`, no pytest, no fixtures framework.

```bash
python3 tests/test_pkc.py                              # all 27
python3 tests/test_pkc.py TestIncrementalMaterialize   # one class
```

Write the test first. `TestIncrementalMaterialize` is the model: it monkeypatches `pkc_materialize.write_concept` with a counting wrapper and asserts the call list is empty, which tests the actual behavior rather than a proxy. A file-mtime assertion would have passed before the feature existed.

CI is the real specification. Beyond unit tests it compiles every script, validates and doctors `sample-knowledge`, asserts the golden pack shape, exercises the ingestion fixtures, and asserts materialize idempotency via `grep -q "0 created"`.

## Releasing

Version lives in **six** places and they must agree:

```
.claude-plugin/plugin.json
.claude-plugin/marketplace.json
.grok-plugin/marketplace.json
marketplace.json
package.json
README.md          (the version table row)
```

Plus a `CHANGELOG.md` entry. Bump policy: a new command, a new concept type, or an API change is a minor bump. Internal optimizations and additive frontmatter are patches.

Full checklist in [[Worklog-Spec]].

## Local development

```bash
git clone https://github.com/SpillwaveSolutions/project-knowledge-capture
cd project-knowledge-capture
python3 tests/test_pkc.py
npm run validate
```

No install step and no dependencies — Python 3.12 and, for the docs preview only, Node 20.

To exercise a script against the golden fixture:

```bash
python3 scripts/pkc_pack.py features/user-authentication.md --bundle sample-knowledge --hops 2
```

`sample-knowledge/` is CI's test subject as well as the worked example. Keep it valid; a change that breaks it breaks the build.

## Contributing

This repo runs WikiTicket SDD on itself, which means two rules with no exceptions:

1. No commits on `main` — work on a branch.
2. Every commit message references a 26-character ULID or `#123`.

Both are enforced by git hooks and by CI. See [[Worklog-Spec]] for the full contract, and `docs/vision.md` for what PKC deliberately refuses to become.
