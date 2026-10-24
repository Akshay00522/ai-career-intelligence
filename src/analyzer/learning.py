
"""Learning plan: order missing skills (prerequisites first) with effort and resources."""
from __future__ import annotations

import heapq
import json
import math
from functools import lru_cache
from pathlib import Path

from .skills import load_taxonomy, prerequisites

DEFAULT_RESOURCES = Path(__file__).resolve().parents[2] / "data" / "resources.json"
DEFAULT_HOURS = 20
IMPORTANCE_RANK = {"required": 0, "preferred": 1, "prerequisite": 2}


@lru_cache(maxsize=2)
def load_resources(path: str | None = None) -> dict:
    """Load the learning-resource catalogue."""
    with open(path or DEFAULT_RESOURCES, encoding="utf-8") as f:
        return json.load(f)


def _info(skill: str) -> dict:
    return load_resources().get(skill, {})


def _hours(skill: str) -> int:
    return _info(skill).get("hours", DEFAULT_HOURS)


def _closure(skill: str, have: frozenset | set = frozenset()) -> list[str]:
    """Return prerequisites, stopping traversal at skills the user already knows."""
    seen: list[str] = []
    visited: set[str] = set()
    stack = list(prerequisites(skill))

    while stack:
        current = stack.pop()

        if current in visited:
            continue

        visited.add(current)
        seen.append(current)

        if current not in have:
            stack.extend(prerequisites(current))

    return seen


def _choose_option(
    options: list[str],
    have: set[str],
    demand: dict[str, float],
) -> str:
    """Choose the lowest-cost alternative, using market demand to break ties."""
    def cost(skill: str) -> tuple:
        missing_prereqs = [
            prereq for prereq in _closure(skill, have)
            if prereq not in have
        ]
        total_hours = _hours(skill) + sum(
            _hours(prereq) for prereq in missing_prereqs
        )
        return (
            total_hours,
            -demand.get(skill, 0.0),
            skill,
        )

    return min(options, key=cost)


def build_plan(
    gaps: list[dict],
    have: set[str],
    demand: dict[str, float] | None = None,
    hours_per_week: float = 10,
) -> dict:
    """Build a prerequisite-aware learning plan from identified skill gaps."""
    demand = demand or {}
    taxonomy = load_taxonomy()
    known = set(have)

    # Collect missing skills and their prerequisites.
    nodes: dict[str, str] = {}

    for gap in gaps:
        options = gap.get("options", [])
        if not options:
            continue

        importance = gap.get("importance", "required")
        if importance not in ("required", "preferred"):
            importance = "required"

        skill = _choose_option(options, known, demand)

        for dependency in [skill] + _closure(skill, known):
            if dependency in known:
                continue

            dependency_importance = (
                importance if dependency == skill else "prerequisite"
            )

            existing = nodes.get(dependency)
            if (
                existing is None
                or IMPORTANCE_RANK[dependency_importance]
                < IMPORTANCE_RANK[existing]
            ):
                nodes[dependency] = dependency_importance

    if not nodes:
        return {
            "steps": [],
            "total_hours": 0,
            "hours_per_week": hours_per_week,
            "estimated_weeks": 0,
        }

    # Propagate the highest urgency from dependent skills to prerequisites.
    urgency = {
        skill: IMPORTANCE_RANK[importance]
        for skill, importance in nodes.items()
    }

    changed = True
    while changed:
        changed = False

        for skill in nodes:
            for dependency in _closure(skill, known):
                if dependency in nodes and urgency[skill] < urgency[dependency]:
                    urgency[dependency] = urgency[skill]
                    changed = True

    # Topologically sort so every prerequisite appears before its dependents.
    dependencies = {
        skill: [
            prereq for prereq in prerequisites(skill)
            if prereq in nodes
        ]
        for skill in nodes
    }
    indegree = {
        skill: len(prereqs)
        for skill, prereqs in dependencies.items()
    }
    dependents: dict[str, list[str]] = {
        skill: [] for skill in nodes
    }

    for skill, prereqs in dependencies.items():
        for prereq in prereqs:
            dependents[prereq].append(skill)

    def priority(skill: str) -> tuple:
        return (
            urgency[skill],
            -demand.get(skill, 0.0),
            _hours(skill),
            skill,
        )

    heap = [
        (priority(skill), skill)
        for skill, degree in indegree.items()
        if degree == 0
    ]
    heapq.heapify(heap)

    ordered: list[str] = []

    while heap:
        _, skill = heapq.heappop(heap)
        ordered.append(skill)

        for dependent in dependents[skill]:
            indegree[dependent] -= 1
            if indegree[dependent] == 0:
                heapq.heappush(heap, (priority(dependent), dependent))

    if len(ordered) != len(nodes):
        unresolved = sorted(set(nodes) - set(ordered))
        raise ValueError(
            "Cycle detected in skill prerequisites involving: "
            + ", ".join(unresolved)
        )

    # Build the final learning steps.
    steps: list[dict] = []
    total_hours = 0

    for index, skill in enumerate(ordered, start=1):
        info = _info(skill)
        hours = _hours(skill)
        total_hours += hours

        needed_by = [
            target
            for target in nodes
            if skill in dependencies[target]
            and nodes[skill] == "prerequisite"
        ]

        resources = info.get("resources", [])
        if not isinstance(resources, list):
            resources = []

        steps.append({
            "order": index,
            "skill": skill,
            "importance": nodes[skill],
            "category": taxonomy.get(skill, {}).get("category", "other"),
            "hours": hours,
            "market_demand": round(demand.get(skill, 0.0), 2),
            "why": (
                f"Prerequisite for {', '.join(needed_by)}."
                if needed_by
                else f"{nodes[skill].capitalize()} skill missing from your resume."
            ),
            "practice": info.get(
                "practice",
                f"Build a small project using {skill} and add it to your resume.",
            ),
            "resources": resources,
            "prerequisites": dependencies[skill],
        })

    estimated_weeks = (
        math.ceil(total_hours / hours_per_week)
        if hours_per_week > 0 and total_hours
        else 0
    )

    return {
        "steps": steps,
        "total_hours": total_hours,
        "hours_per_week": hours_per_week,
        "estimated_weeks": estimated_weeks,
    }
