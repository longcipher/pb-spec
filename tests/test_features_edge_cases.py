"""Tests for Gherkin parsing edge cases."""

from pathlib import Path

import pytest

from pb_spec.validation.features import collect_feature_scenarios, parse_feature_file


def test_parse_scenario_with_multiline_name(tmp_path: Path) -> None:
    """Parse scenario with multi-line name (continuation lines)."""
    feature_file = tmp_path / "test.feature"
    feature_file.write_text(
        """Feature: Test

  Scenario: User performs a long action
    that spans multiple lines
    Given the user is logged in
    When the user performs an action
    Then the result is successful
""",
        encoding="utf-8",
    )

    scenarios = parse_feature_file(feature_file)

    assert len(scenarios) == 1
    assert scenarios[0].name == "User performs a long action that spans multiple lines"


def test_parse_scenario_outline(tmp_path: Path) -> None:
    """Parse Scenario Outline with Examples table."""
    feature_file = tmp_path / "test.feature"
    feature_file.write_text(
        """Feature: Test

  Scenario Outline: User logs in with <username>
    Given the user has username "<username>"
    When the user signs in
    Then access is granted

    Examples:
      | username |
      | alice    |
      | bob      |
""",
        encoding="utf-8",
    )

    scenarios = parse_feature_file(feature_file)

    assert len(scenarios) == 1
    assert scenarios[0].name == "User logs in with <username>"
    assert scenarios[0].is_outline is True


def test_parse_scenario_template(tmp_path: Path) -> None:
    """Parse Scenario Template (synonym for Scenario Outline)."""
    feature_file = tmp_path / "test.feature"
    feature_file.write_text(
        """Feature: Test

  Scenario Template: User performs action <action>
    Given the user is ready
    When the user performs "<action>"
    Then the result is "<result>"

    Examples:
      | action | result |
      | login  | ok     |
      | logout | done   |
""",
        encoding="utf-8",
    )

    scenarios = parse_feature_file(feature_file)

    assert len(scenarios) == 1
    assert scenarios[0].name == "User performs action <action>"
    assert scenarios[0].is_outline is True


def test_parse_scenario_with_comments(tmp_path: Path) -> None:
    """Parse scenario with interspersed comments."""
    feature_file = tmp_path / "test.feature"
    feature_file.write_text(
        """Feature: Test

  # This is a comment before scenario
  Scenario: User logs in
    # Comment inside scenario
    Given the user has valid credentials
    # Another comment
    When the user signs in
    Then access is granted
""",
        encoding="utf-8",
    )

    scenarios = parse_feature_file(feature_file)

    assert len(scenarios) == 1
    assert scenarios[0].name == "User logs in"


def test_parse_scenario_with_tags(tmp_path: Path) -> None:
    """Parse scenario with tags."""
    feature_file = tmp_path / "test.feature"
    feature_file.write_text(
        """Feature: Test

  @smoke @critical
  Scenario: User logs in
    Given the user has valid credentials
    When the user signs in
    Then access is granted

  @regression
  Scenario: User logs out
    Given the user is logged in
    When the user signs out
    Then the session is ended
""",
        encoding="utf-8",
    )

    scenarios = parse_feature_file(feature_file)

    assert len(scenarios) == 2
    assert scenarios[0].name == "User logs in"
    assert scenarios[1].name == "User logs out"


def test_parse_multiple_scenarios(tmp_path: Path) -> None:
    """Parse multiple scenarios in a single feature file."""
    feature_file = tmp_path / "test.feature"
    feature_file.write_text(
        """Feature: Authentication

  Scenario: User logs in successfully
    Given the user has valid credentials
    When the user signs in
    Then access is granted

  Scenario: User receives auth error
    Given the user has invalid credentials
    When the user signs in
    Then an error is shown

  Scenario: User logs out
    Given the user is logged in
    When the user signs out
    Then the session is ended
""",
        encoding="utf-8",
    )

    scenarios = parse_feature_file(feature_file)

    assert len(scenarios) == 3
    assert scenarios[0].name == "User logs in successfully"
    assert scenarios[1].name == "User receives auth error"
    assert scenarios[2].name == "User logs out"


