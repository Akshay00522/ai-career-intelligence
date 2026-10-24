"""Thin orchestration layer shared by the CLI, the API and the UI (so logic is tested once)."""
from __future__ import annotations

from pathlib import Path

from .learning import build_plan
from .market import load_jds, skill_demand
from .pipeline import analyze


def run_analysis(
    resume_text: str,
    jd_text: str,
    method: str = "tfidf",
    hours_per_week: float = 10,
    market_dir: str | Path | None = None,
    include_plan: bool = True,
) -> dict:
    """Analyze one resume against one JD. Returns {"analysis": {...}, "plan": {...}}."""
    result = analyze(resume_text, jd_text, similarity_method=method)
    out = {"analysis": result.to_dict()}
    if include_plan:
        demand = skill_demand(list(load_jds(market_dir).values())) if market_dir else {}
        out["plan"] = build_plan(result.gaps, set(result.resume_skills), demand, hours_per_week)
    return out
