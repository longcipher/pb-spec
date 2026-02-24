"""Version resolution helpers for pb-spec."""

import tomllib
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as distribution_version
from pathlib import Path

PACKAGE_NAME = "pb-spec"
DEFAULT_VERSION = "0.0.0"


def _read_version_from_pyproject() -> str | None:
    """Read version from local pyproject.toml when running from source tree."""
    pyproject_path = Path(__file__).resolve().parents[2] / "pyproject.toml"
    if not pyproject_path.exists():
        return None

    with pyproject_path.open("rb") as file_handle:
        pyproject_data = tomllib.load(file_handle)

    project_data = pyproject_data.get("project")
    if not isinstance(project_data, dict):
        return None

    project_version = project_data.get("version")
    if isinstance(project_version, str) and project_version:
        return project_version
    return None


def get_version() -> str:
    """Resolve version from installed metadata, then source fallback."""
    try:
        return distribution_version(PACKAGE_NAME)
    except PackageNotFoundError:
        source_version = _read_version_from_pyproject()
        if source_version is not None:
            return source_version
        return DEFAULT_VERSION
