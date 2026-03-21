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


def test_pb_init_templates_capture_architecture_decision_snapshot():
    """pb-init templates should snapshot repo-level architecture decisions for later agents."""
    for content in (load_skill_content("pb-init"), load_prompt("pb-init")):
        assert "Architecture Decision Snapshot" in content
        assert "Established Patterns" in content
        assert "Dependency Injection Boundaries" in content
        assert "Error Handling Conventions" in content
        assert "Only record decisions grounded in explicit evidence" in content


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


def test_pb_plan_templates_accept_arbitrary_source_material_without_prompt_recipes():
    """pb-plan should accept raw design docs or rough requirements without special wording."""
    for content in (load_skill_content("pb-plan"), load_prompt("pb-plan")):
        assert "arbitrary format" in content
        assert "rough notes" in content
        assert "partial design" in content
        assert "Do not require the user to provide pb-plan-specific prompt wording" in content


def test_pb_plan_templates_require_subagent_backed_analysis_and_reconciliation():
    """pb-plan should use fresh subagents to analyze inputs and reconcile output coverage."""
    refs = load_references("pb-plan")

    for content in (
        load_skill_content("pb-plan"),
        load_prompt("pb-plan"),
        refs["design_template.md"],
        refs["tasks_template.md"],
    ):
        assert "subagent" in content

    for content in (load_skill_content("pb-plan"), load_prompt("pb-plan")):
        assert "Source Requirements Analyst" in content
        assert "Codebase Analyst" in content
        assert "Spec Reconciliation Auditor" in content
        assert "fresh, minimal context" in content
        assert "Requirements Coverage Matrix" in content
        assert (
            "reconcile the extracted source requirements against the generated `design.md`"
            in content
        )


def test_pb_plan_reference_templates_require_source_requirement_traceability():
    """pb-plan reference templates should surface source inputs and traceability fields."""
    refs = load_references("pb-plan")
    design = refs["design_template.md"]
    tasks = refs["tasks_template.md"]

    assert "Source Inputs & Normalization" in design
    assert "Requirements Coverage Matrix" in design
    assert "Requirement ID" in design
    assert "Requirement Coverage" in tasks


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


def test_pb_plan_templates_require_explicit_architecture_decisions():
    """pb-plan templates should require upfront architecture decisions before implementation."""
    refs = load_references("pb-plan")

    for content in (
        load_skill_content("pb-plan"),
        load_prompt("pb-plan"),
        refs["design_template.md"],
        refs["tasks_template.md"],
    ):
        assert "Architecture Decisions" in content
        assert "SRP" in content
        assert "DIP" in content
        assert "Factory" in content
        assert "Strategy" in content
        assert "Observer" in content
        assert "Adapter" in content
        assert "Decorator" in content

    for content in (load_skill_content("pb-plan"), load_prompt("pb-plan")):
        assert "200 lines" in content
        assert "through interfaces or abstract classes" in content
        assert "Architecture Decision Snapshot" in content


def test_pb_plan_templates_require_build_eligible_contract_language():
    """pb-plan templates should describe a contract-complete, build-eligible spec."""
    for content in (load_skill_content("pb-plan"), load_prompt("pb-plan")):
        assert "contract-complete spec" in content
        assert "build-eligible spec" in content
        assert "markdown-carried packet" in content


def test_pb_plan_reference_templates_define_contract_types_and_task_states():
    """pb-plan reference templates should expose explicit planner contract types and states."""
    refs = load_references("pb-plan")
    design = refs["design_template.md"]
    tasks = refs["tasks_template.md"]

    assert "PlannedSpecContract" in design
    assert "TaskContract" in design
    assert "BuildBlockedPacket" in design
    assert "DesignChangeRequestPacket" in design

    assert "🟡 IN PROGRESS" in tasks
    assert "⛔ OBSOLETE" in tasks
    assert "allowed status markers and transitions" in tasks


def test_pb_plan_templates_define_legacy_todo_compatibility_for_task_states():
    """pb-plan templates should explain how legacy TODO-only specs map into the explicit state machine."""
    refs = load_references("pb-plan")

    for content in (
        load_skill_content("pb-plan"),
        load_prompt("pb-plan"),
        refs["tasks_template.md"],
    ):
        assert "legacy `TODO`" in content
        assert "treat it as `🔴 TODO`" in content
        assert "before it can move to `🟡 IN PROGRESS`" in content


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


