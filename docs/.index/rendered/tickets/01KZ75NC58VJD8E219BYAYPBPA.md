# Agent auto-context injection

`01KZ75NC58VJD8E219BYAYPBPA` · epic/feature · **done**

Agents working on a Feature should get the knowledge graph without being asked.

## Children

- [[Ticket-01KZ75R1ZYFEZVPWDY73CK4P4N]] Detect Feature path or ULID in agent context — Recognise when the current work is about a specific Feature: a path under features/ in the conversation, or a worklog item whose materialized concept points at one. (done)
- [[Ticket-01KZ75R254CS97W8MNX9CV3SNF]] Inject tiny pack for the detected Feature — Given a detected Feature, produce the tiny pack (1 hop, max 8 nodes) and place it where the agent will read it. (done)
- [[Ticket-01KZ75R2ADREHM3JD22V5C5HE7]] Gate injection behind pack.auto_inject_on_feature — Auto-injection must be opt-out. (done)

Progress: 3/3 done

## Related tickets

- [github #2](https://github.com/SpillwaveSolutions/project-knowledge-capture/issues/2)
