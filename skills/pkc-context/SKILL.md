---
name: pkc-context
description: Build a progressive-disclosure context pack for a Feature (or any concept) including related Meetings, Experiments, DecisionRecords, and Designs. Use when starting work on a feature, needing historical rationale, or preparing agent context.
---

# PKC Context Pack

Give an agent the **minimum institutional memory** needed for a Feature or change — not the whole knowledge tree.

## When to use

- “What decided this feature?”
- “Load context for user-authentication”
- Starting implementation on a Feature / Design / Requirement
- Before a large change — pair with okf impact when available

## Process

1. Resolve knowledge root and target concept path.
2. Prefer **okf-plugin** when installed:
   ```bash
   python3 <okf-plugin>/scripts/okf-graph.py pack <bundle> features/<slug>.md --hops 2 --max-nodes 20
   ```
3. Otherwise use PKC standalone packer:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/pkc_pack.py" \
     features/user-authentication.md \
     --repo . \
     --hops 2 \
     --max-nodes 20 \
     --write knowledge/packs/
   ```
4. Present the pack as a short report:
   - Seed concept
   - DecisionRecords (with status)
   - Meetings / Experiments / Discoveries that informed it
   - Designs / Requirements / TicketLinks
   - Open questions / missing links
5. Offer impact analysis on the governing DecisionRecord if okf-plugin is present.

## Defaults

| Setting | Value |
|---------|-------|
| Hops | 2 |
| Max nodes | ~20 |
| Rank bias | Decision → Meeting → Experiment → Design → Requirement → Feature → Ticket → Code |

## Rules

- Never invent edges — only report links that exist.
- Prefer `verified: true` and `truth_state: current` nodes when summarizing.
- If the pack is thin, suggest capture skills (meeting/experiment/decision) to fill gaps.

## Done when

- Pack markdown produced (stdout or `packs/<slug>-pack.md`)
- User can act with rationale, not just the Feature file
