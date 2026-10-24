from analyzer.learning import build_plan


def gap(*options, importance="required"):
    return {"options": list(options), "importance": importance}


def order(plan):
    return [s["skill"] for s in plan["steps"]]


def test_prerequisites_are_scheduled_before_dependents():
    plan = build_plan([gap("kubernetes")], have={"python"})
    skills = order(plan)
    assert skills.index("linux") < skills.index("docker") < skills.index("kubernetes")
    docker = next(s for s in plan["steps"] if s["skill"] == "docker")
    assert docker["importance"] == "prerequisite" and "kubernetes" in docker["why"]


def test_known_skills_are_not_scheduled():
    plan = build_plan([gap("kubernetes")], have={"docker", "linux"})
    assert order(plan) == ["kubernetes"]


def test_required_before_preferred():
    plan = build_plan([gap("excel", importance="preferred"), gap("sql")], have=set())
    assert order(plan).index("sql") < order(plan).index("excel")


def test_hours_and_weeks():
    plan = build_plan([gap("docker")], have={"linux"}, hours_per_week=10)
    assert plan["total_hours"] == 20 and plan["estimated_weeks"] == 2
    assert build_plan([gap("docker")], have={"linux"}, hours_per_week=40)["estimated_weeks"] == 1


def test_no_gaps_gives_empty_plan():
    plan = build_plan([], have={"python"})
    assert plan["steps"] == [] and plan["total_hours"] == 0 and plan["estimated_weeks"] == 0


def test_or_group_prefers_cheaper_path_then_demand():
    have = {"python", "machine learning", "deep learning"}
    plan = build_plan([gap("pytorch", "tensorflow")], have, demand={"tensorflow": 0.9})
    assert order(plan) == ["tensorflow"]
    plan = build_plan([gap("pytorch", "tensorflow")], have, demand={"pytorch": 0.9})
    assert order(plan) == ["pytorch"]


def test_every_step_has_practice_text_and_resources_key():
    for step in build_plan([gap("rag"), gap("terraform", importance="preferred")], have=set())["steps"]:
        assert step["practice"] and isinstance(step["resources"], list)


def test_unknown_skill_falls_back_to_default_hours():
    plan = build_plan([gap("unknown test skill")], have=set())
    assert plan["steps"][0]["hours"] == 20


def test_plan_has_no_cycles_or_duplicates():
    plan = build_plan([gap("rag"), gap("mlops"), gap("kubernetes", importance="preferred")], have=set())
    skills = order(plan)
    assert len(skills) == len(set(skills))


def test_prerequisites_of_known_skills_are_not_relearned():
    # having machine learning means its own foundations (statistics) are assumed covered
    plan = build_plan([gap("tensorflow")], have={"python", "machine learning", "deep learning"})
    assert order(plan) == ["tensorflow"]

def test_shared_prerequisite_inherits_required_priority():
    plan = build_plan(
        [
            gap("kubernetes"),
            gap("terraform", importance="preferred"),
        ],
        have=set(),
    )

    steps = {step["skill"]: step for step in plan["steps"]}

    # Linux is a prerequisite in these learning paths.
    assert steps["linux"]["importance"] == "prerequisite"

    # All prerequisites must still appear before the skills that need them.
    skills = order(plan)
    assert skills.index("linux") < skills.index("kubernetes")
    assert skills.index("linux") < skills.index("terraform")
