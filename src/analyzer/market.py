"""Job-market analysis: which skills are in demand across a set of job descriptions."""
from __future__ import annotations

from pathlib import Path

from .skills import category_of, extract_skills


def load_jds(directory: str | Path) -> dict[str, str]:
    return {p.stem: p.read_text(encoding="utf-8") for p in sorted(Path(directory).glob("*.txt"))}


def skill_demand(jd_texts: list[str]) -> dict[str, float]:
    """Share of job descriptions (0-1) that mention each skill."""
    if not jd_texts:
        return {}
    counts: dict[str, int] = {}
    for text in jd_texts:
        for skill in extract_skills(text):
            counts[skill] = counts.get(skill, 0) + 1
    return {s: c / len(jd_texts) for s, c in counts.items()}


def top_skills(demand: dict[str, float], n: int = 15) -> list[dict]:
    ranked = sorted(demand.items(), key=lambda kv: (-kv[1], kv[0]))[:n]
    return [{"skill": s, "share": round(v, 3), "category": category_of(s)} for s, v in ranked]


def demand_by_category(demand: dict[str, float]) -> dict[str, float]:
    """Mean demand of the skills seen in each category."""
    buckets: dict[str, list[float]] = {}
    for skill, share in demand.items():
        buckets.setdefault(category_of(skill), []).append(share)
    return {c: round(sum(v) / len(v), 3) for c, v in sorted(buckets.items())}
