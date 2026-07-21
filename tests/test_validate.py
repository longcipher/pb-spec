"""Unit tests for the validate command."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from click.testing import CliRunner

from pb_spec.cli import main
from pb_spec.commands.discovery import get_latest_spec_dir
from pb_spec.exceptions import SpecNotFoundError
from pb_spec.validation.build import validate_build, validate_task
from pb_spec.validation.plan import validate_plan, validate_tasks_structure


@pytest.fixture
def runner() -> CliRunner:
    """Create a Click test runner."""
    return CliRunner()


def _create_spec_files(
    spec_dir: Path,
    design_content: str | None = None,
    tasks_content: str | None = None,
    features_content: str | None = None,
) -> None:
    """Helper to create spec files."""
    spec_dir.mkdir(parents=True, exist_ok=True)
    if design_content is not None:
        (spec_dir / "design.md").write_text(design_content)
    if tasks_content is not None:
        (spec_dir / "tasks.md").write_text(tasks_content)
    if features_content is not None:
        features_dir = spec_dir / "features"
        features_dir.mkdir(exist_ok=True)
        (features_dir / "test.feature").write_text(features_content)


VALID_DESIGN_CONTENT = (
    "# Design Document\n\n"
    "## Summary\nA brief summary of the feature.\n\n"
    "## Approach\nImplementation approach.\n\n"
    "## Architecture Decisions\nDecision 1: Use Python\n\n"
    "## BDD/TDD Strategy\nWe will use BDD+TDD approach\n\n"
    "## Verification\nTests will verify the implementation\n"
)

VALID_TASKS_CONTENT = (
    "# Tasks\n\n"
    "### Task 1.1: Implement feature\n"
    "Context: Implement the core feature logic.\n"
    "Verification: Run the full test suite.\n"
    "Scenario Coverage: Test scenario in test.feature.\n"
    "Status: 🟢 DONE\n"
    "- [x] Step 1: Write test\n"
    "- [x] Step 2: Implement\n"
)

VALID_FEATURE_CONTENT = (
    "Feature: Test Feature\n"
    "  Scenario: Test scenario\n"
    "    Given a condition\n"
    "    When action\n"
    "    Then result\n"
)

_DESIGN_SECTIONS: dict[str, str] = {
    "Summary": "## Summary\nSummary.\n\n",
    "Approach": "## Approach\nApproach.\n\n",
    "Architecture Decisions": "## Architecture Decisions\nDecision.\n\n",
    "BDD/TDD Strategy": "## BDD/TDD Strategy\nStrategy.\n\n",
    "Verification": "## Verification\nVerify.\n",
}

_TASK_FIELDS: dict[str, str] = {
    "Context:": "Context: Build piece.\n",
    "Verification:": "Verification: Run tests.\n",
    "Scenario Coverage:": "Scenario Coverage: N/A\n",
    "Status:": "Status: 🔴 TODO\n",
}


def _design_missing(missing: str) -> str:
    """Build a design.md body with all required sections except `missing`."""
    parts = [_DESIGN_SECTIONS[k] for k in _DESIGN_SECTIONS if k != missing]
    return "# Design\n\n" + "".join(parts)


def _tasks_missing(missing: str) -> str:
    """Build a tasks.md body with all required fields except `missing`."""
    fields = [_TASK_FIELDS[k] for k in _TASK_FIELDS if k != missing]
    return "# Tasks\n\n### Task 1.1: Test task\n" + "".join(fields) + "- [ ] Step 1: Write test\n"


def _task_with_packet(
    status: str,
    packet_header: str,
    packet_fields: str,
) -> str:
    """Build a tasks.md with a task block followed by a contract packet.

    Status is placed before Scenario Coverage so the contract block header
    (which the parser treats as a continuation line) contaminates Scenario
    Coverage rather than Status. Scenario Coverage is only checked for
    non-emptiness, while Status must match an allowed marker.
    """
    return (
        "# Tasks\n\n"
        "### Task 1.1: Test task\n"
        f"Status: {status}\n"
        "Context: Build piece.\n"
        "Verification: Run tests.\n"
        "Scenario Coverage: N/A\n"
        "- [ ] Step 1: Resolve\n"
        "\n"
        f"{packet_header}\n"
        "\n"
        f"{packet_fields}"
    )


@pytest.fixture
def valid_spec_dir(tmp_path: Path) -> Path:
    """Create a valid spec directory structure."""
    spec_dir = tmp_path / "specs" / "2026-03-28-test-feature"
    _create_spec_files(
        spec_dir,
        design_content=VALID_DESIGN_CONTENT,
        tasks_content=VALID_TASKS_CONTENT,
        features_content=VALID_FEATURE_CONTENT,
    )
    return spec_dir


class TestCLI:
    """Tests for CLI interface."""

    def test_help_shows_validate_command(self, runner: CliRunner) -> None:
        """Test that help shows the validate command."""
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "validate" in result.output

    def test_validate_help_shows_options(self, runner: CliRunner) -> None:
        """Test that validate help shows all options."""
        result = runner.invoke(main, ["validate", "--help"])
        assert result.exit_code == 0
        assert "--plan" in result.output
        assert "--build" in result.output
        assert "--task" in result.output

    def test_validate_requires_mode(self, runner: CliRunner) -> None:
        """Test that validate requires a mode flag."""
        result = runner.invoke(main, ["validate"])
        assert result.exit_code != 0


class TestGetLatestSpecDir:
    """Tests for get_latest_spec_dir function."""

    def test_returns_latest_spec_dir(self, tmp_path: Path) -> None:
        """Test that it returns the latest spec directory by name."""
        specs_dir = tmp_path / "specs"
        specs_dir.mkdir()
        (specs_dir / "2026-03-01-old-feature").mkdir()
        (specs_dir / "2026-03-28-new-feature").mkdir()
        result = get_latest_spec_dir(specs_dir)
        assert result.name == "2026-03-28-new-feature"

    def test_exits_when_no_specs_dir(self, tmp_path: Path) -> None:
        """Test that it raises SpecNotFoundError when specs directory doesn't exist."""
        with pytest.raises(SpecNotFoundError):
            get_latest_spec_dir(tmp_path / "specs")

    def test_exits_when_no_spec_dirs(self, tmp_path: Path) -> None:
        """Test that it raises SpecNotFoundError when specs directory is empty."""
        specs_dir = tmp_path / "specs"
        specs_dir.mkdir()
        with pytest.raises(SpecNotFoundError):
            get_latest_spec_dir(specs_dir)


