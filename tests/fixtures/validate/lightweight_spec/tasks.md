# Example Lightweight Tasks

## Phase 1

### Task 1.1: Add health check endpoint

> **Context:** Add a minimal health check endpoint for uptime monitoring.
> **Verification:** Run `uv run pytest tests/test_health.py -v` and `uv run behave features/health.feature`.

- **Status:** 🔴 TODO
- **Loop Type:** BDD+TDD
- **Scenario Coverage:** Health check returns service status
- **Behavioral Contract:** The endpoint returns 200 with a JSON body containing service status
- **Simplification Focus:** Keep handler minimal with no middleware
- [ ] **Step 1:** Add the GET /health route handler.
- [ ] **Step 2:** Add unit tests for the response shape.
- [ ] **BDD Verification:** Run `uv run behave features/health.feature` and confirm the scenario passes
- [ ] **Advanced Test Verification:** N/A because no advanced tests apply to a health endpoint
- [ ] **Runtime Verification:** curl -s <http://localhost:8000/health> and confirm JSON status response
