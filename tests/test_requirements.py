from analyzer.jd_parser import build_requirements, split_jd


def reqs(text, **kw):
    return {tuple(sorted(r)) for r in build_requirements(text, **kw)}


def test_split_jd_sections():
    req, pref = split_jd("Requirements\n- Python\n\nNice to have\n- Kubernetes")
    assert "Python" in req and "Kubernetes" not in req
    assert "Kubernetes" in pref


def test_inline_preferred_marker():
    req, pref = split_jd("- Python\n- Docker is a plus")
    assert "Docker" in pref and "Docker" not in req


def test_or_group():
    assert reqs("- REST APIs with FastAPI or Flask") == {("rest apis",), ("fastapi", "flask")}


def test_comma_list_ending_in_or_is_one_group():
    assert ("aws", "azure", "gcp") in reqs("- Cloud experience: AWS, GCP or Azure")


def test_comma_list_without_or_is_separate_requirements():
    assert reqs("- Python, SQL") == {("python",), ("sql",)}


def test_and_is_never_a_group():
    assert reqs("- Docker and Kubernetes") == {("docker",), ("kubernetes",)}


def test_different_categories_are_not_grouped():
    # python is a language, docker is engineering
    assert reqs("- Python or Docker") == {("python",), ("docker",)}


def test_group_dropped_when_member_is_required_alone():
    assert reqs("- Flask\n- FastAPI or Flask") == {("flask",)}


def test_or_groups_can_be_disabled():
    assert reqs("- FastAPI or Flask", use_or_groups=False) == {("fastapi",), ("flask",)}


def test_alias_pairs_collapse_to_one_requirement():
    # LlamaIndex is an alias of langchain in the taxonomy
    assert reqs("- LangChain or LlamaIndex") == {("langchain",)}


def test_no_cross_line_chains():
    assert reqs("- FastAPI\n- or Flask") == {("fastapi",), ("flask",)}


def test_unrecognized_section_heading_does_not_remain_preferred():
    req, pref = split_jd(
        "Requirements\n"
        "- Python\n"
        "Nice to have\n"
        "- Kubernetes\n"
        "What you will do\n"
        "- SQL"
    )

    assert "Python" in req
    assert "Kubernetes" in pref
    assert "SQL" not in pref

def test_inline_required_and_preferred_skills_on_same_line():
    req, pref = split_jd(
        "Required skills: Python, machine learning, SQL, FastAPI. "
        "Preferred skills: Docker, AWS."
    )

    assert all(
        skill in req
        for skill in ("Python", "machine learning", "SQL", "FastAPI")
    )
    assert all(skill in pref for skill in ("Docker", "AWS"))
    assert "AWS" not in req