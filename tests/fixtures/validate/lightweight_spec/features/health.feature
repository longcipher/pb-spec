Feature: Health Check

  Scenario: Health check returns service status
    Given the service is running
    When a GET request is made to /health
    Then the response contains a status field with value "ok"
