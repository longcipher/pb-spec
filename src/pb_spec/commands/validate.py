"""Validate command for pb-spec with --plan, --build, and --task modes."""

from __future__ import annotations

import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

import click

from pb_spec.validation import CodeScanner, IssueType


def get_timeout_config() -> dict[str, int]:
    """Get timeout configuration from environment variables with defaults."""
    return {
        "git_ls_files": int(os.getenv("PB_SPEC_GIT_TIMEOUT", "60")),
        "rumdl_check": int(os.getenv("PB_SPEC_RUMDL_CHECK_TIMEOUT", "10")),
        "rumdl_format": int(os.getenv("PB_SPEC_RUMDL_FORMAT_TIMEOUT", "30")),
    }


@dataclass
class ValidationResult:
    """Structured result of a validation operation."""

    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class TaskBlock:
    """Represents a parsed task block from tasks.md."""

    id: str
    name: str
    content: str
    fields: dict[str, str]


class MarkdownParser:
    """Simple markdown parser for extracting task blocks."""

    def parse_task_blocks(self, content: str) -> list[TaskBlock]:
        """Parse markdown content and extract task blocks."""
        lines = content.split("\n")
        task_blocks = []
        current_task: TaskBlock | None = None
        current_field = ""
        current_field_content = []

        for line in lines:
            # Check for task heading
            task_match = re.match(r"^(#{2,3})\s+Task\s+(\d+\.\d+):\s*(.*)$", line)
            if task_match:
                # Save previous task if exists
                if current_task:
                    current_task.fields[current_field] = "\n".join(current_field_content).strip()
                    task_blocks.append(current_task)

                # Start new task
                level, task_id, task_name = task_match.groups()
                current_task = TaskBlock(id=task_id, name=task_name.strip(), content="", fields={})
                current_field = ""
                current_field_content = []
                current_task.content = line + "\n"  # Start accumulating content
                continue

            if current_task is None:
                continue

            # Accumulate content for the task block
            current_task.content += line + "\n"

            if current_task is None:
                continue

            # Check for field headers (may be indented)
            field_match = re.match(r"^\s*(\w+(?:\s+\w+)*):\s*(.*)", line)
            if field_match:
                # Save previous field
                if current_field:
                    current_task.fields[current_field] = "\n".join(current_field_content).strip()

                # Start new field
                field_name = field_match.group(1) + ":"
                field_value = field_match.group(2).strip()
                current_field = field_name
                current_task.fields[current_field] = field_value
                current_field_content = [field_value] if field_value else []
            elif current_field and line.strip():  # Additional content lines for current field
                current_field_content.append(line)
                current_task.fields[current_field] = "\n".join(current_field_content).strip()

        # Save last task
        if current_task and current_field:
            current_task.fields[current_field] = "\n".join(current_field_content).strip()
            task_blocks.append(current_task)

        return task_blocks


def combine_validation_results(*results: ValidationResult) -> ValidationResult:
    """Combine multiple ValidationResult objects."""
    combined_errors = []
    combined_warnings = []
    is_valid = True

    for result in results:
        combined_errors.extend(result.errors)
        combined_warnings.extend(result.warnings)
        is_valid &= result.is_valid

    return ValidationResult(is_valid=is_valid, errors=combined_errors, warnings=combined_warnings)


class ValidationError(Exception):
    """Base exception for validation errors."""

    pass


class SpecNotFoundError(ValidationError):
    """Raised when spec directory is not found."""

    pass


class FileReadError(ValidationError):
    """Raised when spec files cannot be read."""

    pass


class ContractViolationError(ValidationError):
    """Raised when markdown contract is violated."""

    pass


