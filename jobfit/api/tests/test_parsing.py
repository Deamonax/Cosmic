from services.parsing import split_cv


def test_split_cv_groups_wrapped_bullet_lines():
    text = "\n".join(
        [
            "Experience",
            "",
            "• Product",
            "Executive",
            "| Data-Driven",
            "Leader",
            "",
            "• Led global teams",
        ]
    )

    preview = split_cv(text)

    assert preview["sections"]
    section = preview["sections"][0]
    assert section["name"].lower().startswith("experience")
    assert section["bullets"][0] == "Product Executive | Data-Driven Leader"
    assert section["bullets"][1] == "Led global teams"


def test_split_cv_keeps_distinct_skill_bullets():
    text = "\n".join([
        "Skills",
        "• Python",
        "• SQL",
        "• AWS",
    ])

    preview = split_cv(text)

    assert preview["sections"]
    skills = preview["sections"][0]
    assert skills["bullets"] == ["Python", "SQL", "AWS"]
