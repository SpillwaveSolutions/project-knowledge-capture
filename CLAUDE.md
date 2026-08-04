# CLAUDE.md — project-knowledge-capture

## What this is

**PKC** captures meetings, experiments, discoveries, decisions and materializes WikiTicket work into an OKF knowledge graph.

**Hosts:** Claude Code + Grok Build (same tree).

## Layout

```
.claude-plugin/   hooks/   skills/   commands/   agents/
scripts/          templates/   sample-knowledge/   docs/
```

## Skills

| Skill | When |
|-------|------|
| pkc-init | scaffold knowledge root |
| pkc-capture-* | meeting / experiment / discovery / decision |
| pkc-materialize | worklog → OKF |
| pkc-promote / pkc-link | formalize / connect |
| pkc-context | progressive disclosure pack |
| pkc-doctor | health check |
| pkc-capture-assumption / question | soft knowledge |
| pkc-capture-transcript / pr | ingest |

## Rules

1. Valid OKF Markdown only.
2. Use `scripts/pkc_*.py` for deterministic ops.
3. Absolute links + typed `rel`.
4. Idempotent paths; never invent edges.
5. No hand-edits to `.work/*.jsonl`.
6. Bump version in plugin manifests on release.
7. `python3 tests/test_pkc.py` after script changes.

## v0.2 extras

- `pkc_pack.py`, `pkc_validate.py`, `pkc_action_items.py`
- Post-edit `pkc-curate.sh`
- CI in `.github/workflows/ci.yml`
- Ideas: `docs/roadmap.md`

## v0.3

Doctor, assumptions/questions, scrub, transcript, PR capture, tiny packs, mermaid, config schema.
