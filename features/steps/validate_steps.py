"""Step definitions for validate.feature."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from behave import given, then, when

_VALID_DESIGN_SECTIONS: dict[str, str] = {
    "Summary": "## Summary\nA brief summary.\n",
    "Approach": "## Approach\nImplementation approach.\n",
    "Architecture Decisions": "## Architecture Decisions\nDecision 1\n",
    "BDD/TDD Strategy": "## BDD/TDD Strategy\nStrategy\n",
    "Verification": "## Verification\nVerification approach\n",
}

_VALID_TASK_FIELDS: dict[str, str] = {
    "Context:": "Context: Test context.\n",
    "Verification:": "Verification: Run tests.\n",
    "Status:": "Status: 🔴 TODO\n",
    "Scenario Coverage:": "Scenario Coverage: @scenario-1.1\n",
}

_BUILD_BLOCKED_FIELDS: dict[str, str] = {
    "Reason": "Reason: Tests fail with current API.\n",
    "Requested Change": "Requested Change: Add retry logic to client.\n",
    "Impact": "Impact: Adds 50ms latency to all calls.\n",
}

_DCR_FIELDS: dict[str, str] = {
    "Reason": "Reason: API shape changed upstream.\n",
    "Requested Change": "Requested Change: Update client to v2 API.\n",
    "Impact": "Impact: Breaking change for callers.\n",
}

_VALID_FEATURE_FILE = (
    "Feature: Test Feature\n"
    "  Scenario: Test scenario\n"
    "    Given a condition\n"
    "    When action\n"
    "    Then result\n"
)


def _design_md(missing_section: str | None = None) -> str:
    content = "# Design Document\n\n"
    for name, body in _VALID_DESIGN_SECTIONS.items():
        if name != missing_section:
            content += body + "\n"
    return content


def _tasks_md(missing_field: str | None = None) -> str:
    content = "# Tasks\n\n### Task 1.1: Test Task\n"
    for name, line in _VALID_TASK_FIELDS.items():
        if name != missing_field:
            content += line
    content += "- [ ] Step 1: Write test\n"
    return content


def _tasks_md_with_build_blocked(missing_field: str | None = None) -> str:
    content = "# Tasks\n\n### Task 1.1: Test Task\n"
    for line in _VALID_TASK_FIELDS.values():
        content += line
    content += "- [ ] Step 1: Write test\n"
    content += "\n🛑 Build Blocked — Task 1.1: Test Task\n"
    for name, line in _BUILD_BLOCKED_FIELDS.items():
        if name != missing_field:
            content += line
    return content


def _tasks_md_with_dcr(missing_field: str | None = None) -> str:
    content = "# Tasks\n\n### Task 1.1: Test Task\n"
    for line in _VALID_TASK_FIELDS.values():
        content += line
    content += "- [ ] Step 1: Write test\n"
    content += "\n🔄 Design Change Request — Task 1.1: Test Task\n"
    for name, line in _DCR_FIELDS.items():
        if name != missing_field:
            content += line
    return content


def _write_features_dir(spec_dir: Path) -> None:
    features_dir = spec_dir / "features"
    features_dir.mkdir(exist_ok=True)
    (features_dir / "test.feature").write_text(_VALID_FEATURE_FILE)


@given("I have a pb-spec project set up")
def step_pb_spec_project_setup(context) -> None:
    """Set up a pb-spec project context."""
    context.temp_dir = tempfile.mkdtemp()
    context.add_cleanup(shutil.rmtree, context.temp_dir, ignore_errors=True)
    context.specs_dir = Path(context.temp_dir) / "specs"
    context.specs_dir.mkdir()
    context.spec_dir = context.specs_dir / "2026-03-28-test-feature"
    context.spec_dir.mkdir()
    context.cwd = os.getcwd()


@given("I have a spec directory with a valid plan")
def step_valid_plan(context) -> None:
    """Create a spec directory with valid design.md, tasks.md, and features/."""
    (context.spec_dir / "design.md").write_text(_design_md())
    (context.spec_dir / "tasks.md").write_text(_tasks_md())
    _write_features_dir(context.spec_dir)


@given('I have a spec directory with design.md missing "{section}"')
def step_design_missing_section(context, section: str) -> None:
    """Create a spec directory with design.md missing one required section."""
    (context.spec_dir / "design.md").write_text(_design_md(missing_section=section))
    (context.spec_dir / "tasks.md").write_text(_tasks_md())
    _write_features_dir(context.spec_dir)


@given('I have a spec directory with tasks.md missing "{field}"')
def step_tasks_missing_field(context, field: str) -> None:
    """Create a spec directory with tasks.md missing one required field."""
    (context.spec_dir / "design.md").write_text(_design_md())
    (context.spec_dir / "tasks.md").write_text(_tasks_md(missing_field=field))
    _write_features_dir(context.spec_dir)


@given("I have a spec directory with a valid Build Blocked packet")
def step_valid_build_blocked(context) -> None:
    """Create a spec directory with a complete Build Blocked packet."""
    (context.spec_dir / "design.md").write_text(_design_md())
    (context.spec_dir / "tasks.md").write_text(_tasks_md_with_build_blocked())
    _write_features_dir(context.spec_dir)


@given('I have a spec directory with a Build Blocked packet missing "{field}"')
def step_build_blocked_missing_field(context, field: str) -> None:
    """Create a spec directory with a Build Blocked packet missing one field."""
    (context.spec_dir / "design.md").write_text(_design_md())
    (context.spec_dir / "tasks.md").write_text(_tasks_md_with_build_blocked(missing_field=field))
    _write_features_dir(context.spec_dir)


@given("I have a spec directory with a valid DCR packet")
def step_valid_dcr(context) -> None:
    """Create a spec directory with a complete DCR packet."""
    (context.spec_dir / "design.md").write_text(_design_md())
    (context.spec_dir / "tasks.md").write_text(_tasks_md_with_dcr())
    _write_features_dir(context.spec_dir)


@given('I have a spec directory with a DCR packet missing "{field}"')
def step_dcr_missing_field(context, field: str) -> None:
    """Create a spec directory with a DCR packet missing one field."""
    (context.spec_dir / "design.md").write_text(_design_md())
    (context.spec_dir / "tasks.md").write_text(_tasks_md_with_dcr(missing_field=field))
    _write_features_dir(context.spec_dir)


@given("I have a spec directory without a features directory")
def step_no_features_directory(context) -> None:
    """Create a valid spec directory without a features/ directory."""
    (context.spec_dir / "design.md").write_text(_design_md())
    (context.spec_dir / "tasks.md").write_text(_tasks_md())


@when('I run "{command}"')
def step_run_command(context, command: str) -> None:
    """Run a pb-spec command."""
    original_dir = os.getcwd()
    try:
        os.chdir(context.temp_dir)
        result = subprocess.run(
            command.split(),
            capture_output=True,
            text=True,
            cwd=context.temp_dir,
        )
        context.return_code = result.returncode
        context.output = result.stdout + result.stderr
    finally:
        os.chdir(original_dir)


@then("the command should succeed")
def step_command_succeeds(context) -> None:
    """Verify the command succeeded."""
    assert context.return_code == 0, (
        f"Command should succeed but got exit code {context.return_code}.\nOutput: {context.output}"
    )


@then("the command should fail")
def step_command_fails(context) -> None:
    """Verify the command failed."""
    assert context.return_code != 0, (
        f"Command should fail but got exit code {context.return_code}.\nOutput: {context.output}"
    )


@then('I should see "{text}"')
def step_should_see(context, text: str) -> None:
    """Verify output contains specific text."""
    normalized_output = context.output.lower()
    normalized_text = text.lower()
    assert normalized_text in normalized_output, (
        f"Should see '{text}' in output.\nActual output: {context.output}"
    )
