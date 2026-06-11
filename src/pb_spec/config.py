"""Shared configuration for pb-spec."""

from __future__ import annotations

import functools
import logging
import os

logger = logging.getLogger(__name__)


def _parse_int_env(name: str, default: int) -> int:
    """Parse an integer from an environment variable with validation."""
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        logger.warning("Invalid value for %s=%r, using default %d", name, raw, default)
        return default


@functools.lru_cache(maxsize=1)
def _get_timeout_config_cached() -> dict[str, int]:
    """Cached implementation of timeout config (for testing)."""
    return {
        "git_ls_files": _parse_int_env("PB_SPEC_GIT_TIMEOUT", 60),
        "rumdl_check": _parse_int_env("PB_SPEC_RUMDL_CHECK_TIMEOUT", 10),
        "rumdl_format": _parse_int_env("PB_SPEC_RUMDL_FORMAT_TIMEOUT", 30),
    }


def get_timeout_config() -> dict[str, int]:
    """Get timeout configuration from environment variables with defaults."""
    return _get_timeout_config_cached()


def clear_timeout_cache() -> None:
    """Clear the timeout config cache. For testing only."""
    _get_timeout_config_cached.cache_clear()