def test_pb_build_templates_require_phase_zero_validation_gate():
    """pb-build templates should validate spec contracts before task execution begins."""
    required_design_sections = (
        "Architecture Overview",
        "BDD/TDD Strategy",
        "Detailed Design",
        "Verification & Testing Strategy",
        "Implementation Plan",
    )
    required_task_fields = (
        "Context",
        "Verification",
        "Scenario Coverage",
        "Loop Type",
        "Behavioral Contract",
        "Simplification Focus",
        "BDD Verification",
        "Advanced Test Verification",
        "Runtime Verification",
    )

    for content in (load_skill_content("pb-build"), load_prompt("pb-build")):
        assert "Phase 0 — Validate Spec Contract" in content
        for section in required_design_sections:
            assert section in content
        for field in required_task_fields:
            assert field in content
        assert "at least one `.feature` file with at least one `Scenario`" in content
        assert "❌ Missing required design section in specs/<spec-dir>/design.md:" in content
        assert (
            "❌ Missing required task field in specs/<spec-dir>/tasks.md for Task X.Y:" in content
        )
        assert "❌ Missing required feature scenario in specs/<spec-dir>/features/" in content
        assert "stop immediately and report the missing field instead of spawning a subagent" in (
            content
        )

    skill = load_skill_content("pb-build")
    prompt = load_prompt("pb-build")
    assert skill.index("Phase 0 — Validate Spec Contract") < skill.index(
        "Create a **fresh subagent** for this task"
    )
    assert prompt.index("Phase 0 — Validate Spec Contract") < prompt.index("Spawn a fresh subagent")


def test_pb_build_implementer_templates_fail_fast_on_incomplete_contract_context():
    """Implementer guidance should stop immediately if the orchestrator passed malformed spec context."""
    build_refs = load_references("pb-build")
    for content in (build_refs["implementer_prompt.md"], load_prompt("pb-build")):
        assert (
            "If the provided task block or project context is missing any required contract field, stop immediately."
            in content
        )
        assert "❌ Missing required design section in specs/<spec-dir>/design.md:" in content
        assert (
            "❌ Missing required task field in specs/<spec-dir>/tasks.md for Task X.Y:" in content
        )


def test_pb_build_templates_require_completion_gates_and_failure_packets():
    """pb-build templates should require evidence-backed completion and blocked-build packets."""
    build_refs = load_references("pb-build")
    for content in (
        load_skill_content("pb-build"),
        load_prompt("pb-build"),
        build_refs["implementer_prompt.md"],
    ):
        assert "Scenario Coverage" in content
        assert "BDD Verification" in content
        assert "Completion gate" in content or "completion" in content

    for content in (load_skill_content("pb-build"), load_prompt("pb-build")):
        assert "Failure Evidence" in content
        assert "Impact:" in content
        assert "stop the build loop" in content


def test_pb_build_templates_define_allowed_task_transitions_and_legacy_todo_handling():
    """pb-build templates should require TODO -> IN PROGRESS -> DONE and ban direct closeout."""
    for content in (load_skill_content("pb-build"), load_prompt("pb-build")):
        assert "When the builder starts a task" in content
        assert "legacy `TODO`" in content
        assert "update the task Status to `🟡 IN PROGRESS`" in content
        assert "Do not move a task directly from `🔴 TODO` or legacy `TODO` to `🟢 DONE`" in content
        assert "`⏭️ SKIPPED` and `🔄 DCR` remain explicit exceptional states" in content
        assert (
            "| In Progress | `🟡 IN PROGRESS` | Active implementation after work has started |"
            in content
        )
        assert (
            "every required evidence checkbox in that task block is either `- [x]` or explicitly marked `N/A`"
            in content
        )


