# AGENTS.md — project-knowledge-capture

Agent-facing instructions for **Grok Build**, Codex-style runners, and any host that loads this repository as a Claude-compatible plugin.

## Host compatibility

| Host | How this plugin loads |
|------|------------------------|
| **Claude Code** | Native plugin (`.claude-plugin/plugin.json`, skills, agents, commands) |
| **Grok Build** | Zero-config Claude plugin compatibility — skills/agents discovered automatically |

This repo is intentionally **one plugin, two hosts**. Do not introduce Grok-only packaging that diverges from Claude conventions unless adding optional metadata (e.g. `.grok-plugin/marketplace.json`).

## Mission

Turn project reasoning into a durable OKF knowledge graph:

- Capture meetings, experiments, discoveries, decisions
- Materialize WikiTicket work items / docs into the same graph
- Maintain typed edges for impact analysis and progressive disclosure
- Remain Git-native and PR-reviewable

## Component map

- **Skills** — `skills/*/SKILL.md`
- **Commands** — `commands/*.md` (slash entry points)
- **Agent** — `agents/knowledge-capturer.md`
- **Scripts** — `scripts/pkc_*.py` (deterministic helpers)
- **Templates** — `templates/*.md`
- **Sample bundle** — `sample-knowledge/`
- **Docs** — `docs/`

Plugin root variable: `${CLAUDE_PLUGIN_ROOT}`.

## Operating principles

1. **OKF format only** — frontmatter + body + absolute Markdown links + optional `links[].rel`.
2. Prefer **deterministic scripts** for path selection, materialize, and link; agents still extract structure from free text.
3. **Idempotent** — same meeting date+slug updates; materialize reports created/updated/skipped.
4. **Never invent edges.**
5. **WikiTicket is source of truth for work status** — do not hand-edit `.work/*.jsonl`; use `bin/worklog`.
6. Respect `truth_state` (`current` | `snapshot` | `superseded` | `archived`).
7. Complete frontmatter: `type`, `title`, `description`, `timestamp` at minimum; prefer `wiki_key`, `verified`, `status`.
8. After capture, update catalog `index.md` files and `log.md`.
9. When okf-plugin is present, validate and offer 2-hop packs for Features.
10. Working in an isolated worktree: verify base with `git log --oneline -3` before large rewrites.

## Common commands

```bash
python3 scripts/pkc_common.py init-bundle --repo . --bundle knowledge
python3 scripts/pkc_capture.py meeting --title "…" --date 2026-08-03 --notes "…"
python3 scripts/pkc_materialize.py --repo . --fold tests/fixtures/fold.json
python3 scripts/pkc_link.py decisions/x.md /features/y.md --rel decides --repo .
python3 tests/test_pkc.py
```

## Companion plugins

- **okf-plugin** (`okf-graph-eng`) — impact, query/pack, validate, visualize
- **wiki_ticket_sdd** — worklog, plans, wiki publish

Install all three side-by-side; PKC only writes Markdown under the knowledge root.
