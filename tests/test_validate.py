"""Unit tests for the validate command."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from pb_spec.cli import main
from pb_spec.commands.validate import (
    get_latest_spec_dir,
    validate_build,
    validate_plan,
    validate_task,
)


@pytest.fixture
def runner() -> CliRunner:
    """Create a Click test runner."""
    return CliRunner()


@pytest.fixture
def valid_spec_dir(tmp_path: Path) -> Path:
    """Create a valid spec directory structure."""
    spec_dir = tmp_path / "specs" / "2026-03-28-test-feature"
    spec_dir.mkdir(parents=True)

    # Create design.md with required sections
    design_file = spec_dir / "design.md"
    design_file.write_text(
        "# Design Document\n"
        "\n"
        "## Architecture Decisions\n"
        "Decision 1: Use Python\n"
        "\n"
        "## BDD/TDD Strategy\n"
        "We will use BDD+TDD approach\n"
        "\n"
        "## Verification\n"
        "Tests will verify the implementation\n"
    )

    # Create tasks.md with valid structure (all required fields per contract §7.2)
    tasks_file = spec_dir / "tasks.md"
    tasks_file.write_text(
        "# Tasks\n"
        "\n"
        "### Task 1.1: Implement feature\n"
        "Context: Implement the core feature logic.\n"
        "Verification: Run the full test suite.\n"
        "Scenario Coverage: Test scenario in test.feature.\n"
        "Loop Type: TDD-only\n"
        "Behavioral Contract: Must pass all tests.\n"
        "Simplification Focus: Keep implementation minimal.\n"
        "BDD Verification: N/A — TDD-only task.\n"
        "Advanced Test Verification: N/A — no advanced tests planned.\n"
        "Runtime Verification: N/A — no runtime changes.\n"
        "Status: 🟢 DONE\n"
        "- [x] Step 1: Write test\n"
        "- [x] Step 2: Implement\n"
    )

    # Create features directory with a feature file
    features_dir = spec_dir / "features"
    features_dir.mkdir()
    feature_file = features_dir / "test.feature"
    feature_file.write_text(
        "Feature: Test Feature\n"
        "  Scenario: Test scenario\n"
        "    Given a condition\n"
        "    When action\n"
        "    Then result\n"
    )

    return spec_dir


@pytest.fixture
def invalid_spec_dir(tmp_path: Path) -> Path:
    """Create an invalid spec directory structure."""
    spec_dir = tmp_path / "specs" / "2026-03-28-invalid-feature"
    spec_dir.mkdir(parents=True)

    # Create design.md missing required sections
    design_file = spec_dir / "design.md"
    design_file.write_text("# Design Document\n\n## Some Section\nContent here\n")

    # Create tasks.md without valid task structure
    tasks_file = spec_dir / "tasks.md"
    tasks_file.write_text("# Tasks\n\nSome tasks here\n")

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
        """Test that it exits when specs directory doesn't exist."""
        specs_dir = tmp_path / "specs"

        with pytest.raises(SystemExit):
            get_latest_spec_dir(specs_dir)

    def test_exits_when_no_spec_dirs(self, tmp_path: Path) -> None:
        """Test that it exits when specs directory is empty."""
        specs_dir = tmp_path / "specs"
        specs_dir.mkdir()

        with pytest.raises(SystemExit):
            get_latest_spec_dir(specs_dir)


class TestValidatePlan:
    """Tests for validate_plan function."""

    def test_valid_spec_passes(self, valid_spec_dir: Path) -> None:
        """Test that a valid spec passes validation."""
        result = validate_plan(valid_spec_dir)
        assert result is True

    def test_missing_design_file_fails(self, tmp_path: Path) -> None:
        """Test that missing design.md fails validation."""
        spec_dir = tmp_path / "specs" / "test"
        spec_dir.mkdir(parents=True)

        tasks_file = spec_dir / "tasks.md"
        tasks_file.write_text("### Task 1.1: Test\nStatus: TODO\n")

        result = validate_plan(spec_dir)
        assert result is False

    def test_missing_tasks_file_fails(self, tmp_path: Path) -> None:
        """Test that missing tasks.md fails validation."""
        spec_dir = tmp_path / "specs" / "test"
        spec_dir.mkdir(parents=True)

        design_file = spec_dir / "design.md"
        design_file.write_text("## Architecture Decisions\n## BDD/TDD Strategy\n## Verification\n")

        result = validate_plan(spec_dir)
        assert result is False

    def test_missing_design_section_fails(self, tmp_path: Path) -> None:
        """Test that missing required design section fails validation."""
        spec_dir = tmp_path / "specs" / "test"
        spec_dir.mkdir(parents=True)

        design_file = spec_dir / "design.md"
        design_file.write_text("## Some Section\n")

        tasks_file = spec_dir / "tasks.md"
        tasks_file.write_text("### Task 1.1: Test\nStatus: TODO\n")

        result = validate_plan(spec_dir)
        assert result is False

    def test_invalid_tasks_structure_fails(self, tmp_path: Path) -> None:
        """Test that invalid tasks.md structure fails validation."""
        spec_dir = tmp_path / "specs" / "test"
        spec_dir.mkdir(parents=True)

        design_file = spec_dir / "design.md"
        design_file.write_text("## Architecture Decisions\n## BDD/TDD Strategy\n## Verification\n")

        tasks_file = spec_dir / "tasks.md"
        tasks_file.write_text("# Tasks\nSome content without task definitions\n")

        result = validate_plan(spec_dir)
        assert result is False


