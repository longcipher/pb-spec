"""Code scanner for detecting TODOs, skipped tests, debug artifacts, and mocks."""

from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from pb_spec.config import GIT_TIMEOUT


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
        return bool(self.issues)


VALIDATION_PACKAGE_DIR: Path = Path(__file__).parent

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

SKIP_TEST_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"@pytest\.mark\.skip"),
    re.compile(r"@unittest\.skip"),
    re.compile(r"@pytest\.mark\.skipif"),
    re.compile(r"\.skip\("),
    re.compile(r"\bxit\("),
    re.compile(r"\bxtest\("),
    re.compile(r"\bxit\b"),
    re.compile(r"\bxtest\b"),
    re.compile(r"test\.skip"),
    re.compile(r"it\.skip"),
    re.compile(r"describe\.skip"),
    re.compile(r"#\[ignore\]"),
    re.compile(r"@Ignore"),
    re.compile(r"t\.Skip\(\)"),
]

NOT_IMPLEMENTED_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"raise NotImplementedError\b"),
    re.compile(r"unimplemented!"),
    re.compile(r"todo!"),
]

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

DEBUG_ARTIFACT_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"console\.log\("),
    re.compile(r"console\.debug\("),
    re.compile(r"debugger;"),
    re.compile(r"pdb\.set_trace\(\)"),
    re.compile(r"breakpoint\(\)"),
    re.compile(r"import pdb"),
    re.compile(r"from pdb import"),
    re.compile(r"import ipdb"),
    re.compile(r"binding\.pry"),
    re.compile(r"byebug"),
    re.compile(r"import debugpy"),
]

_ALL_PATTERNS: list[tuple[IssueType, list[re.Pattern[str]]]] = [
    (IssueType.SKIPPED_TEST, SKIP_TEST_PATTERNS),
    (IssueType.NOT_IMPLEMENTED, NOT_IMPLEMENTED_PATTERNS),
    (IssueType.TODO, TODO_PATTERNS),
    (IssueType.DEBUG_ARTIFACT, DEBUG_ARTIFACT_PATTERNS),
]


class CodeScanner:
    """Scans codebase for code quality issues."""

    def __init__(
        self,
        root_dir: Path | str = ".",
        exclude_dirs: frozenset[str] | None = None,
        scan_extensions: frozenset[str] | None = None,
        target_files: set[Path] | None = None,
    ) -> None:
        self.root_dir = Path(root_dir)
        self.exclude_dirs = exclude_dirs or EXCLUDE_DIRS
        self.scan_extensions = scan_extensions or SCAN_EXTENSIONS
        self.target_files = target_files

    def _get_git_files(self) -> list[Path] | None:
        """Get files managed by git, respecting .gitignore exclusions."""
        try:
            result = subprocess.run(
                ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
                capture_output=True,
                text=True,
                check=True,
                cwd=self.root_dir,
                timeout=GIT_TIMEOUT,
            )
            files = []
            for line in result.stdout.splitlines():
                line = line.strip()
                if not line:
                    continue
                file_path = self.root_dir / line
                if file_path.suffix in self.scan_extensions and self._should_scan_file(file_path):
                    files.append(file_path)
            return files
        except subprocess.CalledProcessError, FileNotFoundError:
            return None

    def _should_scan_file(self, file_path: Path) -> bool:
        """Check whether a file should be scanned."""
        resolved = file_path.resolve()
        if resolved.is_relative_to(VALIDATION_PACKAGE_DIR.resolve()):
            return False
        return not resolved.is_relative_to((self.root_dir / "specs").resolve())

    def _get_files_fallback(self) -> list[Path]:
        """Fall back to os.walk when git is unavailable."""
        files = []
        for root, dirs, filenames in os.walk(self.root_dir):
            dirs[:] = [d for d in dirs if d not in self.exclude_dirs and not d.startswith(".")]
            for filename in filenames:
                file_path = Path(root) / filename
                if file_path.suffix not in self.scan_extensions:
                    continue
                if not self._should_scan_file(file_path):
                    continue
                files.append(file_path)
        return files

    def _get_files_to_scan(self) -> list[Path]:
        """Determine which files to scan."""
        if self.target_files is not None:
            return [f for f in self.target_files if f.suffix in self.scan_extensions and f.exists()]

        git_files = self._get_git_files()
        if git_files is not None:
            return git_files
        return self._get_files_fallback()

    def scan(self) -> ScanResult:
        """Scan the codebase and return results."""
        result = ScanResult()
        for file_path in self._get_files_to_scan():
            self._scan_file(file_path, result)
        return result

    def _scan_file(self, file_path: Path, result: ScanResult) -> None:
        """Scan a single file for issues."""
        if not file_path.exists() or not file_path.is_file():
            return

        try:
            content = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError, OSError:
            return

        lines = content.split("\n")
        try:
            rel_path = str(file_path.relative_to(self.root_dir))
        except ValueError:
            rel_path = str(file_path)

        for i, line in enumerate(lines, start=1):
            self._check_line(rel_path, i, line, result)

    def _check_line(self, file_path: str, line_number: int, line: str, result: ScanResult) -> None:
        """Check a single line for all issue types."""
        for issue_type, patterns in _ALL_PATTERNS:
            for pattern in patterns:
                if pattern.search(line):
                    result.issues.append(
                        ScanIssue(
                            issue_type=issue_type,
                            file_path=file_path,
                            line_number=line_number,
                            line_content=line.strip(),
                            message=f"{issue_type.value.replace('_', ' ').title()} found: {line.strip()}",
                        )
                    )
                    break
