from pathlib import Path

from analyzer import analyze
from analyzer.pipeline import DEFAULT_WEIGHTS, blend

ROOT = Path(__file__).resolve().parents[1]


def test_perfect_match_scores_high():
    r = analyze("Python SQL pandas scikit-learn machine learning",
                "Requirements\n- Python\n- SQL\n- machine learning")
    assert r.required_coverage == 1.0 and r.missing_required == []
    assert r.score > 70


def test_missing_skills_reported():
    r = analyze("I know Python.", "Requirements\n- Python\n- Docker\nNice to have\n- Kubernetes")
    assert r.missing_required == ["docker"]
    assert r.missing_preferred == ["kubernetes"]
    assert {g["importance"] for g in r.gaps} == {"required", "preferred"}


def test_implied_skill_satisfies_requirement_and_is_flagged():
    r = analyze("Built models with scikit-learn.", "Requirements\n- machine learning")
    assert r.missing_required == []
    assert r.matched_by_implication == ["machine learning"]


def test_implications_can_be_disabled():
    r = analyze("Built models with scikit-learn.", "Requirements\n- machine learning", use_implications=False)
    assert r.missing_required == ["machine learning"]


def test_or_group_satisfied_by_either_option():
    r = analyze("Built APIs with Flask.", "Requirements\n- FastAPI or Flask")
    assert r.missing_required == [] and r.matched_required == ["fastapi or flask"]


def test_or_group_gap_lists_all_options():
    r = analyze("Python only.", "Requirements\n- FastAPI or Flask")
    assert r.missing_required == ["fastapi or flask"]
    assert r.gaps[0]["options"] == ["fastapi", "flask"]



def test_no_skills_in_jd_marks_skill_match_score_unavailable():
    r = analyze(
        "Python developer with SQL",
        "We are a friendly team that loves coffee and people.",
    )

    assert r.score_status == "unavailable_no_jd_skills"
    assert r.skill_match_score is None
    assert r.text_similarity_score == r.semantic_similarity
    assert 0 <= r.score <= 100  # Legacy field retained for compatibility.
    assert any("skill-match score is unavailable" in w for w in r.warnings)



def test_blend_renormalises_when_a_section_is_absent():
    only_required_and_semantic = blend({"required": 1.0, "preferred": None, "semantic": 0.0})
    expected = DEFAULT_WEIGHTS["required"] / (DEFAULT_WEIGHTS["required"] + DEFAULT_WEIGHTS["semantic"])
    assert abs(only_required_and_semantic - expected) < 1e-9


def test_blend_respects_custom_weights():
    w = {"required": 1.0, "preferred": 0.0, "semantic": 0.0}
    assert blend({"required": 0.5, "preferred": 1.0, "semantic": 1.0}, w) == 0.5


def test_score_bounds_and_extras():
    r = analyze("Python, Docker, Tableau", "Requirements\n- Python")
    assert 0 <= r.score <= 100
    assert set(r.extra_skills) == {"docker", "tableau"}


def test_sample_files():
    r = analyze((ROOT / "samples" / "resume.txt").read_text(), (ROOT / "samples" / "jd.txt").read_text())
    assert "python" in r.matched_required
    assert "docker" in r.missing_required
    assert "machine learning" in r.matched_by_implication

import pytest


def test_blend_rejects_negative_weights():
    with pytest.raises(ValueError, match="non-negative"):
        blend(
            {"required": 1.0},
            {"required": -1.0, "preferred": 0.0, "semantic": 1.0},
        )


def test_blend_rejects_missing_weight_keys():
    with pytest.raises(ValueError, match="exactly these keys"):
        blend({"required": 1.0}, {"required": 1.0})
