"""Integration tests for pb-spec complete workflow."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from pb_spec.cli import main
from pb_spec.validation import (
    collect_feature_scenarios,
    parse_task_blocks,
    validate_design_file,
    validate_task_file,
)


@pytest.fixture
def runner() -> CliRunner:
    """Create a Click test runner."""
    return CliRunner()


@pytest.fixture
def sample_spec_dir(tmp_path: Path) -> Path:
    """Create a sample spec directory with all required artifacts."""
    spec_dir = tmp_path / "specs" / "2026-03-01-01-user-auth"
    spec_dir.mkdir(parents=True)

    # Create design.md
    design_file = spec_dir / "design.md"
    design_file.write_text(
        """# User Authentication Design

## Executive Summary

Implement user authentication with JWT tokens.

## Source Inputs & Normalization

### 2.1 Source Materials

- Product requirements document
- Security best practices

### 2.2 Normalization Approach

Standardized into functional requirements.

### 2.3 Source Requirement Ledger

| Requirement ID | Source Summary | Type | Notes |
| :--- | :--- | :--- | :--- |
| `AUTH-1` | `User login with credentials` | `Functional` | `Core feature` |
| `AUTH-2` | `JWT token generation` | `Technical` | `Security requirement` |

## Requirements & Goals

- Secure user authentication
- Stateless session management
- Token-based authorization

## Requirements Coverage Matrix

| Requirement ID | Covered In Design | Scenario Coverage | Task Coverage | Status / Rationale |
| :--- | :--- | :--- | :--- | :--- |
| `AUTH-1` | `Detailed Design` | `auth.feature / User logs in successfully` | `Task 1.1` | `Covered` |
| `AUTH-2` | `Detailed Design` | `auth.feature / User logs in successfully` | `Task 1.2` | `Covered` |

## Architecture Overview

```
Client -> API Gateway -> Auth Service -> Database
                |
                v
            JWT Token
```

## Existing Components to Reuse

- Existing user database schema
- Password hashing utilities

## Detailed Design

### Authentication Flow

1. User submits credentials
2. Validate credentials against database
3. Generate JWT token
4. Return token to client

### Token Structure

- Header: Algorithm and type
- Payload: User ID and expiration
- Signature: HMAC-SHA256

## Verification & Testing Strategy

- Unit tests for token generation
- Integration tests for auth flow
- BDD scenarios for user-facing behavior

## Implementation Plan

1. Implement auth service
2. Add JWT utilities
3. Create API endpoints
4. Write tests and scenarios
""",
        encoding="utf-8",
    )

    # Create tasks.md
    tasks_file = spec_dir / "tasks.md"
    tasks_file.write_text(
        """# User Authentication Tasks

### Task 1.1: Implement user login endpoint

> **Context:** Create POST /auth/login endpoint that accepts username and password.
> **Verification:** Run auth feature scenarios and verify JWT token is returned.

- **Status:** 🟢 DONE
- **Loop Type:** BDD+TDD
- **Requirement Coverage:** `AUTH-1`
- **Scenario Coverage:** auth.feature / User logs in successfully, auth.feature / User logs in with invalid credentials
- **Behavioral Contract:** Return JWT token on valid credentials, 401 on invalid
- **Simplification Focus:** Use bcrypt for password hashing
- [x] **Step 1:** Create auth router with login endpoint
- [x] **Step 2:** Implement credential validation
- [x] **Step 3:** Generate JWT token on success
- [x] **BDD Verification:** uv run behave features/auth.feature
- [x] **Advanced Test Verification:** N/A because no advanced tests apply
- [x] **Runtime Verification:** curl -X POST http://localhost:8000/auth/login -d '{"username":"test","password":"test"}'

### Task 1.2: Add JWT token utilities

> **Context:** Create utilities for JWT token generation and validation.
> **Verification:** Run unit tests for token operations.

- **Status:** 🟢 DONE
- **Loop Type:** TDD-only
- **Requirement Coverage:** `AUTH-2`
- **Scenario Coverage:** N/A because this is internal utility work
- **Behavioral Contract:** Tokens must be validatable and expire correctly
- **Simplification Focus:** Use python-jose library
- [x] **Step 1:** Create token generation function
- [x] **Step 2:** Create token validation function
- [x] **Step 3:** Add expiration handling
- [x] **BDD Verification:** N/A because this task does not expose user-visible behavior
- [x] **Advanced Test Verification:** N/A because no advanced tests apply
- [x] **Runtime Verification:** N/A because this is not runtime-facing work

### Task 1.3: Add authentication middleware

> **Context:** Create middleware to validate JWT tokens on protected routes.
> **Verification:** Test protected endpoints with valid and invalid tokens.

