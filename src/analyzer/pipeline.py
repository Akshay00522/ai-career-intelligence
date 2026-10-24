
"""End-to-end analysis: resume + JD -> score, matches, and skill gaps."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from math import isfinite

from .jd_parser import build_requirements, split_jd
from .similarity import text_similarity
from .skills import category_of, expand_implied, extract_skills

DEFAULT_WEIGHTS = {"required": 0.60, "preferred": 0.15, "semantic": 0.25}
SEMANTIC_SCALE = {"tfidf": 2.0, "embedding": 1.0}


@dataclass
class AnalysisResult:
    score: float
    required_coverage: float
    preferred_coverage: float
    semantic_similarity: float
    matched_required: list[str] = field(default_factory=list)
    missing_required: list[str] = field(default_factory=list)
    matched_preferred: list[str] = field(default_factory=list)
    missing_preferred: list[str] = field(default_factory=list)
    matched_by_implication: list[str] = field(default_factory=list)
    extra_skills: list[str] = field(default_factory=list)
    gaps: list[dict] = field(default_factory=list)
    resume_skills: list[str] = field(default_factory=list)
    components: dict = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    score_status: str = "available"
    skill_match_score: float | None = None
    text_similarity_score: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)


def label(options) -> str:
    return " or ".join(sorted(options))


def blend(components: dict, weights: dict | None = None) -> float:
    """Weighted blend (0-1), renormalising weights for available components."""
    w = DEFAULT_WEIGHTS if weights is None else weights

    expected = set(DEFAULT_WEIGHTS)
    if set(w) != expected:
        raise ValueError(
            f"Weights must contain exactly these keys: {sorted(expected)}"
        )

    for key, value in w.items():
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not isfinite(value)
            or value < 0
        ):
            raise ValueError(f"Weight '{key}' must be a finite, non-negative number.")

    present = {k: v for k, v in components.items() if v is not None}
    total = sum(w[k] for k in present)
    if total == 0:
        return 0.0
    return sum(w[k] * v for k, v in present.items()) / total


def _check(requirements, have, explicit):
    matched, missing, implied_only = [], [], []
    for req in requirements:
        if req & have:
            matched.append(req)
            if not (req & explicit):
                implied_only.append(req)
        else:
            missing.append(req)
    return matched, missing, implied_only


def analyze(
    resume_text,
    jd_text,
    similarity_method="tfidf",
    weights=None,
    use_implications=True,
    use_or_groups=True,
) -> AnalysisResult:
    explicit = extract_skills(resume_text)
    have, implied = (
        expand_implied(explicit) if use_implications else (set(explicit), set())
    )

    req_text, pref_text = split_jd(jd_text)
    required = build_requirements(req_text, use_or_groups)

    req_singletons = {next(iter(r)) for r in required if len(r) == 1}
    preferred = [
        r
        for r in build_requirements(pref_text, use_or_groups)
        if r not in required
        and not (len(r) == 1 and r <= req_singletons)
    ]

    m_req, x_req, i_req = _check(required, have, explicit)
    m_pref, x_pref, i_pref = _check(preferred, have, explicit)

    sem_raw = text_similarity(resume_text, jd_text, method=similarity_method)
    sem = min(1.0, sem_raw * SEMANTIC_SCALE.get(similarity_method, 1.0))

    components = {
        "required": len(m_req) / len(required) if required else None,
        "preferred": len(m_pref) / len(preferred) if preferred else None,
        "semantic": sem,
    }

    skill_match_available = bool(required or preferred)
    legacy_score = round(blend(components, weights) * 100, 1)

    warnings = []
    if not skill_match_available:
        warnings.append(
            "No known skills were detected in the job description. "
            "The skill-match score is unavailable; text similarity is shown "
            "separately and is not a qualification score."
        )
    if not explicit:
        warnings.append(
            "No known skills were detected in the resume; check the file text."
        )

    gaps = [
        {
            "label": label(r),
            "options": sorted(r),
            "importance": importance,
            "category": category_of(sorted(r)[0]),
        }
        for importance, group in (
            ("required", x_req),
            ("preferred", x_pref),
        )
        for r in group
    ]

    all_needed = (
        set().union(*required, *preferred) if (required or preferred) else set()
    )

    return AnalysisResult(
        score=legacy_score,
        required_coverage=round(components["required"] or 0.0, 3),
        preferred_coverage=round(components["preferred"] or 0.0, 3),
        semantic_similarity=round(sem_raw, 3),
        matched_required=sorted(label(r) for r in m_req),
        missing_required=sorted(label(r) for r in x_req),
        matched_preferred=sorted(label(r) for r in m_pref),
        missing_preferred=sorted(label(r) for r in x_pref),
        matched_by_implication=sorted(label(r) for r in i_req + i_pref),
        extra_skills=sorted(explicit - all_needed),
        gaps=gaps,
        resume_skills=sorted(have),
        components=components,
        warnings=warnings,
        score_status=(
            "available" if skill_match_available else "unavailable_no_jd_skills"
        ),
        skill_match_score=legacy_score if skill_match_available else None,
        text_similarity_score=round(sem_raw, 3),
    )
