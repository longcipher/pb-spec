# Example Full-Mode Design

## Executive Summary

This is a canonical full-mode design document that demonstrates all required sections for a build-eligible spec.

## Source Inputs & Normalization

### 2.1 Source Materials

Authentication endpoint notes and API requirements.

### 2.2 Normalization Approach

The raw notes were normalized into a ledger of concrete behavior and internal support requirements.

### 2.3 Source Requirement Ledger

| Requirement ID | Source Summary | Type | Notes |
| :--- | :--- | :--- | :--- |
| `R1` | `Define the user model and credential storage` | `Functional` | `Supports later auth behavior` |
| `R2` | `Return a JWT when valid credentials are submitted` | `Functional` | `User-visible` |
| `R3` | `Return 401 on invalid credentials` | `Functional` | `User-visible` |

## Requirements & Goals

- Implement a user authentication endpoint
- Validate credentials against a stored hash
- Return a signed JWT on success

## Requirements Coverage Matrix

| Requirement ID | Covered In Design | Scenario Coverage | Task Coverage | Status / Rationale |
| :--- | :--- | :--- | :--- | :--- |
| `R1` | `Detailed Design` | `N/A because this is internal scaffolding` | `Task 1.1` | `Covered` |
| `R2` | `Detailed Design` | `auth.feature / User authenticates successfully` | `Task 1.2` | `Covered` |
| `R3` | `Detailed Design` | `auth.feature / User receives an auth error` | `Task 1.3` | `Covered` |

## Architecture Overview

The authentication feature follows a layered architecture:

- API layer handles HTTP request/response
- Service layer contains business logic
- Repository layer manages data access

## Existing Components to Reuse

No existing components identified for reuse.

## Detailed Design

The authentication feature exposes a single API endpoint with clear separation of concerns across API, service, and repository layers.

### API Contract

POST /auth/login accepts `{ email, password }` and returns `{ token }` on success.

### Data Model

The User model stores email and bcrypt-hashed password.

## Verification & Testing Strategy

- Unit tests for service logic
- Integration tests for API endpoint
- BDD scenarios for user-visible behavior

## Implementation Plan

1. Add User model and migration
2. Implement auth service
3. Wire API endpoint
4. Add BDD scenarios and integration tests