def get_git_modified_files(root_dir: Path | str = ".") -> set[Path]:
    """Get files with staged, unstaged, or untracked changes.

    Uses `git status --porcelain` which works even on initial commits
    (no HEAD yet) and covers all change categories in a single command.
    Falls back to an empty set if not in a git repository.
    """
    root = Path(root_dir)
    files: set[Path] = set()

    try:
        timeouts = get_timeout_config()
        result = subprocess.run(
            ["git", "-c", "core.quotePath=false", "status", "--porcelain", "-uall"],
            capture_output=True,
            text=True,
            cwd=root,
            encoding="utf-8",
            timeout=timeouts["git_ls_files"],
        )
        for line in result.stdout.splitlines():
            if len(line) < 4:
                continue
            # git status --porcelain output: XY <path> or XY <path> -> <new_path>
            # XY are the staged (col 1) and unstaged (col 2) status codes
            path_str = line[3:].strip()
            # Handle renamed files: "R  old -> new"
            if " -> " in path_str:
                path_str = path_str.split(" -> ", 1)[1].strip()
            # Strip surrounding quotes (git adds them for special-char paths)
            if path_str.startswith('"') and path_str.endswith('"'):
                path_str = path_str[1:-1]
            files.add(root / path_str)
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        pass

    return files


class Colors:
    """ANSI color codes for terminal output."""

    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"


def print_success(msg: str) -> None:
    """Print a success message."""
    click.echo(f"{Colors.GREEN}✅ {msg}{Colors.RESET}")


def print_error(msg: str) -> None:
    """Print an error message."""
    click.echo(f"{Colors.RED}❌ {msg}{Colors.RESET}")


def print_warning(msg: str) -> None:
    """Print a warning message."""
    click.echo(f"{Colors.YELLOW}⚠️  {msg}{Colors.RESET}")


def print_info(msg: str) -> None:
    """Print an info message."""
    click.echo(f"{Colors.BLUE}ℹ️  {msg}{Colors.RESET}")


def get_latest_spec_dir(specs_dir: Path | None = None) -> Path:
    """Get the latest feature spec directory from specs/."""
    if specs_dir is None:
        specs_dir = Path("specs")

    if not specs_dir.exists() or not specs_dir.is_dir():
        raise SpecNotFoundError("Directory 'specs/' not found. Run /pb-plan first.")

    spec_dirs = [d for d in specs_dir.iterdir() if d.is_dir()]
    if not spec_dirs:
        raise SpecNotFoundError("No feature specs found in 'specs/'.")

    # Sort by name (relies on YYYY-MM-DD prefix)
    return sorted(spec_dirs, key=lambda x: x.name)[-1]


def is_rumdl_available() -> bool:
    """Check if rumdl is available and working."""
    try:
        timeouts = get_timeout_config()
        subprocess.run(
            ["rumdl", "--version"], capture_output=True, check=True, timeout=timeouts["rumdl_check"]
        )
        return True
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return False


def read_file_content(file_path: Path) -> str:
    """Safely read file content with error handling."""
    try:
        return file_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        raise FileReadError(f"Cannot read file {file_path}: {e}") from e


def validate_required_files_exist(spec_dir: Path) -> ValidationResult:
    """Check that required files exist."""
    errors = []
    design_file = spec_dir / "design.md"
    tasks_file = spec_dir / "tasks.md"

    for f in [design_file, tasks_file]:
        if not f.exists():
            errors.append(f"Missing required file: {f.relative_to(spec_dir.parent)}")

    return ValidationResult(is_valid=len(errors) == 0, errors=errors)


def detect_design_mode(content: str) -> tuple[bool, list[str]]:
    """Detect design.md mode and return required sections."""
    is_full_mode = "Executive Summary" in content or "Requirements & Goals" in content

    if is_full_mode:
        required_sections = [
            "Executive Summary",
            "Requirements & Goals",
            "Architecture Overview",
            "Detailed Design",
            "Verification & Testing Strategy",
            "Implementation Plan",
        ]
    else:
        # Lightweight mode (per contract §6.4)
        required_sections = [
            "Architecture Decisions",
            "BDD/TDD Strategy",
            "Verification",
        ]

    return is_full_mode, required_sections


def validate_design_structure(spec_dir: Path) -> ValidationResult:
    """Validate design.md required sections."""
    errors = []
    warnings = []
    design_file = spec_dir / "design.md"
    if not design_file.exists():
        errors.append("design.md file does not exist")
        return ValidationResult(is_valid=False, errors=errors)

    try:
        content = read_file_content(design_file)
    except FileReadError as e:
        errors.append(str(e))
        return ValidationResult(is_valid=False, errors=errors)

    is_full_mode, required_sections = detect_design_mode(content)

    for sec in required_sections:
        if sec not in content:
            errors.append(f"design.md is missing required section: '{sec}'")

    if not errors:
        mode_name = "full" if is_full_mode else "lightweight"
        warnings.append(f"design.md ({mode_name} mode) structural checks passed.")

    return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings)


