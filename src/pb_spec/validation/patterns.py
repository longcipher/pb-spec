"""Shared regex patterns for task and status parsing."""

from __future__ import annotations

import re
from typing import Final

TASK_HEADING_RE: Final[re.Pattern[str]] = re.compile(r"^### (Task \d+\.\d+):\s+(.+?)\s*$")
FIELD_RE: Final[re.Pattern[str]] = re.compile(r"^- \*\*(.+?):\*\*\s*(.+?)\s*$")
QUOTE_FIELD_RE: Final[re.Pattern[str]] = re.compile(r"^> \*\*(.+?):\*\*\s*(.+?)\s*$")
CHECKBOX_RE: Final[re.Pattern[str]] = re.compile(r"^- \[[ xX]\] ")
CHECKBOX_LABEL_RE: Final[re.Pattern[str]] = re.compile(r"^- \[[ xX]\] \*\*(.+?):\*\*\s*(.+?)\s*$")
STATUS_RE: Final[re.Pattern[str]] = re.compile(r"^- \*\*Status:\*\*\s*(.+?)\s*$")
