# Rate Limiter Middleware

## Executive Summary

Add a sliding-window rate limiter middleware to the HTTP API that protects endpoints from abuse while allowing legitimate traffic through.

## Source Inputs & Normalization

### 2.1 Source Materials

Rate limiting requirements, middleware notes, and distributed deployment constraints.

### 2.2 Normalization Approach

The incoming notes were reduced into concrete backend, rejection, and pass-through requirements.

### 2.3 Source Requirement Ledger

| Requirement ID | Source Summary | Type | Notes |
| :--- | :--- | :--- | :--- |
| `R1` | `Define a backend-agnostic store protocol for counters` | `Functional` | `Internal foundation` |
| `R2` | `Return 429 when the limit is exceeded` | `Functional` | `User-visible` |
| `R3` | `Allow requests under the limit to pass through` | `Functional` | `User-visible` |

## Requirements & Goals

- Enforce per-client request limits using a sliding window algorithm
- Return 429 Too Many Requests when limits are exceeded
- Store counters in Redis for distributed deployments

## Requirements Coverage Matrix

| Requirement ID | Covered In Design | Scenario Coverage | Task Coverage | Status / Rationale |
| :--- | :--- | :--- | :--- | :--- |
| `R1` | `Detailed Design` | `N/A because this is internal protocol work` | `Task 1.1` | `Covered` |
| `R2` | `Detailed Design` | `rate_limiter.feature / Rate limited request receives 429 response` | `Task 1.2` | `Covered` |
| `R3` | `Detailed Design` | `rate_limiter.feature / Allowed request passes through rate limiter` | `Task 1.3` | `Covered` |

## Architecture Overview

The rate limiter follows a middleware pattern that intercepts requests before they reach route handlers. It uses a pluggable storage backend behind a `RateLimiterStore` protocol.

## Architecture Decisions

- **Pattern:** Middleware/Decorator — intercept requests at the HTTP layer without modifying route handlers
- **Storage:** Redis-backed with in-memory fallback for development
- **SRP:** The middleware only counts and rejects; it does not log or report metrics

## Existing Components to Reuse

- `src/middleware/base.py` — existing middleware base class provides `before_request` and `after_request` hooks

## Detailed Design

The rate limiter uses a sliding window algorithm with Redis sorted sets and exposes configuration via a route decorator.

### Sliding Window Algorithm

Use a sorted set in Redis with timestamps as scores. On each request, remove entries older than the window, count remaining, and add the current timestamp.

### Configuration

Rate limits are configurable per-route via a decorator:

```python
@rate_limit(requests=100, window=60)
def get_users():
    ...
```

## Verification & Testing Strategy

- Unit tests for the sliding window logic with a mock Redis client
- Integration tests for middleware behavior with a test HTTP client
- BDD scenarios for user-visible rate limit responses

## Implementation Plan

1. Implement `RateLimiterStore` protocol and Redis backend
2. Add the middleware class with configurable limits
3. Wire middleware into the application stack
4. Add BDD scenarios and integration tests