- **Status:** 🔴 TODO
- **Loop Type:** BDD+TDD
- **Requirement Coverage:** `AUTH-1`, `AUTH-2`
- **Scenario Coverage:** auth.feature / User accesses protected resource with valid token, auth.feature / User accesses protected resource without token
- **Behavioral Contract:** Allow access with valid token, reject with 401 otherwise
- **Simplification Focus:** Use FastAPI dependency injection
- [ ] **Step 1:** Create auth dependency
- [ ] **Step 2:** Apply to protected routes
- [ ] **Step 3:** Handle token validation errors
- [ ] **BDD Verification:** uv run behave features/auth.feature
- [ ] **Advanced Test Verification:** N/A because no advanced tests apply
- [ ] **Runtime Verification:** curl -H "Authorization: Bearer <token>" http://localhost:8000/protected
""",
        encoding="utf-8",
    )

    # Create features directory and auth.feature
    features_dir = spec_dir / "features"
    features_dir.mkdir()
    auth_feature = features_dir / "auth.feature"
    auth_feature.write_text(
        """Feature: User Authentication

  Background:
    Given the auth service is running
    And a user exists with username "testuser" and password "testpass"

  Scenario: User logs in successfully
    When the user logs in with username "testuser" and password "testpass"
    Then the response should be successful
    And a JWT token should be returned

  Scenario: User logs in with invalid credentials
    When the user logs in with username "testuser" and password "wrongpass"
    Then the response should be 401 Unauthorized
    And no token should be returned

  Scenario: User accesses protected resource with valid token
    Given the user has a valid JWT token
    When the user accesses a protected resource
    Then the response should be successful

  Scenario: User accesses protected resource without token
    When the user accesses a protected resource without a token
    Then the response should be 401 Unauthorized
""",
        encoding="utf-8",
    )

    return spec_dir


class TestDesignValidation:
    """Tests for design.md validation."""

    def test_validate_design_full_mode(self, sample_spec_dir: Path) -> None:
        """Test validation of full-mode design document."""
        design_file = sample_spec_dir / "design.md"
        errors = validate_design_file(design_file)
        assert errors == [], f"Design validation failed: {errors}"

    def test_validate_design_missing_sections(self, tmp_path: Path) -> None:
        """Test validation detects missing required sections."""
        design_file = tmp_path / "design.md"
        design_file.write_text(
            """# Incomplete Design

## Executive Summary

