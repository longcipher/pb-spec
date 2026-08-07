"""Unit tests for the test/mutate/verify CLI commands."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from click.testing import CliRunner

from pb_spec.cli import main
from pb_spec.commands.mutate import build_mutate_command, mutation_script_path
from pb_spec.commands.test import build_pytest_command, run_test_suite


@pytest.fixture
def runner() -> CliRunner:
    """Create a Click test runner."""
    return CliRunner()


class TestBuildPytestCommand:
    """Tests for the pytest command builder."""

    def test_default_parallel(self) -> None:
        """Default command runs pytest in parallel."""
        cmd = build_pytest_command()
        assert cmd == [sys.executable, "-m", "pytest", "-n", "auto"]

    def test_serial_disables_xdist(self) -> None:
        """--serial drops the -n auto flag."""
        cmd = build_pytest_command(parallel=False)
        assert "-n" not in cmd

    def test_coverage_adds_cov_args(self) -> None:
        """Coverage mode adds pytest-cov args."""
        cmd = build_pytest_command(parallel=False, coverage=True)
        assert "--cov=pb_spec" in cmd
        assert "--cov-report=term-missing" in cmd

    def test_extra_args_passed_through(self) -> None:
        """Extra pytest args are appended."""
        cmd = build_pytest_command(parallel=False, extra_args=("-k", "boundary"))
        assert cmd[-2:] == ["-k", "boundary"]


class TestBuildMutateCommand:
    """Tests for the mutation command builder."""

    def test_basic_command(self) -> None:
        """Base command runs the script via bash."""
        script = Path("/tmp/run-mutation-diff.sh")
        cmd = build_mutate_command(script)
        assert cmd == ["bash", "/tmp/run-mutation-diff.sh"]

    def test_against_and_threshold(self) -> None:
        """--against and --threshold are forwarded."""
        script = Path("/tmp/run-mutation-diff.sh")
        cmd = build_mutate_command(script, against="HEAD", threshold=90)
        assert cmd == [
            "bash",
            "/tmp/run-mutation-diff.sh",
            "--against",
            "HEAD",
            "--threshold",
            "90",
        ]


class TestMutationScriptPath:
    """Tests for script discovery (hermetic — no repo-layout assumptions)."""

    def test_finds_script_via_cwd(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """The script is discovered relative to the current directory."""
        script = tmp_path / "scripts" / "run-mutation-diff.sh"
        script.parent.mkdir()
        script.touch()
        monkeypatch.chdir(tmp_path)
        found = mutation_script_path()
        assert found is not None
        assert found.resolve() == script.resolve()

    def test_finds_script_via_package_root(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The script is discovered relative to the package root."""
        pkg_root = tmp_path / "src" / "pb_spec" / "commands"
        pkg_root.mkdir(parents=True)
        script = tmp_path / "scripts" / "run-mutation-diff.sh"
        script.parent.mkdir()
        script.touch()
        # chdir somewhere without a scripts/ dir so the cwd candidate is missed
        other = tmp_path / "cwd"
        other.mkdir()
        monkeypatch.chdir(other)
        monkeypatch.setattr(
            "pb_spec.commands.mutate.__file__",
            str(pkg_root / "test.py"),
        )
        found = mutation_script_path()
        assert found is not None
        assert found.resolve() == script.resolve()

    def test_returns_none_when_missing(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Returns None when no script exists in either candidate location."""
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(
            "pb_spec.commands.mutate.__file__",
            str(tmp_path / "fake" / "x.py"),
        )
        assert mutation_script_path() is None


class TestCLIRegistration:
    """Tests that the new subcommands are registered."""

    def test_help_shows_new_commands(self, runner: CliRunner) -> None:
        """The help output lists test, mutate, and verify."""
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        for command in ("validate", "test", "mutate", "verify"):
            assert command in result.output

    def test_test_help(self, runner: CliRunner) -> None:
        """test command exposes its options."""
        result = runner.invoke(main, ["test", "--help"])
        assert result.exit_code == 0
        assert "--parallel" in result.output
        assert "--serial" in result.output
        assert "--coverage" in result.output

    def test_mutate_help(self, runner: CliRunner) -> None:
        """mutate command exposes its options."""
        result = runner.invoke(main, ["mutate", "--help"])
        assert result.exit_code == 0
        assert "--against" in result.output
        assert "--threshold" in result.output

    def test_verify_help(self, runner: CliRunner) -> None:
        """verify command exposes its options."""
        result = runner.invoke(main, ["verify", "--help"])
        assert result.exit_code == 0
        assert "--against" in result.output
        assert "--threshold" in result.output


class TestRunTestSuite:
    """Tests for the pytest subprocess runner."""

    def test_run_test_suite_forwards_exit_code(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The subprocess exit code is returned."""
        monkeypatch.setattr(
            "pb_spec.commands.test.subprocess.call",
            lambda _cmd: 7,
        )
        assert run_test_suite(parallel=False) == 7

    def test_parallel_command_built(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Parallel mode forwards the xdist flag and exit code."""
        cmd: list[str] = []
        monkeypatch.setattr(
            "pb_spec.commands.test.subprocess.call",
            lambda c: cmd.append(c) or 0,
        )
        assert run_test_suite(parallel=True) == 0
        assert cmd[0] == [sys.executable, "-m", "pytest", "-n", "auto"]

    def test_serial_command_has_no_xdist(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Serial mode omits the xdist flag."""
        cmd: list[str] = []
        monkeypatch.setattr(
            "pb_spec.commands.test.subprocess.call",
            lambda c: cmd.append(c) or 0,
        )
        run_test_suite(parallel=False)
        assert "-n" not in cmd[0]

    def test_coverage_command_has_cov_flags(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Coverage mode appends the coverage flags."""
        cmd: list[str] = []
        monkeypatch.setattr(
            "pb_spec.commands.test.subprocess.call",
            lambda c: cmd.append(c) or 0,
        )
        run_test_suite(parallel=False, coverage=True)
        assert "--cov=pb_spec" in cmd[0]
        assert "--cov-report=term-missing" in cmd[0]

    def test_extra_args_forwarded(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Extra pytest args are appended to the command."""
        cmd: list[str] = []
        monkeypatch.setattr(
            "pb_spec.commands.test.subprocess.call",
            lambda c: cmd.append(c) or 0,
        )
        run_test_suite(parallel=False, extra_args=("-k", "boundary"))
        assert cmd[0][-2:] == ["-k", "boundary"]

    def test_defaults_to_parallel(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Calling run_test_suite with no args uses the parallel default."""
        cmd: list[str] = []
        monkeypatch.setattr(
            "pb_spec.commands.test.subprocess.call",
            lambda c: cmd.append(c) or 0,
        )
        run_test_suite()
        assert "-n" in cmd[0]


class TestTestCommand:
    """Tests for the test command execution paths."""

    def test_green_suite_exits_zero(
        self, runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A passing suite exits 0."""
        monkeypatch.setattr("pb_spec.commands.test.run_test_suite", lambda **_: 0)
        result = runner.invoke(main, ["test", "--serial"])
        assert result.exit_code == 0
        assert "passed" in result.output.lower()

    def test_failing_suite_exits_nonzero(
        self, runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A failing suite propagates its exit code."""
        monkeypatch.setattr("pb_spec.commands.test.run_test_suite", lambda **_: 3)
        result = runner.invoke(main, ["test", "--serial"])
        assert result.exit_code == 3
        assert "failed" in result.output.lower()


class TestMutateCommand:
    """Tests for the mutate command execution paths."""

    @staticmethod
    def _patch_script(monkeypatch: pytest.MonkeyPatch) -> None:
        """Point script discovery at a hermetic path (mutmut sandbox has no scripts/)."""
        monkeypatch.setattr(
            "pb_spec.commands.mutate.mutation_script_path",
            lambda: Path("/tmp/run-mutation-diff.sh"),
        )

    def test_pass_exits_zero(self, runner: CliRunner, monkeypatch: pytest.MonkeyPatch) -> None:
        """Mutation score above threshold exits 0."""
        self._patch_script(monkeypatch)
        monkeypatch.setattr("pb_spec.commands.mutate.subprocess.call", lambda _cmd: 0)
        result = runner.invoke(main, ["mutate"])
        assert result.exit_code == 0

    def test_no_changed_files_exits_zero(
        self, runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Exit code 2 (nothing to mutate) is treated as success."""
        self._patch_script(monkeypatch)
        monkeypatch.setattr("pb_spec.commands.mutate.subprocess.call", lambda _cmd: 2)
        result = runner.invoke(main, ["mutate"])
        assert result.exit_code == 0

    def test_survivors_exit_nonzero(
        self, runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Surviving mutants (exit 1) fail the command."""
        self._patch_script(monkeypatch)
        monkeypatch.setattr("pb_spec.commands.mutate.subprocess.call", lambda _cmd: 1)
        result = runner.invoke(main, ["mutate"])
        assert result.exit_code == 1

    def test_script_missing_exits_nonzero(
        self, runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A missing mutation script fails the command."""
        monkeypatch.setattr("pb_spec.commands.mutate.mutation_script_path", lambda: None)
        result = runner.invoke(main, ["mutate"])
        assert result.exit_code == 1


class TestVerifyCommand:
    """Tests for the verify command execution paths."""

    @staticmethod
    def _patch_script(monkeypatch: pytest.MonkeyPatch) -> None:
        """Point script discovery at a hermetic path (mutmut sandbox has no scripts/)."""
        monkeypatch.setattr(
            "pb_spec.commands.verify.mutation_script_path",
            lambda: Path("/tmp/run-mutation-diff.sh"),
        )

    def test_all_green_exits_zero(self, runner: CliRunner, monkeypatch: pytest.MonkeyPatch) -> None:
        """Tests pass and mutation gate passes -> exit 0."""
        self._patch_script(monkeypatch)
        monkeypatch.setattr(
            "pb_spec.commands.verify.subprocess.call",
            lambda cmd: 0 if cmd[:1] else 0,
        )
        result = runner.invoke(main, ["verify"])
        assert result.exit_code == 0

    def test_test_failure_stops(self, runner: CliRunner, monkeypatch: pytest.MonkeyPatch) -> None:
        """A failing test suite aborts before mutation runs."""
        self._patch_script(monkeypatch)
        calls: list[list[str]] = []
        monkeypatch.setattr(
            "pb_spec.commands.verify.subprocess.call",
            lambda cmd: calls.append(cmd) or 1,
        )
        result = runner.invoke(main, ["verify"])
        assert result.exit_code == 1
        assert len(calls) == 1  # mutation never ran

    def test_mutation_failure_fails(
        self, runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Tests green but mutation gate fails -> exit non-zero."""
        self._patch_script(monkeypatch)
        monkeypatch.setattr(
            "pb_spec.commands.verify.subprocess.call",
            lambda cmd: 0 if "-m" in cmd[1:3] else 1,
        )
        result = runner.invoke(main, ["verify"])
        assert result.exit_code == 1

    def test_no_changed_files_passes(
        self, runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Mutation exit 2 (nothing changed) is treated as success."""
        self._patch_script(monkeypatch)
        monkeypatch.setattr(
            "pb_spec.commands.verify.subprocess.call",
            lambda cmd: 0 if "-m" in cmd[1:3] else 2,
        )
        result = runner.invoke(main, ["verify"])
        assert result.exit_code == 0

    def test_script_missing_fails(self, runner: CliRunner, monkeypatch: pytest.MonkeyPatch) -> None:
        """A missing mutation script fails verify after green tests."""
        monkeypatch.setattr("pb_spec.commands.verify.subprocess.call", lambda cmd: 0)
        monkeypatch.setattr("pb_spec.commands.verify.mutation_script_path", lambda: None)
        result = runner.invoke(main, ["verify"])
        assert result.exit_code == 1
