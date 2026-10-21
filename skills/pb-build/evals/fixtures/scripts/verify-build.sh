#!/bin/bash
# Judge for pb-build: suite green, all tasks marked done, no scope creep, no commits.
set -u
fail() { echo "FAIL: $1"; exit 1; }

# Full suite passes.
if ! uv run --with pytest -q pytest >/tmp/build-eval-pytest.log 2>&1; then
  tail -20 /tmp/build-eval-pytest.log
  fail "pytest does not pass"
fi

tail -1 /tmp/build-eval-pytest.log | grep -qE "[0-9]+ passed" || fail "pytest summary line shows no passed tests"

# Implementation exists and is not a stub.
grep -q "def power" src/calculator/__init__.py || fail "power not implemented"
grep -q "def mean" src/calculator/__init__.py || fail "mean not implemented"
if grep -qE "TODO|FIXME|NotImplementedError" src/calculator/__init__.py; then
  fail "implementation contains TODO/FIXME/NotImplementedError stubs"
fi

# Task statuses updated to DONE.
tasks=$(ls specs/*/tasks.md | head -1)
grep -q "🟢 DONE" "$tasks" || fail "no task marked 🟢 DONE in tasks.md"

# No commits were made beyond the fixture's initial state.
commits=$(git rev-list --count HEAD 2>/dev/null || echo 0)
[ "$commits" -le 1 ] || fail "agent made git commits (forbidden)"

echo "PASS: suite green, power+mean implemented, tasks marked DONE, no commits"
