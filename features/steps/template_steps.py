from __future__ import annotations

from collections.abc import Callable
from typing import Any, cast

from behave import given, then, when

from pb_spec.templates import load_prompt, load_skill_content

type BehaveContext = Any
type StepFunction = Callable[..., object]
type StepDecoratorFactory = Callable[[str], Callable[[StepFunction], StepFunction]]

given_step = cast(StepDecoratorFactory, given)
when_step = cast(StepDecoratorFactory, when)
then_step = cast(StepDecoratorFactory, then)


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
