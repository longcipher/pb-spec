# Example Lightweight Design

## Summary

Add a health check endpoint for monitoring.

## Approach

Add a simple GET /health route that returns 200 with service status.

## Architecture Decisions

No new boundaries introduced. Uses existing API router pattern.

## BDD/TDD Strategy

- BDD: one scenario for health check visibility
- TDD: unit test the response shape

## Code Simplification Constraints

Keep the handler minimal — single function, no middleware.

## BDD Scenario Inventory

- Health check returns service status

## Existing Components to Reuse

No existing components identified for reuse.

## Verification

Run `uv run pytest tests/test_health.py -v` and `uv run behave features/health.feature`.