def test_pb_refine_templates_require_complete_blocked_build_and_dcr_packets():
    """pb-refine templates should define complete required sections for both packet families."""
    for content in (load_skill_content("pb-refine"), load_prompt("pb-refine")):
        assert "🛑 Build Blocked" in content
        assert "🔄 Design Change Request" in content
        assert "high-priority execution evidence" in content
        assert "Required `🛑 Build Blocked` sections:" in content
        assert "Required `🔄 Design Change Request` sections:" in content
        assert "Reason" in content
        assert "Loop Type" in content
        assert "Scenario Coverage" in content
        assert "What We Tried" in content
        assert "Failure Evidence" in content
        assert "Failing Step" in content
        assert "Suggested Design Change" in content
        assert "Next Action" in content
        assert "Problem" in content
        assert "Suggested Change" in content
        assert "Do NOT modify completed tasks" in content
        assert "specs/<spec-dir>/features/" in content


def test_pb_refine_templates_report_missing_packet_sections_instead_of_guessing():
    """pb-refine templates should reject malformed packets with explicit missing-section output."""
    for content in (load_skill_content("pb-refine"), load_prompt("pb-refine")):
        assert "❌ Incomplete 🛑 Build Blocked packet. Missing required section(s):" in content
        assert (
            "❌ Incomplete 🔄 Design Change Request packet. Missing required section(s):" in content
        )
        assert (
            "Do not guess or reconstruct missing failure evidence, impact, or suggested changes."
            in content
        )


def test_pb_build_templates_require_architecture_decision_adherence():
    """pb-build templates should force implementers to follow planned architecture decisions."""
    build_refs = load_references("pb-build")
    for content in (
        load_skill_content("pb-build"),
        load_prompt("pb-build"),
        build_refs["implementer_prompt.md"],
    ):
        assert "Architecture Decisions" in content
        assert "Architecture Decision Snapshot" in content
        assert "SRP" in content
        assert "DIP" in content
        assert "Factory" in content
        assert "Strategy" in content
        assert "Observer" in content
        assert "Adapter" in content
        assert "Decorator" in content
        assert "interfaces or abstract classes" in content
        assert (
            "do not improvise a new pattern mid-build" in content
            or "Do not add architecture or abstractions beyond what the task requires" in content
        )


def test_readme_documents_architecture_decision_workflow():
    """README should explain the architecture snapshot and decision flow across pb-init/pb-plan/pb-build."""
    readme = Path(__file__).resolve().parents[1].joinpath("README.md").read_text(encoding="utf-8")

    assert "Architecture Decision Snapshot" in readme
    assert "Architecture Decisions" in readme
    assert "SRP" in readme
    assert "DIP" in readme
    assert "Factory" in readme
    assert "Strategy" in readme
    assert "Observer" in readme
    assert "Adapter" in readme
    assert "Decorator" in readme
    assert "code-simplification lens" in readme or "code simplifier" in readme


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


def test_pb_build_templates_parse_task_blocks_instead_of_raw_checkboxes():
    """pb-build should treat Task X.Y blocks as the execution unit, not each checkbox line."""
    for content in (load_skill_content("pb-build"), load_prompt("pb-build")):
        assert "Determine unfinished tasks from each `### Task X.Y:` block" in content
        assert "Do not treat every `- [ ]` step as a separate task." in content


def test_pb_build_implementer_templates_require_concise_evidence_not_reasoning_dump():
    """Implementer templates should ask for concise evidence, not full reasoning traces."""
    build_refs = load_references("pb-build")
    for content in (build_refs["implementer_prompt.md"], load_prompt("pb-build")):
        assert "output your reasoning for each step" not in content
        assert "Report concise decisions and evidence for each step" in content


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
        assert "🔄 Design Change Request" in content


def test_pb_refine_templates_validate_packets_before_touching_spec_files():
    """pb-refine templates should validate structured packets before editing spec artifacts."""
    for content in (load_skill_content("pb-refine"), load_prompt("pb-refine")):
        assert "Validate the packet before modifying any spec file." in content
        assert (
            "Only after packet validation passes may you update the affected `.feature`, `design.md`, and `tasks.md` files."
            in content
        )
        assert content.index("Validate the packet before modifying any spec file.") < content.index(
            "If feedback changes user-visible behavior, update the relevant files under `specs/<spec-dir>/features/` first."
        )


def test_project_design_doc_matches_current_snapshot_workflow():
    """docs/design.md should describe the same managed-snapshot workflow implemented by templates."""
    design = Path("docs/design.md").read_text(encoding="utf-8")

    assert "managed snapshot block" in design
    assert "Architecture Decision Snapshot" in design
    assert "BDD outer loop" in design
    assert "parity is guarded by regression tests" in design
