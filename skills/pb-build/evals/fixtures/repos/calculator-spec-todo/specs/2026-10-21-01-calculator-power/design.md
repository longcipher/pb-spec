# Design: calculator-power

| Field | Value |
| :--- | :--- |
| Spec Directory | specs/2026-10-21-01-calculator-power/ |
| Status | Draft |
| Date | 2026-10-21 |
| Commit | 0000000 |

## Summary

Implement two missing functions the failing tests already cover: `power(base, exponent)`
(integer exponentiation with ValueError on negative exponents) and `mean(values)`
(arithmetic mean, ValueError on empty input).

## Approach

Implement both directly in `src/calculator/__init__.py` in the existing style. The tests
in `tests/test_calculator.py` are the red layer; the minimum implementation turns them
green. No new dependencies.

## Architecture Decisions

### [ADR-001] Stdlib-only implementation

- **Context:** Both functions are trivial pure math.
- **Decision:** Use the `**` operator and `sum()/len()`; no dependencies.
- **Consequences:** `power` is int-exact; `mean` returns float via true division.

## TDD & Mutation Testing Strategy

- **Type contracts:** `power(base: int, exponent: int) -> int` (ValueError on negative
  exponent, `power(0, 0) == 1`); `mean(values: list[int]) -> float` (ValueError on empty).
- **Test matrix:** existing failing unit tests cover happy paths and error paths for both
  functions; boundary cases (`power(0, 0)`, empty `mean`) are explicit.
- **Mutation strategy — selective and scope-bounded:** mutate only
  `src/calculator/__init__.py::power` and `::mean` (boundary math); target ≥ 85% with
  `mutmut`. Infra and trivial code are mutation-exempt.

## Verification

`uv run --with pytest -q pytest` exits 0 with all tests passing.
