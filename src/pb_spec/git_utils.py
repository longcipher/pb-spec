"""Git interaction utilities for pb-spec."""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path

from pb_spec.config import get_timeout_config

logger = logging.getLogger(__name__)


def get_git_modified_files(root_dir: Path | str = ".") -> set[Path]:
    """Get files with staged, unstaged, or untracked changes.

    Uses `git status --porcelain` which works even on initial commits
    (no HEAD yet) and covers all change categories in a single command.
    Falls back to an empty set if not in a git repository.

    Returns resolved absolute paths for consistent comparison.
    """
    root = Path(root_dir).resolve()
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
            path_str = line[3:].strip()
            if " -> " in path_str:
                path_str = path_str.split(" -> ", 1)[1].strip()
            if path_str.startswith('"') and path_str.endswith('"'):
                path_str = path_str[1:-1]
            file_path = (root / path_str).resolve()
            files.add(file_path)
    except subprocess.TimeoutExpired:
        logger.warning("git status timed out in %s", root)
    except subprocess.CalledProcessError as e:
        logger.debug("git status failed: %s", e.stderr)
    except FileNotFoundError:
        logger.debug("git not found, returning empty set")

    return files
