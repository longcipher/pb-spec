Feature: Authentication

  Scenario: User authenticates successfully
    Given a registered user with email "user@example.com" and password "secret123"
    When the user submits valid credentials to the login endpoint
    Then the response contains a signed JWT token

  Scenario: User receives an auth error
    Given a registered user with email "user@example.com" and password "secret123"
    When the user submits an invalid password to the login endpoint
    Then the response returns a 401 status code
