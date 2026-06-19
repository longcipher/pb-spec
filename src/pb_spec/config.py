"""Shared configuration for pb-spec."""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)


def _int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        logger.warning("Invalid value for %s=%r, using default %d", name, raw, default)
        return default


GIT_TIMEOUT: int = _int_env("PB_SPEC_GIT_TIMEOUT", 60)
RUMDL_CHECK_TIMEOUT: int = _int_env("PB_SPEC_RUMDL_CHECK_TIMEOUT", 10)
RUMDL_FORMAT_TIMEOUT: int = _int_env("PB_SPEC_RUMDL_FORMAT_TIMEOUT", 30)
