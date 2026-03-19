# Rate Limiter Middleware

## Executive Summary

Add a sliding-window rate limiter middleware to the HTTP API that protects endpoints from abuse while allowing legitimate traffic through.

## Requirements & Goals

- Enforce per-client request limits using a sliding window algorithm
- Return 429 Too Many Requests when limits are exceeded
- Store counters in Redis for distributed deployments

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
