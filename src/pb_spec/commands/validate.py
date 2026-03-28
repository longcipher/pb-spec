"""Validate command for pb-spec with --plan, --build, and --task modes."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import click

from pb_spec.validation import CodeScanner, IssueType


def get_git_modified_files(root_dir: Path | str = ".") -> set[Path]:
    """Get files with staged, unstaged, or untracked changes.

    Uses `git status --porcelain` which works even on initial commits
    (no HEAD yet) and covers all change categories in a single command.
    Falls back to an empty set if not in a git repository.
    """
    root = Path(root_dir)
    files: set[Path] = set()

    try:
        result = subprocess.run(
            ["git", "-c", "core.quotePath=false", "status", "--porcelain", "-uall"],
            capture_output=True,
            text=True,
            cwd=root,
            encoding="utf-8",
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
    except (subprocess.CalledProcessError, FileNotFoundError):
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
        print_error("Directory 'specs/' not found. Run /pb-plan first.")
        sys.exit(1)

    spec_dirs = [d for d in specs_dir.iterdir() if d.is_dir()]
    if not spec_dirs:
        print_error("No feature specs found in 'specs/'.")
        sys.exit(1)

    # Sort by name (relies on YYYY-MM-DD prefix)
    return sorted(spec_dirs, key=lambda x: x.name)[-1]


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
    try:
        # Check once if rumdl is available before iterating files
        subprocess.run(["rumdl", "--version"], capture_output=True, check=True)
    except FileNotFoundError:
        print_warning(
            "Command 'rumdl' not found — skipping markdown auto-format. "
            "Install it with: cargo install rumdl  (or: pip install rumdl) "
            "to enable automatic markdown formatting."
        )
        return
    except subprocess.CalledProcessError:
        pass  # rumdl exists but --version may not be supported; proceed anyway

    for md_file in md_files:
        result = subprocess.run(["rumdl", "fmt", str(md_file)], capture_output=True, text=True)
        if result.returncode == 0:
            print_success(f"Formatted: {md_file.name}")
        else:
            print_warning(f"rumdl failed on {md_file.name}: {result.stderr.strip()}")


def validate_plan(spec_dir: Path) -> bool:
    """Validate pb-plan generated documents."""
    print_info(f"Running Post-Plan Validation on: {spec_dir}")
    passed = True

    design_file = spec_dir / "design.md"
    tasks_file = spec_dir / "tasks.md"
    features_dir = spec_dir / "features"

    # 1. Check required files exist
    for f in [design_file, tasks_file]:
        if not f.exists():
            print_error(f"Missing required file: {f.relative_to(spec_dir.parent)}")
            passed = False

    # 2. Validate design.md required sections
    if design_file.exists():
        content = design_file.read_text(encoding="utf-8")
        required_sections = [
            "Architecture Decisions",
            "BDD/TDD Strategy",
            "Verification",
        ]
        for sec in required_sections:
            if sec not in content:
                print_error(f"design.md is missing required section: '{sec}'")
                passed = False
        if passed:
            print_success("design.md structural checks passed.")

    # 3. Validate tasks.md structure
    if tasks_file.exists():
        content = tasks_file.read_text(encoding="utf-8")
        if not re.search(r"#{2,3} Task \d+\.\d+:", content):
            print_error(
                "tasks.md does not contain any valid '## Task X.Y:' or '### Task X.Y:' definitions."
            )
            passed = False
        if "Status:" not in content:
            print_error("tasks.md tasks are missing 'Status:' fields.")
            passed = False

        # Validate each task block has all required fields per contract §7.2
        task_blocks = re.split(r"(?=#{2,3} Task \d+\.\d+:)", content)
        task_blocks = [b for b in task_blocks if re.match(r"#{2,3} Task \d+", b)]
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
        for block in task_blocks:
            task_name_match = re.search(r"#{2,3} Task (\d+\.\d+.*)", block)
            task_name = task_name_match.group(1).strip() if task_name_match else "Unknown Task"
            for field in required_task_fields:
                if field not in block:
                    print_error(f"Task '{task_name}' is missing required field: '{field}'")
                    passed = False

        if passed:
            print_success("tasks.md structural checks passed.")

    # 4. Check for feature files
    has_features = features_dir.exists() and list(features_dir.glob("*.feature"))
    if not has_features:
        print_warning("No .feature files found. (OK if this is a TDD-only lightweight spec)")
    else:
        print_success("Found Gherkin .feature files.")

    return passed


def validate_build(spec_dir: Path) -> bool:
    """Validate pb-build task completion (Orchestrator level)."""
    print_info(f"Running Post-Build Validation on: {spec_dir}")
    passed = True

    tasks_file = spec_dir / "tasks.md"
    if not tasks_file.exists():
        print_error(f"Missing {tasks_file}")
        return False

    content = tasks_file.read_text(encoding="utf-8")

    # Parse task blocks and check completion (use #{2,3} to match ## or ### headings)
    task_blocks = re.split(r"(?=#{2,3} Task \d+\.\d+:)", content)
    task_blocks = [b for b in task_blocks if re.match(r"^#{2,3} Task \d+", b)]

    for block in task_blocks:
        task_name_match = re.search(r"#{2,3} Task (\d+\.\d+.*)", block)
        task_name = task_name_match.group(1).strip() if task_name_match else "Unknown Task"

        if "🟢 DONE" not in block:
            if "⏭️ SKIPPED" in block:
                print_warning(f"Task Skipped: {task_name}. (Ignored in strict completion check)")
            elif "⛔ OBSOLETE" in block:
                print_info(f"Task Obsolete: {task_name}. (Ignored in strict completion check)")
            elif "🔴 TODO" in block or "🟡 IN PROGRESS" in block:
                print_error(f"Task Unfinished: {task_name} is not marked as DONE.")
                passed = False
            elif "🔄 DCR" in block:
                print_error(f"Task Blocked by DCR: {task_name}. Needs design refinement.")
                passed = False
            else:
                print_error(f"Task Invalid Status: {task_name}. Missing 🟢 DONE.")
                passed = False
            continue

        # Check for unchecked steps
        unchecked = re.findall(r"^[ \t]*- \[ \].*", block, re.MULTILINE)
        if unchecked:
            print_error(
                f"Task '{task_name}' is marked DONE but has incomplete steps:\n  "
                + "\n  ".join(unchecked)
            )
            passed = False

        # Check that at least one step checkbox exists (prevents LLM from deleting all steps)
        all_checkboxes = re.findall(r"^[ \t]*- \[[ xX]\].*", block, re.MULTILINE)
        if not all_checkboxes:
            print_error(
                f"Task '{task_name}' is marked DONE but contains no step checkboxes. "
                "Contract requires at least one step."
            )
            passed = False

    if passed:
        print_success("All targeted tasks in tasks.md are properly marked as DONE.")

    # Deep codebase scan for mocks, TODOs, and skipped tests
    passed &= scan_codebase(mode="build")
    return passed


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
        latest_spec = get_latest_spec_dir(specs_dir)

        if mode == "plan":
            run_rumdl_format(latest_spec)
            all_passed = validate_plan(latest_spec)

        if mode == "build":
            all_passed = validate_build(latest_spec)

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
