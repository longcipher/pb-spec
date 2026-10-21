#!/bin/bash
# Judge for pb-goal (complete path): state file present, COMPLETE with evidence, suite green.
set -u
fail() { echo "FAIL: $1"; exit 1; }

# Goal state file with the required structure.
grep -q "^# Goal:" .pb-goal.md || fail ".pb-goal.md missing '# Goal:' header"
grep -q "Acceptance criteria" .pb-goal.md || fail ".pb-goal.md missing acceptance criteria"

# Suite actually passes — evidence, not claims.
if ! uv run --with pytest -q pytest >/tmp/goal-eval-pytest.log 2>&1; then
  tail -20 /tmp/goal-eval-pytest.log
  fail "pytest does not pass but goal claims progress"
fi

grep -q "def power" src/calculator/__init__.py || fail "power not implemented"

# Status is COMPLETE only with the evidence present.
grep -q "COMPLETE" .pb-goal.md || fail ".pb-goal.md not marked COMPLETE despite green suite"

# Evidence log is not empty.
grep -qi "evidence" .pb-goal.md || fail ".pb-goal.md missing evidence log"

echo "PASS: goal completed with evidence (suite green, .pb-goal.md COMPLETE)"