def validate_tasks_structure(spec_dir: Path) -> ValidationResult:
    """Validate tasks.md structure and required fields."""
    errors = []
    warnings = []
    tasks_file = spec_dir / "tasks.md"
    if not tasks_file.exists():
        errors.append("tasks.md file does not exist")
        return ValidationResult(is_valid=False, errors=errors)

    try:
        content = read_file_content(tasks_file)
    except FileReadError as e:
        errors.append(str(e))
        return ValidationResult(is_valid=False, errors=errors)

    # Parse task blocks using proper markdown parser
    parser = MarkdownParser()
    task_blocks = parser.parse_task_blocks(content)

    if not task_blocks:
        errors.append(
            "tasks.md does not contain any valid '## Task X.Y:' or '### Task X.Y:' definitions."
        )
        return ValidationResult(is_valid=False, errors=errors)

    # Check for status fields globally
    if "Status:" not in content:
        errors.append("tasks.md tasks are missing 'Status:' fields.")

    required_task_fields = [
        "Context:",
        "Verification:",
        "Scenario Coverage:",
        "Loop Type:",
        "Behavioral Contract:",
        "Simplification Focus:",
        "BDD Verification:",
        "Advanced Test Verification:",
        "Runtime Verification:",
    ]

    for task_block in task_blocks:
        task_display_name = (
            f"{task_block.id}: {task_block.name}" if task_block.name else task_block.id
        )

        for required_field in required_task_fields:
            if required_field not in task_block.fields:
                errors.append(
                    f"Task '{task_display_name}' is missing required field: '{required_field}'"
                )
            elif not task_block.fields[required_field].strip():
                errors.append(
                    f"Task '{task_display_name}' has empty required field: '{required_field}'"
                )

    if not errors:
        warnings.append("tasks.md structural checks passed.")

    return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings)


def validate_features_directory(spec_dir: Path) -> ValidationResult:
    """Validate features directory has feature files."""
    warnings = []
    features_dir = spec_dir / "features"
    has_features = features_dir.exists() and list(features_dir.glob("*.feature"))

    if not has_features:
        warnings.append("No .feature files found. (OK if this is a TDD-only lightweight spec)")
    else:
        warnings.append("Found Gherkin .feature files.")

    return ValidationResult(is_valid=True, warnings=warnings)  # This is not a hard failure


def run_rumdl_format(spec_dir: Path) -> None:
    """Format markdown files using rumdl.

    rumdl is an optional external formatter. If it is not installed, this
    step is skipped with a warning rather than failing the pipeline, since
    markdown formatting is not a structural contract requirement.
    """
    md_files = list(spec_dir.rglob("*.md"))
    if not md_files:
        return

    print_info(f"Formatting markdown files using 'rumdl' in {spec_dir}...")

    if not is_rumdl_available():
        print_warning(
            "Command 'rumdl' not found — skipping markdown auto-format. "
            "Install it with: cargo install rumdl  (or: pip install rumdl) "
            "to enable automatic markdown formatting."
        )
        return

    for md_file in md_files:
        try:
            timeouts = get_timeout_config()
            subprocess.run(
                ["rumdl", "fmt", str(md_file)],
                capture_output=True,
                text=True,
                timeout=timeouts["rumdl_format"],
                check=True,
            )
            print_success(f"Formatted: {md_file.name}")
        except subprocess.TimeoutExpired:
            print_warning(f"rumdl timed out on {md_file.name}")
        except subprocess.CalledProcessError as e:
            print_warning(f"rumdl failed on {md_file.name}: {e.stderr.strip()}")
        except Exception as e:
            print_warning(f"Unexpected error formatting {md_file.name}: {e}")


def validate_plan(spec_dir: Path) -> ValidationResult:
    """Validate pb-plan generated documents."""
    print_info(f"Running Post-Plan Validation on: {spec_dir}")

    results = [
        validate_required_files_exist(spec_dir),
        validate_design_structure(spec_dir),
        validate_tasks_structure(spec_dir),
        validate_features_directory(spec_dir),
    ]

    combined = combine_validation_results(*results)

    # Print results for backward compatibility
    for error in combined.errors:
        print_error(error)
    for warning in combined.warnings:
        if "structural checks passed" in warning:
            print_success(warning)
        else:
            print_warning(warning)

    return combined


