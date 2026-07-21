Feature: Validate pb-spec workflow artifacts
  As a developer using pb-spec
  I want to validate my workflow artifacts
  So that I can ensure code quality and task completion

  Background:
    Given I have a pb-spec project set up

  Scenario: design.md with all 5 required sections is valid
    Given I have a spec directory with a valid plan
    When I run "pb-spec validate --plan"
    Then the command should succeed
    And I should see "design.md structural checks passed"

  Scenario Outline: design.md missing a required section is invalid
    Given I have a spec directory with design.md missing "<section>"
    When I run "pb-spec validate --plan"
    Then the command should fail
    And I should see "is missing required section"
    Examples:
      | section                  |
      | Summary                  |
      | Approach                 |
      | Architecture Decisions   |
      | BDD/TDD Strategy         |
      | Verification             |

  Scenario: tasks.md with all 4 required fields is valid
    Given I have a spec directory with a valid plan
    When I run "pb-spec validate --plan"
    Then the command should succeed
    And I should see "tasks.md structural checks passed"

  Scenario Outline: tasks.md missing a required field is invalid
    Given I have a spec directory with tasks.md missing "<field>"
    When I run "pb-spec validate --plan"
    Then the command should fail
    And I should see "is missing required field"
    Examples:
      | field              |
      | Context:           |
      | Verification:      |
      | Status:            |
      | Scenario Coverage: |

  Scenario: Build Blocked packet with all 3 fields is valid
    Given I have a spec directory with a valid Build Blocked packet
    When I run "pb-spec validate --plan"
    Then the command should succeed
    And I should see "tasks.md structural checks passed"

  Scenario Outline: Build Blocked packet missing a field is invalid
    Given I have a spec directory with a Build Blocked packet missing "<field>"
    When I run "pb-spec validate --plan"
    Then the command should fail
    And I should see "Incomplete"
    Examples:
      | field            |
      | Reason           |
      | Requested Change |
      | Impact           |

  Scenario: DCR packet with all 3 fields is valid
    Given I have a spec directory with a valid DCR packet
    When I run "pb-spec validate --plan"
    Then the command should succeed
    And I should see "tasks.md structural checks passed"

  Scenario Outline: DCR packet missing a field is invalid
    Given I have a spec directory with a DCR packet missing "<field>"
    When I run "pb-spec validate --plan"
    Then the command should fail
    And I should see "Incomplete"
    Examples:
      | field            |
      | Reason           |
      | Requested Change |
      | Impact           |

  Scenario: features directory with at least one .feature file is valid
    Given I have a spec directory with a valid plan
    When I run "pb-spec validate --plan"
    Then the command should succeed
    And I should see "Found Gherkin .feature files"

  Scenario: features directory missing is invalid
    Given I have a spec directory without a features directory
    When I run "pb-spec validate --plan"
    Then the command should fail
    And I should see "No .feature files found"
