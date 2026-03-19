Feature: Rate Limiting

  Scenario: Rate limited request receives 429 response
    Given the rate limit is set to 5 requests per 60 seconds
    And the client has made 5 requests in the current window
    When the client makes a 6th request to the API
    Then the response returns a 429 status code
    And the response includes a Retry-After header

  Scenario: Allowed request passes through rate limiter
    Given the rate limit is set to 100 requests per 60 seconds
    And the client has made 10 requests in the current window
    When the client makes a request to /api/users
    Then the response returns a 200 status code
    And the response includes X-RateLimit-Remaining header with value 89
