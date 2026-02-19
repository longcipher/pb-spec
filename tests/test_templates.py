"""Tests for the template loading system."""

from pb_spec.templates import load_prompt, load_references, load_skill_content, load_template


def test_load_template_returns_string():
    result = load_template("pb-init", "SKILL.md")
    assert isinstance(result, str)
    assert len(result) > 0


def test_load_skill_content():
    result = load_skill_content("pb-init")
    assert isinstance(result, str)
    assert len(result) > 0


def test_load_skill_content_all_skills():
    for skill in ("pb-init", "pb-plan", "pb-refine", "pb-build"):
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
    for skill in ("pb-init", "pb-plan", "pb-refine", "pb-build"):
        content = load_prompt(skill)
        assert isinstance(content, str)
        assert len(content) > 0, f"{skill} prompt is empty"


def test_pb_refine_templates_are_not_wrapped_as_code_block():
    skill = load_skill_content("pb-refine").lstrip()
    prompt = load_prompt("pb-refine").lstrip()
    assert not skill.startswith("```"), "pb-refine SKILL should be plain markdown, not a code block"
    assert not prompt.startswith("```"), (
        "pb-refine prompt should be plain markdown, not a code block"
    )


def test_pb_build_templates_avoid_destructive_git_checkout():
    skill = load_skill_content("pb-build")
    prompt = load_prompt("pb-build")
    assert "git checkout ." not in skill
    assert "git checkout ." not in prompt


def test_prompt_templates_no_duplicate_separators():
    """Prompt templates should not have consecutive --- separators (redundant formatting)."""
    for skill in ("pb-init", "pb-plan", "pb-refine", "pb-build"):
        content = load_prompt(skill)
        assert "\n---\n\n---\n" not in content, f"{skill} prompt has duplicate --- separators"