def validate_build(spec_dir: Path) -> ValidationResult:
    """Validate pb-build task completion (Orchestrator level)."""
    print_info(f"Running Post-Build Validation on: {spec_dir}")
    errors = []
    warnings = []
    infos = []

    tasks_file = spec_dir / "tasks.md"
    if not tasks_file.exists():
        errors.append(f"Missing {tasks_file}")
        return ValidationResult(is_valid=False, errors=errors)

    try:
        content = read_file_content(tasks_file)
    except FileReadError as e:
        errors.append(str(e))
        return ValidationResult(is_valid=False, errors=errors)

    # Parse task blocks using proper markdown parser
    parser = MarkdownParser()
    task_blocks = parser.parse_task_blocks(content)

    for task_block in task_blocks:
        task_display_name = (
            f"{task_block.id}: {task_block.name}" if task_block.name else task_block.id
        )

        # Check task status
        status_field = task_block.fields.get("Status:", "")
        if "🟢 DONE" not in status_field:
            if "⏭️ SKIPPED" in status_field:
                warnings.append(
                    f"Task Skipped: {task_display_name}. (Ignored in strict completion check)"
                )
            elif "⛔ OBSOLETE" in status_field:
                infos.append(
                    f"Task Obsolete: {task_display_name}. (Ignored in strict completion check)"
                )
            elif "🔴 TODO" in status_field or "🟡 IN PROGRESS" in status_field:
                errors.append(f"Task Unfinished: {task_display_name} is not marked as DONE.")
            elif "🔄 DCR" in status_field:
                errors.append(f"Task Blocked by DCR: {task_display_name}. Needs design refinement.")
            else:
                errors.append(f"Task Invalid Status: {task_display_name}. Missing 🟢 DONE.")
            continue

        # Check for unchecked steps
        unchecked = re.findall(r"^[ \t]*- \[ \].*", task_block.content, re.MULTILINE)
        if unchecked:
            errors.append(
                f"Task '{task_display_name}' is marked DONE but has incomplete steps:\n  "
                + "\n  ".join(unchecked)
            )

        # Check that at least one step checkbox exists (prevents LLM from deleting all steps)
        all_checkboxes = re.findall(r"^[ \t]*- \[[ xX]\].*", task_block.content, re.MULTILINE)
        if not all_checkboxes:
            errors.append(
                f"Task '{task_display_name}' is marked DONE but contains no step checkboxes. "
                "Contract requires at least one step."
            )

    if not errors:
        infos.append("All targeted tasks in tasks.md are properly marked as DONE.")

    # Deep codebase scan for mocks, TODOs, and skipped tests
    scan_result = scan_codebase(mode="build")
    if not scan_result:
        errors.append("Codebase scan failed - found issues that need to be addressed.")

    # Print results for backward compatibility
    for error in errors:
        print_error(error)
    for warning in warnings:
        print_warning(warning)
    for info in infos:
        if "properly marked as DONE" in info:
            print_success(info)
        else:
            print_info(info)

    return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings)


def validate_task() -> bool:
    """Subagent self-check before signaling READY_FOR_EVAL."""
    print_info("Running Subagent Task Self-Check (Pre-Eval Validation)...")
    passed = scan_codebase(mode="task")

    if passed:
        print_success(
            "Subagent self-check passed! Code is clean of mocks, skipped tests, and debug artifacts."
        )
        print_info("You may now signal READY_FOR_EVAL.")
    else:
        print_error(
            "Subagent self-check failed! Please fix the dirty code, TODOs, or skipped tests before signaling READY_FOR_EVAL."
        )

    return passed


