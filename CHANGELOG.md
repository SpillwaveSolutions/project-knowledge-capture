# Changelog

## 0.3.0 — 2026-08-04

### Added
- `pkc_doctor.py` / `/pkc-doctor` — broken links, orphans, thin Features, decision conflicts, open Questions, stale Discoveries, unvalidated Assumptions
- `Assumption` + `Question` concept types, catalogs, templates, capture helpers, skills
- `pkc_scrub.py` + auto-scrub on meeting/transcript capture (secrets + PII)
- `pkc_transcript.py` / `/pkc-capture-transcript` — Fireflies / Otter / Granola / speaker lines
- `pkc_pr_capture.py` / `/pkc-capture-pr` — GitHub PR → CodeChange (`gh` or JSON fixture)
- Tiny packs (`--tiny`: 1 hop / 8 nodes) + Mermaid graph export (`--mermaid`)
- Config schema `.pkc/config.schema.json` + expanded example config
- Preview: Graph (mermaid) + Doctor views
- Optional CI job for okf-plugin interop
- Sample Assumption + open Question linked to auth Feature
- 18 unit tests

### Improved
- Agent auto-inject guidance for Feature context packs
- Relations: `assumes`, `blocks`, `answers`, `validates`, `invalidates`

## 0.2.0 — 2026-08-04

### Added
- Context packs, validate, action-item bridge, curate hook, CI, golden pack, roadmap

## 0.1.0 — 2026-08-03

### Added
- Dual-host plugin, core capture/materialize skills, sample chain, templates
