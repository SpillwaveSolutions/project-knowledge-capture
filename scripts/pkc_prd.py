#!/usr/bin/env python3
"""Capture a PRD narrative (persona, journey, stage, scenario, user story)
and link it to the product plane and, by default, the work-plane backlog.

Story (WikiTicket) stays the work item. UserStory is the product slice.
A journey stage becomes a Feature. An in-scope stage becomes an Epic.
A user story becomes a work Story under that epic.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pkc_common import (  # noqa: E402
    add_typed_link,
    append_log,
    concept_ref,
    path_for_type,
    refresh_catalog_index,
    scrub_text,
    slugify,
    utc_now,
    write_knowledge,
)


def _scrub(text: str) -> str:
    clean, _ = scrub_text(text or "")
    return clean


def _fm(
    typ: str,
    title: str,
    description: str,
    tags: list[str],
    wiki_prefix: str,
    slug: str,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    fm: dict[str, Any] = {
        "type": typ,
        "title": title,
        "description": (description or title)[:200],
        "tags": tags,
        "timestamp": utc_now(),
        "status": "active",
        "verified": False,
        "generated": True,
        "stable_timestamp": True,
        "wiki_key": f"{wiki_prefix}-{slug}",
        "truth_state": "current",
    }
    if extra:
        for key, value in extra.items():
            if value is not None and value != [] and value != "":
                fm[key] = value
    return fm


def _related(links: list[dict[str, str]]) -> str:
    if not links:
        return ""
    lines = "\n## Related\n\n"
    for link in links:
        lines += f"- [{link['target']}]({link['target']}) (`{link['rel']}`)\n"
    return lines


def _write(
    bundle: Path,
    *,
    author: str,
    typ: str,
    title: str,
    description: str,
    tags: list[str],
    wiki_prefix: str,
    body: str,
    links: list[dict[str, str]],
    extra: dict[str, Any] | None = None,
    catalog: str,
) -> tuple[str, str]:
    slug = slugify(title)
    rel = path_for_type(typ, slug)
    fm = _fm(typ, title, description, tags, wiki_prefix, slug, extra)
    if links:
        fm["links"] = links
    text = body.rstrip() + "\n" + _related(links)
    _, action = write_knowledge(bundle, rel, fm, text, author=author)
    refresh_catalog_index(bundle, catalog)
    return rel, action


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [_scrub(value)] if value.strip() else []
    return [_scrub(str(item)) for item in value if str(item).strip()]


def capture_persona(
    bundle: Path,
    *,
    author: str,
    title: str,
    role: str = "",
    goals: list[str] | None = None,
    pain_points: list[str] | None = None,
    context: str = "",
) -> list[tuple[str, str]]:
    goals = _as_list(goals)
    pain_points = _as_list(pain_points)
    goal_md = "\n".join(f"- {g}" for g in goals) or "_TBD_"
    pain_md = "\n".join(f"- {p}" for p in pain_points) or "_TBD_"
    body = f"""# {title}

## Role

{_scrub(role) or title}

## Goals

{goal_md}

## Pain points

{pain_md}

## Context

{_scrub(context) or '_TBD_'}
"""
    rel, action = _write(
        bundle,
        author=author,
        typ="Persona",
        title=title,
        description=role or title,
        tags=["persona"],
        wiki_prefix="persona",
        body=body,
        links=[],
        extra={"role": _scrub(role), "goals": goals, "pain_points": pain_points},
        catalog="personas",
    )
    append_log(bundle, f"Captured persona: {title}")
    return [(rel, action)]


def capture_user_journey(
    bundle: Path,
    *,
    author: str,
    title: str,
    goal: str,
    persona: str,
    trigger: str = "",
    end_state: str = "",
    golden_thread: bool = False,
    release: str | None = None,
    stages: list[str] | None = None,
    scenarios: list[str] | None = None,
) -> list[tuple[str, str]]:
    links: list[dict[str, str]] = [
        {"target": concept_ref(persona, "personas"), "rel": "for_persona"}
    ]
    for stage in stages or []:
        links.append({"target": concept_ref(stage, "journey-stages"), "rel": "covers"})
    for scenario in scenarios or []:
        links.append({"target": concept_ref(scenario, "scenarios"), "rel": "has_scenario"})
    if release:
        links.append({"target": concept_ref(release, "releases"), "rel": "golden_thread_for"})
    stage_md = "\n".join(f"- [{concept_ref(s, 'journey-stages')}]({concept_ref(s, 'journey-stages')})" for s in (stages or [])) or "_TBD_"
    body = f"""# {title}

