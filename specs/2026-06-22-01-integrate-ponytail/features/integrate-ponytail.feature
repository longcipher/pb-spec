Feature: Integrate ponytail simplification philosophy into pb-spec skills
  As a developer using pb-spec to plan, build, and improve code
  I want the ponytail decision ladder embedded in each skill
  So that agents naturally produce minimal, non-over-engineered code

  Background:
    Given the ponytail ladder: YAGNI → stdlib → native → existing dep → one-liner → minimum
    And the ponytail comment convention for tracked deferrals
    And the rule: never simplify away validation, error handling, security

  Scenario: pb-plan applies ponytail ladder to architecture decisions
    Given a requirement to plan a feature
    When the planner evaluates architecture choices
    Then the planner applies the ponytail ladder before selecting a pattern
    And stdlib/native solutions are preferred over custom implementations
    And design.md includes a "Simplification Strategy" section with ponytail ladder

  Scenario: pb-plan design template includes ponytail section
    Given the lightweight design template in references/
    When the template is rendered
    Then it contains a "Simplification Strategy" section
    And the section states the ponytail ladder
    And the section asks: "Does this need to exist? Can stdlib do it? One line?"

  Scenario: pb-build Generator applies ponytail before coding
    Given a task to implement
    When the Generator writes code (GREEN phase)
    Then the Generator climbs the ponytail ladder before writing any code
    And the implementer prompt includes the ladder as a pre-implementation check

  Scenario: pb-build Evaluator detects over-engineering
    Given a Generator's implementation diff
    When the Evaluator audits the diff
    Then the Evaluator checks for over-engineering using ponytail criteria
    And unnecessary abstractions are flagged as FAIL

  Scenario: pb-improve audits for over-engineering
    Given an existing codebase to audit
    When the audit runs across categories
    Then "over-engineering" is a finding category under Tech Debt
    And findings are ranked by deletion value (lines removable)

  Scenario: Generated specs include ponytail ladder
    Given pb-plan or pb-improve generates a design.md
    When the design.md is read
    Then it contains a Code Simplification Constraints section
    And the section references the ponytail ladder explicitly
    And tasks.md Simplification Focus field references the ladder
