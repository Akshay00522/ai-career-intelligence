
"""Render an analysis (and learning plan) as a Markdown report."""
from __future__ import annotations


def _list(items: list[str]) -> str:
    return ", ".join(items) if items else "none"


def to_markdown(analysis: dict, plan: dict | None = None) -> str:
    a = analysis
    available = a.get("score_status", "available") == "available"
    skill_score = a.get("skill_match_score", a.get("score"))
    text_similarity = a.get(
        "text_similarity_score", a.get("semantic_similarity", 0.0)
    )

    score_text = (
        f"{skill_score} / 100"
        if available and skill_score is not None
        else "Unavailable — no recognized job skills"
    )
    required_coverage = (
        f"{a['required_coverage']:.0%}" if available else "N/A"
    )
    preferred_coverage = (
        f"{a['preferred_coverage']:.0%}" if available else "N/A"
    )

    lines = [
        "# Skill-Gap Analysis Report",
        "",
        f"**Skill-match score: {score_text}**",
        "",
        "| Component | Value |",
        "|---|---|",
        f"| Required skills covered | {required_coverage} |",
        f"| Preferred skills covered | {preferred_coverage} |",
        f"| Text similarity (raw cosine; not a qualification score) | {text_similarity:.3f} |",
        "",
    ]

    for warning in a.get("warnings", []):
        lines += [f"> Warning: {warning}", ""]

    lines += [
        "## Required skills",
        "",
        f"- Matched: {_list(a['matched_required'])}",
        f"- Missing: {_list(a['missing_required'])}",
        "",
        "## Preferred skills",
        "",
        f"- Matched: {_list(a['matched_preferred'])}",
        f"- Missing: {_list(a['missing_preferred'])}",
        "",
    ]

    if a.get("matched_by_implication"):
        lines += [
            "_Counted via implied skills (e.g. scikit-learn implies machine learning): "
            f"{_list(a['matched_by_implication'])}._",
            "",
        ]

    lines += [
        "## Other skills on your resume",
        "",
        _list(a["extra_skills"]),
        "",
    ]

    if plan and plan.get("steps"):
        lines += [
            "## Learning plan",
            "",
            f"About **{plan['total_hours']} hours**, roughly "
            f"**{plan['estimated_weeks']} weeks** at "
            f"{plan['hours_per_week']:g} hours per week.",
            "",
        ]
        for step in plan["steps"]:
            lines += [
                f"### {step['order']}. {step['skill']} "
                f"({step['importance']}, ~{step['hours']} h)",
                "",
                step["why"],
                "",
                f"Practice: {step['practice']}",
                "",
            ]
            for resource in step["resources"]:
                lines.append(
                    f"- [{resource['title']}]({resource['url']}) - "
                    f"{resource['provider']}"
                )
            lines.append("")

    return "\n".join(lines)
