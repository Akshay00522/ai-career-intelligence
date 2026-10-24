from analyzer.skills import expand_implied, extract_skills, find_mentions, prerequisites


def test_alias_normalization():
    assert "scikit-learn" in extract_skills("I use sklearn daily")
    assert "kubernetes" in extract_skills("deployed on k8s")


def test_java_not_matched_inside_javascript():
    s = extract_skills("Frontend work in JavaScript")
    assert "javascript" in s and "java" not in s


def test_symbol_skills():
    assert "c++" in extract_skills("Wrote C++ services")
    assert "c#" in extract_skills("Backend in C# and .NET")
    assert "ci/cd" in extract_skills("Maintained CI/CD pipelines")


def test_case_sensitive_r():
    assert "r" in extract_skills("Statistics in R and Python")
    assert "r" not in extract_skills("we are looking for strong results")
    assert "r" not in extract_skills("worked in R&D")


def test_library_names_do_not_leak_into_javascript():
    assert "javascript" not in extract_skills("charts with d3.js")


def test_longest_match_wins():
    # "Azure ML" is azure, not azure + machine learning via the alias "ml"
    assert extract_skills("Trained models on Azure ML") == {"azure"}
    assert [m.skill for m in find_mentions("Azure ML")] == ["azure"]


def test_aws_lambda_alias_does_not_match_python_lambda():
    assert "aws" not in extract_skills("used a lambda function in Python")
    assert "aws" in extract_skills("deployed on AWS Lambda")


def test_implications_are_transitive():
    have, implied = expand_implied({"pytorch"})
    assert {"python", "deep learning", "machine learning"} <= have
    assert "pytorch" not in implied and "machine learning" in implied


def test_kubernetes_implies_docker_but_not_reverse():
    assert "docker" in expand_implied({"kubernetes"})[0]
    assert "kubernetes" not in expand_implied({"docker"})[0]


def test_prerequisites_combine_implies_and_prereqs():
    prereqs = prerequisites("docker")
    assert "linux" in prereqs
    assert "python" in prerequisites("pandas")


def test_empty_text():
    assert extract_skills("") == set()
