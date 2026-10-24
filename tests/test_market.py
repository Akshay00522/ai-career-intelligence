from analyzer.market import demand_by_category, load_jds, skill_demand, top_skills


def test_demand_shares():
    d = skill_demand(["Python and SQL", "Python and Docker", "SQL"])
    assert abs(d["python"] - 2 / 3) < 1e-9 and abs(d["docker"] - 1 / 3) < 1e-9


def test_top_skills_sorted_and_limited():
    rows = top_skills({"a": 0.2, "python": 0.9, "sql": 0.5}, n=2)
    assert [r["skill"] for r in rows] == ["python", "sql"]


def test_empty_input():
    assert skill_demand([]) == {}


def test_category_means():
    assert demand_by_category({"python": 1.0, "sql": 0.5})["language"] == 0.75


def test_load_jds(tmp_path):
    (tmp_path / "a.txt").write_text("Python", encoding="utf-8")
    (tmp_path / "ignore.md").write_text("x", encoding="utf-8")
    assert list(load_jds(tmp_path)) == ["a"]