class TestValidateBuild:
    """Tests for validate_build function."""

    def test_all_tasks_done_passes(self, tmp_path: Path, monkeypatch) -> None:
        """Test that all tasks marked DONE with checked steps passes."""
        spec_dir = tmp_path / "specs" / "test"
        spec_dir.mkdir(parents=True)

        tasks_file = spec_dir / "tasks.md"
        tasks_file.write_text(
            "### Task 1.1: Test Task\n"
            "Status: 🟢 DONE\n"
            "- [x] Step 1: Complete\n"
            "- [x] Step 2: Complete\n"
        )

        # Create a clean code file
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "clean.py").write_text("def foo():\n    return 42\n")

        # Initialize a git repo so scanner can find files via git ls-files
        import subprocess

        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
        subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True)

        monkeypatch.chdir(tmp_path)
        result = validate_build(spec_dir)
        assert result is True

    def test_todo_task_fails(self, tmp_path: Path) -> None:
        """Test that TODO task fails validation."""
        spec_dir = tmp_path / "specs" / "test"
        spec_dir.mkdir(parents=True)

        tasks_file = spec_dir / "tasks.md"
        tasks_file.write_text("### Task 1.1: Test Task\nStatus: 🔴 TODO\n- [ ] Step 1: Not done\n")

        result = validate_build(spec_dir)
        assert result is False

    def test_in_progress_task_fails(self, tmp_path: Path) -> None:
        """Test that IN PROGRESS task fails validation."""
        spec_dir = tmp_path / "specs" / "test"
        spec_dir.mkdir(parents=True)

        tasks_file = spec_dir / "tasks.md"
        tasks_file.write_text(
            "### Task 1.1: Test Task\nStatus: 🟡 IN PROGRESS\n- [ ] Step 1: In progress\n"
        )

        result = validate_build(spec_dir)
        assert result is False

    def test_dcr_task_fails(self, tmp_path: Path) -> None:
        """Test that DCR task fails validation."""
        spec_dir = tmp_path / "specs" / "test"
        spec_dir.mkdir(parents=True)

        tasks_file = spec_dir / "tasks.md"
        tasks_file.write_text("### Task 1.1: Test Task\nStatus: 🔄 DCR\n- [ ] Step 1: Blocked\n")

        result = validate_build(spec_dir)
        assert result is False

    def test_unchecked_steps_fails(self, tmp_path: Path) -> None:
        """Test that DONE task with unchecked steps fails validation."""
        spec_dir = tmp_path / "specs" / "test"
        spec_dir.mkdir(parents=True)

        tasks_file = spec_dir / "tasks.md"
        tasks_file.write_text(
            "### Task 1.1: Test Task\n"
            "Status: 🟢 DONE\n"
            "- [x] Step 1: Complete\n"
            "- [ ] Step 2: Not complete\n"
        )

        result = validate_build(spec_dir)
        assert result is False

    def test_skipped_task_warns(self, tmp_path: Path, monkeypatch) -> None:
        """Test that skipped task warns but passes."""
        spec_dir = tmp_path / "specs" / "test"
        spec_dir.mkdir(parents=True)

        tasks_file = spec_dir / "tasks.md"
        tasks_file.write_text("### Task 1.1: Test Task\nStatus: ⏭️ SKIPPED\n- [ ] Step 1: Skipped\n")

        monkeypatch.chdir(tmp_path)
        result = validate_build(spec_dir)
        assert result is True


class TestValidateTask:
    """Tests for validate_task function."""

    def test_clean_codebase_passes(self, tmp_path: Path, monkeypatch) -> None:
        """Test that clean codebase passes validation."""
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "clean.py").write_text("def foo():\n    return 42\n")

        # Initialize a git repo so git ls-files finds our file
        import subprocess

        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
        subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True)

        monkeypatch.chdir(tmp_path)
        result = validate_task()
        assert result is True

    def test_codebase_with_todos_fails(self, tmp_path: Path, monkeypatch) -> None:
        """Test that codebase with TODOs fails validation."""
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        dirty_file = src_dir / "dirty.py"
        dirty_file.write_text("# TODO: fix this\n")

        # Initialize a git repo with an initial commit, then modify the file
        # so that get_git_modified_files() detects it as changed
        import subprocess

        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"], cwd=tmp_path, capture_output=True
        )
        subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, capture_output=True)
        # Commit a clean version first
        clean_file = src_dir / "clean.py"
        clean_file.write_text("pass\n")
        subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=tmp_path, capture_output=True)
        # Now dirty.py is an untracked file that git diff won't see,
        # so we mock get_git_modified_files to include it
        monkeypatch.setattr(
            "pb_spec.commands.validate.get_git_modified_files",
            lambda: {dirty_file},
        )

        monkeypatch.chdir(tmp_path)
        result = validate_task()
        assert result is False


class TestValidateCommand:
    """Tests for validate command integration."""

    def test_task_mode_passes_on_clean_code(self, runner: CliRunner) -> None:
        """Test that --task mode passes on clean codebase."""
        with runner.isolated_filesystem():
            # Create a clean Python file
            with open("clean.py", "w") as f:
                f.write("def foo():\n    return 42\n")

            result = runner.invoke(main, ["validate", "--task"])
            assert result.exit_code == 0
            assert "passed" in result.output.lower() or "✅" in result.output
