"""Validation utilities for pb-spec."""

from __future__ import annotations

from pb_spec.validation.build import validate_build, validate_task
from pb_spec.validation.io import read_file_content, read_spec_file
from pb_spec.validation.parser import (
    ALLOWED_LOOP_TYPES,
    ALLOWED_TASK_STATUSES,
    BUILD_BLOCKED_REQUIRED_SECTIONS,
    CONTRACT_SECTION_NAMES,
    DCR_REQUIRED_SECTIONS,
    KNOWN_TASK_FIELDS,
    ContractBlock,
    TaskBlock,
    is_bare_na,
    parse_contract_blocks,
    parse_contract_sections,
    parse_task_blocks,
    required_sections_for_contract_block,
    task_display_name,
    validate_contract_blocks,
)
from pb_spec.validation.plan import (
    _load_contract_config,
    validate_plan,
)
from pb_spec.validation.result import (
    ErrorSeverity,
    ValidationError,
    ValidationMode,
    ValidationResult,
    make_validation_error,
)
from pb_spec.validation.scanner import CodeScanner, IssueType, ScanIssue, ScanResult

__all__ = [
    "ALLOWED_LOOP_TYPES",
    "ALLOWED_TASK_STATUSES",
    "BUILD_BLOCKED_REQUIRED_SECTIONS",
    "CONTRACT_SECTION_NAMES",
    "CodeScanner",
    "ContractBlock",
    "DCR_REQUIRED_SECTIONS",
    "ErrorSeverity",
    "IssueType",
    "KNOWN_TASK_FIELDS",
    "ScanIssue",
    "ScanResult",
    "TaskBlock",
    "ValidationError",
    "ValidationMode",
    "ValidationResult",
    "make_validation_error",
    "read_file_content",
    "read_spec_file",
    "validate_build",
    "validate_plan",
    "validate_task",
    "is_bare_na",
    "parse_contract_blocks",
    "parse_contract_sections",
    "parse_task_blocks",
    "required_sections_for_contract_block",
    "task_display_name",
    "validate_contract_blocks",
    "_load_contract_config",
]
