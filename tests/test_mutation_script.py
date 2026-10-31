"""Integration tests for the spec-marked mutation gate script."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "run-mutation-diff.sh"

pytestmark = [
    pytest.mark.skipif(
        not SCRIPT.exists(),
        reason="mutation script is absent in the mutmut sandbox",
    ),
    pytest.mark.skipif(
        os.name != "posix" or shutil.which("bash") is None or shutil.which("git") is None,
        reason="mutation script tests need POSIX bash and git",
    ),
]


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )


def _write_stub(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    path.chmod(0o755)


def _make_repo(tmp_path: Path, *, mutmut_config: bool = True) -> dict[str, str]:
    """Create a git repo with one changed Python file and stub mutation tools."""
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "src" / "pkg").mkdir(parents=True)
    (repo / "src" / "pkg" / "core.py").write_text("def foo():\n    return 1\n", encoding="utf-8")
    if mutmut_config:
        (repo / "pyproject.toml").write_text(
            '[tool.mutmut]\nsource_paths = ["src/pkg/core.py"]\n',
            encoding="utf-8",
        )

    _git(repo, "init")
    branch = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if branch != "main":
        _git(repo, "checkout", "-b", "main")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "init")

    (repo / "src" / "pkg" / "core.py").write_text("def foo():\n    return 2\n", encoding="utf-8")

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    _write_stub(
        bin_dir / "mutmut",
        """#!/usr/bin/env bash
set -e
cmd="${1:-}"
if [[ "$cmd" == "print-time-estimates" ]]; then
  count="${FAKE_MUTANT_COUNT:-1}"
  i=1
  while [[ "$i" -le "$count" ]]; do
    echo "1ms pkg.core.x__foo__mutmut_$i"
    i=$((i + 1))
  done
  exit 0
fi
if [[ "$cmd" == "run" ]]; then
  mkdir -p mutants/src/pkg
  printf '{"exit_code_by_key": {"pkg.core.x__foo__mutmut_1": 1}}' > mutants/src/pkg/core.py.meta
  exit 0
fi
exit 0
""",
    )
    _write_stub(
        bin_dir / "uv",
        """#!/usr/bin/env bash
set -e
if [[ "${1:-}" == "run" ]]; then
  shift
  case "${1:-}" in
    mutmut) shift; exec "$(dirname "$0")/mutmut" "$@" ;;
    python) shift; exec python3 "$@" ;;
  esac
fi
exec "$@"
""",
    )

    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}:{env['PATH']}"
    return {"repo": str(repo), "env_path": env["PATH"]}


def _run(repo: Path, env_path: str, *args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PATH"] = env_path
    return subprocess.run(
        ["bash", str(SCRIPT), *args],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
    )


def _write_tasks(repo: Path, mutation: str | None) -> None:
    spec_dir = repo / "specs" / "2026-10-31-01-test"
    spec_dir.mkdir(parents=True)
    lines = [
        "# Tasks",
        "",
        "### Task 1.1: Test",
        "Context: test.",
        "Verification: test.",
        "Test Coverage: N/A",
    ]
    if mutation is not None:
        lines.append(f"Mutation: {mutation}")
    lines.extend(["Status: 🔴 TODO", "- [ ] Step 1"])
    (spec_dir / "tasks.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


class TestMutationScript:
    """End-to-end behavior of the mutation gate."""

    def test_skips_without_specs(self, tmp_path: Path) -> None:
        """No specs directory means the gate is skipped."""
        data = _make_repo(tmp_path)
        result = _run(Path(data["repo"]), data["env_path"])
        assert result.returncode == 2
        assert "no specs/*/tasks.md" in result.stdout

    def test_skips_without_mutation_marker(self, tmp_path: Path) -> None:
        """Tasks without Mutation: keep mutation disabled."""
        data = _make_repo(tmp_path)
        repo = Path(data["repo"])
        _write_tasks(repo, None)
        result = _run(repo, data["env_path"])
        assert result.returncode == 2
        assert "no task declares 'Mutation:" in result.stdout

    def test_skips_when_targets_do_not_match(self, tmp_path: Path) -> None:
        """A Mutation: target outside the changed files skips the run."""
        data = _make_repo(tmp_path)
        repo = Path(data["repo"])
        _write_tasks(repo, "src/other.py")
        result = _run(repo, data["env_path"])
        assert result.returncode == 2
        assert "do not match" in result.stdout

    def test_skips_when_mutmut_is_not_configured(self, tmp_path: Path) -> None:
        """An installed mutmut without project config must not run."""
        data = _make_repo(tmp_path, mutmut_config=False)
        repo = Path(data["repo"])
        _write_tasks(repo, "src/pkg/core.py")
        result = _run(repo, data["env_path"])
        assert result.returncode == 2
        assert "mutmut is not configured" in result.stdout

    def test_runs_scoped_python_mutants(self, tmp_path: Path) -> None:
        """A matching marker runs only the selected module and passes."""
        data = _make_repo(tmp_path)
        repo = Path(data["repo"])
        _write_tasks(repo, "src/pkg/core.py")
        result = _run(repo, data["env_path"])
        assert result.returncode == 0
        assert "score 100%" in result.stdout

    def test_budget_hard_fails_before_running(self, tmp_path: Path) -> None:
        """Too many mutants exits 3 instead of falling back to a full run."""
        data = _make_repo(tmp_path)
        repo = Path(data["repo"])
        _write_tasks(repo, "src/pkg/core.py")
        env = os.environ.copy()
        env["PATH"] = data["env_path"]
        env["FAKE_MUTANT_COUNT"] = "61"
        result = subprocess.run(
            ["bash", str(SCRIPT)],
            cwd=repo,
            env=env,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 3
        assert "BUDGET EXCEEDED" in result.stdout
        assert not (repo / "mutants").exists()
