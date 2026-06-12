"""Step definitions for validate.feature."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from behave import given, then, when


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


@given("I have a spec directory with a valid design.md")
def step_valid_design_md(context) -> None:
    """Create a valid design.md file."""
    design_file = context.spec_dir / "design.md"
    design_file.write_text(
        "# Design Document\n"
        "\n"
        "## Summary\n"
        "A brief summary.\n"
        "\n"
        "## Approach\n"
        "Implementation approach.\n"
        "\n"
        "## Architecture Decisions\n"
        "Decision 1\n"
        "\n"
        "## BDD/TDD Strategy\n"
        "Strategy\n"
        "\n"
        "## Code Simplification Constraints\n"
        "Keep it minimal.\n"
        "\n"
        "## BDD Scenario Inventory\n"
        "Scenario 1: Basic flow\n"
        "\n"
        "## Existing Components to Reuse\n"
        "None.\n"
        "\n"
        "## Verification\n"
        "Verification approach\n"
    )
    context.design_file = design_file

    # Also create tasks.md (with all required fields per contract §7.2) and features directory
    tasks_file = context.spec_dir / "tasks.md"
    tasks_file.write_text(
        "# Tasks\n"
        "\n"
        "### Task 1.1: Test Task\n"
        "Context: Test context.\n"
        "Verification: Run tests.\n"
        "Scenario Coverage: Test scenario.\n"
        "Loop Type: TDD-only\n"
        "Behavioral Contract: Must pass.\n"
        "Simplification Focus: Keep minimal.\n"
        "BDD Verification: N/A — TDD-only task.\n"
        "Advanced Test Verification: N/A — no advanced tests planned.\n"
        "Runtime Verification: N/A — no runtime changes.\n"
        "Status: 🟢 DONE\n"
        "- [x] Step 1: Complete\n"
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
    """Create an incomplete design.md file with a minimal tasks.md."""
    design_file = context.spec_dir / "design.md"
    design_file.write_text("# Design Document\n\n## Some Section\nContent\n")
    context.design_file = design_file

    tasks_file = context.spec_dir / "tasks.md"
    tasks_file.write_text(
        "# Tasks\n"
        "\n"
        "### Task 1.1: Test Task\n"
        "Context: Test context.\n"
        "Verification: Run tests.\n"
        "Scenario Coverage: N/A — internal task.\n"
        "Loop Type: TDD-only\n"
        "Behavioral Contract: Must pass.\n"
        "Simplification Focus: Keep minimal.\n"
        "BDD Verification: N/A — TDD-only task.\n"
        "Advanced Test Verification: N/A — no advanced tests planned.\n"
        "Runtime Verification: N/A — no runtime changes.\n"
        "Status: 🔴 TODO\n"
        "- [ ] Step 1: Write test\n"
    )


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
        "# Tasks\n"
        "\n"
        "### Task 1.1: Test Task\n"
        "Context: Test context.\n"
        "Verification: Run tests.\n"
        "Scenario Coverage: Test scenario.\n"
        "Loop Type: TDD-only\n"
        "Behavioral Contract: Must pass.\n"
        "Simplification Focus: Keep minimal.\n"
        "BDD Verification: N/A — TDD-only task.\n"
        "Advanced Test Verification: N/A — no advanced tests planned.\n"
        "Runtime Verification: N/A — no runtime changes.\n"
        "Status: 🟢 DONE\n"
        "- [x] Step 1: Complete\n"
    )
    context.tasks_file = tasks_file

    # Also create design.md and features directory for complete validation
    design_file = context.spec_dir / "design.md"
    design_file.write_text(
        "# Design Document\n"
        "\n"
        "## Summary\n"
        "A brief summary.\n"
        "\n"
        "## Approach\n"
        "Implementation approach.\n"
        "\n"
        "## Architecture Decisions\n"
        "Decision 1\n"
        "\n"
        "## BDD/TDD Strategy\n"
        "Strategy\n"
        "\n"
        "## Code Simplification Constraints\n"
        "Keep it minimal.\n"
        "\n"
        "## BDD Scenario Inventory\n"
        "Scenario 1: Basic flow\n"
        "\n"
        "## Existing Components to Reuse\n"
        "None.\n"
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


@given("I have a consolidated spec directory with valid design.md and tasks.md")
def step_consolidated_valid_spec(context) -> None:
    """Create a consolidated spec directory with all required sections."""
    design_file = context.spec_dir / "design.md"
    design_file.write_text(
        "# Design: Codebase Quality Improvements\n"
        "\n"
        "## Summary\n"
        "Consolidated improvements across correctness, security, and performance.\n"
        "\n"
        "## Approach\n"
        "Implement findings sequentially, starting with highest-impact items.\n"
        "\n"
        "## Findings\n"
        "\n"
        "### Finding 1: Fix N+1 query\n"
        "- **Category:** performance\n"
        "- **Impact:** HIGH\n"
        "\n"
        "#### Approach\n"
        "Add batch loading.\n"
        "\n"
        "## Architecture Decisions\n"
        "### AD-01: Use batch loading\n"
        "- **Status:** Accepted\n"
        "\n"
        "**Context:** N+1 queries detected.\n"
        "**Decision:** Use DataLoader pattern.\n"
        "**Consequences:** Reduces query count.\n"
        "\n"
        "## BDD/TDD Strategy\n"
        "BDD+TDD with behave.\n"
        "\n"
        "## Code Simplification Constraints\n"
        "Keep minimal.\n"
        "\n"
        "## BDD Scenario Inventory\n"
        "- features/performance.feature — Batch loading: reduces queries → Task 1.1\n"
        "\n"
        "## Existing Components to Reuse\n"
        "None.\n"
        "\n"
        "## Verification\n"
        "Run full test suite.\n"
    )

    tasks_file = context.spec_dir / "tasks.md"
    tasks_file.write_text(
        "# Tasks\n"
        "\n"
        "### Task 1.1: Fix N+1 query\n"
        "Context: Address performance issue in order listing.\n"
        "Verification: Run tests.\n"
        "Scenario Coverage: features/performance.feature — Batch loading.\n"
        "Loop Type: BDD+TDD\n"
        "Behavioral Contract: Preserve existing behavior.\n"
        "Simplification Focus: Reduce nesting.\n"
        "BDD Verification: uv run behave features/performance.feature\n"
        "Advanced Test Verification: N/A — no advanced tests planned.\n"
        "Runtime Verification: N/A — no runtime changes.\n"
        "Status: 🔴 TODO\n"
        "- [ ] Step 1: Write failing test\n"
    )

    features_dir = context.spec_dir / "features"
    features_dir.mkdir(exist_ok=True)
    (features_dir / "performance.feature").write_text(
        "Feature: Performance improvements\n"
        "  Scenario: Batch loading reduces queries\n"
        "    Given a list of orders\n"
        "    When orders are fetched\n"
        "    Then only one query is executed\n"
    )


@given('I have a consolidated spec directory with design.md missing "{section}" section')
def step_consolidated_missing_design_section(context, section: str) -> None:
    """Create a consolidated spec with a missing design section."""
    design_file = context.spec_dir / "design.md"
    design_file.write_text(
        "# Design: Improvements\n"
        "\n"
        "## Summary\n"
        "Summary.\n"
        "\n"
        "## Approach\n"
        "Approach.\n"
        "\n"
        "## Architecture Decisions\n"
        "Decision.\n"
        "\n"
        "## Code Simplification Constraints\n"
        "Keep minimal.\n"
        "\n"
        "## BDD Scenario Inventory\n"
        "Scenarios.\n"
        "\n"
        "## Existing Components to Reuse\n"
        "None.\n"
        "\n"
        "## Verification\n"
        "Run tests.\n"
    )

    tasks_file = context.spec_dir / "tasks.md"
    tasks_file.write_text(
        "# Tasks\n"
        "\n"
        "### Task 1.1: Test Task\n"
        "Context: Test.\n"
        "Verification: Run tests.\n"
        "Scenario Coverage: N/A — internal task.\n"
        "Loop Type: TDD-only\n"
        "Behavioral Contract: Must pass.\n"
        "Simplification Focus: Keep minimal.\n"
        "BDD Verification: N/A — TDD-only task.\n"
        "Advanced Test Verification: N/A — no advanced tests.\n"
        "Runtime Verification: N/A — no runtime changes.\n"
        "Status: 🔴 TODO\n"
        "- [ ] Step 1: Write test\n"
    )


@given('I have a consolidated spec directory with tasks.md missing "{field}" field')
def step_consolidated_missing_task_field(context, field: str) -> None:
    """Create a consolidated spec with a missing task field."""
    design_file = context.spec_dir / "design.md"
    design_file.write_text(
        "# Design: Improvements\n"
        "\n"
        "## Summary\n"
        "Summary.\n"
        "\n"
        "## Approach\n"
        "Approach.\n"
        "\n"
        "## Architecture Decisions\n"
        "Decision.\n"
        "\n"
        "## BDD/TDD Strategy\n"
        "Strategy.\n"
        "\n"
        "## Code Simplification Constraints\n"
        "Keep minimal.\n"
        "\n"
        "## BDD Scenario Inventory\n"
        "Scenarios.\n"
        "\n"
        "## Existing Components to Reuse\n"
        "None.\n"
        "\n"
        "## Verification\n"
        "Run tests.\n"
    )

    tasks_file = context.spec_dir / "tasks.md"
    # Write a task that is missing the specified field
    tasks_file.write_text(
        "# Tasks\n"
        "\n"
        "### Task 1.1: Test Task\n"
        "Context: Test.\n"
        "Verification: Run tests.\n"
        "Scenario Coverage: N/A — internal task.\n"
        "Behavioral Contract: Must pass.\n"
        "Simplification Focus: Keep minimal.\n"
        "BDD Verification: N/A — TDD-only task.\n"
        "Advanced Test Verification: N/A — no advanced tests.\n"
        "Runtime Verification: N/A — no runtime changes.\n"
        "Status: 🔴 TODO\n"
        "- [ ] Step 1: Write test\n"
    )


@given("I have a full-mode spec directory with all required sections")
def step_full_mode_valid_spec(context) -> None:
    """Create a full-mode spec directory with all required sections."""
    design_file = context.spec_dir / "design.md"
    design_file.write_text(
        "# Design: Full Feature\n"
        "\n"
        "## Executive Summary\n"
        "Complete feature implementation.\n"
        "\n"
        "## Requirements & Goals\n"
        "- **[REQ-01]:** The system *shall* validate inputs when form is submitted.\n"
        "\n"
        "## Architecture Overview\n"
        "```mermaid\n"
        "graph TD\n"
        "  A[Client] --> B[Server]\n"
        "```\n"
        "\n"
        "## Architecture Decisions\n"
        "### AD-01: Use REST API\n"
        "- **Status:** Accepted\n"
        "\n"
        "**Context:** Need external API.\n"
        "**Decision:** Use REST.\n"
        "**Consequences:** Simple integration.\n"
        "\n"
        "## Data Models\n"
        "```dbml\n"
        "Table users {\n"
        "  id integer [pk]\n"
        "  name varchar\n"
        "}\n"
        "```\n"
        "\n"
        "## Interface Contracts\n"
        "```python\n"
        "class UserProto(Protocol):\n"
        "    def get_name(self) -> str: ...\n"
        "```\n"
        "\n"
        "## Detailed Design\n"
        "Implementation details.\n"
        "\n"
        "## Verification & Testing Strategy\n"
        "BDD + unit tests.\n"
        "\n"
        "## Implementation Plan\n"
        "- [ ] Phase 1: Core\n"
    )

    tasks_file = context.spec_dir / "tasks.md"
    tasks_file.write_text(
        "# Tasks\n"
        "\n"
        "### Task 1.1: Implement feature\n"
        "Context: Build the feature.\n"
        "Verification: Run tests.\n"
        "Scenario Coverage: Test scenario.\n"
        "Loop Type: BDD+TDD\n"
        "Behavioral Contract: Must pass.\n"
        "Simplification Focus: Keep minimal.\n"
        "BDD Verification: uv run behave\n"
        "Advanced Test Verification: N/A — no advanced tests.\n"
        "Runtime Verification: N/A — no runtime changes.\n"
        "Status: 🔴 TODO\n"
        "- [ ] Step 1: Write test\n"
    )

    features_dir = context.spec_dir / "features"
    features_dir.mkdir(exist_ok=True)
    (features_dir / "test.feature").write_text(
        "Feature: Full feature\n"
        "  Scenario: Happy path\n"
        "    Given a user\n"
        "    When they submit\n"
        "    Then success\n"
    )


@given('I have a full-mode spec directory missing "{section}" section')
def step_full_mode_missing_section(context, section: str) -> None:
    """Create a full-mode spec missing a required section."""
    design_file = context.spec_dir / "design.md"
    # Write all sections except the missing one
    sections = {
        "Executive Summary": "## Executive Summary\nSummary.\n",
        "Requirements & Goals": "## Requirements & Goals\n- **[REQ-01]:** The system *shall* validate.\n",
        "Architecture Overview": "## Architecture Overview\n```mermaid\ngraph TD\n  A-->B\n```\n",
        "Architecture Decisions": "## Architecture Decisions\n### AD-01: Decision\n- **Status:** Accepted\n\n**Context:** C\n**Decision:** D\n**Consequences:** E\n",
        "Data Models": "## Data Models\n```dbml\nTable t { id integer [pk] }\n```\n",
        "Interface Contracts": "## Interface Contracts\n```python\nproto...\n```\n",
        "Detailed Design": "## Detailed Design\nDetails.\n",
        "Verification & Testing Strategy": "## Verification & Testing Strategy\nStrategy.\n",
        "Implementation Plan": "## Implementation Plan\n- [ ] Phase 1\n",
    }
    content = "# Design: Full Feature\n\n"
    for sec_name, sec_content in sections.items():
        if sec_name != section:
            content += sec_content + "\n"
    design_file.write_text(content)

    tasks_file = context.spec_dir / "tasks.md"
    tasks_file.write_text(
        "# Tasks\n"
        "\n"
        "### Task 1.1: Implement\n"
        "Context: Build.\n"
        "Verification: Run tests.\n"
        "Scenario Coverage: Scenario.\n"
        "Loop Type: TDD-only\n"
        "Behavioral Contract: Must pass.\n"
        "Simplification Focus: Keep minimal.\n"
        "BDD Verification: N/A — TDD-only.\n"
        "Advanced Test Verification: N/A — no advanced tests.\n"
        "Runtime Verification: N/A — no runtime.\n"
        "Status: 🔴 TODO\n"
        "- [ ] Step 1: Write test\n"
    )

    features_dir = context.spec_dir / "features"
    features_dir.mkdir(exist_ok=True)
    (features_dir / "test.feature").write_text(
        "Feature: Test\n  Scenario: Test\n    Given a\n    When b\n    Then c\n"
    )


@given("I have a consolidated tasks.md with tasks across multiple findings")
def step_consolidated_cross_finding_tasks(context) -> None:
    """Create a consolidated tasks.md with tasks numbered across findings."""
    design_file = context.spec_dir / "design.md"
    design_file.write_text(
        "# Design: Multiple Findings\n"
        "\n"
        "## Summary\n"
        "Multiple improvements.\n"
        "\n"
        "## Approach\n"
        "Approach.\n"
        "\n"
        "## Architecture Decisions\n"
        "Decision.\n"
        "\n"
        "## BDD/TDD Strategy\n"
        "Strategy.\n"
        "\n"
        "## Code Simplification Constraints\n"
        "Keep minimal.\n"
        "\n"
        "## BDD Scenario Inventory\n"
        "Scenarios.\n"
        "\n"
        "## Existing Components to Reuse\n"
        "None.\n"
        "\n"
        "## Verification\n"
        "Run tests.\n"
    )

    tasks_file = context.spec_dir / "tasks.md"
    tasks_file.write_text(
        "# Tasks\n"
        "\n"
        "### Task 1.1: Finding 1 — Fix bug\n"
        "Context: Fix the bug.\n"
        "Verification: Run tests.\n"
        "Scenario Coverage: features/correctness.feature — Bug fix.\n"
        "Loop Type: BDD+TDD\n"
        "Behavioral Contract: Must pass.\n"
        "Simplification Focus: Keep minimal.\n"
        "BDD Verification: uv run behave features/correctness.feature\n"
        "Advanced Test Verification: N/A — no advanced tests.\n"
        "Runtime Verification: N/A — no runtime changes.\n"
        "Status: 🔴 TODO\n"
        "- [ ] Step 1: Write test\n"
        "\n"
        "### Task 2.1: Finding 2 — Add feature\n"
        "Context: Add new feature.\n"
        "Verification: Run tests.\n"
        "Scenario Coverage: features/security.feature — Auth check.\n"
        "Loop Type: BDD+TDD\n"
        "Behavioral Contract: Must pass.\n"
        "Simplification Focus: Keep minimal.\n"
        "BDD Verification: uv run behave features/security.feature\n"
        "Advanced Test Verification: N/A — no advanced tests.\n"
        "Runtime Verification: N/A — no runtime changes.\n"
        "Status: 🔴 TODO\n"
        "- [ ] Step 1: Write test\n"
    )

    features_dir = context.spec_dir / "features"
    features_dir.mkdir(exist_ok=True)
    (features_dir / "correctness.feature").write_text(
        "Feature: Correctness\n"
        "  Scenario: Bug fix\n"
        "    Given a bug\n"
        "    When fixed\n"
        "    Then works\n"
    )
    (features_dir / "security.feature").write_text(
        "Feature: Security\n"
        "  Scenario: Auth check\n"
        "    Given a user\n"
        "    When authenticated\n"
        "    Then access granted\n"
    )


def _init_git_repo(context) -> None:
    """Initialize a git repo with an initial commit so scanner can find files."""
    subprocess.run(["git", "init"], cwd=context.temp_dir, capture_output=True, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=context.temp_dir,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=context.temp_dir,
        capture_output=True,
    )
    subprocess.run(["git", "add", "-A"], cwd=context.temp_dir, capture_output=True, check=True)
    subprocess.run(
        ["git", "commit", "-m", "initial", "--allow-empty"],
        cwd=context.temp_dir,
        capture_output=True,
        check=True,
    )


@given("I have a clean codebase without issues")
def step_clean_codebase(context) -> None:
    """Create a clean codebase."""
    src_dir = Path(context.temp_dir) / "src"
    src_dir.mkdir()
    (src_dir / "clean.py").write_text("def foo():\n    return 42\n")
    _init_git_repo(context)


@given('I have a codebase with "{issue}" comment')
def step_codebase_with_issue(context, issue: str) -> None:
    """Create a codebase with a specific issue.

    Files are created, committed, then modified so they appear as git changes.
    """
    src_dir = Path(context.temp_dir) / "src"
    src_dir.mkdir()
    if "console.log" in issue:
        (src_dir / "test.js").write_text("function foo() {}\n")
    else:
        (src_dir / "test.py").write_text("pass\n")
    _init_git_repo(context)
    # Now modify the file so it shows up as a git modification
    if "console.log" in issue:
        (src_dir / "test.js").write_text(f"function foo() {{ {issue}('debug'); }}\n")
    else:
        (src_dir / "test.py").write_text(f"# {issue} fix this\n")


@given('I have a codebase with "@pytest.mark.skip" decorator')
def step_codebase_with_pytest_skip(context) -> None:
    """Create a codebase with pytest skip decorator."""
    src_dir = Path(context.temp_dir) / "src"
    src_dir.mkdir()
    (src_dir / "test.py").write_text("def test_foo():\n    pass\n")
    _init_git_repo(context)
    (src_dir / "test.py").write_text("@pytest.mark.skip\ndef test_foo():\n    pass\n")


@given('I have a codebase with "console.log" statement')
def step_codebase_with_console_log(context) -> None:
    """Create a codebase with console.log."""
    src_dir = Path(context.temp_dir) / "src"
    src_dir.mkdir()
    (src_dir / "test.js").write_text("function foo() {}\n")
    _init_git_repo(context)
    (src_dir / "test.js").write_text("function foo() {\n  console.log('debug');\n}\n")


@given('I have a codebase with "raise NotImplementedError"')
def step_codebase_with_not_implemented(context) -> None:
    """Create a codebase with NotImplementedError."""
    src_dir = Path(context.temp_dir) / "src"
    src_dir.mkdir()
    (src_dir / "test.py").write_text("def foo():\n    pass\n")
    _init_git_repo(context)
    (src_dir / "test.py").write_text("def foo():\n    raise NotImplementedError\n")


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