This design is missing required sections.
""",
            encoding="utf-8",
        )

        errors = validate_design_file(design_file)
        assert len(errors) > 0
        assert any("Missing required design section" in e for e in errors)


class TestTaskValidation:
    """Tests for tasks.md validation."""

    def test_validate_tasks_with_scenarios(self, sample_spec_dir: Path) -> None:
        """Test validation of tasks with scenario coverage."""
        tasks_file = sample_spec_dir / "tasks.md"
        scenario_inventory = collect_feature_scenarios(sample_spec_dir / "features")
        errors = validate_task_file(tasks_file, scenario_inventory=scenario_inventory)
        assert errors == [], f"Task validation failed: {errors}"

    def test_validate_tasks_parse_blocks(self, sample_spec_dir: Path) -> None:
        """Test parsing of task blocks."""
        tasks_file = sample_spec_dir / "tasks.md"
        task_blocks = parse_task_blocks(tasks_file)

        assert len(task_blocks) == 3
        assert task_blocks[0].task_id == "Task 1.1"
        assert task_blocks[0].name == "Implement user login endpoint"
        assert task_blocks[0].fields.get("Status") == "🟢 DONE"
        assert task_blocks[2].fields.get("Status") == "🔴 TODO"


class TestFeatureParsing:
    """Tests for feature file parsing."""

    def test_collect_scenarios(self, sample_spec_dir: Path) -> None:
        """Test collecting scenarios from feature files."""
        features_dir = sample_spec_dir / "features"
        scenario_inventory = collect_feature_scenarios(features_dir)

        assert len(scenario_inventory) == 4
        assert "User logs in successfully" in scenario_inventory
        assert "User logs in with invalid credentials" in scenario_inventory
        assert "User accesses protected resource with valid token" in scenario_inventory
        assert "User accesses protected resource without token" in scenario_inventory


class TestCLIValidate:
    """Tests for CLI validate command."""

    def test_validate_spec_directory(self, runner: CliRunner, sample_spec_dir: Path) -> None:
        """Test validating a complete spec directory."""
        result = runner.invoke(main, ["validate", str(sample_spec_dir)])
        assert result.exit_code == 0, f"Validation failed: {result.output}"
        assert "Validation passed" in result.output

    def test_validate_missing_design(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test validation fails when design.md is missing."""
        spec_dir = tmp_path / "spec"
        spec_dir.mkdir()
        (spec_dir / "tasks.md").write_text("# Tasks", encoding="utf-8")
        (spec_dir / "features").mkdir()

        result = runner.invoke(main, ["validate", str(spec_dir)])
        assert result.exit_code != 0
        assert "Missing required file" in result.output and "design.md" in result.output

    def test_validate_missing_tasks(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test validation fails when tasks.md is missing."""
        spec_dir = tmp_path / "spec"
        spec_dir.mkdir()
        (spec_dir / "design.md").write_text("# Design", encoding="utf-8")
        (spec_dir / "features").mkdir()

        result = runner.invoke(main, ["validate", str(spec_dir)])
        assert result.exit_code != 0
        assert "Missing required file" in result.output and "tasks.md" in result.output

    def test_validate_missing_features(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test validation fails when features directory is missing."""
        spec_dir = tmp_path / "spec"
        spec_dir.mkdir()
        (spec_dir / "design.md").write_text("# Design", encoding="utf-8")
        (spec_dir / "tasks.md").write_text("# Tasks", encoding="utf-8")

        result = runner.invoke(main, ["validate", str(spec_dir)])
        assert result.exit_code != 0
        assert "Missing required directory" in result.output and "features" in result.output


class TestEndToEndWorkflow:
    """End-to-end workflow tests."""

    def test_full_workflow_validation(self, runner: CliRunner, sample_spec_dir: Path) -> None:
        """Test complete workflow from spec creation to validation."""
        # Step 1: Validate design
        design_errors = validate_design_file(sample_spec_dir / "design.md")
        assert design_errors == [], f"Design validation failed: {design_errors}"

        # Step 2: Collect scenarios
        scenario_inventory = collect_feature_scenarios(sample_spec_dir / "features")
        assert len(scenario_inventory) > 0, "No scenarios found"

        # Step 3: Validate tasks with scenarios
        task_errors = validate_task_file(
            sample_spec_dir / "tasks.md", scenario_inventory=scenario_inventory
        )
        assert task_errors == [], f"Task validation failed: {task_errors}"

        # Step 4: Parse task blocks
        task_blocks = parse_task_blocks(sample_spec_dir / "tasks.md")
        assert len(task_blocks) > 0, "No task blocks found"

        # Step 5: CLI validation
        result = runner.invoke(main, ["validate", str(sample_spec_dir)])
        assert result.exit_code == 0, f"CLI validation failed: {result.output}"

    def test_workflow_with_orphan_scenarios(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test workflow detects orphan scenarios."""
        spec_dir = tmp_path / "spec"
        features_dir = spec_dir / "features"
        features_dir.mkdir(parents=True)

        # Create feature with multiple scenarios
        (features_dir / "auth.feature").write_text(
            """Feature: Auth

  Scenario: Login success
    Given user exists
    When user logs in
    Then token is returned

  Scenario: Login failure
    Given user exists
    When user logs in with wrong password
    Then error is returned
""",
            encoding="utf-8",
        )

        # Create design.md
        (spec_dir / "design.md").write_text(
            """# Design

## Summary

Auth feature.

## Approach

JWT-based auth.

## Architecture Decisions

Use FastAPI.

## BDD/TDD Strategy

Behave for BDD.

## Code Simplification Constraints

Keep it simple.

## BDD Scenario Inventory

- Login success
- Login failure

## Existing Components to Reuse

None.

## Verification

Run tests.
""",
            encoding="utf-8",
        )

        # Create tasks.md with only one scenario referenced
        (spec_dir / "tasks.md").write_text(
            """# Tasks

### Task 1.1: Implement login

> **Context:** Add login endpoint.
> **Verification:** Run auth tests.

- **Status:** 🔴 TODO
- **Loop Type:** BDD+TDD
- **Requirement Coverage:** `AUTH-1`
- **Scenario Coverage:** Login success
- **Behavioral Contract:** Return token on success
- **Simplification Focus:** N/A
- [ ] **Step 1:** Implement login
- [ ] **BDD Verification:** uv run behave features/auth.feature
- [ ] **Advanced Test Verification:** N/A because no advanced tests apply
- [ ] **Runtime Verification:** curl -X POST /auth/login
""",
            encoding="utf-8",
        )

        # Validation should detect orphan scenario
        result = runner.invoke(main, ["validate", str(spec_dir)])
        assert result.exit_code != 0
        assert "Orphan scenario not referenced by any task" in result.output
        assert "Login failure" in result.output
