---
name: pkc-promote
description: Promote a Discovery, Experiment, or Meeting into a formal Requirement, Feature, Specification, Design, or DecisionRecord while preserving originates_from / informs provenance. Use when informal knowledge is ready to become durable product structure.
---

# PKC Promote

Lift informal capture into formal product concepts without losing provenance.

## Process

1. Identify source concept path (e.g. `discoveries/auth-competitor-scan.md`).
2. Choose target type: `Feature` | `Requirement` | `DecisionRecord` | `Specification` | `Design`.
3. Run helper or hand-author:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/pkc_promote.py" \
     discoveries/auth-competitor-scan.md \
     --to Feature \
     --title "User authentication" \
     --repo .
   ```
4. Ensure edges:
   - New formal concept → source: `originates_from` or retains `sources: [...]`
   - Source → new concept: soft `related_to` (helper adds this)
5. Refine body (acceptance criteria, status) after skeleton write.
6. Refresh catalogs + log.
7. Optionally create WikiTicket work item for the new Feature (bridge — user assent).

## Done when

- Formal concept exists under the correct catalog
- Provenance to the informal source is explicit
- User can run impact/query from okf-plugin on the new node
