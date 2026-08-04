# CLAUDE.md — project-knowledge-capture

Instructions for **Claude Code** when working in this repository or when the plugin is installed.

## What this project is

**Project Knowledge Capture (PKC)** is a Claude Code plugin that captures informal knowledge (meetings, experiments, discoveries, decisions) and materializes WikiTicket work into a durable **OKF** knowledge graph.

**Hosts:** Claude Code (primary packaging) and **Grok Build** (native zero-config compatibility). Do not add Grok-only features that break Claude Code.

## Plugin layout

```
.claude-plugin/plugin.json   # manifest (name: project-knowledge-capture)
.grok-plugin/                # optional Grok marketplace pin
skills/                      # portable intelligence (SKILL.md per skill)
commands/                    # slash command wrappers
agents/knowledge-capturer.md
scripts/                     # pkc_common, capture, materialize, link, promote
templates/                   # OKF concept skeletons
sample-knowledge/            # self-describing demo bundle
docs/                        # PRD, design, integration
```

Use `${CLAUDE_PLUGIN_ROOT}` for all intra-plugin paths in skill instructions.

## Skills (auto-invoke)

| Skill | Trigger themes |
|-------|----------------|
| pkc-init | scaffold knowledge/, new PKC bundle |
| pkc-capture-meeting | meeting notes, transcript, standup decisions |
| pkc-capture-experiment | spike, experiment, POC results |
| pkc-capture-discovery | research, competitive scan, user findings |
| pkc-capture-decision | ADR, decision record, architecture choice |
| pkc-materialize | sync worklog, import tickets into OKF |
| pkc-promote | promote discovery/experiment to feature/requirement |
| pkc-link | typed edge, connect concepts, relates to |

## Working rules

1. Write **valid OKF Markdown** only (no hidden DBs).
2. Prefer `scripts/pkc_*.py` for deterministic file ops.
3. Absolute links: `[Title](/features/….md)`.
4. Typed `links[].rel` for PKC relations (`decides`, `informs`, `originates_from`, …).
5. Idempotent paths: `meetings/YYYY-MM-DD-slug.md`, stable slugs for decisions.
6. Never hand-edit WikiTicket `.work/*.jsonl`.
7. Do not overwrite `truth_state: snapshot|superseded|archived` without force/assent.
8. Keep each `SKILL.md` focused; deep material in `docs/` and `templates/`.
9. Bump version in `.claude-plugin/plugin.json` on release.
10. Run `python3 tests/test_pkc.py` after script changes.

## Dual-host note

Grok Build loads this same tree. Prefer Claude plugin conventions so both hosts stay aligned. See [AGENTS.md](./AGENTS.md).
