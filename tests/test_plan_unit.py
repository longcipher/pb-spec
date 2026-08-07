"""Unit tests for plan-validation internals (strong assertions)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from pb_spec.validation.plan import (
    _DESIGN_REQUIRED_SECTIONS,
    load_contract_config,
    validate_design_structure,
    validate_plan,
    validate_tasks_structure,
)

VALID_DESIGN = (
    "# Design\n\n"
    "## Summary\nS.\n\n"
    "## Approach\nA.\n\n"
    "## Architecture Decisions\nD.\n\n"
    "## TDD & Mutation Testing Strategy\nT.\n\n"
    "## Verification\nV.\n"
)

VALID_TASKS = (
    "# Tasks\n\n"
    "### Task 1.1: First\n"
    "Context: c.\n"
    "Verification: v.\n"
    "Test Coverage: t.\n"
    "Status: 🔴 TODO\n"
    "- [ ] Step 1\n"
)


class TestLoadContractConfig:
    """Tests for contract configuration loading."""

    def test_custom_config_changes_required_sections(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A custom TOML replaces the default required sections."""
        import pb_spec.validation.plan as plan_module

        cfg = tmp_path / "contract.toml"
        cfg.write_text(
            "[design]\n"
            'required_sections = ["Only Section"]\n'
            "optional_sections = []\n"
            "[tasks]\n"
            'required_fields = ["Context:", "Status:"]\n'
            "[build_blocked]\n"
            'required_fields = ["Reason"]\n'
            "[dcr]\n"
            'required_fields = ["Reason"]\n',
            encoding="utf-8",
        )
        load_contract_config(cfg)
        assert plan_module._DESIGN_REQUIRED_SECTIONS == ["Only Section"]
        # Restore the default for subsequent tests.
        load_contract_config()
        monkeypatch.setattr(plan_module, "_DESIGN_REQUIRED_SECTIONS", _DESIGN_REQUIRED_SECTIONS)

    def test_load_contract_config_none_uses_default(self) -> None:
        """Loading with no path refreshes from the packaged default."""
        import pb_spec.validation.plan as plan_module

        load_contract_config()
        assert "Summary" in plan_module._DESIGN_REQUIRED_SECTIONS

    def test_validators_run_after_reload(self, tmp_path: Path) -> None:
        """Validators consume the reloaded globals without crashing."""
        (tmp_path / "design.md").write_text(VALID_DESIGN, encoding="utf-8")
        (tmp_path / "tasks.md").write_text(VALID_TASKS, encoding="utf-8")
        load_contract_config()
        result = validate_tasks_structure(tmp_path)
        assert result.is_valid is True
        design = validate_design_structure(tmp_path)
        assert design.is_valid is True


class TestValidateDesignStructure:
    """Tests for design.md structural validation."""

    def test_missing_file_critical(self, tmp_path: Path) -> None:
        """A missing design.md is a CRITICAL error."""
        result = validate_design_structure(tmp_path)
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert result.errors[0].message == "design.md file does not exist"
        assert result.errors[0].file_path == "design.md"
        assert result.errors[0].severity.value == "critical"

    @pytest.mark.skipif(sys.platform == "darwin", reason="macOS APFS is case-insensitive")
    def test_uppercase_design_file_ignored(self, tmp_path: Path) -> None:
        """A DESIGN.MD file does not satisfy the design.md contract (case-sensitive FS)."""
        (tmp_path / "DESIGN.MD").write_text(VALID_DESIGN, encoding="utf-8")
        result = validate_design_structure(tmp_path)
        assert result.is_valid is False
        assert result.errors[0].message == "design.md file does not exist"

    def test_valid_design_warns(self, tmp_path: Path) -> None:
        """A complete design produces a structural-pass warning."""
        (tmp_path / "design.md").write_text(VALID_DESIGN, encoding="utf-8")
        result = validate_design_structure(tmp_path)
        assert result.is_valid is True
        assert result.warnings == ["design.md structural checks passed."]

    @pytest.mark.parametrize(
        ("section", "fragment"),
        [
            ("Summary", "missing required section: 'Summary'"),
            ("Approach", "missing required section: 'Approach'"),
            ("Architecture Decisions", "missing required section: 'Architecture Decisions'"),
            (
                "TDD & Mutation Testing Strategy",
                "missing required section: 'TDD & Mutation Testing Strategy'",
            ),
            ("Verification", "missing required section: 'Verification'"),
        ],
    )
    def test_missing_section_message(self, tmp_path: Path, section: str, fragment: str) -> None:
        """Each missing required section yields a precise error."""
        content = VALID_DESIGN.replace(f"## {section}\n", "", 1)
        (tmp_path / "design.md").write_text(content, encoding="utf-8")
        result = validate_design_structure(tmp_path)
        assert result.is_valid is False
        assert any(fragment in e.message for e in result.errors)
        assert any(e.field_name == section for e in result.errors)

    def test_unreadable_design_is_critical(self, tmp_path: Path) -> None:
        """An unreadable design.md is a CRITICAL error."""
        target = tmp_path / "design.md"
        target.write_bytes(b"\xff\xfe\x00")
        result = validate_design_structure(tmp_path)
        assert result.is_valid is False
        assert result.errors[0].severity.value == "critical"
        assert "Cannot read file" in result.errors[0].message
        assert result.errors[0].file_path == "design.md"


