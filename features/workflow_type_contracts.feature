Feature: Workflow artifacts carry executable contract meaning

  Scenario: Planner emits a build-eligible spec contract
    Given a feature requirement is planned through the existing pb-spec workflow
    When the planner produces design, task, and feature artifacts
    Then the artifacts include the required contract fields in the existing markdown format
    And the build workflow can treat the planned spec as ready for validation instead of re-interpreting missing structure

  Scenario: Builder rejects an incomplete spec before execution
    Given a planned spec is missing a required contract field
    When the builder evaluates the spec
    Then the builder reports the missing field before spawning implementation work
    And the builder does not continue to later tasks

  Scenario: Builder uses allowed task state transitions only
    Given a pending task in a build-eligible spec
    When the builder starts work on the task
    Then the task enters the allowed in-progress path before completion
    And the task cannot be marked done until scenario, test, and verification evidence are satisfied

  Scenario: Refiner accepts only complete blocked-build packets
    Given a blocked build handoff for a feature
    When the handoff omits required failure evidence or impact details
    Then the refiner rejects the handoff as incomplete
    But when the handoff includes the required packet sections
    Then the refiner updates only the affected spec artifacts