## Goal

{_scrub(goal)}

## Trigger

{_scrub(trigger) or '_TBD_'}

## End state

{_scrub(end_state) or '_TBD_'}

## Stages

{stage_md}
"""
    rel, action = _write(
        bundle,
        author=author,
        typ="UserJourney",
        title=title,
        description=goal,
        tags=["journey", "golden-thread"] if golden_thread else ["journey"],
        wiki_prefix="journey",
        body=body,
        links=links,
        extra={
            "goal": _scrub(goal),
            "trigger": _scrub(trigger),
            "end_state": _scrub(end_state),
            "golden_thread": bool(golden_thread),
        },
        catalog="journeys",
    )
    append_log(bundle, f"Captured user journey: {title}")
    return [(rel, action)]


def _ensure_named(
    bundle: Path,
    *,
    author: str,
    typ: str,
    title: str,
    catalog: str,
    wiki_prefix: str,
    tags: list[str],
    extra: dict[str, Any] | None = None,
) -> str:
    """Create a thin concept if it is not already on disk. Return its absolute path."""
    target = concept_ref(title, catalog)
    rel = target.lstrip("/")
    if (bundle / rel).is_file():
        return target
    _write(
        bundle,
        author=author,
        typ=typ,
        title=title,
        description=title,
        tags=tags,
        wiki_prefix=wiki_prefix,
        body=f"# {title}\n\n_Created from a journey stage. Fill the product detail here._\n",
        links=[],
        extra=extra,
        catalog=catalog,
    )
    return target


def capture_journey_stage(
    bundle: Path,
    *,
    author: str,
    title: str,
    journey: str,
    outcome: str = "",
    success_metric: str = "",
    feature: str | None = None,
    persona: str | None = None,
    order: int | None = None,
) -> list[tuple[str, str]]:
    feature_title = feature or title
    feature_target = _ensure_named(
        bundle,
        author=author,
        typ="Feature",
        title=feature_title,
        catalog="features",
        wiki_prefix="feature",
        tags=["feature"],
        extra={"priority": "medium"},
    )
    links = [
        {"target": concept_ref(journey, "journeys"), "rel": "stage_of"},
        {"target": feature_target, "rel": "realized_by"},
    ]
    if persona:
        links.append({"target": concept_ref(persona, "personas"), "rel": "for_persona"})
    body = f"""# {title}

## Outcome

{_scrub(outcome) or title}

## Success metric

{_scrub(success_metric) or '_TBD_'}

## Feature

This stage is delivered by [{feature_target}]({feature_target}).
"""
    rel, action = _write(
        bundle,
        author=author,
        typ="JourneyStage",
        title=title,
        description=outcome or title,
        tags=["journey-stage"],
        wiki_prefix="stage",
        body=body,
        links=links,
        extra={
            "outcome": _scrub(outcome),
            "success_metric": _scrub(success_metric),
            "order": order,
        },
        catalog="journey-stages",
    )
    # The feature asserts where it came from. Inbound `realized_by` already
    # makes the stage visible from a pack of the feature.
    feature_path = bundle / feature_target.lstrip("/")
    if add_typed_link(feature_path, f"/{rel}", "derived_from") == "error":
        print(f"warning: no derived_from edge written, {feature_target} not found", file=sys.stderr)
    append_log(bundle, f"Captured journey stage: {title}")
    return [(rel, action)]


def capture_scenario(
    bundle: Path,
    *,
    author: str,
    title: str,
    stage: str,
    preconditions: str = "",
    steps: list[str] | None = None,
    success_outcome: str = "",
    stories: list[str] | None = None,
) -> list[tuple[str, str]]:
    steps = _as_list(steps)
    links = [{"target": concept_ref(stage, "journey-stages"), "rel": "illustrates"}]
    for story in stories or []:
        links.append({"target": concept_ref(story, "user-stories"), "rel": "realized_by"})
    step_md = "\n".join(f"{i}. {step}" for i, step in enumerate(steps, start=1)) or "_TBD_"
    body = f"""# {title}

