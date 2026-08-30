---
name: pkc-doctor
description: Run a one-screen health check on a PKC knowledge bundle — broken links, orphans, thin Features, decision conflicts, open Questions, stale Discoveries/Assumptions, toolchain (ripgrep). Use when auditing knowledge quality or before a release.
---

# PKC Doctor

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/pkc_doctor.py" --repo . --bundle knowledge
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/pkc_doctor.py" --bundle sample-knowledge --strict
```

## What it reports

| Kind | Meaning |
|------|---------|
| broken_link | Absolute link target missing |
| orphan | No inbound/outbound edges |
| thin_feature | Feature lacks Meeting/Decision/Experiment/Design provenance |
| decision_conflict | Multiple accepted Decisions decide the same Feature |
| open_question | Question with `blocks` on a Feature still open |
| stale | Discovery/Assumption past stale_after or old + unverified |
| unvalidated_assumption | Assumption not yet proven |
| missing_catalog | Expected catalog directory absent |

Also reports **toolchain**: Python, ripgrep found/missing, SQLite FTS5. If rg is missing, offer `/pkc-setup` (consent-gated install). Do not install from this skill.

## Done when

- Report shown with severities
- User knows top 3 fixes (if any)
- User knows whether search/pack will use rg or a full scan
