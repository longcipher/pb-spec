"""Spec directory resolution helpers."""

from __future__ import annotations

import os
from pathlib import Path


class SpecResolutionError(Exception):
    """Raised when a spec directory cannot be resolved."""


def resolve_spec_dir(feature_or_path: str, base_dir: Path = Path(".")) -> Path:
    """Resolve feature name or path to spec directory.

    Supports:
    - Full path: specs/2026-03-09-01-workflow-type-contracts
    - Feature name: workflow-type-contracts (resolves to matching spec dir)
    - Configurable via PB_SPEC_SPECS_DIR environment variable
    """
    path = Path(feature_or_path)

    if path.exists():
        return path

    if feature_or_path.startswith("specs/"):
        return Path(feature_or_path)

    # Allow configurable specs directory via environment variable
    specs_dir_env = os.environ.get("PB_SPEC_SPECS_DIR")
    specs_dir = Path(specs_dir_env) if specs_dir_env else base_dir / "specs"

    if not specs_dir.exists():
        raise SpecResolutionError(
            f"specs/ directory not found. Cannot resolve feature name: {feature_or_path}"
        )

    matching_dirs = sorted(
        [d for d in specs_dir.iterdir() if d.is_dir() and d.name.endswith(f"-{feature_or_path}")],
        reverse=True,
    )

    if not matching_dirs:
        raise SpecResolutionError(
            f"No spec directory found for feature '{feature_or_path}' in specs/.\n"
            f"Run /pb-plan <requirement> first to generate the spec."
        )

    return matching_dirs[0]
