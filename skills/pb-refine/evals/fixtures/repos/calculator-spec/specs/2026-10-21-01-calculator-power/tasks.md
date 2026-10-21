# Tasks: calculator-power

## Task 1.1: "Implement power" — integer exponentiation with guard

- **TaskID:** `T1` - **DependsOn:** `None` - **Complexity:** `Low`
- **Context:** Implement `power(base, exponent)` in src/calculator/**init**.py per the TDD & Mutation Testing Strategy section.
- **Verification:** `uv run --with pytest -q pytest` exits 0.
- **Status:** 🟢 DONE
- **Test Coverage:** tests/test_calculator.py::test_power_non_negative, tests/test_calculator.py::test_power_zero, tests/test_calculator.py::test_power_negative_raises

### Task 1.2: "Document power" — note the new function in README

- **TaskID:** `T2` - **DependsOn:** `T1` - **Complexity:** `Low`
- **Context:** Add a one-line README entry for `power`.
- **Verification:** `grep -q "power" README.md` exits 0.
- **Status:** 🔴 TODO
- **Test Coverage:** N/A
