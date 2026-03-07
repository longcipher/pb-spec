"""Tests for the template loading system."""

from pathlib import Path

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


def test_pb_init_templates_use_non_destructive_marker_merge_for_agents_md():
    """pb-init templates should update AGENTS.md via a marker block without rewriting existing text."""
    for content in (load_skill_content("pb-init"), load_prompt("pb-init")):
        assert "<!-- BEGIN PB-INIT MANAGED BLOCK -->" in content
        assert "<!-- END PB-INIT MANAGED BLOCK -->" in content
        assert (
            "If `AGENTS.md` exists but markers are absent: append the managed block at the end"
            in content
        )
        assert (
            "Do NOT delete, reorder, or rewrite any pre-existing content outside the managed block."
            in content
        )
        assert (
            "Never assume a specific `AGENTS.md` format, section name, or template structure."
            in content
        )


def test_non_init_templates_treat_agents_md_as_read_only():
    """pb-plan/pb-refine/pb-build should not modify AGENTS.md unless explicitly asked."""
    for skill in ("pb-plan", "pb-refine", "pb-build"):
        for content in (load_skill_content(skill), load_prompt(skill)):
            assert (
                "`AGENTS.md` is read-only in this phase." in content
                or "modify, delete, or reformat `AGENTS.md`" in content
            ), f"{skill} template must mark AGENTS.md as read-only"


def test_pb_plan_templates_require_runtime_observability_verification():
    """pb-plan templates should require runtime evidence in task verification when applicable."""
    refs = load_references("pb-plan")
    for content in (
        load_skill_content("pb-plan"),
        load_prompt("pb-plan"),
        refs["tasks_template.md"],
    ):
        assert "tail -n 50 app.log" in content
        assert "curl http://localhost:8080/health" in content


def test_pb_plan_reference_templates_require_bdd_tdd_fields():
    """pb-plan reference templates should expose BDD/TDD planning fields."""
    refs = load_references("pb-plan")
    design = refs["design_template.md"]
    tasks = refs["tasks_template.md"]

    assert "BDD/TDD Strategy" in design
    assert "Project Identity Alignment" in design
    assert "BDD Scenario Inventory" in design
    assert "BDD Runner" in design
    assert "BDD Command" in design
    assert "Unit Test Command" in design
    assert "Property Test Tool" in design
    assert "Hypothesis" in design
    assert "fast-check" in design
    assert "proptest" in design
    assert "cargo-fuzz" in design
    assert "criterion" in design

    assert "Scenario Coverage" in tasks
    assert "Loop Type" in tasks
    assert "BDD Verification" in tasks
    assert "Advanced Test Coverage" in tasks
    assert "Advanced Test Verification" in tasks


def test_pb_plan_templates_require_gherkin_feature_generation():
    """pb-plan templates should generate spec-native Gherkin artifacts."""
    for content in (load_skill_content("pb-plan"), load_prompt("pb-plan")):
        assert "features/*.feature" in content
        assert "Gherkin" in content
        assert "@cucumber/cucumber" in content
        assert "behave" in content
        assert "cucumber" in content
        assert "BDD/TDD Strategy" in content
        assert "BDD Scenario Inventory" in content
        assert "Scenario Coverage" in content


def test_pb_plan_lightweight_templates_remain_pb_build_compatible():
    """Lightweight task examples must still satisfy pb-build task parsing rules."""
    for content in (load_skill_content("pb-plan"), load_prompt("pb-plan")):
        lightweight_section = content.split("## Step 5b:", maxsplit=1)[0]

        assert "### Task 1.1:" in lightweight_section
        assert "- **Status:** 🔴 TODO" in lightweight_section
        assert "### Task 1:" not in lightweight_section


def test_pb_plan_templates_require_project_identity_alignment_for_template_repos():
    """pb-plan templates should normalize placeholder module identities in scaffold repos."""
    refs = load_references("pb-plan")
    for content in (
        load_skill_content("pb-plan"),
        load_prompt("pb-plan"),
        refs["design_template.md"],
    ):
        assert (
            "generic crate/package/module names" in content
            or "Project Identity Alignment" in content
        )
        assert "project-matching" in content or "current project or product identity" in content


