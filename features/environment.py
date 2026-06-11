"""Behave environment hooks for scenario cleanup."""

from __future__ import annotations

import os
import shutil


def after_scenario(context, scenario) -> None:
    """Clean up temporary directory after each scenario."""
    temp_dir = getattr(context, "temp_dir", None)
    if temp_dir and os.path.exists(temp_dir):
        shutil.rmtree(temp_dir, ignore_errors=True)
