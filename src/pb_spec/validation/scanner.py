"""Code scanner for detecting TODOs, skipped tests, debug artifacts, and mocks."""

from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class IssueType(Enum):
    """Types of code issues that can be detected."""

    SKIPPED_TEST = "skipped_test"
    NOT_IMPLEMENTED = "not_implemented"
    TODO = "todo"
    DEBUG_ARTIFACT = "debug_artifact"


@dataclass(frozen=True)
class ScanIssue:
    """A single issue found during code scanning."""

    issue_type: IssueType
    file_path: str
    line_number: int
    line_content: str
    message: str


@dataclass
class ScanResult:
    """Result of a code scan."""

    issues: list[ScanIssue] = field(default_factory=list)

    @property
    def has_issues(self) -> bool:
        """Return True if any issues were found."""
        return len(self.issues) > 0

    def issues_by_type(self, issue_type: IssueType) -> list[ScanIssue]:
        """Return issues filtered by type."""
        return [i for i in self.issues if i.issue_type == issue_type]


# Directories to exclude from scanning
EXCLUDE_DIRS: frozenset[str] = frozenset(
    {
        ".git",
        "node_modules",
        ".venv",
        "venv",
        "__pycache__",
        "dist",
        "build",
        ".pytest_cache",
        "target",
        ".tox",
        ".mypy_cache",
        ".ruff_cache",
    }
)

# File extensions to scan
SCAN_EXTENSIONS: frozenset[str] = frozenset(
    {
        ".py",
        ".ts",
        ".tsx",
        ".js",
        ".jsx",
        ".rs",
        ".go",
        ".java",
        ".rb",
        ".cs",
        ".cpp",
        ".c",
        ".h",
    }
)

# Patterns for skipped tests
SKIP_TEST_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"@pytest\.mark\.skip"),
    re.compile(r"@unittest\.skip"),
    re.compile(r"@pytest\.mark\.skipif"),
    re.compile(r"\.skip\("),  # it.skip(), test.skip(), describe.skip()
    re.compile(r"\bxit\("),  # xit() in Mocha/Jest
    re.compile(r"\bxtest\("),  # xtest() in Jest
    re.compile(r"\bxit\b"),  # xit as standalone word
    re.compile(r"\bxtest\b"),  # xtest as standalone word
    re.compile(r"test\.skip"),  # test.skip in Jest
    re.compile(r"it\.skip"),  # it.skip in Jest
    re.compile(r"describe\.skip"),  # describe.skip in Jest
    re.compile(r"#\[ignore\]"),  # Rust #[ignore]
    re.compile(r"@Ignore"),  # Java/Kotlin @Ignore
    re.compile(r"t\.Skip\(\)"),  # Go t.Skip()
]

# Patterns for NotImplementedError / NotImplemented
# Only match *raising* NotImplementedError — not catching it or using pytest.raises()
# which are legitimate exception handling and test code patterns.
# Bare `NotImplemented` is a valid Python singleton used in __eq__, __add__ etc.
NOT_IMPLEMENTED_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"raise NotImplementedError\b"),
    re.compile(r"unimplemented!"),  # Rust
    re.compile(r"todo!"),  # Rust todo! macro
]

# Patterns for TODO/FIXMO
TODO_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"TODO:", re.IGNORECASE),
    re.compile(r"FIXME:", re.IGNORECASE),
    re.compile(r"//\s*TODO", re.IGNORECASE),
    re.compile(r"//\s*FIXME", re.IGNORECASE),
    re.compile(r"<!--\s*TODO", re.IGNORECASE),
    re.compile(r"<!--\s*FIXME", re.IGNORECASE),
    re.compile(r"#\s*TODO", re.IGNORECASE),
    re.compile(r"#\s*FIXME", re.IGNORECASE),
]

# Patterns for debug artifacts
DEBUG_ARTIFACT_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"console\.log\("),
    re.compile(r"console\.debug\("),
    re.compile(r"debugger;"),
    re.compile(r"pdb\.set_trace\(\)"),
    re.compile(r"breakpoint\(\)"),
    re.compile(r"import pdb"),
    re.compile(r"from pdb import"),
    re.compile(r"import ipdb"),
    re.compile(r"binding\.pry"),  # Ruby
    re.compile(r"byebug"),  # Ruby
    re.compile(r"import debugpy"),
]


