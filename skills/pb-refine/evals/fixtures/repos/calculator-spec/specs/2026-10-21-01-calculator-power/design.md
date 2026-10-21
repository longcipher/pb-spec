# Design: calculator-power

| Field | Value |
| :--- | :--- |
| Spec Directory | specs/2026-10-21-01-calculator-power/ |
| Status | Draft |
| Date | 2026-10-21 |
| Commit | 0000000 |

## Summary

Add a `power(base, exponent)` function to the calculator package with non-negative
integer exponents, raising ValueError on negative exponents. No user-visible impact
beyond the new library function.

## Approach

Implement integer exponentiation with the built-in `**` operator and a guard for
negative exponents. Alternative: `math.pow`, rejected because it returns floats and
loses int precision for large results. Ladder: stdlib operator, minimum code.

## Architecture Decisions

### [ADR-001] Use the `**` operator with a negative-exponent guard

- **Context:** power needs int-exact results and strict input validation.
- **Decision:** use `**`; raise ValueError when exponent < 0.
- **Consequences:** floats are not supported yet; a later revision may add them.

## TDD & Mutation Testing Strategy

- **Type contracts:** `power(base: int, exponent: int) -> int`; ValueError on negative
  exponent; `power(0, 0) == 1`.
- **Test matrix:** unit tests for positive exponents, zero exponent, zero base,
  negative-exponent error path; property test: `power(b, e) == b ** e` for random
  non-negative ints (hypothesis, invariants).
- **Mutation strategy — selective and scope-bounded:** mutate only
  `src/calculator/__init__.py::power` (boundary math); target score ≥ 85% with `mutmut`.
  Infra and trivial code are mutation-exempt.

## Verification

`uv run --with pytest -q pytest` exits 0; `mutmut run --paths-to-mutate src/calculator/__init__.py` score ≥ 85%.
