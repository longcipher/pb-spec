"""Shared configuration for pb-spec."""

from __future__ import annotations

import logging
import os
import threading
from dataclasses import dataclass

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


@dataclass(frozen=True)
class TimeoutConfig:
    """Structured timeout configuration."""

    git_ls_files: int = 60
    rumdl_check: int = 10
    rumdl_format: int = 30


_timeout_config: TimeoutConfig | None = None
_config_lock = threading.Lock()


def get_timeout_config() -> TimeoutConfig:
    """Get timeout configuration from environment variables with defaults.

    Cached after first call with thread-safe double-checked locking.
    Call _reset_timeout_config_cache() to refresh.
    """
    global _timeout_config
    if _timeout_config is None:
        with _config_lock:
            if _timeout_config is None:
                _timeout_config = TimeoutConfig(
                    git_ls_files=_parse_int_env("PB_SPEC_GIT_TIMEOUT", 60),
                    rumdl_check=_parse_int_env("PB_SPEC_RUMDL_CHECK_TIMEOUT", 10),
                    rumdl_format=_parse_int_env("PB_SPEC_RUMDL_FORMAT_TIMEOUT", 30),
                )
    return _timeout_config


def _reset_timeout_config_cache() -> None:
    """Reset the cached config. For testing only."""
    global _timeout_config
    with _config_lock:
        _timeout_config = None