class CodeScanner:
    """Scans codebase for code quality issues."""

    def __init__(
        self,
        root_dir: Path | str = ".",
        exclude_dirs: frozenset[str] | None = None,
        scan_extensions: frozenset[str] | None = None,
        check_skipped_tests: bool = True,
        check_not_implemented: bool = True,
        check_todos: bool = True,
        check_debug_artifacts: bool = True,
        target_files: set[Path] | None = None,
    ) -> None:
        self.root_dir = Path(root_dir)
        self.exclude_dirs = exclude_dirs or EXCLUDE_DIRS
        self.scan_extensions = scan_extensions or SCAN_EXTENSIONS
        self.check_skipped_tests = check_skipped_tests
        self.check_not_implemented = check_not_implemented
        self.check_todos = check_todos
        self.check_debug_artifacts = check_debug_artifacts
        # When set, scan only these files (used by --task mode to scope to git-modified files)
        self.target_files = target_files

    def _get_git_files(self) -> list[Path] | None:
        """Get files managed by git, respecting .gitignore exclusions.

        Uses `git ls-files --cached --others --exclude-standard` to list both
        tracked and untracked-but-not-ignored files. This avoids scanning
        vendor directories, build outputs, and other .gitignored paths
        without requiring a hardcoded EXCLUDE_DIRS list.

        Returns:
            list of Paths if git is available (may be empty when no code files match).
            None if git is unavailable or the directory is not a git repo.
        """
        try:
            result = subprocess.run(
                ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
                capture_output=True,
                text=True,
                check=True,
                cwd=self.root_dir,
            )
            files = []
            for line in result.stdout.splitlines():
                line = line.strip()
                if not line:
                    continue
                file_path = self.root_dir / line
                if file_path.suffix in self.scan_extensions:
                    files.append(file_path)
            return files
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Not a git repo or git not installed — fall back to os.walk
            return None

    def _get_files_fallback(self) -> list[Path]:
        """Fall back to os.walk when git is unavailable."""
        # Files to exclude from scanning (validation infrastructure)
        exclude_files = {"scanner.py", "validate.py"}
        files = []
        for root, dirs, filenames in os.walk(self.root_dir):
            dirs[:] = [d for d in dirs if d not in self.exclude_dirs and not d.startswith(".")]
            for filename in filenames:
                file_path = Path(root) / filename
                if file_path.suffix not in self.scan_extensions:
                    continue
                if file_path.name == "pb-spec":
                    continue
                if file_path.name in exclude_files:
                    continue
                if "specs/" in str(file_path):
                    continue
                files.append(file_path)
        return files

    def _get_files_to_scan(self) -> list[Path]:
        """Determine which files to scan.

        Priority:
        1. target_files (explicit set for --task mode scoping)
        2. git ls-files (respects .gitignore)
        3. os.walk fallback (legacy behavior)

        Note: git_files being None means git is unavailable (fall back).
        git_files being an empty list means git works but found no matching code files.
        """
        if self.target_files is not None:
            return [f for f in self.target_files if f.suffix in self.scan_extensions]

        git_files = self._get_git_files()
        if git_files is not None:
            return git_files
        return self._get_files_fallback()

    def scan(self) -> ScanResult:
        """Scan the codebase and return results."""
        result = ScanResult()

        # Files to exclude from scanning (validation infrastructure)
        exclude_files = {"scanner.py", "validate.py"}

        for file_path in self._get_files_to_scan():
            # Skip the pb-spec script itself
            if file_path.name == "pb-spec":
                continue

            # Skip validation infrastructure files
            if file_path.name in exclude_files:
                continue

            # Skip files in specs directory (markdown specs, not code)
            if "specs/" in str(file_path):
                continue

            self._scan_file(file_path, result)

        return result

    def _scan_file(self, file_path: Path, result: ScanResult) -> None:
        """Scan a single file for issues."""
        # Skip files that don't exist (e.g., deleted by subagent but still in git diff)
        if not file_path.exists() or not file_path.is_file():
            return

        try:
            content = file_path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            return

        lines = content.split("\n")
        try:
            rel_path = str(file_path.relative_to(self.root_dir))
        except ValueError:
            # file_path is absolute but root_dir is relative (or vice versa)
            rel_path = str(file_path)

        for i, line in enumerate(lines, start=1):
            self._check_line(rel_path, i, line, result)

    def _check_line(self, file_path: str, line_number: int, line: str, result: ScanResult) -> None:
        """Check a single line for all enabled issue types."""
        if self.check_skipped_tests:
            for pattern in SKIP_TEST_PATTERNS:
                if pattern.search(line):
                    result.issues.append(
                        ScanIssue(
                            issue_type=IssueType.SKIPPED_TEST,
                            file_path=file_path,
                            line_number=line_number,
                            line_content=line.strip(),
                            message=f"Skipped test found: {line.strip()}",
                        )
                    )
                    break  # Only report one issue per line

        if self.check_not_implemented:
            for pattern in NOT_IMPLEMENTED_PATTERNS:
                if pattern.search(line):
                    result.issues.append(
                        ScanIssue(
                            issue_type=IssueType.NOT_IMPLEMENTED,
                            file_path=file_path,
                            line_number=line_number,
                            line_content=line.strip(),
                            message=f"NotImplemented/Mock found: {line.strip()}",
                        )
                    )
                    break

        if self.check_todos:
            for pattern in TODO_PATTERNS:
                if pattern.search(line):
                    result.issues.append(
                        ScanIssue(
                            issue_type=IssueType.TODO,
                            file_path=file_path,
                            line_number=line_number,
                            line_content=line.strip(),
                            message=f"TODO/FIXME found: {line.strip()}",
                        )
                    )
                    break

        if self.check_debug_artifacts:
            for pattern in DEBUG_ARTIFACT_PATTERNS:
                if pattern.search(line):
                    result.issues.append(
                        ScanIssue(
                            issue_type=IssueType.DEBUG_ARTIFACT,
                            file_path=file_path,
                            line_number=line_number,
                            line_content=line.strip(),
                            message=f"Debug artifact found: {line.strip()}",
                        )
                    )
                    break