class TestValidatePlan:
    """Tests for validate_plan function."""

    def test_valid_spec_passes(self, valid_spec_dir: Path) -> None:
        """Test that a valid spec passes validation."""
        result = validate_plan(valid_spec_dir)
        assert result.is_valid is True

    def test_missing_design_file_fails(self, tmp_path: Path) -> None:
        """Test that missing design.md fails validation."""
        spec_dir = tmp_path / "specs" / "test"
        spec_dir.mkdir(parents=True)
        (spec_dir / "tasks.md").write_text(VALID_TASKS_CONTENT)
        result = validate_plan(spec_dir)
        assert result.is_valid is False

    def test_missing_tasks_file_fails(self, tmp_path: Path) -> None:
        """Test that missing tasks.md fails validation."""
        spec_dir = tmp_path / "specs" / "test"
        spec_dir.mkdir(parents=True)
        (spec_dir / "design.md").write_text(VALID_DESIGN_CONTENT)
        result = validate_plan(spec_dir)
        assert result.is_valid is False

    def test_missing_design_section_fails(self, tmp_path: Path) -> None:
        """Test that design with no required sections fails validation."""
        spec_dir = tmp_path / "specs" / "test"
        _create_spec_files(
            spec_dir,
            design_content="## Some Section\n",
            tasks_content=VALID_TASKS_CONTENT,
        )
        result = validate_plan(spec_dir)
        assert result.is_valid is False

    def test_missing_summary_section_fails(self, tmp_path: Path) -> None:
        """Test that design missing Summary section fails."""
        spec_dir = tmp_path / "specs" / "test"
        _create_spec_files(
            spec_dir,
            design_content=_design_missing("Summary"),
            tasks_content=VALID_TASKS_CONTENT,
        )
        result = validate_plan(spec_dir)
        assert result.is_valid is False
        assert any("Summary" in e.message for e in result.errors)

    def test_missing_approach_section_fails(self, tmp_path: Path) -> None:
        """Test that design missing Approach section fails."""
        spec_dir = tmp_path / "specs" / "test"
        _create_spec_files(
            spec_dir,
            design_content=_design_missing("Approach"),
            tasks_content=VALID_TASKS_CONTENT,
        )
        result = validate_plan(spec_dir)
        assert result.is_valid is False
        assert any("Approach" in e.message for e in result.errors)

    def test_missing_architecture_decisions_section_fails(self, tmp_path: Path) -> None:
        """Test that design missing Architecture Decisions section fails."""
        spec_dir = tmp_path / "specs" / "test"
        _create_spec_files(
            spec_dir,
            design_content=_design_missing("Architecture Decisions"),
            tasks_content=VALID_TASKS_CONTENT,
        )
        result = validate_plan(spec_dir)
        assert result.is_valid is False
        assert any("Architecture Decisions" in e.message for e in result.errors)

    def test_missing_bdd_tdd_strategy_section_fails(self, tmp_path: Path) -> None:
        """Test that design missing BDD/TDD Strategy section fails."""
        spec_dir = tmp_path / "specs" / "test"
        _create_spec_files(
            spec_dir,
            design_content=_design_missing("BDD/TDD Strategy"),
            tasks_content=VALID_TASKS_CONTENT,
        )
        result = validate_plan(spec_dir)
        assert result.is_valid is False
        assert any("BDD/TDD Strategy" in e.message for e in result.errors)

    def test_missing_verification_section_fails(self, tmp_path: Path) -> None:
        """Test that design missing Verification section fails."""
        spec_dir = tmp_path / "specs" / "test"
        _create_spec_files(
            spec_dir,
            design_content=_design_missing("Verification"),
            tasks_content=VALID_TASKS_CONTENT,
        )
        result = validate_plan(spec_dir)
        assert result.is_valid is False
        assert any("Verification" in e.message for e in result.errors)

    def test_invalid_tasks_structure_fails(self, tmp_path: Path) -> None:
        """Test that tasks.md without task blocks fails validation."""
        spec_dir = tmp_path / "specs" / "test"
        _create_spec_files(
            spec_dir,
            design_content=VALID_DESIGN_CONTENT,
            tasks_content="# Tasks\nSome content without task definitions\n",
        )
        result = validate_plan(spec_dir)
        assert result.is_valid is False

    def test_duplicate_task_ids_fail(self, tmp_path: Path) -> None:
        """Test that duplicate task IDs fail validation."""
        spec_dir = tmp_path / "specs" / "test"
        one_task = (
            "### Task 1.1: Task\n"
            "Context: Build.\n"
            "Verification: Run tests.\n"
            "Scenario Coverage: N/A\n"
            "Status: 🔴 TODO\n"
            "- [ ] Step 1: Write test\n"
        )
        tasks_content = f"# Tasks\n\n{one_task}\n{one_task}"
        _create_spec_files(
            spec_dir,
            design_content=VALID_DESIGN_CONTENT,
            tasks_content=tasks_content,
        )
        result = validate_tasks_structure(spec_dir)
        assert result.is_valid is False
        assert any("Duplicate task ID" in e.message for e in result.errors)

    def test_task_missing_status_fails(self, tmp_path: Path) -> None:
        """Test that task missing Status field fails."""
        spec_dir = tmp_path / "specs" / "test"
        _create_spec_files(spec_dir, tasks_content=_tasks_missing("Status:"))
        result = validate_tasks_structure(spec_dir)
        assert result.is_valid is False
        assert any("missing required field: 'Status:'" in e.message for e in result.errors)

    def test_task_missing_context_fails(self, tmp_path: Path) -> None:
        """Test that task missing Context field fails."""
        spec_dir = tmp_path / "specs" / "test"
        _create_spec_files(spec_dir, tasks_content=_tasks_missing("Context:"))
        result = validate_tasks_structure(spec_dir)
        assert result.is_valid is False
        assert any("missing required field: 'Context:'" in e.message for e in result.errors)

    def test_task_missing_verification_fails(self, tmp_path: Path) -> None:
        """Test that task missing Verification field fails."""
        spec_dir = tmp_path / "specs" / "test"
        _create_spec_files(spec_dir, tasks_content=_tasks_missing("Verification:"))
        result = validate_tasks_structure(spec_dir)
        assert result.is_valid is False
        assert any("missing required field: 'Verification:'" in e.message for e in result.errors)

    def test_task_missing_scenario_coverage_fails(self, tmp_path: Path) -> None:
        """Test that task missing Scenario Coverage field fails."""
        spec_dir = tmp_path / "specs" / "test"
        _create_spec_files(spec_dir, tasks_content=_tasks_missing("Scenario Coverage:"))
        result = validate_tasks_structure(spec_dir)
        assert result.is_valid is False
        assert any(
            "missing required field: 'Scenario Coverage:'" in e.message for e in result.errors
        )

    def test_invalid_task_status_fails(self, tmp_path: Path) -> None:
        """Test that task with invalid Status (no emoji marker) fails."""
        spec_dir = tmp_path / "specs" / "test"
        tasks_content = (
            "# Tasks\n\n"
            "### Task 1.1: Invalid status\n"
            "Context: Build piece.\n"
            "Verification: Run tests.\n"
            "Scenario Coverage: N/A\n"
            "Status: DONE\n"
            "- [ ] Step 1: Write test\n"
        )
        _create_spec_files(spec_dir, tasks_content=tasks_content)
        result = validate_tasks_structure(spec_dir)
        assert result.is_valid is False
        assert any("invalid Status" in e.message for e in result.errors)

    def test_task_without_checkbox_fails(self, tmp_path: Path) -> None:
        """Test that task without checkbox step fails."""
        spec_dir = tmp_path / "specs" / "test"
        tasks_content = (
            "# Tasks\n\n"
            "### Task 1.1: No checkbox\n"
            "Context: Build piece.\n"
            "Verification: Run tests.\n"
            "Scenario Coverage: N/A\n"
            "Status: 🔴 TODO\n"
        )
        _create_spec_files(spec_dir, tasks_content=tasks_content)
        result = validate_tasks_structure(spec_dir)
        assert result.is_valid is False
        assert any("contains no step checkboxes" in e.message for e in result.errors)

    def test_na_scenario_coverage_passes(self, tmp_path: Path) -> None:
        """Test that Scenario Coverage: N/A (literal) passes for non-BDD tasks."""
        spec_dir = tmp_path / "specs" / "test"
        tasks_content = (
            "# Tasks\n\n"
            "### Task 1.1: Infrastructure task\n"
            "Context: Setup CI.\n"
            "Verification: Run pipeline.\n"
            "Scenario Coverage: N/A\n"
            "Status: 🔴 TODO\n"
            "- [ ] Step 1: Configure CI\n"
        )
        _create_spec_files(spec_dir, tasks_content=tasks_content)
        result = validate_tasks_structure(spec_dir)
        assert result.is_valid is True

    def test_valid_build_blocked_packet_passes(self, tmp_path: Path) -> None:
        """Test that a valid Build Blocked packet passes validation."""
        spec_dir = tmp_path / "specs" / "test"
        packet = (
            "Reason: Three consecutive failures.\n"
            "Requested Change: Update design boundary.\n"
            "Impact: Task 1.1 blocked; affects @scenario-1.\n"
        )
        tasks = _task_with_packet("🔄 DCR", "🛑 Build Blocked — Task 1.1: Test task", packet)
        _create_spec_files(spec_dir, tasks_content=tasks)
        result = validate_tasks_structure(spec_dir)
        assert result.is_valid is True

    def test_incomplete_build_blocked_packet_fails(self, tmp_path: Path) -> None:
        """Test that Build Blocked packet missing Impact fails."""
        spec_dir = tmp_path / "specs" / "test"
        packet = "Reason: Three consecutive failures.\nRequested Change: Update design boundary.\n"
        tasks = _task_with_packet("🔄 DCR", "🛑 Build Blocked — Task 1.1: Test task", packet)
        _create_spec_files(spec_dir, tasks_content=tasks)
        result = validate_tasks_structure(spec_dir)
        assert result.is_valid is False
        assert any("Incomplete 🛑 Build Blocked packet" in e.message for e in result.errors)

    def test_valid_dcr_packet_passes(self, tmp_path: Path) -> None:
        """Test that a valid DCR packet passes validation."""
        spec_dir = tmp_path / "specs" / "test"
        packet = (
            "Reason: Spec is ambiguous about data format.\n"
            "Requested Change: Add Data Models section with DBML schema.\n"
            "Impact: Task 1.1 blocked; affects @scenario-2.\n"
        )
        tasks = _task_with_packet(
            "🔄 DCR", "🔄 Design Change Request — Task 1.1: Test task", packet
        )
        _create_spec_files(spec_dir, tasks_content=tasks)
        result = validate_tasks_structure(spec_dir)
        assert result.is_valid is True

    def test_incomplete_dcr_packet_fails(self, tmp_path: Path) -> None:
        """Test that DCR packet missing Requested Change fails."""
        spec_dir = tmp_path / "specs" / "test"
        packet = "Reason: Spec is ambiguous.\nImpact: Task 1.1 blocked.\n"
        tasks = _task_with_packet(
            "🔄 DCR", "🔄 Design Change Request — Task 1.1: Test task", packet
        )
        _create_spec_files(spec_dir, tasks_content=tasks)
        result = validate_tasks_structure(spec_dir)
        assert result.is_valid is False
        assert any("Incomplete 🔄 Design Change Request packet" in e.message for e in result.errors)


