"""Step definitions for validate.feature."""

from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path

from behave import given, then, when


@given("I have a pb-spec project set up")
def step_pb_spec_project_setup(context) -> None:
    """Set up a pb-spec project context."""
    context.temp_dir = tempfile.mkdtemp()
    context.specs_dir = Path(context.temp_dir) / "specs"
    context.specs_dir.mkdir()
    context.spec_dir = context.specs_dir / "2026-03-28-test-feature"
    context.spec_dir.mkdir()
    context.cwd = os.getcwd()


@given("I have a spec directory with a valid design.md")
def step_valid_design_md(context) -> None:
    """Create a valid design.md file."""
    design_file = context.spec_dir / "design.md"
    design_file.write_text(
        "# Design Document\n"
        "\n"
        "## Architecture Decisions\n"
        "Decision 1\n"
        "\n"
        "## BDD/TDD Strategy\n"
        "Strategy\n"
        "\n"
        "## Verification\n"
        "Verification approach\n"
    )
    context.design_file = design_file

    # Also create tasks.md and features directory for complete validation
    tasks_file = context.spec_dir / "tasks.md"
    tasks_file.write_text(
        "# Tasks\n\n### Task 1.1: Test Task\nStatus: 🟢 DONE\n- [x] Step 1: Complete\n"
    )

    features_dir = context.spec_dir / "features"
    features_dir.mkdir(exist_ok=True)
    feature_file = features_dir / "test.feature"
    feature_file.write_text(
        "Feature: Test Feature\n"
        "  Scenario: Test scenario\n"
        "    Given a condition\n"
        "    When action\n"
        "    Then result\n"
    )


@given('design.md contains "{section}" section')
def step_design_contains_section(context, section: str) -> None:
    """Verify design.md contains a specific section."""
    content = context.design_file.read_text()
    assert section in content, f"design.md should contain '{section}' section"


@given("I have a spec directory with an incomplete design.md")
def step_incomplete_design_md(context) -> None:
    """Create an incomplete design.md file."""
    design_file = context.spec_dir / "design.md"
    design_file.write_text("# Design Document\n\n## Some Section\nContent\n")
    context.design_file = design_file


@given('design.md is missing "{section}" section')
def step_design_missing_section(context, section: str) -> None:
    """Verify design.md is missing a specific section."""
    content = context.design_file.read_text()
    assert section not in content, f"design.md should not contain '{section}' section"


@given("I have a spec directory with a valid tasks.md")
def step_valid_tasks_md(context) -> None:
    """Create a valid tasks.md file."""
    tasks_file = context.spec_dir / "tasks.md"
    tasks_file.write_text(
        "# Tasks\n\n### Task 1.1: Test Task\nStatus: 🟢 DONE\n- [x] Step 1: Complete\n"
    )
    context.tasks_file = tasks_file

    # Also create design.md and features directory for complete validation
    design_file = context.spec_dir / "design.md"
    design_file.write_text(
        "# Design Document\n"
        "\n"
        "## Architecture Decisions\n"
        "Decision 1\n"
        "\n"
        "## BDD/TDD Strategy\n"
        "Strategy\n"
        "\n"
        "## Verification\n"
        "Verification approach\n"
    )

    features_dir = context.spec_dir / "features"
    features_dir.mkdir(exist_ok=True)
    feature_file = features_dir / "test.feature"
    feature_file.write_text(
        "Feature: Test Feature\n"
        "  Scenario: Test scenario\n"
        "    Given a condition\n"
        "    When action\n"
        "    Then result\n"
    )


@given('tasks.md contains "{field}" definition')
def step_tasks_contains_definition(context, field: str) -> None:
    """Verify tasks.md contains a specific definition."""
    content = context.tasks_file.read_text()
    assert field in content, f"tasks.md should contain '{field}'"


@given('tasks.md contains "{field}" field')
def step_tasks_contains_field(context, field: str) -> None:
    """Verify tasks.md contains a specific field."""
    content = context.tasks_file.read_text()
    assert field in content, f"tasks.md should contain '{field}'"


@given("I have a spec directory with tasks.md")
def step_spec_with_tasks(context) -> None:
    """Create a spec directory with tasks.md."""
    tasks_file = context.spec_dir / "tasks.md"
    tasks_file.write_text("# Tasks\n\n")
    context.tasks_file = tasks_file


