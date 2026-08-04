# Changelog

## 0.2.0 — 2026-08-04

### Added
- `pkc_pack.py` — progressive disclosure context packs (standalone, no okf-plugin required)
- `pkc_validate.py` — bundle structure + link validation
- `pkc_action_items.py` — extract meeting action items → TicketLink / worklog bridge (dry-run default)
- `/pkc-context` skill + command — “load institutional memory for this Feature”
- Post-edit hook `hooks/hooks.json` → `scripts/pkc-curate.sh` (catalog refresh + light validate)
- CI workflow (`.github/workflows/ci.yml`)
- Golden pack: `sample-knowledge/packs/user-authentication-pack.md`
- Roadmap + brainstorm backlog: `docs/roadmap.md`
- Tests for validate, pack, action-item extraction (12 total)

### Improved
- Sample meeting restored with full notes + action items for bridge demos

## 0.1.0 — 2026-08-03

### Added
- Dual-host Claude Code + Grok Build plugin packaging
- Skills: pkc-init, pkc-capture-meeting/experiment/discovery/decision, pkc-materialize, pkc-promote, pkc-link
- Slash command wrappers for all skills
- Deterministic scripts: pkc_common, pkc_capture, pkc_materialize, pkc_link, pkc_promote
- Templates for all PKC concept types
- knowledge-capturer specialist agent
- sample-knowledge auth institutional-memory chain
- Docs: PRD, design, OKF/WikiTicket integration, typed edges
- Preview explorer (docs + sample graph browser)
- Unit tests for capture, materialize, links, truth_state
