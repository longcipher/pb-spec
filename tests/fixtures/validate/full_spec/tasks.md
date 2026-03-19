# Example Full-Mode Tasks

## Phase 1

### Task 1.1: Add user model

> **Context:** Create the User data model with email and password hash fields.
> **Verification:** Run `uv run pytest tests/test_models.py -v` and confirm all model tests pass.

- **Status:** 🔴 TODO
- **Loop Type:** TDD-only
- **Scenario Coverage:** N/A because this is internal scaffolding with no user-visible behavior
- **Behavioral Contract:** The User model stores email and hashed password without exposing raw credentials
- **Simplification Focus:** N/A
- [ ] **Step 1:** Create the User model class with required fields.
- [ ] **Step 2:** Add database migration for the users table.
- [ ] **BDD Verification:** N/A because this task does not expose user-visible behavior
- [ ] **Advanced Test Verification:** N/A because no advanced tests apply to a basic model
- [ ] **Runtime Verification:** N/A because this is not runtime-facing work

### Task 1.2: Implement auth endpoint

> **Context:** Add a POST /auth/login endpoint that validates credentials and returns a JWT.
> **Verification:** Run `uv run pytest tests/test_auth.py -v` and confirm endpoint tests pass.

- **Status:** 🔴 TODO
- **Loop Type:** BDD+TDD
- **Scenario Coverage:** User authenticates successfully
- **Behavioral Contract:** The endpoint returns 200 with a token on valid credentials and 401 on invalid credentials
- **Simplification Focus:** N/A
- [ ] **Step 1:** Create the auth service with credential validation.
- [ ] **Step 2:** Wire the POST /auth/login endpoint.
- [ ] **BDD Verification:** Run `uv run behave features/auth.feature` and confirm the scenario passes
- [ ] **Advanced Test Verification:** N/A because no advanced tests apply to a standard auth endpoint
- [ ] **Runtime Verification:** N/A because local endpoint testing does not require runtime evidence

### Task 1.3: Handle auth errors

> **Context:** Return a 401 status code when credentials are invalid.
> **Verification:** Run `uv run pytest tests/test_auth.py -v` and confirm error scenario passes.

- **Status:** 🔴 TODO
- **Loop Type:** BDD+TDD
- **Scenario Coverage:** User receives an auth error
- **Behavioral Contract:** The endpoint returns 401 with an error message on invalid credentials
- **Simplification Focus:** N/A
- [ ] **Step 1:** Add credential validation error handling.
- [ ] **Step 2:** Return proper 401 response.
- [ ] **BDD Verification:** Run `uv run behave features/auth.feature` and confirm the error scenario passes
- [ ] **Advanced Test Verification:** N/A because no advanced tests apply to error handling
- [ ] **Runtime Verification:** N/A because local endpoint testing does not require runtime evidence