@given('all tasks have status "{status}"')
def step_all_tasks_status(context, status: str) -> None:
    """Set all tasks to a specific status."""
    content = context.tasks_file.read_text()
    if "### Task" not in content:
        content += f"### Task 1.1: Test Task\nStatus: {status}\n"
    else:
        # Replace existing status
        import re

        content = re.sub(r"Status: .+", f"Status: {status}", content)
    context.tasks_file.write_text(content)


@given('all task steps are checked "{checkbox}"')
def step_all_steps_checked(context, checkbox: str) -> None:
    """Mark all task steps as checked."""
    content = context.tasks_file.read_text()
    if "- [" not in content:
        content += "- [x] Step 1: Complete\n"
    context.tasks_file.write_text(content)


@given('a task has status "{status}"')
def step_task_has_status(context, status: str) -> None:
    """Set a task to a specific status."""
    content = context.tasks_file.read_text()
    content += f"### Task 1.1: Test Task\nStatus: {status}\n- [ ] Step 1: Pending\n"
    context.tasks_file.write_text(content)


@given('a task has an unchecked step "{checkbox}"')
def step_task_unchecked_step(context, checkbox: str) -> None:
    """Add an unchecked step to a task."""
    content = context.tasks_file.read_text()
    if "- [ ]" not in content:
        content += f"{checkbox} Unchecked step\n"
    context.tasks_file.write_text(content)


@given("I have a clean codebase without issues")
def step_clean_codebase(context) -> None:
    """Create a clean codebase."""
    src_dir = Path(context.temp_dir) / "src"
    src_dir.mkdir()
    (src_dir / "clean.py").write_text("def foo():\n    return 42\n")


@given('I have a codebase with "{issue}" comment')
def step_codebase_with_issue(context, issue: str) -> None:
    """Create a codebase with a specific issue."""
    src_dir = Path(context.temp_dir) / "src"
    src_dir.mkdir()
    # Create different file types based on issue
    if "console.log" in issue:
        (src_dir / "test.js").write_text(f"function foo() {{ {issue}('debug'); }}\n")
    else:
        (src_dir / "test.py").write_text(f"# {issue} fix this\n")


@given('I have a codebase with "@pytest.mark.skip" decorator')
def step_codebase_with_pytest_skip(context) -> None:
    """Create a codebase with pytest skip decorator."""
    src_dir = Path(context.temp_dir) / "src"
    src_dir.mkdir()
    (src_dir / "test.py").write_text("@pytest.mark.skip\ndef test_foo():\n    pass\n")


@given('I have a codebase with "console.log" statement')
def step_codebase_with_console_log(context) -> None:
    """Create a codebase with console.log."""
    src_dir = Path(context.temp_dir) / "src"
    src_dir.mkdir()
    (src_dir / "test.js").write_text("function foo() {\n  console.log('debug');\n}\n")


@given('I have a codebase with "raise NotImplementedError"')
def step_codebase_with_not_implemented(context) -> None:
    """Create a codebase with NotImplementedError."""
    src_dir = Path(context.temp_dir) / "src"
    src_dir.mkdir()
    (src_dir / "test.py").write_text("def foo():\n    raise NotImplementedError\n")


@when('I run "{command}"')
def step_run_command(context, command: str) -> None:
    """Run a pb-spec command."""
    # Change to temp directory for the test
    os.chdir(context.temp_dir)

    # Run the command
    result = subprocess.run(
        command.split(),
        capture_output=True,
        text=True,
        cwd=context.temp_dir,
    )

    context.return_code = result.returncode
    context.output = result.stdout + result.stderr

    # Restore original directory
    os.chdir(context.cwd)


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
    # Normalize the output for flexible matching
    normalized_output = context.output.lower()
    normalized_text = text.lower()

    # Handle variations in the output format
    flexible_checks = {
        "todo/fixme found": ["todo/fixme", "todo", "fixme"],
        "skipped test found": ["skipped test"],
        "debug artifact found": ["debug artifact"],
        "notimplemented/mock found": ["notimplemented", "mock"],
    }

    found = normalized_text in normalized_output

    if not found and normalized_text in flexible_checks:
        for alternative in flexible_checks[normalized_text]:
            if alternative in normalized_output:
                found = True
                break

    assert found, f"Should see '{text}' in output.\nActual output: {context.output}"
