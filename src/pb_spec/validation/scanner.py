"""Code scanner for detecting TODOs, skipped tests, debug artifacts, and mocks."""

from __future__ import annotations

import os
import re
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
    re.compile(r"xit\("),  # xit() in Mocha/Jest
    re.compile(r"xtest\("),  # xtest() in Jest
    re.compile(r"xit\s"),  # xit with space
    re.compile(r"xtest\s"),  # xtest with space
    re.compile(r"test\.skip"),  # test.skip in Jest
    re.compile(r"it\.skip"),  # it.skip in Jest
    re.compile(r"describe\.skip"),  # describe.skip in Jest
    re.compile(r"#\[ignore\]"),  # Rust #[ignore]
    re.compile(r"@Ignore"),  # Java/Kotlin @Ignore
    re.compile(r"t\.Skip\(\)"),  # Go t.Skip()
]

# Patterns for NotImplementedError / NotImplemented
NOT_IMPLEMENTED_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"NotImplementedError"),
    re.compile(r"raise NotImplemented\b"),  # Not "NotImplementedError"
    re.compile(r"raise NotImplemented\s"),
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
    ) -> None:
        self.root_dir = Path(root_dir)
        self.exclude_dirs = exclude_dirs or EXCLUDE_DIRS
        self.scan_extensions = scan_extensions or SCAN_EXTENSIONS
        self.check_skipped_tests = check_skipped_tests
        self.check_not_implemented = check_not_implemented
        self.check_todos = check_todos
        self.check_debug_artifacts = check_debug_artifacts

    def scan(self) -> ScanResult:
        """Scan the codebase and return results."""
        result = ScanResult()

        # Files to exclude from scanning (validation infrastructure)
        exclude_files = {"scanner.py", "validate.py"}

        for root, dirs, files in os.walk(self.root_dir):
            # Filter out excluded directories
            dirs[:] = [d for d in dirs if d not in self.exclude_dirs and not d.startswith(".")]

            for filename in files:
                file_path = Path(root) / filename

                # Skip files that don't match our extensions
                if file_path.suffix not in self.scan_extensions:
                    continue

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
        try:
            content = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return

        lines = content.split("\n")
        rel_path = str(file_path.relative_to(self.root_dir))

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