def scan_codebase(mode: str) -> bool:
    """Scan codebase for issues.

    Args:
        mode: "build" for full scan, "task" for subagent self-check.
            In task mode, scanning is scoped to git-modified files only
            to prevent subagents from chasing historical tech debt.
    """
    print_info(f"Scanning codebase for code quality issues (mode={mode})...")

    target_files: set[Path] | None = None
    if mode == "task":
        target_files = get_git_modified_files()
        if target_files:
            print_info(f"Task mode: scanning only {len(target_files)} git-modified file(s).")
        else:
            print_info("Task mode: no git modifications detected; scanning all tracked files.")

    scanner = CodeScanner(
        root_dir=".",
        check_skipped_tests=True,
        check_not_implemented=True,
        check_todos=True,
        check_debug_artifacts=True,
        target_files=target_files,
    )

    result = scanner.scan()

    if not result.has_issues:
        print_success("Codebase scan passed - no issues found.")
        return True

    # Report issues by type
    passed = True

    skipped_tests = result.issues_by_type(IssueType.SKIPPED_TEST)
    if skipped_tests:
        print_error(f"Found {len(skipped_tests)} skipped test(s):")
        for issue in skipped_tests[:10]:  # Limit output
            click.echo(f"  {issue.file_path}:{issue.line_number} -> {issue.line_content}")
        if len(skipped_tests) > 10:
            click.echo(f"  ... and {len(skipped_tests) - 10} more")
        passed = False

    not_implemented = result.issues_by_type(IssueType.NOT_IMPLEMENTED)
    if not_implemented:
        print_error(f"Found {len(not_implemented)} not-implemented/mock issue(s):")
        for issue in not_implemented[:10]:
            click.echo(f"  {issue.file_path}:{issue.line_number} -> {issue.line_content}")
        if len(not_implemented) > 10:
            click.echo(f"  ... and {len(not_implemented) - 10} more")
        passed = False

    todos = result.issues_by_type(IssueType.TODO)
    if todos:
        print_error(f"Found {len(todos)} TODO/FIXME(s):")
        for issue in todos[:10]:
            click.echo(f"  {issue.file_path}:{issue.line_number} -> {issue.line_content}")
        if len(todos) > 10:
            click.echo(f"  ... and {len(todos) - 10} more")
        passed = False

    debug_artifacts = result.issues_by_type(IssueType.DEBUG_ARTIFACT)
    if debug_artifacts:
        print_error(f"Found {len(debug_artifacts)} debug artifact(s):")
        for issue in debug_artifacts[:10]:
            click.echo(f"  {issue.file_path}:{issue.line_number} -> {issue.line_content}")
        if len(debug_artifacts) > 10:
            click.echo(f"  ... and {len(debug_artifacts) - 10} more")
        passed = False

    return passed


@click.command("validate")
@click.option(
    "--plan",
    "mode",
    flag_value="plan",
    help="Validate and format specs after /pb-plan.",
)
@click.option(
    "--build",
    "mode",
    flag_value="build",
    help="Validate strict completion after /pb-build.",
)
@click.option(
    "--task",
    "mode",
    flag_value="task",
    help="Subagent self-check before signaling READY_FOR_EVAL.",
)
@click.option(
    "--specs-dir",
    type=click.Path(path_type=Path),
    default=None,
    help="Path to specs directory (default: specs/).",
)
def validate_cmd(mode: str | None, specs_dir: Path | None) -> None:
    """Validate pb-spec workflow artifacts at different stages.

    Use --plan after /pb-plan to check spec structure.
    Use --build after /pb-build to verify task completion.
    Use --task for subagent self-check before signaling READY_FOR_EVAL.
    """
    if mode is None:
        click.echo("Error: Must specify one of --plan, --build, or --task")
        click.echo("Run 'pb-spec validate --help' for usage information.")
        sys.exit(1)

    all_passed = True

    if mode in ("plan", "build"):
        try:
            latest_spec = get_latest_spec_dir(specs_dir)
        except SpecNotFoundError as e:
            print_error(str(e))
            sys.exit(1)

        if mode == "plan":
            run_rumdl_format(latest_spec)
            result = validate_plan(latest_spec)
            all_passed = result.is_valid

        if mode == "build":
            result = validate_build(latest_spec)
            all_passed = result.is_valid

    if mode == "task":
        all_passed = validate_task()

    if not all_passed:
        click.echo(
            f"\n{Colors.RED}❌ Validation Failed. Please fix the above issues.{Colors.RESET}"
        )
        sys.exit(1)
    else:
        click.echo(f"\n{Colors.GREEN}🎉 All validations passed successfully!{Colors.RESET}")
        sys.exit(0)
