---
name: pkc-capture-decision
description: Capture a short decision statement as an OKF DecisionRecord (ADR-style) linked to Features, Designs, Requirements, Meetings, or Experiments. Use for ADRs, architecture choices, and lightweight decision logging.
---

# PKC Capture Decision

Lightweight ADR capture that plugs into the same graph as meetings and features.

## Process

1. Resolve knowledge root.
2. Collect classic ADR fields: context, decision, consequences, alternatives (optional), status (`proposed|accepted|deprecated|superseded`).
3. Write `decisions/<slug>.md`:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/pkc_capture.py" decision \
     --repo . \
     --title "Use JWT for session management" \
     --context "Need stateless auth for horizontal scale" \
     --decision "Use short-lived JWT access tokens + refresh cookies" \
     --consequences "Clients must handle refresh; revoke list optional" \
     --status accepted \
     --originates-from /meetings/2026-08-03-auth-design.md \
     --decides user-authentication
   ```
4. Typed edges (required when known):
   - `originates_from` → Meeting or Experiment
   - `decides` → Feature / Design / Requirement
   - `supersedes` → older DecisionRecord
5. Refresh `decisions/index.md` + `log.md`.
6. If status is `accepted`, suggest impact analysis via okf-plugin:
   ```bash
   # when okf-plugin is installed alongside
   python3 …/okf-graph.py impact <bundle> decisions/<slug>.md
   ```

## Template

Use `${CLAUDE_PLUGIN_ROOT}/templates/decision-record.md`.

## Done when

- DecisionRecord exists with Context / Decision / Consequences
- Links to origin and affected features when known
- Catalog + log updated
