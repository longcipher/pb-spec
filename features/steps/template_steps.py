from __future__ import annotations

import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

from behave import given, then, when
from click.testing import CliRunner

from pb_spec.cli import main
from pb_spec.templates import load_prompt, load_references, load_skill_content

type BehaveContext = Any
type StepFunction = Callable[..., object]
type StepDecoratorFactory = Callable[[str], Callable[[StepFunction], StepFunction]]

given_step = cast(StepDecoratorFactory, given)
when_step = cast(StepDecoratorFactory, when)
then_step = cast(StepDecoratorFactory, then)

REQUIRED_DESIGN_SECTIONS = (
    "Architecture Overview",
    "BDD/TDD Strategy",
    "Detailed Design",
    "Verification & Testing Strategy",
    "Implementation Plan",
)

REQUIRED_TASK_FIELDS = (
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


def _load_workflow_contract_context() -> dict[str, Any]:
    return {
        "pb_plan_templates": [load_skill_content("pb-plan"), load_prompt("pb-plan")],
        "pb_plan_references": load_references("pb-plan"),
        "pb_build_skill": load_skill_content("pb-build"),
        "pb_build_prompt": load_prompt("pb-build"),
        "pb_build_references": load_references("pb-build"),
        "pb_refine_templates": [load_skill_content("pb-refine"), load_prompt("pb-refine")],
    }


@given_step("the pb-plan templates are loaded")
def step_given_pb_plan_templates(context: BehaveContext) -> None:
    context.pb_plan_templates = [load_skill_content("pb-plan"), load_prompt("pb-plan")]


@when_step("I inspect the lightweight tasks instructions")
def step_when_inspect_lightweight_tasks(context: BehaveContext) -> None:
    context.lightweight_sections = [
        content.split("## Step 5b:", maxsplit=1)[0] for content in context.pb_plan_templates
    ]


@then_step("the lightweight tasks use Task X.Y headings")
def step_then_lightweight_tasks_use_task_ids(context: BehaveContext) -> None:
    for section in context.lightweight_sections:
        assert "### Task 1.1:" in section
        assert "### Task 1:" not in section


@then_step("each lightweight task includes a status marker")
def step_then_lightweight_tasks_include_status(context: BehaveContext) -> None:
    for section in context.lightweight_sections:
        assert "- **Status:** 🔴 TODO" in section


@given_step("the pb-build prompt template is loaded")
def step_given_pb_build_prompt_template(context: BehaveContext) -> None:
    context.pb_build_prompt = load_prompt("pb-build")


@when_step("I inspect the prompt-only build instructions")
def step_when_inspect_prompt_build_instructions(context: BehaveContext) -> None:
    context.pb_build_prompt_text = context.pb_build_prompt


@then_step("the embedded implementer prompt is present")
def step_then_embedded_implementer_prompt_present(context: BehaveContext) -> None:
    assert "## IMPLEMENTER PROMPT TEMPLATE" in context.pb_build_prompt_text
    assert "Task {{TASK_NUMBER}}: {{TASK_NAME}}" in context.pb_build_prompt_text


@then_step("the prompt does not require references/implementer_prompt.md")
def step_then_prompt_does_not_require_reference_file(context: BehaveContext) -> None:
    assert "Read `references/implementer_prompt.md`" not in context.pb_build_prompt_text


@given_step("a feature requirement is planned through the existing pb-spec workflow")
def step_given_feature_requirement_is_planned(context: BehaveContext) -> None:
    context.pb_plan_templates = [load_skill_content("pb-plan"), load_prompt("pb-plan")]
    context.pb_plan_references = load_references("pb-plan")


@when_step("the planner produces design, task, and feature artifacts")
def step_when_planner_produces_artifacts(context: BehaveContext) -> None:
    context.planner_design_template = context.pb_plan_references["design_template.md"]
    context.planner_tasks_template = context.pb_plan_references["tasks_template.md"]


@then_step("the artifacts include the required contract fields in the existing markdown format")
def step_then_artifacts_include_contract_fields(context: BehaveContext) -> None:
    for content in context.pb_plan_templates:
        assert "contract-complete spec" in content
        assert "build-eligible spec" in content
        assert "markdown-carried packet" in content

    assert "PlannedSpecContract" in context.planner_design_template
    assert "TaskContract" in context.planner_design_template
    assert "BuildBlockedPacket" in context.planner_design_template
    assert "DesignChangeRequestPacket" in context.planner_design_template
    assert "🟡 IN PROGRESS" in context.planner_tasks_template
    assert "⛔ OBSOLETE" in context.planner_tasks_template
    assert "allowed status markers and transitions" in context.planner_tasks_template


@then_step(
    "the build workflow can treat the planned spec as ready for validation instead of re-interpreting missing structure"
)
def step_then_build_can_treat_spec_as_ready(context: BehaveContext) -> None:
    for content in context.pb_plan_templates:
        assert "Do not introduce a new schema or command surface" in content

    assert "build-eligible spec" in context.planner_tasks_template


@given_step("a planned spec is missing a required contract field")
def step_given_incomplete_planned_spec(context: BehaveContext) -> None:
    context.workflow_contract = _load_workflow_contract_context()
    context.missing_contract_field = "Scenario Coverage"


@when_step("the builder evaluates the spec")
def step_when_builder_evaluates_spec(context: BehaveContext) -> None:
    workflow_contract = context.workflow_contract
    context.builder_contract_design = workflow_contract["pb_plan_references"]["design_template.md"]
    context.builder_contract_tasks = workflow_contract["pb_plan_references"]["tasks_template.md"]
    context.builder_skill = workflow_contract["pb_build_skill"]
    context.builder_prompt = workflow_contract["pb_build_prompt"]
    context.builder_implementer = workflow_contract["pb_build_references"]["implementer_prompt.md"]


@then_step("the builder reports the missing field before spawning implementation work")
def step_then_builder_reports_missing_field(context: BehaveContext) -> None:
    assert context.missing_contract_field in context.builder_contract_design
    assert "Phase 0 — Validate Spec Contract" in context.builder_skill
    assert "Phase 0 — Validate Spec Contract" in context.builder_prompt

    for section in REQUIRED_DESIGN_SECTIONS:
        assert section in context.builder_skill
        assert section in context.builder_prompt

    for field in REQUIRED_TASK_FIELDS:
        assert field in context.builder_skill
        assert field in context.builder_prompt

    assert "at least one `.feature` file with at least one `Scenario`" in context.builder_skill
    assert "at least one `.feature` file with at least one `Scenario`" in context.builder_prompt

    assert "❌ Missing required design section in specs/<spec-dir>/design.md:" in (
        context.builder_skill
    )
    assert "❌ Missing required task field in specs/<spec-dir>/tasks.md for Task X.Y:" in (
        context.builder_skill
    )
    assert "❌ Missing required feature scenario in specs/<spec-dir>/features/" in (
        context.builder_skill
    )
    assert "❌ Missing required design section in specs/<spec-dir>/design.md:" in (
        context.builder_prompt
    )
    assert "❌ Missing required task field in specs/<spec-dir>/tasks.md for Task X.Y:" in (
        context.builder_prompt
    )
    assert "❌ Missing required feature scenario in specs/<spec-dir>/features/" in (
        context.builder_prompt
    )

    assert (
        "If the provided task block or project context is missing any required contract field, stop immediately."
        in (context.builder_implementer)
    )
    assert "❌ Missing required task field in specs/<spec-dir>/tasks.md for Task X.Y:" in (
        context.builder_implementer
    )


@then_step("the builder does not continue to later tasks")
def step_then_builder_stops_before_later_tasks(context: BehaveContext) -> None:
    assert context.builder_skill.index(
        "Phase 0 — Validate Spec Contract"
    ) < context.builder_skill.index("Create a **fresh subagent** for this task")
    assert context.builder_prompt.index(
        "Phase 0 — Validate Spec Contract"
    ) < context.builder_prompt.index("Spawn a fresh subagent")
    assert "stop immediately and report the missing field instead of spawning a subagent" in (
        context.builder_skill
    )
    assert "stop immediately and report the missing field instead of spawning a subagent" in (
        context.builder_prompt
    )


@given_step("a spec includes a source requirement ledger")
def step_given_spec_includes_source_requirement_ledger(context: BehaveContext) -> None:
    temp_dir = tempfile.TemporaryDirectory()
    context.traceability_temp_dir = temp_dir
    spec_dir = Path(temp_dir.name) / "spec"
    features_dir = spec_dir / "features"
    features_dir.mkdir(parents=True)

    (features_dir / "auth.feature").write_text(
        """Feature: Authentication

  Scenario: User authenticates successfully
    Given the user has valid credentials
    When the user signs in
    Then access is granted
""",
        encoding="utf-8",
    )
    (spec_dir / "design.md").write_text(
        """# Example Design

## Executive Summary

Concrete summary.

## Source Inputs & Normalization

### 2.1 Source Materials

Original design notes.

### 2.2 Normalization Approach

Normalized into a requirement ledger.

### 2.3 Source Requirement Ledger

| Requirement ID | Source Summary | Type | Notes |
| :--- | :--- | :--- | :--- |
| `R1` | `Support successful login` | `Functional` | `Must remain user-visible` |

## Requirements & Goals

Concrete requirements.

## Architecture Overview

Concrete architecture overview.

## Existing Components to Reuse

No existing components identified for reuse.

## Detailed Design

Concrete design details.

## Verification & Testing Strategy

Concrete verification strategy.

## Implementation Plan

Concrete implementation plan.
""",
        encoding="utf-8",
    )
    (spec_dir / "tasks.md").write_text(
        """# Example Tasks

### Task 1.1: Implement login

> **Context:** Add login endpoint.
> **Verification:** Run auth tests.

- **Status:** 🔴 TODO
- **Loop Type:** BDD+TDD
- **Scenario Coverage:** User authenticates successfully
- **Behavioral Contract:** Return token on valid credentials
- **Simplification Focus:** N/A
- [ ] **Step 1:** Implement login.
- [ ] **BDD Verification:** Run auth scenario.
- [ ] **Advanced Test Verification:** N/A because no advanced tests apply
- [ ] **Runtime Verification:** N/A because this is not runtime-facing work
""",
        encoding="utf-8",
    )
    context.traceability_spec_dir = spec_dir


@when_step("the validate command inspects a spec with missing requirement mappings")
def step_when_validate_inspects_traceability_gap(context: BehaveContext) -> None:
    runner = CliRunner()
    context.traceability_result = runner.invoke(
        main, ["validate", str(context.traceability_spec_dir)]
    )


@then_step("validation fails with requirement traceability findings before build work starts")
def step_then_validation_fails_with_traceability_findings(context: BehaveContext) -> None:
    result = context.traceability_result
    assert result.exit_code != 0
    assert "Validation failed" in result.output
    assert "Requirements Coverage Matrix" in result.output
    assert "Requirement Coverage" in result.output


@given_step("a spec includes a requirements coverage matrix scenario reference")
def step_given_spec_includes_matrix_scenario_reference(context: BehaveContext) -> None:
    temp_dir = tempfile.TemporaryDirectory()
    context.matrix_scenario_temp_dir = temp_dir
    spec_dir = Path(temp_dir.name) / "spec"
    features_dir = spec_dir / "features"
    features_dir.mkdir(parents=True)

    (features_dir / "auth.feature").write_text(
        """Feature: Authentication

  Scenario: User authenticates successfully
    Given the user has valid credentials
    When the user signs in
    Then access is granted
""",
        encoding="utf-8",
    )
    (spec_dir / "design.md").write_text(
        """# Example Design

## Executive Summary

Concrete summary.

## Source Inputs & Normalization

### 2.1 Source Materials

Original design notes.

### 2.2 Normalization Approach

Normalized into a requirement ledger.

### 2.3 Source Requirement Ledger

| Requirement ID | Source Summary | Type | Notes |
| :--- | :--- | :--- | :--- |
| `R1` | `Support successful login` | `Functional` | `Must remain user-visible` |

## Requirements & Goals

Concrete requirements.

## Requirements Coverage Matrix

| Requirement ID | Covered In Design | Scenario Coverage | Task Coverage | Status / Rationale |
| :--- | :--- | :--- | :--- | :--- |
| `R1` | `Detailed Design` | `auth.feature / User receives an auth error` | `Task 1.1` | `Covered` |

## Architecture Overview

Concrete architecture overview.

## Existing Components to Reuse

No existing components identified for reuse.

## Detailed Design

Concrete design details.

## Verification & Testing Strategy

Concrete verification strategy.

## Implementation Plan

Concrete implementation plan.
""",
        encoding="utf-8",
    )
    (spec_dir / "tasks.md").write_text(
        """# Example Tasks

### Task 1.1: Implement login

> **Context:** Add login endpoint.
> **Verification:** Run auth tests.

- **Status:** 🔴 TODO
- **Loop Type:** BDD+TDD
- **Requirement Coverage:** `R1`
- **Scenario Coverage:** User authenticates successfully
- **Behavioral Contract:** Return token on valid credentials
- **Simplification Focus:** N/A
- [ ] **Step 1:** Implement login.
- [ ] **BDD Verification:** Run auth scenario.
- [ ] **Advanced Test Verification:** N/A because no advanced tests apply
- [ ] **Runtime Verification:** N/A because this is not runtime-facing work
""",
        encoding="utf-8",
    )
    context.matrix_scenario_spec_dir = spec_dir


@when_step("the validate command inspects a spec with a missing matrix scenario target")
def step_when_validate_inspects_missing_matrix_scenario(context: BehaveContext) -> None:
    runner = CliRunner()
    context.matrix_scenario_result = runner.invoke(
        main, ["validate", str(context.matrix_scenario_spec_dir)]
    )


@then_step("validation fails with matrix scenario coverage findings before build work starts")
def step_then_validation_fails_with_matrix_scenario_findings(context: BehaveContext) -> None:
    result = context.matrix_scenario_result
    assert result.exit_code != 0
    assert "Validation failed" in result.output
    assert "Requirements Coverage Matrix" in result.output
    assert "Scenario reference not found in Requirements Coverage Matrix" in result.output


@given_step("a spec includes a requirements coverage matrix task reference")
def step_given_spec_includes_matrix_task_reference(context: BehaveContext) -> None:
    temp_dir = tempfile.TemporaryDirectory()
    context.matrix_task_temp_dir = temp_dir
    spec_dir = Path(temp_dir.name) / "spec"
    features_dir = spec_dir / "features"
    features_dir.mkdir(parents=True)

    (features_dir / "auth.feature").write_text(
        """Feature: Authentication

  Scenario: User authenticates successfully
    Given the user has valid credentials
    When the user signs in
    Then access is granted
""",
        encoding="utf-8",
    )
    (spec_dir / "design.md").write_text(
        """# Example Design

## Executive Summary

Concrete summary.

## Source Inputs & Normalization

### 2.1 Source Materials

Original design notes.

### 2.2 Normalization Approach

Normalized into a requirement ledger.

### 2.3 Source Requirement Ledger

| Requirement ID | Source Summary | Type | Notes |
| :--- | :--- | :--- | :--- |
| `R1` | `Support successful login` | `Functional` | `Must remain user-visible` |

## Requirements & Goals

Concrete requirements.

## Requirements Coverage Matrix

| Requirement ID | Covered In Design | Scenario Coverage | Task Coverage | Status / Rationale |
| :--- | :--- | :--- | :--- | :--- |
| `R1` | `Detailed Design` | `auth.feature / User authenticates successfully` | `Task 9.9` | `Covered` |

## Architecture Overview

Concrete architecture overview.

## Existing Components to Reuse

No existing components identified for reuse.

## Detailed Design

Concrete design details.

## Verification & Testing Strategy

Concrete verification strategy.

## Implementation Plan

Concrete implementation plan.
""",
        encoding="utf-8",
    )
    (spec_dir / "tasks.md").write_text(
        """# Example Tasks

### Task 1.1: Implement login

> **Context:** Add login endpoint.
> **Verification:** Run auth tests.

- **Status:** 🔴 TODO
- **Loop Type:** BDD+TDD
- **Requirement Coverage:** `R1`
- **Scenario Coverage:** User authenticates successfully
- **Behavioral Contract:** Return token on valid credentials
- **Simplification Focus:** N/A
- [ ] **Step 1:** Implement login.
- [ ] **BDD Verification:** Run auth scenario.
- [ ] **Advanced Test Verification:** N/A because no advanced tests apply
- [ ] **Runtime Verification:** N/A because this is not runtime-facing work
""",
        encoding="utf-8",
    )
    context.matrix_task_spec_dir = spec_dir


@when_step("the validate command inspects a spec with a missing matrix task target")
def step_when_validate_inspects_missing_matrix_task(context: BehaveContext) -> None:
    runner = CliRunner()
    context.matrix_task_result = runner.invoke(
        main, ["validate", str(context.matrix_task_spec_dir)]
    )


@then_step("validation fails with matrix task coverage findings before build work starts")
def step_then_validation_fails_with_matrix_task_findings(context: BehaveContext) -> None:
    result = context.matrix_task_result
    assert result.exit_code != 0
    assert "Validation failed" in result.output
    assert "Requirements Coverage Matrix" in result.output
    assert "Task reference not found in Requirements Coverage Matrix" in result.output


@given_step("a pending task in a build-eligible spec")
def step_given_pending_task(context: BehaveContext) -> None:
    context.workflow_contract = _load_workflow_contract_context()


@when_step("the builder starts work on the task")
def step_when_builder_starts_task(context: BehaveContext) -> None:
    workflow_contract = context.workflow_contract
    context.builder_contract_tasks = workflow_contract["pb_plan_references"]["tasks_template.md"]
    context.builder_skill = workflow_contract["pb_build_skill"]
    context.builder_prompt = workflow_contract["pb_build_prompt"]


@then_step("the task enters the allowed in-progress path before completion")
def step_then_task_enters_in_progress_path(context: BehaveContext) -> None:
    assert "🔴 TODO` -> `🟡 IN PROGRESS` -> `🟢 DONE`" in context.builder_contract_tasks
    assert "When the builder starts a task" in context.builder_skill
    assert "When the builder starts a task" in context.builder_prompt
    assert "legacy `TODO`" in context.builder_skill
    assert "legacy `TODO`" in context.builder_prompt
    assert "update the task Status to `🟡 IN PROGRESS`" in context.builder_skill
    assert "update the task Status to `🟡 IN PROGRESS`" in context.builder_prompt
    assert (
        "| In Progress | `🟡 IN PROGRESS` | Active implementation after work has started |"
        in context.builder_skill
    )
    assert (
        "| In Progress | `🟡 IN PROGRESS` | Active implementation after work has started |"
        in context.builder_prompt
    )


@then_step(
    "the task cannot be marked done until scenario, test, and verification evidence are satisfied"
)
def step_then_task_requires_evidence_before_done(context: BehaveContext) -> None:
    assert "Mark a task as done only after `BDD Verification` passes" in context.builder_skill
    assert "Completion gate" in context.builder_skill
    assert "runtime evidence" in context.builder_skill
    assert "Mark a task as done only after `BDD Verification` passes" in context.builder_prompt
    assert "Completion gate" in context.builder_prompt
    assert "runtime evidence" in context.builder_prompt
    assert (
        "Do not move a task directly from `🔴 TODO` or legacy `TODO` to `🟢 DONE`"
        in context.builder_skill
    )
    assert (
        "Do not move a task directly from `🔴 TODO` or legacy `TODO` to `🟢 DONE`"
        in context.builder_prompt
    )
    assert (
        "every required evidence checkbox in that task block is either `- [x]` or explicitly marked `N/A`"
        in context.builder_skill
    )
    assert (
        "every required evidence checkbox in that task block is either `- [x]` or explicitly marked `N/A`"
        in context.builder_prompt
    )


@given_step("a blocked build handoff for a feature")
def step_given_blocked_build_handoff(context: BehaveContext) -> None:
    context.workflow_contract = _load_workflow_contract_context()


@when_step("the handoff omits required failure evidence or impact details")
def step_when_handoff_omits_required_sections(context: BehaveContext) -> None:
    workflow_contract = context.workflow_contract
    context.refine_contract_design = workflow_contract["pb_plan_references"]["design_template.md"]
    context.refine_templates = workflow_contract["pb_refine_templates"]


@then_step("the refiner rejects the handoff as incomplete")
def step_then_refiner_rejects_incomplete_handoff(context: BehaveContext) -> None:
    assert "Failure Evidence" in context.refine_contract_design
    assert "Impact" in context.refine_contract_design
    for content in context.refine_templates:
        assert "🛑 Build Blocked" in content
        assert "high-priority execution evidence" in content
        assert "Validate the packet before modifying any spec file." in content
        assert "❌ Incomplete 🛑 Build Blocked packet. Missing required section(s):" in content
        assert (
            "❌ Incomplete 🔄 Design Change Request packet. Missing required section(s):" in content
        )
        assert (
            "Do not guess or reconstruct missing failure evidence, impact, or suggested changes."
            in content
        )


@then_step("when the handoff includes the required packet sections")
def step_then_handoff_includes_required_sections(context: BehaveContext) -> None:
    assert "BuildBlockedPacket" in context.refine_contract_design
    assert "Failure Evidence, Failing Step (or `N/A`), Suggested Design Change, Impact" in (
        context.refine_contract_design
    )
    assert "DesignChangeRequestPacket" in context.refine_contract_design
    assert "Failure Evidence, Failing Step (or `N/A`), Suggested Change, Impact" in (
        context.refine_contract_design
    )

    for content in context.refine_templates:
        assert "Required `🛑 Build Blocked` sections:" in content
        assert "Reason" in content
        assert "Loop Type" in content
        assert "Scenario Coverage" in content
        assert "What We Tried" in content
        assert "Failure Evidence" in content
        assert "Failing Step" in content
        assert "Suggested Design Change" in content
        assert "Impact" in content
        assert "Next Action" in content
        assert "Required `🔄 Design Change Request` sections:" in content
        assert "Problem" in content
        assert "Suggested Change" in content


@then_step("the refiner updates only the affected spec artifacts")
def step_then_refiner_updates_only_affected_artifacts(context: BehaveContext) -> None:
    for content in context.refine_templates:
        assert (
            "Only after packet validation passes may you update the affected `.feature`, `design.md`, and `tasks.md` files."
            in content
        )
        assert "Modify only the affected scenarios and steps" in content
        assert "Modify only the affected sections" in content
        assert content.index("Validate the packet before modifying any spec file.") < content.index(
            "If feedback changes user-visible behavior, update the relevant files under `specs/<spec-dir>/features/` first."
        )
