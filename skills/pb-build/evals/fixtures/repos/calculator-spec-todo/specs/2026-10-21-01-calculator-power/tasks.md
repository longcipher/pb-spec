# Tasks: calculator-power

## Task 1.1: "Implement power" — integer exponentiation with guard

- **TaskID:** `T1` - **DependsOn:** `None` - **Complexity:** `Low`
- **Context:** Implement `power(base, exponent)` in src/calculator/**init**.py per the TDD & Mutation Testing Strategy section. Failing tests already exist.
- **Verification:** `uv run --with pytest -q pytest tests/test_calculator.py -k power` exits 0.
- **Status:** 🔴 TODO
- **Test Coverage:** tests/test_calculator.py::test_power_non_negative, tests/test_calculator.py::test_power_zero, tests/test_calculator.py::test_power_negative_raises

### Task 1.2: "Implement mean" — arithmetic mean with empty guard

- **TaskID:** `T2` - **DependsOn:** `None` - **Complexity:** `Low`
- **Context:** Implement `mean(values)` in src/calculator/**init**.py per the TDD & Mutation Testing Strategy section. Failing tests already exist.
- **Verification:** `uv run --with pytest -q pytest tests/test_calculator.py -k mean` exits 0.
- **Status:** 🔴 TODO
- **Test Coverage:** tests/test_calculator.py::test_mean_basic, tests/test_calculator.py::test_mean_empty_raises
