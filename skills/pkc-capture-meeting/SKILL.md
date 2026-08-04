---
name: pkc-capture-meeting
description: Capture meeting notes into OKF Meeting concepts, extract DecisionRecords, and optionally create WikiTicket action items + TicketLinks. Use when the user pastes meeting notes, transcripts, or asks to record a meeting decision trail.
---

# PKC Capture Meeting

Turn messy meeting notes into durable OKF concepts under the project knowledge root.

## When to use

- User pastes meeting notes / transcript
- User says “capture this meeting”, “record decisions from standup”, etc.
- Action items need optional WikiTicket tickets

## Inputs

| Input | Required | Notes |
|-------|----------|-------|
| Notes (paste, file path, or transcript) | yes | Free text |
| Title | no | Infer from first heading or date + topic |
| Date | no | ISO `YYYY-MM-DD`; default today |
| Attendees | no | Parse from notes when present |
| Knowledge root | no | From `.pkc/config.yml` → `knowledge` / `.okf` / `sample-knowledge` |
| Create tickets | no | Only if user asks or config `bridge.wikiticket: true` |

## Process

1. **Resolve knowledge root**
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/pkc_common.py" resolve-root --repo .
   ```
   If missing, run **pkc-init** skill or:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/pkc_common.py" init-bundle --repo . --bundle knowledge
   ```

2. **Structure the notes**
   - Title, date, attendees, duration if known
   - Discussion summary (concise)
   - **Extract decisions** as separate `DecisionRecord` concepts
   - **Action items** as a list (owner + due if present)

3. **Write concepts** (prefer helper for paths/idempotency, then refine body):
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/pkc_capture.py" meeting \
     --repo . \
     --title "Auth design discussion" \
     --date 2026-08-03 \
     --attendees "rick,alice" \
     --notes-file /tmp/notes.md \
     --decision "Use JWT for session management"
   ```
   Or hand-author from `${CLAUDE_PLUGIN_ROOT}/templates/meeting.md` and
   `decision-record.md`.

4. **Frontmatter rules**
   - `type: Meeting` / `type: DecisionRecord`
   - Absolute links: `[Label](/decisions/….md)`
   - Typed edges:
     - Meeting → Decision: `rel: decides`
     - Decision → Meeting: `rel: originates_from`
     - Decision → Feature: `rel: decides` (when feature known)
   - Set `wiki_key`, `truth_state: current`, `timestamp` (ISO-8601)

5. **Idempotency**
   - Path: `meetings/YYYY-MM-DD-<slug>.md`
   - Re-running on the same title+date **updates** the file; do not create duplicates

6. **Catalogs & log**
   - Refresh `meetings/index.md` and `decisions/index.md`
   - Append one line to `log.md`

7. **Optional WikiTicket bridge**
   - Only when user assents or config enables it
   - Create work items via repo-local `bin/worklog` (never hand-edit `.work/*.jsonl`)
   - Emit `TicketLink` concepts under `tickets/` with `worklog_id`
   - PKC is **not** source of truth for status

8. **Validate** (if okf-plugin available):
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/../okf-plugin/scripts/okf-graph.py" validate <bundle> 2>/dev/null \
     || okf validate <bundle> 2>/dev/null \
     || true
   ```

## Output report

```
Created:
  meetings/2026-08-03-auth-design.md
  decisions/use-jwt-for-session.md
Updated catalogs: meetings, decisions
Optional tickets: (none | list)
```

## Done when

- Meeting file exists with complete frontmatter + notes body
- Each extracted decision is its own DecisionRecord with `originates_from` link
- Catalogs and log updated
- No duplicate meetings for the same date+slug
