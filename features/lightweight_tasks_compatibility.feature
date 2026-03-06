Feature: Lightweight pb-plan tasks stay compatible with pb-build

  Scenario: Lightweight task examples use pb-build compatible identifiers and status markers
    Given the pb-plan templates are loaded
    When I inspect the lightweight tasks instructions
    Then the lightweight tasks use Task X.Y headings
    And each lightweight task includes a status marker

  Scenario: Prompt-based pb-build instructions are self-contained
    Given the pb-build prompt template is loaded
    When I inspect the prompt-only build instructions
    Then the embedded implementer prompt is present
    And the prompt does not require references/implementer_prompt.md