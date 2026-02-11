"""Tests for the template loading system."""

from pb.templates import load_template, load_skill_content, load_references, load_prompt


def test_load_template_returns_string():
    result = load_template("pb-init", "SKILL.md")
    assert isinstance(result, str)
    assert len(result) > 0


def test_load_skill_content():
    result = load_skill_content("pb-init")
    assert isinstance(result, str)
    assert len(result) > 0


def test_load_skill_content_all_skills():
    for skill in ("pb-init", "pb-plan", "pb-build"):
        content = load_skill_content(skill)
        assert isinstance(content, str)
        assert len(content) > 0, f"{skill} SKILL.md is empty"


def test_load_references_pb_plan():
    refs = load_references("pb-plan")
    assert isinstance(refs, dict)
    assert "design_template.md" in refs
    assert "tasks_template.md" in refs
    assert len(refs["design_template.md"]) > 0
    assert len(refs["tasks_template.md"]) > 0


def test_load_references_pb_build():
    refs = load_references("pb-build")
    assert isinstance(refs, dict)
    assert "implementer_prompt.md" in refs
    assert len(refs["implementer_prompt.md"]) > 0


def test_load_references_pb_init():
    refs = load_references("pb-init")
    assert isinstance(refs, dict)
    assert len(refs) == 0


def test_load_prompt_content():
    result = load_prompt("pb-init")
    assert isinstance(result, str)
    assert len(result) > 0


def test_load_prompt_all_skills():
    for skill in ("pb-init", "pb-plan", "pb-build"):
        content = load_prompt(skill)
        assert isinstance(content, str)
        assert len(content) > 0, f"{skill} prompt is empty"
