---
name: pkc-capture-prd
description: Ingest a PRD journey section as Persona, UserJourney, JourneyStage, Scenario, and UserStory concepts, and link them to Features, Epics, and work Stories. Use when a PRD must drive story mapping.
---

# Capture a PRD journey

A user journey is the ordered path one persona takes to one goal. Stages become Features. In-scope stages become Epics. Each step becomes a UserStory, and the work-plane Story under that epic. Scenarios are concrete paths through a stage. Technology stays out of these nodes.

## Input

Write a JSON object and pass it to the capture script. Do not invent client names. Do not put component or vendor names in titles, outcomes, or acceptance lines.

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/pkc_capture.py" prd \
  --repo . \
  --author "${SECOND_BRAIN_IDENTITY}" \
  --file prd-journey.json
```

`--no-backlog` writes only the product plane (no Epic, no work Story).

```json
{
  "personas": [
    {
      "title": "Operator",
      "role": "operator",
      "goals": ["Finish the task and end the session"],
      "pain_points": ["Sessions that never expire"]
    }
  ],
  "journeys": [
    {
      "title": "Finish a signed-in task",
      "persona": "Operator",
      "goal": "The task is done and the session can end",
      "trigger": "The operator opens the product",
      "end_state": "The task is done and the session is closed",
      "golden_thread": true,
      "stages": [
        {
          "title": "Establish a session",
          "outcome": "The operator has a session that will expire",
          "success_metric": "Time to a usable session",
          "feature": "User authentication",
          "in_scope": true,
          "scenarios": [
            {
              "title": "Session reaches its limit",
              "preconditions": "A session was issued",
              "steps": ["Wait past the limit", "Try the next action"],
              "success_outcome": "The next action is refused"
            }
          ],
          "stories": [
            {
              "title": "Session expires on its own",
              "capability": "have the session expire",
              "outcome": "a stolen token stops working",
              "priority": "must",
              "acceptance": ["An access token is rejected after the limit"],
              "requirement": "Secure session tokens",
              "requirement_ids": ["FR-001"]
            }
          ]
        }
      ]
    }
  ]
}
```

## Edges

| rel | Direction | Meaning |
|-----|-----------|---------|
| `for_persona` | UserJourney / JourneyStage / UserStory → Persona | Who |
| `covers` | UserJourney → JourneyStage | Journey contains the stage |
| `stage_of` | JourneyStage → UserJourney | Stage belongs to the journey |
| `realized_by` | JourneyStage → Feature, Scenario → UserStory | What delivers it |
| `derived_from` | Feature → JourneyStage, Epic → JourneyStage | Where the backlog node came from |
| `illustrates` | Scenario → JourneyStage | Concrete path through the stage |
| `has_scenario` | UserJourney → Scenario | Journey owns the scenario |
| `implements_step` | UserStory → JourneyStage | Story covers this step |
| `traces_to` | UserStory → Requirement | Requirement that supplies the content |
| `maps_to` | UserStory → Story | Product story to work-plane story |
| `child_of` | Story → Epic | Work story sits under the epic |
| `golden_thread_for` | UserJourney → Release | This journey is the release backbone |

`pack()` on the Feature reaches the stage in one hop (`realized_by` inbound and `derived_from` outbound) and the journey, persona, scenario, and user story in the second hop. Default `max_nodes` is 20, which is enough for a feature created from this capture. A crowded feature (the sample auth bundle) clips those hop-2 nodes until `max_nodes` is 60.

## Done when

- Persona, UserJourney, JourneyStage, Scenario, and UserStory files exist.
- The Feature `derived_from` the stage. The Epic `derived_from` the stage. The work Story `child_of` the epic.
- The UserStory `maps_to` the work Story and `traces_to` the Requirement.
- `python3 scripts/pkc_validate.py --bundle <root>` reports no errors.
- A 2-hop pack of the Feature includes the journey types when the node budget covers that neighborhood.