class TestValidateBuild:
    """Tests for validate_build function."""

    def test_all_tasks_done_passes(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that all tasks marked DONE with checked steps passes."""
        spec_dir = tmp_path / "specs" / "test"
        spec_dir.mkdir(parents=True)
        tasks_content = (
            "### Task 1.1: Test Task\n"
            "Status: 🟢 DONE\n"
            "- [x] Step 1: Complete\n"
            "- [x] Step 2: Complete\n"
        )
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "clean.py").write_text("def foo():\n    return 42\n")
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
        subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True)
        _create_spec_files(spec_dir, tasks_content=tasks_content)
        monkeypatch.chdir(tmp_path)
        result = validate_build(spec_dir)
        assert result.is_valid is True

    def test_todo_task_fails(self, tmp_path: Path) -> None:
        """Test that TODO task fails validation."""
        spec_dir = tmp_path / "specs" / "test"
        spec_dir.mkdir(parents=True)
        tasks_content = "### Task 1.1: Test Task\nStatus: 🔴 TODO\n- [ ] Step 1: Not done\n"
        _create_spec_files(spec_dir, tasks_content=tasks_content)
        result = validate_build(spec_dir)
        assert result.is_valid is False

    def test_in_progress_task_fails(self, tmp_path: Path) -> None:
        """Test that IN PROGRESS task fails validation."""
        spec_dir = tmp_path / "specs" / "test"
        spec_dir.mkdir(parents=True)
        tasks_content = (
            "### Task 1.1: Test Task\nStatus: 🟡 IN PROGRESS\n- [ ] Step 1: In progress\n"
        )
        _create_spec_files(spec_dir, tasks_content=tasks_content)
        result = validate_build(spec_dir)
        assert result.is_valid is False

    def test_dcr_task_fails(self, tmp_path: Path) -> None:
        """Test that DCR task fails validation."""
        spec_dir = tmp_path / "specs" / "test"
        spec_dir.mkdir(parents=True)
        tasks_content = "### Task 1.1: Test Task\nStatus: 🔄 DCR\n- [ ] Step 1: Blocked\n"
        _create_spec_files(spec_dir, tasks_content=tasks_content)
        result = validate_build(spec_dir)
        assert result.is_valid is False

    def test_unchecked_steps_fails(self, tmp_path: Path) -> None:
        """Test that DONE task with unchecked steps fails validation."""
        spec_dir = tmp_path / "specs" / "test"
        spec_dir.mkdir(parents=True)
        tasks_content = (
            "### Task 1.1: Test Task\n"
            "Status: 🟢 DONE\n"
            "- [x] Step 1: Complete\n"
            "- [ ] Step 2: Not complete\n"
        )
        _create_spec_files(spec_dir, tasks_content=tasks_content)
        result = validate_build(spec_dir)
        assert result.is_valid is False


class TestValidateTask:
    """Tests for validate_task function."""

    def test_clean_codebase_passes(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that clean codebase passes validation."""
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "clean.py").write_text("def foo():\n    return 42\n")
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
        subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True)
        monkeypatch.chdir(tmp_path)
        result = validate_task()
        assert result.is_valid is True

    def test_codebase_with_todos_fails(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that codebase with TODOs fails validation."""
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        dirty_file = src_dir / "dirty.py"
        dirty_file.write_text("# TODO: fix this\n")
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=tmp_path,
            capture_output=True,
        )
        subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, capture_output=True)
        clean_file = src_dir / "clean.py"
        clean_file.write_text("pass\n")
        subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True)
        subprocess.run(
            ["git", "commit", "--no-gpg-sign", "-m", "init"], cwd=tmp_path, capture_output=True
        )
        monkeypatch.setattr(
            "pb_spec.validation.build.get_git_modified_files",
            lambda _root_dir=".": {dirty_file},
        )
        monkeypatch.chdir(tmp_path)
        result = validate_task()
        assert result.is_valid is False
        assert len(result.errors) > 0


class TestValidateCommand:
    """Tests for validate command integration."""

    def test_task_mode_passes_on_clean_code(self, runner: CliRunner) -> None:
        """Test that --task mode passes on clean codebase."""
        with runner.isolated_filesystem():
            with open("clean.py", "w") as f:
                f.write("def foo():\n    return 42\n")
            result = runner.invoke(main, ["validate", "--task"])
            assert result.exit_code == 0
            assert "passed" in result.output.lower() or "✅" in result.output


CONSOLIDATED_VALID_DESIGN = (
    "# Design: Codebase Quality Improvements\n\n"
    "## Summary\n"
    "Consolidated improvements across correctness, security, and performance.\n\n"
    "## Approach\nImplement findings sequentially.\n\n"
    "## Findings\n\n"
    "### Finding 1: Fix N+1 query\n"
    "- **Category:** performance\n"
    "- **Impact:** HIGH\n\n"
    "## Architecture Decisions\n"
    "### AD-01: Use batch loading\n"
    "- **Status:** Accepted\n\n"
    "**Context:** N+1 queries detected.\n"
    "**Decision:** Use DataLoader pattern.\n"
    "**Consequences:** Reduces query count.\n\n"
    "## BDD/TDD Strategy\nBDD+TDD with behave.\n\n"
    "## Verification\nRun full test suite.\n"
)

CONSOLIDATED_VALID_TASKS = (
    "# Tasks\n\n"
    "### Task 1.1: Fix N+1 query\n"
    "Context: Address performance issue.\n"
    "Verification: Run tests.\n"
    "Scenario Coverage: features/performance.feature — Batch loading.\n"
    "Status: 🔴 TODO\n"
    "- [ ] Step 1: Write failing test\n"
)

CONSOLIDATED_CROSS_FINDING_TASKS = (
    "# Tasks\n\n"
    "### Task 1.1: Finding 1 — Fix bug\n"
    "Context: Fix the bug.\n"
    "Verification: Run tests.\n"
    "Scenario Coverage: features/correctness.feature — Bug fix.\n"
    "Status: 🔴 TODO\n"
    "- [ ] Step 1: Write test\n"
    "\n"
    "### Task 2.1: Finding 2 — Add feature\n"
    "Context: Add new feature.\n"
    "Verification: Run tests.\n"
    "Scenario Coverage: features/security.feature — Auth check.\n"
    "Status: 🔴 TODO\n"
    "- [ ] Step 1: Write test\n"
)


class TestConsolidatedSpec:
    """Tests for consolidated spec format (pb-improve → pb-build flow)."""

    def test_consolidated_design_passes(self, tmp_path: Path) -> None:
        """Test that consolidated design.md with Findings section passes."""
        spec_dir = tmp_path / "specs" / "2026-06-12-improvements"
        _create_spec_files(
            spec_dir,
            design_content=CONSOLIDATED_VALID_DESIGN,
            tasks_content=CONSOLIDATED_VALID_TASKS,
            features_content=(
                "Feature: Performance\n  Scenario: Batch loading\n    Given orders\n"
                "    When fetched\n    Then one query\n"
            ),
        )
        result = validate_plan(spec_dir)
        assert result.is_valid is True

    def test_consolidated_tasks_with_cross_finding_numbering(self, tmp_path: Path) -> None:
        """Test that tasks numbered across findings (1.1, 2.1) pass validation."""
        spec_dir = tmp_path / "specs" / "2026-06-12-multi-finding"
        _create_spec_files(
            spec_dir,
            design_content=CONSOLIDATED_VALID_DESIGN,
            tasks_content=CONSOLIDATED_CROSS_FINDING_TASKS,
            features_content=(
                "Feature: Correctness\n  Scenario: Bug fix\n    Given bug\n"
                "    When fixed\n    Then works\n"
                "Feature: Security\n  Scenario: Auth\n    Given user\n"
                "    When auth\n    Then ok\n"
            ),
        )
        result = validate_plan(spec_dir)
        assert result.is_valid is True

    def test_consolidated_design_missing_approach_fails(self, tmp_path: Path) -> None:
        """Test that consolidated design.md missing Approach section fails."""
        spec_dir = tmp_path / "specs" / "2026-06-12-no-approach"
        _create_spec_files(
            spec_dir,
            design_content=_design_missing("Approach"),
            tasks_content=CONSOLIDATED_VALID_TASKS,
        )
        result = validate_plan(spec_dir)
        assert result.is_valid is False
        assert any("Approach" in e.message for e in result.errors)

    def test_consolidated_tasks_missing_status_fails(self, tmp_path: Path) -> None:
        """Test that consolidated tasks.md missing Status field fails."""
        spec_dir = tmp_path / "specs" / "2026-06-12-no-status"
        _create_spec_files(
            spec_dir,
            design_content=CONSOLIDATED_VALID_DESIGN,
            tasks_content=_tasks_missing("Status:"),
        )
        result = validate_plan(spec_dir)
        assert result.is_valid is False
        assert any("Status" in e.message for e in result.errors)

    def test_consolidated_build_passes_when_all_done(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that consolidated spec passes build validation when all tasks are DONE."""
        spec_dir = tmp_path / "specs" / "2026-06-12-done"
        tasks_content = (
            "# Tasks\n\n"
            "### Task 1.1: Fix bug\n"
            "Status: 🟢 DONE\n"
            "- [x] Step 1: Write test\n"
            "- [x] Step 2: Implement\n"
            "\n"
            "### Task 2.1: Add feature\n"
            "Status: 🟢 DONE\n"
            "- [x] Step 1: Write test\n"
            "- [x] Step 2: Implement\n"
        )
        _create_spec_files(spec_dir, tasks_content=tasks_content)
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "clean.py").write_text("def foo():\n    return 42\n")
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
        subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True)
        monkeypatch.chdir(tmp_path)
        result = validate_build(spec_dir)
        assert result.is_valid is True

    def test_consolidated_build_fails_when_first_task_todo(self, tmp_path: Path) -> None:
        """Test that consolidated spec fails build when first task is TODO."""
        spec_dir = tmp_path / "specs" / "2026-06-12-partial"
        tasks_content = (
            "# Tasks\n\n"
            "### Task 1.1: Fix bug\n"
            "Status: 🔴 TODO\n"
            "- [ ] Step 1: Write test\n"
            "\n"
            "### Task 2.1: Add feature\n"
            "Status: 🟢 DONE\n"
            "- [x] Step 1: Complete\n"
        )
        _create_spec_files(spec_dir, tasks_content=tasks_content)
        result = validate_build(spec_dir)
        assert result.is_valid is False
