# Rate Limiter Tasks

## Phase 1

### Task 1.1: Implement rate limiter store protocol

> **Context:** Define the storage abstraction so the middleware is backend-agnostic.
> **Verification:** Run `uv run pytest tests/test_rate_limiter_store.py -v` and confirm all store tests pass.

- **Status:** 🔴 TODO
- **Loop Type:** TDD-only
- **Scenario Coverage:** N/A because this is internal protocol definition with no user-visible behavior
- **Behavioral Contract:** The store protocol defines `increment`, `count`, and `reset` methods
- **Simplification Focus:** Keep protocol minimal — three methods only
- **Advanced Test Coverage:** Property tests for counter invariants across window boundaries
- [ ] **Step 1:** Define the `RateLimiterStore` protocol.
- [ ] **Step 2:** Implement the Redis backend.
- [ ] **Step 3:** Implement the in-memory fallback.
- [ ] **BDD Verification:** N/A because this task does not expose user-visible behavior
- [ ] **Advanced Test Verification:** uv run pytest tests/test_rate_limiter_store.py --hypothesis-show-statistics
- [ ] **Runtime Verification:** N/A because this is not runtime-facing work

### Task 1.2: Add rate limiter middleware

> **Context:** Create the middleware that intercepts requests and enforces limits.
> **Verification:** Run `uv run pytest tests/test_rate_limiter_middleware.py -v` and confirm middleware tests pass.

- **Status:** 🔴 TODO
- **Loop Type:** BDD+TDD
- **Scenario Coverage:** Rate limited request receives 429 response
- **Behavioral Contract:** The middleware returns 429 with Retry-After header when the limit is exceeded
- **Simplification Focus:** N/A
- [ ] **Step 1:** Implement the middleware class using the store protocol.
- [ ] **Step 2:** Add the `@rate_limit` decorator.
- [ ] **BDD Verification:** Run `uv run behave features/rate_limiter.feature` and confirm the rate limit scenario passes
- [ ] **Advanced Test Verification:** N/A because no advanced tests apply to middleware orchestration
- [ ] **Runtime Verification:** curl -s -o /dev/null -w "%{http_code}" <http://localhost:8000/api/limited> and confirm 429 after exceeding limit

### Task 1.3: Wire middleware into application

> **Context:** Register the rate limiter middleware in the application stack.
> **Verification:** Run `uv run pytest tests/test_app_integration.py -v` and confirm integration tests pass.

- **Status:** 🔴 TODO
- **Loop Type:** BDD+TDD
- **Scenario Coverage:** Allowed request passes through rate limiter
- **Behavioral Contract:** Requests under the limit pass through with no added latency beyond the counting overhead
- **Simplification Focus:** N/A
- [ ] **Step 1:** Register the middleware in the application factory.
- [ ] **Step 2:** Add integration tests for end-to-end middleware behavior.
- [ ] **BDD Verification:** Run `uv run behave features/rate_limiter.feature` and confirm the allowed request scenario passes
- [ ] **Advanced Test Verification:** N/A because integration tests cover the wiring
- [ ] **Runtime Verification:** curl -s <http://localhost:8000/api/health> and confirm 200 with no rate limit headers on health endpoint