## Preconditions

{_scrub(preconditions) or '_TBD_'}

## Steps

{step_md}

## Success outcome

{_scrub(success_outcome) or '_TBD_'}
"""
    rel, action = _write(
        bundle,
        author=author,
        typ="Scenario",
        title=title,
        description=success_outcome or title,
        tags=["scenario"],
        wiki_prefix="scenario",
        body=body,
        links=links,
        extra={"preconditions": _scrub(preconditions), "steps": steps, "success_outcome": _scrub(success_outcome)},
        catalog="scenarios",
    )
    append_log(bundle, f"Captured scenario: {title}")
    return [(rel, action)]


def capture_user_story(
    bundle: Path,
    *,
    author: str,
    title: str,
    persona: str,
    capability: str,
    outcome: str,
    stage: str,
    priority: str = "must",
    acceptance: list[str] | None = None,
    requirement: str | None = None,
    requirement_ids: list[str] | None = None,
    work_story: str | None = None,
) -> list[tuple[str, str]]:
    acceptance = _as_list(acceptance)
    requirement_ids = _as_list(requirement_ids)
    persona_name = persona
    links = [
        {"target": concept_ref(persona, "personas"), "rel": "for_persona"},
        {"target": concept_ref(stage, "journey-stages"), "rel": "implements_step"},
    ]
    if requirement:
        req_target = _ensure_named(
            bundle,
            author=author,
            typ="Requirement",
            title=requirement,
            catalog="requirements",
            wiki_prefix="req",
            tags=["requirement"],
            extra={"priority": priority},
        )
        links.append({"target": req_target, "rel": "traces_to"})
    if work_story:
        links.append({"target": concept_ref(work_story, "stories"), "rel": "maps_to"})
    acc_md = "\n".join(f"- {item}" for item in acceptance) or "_TBD_"
    ids = ", ".join(requirement_ids) if requirement_ids else "_none_"
    body = f"""# {title}

As a {persona_name}, I want {_scrub(capability)}, so that {_scrub(outcome)}.

## Acceptance

{acc_md}

## Requirement ids

{ids}
"""
    rel, action = _write(
        bundle,
        author=author,
        typ="UserStory",
        title=title,
        description=outcome or capability,
        tags=["user-story", priority],
        wiki_prefix="user-story",
        body=body,
        links=links,
        extra={
            "persona": persona_name,
            "capability": _scrub(capability),
            "outcome": _scrub(outcome),
            "priority": priority,
            "acceptance_criteria": acceptance,
            "requirement_ids": requirement_ids,
        },
        catalog="user-stories",
    )
    append_log(bundle, f"Captured user story: {title}")
    return [(rel, action)]


def _capture_epic(
    bundle: Path,
    *,
    author: str,
    title: str,
    stage: str,
    outcome: str,
) -> tuple[str, str]:
    links = [{"target": concept_ref(stage, "journey-stages"), "rel": "derived_from"}]
    body = f"""# {title}

## Goal

{_scrub(outcome) or title}

## Scope

In scope for the release that includes this journey stage. Out of scope stays off this epic.
"""
    rel, action = _write(
        bundle,
        author=author,
        typ="Epic",
        title=title,
        description=outcome or title,
        tags=["epic", "work"],
        wiki_prefix="epic",
        body=body,
        links=links,
        extra={"level": "epic", "kind": "feature", "status": "open"},
        catalog="epics",
    )
    return rel, action


def _capture_work_story(
    bundle: Path,
    *,
    author: str,
    title: str,
    epic: str,
    feature: str | None,
    outcome: str,
) -> tuple[str, str]:
    links = [{"target": concept_ref(epic, "epics"), "rel": "child_of"}]
    if feature:
        links.append({"target": concept_ref(feature, "features"), "rel": "implements"})
    body = f"""# {title}

## Story

{_scrub(outcome) or title}