def test_parse_scenario_with_background(tmp_path: Path) -> None:
    """Parse scenario with Background section (should be skipped)."""
    feature_file = tmp_path / "test.feature"
    feature_file.write_text(
        """Feature: Test

  Background:
    Given the system is initialized

  Scenario: User logs in
    Given the user has valid credentials
    When the user signs in
    Then access is granted
""",
        encoding="utf-8",
    )

    scenarios = parse_feature_file(feature_file)

    assert len(scenarios) == 1
    assert scenarios[0].name == "User logs in"


def test_parse_feature_with_rules(tmp_path: Path) -> None:
    """Parse feature with Rule keyword."""
    feature_file = tmp_path / "test.feature"
    feature_file.write_text(
        """Feature: Test

  Rule: Authentication

    Scenario: User logs in
      Given the user has valid credentials
      When the user signs in
      Then access is granted

    Scenario: User receives auth error
      Given the user has invalid credentials
      When the user signs in
      Then an error is shown
""",
        encoding="utf-8",
    )

    scenarios = parse_feature_file(feature_file)

    assert len(scenarios) == 2
    assert scenarios[0].name == "User logs in"
    assert scenarios[1].name == "User receives auth error"


def test_collect_feature_scenarios_from_subdirectory(tmp_path: Path) -> None:
    """Collect scenarios from feature files in subdirectories."""
    features_dir = tmp_path / "features"
    features_dir.mkdir()
    (features_dir / "auth").mkdir()
    (features_dir / "auth" / "login.feature").write_text(
        """Feature: Login

  Scenario: User logs in
    Given the user has valid credentials
    When the user signs in
    Then access is granted
""",
        encoding="utf-8",
    )
    (features_dir / "auth" / "logout.feature").write_text(
        """Feature: Logout

  Scenario: User logs out
    Given the user is logged in
    When the user signs out
    Then the session is ended
""",
        encoding="utf-8",
    )

    scenario_inventory = collect_feature_scenarios(features_dir)

    assert len(scenario_inventory) == 2
    assert "User logs in" in scenario_inventory
    assert "User logs out" in scenario_inventory


def test_parse_scenario_with_special_characters(tmp_path: Path) -> None:
    """Parse scenario with special characters in name."""
    feature_file = tmp_path / "test.feature"
    feature_file.write_text(
        """Feature: Test

  Scenario: User logs in with email "user@example.com"
    Given the user has an email
    When the user signs in
    Then access is granted

  Scenario: User performs action #123
    Given the user is ready
    When the user performs action
    Then the result is successful
""",
        encoding="utf-8",
    )

    scenarios = parse_feature_file(feature_file)

    assert len(scenarios) == 2
    assert scenarios[0].name == 'User logs in with email "user@example.com"'
    assert scenarios[1].name == "User performs action #123"


def test_parse_empty_feature_file(tmp_path: Path) -> None:
    """Parse empty feature file returns no scenarios."""
    feature_file = tmp_path / "test.feature"
    feature_file.write_text(
        """Feature: Empty

""",
        encoding="utf-8",
    )

    scenarios = parse_feature_file(feature_file)

    assert len(scenarios) == 0


def test_parse_feature_with_only_background(tmp_path: Path) -> None:
    """Parse feature with only Background (no scenarios)."""
    feature_file = tmp_path / "test.feature"
    feature_file.write_text(
        """Feature: Test

  Background:
    Given the system is initialized

""",
        encoding="utf-8",
    )

    scenarios = parse_feature_file(feature_file)

    assert len(scenarios) == 0


@pytest.mark.parametrize(
    "scenario_type,is_outline",
    [
        ("Scenario", False),
        ("Scenario Outline", True),
        ("Scenario Template", True),
    ],
)
def test_parse_scenario_types(tmp_path: Path, scenario_type: str, is_outline: bool) -> None:
    """Parse different scenario types."""
    feature_file = tmp_path / "test.feature"
    feature_file.write_text(
        f"""Feature: Test

  {scenario_type}: User performs action
    Given the user is ready
    When the user performs action
    Then the result is successful
""",
        encoding="utf-8",
    )

    scenarios = parse_feature_file(feature_file)

    assert len(scenarios) == 1
    assert scenarios[0].name == "User performs action"
    assert scenarios[0].is_outline == is_outline
