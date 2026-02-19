"""pb-spec (Plan-Build Spec) - A CLI tool for managing AI coding assistant skills."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("pb-spec")
except PackageNotFoundError:
    __version__ = "0.0.0"