Work-plane item. The product statement lives on the UserStory that `maps_to` this node.
"""
    rel, action = _write(
        bundle,
        author=author,
        typ="Story",
        title=title,
        description=outcome or title,
        tags=["story", "work"],
        wiki_prefix="story",
        body=body,
        links=links,
        extra={"level": "story", "kind": "feature", "status": "open"},
        catalog="stories",
    )
    return rel, action


def capture_prd(
    bundle: Path,
    *,
    author: str,
    spec: dict[str, Any],
    materialize_backlog: bool = True,
) -> list[tuple[str, str]]:
    """Turn one PRD journey section into linked OKF concepts.

    `spec` keys: `personas`, `journeys`. See `skills/pkc-capture-prd/SKILL.md`.
    """
    results: list[tuple[str, str]] = []
    for persona in spec.get("personas") or []:
        results.extend(
            capture_persona(
                bundle,
                author=author,
                title=persona["title"],
                role=persona.get("role") or "",
                goals=persona.get("goals"),
                pain_points=persona.get("pain_points"),
                context=persona.get("context") or "",
            )
        )

    for journey in spec.get("journeys") or []:
        journey_title = journey["title"]
        persona_title = journey["persona"]
        stage_titles: list[str] = []
        scenario_titles: list[str] = []
        for index, stage in enumerate(journey.get("stages") or [], start=1):
            stage_title = stage["title"]
            stage_titles.append(stage_title)
            feature_title = stage.get("feature") or stage_title
            results.extend(
                capture_journey_stage(
                    bundle,
                    author=author,
                    title=stage_title,
                    journey=journey_title,
                    outcome=stage.get("outcome") or "",
                    success_metric=stage.get("success_metric") or "",
                    feature=feature_title,
                    persona=stage.get("persona") or persona_title,
                    order=stage.get("order") or index,
                )
            )
            in_scope = stage.get("in_scope", True)
            epic_title = None
            if materialize_backlog and in_scope:
                epic_title = stage.get("epic") or stage_title
                results.append(
                    _capture_epic(
                        bundle,
                        author=author,
                        title=epic_title,
                        stage=stage_title,
                        outcome=stage.get("outcome") or "",
                    )
                )
            story_titles: list[str] = []
            for story in stage.get("stories") or []:
                story_title = story["title"]
                story_titles.append(story_title)
                story_persona = story.get("persona") or stage.get("persona") or persona_title
                work_ref = None
                if materialize_backlog and in_scope and epic_title:
                    work_ref = story_title
                    results.append(
                        _capture_work_story(
                            bundle,
                            author=author,
                            title=story_title,
                            epic=epic_title,
                            feature=feature_title,
                            outcome=story.get("outcome") or "",
                        )
                    )
                results.extend(
                    capture_user_story(
                        bundle,
                        author=author,
                        title=story_title,
                        persona=story_persona,
                        capability=story.get("capability") or story_title,
                        outcome=story.get("outcome") or "",
                        stage=stage_title,
                        priority=story.get("priority") or "must",
                        acceptance=story.get("acceptance"),
                        requirement=story.get("requirement"),
                        requirement_ids=story.get("requirement_ids"),
                        work_story=story_title if work_ref else None,
                    )
                )
            for scenario in stage.get("scenarios") or []:
                scenario_titles.append(scenario["title"])
                results.extend(
                    capture_scenario(
                        bundle,
                        author=author,
                        title=scenario["title"],
                        stage=stage_title,
                        preconditions=scenario.get("preconditions") or "",
                        steps=scenario.get("steps"),
                        success_outcome=scenario.get("success_outcome") or "",
                        stories=story_titles,
                    )
                )
        results.extend(
            capture_user_journey(
                bundle,
                author=author,
                title=journey_title,
                goal=journey.get("goal") or journey_title,
                persona=persona_title,
                trigger=journey.get("trigger") or "",
                end_state=journey.get("end_state") or "",
                golden_thread=bool(journey.get("golden_thread")),
                release=journey.get("release"),
                stages=stage_titles,
                scenarios=scenario_titles,
            )
        )
    append_log(bundle, "Captured PRD journey section")
    return results


def load_spec(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit("PRD journey file must be a JSON object")
    return data