def test_pb_plan_templates_require_risk_based_advanced_test_planning():
    """pb-plan templates should plan property tests by default and fuzz/benchmarks conditionally."""
    refs = load_references("pb-plan")
    combined = (
        load_skill_content("pb-plan"),
        load_prompt("pb-plan"),
        refs["design_template.md"],
        refs["tasks_template.md"],
    )

    for content in combined:
        assert "Hypothesis" in content
        assert "fast-check" in content
        assert "proptest" in content
        assert "Atheris" in content
        assert "jazzer.js" in content
        assert "cargo-fuzz" in content
        assert "pytest-benchmark" in content
        assert "Vitest Bench" in content
        assert "criterion" in content

    for content in (load_skill_content("pb-plan"), load_prompt("pb-plan")):
        assert "Add **property tests** by default" in content
        assert "Add **fuzz testing** only" in content
        assert "Add **benchmarks** only" in content


def test_pb_plan_templates_require_code_simplification_constraints():
    """pb-plan templates should plan for behavior-preserving simplification and clarity."""
    refs = load_references("pb-plan")

    for content in (
        load_skill_content("pb-plan"),
        load_prompt("pb-plan"),
        refs["design_template.md"],
        refs["tasks_template.md"],
    ):
        assert (
            "Preserve existing behavior" in content or "Behavior Preservation Boundary" in content
        )
        assert "Reduce nesting" in content or "reduced nesting" in content
        assert "nested ternary" in content

    for content in (load_skill_content("pb-plan"), load_prompt("pb-plan")):
        assert "keep cleanup scoped to touched code" in content
        assert "explicit readable solutions over clever compact ones" in content
        assert "Read `CLAUDE.md`" in content


def test_pb_build_prompt_template_is_self_contained_for_prompt_platforms():
    """Prompt-only platforms should not rely on an external implementer reference file."""
    prompt = load_prompt("pb-build")

    assert "## IMPLEMENTER PROMPT TEMPLATE" in prompt
    assert "Task {{TASK_NUMBER}}: {{TASK_NAME}}" in prompt
    assert "Read `references/implementer_prompt.md`" not in prompt


def test_pb_build_templates_require_bdd_outer_loop_before_tdd():
    """pb-build templates should enforce BDD outer loop before TDD inner loop."""
    build_refs = load_references("pb-build")
    for content in (
        load_skill_content("pb-build"),
        load_prompt("pb-build"),
        build_refs["implementer_prompt.md"],
    ):
        assert "Scenario Coverage" in content
        assert "outer loop is red" in content
        assert "Re-run the BDD scenario until it passes" in content
        assert "BDD+TDD" in content
        assert "scenario name" in content


def test_pb_refine_templates_update_feature_files_with_design_changes():
    """pb-refine templates should refine `.feature` files alongside design and tasks."""
    for content in (load_skill_content("pb-refine"), load_prompt("pb-refine")):
        assert "specs/<spec-dir>/features/" in content
        assert "update `.feature` first" in content
        assert "Scenario Coverage" in content
        assert "feature-file changes" in content


def test_project_docs_describe_bdd_and_tdd_workflow():
    """Project docs should describe the Gherkin-driven outer loop."""
    readme = Path("README.md").read_text(encoding="utf-8")
    design = Path("docs/design.md").read_text(encoding="utf-8")

    assert "Gherkin" in readme
    assert "BDD" in readme
    assert ".feature" in readme
    assert "outer loop" in design
    assert "inner loop" in design


def test_pb_build_templates_escalate_after_three_failures():
    """pb-build templates should stop thrashing and escalate via DCR after 3 failures."""
    for content in (load_skill_content("pb-build"), load_prompt("pb-build")):
        assert "3 consecutive failed attempts" in content
        assert "Run /pb-refine <feature-name>" in content
        assert "retry budget" in content


def test_pb_build_implementer_templates_require_runtime_evidence():
    """Implementer guidance should require runtime log/probe evidence when applicable."""
    build_refs = load_references("pb-build")
    for content in (build_refs["implementer_prompt.md"], load_prompt("pb-build")):
        assert "Runtime logs:" in content
        assert "Runtime probe:" in content
        assert "Runtime evidence is mandatory when applicable" in content


def test_pb_refine_templates_accept_build_block_packets():
    """pb-refine templates should handle standardized build-block packets from pb-build."""
    for content in (load_skill_content("pb-refine"), load_prompt("pb-refine")):
        assert "Build-block packets" in content
        assert "🛑 Build Blocked" in content