class TestValidateTasksStructure:
    """Tests for tasks.md structural validation."""

    def test_missing_file_critical(self, tmp_path: Path) -> None:
        """A missing tasks.md is a CRITICAL error."""
        result = validate_tasks_structure(tmp_path)
        assert result.is_valid is False
        assert result.errors[0].message == "tasks.md file does not exist"
        assert result.errors[0].file_path == "tasks.md"

    @pytest.mark.skipif(sys.platform == "darwin", reason="macOS APFS is case-insensitive")
    def test_uppercase_tasks_file_ignored(self, tmp_path: Path) -> None:
        """A TASKS.MD file does not satisfy the tasks.md contract (case-sensitive FS)."""
        (tmp_path / "TASKS.MD").write_text(VALID_TASKS, encoding="utf-8")
        result = validate_tasks_structure(tmp_path)
        assert result.is_valid is False
        assert result.errors[0].message == "tasks.md file does not exist"

    def test_no_task_blocks_critical(self, tmp_path: Path) -> None:
        """A tasks.md without task definitions is a CRITICAL error."""
        (tmp_path / "tasks.md").write_text("# Tasks\nno blocks\n", encoding="utf-8")
        result = validate_tasks_structure(tmp_path)
        assert result.is_valid is False
        assert "does not contain any valid" in result.errors[0].message
        assert result.errors[0].severity.value == "critical"

    def test_valid_tasks_warn(self, tmp_path: Path) -> None:
        """A complete tasks.md produces a structural-pass warning."""
        (tmp_path / "tasks.md").write_text(VALID_TASKS, encoding="utf-8")
        result = validate_tasks_structure(tmp_path)
        assert result.is_valid is True
        assert result.warnings == ["tasks.md structural checks passed."]

    def test_duplicate_task_ids_high(self, tmp_path: Path) -> None:
        """Duplicate task IDs are HIGH severity errors."""
        duplicated = VALID_TASKS + VALID_TASKS
        (tmp_path / "tasks.md").write_text(duplicated, encoding="utf-8")
        result = validate_tasks_structure(tmp_path)
        assert result.is_valid is False
        assert any(
            e.message == "Duplicate task ID found in tasks.md: Task 1.1"
            and e.severity.value == "high"
            for e in result.errors
        )

    def test_empty_required_field(self, tmp_path: Path) -> None:
        """An empty required field produces a precise error."""
        content = VALID_TASKS.replace("Verification: v.", "Verification: ")
        (tmp_path / "tasks.md").write_text(content, encoding="utf-8")
        result = validate_tasks_structure(tmp_path)
        assert any("has empty required field: 'Verification:'" in e.message for e in result.errors)

    def test_invalid_status_message(self, tmp_path: Path) -> None:
        """An unknown status produces a precise error naming the marker contract."""
        content = VALID_TASKS.replace("Status: 🔴 TODO", "Status: 🚀 STARTED")
        (tmp_path / "tasks.md").write_text(content, encoding="utf-8")
        result = validate_tasks_structure(tmp_path)
        assert any("invalid Status: '🚀 STARTED'" in e.message for e in result.errors)
        assert any(e.field_name == "Status:" for e in result.errors)

    def test_unreadable_tasks_is_critical(self, tmp_path: Path) -> None:
        """An unreadable tasks.md is a CRITICAL error."""
        target = tmp_path / "tasks.md"
        target.write_bytes(b"\xff\xfe\x00")
        result = validate_tasks_structure(tmp_path)
        assert result.is_valid is False
        assert result.errors[0].severity.value == "critical"


class TestValidatePlan:
    """Tests for the combined plan validator."""

    def test_missing_design_short_circuits(self, tmp_path: Path) -> None:
        """A missing design.md aborts with a CRITICAL error."""
        (tmp_path / "tasks.md").write_text(VALID_TASKS, encoding="utf-8")
        result = validate_plan(tmp_path)
        assert result.is_valid is False
        assert result.errors[0].message == "Missing required file: design.md"

    def test_missing_tasks_short_circuits(self, tmp_path: Path) -> None:
        """A missing tasks.md aborts with a CRITICAL error."""
        (tmp_path / "design.md").write_text(VALID_DESIGN, encoding="utf-8")
        result = validate_plan(tmp_path)
        assert result.is_valid is False
        assert result.errors[0].message == "Missing required file: tasks.md"

    def test_valid_spec_aggregates_warnings(self, tmp_path: Path) -> None:
        """A valid spec passes and aggregates both structural warnings."""
        (tmp_path / "design.md").write_text(VALID_DESIGN, encoding="utf-8")
        (tmp_path / "tasks.md").write_text(VALID_TASKS, encoding="utf-8")
        result = validate_plan(tmp_path)
        assert result.is_valid is True
        assert len(result.warnings) == 2

    def test_invalid_spec_aggregates_errors(self, tmp_path: Path) -> None:
        """A broken design fails and reports the missing section."""
        content = VALID_DESIGN.replace("## Summary\n", "", 1)
        (tmp_path / "design.md").write_text(content, encoding="utf-8")
        (tmp_path / "tasks.md").write_text(VALID_TASKS, encoding="utf-8")
        result = validate_plan(tmp_path)
        assert result.is_valid is False
        assert any("'Summary'" in e.message for e in result.errors)
