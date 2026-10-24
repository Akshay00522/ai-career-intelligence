"""Skill taxonomy: loading, alias matching, implication expansion.

The taxonomy (data/skills.json) maps each canonical skill to:
  aliases  - surface forms found in text ("sklearn" -> scikit-learn)
  implies  - skills a person necessarily has if they have this one
             (scikit-learn implies python and machine learning)
  prereqs  - extra learning prerequisites (not implied by having the skill)
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

DEFAULT_TAXONOMY = Path(__file__).resolve().parents[2] / "data" / "skills.json"


@dataclass(frozen=True)
class Mention:
    skill: str
    start: int
    end: int


@lru_cache(maxsize=4)
def load_taxonomy(path: str | None = None) -> dict:
    with open(path or DEFAULT_TAXONOMY, encoding="utf-8") as f:
        return json.load(f)


def _alias_pattern(alias: str, case_sensitive: bool) -> re.Pattern:
    # Lookarounds instead of \b so "c++", "c#", "ci/cd" match correctly, "java" does
    # not match inside "javascript" or "d3.js", and "R" does not match in "R&D".
    body = re.escape(alias)
    flags = 0 if case_sensitive else re.IGNORECASE
    return re.compile(rf"(?<![\w+#.]){body}(?![\w+#&])", flags)


@lru_cache(maxsize=4)
def _compiled(path: str | None = None) -> list[tuple[str, re.Pattern]]:
    taxonomy = load_taxonomy(path)
    return [
        (canonical, _alias_pattern(alias, meta.get("case_sensitive", False)))
        for canonical, meta in taxonomy.items()
        for alias in meta["aliases"]
    ]


def find_mentions(text: str, taxonomy_path: str | None = None) -> list[Mention]:
    """All skill mentions with positions, overlaps resolved (longest match wins).

    Longest-match resolution means "Azure ML" counts as azure only, not also as
    machine learning via the alias "ml".
    """
    raw = [
        Mention(canonical, m.start(), m.end())
        for canonical, pattern in _compiled(taxonomy_path)
        for m in pattern.finditer(text)
    ]
    raw.sort(key=lambda m: (-(m.end - m.start), m.start))
    taken: list[Mention] = []
    for m in raw:
        if all(m.end <= t.start or m.start >= t.end for t in taken):
            taken.append(m)
    return sorted(taken, key=lambda m: m.start)


def extract_skills(text: str, taxonomy_path: str | None = None) -> set[str]:
    """Canonical skills explicitly mentioned in `text`."""
    return {m.skill for m in find_mentions(text, taxonomy_path)}


def expand_implied(skills: set[str], taxonomy_path: str | None = None) -> tuple[set[str], set[str]]:
    """Close `skills` under 'implies'. Returns (all_skills, implied_only)."""
    taxonomy = load_taxonomy(taxonomy_path)
    result = set(skills)
    stack = list(skills)
    while stack:
        current = stack.pop()
        for implied in taxonomy.get(current, {}).get("implies", []):
            if implied not in result:
                result.add(implied)
                stack.append(implied)
    return result, result - set(skills)


def prerequisites(skill: str, taxonomy_path: str | None = None) -> list[str]:
    meta = load_taxonomy(taxonomy_path).get(skill, {})
    return list(dict.fromkeys(meta.get("implies", []) + meta.get("prereqs", [])))


def category_of(skill: str, taxonomy_path: str | None = None) -> str:
    return load_taxonomy(taxonomy_path).get(skill, {}).get("category", "other")
