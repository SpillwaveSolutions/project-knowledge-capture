# AGENTS.md — project-knowledge-capture

Agent-facing instructions for **Grok Build**, Codex-style runners, and Claude-compatible hosts.

## Host compatibility

| Host | How this plugin loads |
|------|------------------------|
| **Claude Code** | Native plugin (`.claude-plugin/plugin.json`, skills, agents, hooks, commands) |
| **Grok Build** | Zero-config Claude plugin compatibility |

One plugin, two hosts. Do not diverge packaging.

## Mission

Turn project reasoning into a durable OKF knowledge graph: capture informal knowledge, materialize WikiTicket work, maintain typed edges for packs and impact.

## Component map

- **Skills** — `skills/*/SKILL.md` (includes `pkc-context`)
- **Commands** — `commands/*.md`
- **Agent** — `agents/knowledge-capturer.md`
- **Hooks** — `hooks/hooks.json` → `scripts/pkc-curate.sh` (PostToolUse), `scripts/pkc_auto_context.py` (UserPromptSubmit)
- **Scripts** — `scripts/pkc_*.py`, `pkc-curate.sh`
- **Sample** — `sample-knowledge/` (+ `packs/`)
- **Work log** — `.work/*.jsonl` via `bin/worklog` (this repo now runs WikiTicket SDD on itself)
- **Roadmap** — `docs/roadmap.md`, **generated** from the work log; ideas and non-goals live in `docs/vision.md`

Plugin root: `${CLAUDE_PLUGIN_ROOT}`.

## Operating principles

1. OKF format only (frontmatter + body + absolute links + `links[].rel`).
2. Prefer deterministic scripts; agents extract structure from free text.
3. Idempotent writes; respect `truth_state`.
4. Never invent edges. Direction matters: `Decision --mitigates--> Risk` and
   `Acceptance --satisfies--> Feature`, never the reverse.
5. WikiTicket owns work **status** — use `bin/worklog`, never hand-edit jsonl.
6. Default context pack: **2 hops**, ~**20 nodes** (`pkc_pack` or okf pack). Token budget is **1/4 window**, fail-closed. Bodies off unless that node is the pack root.
7. After capture: catalogs + log.
8. Run `python3 tests/test_pkc.py` and `pkc_validate` after script changes.

## Common commands

```bash
python3 scripts/pkc_common.py init-bundle --repo . --bundle knowledge
python3 scripts/pkc_pack.py features/x.md --repo . --hops 2
python3 scripts/pkc_search.py JWT --bundle knowledge
python3 scripts/pkc_index.py status --bundle knowledge
python3 scripts/pkc_validate.py --bundle knowledge
python3 scripts/pkc_action_items.py meetings/….md --repo .   # dry-run
python3 tests/test_pkc.py
```

## v0.4

Search, digest, release notes, thread capture, federation, ADR import.

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

Commits: never on `main` (branch guard), and every message must reference a
26-char ULID or `#123` — both enforced by `hooks/` via `core.hooksPath`.

The work taxonomy (level / kind / milestone / planned) is documented in
`CLAUDE.md` between the `worklog:taxonomy` markers; the same rules apply here.
