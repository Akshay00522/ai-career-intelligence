from analyzer.report import to_markdown
from analyzer.service import run_analysis

RESUME = "Python, pandas, SQL, scikit-learn, Git"
JD = "Requirements\n- Python and SQL\n- Docker\nNice to have\n- Kubernetes"


def test_run_analysis_shape():
    out = run_analysis(RESUME, JD, hours_per_week=5)
    assert set(out) == {"analysis", "plan"}
    assert out["plan"]["hours_per_week"] == 5
    assert [s["skill"] for s in out["plan"]["steps"]][:2] == ["linux", "docker"]


def test_run_analysis_without_plan():
    assert "plan" not in run_analysis(RESUME, JD, include_plan=False)


def test_market_demand_breaks_ties(tmp_path):
    (tmp_path / "a.txt").write_text("Terraform and Excel", encoding="utf-8")
    out = run_analysis("Python", "Requirements\n- Terraform\n- Excel", market_dir=tmp_path)
    assert out["plan"]["steps"][0]["market_demand"] == 1.0


def test_markdown_report_sections():
    out = run_analysis(RESUME, JD)
    md = to_markdown(out["analysis"], out["plan"])
    for heading in ("# Skill-Gap Analysis Report", "## Required skills", "## Learning plan", "docker"):
        assert heading in md


def test_markdown_report_without_plan():
    out = run_analysis(RESUME, JD, include_plan=False)
    assert "## Learning plan" not in to_markdown(out["analysis"])
