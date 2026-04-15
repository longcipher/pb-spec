Feature: Validate pb-spec workflow artifacts
  As a developer using pb-spec
  I want to validate my workflow artifacts
  So that I can ensure code quality and task completion

  Background:
    Given I have a pb-spec project set up

  Scenario: Validate plan mode checks design.md sections
    Given I have a spec directory with a valid design.md
    And design.md contains "Architecture Decisions" section
    And design.md contains "BDD/TDD Strategy" section
    And design.md contains "Verification" section
    When I run "pb-spec validate --plan"
    Then the command should succeed
    And I should see "design.md (lightweight mode) structural checks passed"

  Scenario: Validate plan mode fails on missing design section
    Given I have a spec directory with an incomplete design.md
    And design.md is missing "Architecture Decisions" section
    When I run "pb-spec validate --plan"
    Then the command should fail
    And I should see "is missing required section"

  Scenario: Validate plan mode checks tasks.md structure
    Given I have a spec directory with a valid tasks.md
    And tasks.md contains "### Task 1.1:" definition
    And tasks.md contains "Status:" field
    When I run "pb-spec validate --plan"
    Then the command should succeed
    And I should see "tasks.md structural checks passed"

  Scenario: Validate build mode passes for completed tasks
    Given I have a spec directory with tasks.md
    And all tasks have status "🟢 DONE"
    And all task steps are checked "- [x]"
    When I run "pb-spec validate --build"
    Then the command should succeed
    And I should see "All targeted tasks"

  Scenario: Validate build mode fails for TODO tasks
    Given I have a spec directory with tasks.md
    And a task has status "🔴 TODO"
    When I run "pb-spec validate --build"
    Then the command should fail
    And I should see "Task Unfinished"

  Scenario: Validate build mode fails for unchecked steps
    Given I have a spec directory with tasks.md
    And a task has status "🟢 DONE"
    And a task has an unchecked step "- [ ]"
    When I run "pb-spec validate --build"
    Then the command should fail
    And I should see "incomplete steps"

  Scenario: Validate task mode passes on clean codebase
    Given I have a clean codebase without issues
    When I run "pb-spec validate --task"
    Then the command should succeed
    And I should see "Subagent self-check passed"

  Scenario: Validate task mode detects TODO comments
    Given I have a codebase with "TODO:" comment
    When I run "pb-spec validate --task"
    Then the command should fail
    And I should see "TODO/FIXME found"

  Scenario: Validate task mode detects skipped tests
    Given I have a codebase with "@pytest.mark.skip" decorator
    When I run "pb-spec validate --task"
    Then the command should fail
    And I should see "Skipped test found"

  Scenario: Validate task mode detects debug artifacts
    Given I have a codebase with "console.log" statement
    When I run "pb-spec validate --task"
    Then the command should fail
    And I should see "Debug artifact found"

  Scenario: Validate task mode detects NotImplementedError
    Given I have a codebase with "raise NotImplementedError"
    When I run "pb-spec validate --task"
    Then the command should fail
    And I should see "NotImplemented/Mock found"

  Scenario: Validate help shows all options
    When I run "pb-spec validate --help"
    Then I should see "--plan"
    And I should see "--build"
    And I should see "--task"
    And I should see "--specs-dir"