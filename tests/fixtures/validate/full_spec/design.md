# Example Full-Mode Design

## Executive Summary

This is a canonical full-mode design document that demonstrates all required sections for a build-eligible spec.

## Requirements & Goals

- Implement a user authentication endpoint
- Validate credentials against a stored hash
- Return a signed JWT on success

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
